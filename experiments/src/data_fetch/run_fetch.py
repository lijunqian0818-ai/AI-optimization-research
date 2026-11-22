"""Full-pull fetcher (resumable, unattended). Raw data only: no cleaning, no merging, no features.

  python run_fetch.py --stage universe|bars|factors_events|index|crosscheck|zo [--limit N] [--codes-file F] ...
  python run_fetch.py --status            summary of the manifest (no request is sent)
  python run_fetch.py --stage S --plan    how many units would be requested (no request is sent)

Exit codes: 0 all units done; 1 finished with failed units left (rerun to retry them); 3 --max-requests reached;
4 stopped after repeated pauses (host probably blocking); 5 another process holds the lock of a needed host.
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import core
from core import CFG, BS, StopRun, log


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--stage", choices=["universe", "bars", "factors_events", "index", "crosscheck", "zo"])
    p.add_argument("--source", default="", help="comma-separated subset of the stage's sources (default: all)")
    p.add_argument("--limit", type=int, default=0, help="per-name stages: first N names; date-keyed sources: N evenly spaced units per source")
    p.add_argument("--codes-file", default="", help="text file with one code per line (600000 or sh.600000)")
    p.add_argument("--all-names", action="store_true", help="crosscheck only: allow the whole work list")
    p.add_argument("--resume", dest="resume", action="store_true", default=True, help="skip units already stored and verified (default)")
    p.add_argument("--no-resume", dest="resume", action="store_false")
    p.add_argument("--retry-empty", action="store_true", help="request again the units recorded as 'empty'")
    p.add_argument("--start", default="2008-01-01", help="PLAN 2.2: raw data from 2008-01-01")
    p.add_argument("--end", default="2026-06-30", help="PLAN 2.2: last data day 2026-06-30")
    p.add_argument("--div-years", default="", help="bs_dividend: year range Y0:Y1 (default: years of --start..--end)")
    p.add_argument("--ins-first-year", type=int, default=1994, help="zo/ins_raw: first announcement year")
    # rate limits and failure handling (defaults: PLAN 2.5; see FETCH_README.md for the basis)
    p.add_argument("--bs-gap", type=float, default=CFG.bs_gap)
    p.add_argument("--bs-timeout", type=float, default=CFG.bs_timeout)
    p.add_argument("--bs-relogin-every", type=int, default=CFG.bs_relogin_every)
    p.add_argument("--bs-relogin-minutes", type=float, default=CFG.bs_relogin_minutes)
    p.add_argument("--http-gap", type=float, default=CFG.http_gap)
    p.add_argument("--http-daily-cap", type=int, default=CFG.http_daily_cap)
    p.add_argument("--backoff", default="5,20,60", help="retry waits in seconds; at most 3 retries")
    p.add_argument("--max-consec-fail", type=int, default=None)
    p.add_argument("--pause-seconds", type=float, default=CFG.pause_seconds)
    p.add_argument("--max-pauses", type=int, default=None)
    p.add_argument("--ratelimit-wait", type=float, default=CFG.ratelimit_wait)
    p.add_argument("--daily-unit-cap", type=int, default=None)
    p.add_argument("--max-requests", type=int, default=0)
    p.add_argument("--progress-units", type=int, default=CFG.progress_units)
    p.add_argument("--progress-seconds", type=float, default=CFG.progress_seconds)
    p.add_argument("--status", action="store_true")
    p.add_argument("--plan", action="store_true")
    return p.parse_args()


def status_report():
    recs = core.all_manifest_records()
    latest = core.load_manifest()
    print(f"manifest: {core.MANIFEST}  records={len(recs)}  distinct units={len(latest)}")
    agg = defaultdict(lambda: defaultdict(float))
    last = {}
    for r in recs:     # requests and time: every record (retries of earlier runs included)
        k = (r["stage"], r["source"])
        agg[k]["bs"] += r.get("n_bs_queries", 0) or 0
        agg[k]["http"] += r.get("n_http", 0) or 0
    for (st, so, _), r in latest.items():
        k = (st, so)
        agg[k][r["status"]] += 1
        agg[k]["rows"] += r.get("rows") or 0
        agg[k]["bytes"] += r.get("bytes") or 0
        if r["status"] in ("ok", "empty"):
            agg[k]["t"] += r.get("fetch_s") or 0
            agg[k]["n_t"] += 1
        last[k] = max(last.get(k, ""), r["ts"])
    print(f"{'stage/source':38s} {'ok':>6s} {'empty':>6s} {'failed':>6s} {'rows':>11s} {'MB':>8s} {'s/unit':>7s} {'bs_q':>6s} {'http':>6s}  last")
    for k in sorted(agg):
        v = agg[k]
        mean = v["t"] / v["n_t"] if v["n_t"] else float("nan")
        print(f"{k[0] + '/' + k[1]:38s} {int(v['ok']):6d} {int(v['empty']):6d} {int(v['failed']):6d} {int(v['rows']):11d} "
              f"{v['bytes'] / 1e6:8.2f} {mean:7.2f} {int(v['bs']):6d} {int(v['http']):6d}  {last.get(k, '')}")
    failed = [(k, r) for k, r in latest.items() if not r["ok"]]
    if failed:
        print(f"\nunits whose latest record is a failure: {len(failed)} (they are retried by the next run of their stage)")
        for k, r in failed[:30]:
            print("  ", "/".join(k), "|", (r.get("error") or "")[:160])


def main():
    a = parse_args()
    if a.status:
        status_report()
        return 0
    if not a.stage:
        print("--stage is required (or --status)")
        return 2
    import sources
    builder, all_sources = sources.STAGES[a.stage]
    a.sources = [s for s in a.source.split(",") if s] or all_sources
    bad = set(a.sources) - set(all_sources)
    if bad:
        print(f"unknown source(s) for stage {a.stage}: {sorted(bad)}; available: {all_sources}")
        return 2

    # stage defaults: the Sina bar pull stops at the first sign of a block and is capped at 1000 names a day (PLAN 2.5)
    sina_bars = a.stage == "crosscheck"
    CFG.bs_gap, CFG.bs_timeout = a.bs_gap, a.bs_timeout
    CFG.bs_relogin_every, CFG.bs_relogin_minutes = a.bs_relogin_every, a.bs_relogin_minutes
    CFG.http_gap, CFG.http_daily_cap = a.http_gap, a.http_daily_cap
    CFG.backoff = tuple(float(x) for x in a.backoff.split(",") if x)[:3]
    CFG.max_consec_fail = a.max_consec_fail if a.max_consec_fail is not None else (3 if sina_bars else 5)
    CFG.max_pauses = a.max_pauses if a.max_pauses is not None else (0 if sina_bars else 6)
    CFG.pause_seconds, CFG.ratelimit_wait = a.pause_seconds, a.ratelimit_wait
    CFG.daily_unit_cap = a.daily_unit_cap if a.daily_unit_cap is not None else (1000 if sina_bars else 0)
    CFG.max_requests = a.max_requests
    CFG.progress_units, CFG.progress_seconds = a.progress_units, a.progress_seconds
    CFG.resume, CFG.retry_empty = a.resume, a.retry_empty
    CFG.run_id = f"{a.stage}_{time.strftime('%Y%m%d_%H%M%S')}"

    try:
        units = builder(a)
    except FileNotFoundError as e:
        print(f"cannot build the unit list: {e}")
        return 2
    if a.plan:
        man = core.load_manifest()
        by = defaultdict(lambda: [0, 0])
        for u in units:
            by[u.source][0] += 1
            by[u.source][1] += core.record_is_valid(man.get(u.id), u, check_hash=False)
        for s, (n, d) in by.items():
            print(f"{a.stage}/{s}: units={n} done={d} to fetch={n - d}")
        return 0

    logp = core.open_log(a.stage)
    log(f"[run] id={CFG.run_id} stage={a.stage} sources={a.sources} limit={a.limit} codes_file={a.codes_file or '-'} "
        f"period={a.start}..{a.end} log={logp}")
    log(f"[cfg] {CFG}")
    for h in sorted({u.host for u in units}):
        if not core.acquire_host_lock(h):
            log(f"[lock] another fetch process is using host '{h}'; one process per host (PLAN 2.5). Exiting.")
            return 5
    core.patch_http()
    code = 0
    try:
        cnt = core.run_units(units, a.stage)
        if a.stage == "universe" and (core.RAW / "universe" / "bs_stock_basic.parquet").exists():
            s = sources.build_worklist(a.start, a.end)
            log(f"[universe] summary written to {core.OUT / 'universe_summary.json'}: worklist_n={s['worklist_n']} "
                f"by_board={s['worklist_by_board']}")
        if cnt["failed"]:
            code = 1
    except StopRun as e:
        log(f"[stop] {e}")
        code = e.code
    except KeyboardInterrupt:
        log("[stop] interrupted by user; everything finished so far is in the manifest, rerun to continue")
        code = 130
    finally:
        BS.logout()
    log(f"[exit] code={code}")
    return code


if __name__ == "__main__":
    sys.exit(main())

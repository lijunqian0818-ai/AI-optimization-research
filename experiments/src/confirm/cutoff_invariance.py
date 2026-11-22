"""Cut-off invariance test (copied from the pilot; round 2: adapted to run_confirm.py - compares results,
standard orders, the decision dump, the tuning archive's chosen configurations and each run's own panel).

Original description: cut-off invariance test of the pilot (task step 2.6): deleting, or replacing by garbage, every raw
datum dated after the data cut-off leaves every output of the pilot bit-identical.

Two alternative raw trees are written (outside the project, into --work):
  A "deleted"  every per-name table cut at the cut-off with the loaders' own rule (engine.datacut: bars,
               index and calendar rows <= cut; event rows with ex-date <= cut, or without ex-date and
               announced <= cut, later date fields blanked); Z_O period files after the cut-off left out;
               snapshot dates (delisting / listing) after the cut-off blanked.
  B "garbage"  tree A plus synthetic rows dated after the cut-off with random values (bars, index,
               calendar, event tables), Z_O files of later periods filled with bytes that are not parquet
               (opening one would raise) and with random valid tables, and random later delisting dates.
The trees are BUILT WITHOUT READING any datum after the cut-off: tree A is written from the cut readers,
tree B only adds generated rows.  The pilot is then run on A and on B with the same configuration and
list of names as the reference run on the real tree; the canonical results (timings and paths removed),
the standard-order table and every feature file are compared byte for byte / bit for bit.

    experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/cutoff_invariance.py build \\
        --data-cutoff 2021-12-31 --codes-file <file> --work <dir>
    (then run run_confirm.py --raw-root <dir>/tree_A and <dir>/tree_B, and)
    experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/cutoff_invariance.py compare \\
        --runs <ref_out> <A_out> <B_out> --report <json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import numpy as np          # noqa: E402
import pandas as pd         # noqa: E402

from engine import datacut as dc     # noqa: E402

ROOT = HERE.parents[2]
RAW = ROOT / "experiments" / "data" / "raw"
EVENT_KEYS = {"em_fhps": (16, 14, (15, 18, 0, 1)), "sina_dividend": (5, 0, (6, 7)), "sina_rights": (4, 0, (5, 6, 7, 8))}
ZO = {"lhb_detail": "上榜日", "lhb_jgmmtj": "上榜日期", "dzjy_mrmx": "交易日期", "ins_raw": "NOTICE_DATE"}
INDEXES = ("sh.000001", "sz.399001", "sz.399006")


def build(cut, codes, work: Path) -> dict:
    A, B = work / "tree_A", work / "tree_B"
    for t in (A, B):
        if t.exists():
            shutil.rmtree(t)
    info = {"cut": str(cut), "files_A": 0, "garbage_rows_B": 0, "garbage_zo_files_B": 0}
    # ---- tree A
    (A / "universe").mkdir(parents=True)
    cal = dc.read_parquet_cut(RAW / "universe" / "bs_trade_dates.parquet", "calendar_date", cut)
    cal.to_parquet(A / "universe" / "bs_trade_dates.parquet")
    basic = pd.read_parquet(RAW / "universe" / "bs_stock_basic.parquet")
    for c in ("ipoDate", "outDate"):
        basic[c] = ["" if dc.clip_date(x, cut) is None else x for x in basic[c]]
    basic.to_parquet(A / "universe" / "bs_stock_basic.parquet")
    (A / "bars" / "bs_daily").mkdir(parents=True)
    for c in codes:
        p = RAW / "bars" / "bs_daily" / f"{c}.parquet"
        dc.read_parquet_cut(p, "date", cut).to_parquet(A / "bars" / "bs_daily" / f"{c}.parquet")
        info["files_A"] += 1
    (A / "index" / "bs_index_daily").mkdir(parents=True)
    for ix in INDEXES:
        p = RAW / "index" / "bs_index_daily" / f"{ix}.parquet"
        dc.read_parquet_cut(p, "date", cut).to_parquet(A / "index" / "bs_index_daily" / f"{ix}.parquet")
    for sub, (ex, ann, other) in EVENT_KEYS.items():
        (A / "factors_events" / sub).mkdir(parents=True)
        for c in codes:
            p = RAW / "factors_events" / sub / f"{c}.parquet"
            if p.exists():
                df = dc.read_events_cut(p, ex, ann, cut, other_date_cols=other, by_position=True)
                df.to_parquet(A / "factors_events" / sub / f"{c}.parquet")
                info["files_A"] += 1
    for sub in ZO:
        (A / "zo" / sub).mkdir(parents=True)
        for f in sorted((RAW / "zo" / sub).glob("*.parquet")):
            if f.stem.isdigit() and dc.period_ok(f.stem, cut):
                shutil.copy2(f, A / "zo" / sub / f.name)          # whole period <= the cut-off
                info["files_A"] += 1
    # ---- tree B = A + garbage after the cut-off
    shutil.copytree(A, B)
    rng = np.random.default_rng(42)
    late_days = pd.bdate_range(pd.Timestamp(cut) + pd.Timedelta(days=1), "2026-06-30")
    cal_b = pd.concat([cal, pd.DataFrame({"calendar_date": late_days.strftime("%Y-%m-%d"),
                                          "is_trading_day": rng.choice(["1", "0"], len(late_days), p=[0.9, 0.1])})])
    cal_b.to_parquet(B / "universe" / "bs_trade_dates.parquet")
    bb = pd.read_parquet(B / "universe" / "bs_stock_basic.parquet")
    pick = rng.random(len(bb)) < 0.3
    bb.loc[pick & (bb["outDate"] == ""), "outDate"] = [str(pd.Timestamp(d).date()) for d in rng.choice(late_days, int((pick & (bb["outDate"] == "")).sum()))]
    bb.to_parquet(B / "universe" / "bs_stock_basic.parquet")
    for c in codes:
        p = B / "bars" / "bs_daily" / f"{c}.parquet"
        df = pd.read_parquet(p)
        if not len(df):
            continue
        m = len(late_days)
        g = pd.DataFrame({k: df[k].iloc[-1] for k in df.columns}, index=range(m))
        g["date"] = late_days.strftime("%Y-%m-%d")
        for k in ("open", "high", "low", "close", "preclose", "amount", "turn", "pctChg"):
            g[k] = [f"{x:.4f}" for x in rng.uniform(0.5, 300, m)]
        g["volume"] = [str(int(x)) for x in rng.integers(0, 10 ** 8, m)]
        g["tradestatus"] = rng.choice(["1", "0"], m)
        g["isST"] = rng.choice(["0", "1"], m)
        pd.concat([df, g], ignore_index=True).to_parquet(p)
        info["garbage_rows_B"] += m
    for ix in INDEXES:
        p = B / "index" / "bs_index_daily" / f"{ix}.parquet"
        df = pd.read_parquet(p)
        g = pd.DataFrame({k: df[k].iloc[-1] for k in df.columns}, index=range(len(late_days)))
        g["date"] = late_days.strftime("%Y-%m-%d")
        for k in ("open", "high", "low", "close", "preclose"):
            g[k] = [f"{x:.4f}" for x in rng.uniform(1000, 9000, len(late_days))]
        pd.concat([df, g], ignore_index=True).to_parquet(p)
    for sub, (ex, ann, _other) in EVENT_KEYS.items():
        for f in sorted((B / "factors_events" / sub).glob("*.parquet")):
            df = pd.read_parquet(f)
            if not len(df):
                continue
            cols = list(df.columns)
            g = df.iloc[[-1] * 3].copy().reset_index(drop=True)
            dts = sorted(pd.Timestamp(x) for x in rng.choice(late_days, 3))
            for k in (ex, ann):
                g[cols[k]] = [d.date() for d in dts]
            for col in cols:
                if pd.api.types.is_float_dtype(df[col]):
                    g[col] = rng.uniform(0, 10, 3)
            try:
                pd.concat([df, g], ignore_index=True).to_parquet(f)
                info["garbage_rows_B"] += 3
            except Exception:                                  # a dtype the generator cannot fill: keep A
                pass
    for sub, col in ZO.items():
        d = B / "zo" / sub
        years = sorted({x.year for x in late_days})
        periods = [str(y) for y in years] if sub == "ins_raw" else sorted({x.strftime("%Y%m") for x in late_days})
        for k, per in enumerate(periods):
            if k % 2 == 0:
                (d / f"{per}.parquet").write_bytes(b"not a parquet file: must never be opened")
            else:
                ref = sorted(d.glob("*.parquet"))
                ref = [r for r in ref if dc.period_ok(r.stem, cut)]
                df = pd.read_parquet(ref[-1]).head(50).copy()
                for c2 in df.columns:
                    if pd.api.types.is_float_dtype(df[c2]):
                        df[c2] = rng.uniform(0, 1e6, len(df))
                df.to_parquet(d / f"{per}.parquet")
            info["garbage_zo_files_B"] += 1
    return info


VOLATILE_KEYS = {"timing", "sim_seconds", "seconds", "deploy_seconds", "batch_seconds", "total_seconds",
                 "panel_provenance_action", "loaded_from_checkpoint", "tuning_archive", "created"}


def _strip(x):
    if isinstance(x, dict):
        return {k: _strip(v) for k, v in x.items() if k not in VOLATILE_KEYS}
    if isinstance(x, list):
        return [_strip(v) for v in x]
    return x


def canonical_results(path: Path) -> str:
    """results.json without wall times, paths and run-provenance fields (round 2: recursive)."""
    r = json.loads(path.read_text(encoding="utf-8"))
    if "panel" in r:
        r["panel"].pop("dir", None)
    cfg = r.get("config", {})
    for k in ("out_dir", "panel_dir", "n_jobs"):
        cfg.pop(k, None)
    blob = json.dumps(_strip(r), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()


def frame_hash(df: pd.DataFrame) -> str:
    h = hashlib.sha256()
    h.update(json.dumps([list(map(str, df.columns)), list(map(str, df.index[:3])), len(df)]).encode())
    h.update(pd.util.hash_pandas_object(df, index=True).values.tobytes())
    return h.hexdigest()


def compare(runs: list, report: Path, panels: list | None = None) -> dict:
    """Round 2 (run_confirm.py): results.json (canonical), standard orders (without the internal lot id, which
    depends on the number of worker processes), every decision-dump table, the chosen configurations of the
    tuning archive, and every feature file of each run's own panel directory."""
    out = {"runs": [str(r) for r in runs], "results_hash": [], "standard_orders_hash": [], "dump": {},
           "archive_entries_hash": [], "feature_files": {}}
    for r in runs:
        r = Path(r)
        out["results_hash"].append(canonical_results(r / "results.json"))
        so = pd.read_parquet(r / "standard_orders.parquet")
        out["standard_orders_hash"].append(frame_hash(so.drop(columns=[c for c in ("lot",) if c in so.columns])))
        for t in ("nominations", "submissions", "decision_days", "base_ic"):
            f = r / f"{t}.parquet"
            out["dump"].setdefault(t, []).append(frame_hash(pd.read_parquet(f)) if f.exists() else None)
        fa = r / "tuning_archive.json"
        out["archive_entries_hash"].append(hashlib.sha256(json.dumps(json.loads(fa.read_text(encoding="utf-8"))["entries"],
                                                                     sort_keys=True).encode()).hexdigest()
                                           if fa.exists() else None)
    panels = [Path(p) for p in (panels or [Path(r) / "feature_panel" for r in runs])]
    ref_dir = panels[0] / "features"
    n_same = n_tot = 0
    diff_files = []
    for f in sorted(ref_dir.glob("*.parquet")):
        hs = [frame_hash(pd.read_parquet(pp / "features" / f.name)) if (pp / "features" / f.name).exists() else None
              for pp in panels]
        n_tot += 1
        same = len(set(hs)) == 1 and hs[0] is not None
        n_same += int(same)
        if not same:
            diff_files.append(f.name)
    out["feature_files"] = {"compared": n_tot, "identical_in_all_runs": n_same, "differing": diff_files[:20]}
    out["results_identical"] = len(set(out["results_hash"])) == 1
    out["standard_orders_identical"] = len(set(out["standard_orders_hash"])) == 1
    out["dump_identical"] = {t: (len(set(v)) == 1 and v[0] is not None) for t, v in out["dump"].items()}
    out["archive_identical"] = len(set(out["archive_entries_hash"])) == 1 and out["archive_entries_hash"][0] is not None
    out["pass"] = bool(out["results_identical"] and out["standard_orders_identical"] and all(out["dump_identical"].values())
                       and out["archive_identical"] and n_same == n_tot and n_tot > 0)
    report.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build")
    b.add_argument("--data-cutoff", required=True)
    b.add_argument("--codes-file", required=True)
    b.add_argument("--work", required=True)
    c = sp.add_parser("compare")
    c.add_argument("--runs", nargs="+", required=True)
    c.add_argument("--report", required=True)
    c.add_argument("--panels", nargs="*", default=None, help="each run's feature panel directory (same order as --runs)")
    a = ap.parse_args()
    if a.cmd == "build":
        codes = [l.strip() for l in open(a.codes_file, encoding="utf-8") if l.strip()]
        info = build(dc.require_cutoff(a.data_cutoff), codes, Path(a.work))
        print(json.dumps(info))
        return 0
    res = compare(a.runs, Path(a.report), a.panels)
    print(json.dumps({k: res[k] for k in ("results_identical", "standard_orders_identical", "dump_identical",
                                          "archive_identical", "feature_files", "pass")}))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

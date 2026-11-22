"""Exploratory pilot round (PLAN v0.8 section 13A): the whole pipeline once, development data only.

    experiments/.venv/Scripts/python.exe -X utf8 experiments/src/pilot/run_pilot.py --data-cutoff 2021-12-31 \\
        [--smoke --smoke-n 100] [--out DIR] [--panel-dir DIR] [--jobs N] [--bases lgbm,ridge]

Stages (timed; logged to <out>/logs/run.log):
  1 list and readiness (names without their bar file or pilot event files are skipped and listed)
  2 engine market: bars, event table (EV1 + EV2 by the v0.8 mechanical rules), cut at the data cut-off
  3 feature panel (feature library; Z_O filtered to the list)
  4 universe U-LIQ-P (N_U = 300) and candidate sets
  5 feature rows of the candidate sets, cross-sectional rank transform
  6 base predictors (LightGBM; ridge / elastic net), frozen annual deployment, nominations top-K
  7 standard orders rho and O1 labels for every candidate (engine ledger)
  8 gates and baselines of PLAN 6.1 round 1, tuning by the common criterion, annual deployment
  9 deployment backtests (engine), VT, E-const-dev, RND
 10 estimands: deployed outcomes, Lemma 3 attribution, theta_sel, psi_H / psi_O, coverage, loss shares,
    Theorem 1 interval, abstained trades, RND; date-block bootstrap; seeds
 11 results file, run manifest (code hash, configuration, seeds, data-file SHA-256, times)

Every raw file is read through the cut-off loaders of the engine and of the feature library; the
cut-off is a required argument.  Outcome numbers go to results files only; this script prints none.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import platform
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np          # noqa: E402
import pandas as pd         # noqa: E402

from engine import datacut as dc                         # noqa: E402
from engine.config import conventions_hash               # noqa: E402
from pilot import backtest as BT                         # noqa: E402
from pilot import data as D                              # noqa: E402
from pilot import estimands as E                         # noqa: E402
from pilot import models as M                            # noqa: E402
from pilot import stdorders as SO                        # noqa: E402
from pilot import strategy as S                          # noqa: E402
from pilot.config import REDUCTIONS, PilotConfig, smoke_config   # noqa: E402

ROOT = SRC.parents[1]


class Log:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = open(path, "a", encoding="utf-8")
        self.t0 = time.time()

    def __call__(self, msg: str):
        line = f"{datetime.now().strftime('%H:%M:%S')} +{time.time() - self.t0:7.0f}s {msg}"
        print(line, flush=True)
        self.fh.write(line + "\n")
        self.fh.flush()


def code_hash() -> dict:
    out, h = {}, hashlib.sha256()
    for sub in ("engine", "features", "pilot"):
        for p in sorted((SRC / sub).rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            b = p.read_bytes()
            out[str(p.relative_to(SRC)).replace(os.sep, "/")] = hashlib.sha256(b).hexdigest()
            h.update(b)
    for extra in (SRC / "features" / "lhb_reason_map.csv",):
        out[str(extra.relative_to(SRC)).replace(os.sep, "/")] = dc.file_sha256(extra)
        h.update(extra.read_bytes())
    return {"combined": h.hexdigest(), "files": out}


def data_hashes(codes: list, cut) -> dict:
    """SHA-256 of every raw file the run may open (the file as on disk; the loaders read only rows <= cut)."""
    raw = D.RAW
    files = [raw / "universe" / "bs_trade_dates.parquet", raw / "universe" / "bs_stock_basic.parquet"]
    for c in codes:
        files.append(raw / "bars" / "bs_daily" / f"{c}.parquet")
        for sub in ("em_fhps", "sina_dividend", "sina_rights"):
            files.append(raw / "factors_events" / sub / f"{c}.parquet")
    for idx in ("sh.000001", "sz.399001", "sz.399006"):
        files.append(raw / "index" / "bs_index_daily" / f"{idx}.parquet")
    for sub in ("lhb_detail", "lhb_jgmmtj", "dzjy_mrmx", "ins_raw"):
        for f in sorted((raw / "zo" / sub).glob("*.parquet")):
            if f.stem.isdigit() and dc.period_ok(f.stem, cut):
                files.append(f)
    out = {}
    for f in files:
        if f.exists():
            out[str(f.relative_to(ROOT)).replace(os.sep, "/")] = dc.file_sha256(f)
    return out


def to_jsonable(x):
    if isinstance(x, dict):
        return {str(k): to_jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [to_jsonable(v) for v in x]
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, np.ndarray):
        return [to_jsonable(v) for v in x.tolist()]
    if isinstance(x, pd.DataFrame):
        return x.to_dict("list")
    if isinstance(x, (set, frozenset)):
        return sorted(to_jsonable(v) for v in x)
    if isinstance(x, float) and not np.isfinite(x):
        return None
    return x


# ====================================================================================== pipeline
def run(cfg: PilotConfig, log: Log, outdir: Path, raw: Path = D.RAW, stop_after: str = "",
        dump_decisions: bool = False, reuse_tuning: dict | None = None) -> dict:
    timing, res = {}, {"config": cfg.to_json(), "pilot_reductions": REDUCTIONS}
    cut = cfg.cut()

    def stage(name):
        timing[name] = {"start": time.time()}
        log(f"=== stage {name}")

    def done(name):
        timing[name]["seconds"] = round(time.time() - timing[name]["start"], 1)
        del timing[name]["start"]
        log(f"=== stage {name} done in {timing[name]['seconds']} s")

    # ---------------------------------------------------------------- 1 list and readiness
    stage("1_list")
    codes, linfo = D.pilot_list(cfg)
    # readiness (bar file and pilot event files finished); an alternative raw tree (cut-off test) is
    # used with the list of names of the run it is compared with
    rd = D.readiness(codes) if raw == D.RAW else pd.DataFrame({"code": codes, "ready": True})
    skipped = rd[~rd["ready"]]
    use = [c for c in codes if c in set(rd.loc[rd["ready"], "code"])]
    res["list"] = linfo
    res["readiness"] = {"n_ready": len(use), "n_skipped": int(len(skipped)),
                        "skipped": skipped.drop(columns=[x for x in ("ready",) if x in skipped.columns]).to_dict("records")}
    log(f"list: {len(codes)} names, ready {len(use)}, skipped {len(skipped)}")
    done("1_list")

    # ---------------------------------------------------------------- 2 market
    stage("2_market")
    market, mrep = D.load_market(cfg, use, raw)
    res["market"] = {"n_days": mrep["n_days"], "first_day": mrep["first_day"], "last_day": mrep["last_day"],
                     "data_cutoff": mrep["data_cutoff"], "n_problems": len(mrep["problems"]),
                     "problems": mrep["problems"][:50], "event_table_counts": mrep["event_table"]["counts"],
                     "event_table_by_year": mrep["event_table"]["by_year"], "event_table_hash": mrep["event_table"]["hash"],
                     "hand_check_items_diagnostic": len(mrep["event_table"]["hand_check"]),
                     "urs": len(mrep["event_table"]["urs"]), "event_sources": {k: v for k, v in mrep["event_sources"].items() if k != "column_names"},
                     "dispositions": {k: mrep["dispositions"].get(k) for k in ("no_row", "fallback_sentence_required")}}
    use = [c for c in use if c in market.secs]
    done("2_market")

    # ---------------------------------------------------------------- 3 feature panel
    stage("3_panel")
    pdir = ROOT / cfg.panel_dir
    man = D.build_panel(cfg, use, pdir, raw)
    res["panel"] = {"dir": str(pdir), "n_ok": int((man["status"] == "ok").sum()), "n_error": int((man["status"] == "error").sum()),
                    "errors": man.loc[man["status"] == "error", ["code", "error"]].to_dict("records")[:20],
                    "blk_trades": int(pd.to_numeric(man.get("blk_trades", 0), errors="coerce").fillna(0).sum()),
                    "blk_implausible": int(pd.to_numeric(man.get("blk_implausible", 0), errors="coerce").fillna(0).sum())}
    use = [c for c in use if c in set(man.loc[man["status"] == "ok", "code"])]
    done("3_panel")

    # ---------------------------------------------------------------- 4 universe and candidates
    stage("4_universe")
    days = market.days
    yb_all = S.year_bounds(days, sorted({d.year for d in days}))
    first_i = yb_all[cfg.first_feature_year][0]
    last_dec = market.T - 1 - (cfg.H + 10)              # end-of-window rule (PLAN 8.3, U50)
    by_month, cand, urep = D.universe_and_candidates(market, use, cfg, first_i, last_dec)
    cc = urep["candidate_counts"]
    res["universe"] = {"screens": len(urep["screens"]),
                       "members_per_screen": [r.get("members", 0) for r in urep["screens"]][-24:],
                       "eligible_per_screen_min_med_max": [int(np.min([r.get("eligible", 0) for r in urep["screens"]])),
                                                           int(np.median([r.get("eligible", 0) for r in urep["screens"]])),
                                                           int(np.max([r.get("eligible", 0) for r in urep["screens"]]))],
                       "candidates_per_day_min_med_max": [int(np.min([len(v) for v in cand.values()])),
                                                          int(np.median([len(v) for v in cand.values()])),
                                                          int(np.max([len(v) for v in cand.values()]))],
                       "days_with_fewer_than_K_candidates": int(sum(len(v) < cfg.K for v in cand.values())),
                       "removed": {k: int(sum(r.get(k, 0) for r in cc.values())) for k in
                                   ("removed_listing_age", "removed_suspended", "removed_no_row", "removed_st_lookback")},
                       "last_decision_day": days[last_dec].isoformat()}
    done("4_universe")

    # ---------------------------------------------------------------- 5 feature rows
    stage("5_features")
    colsets = D.feature_columns()
    allcols = colsets["-Z"] + colsets["Z_H"] + colsets["Z_O"]
    di, cc_, Xraw = D.load_feature_rows(pdir, market, cand, allcols)
    Xr = M.rank_within_days(di, Xraw)
    del Xraw
    fr = S.Frame(di, cc_, Xr, allcols, {(int(i), c): k for k, (i, c) in enumerate(zip(di, cc_))})
    der = D.Derived(market, use, cfg)
    res["features"] = {"rows": int(len(di)), "columns": {k: len(v) for k, v in colsets.items()},
                       "candidate_rows_without_feature_row": int(sum(len(v) for v in cand.values()) - len(di))}
    done("5_features")
    if stop_after == "5":
        return res

    # ---------------------------------------------------------------- 6 base predictors and nominations
    stage("6_base")
    y = S.base_target(fr, der)
    first_dep = yb_all[cfg.base_deploy_start][0]
    bases = {}
    for b in cfg.bases:
        bs = S.base_scores(fr, y, days, cfg, b, cfg.seeds, log)
        bases[b] = bs
    noms, ktr = {}, {}
    for b in cfg.bases:
        for s in cfg.seeds:
            rk = bases[b][s]["rank"]
            noms[(b, s)] = {i: v for i, v in S.nominations(fr, rk, cand, cfg.K, first_dep).items() if i <= last_dec}
            ktr[(b, s)] = {i: v for i, v in S.nominations(fr, rk, cand, cfg.K_tr, first_dep).items() if i <= last_dec}
    res["base"] = {b: {"chosen": bases[b][cfg.seeds[0]]["config"], "tuning": bases[b][cfg.seeds[0]]["tuning"]}
                   for b in cfg.bases}
    done("6_base")

    # ---------------------------------------------------------------- 7 standard orders
    stage("7_standard_orders")
    asks = {i: list(cand[i]) for i in range(first_dep, last_dec + 1) if i in cand}
    ecfg = D.engine_config(cfg)
    std_df = SO.standard_orders(market, ecfg, asks, market.T - 1, cfg.n_jobs)
    std = {(int(r.i), r.code): {"filled": bool(r.filled), "rho": float(r.rho), "o1": float(r.o1) if r.o1 == r.o1 else np.nan,
                                "exit_i": int(r.exit_i), "unresolved": bool(r.unresolved), "reason": r.reason}
           for r in std_df.itertuples()}
    std_df.to_parquet(outdir / "standard_orders.parquet")
    res["standard_orders"] = {"n": int(len(std_df)), "filled": int(std_df["filled"].sum()),
                              "by_reason": std_df["reason"].value_counts().to_dict(),
                              "unresolved": int(std_df["unresolved"].sum()),
                              "o1_outcome": std_df["o1_outcome"].value_counts().to_dict()}
    done("7_standard_orders")

    # ---------------------------------------------------------------- 8 gates
    stage("8_gates")
    yb = yb_all
    tune_days = [i for v in cfg.gate_tune_years for i in range(yb[v][0], min(yb[v][1], last_dec) + 1)]
    eval_days = [i for v in cfg.eval_years for i in range(yb[v][0], min(yb[v][1], last_dec) + 1)]
    dep_years = list(cfg.gate_tune_years) + list(cfg.eval_years)
    learned = {m: ("logit" if m.startswith("LOSS-LR") else "lgbm") for m in cfg.methods
               if m.split("(")[0] in ("LOSS", "LOSS-LR", "NET-K", "NET-U")}
    fixed = [m for m in cfg.methods if m in ("G0", "SCORE", "CONF", "VOL", "LIQ")]
    subs: dict = {}                    # (b, s, method) -> {i: (set, scale)}
    tuning_log: dict = {}
    ctxs = {}
    for b in cfg.bases:
        for s in cfg.seeds:
            ctxs[(b, s)] = S.GateContext(fr, bases[b][s]["rank"], noms[(b, s)], ktr[(b, s)], cand, std, der, cfg,
                                         days, colsets, seed=s, perm_seed=1000 + s)
    for b in cfg.bases:
        for m in fixed:
            for s in cfg.seeds:
                sub = {}
                for Y in dep_years:
                    sub.update(ctxs[(b, s)].gate_year(m, {}, Y))
                subs[(b, s, m)] = sub
    # permutation draws of the nuisance controls are made once per (base, seed) before any thread starts,
    # so that they do not depend on scheduling (PLAN 7.3 c: one draw per seed)
    for ctx in ctxs.values():
        for grp in ("Z_H", "Z_O"):
            ctx._permuted(np.zeros(0, dtype=int), grp)

    def learn(b, m, kind):
        confs = M.draw_configs(kind, cfg.n_configs)
        if reuse_tuning is not None:
            # diagnostics re-run: refit only the configuration an earlier identical run chose (no re-tuning)
            prev = reuse_tuning[f"{b}|{m}"]
            if to_jsonable(prev["configs"]) != to_jsonable(confs):
                raise RuntimeError(f"reuse-tuning: configurations of {b}|{m} differ from the earlier run")
            best = int(prev["chosen"])
            out = {}
            for s in cfg.seeds:
                sub = {}
                for Y in list(cfg.gate_tune_years) + list(cfg.eval_years):
                    sub.update(ctxs[(b, s)].gate_year(m, confs[best], Y))
                out[s] = sub
            return b, m, {"configs": confs, "criterion_mean_theta_sel": prev["criterion_mean_theta_sel"],
                          "chosen": best, "reused": True}, out
        fits, crit = {}, []
        for k, conf in enumerate(confs):
            vals = []
            for s in cfg.seeds:
                for v in cfg.gate_tune_years:
                    sub = ctxs[(b, s)].gate_year(m, conf, v)
                    fits[(k, s, v)] = sub
                    dr = [i for i in range(yb[v][0], min(yb[v][1], last_dec) + 1)]
                    if m.startswith("NET-U"):
                        th = S.theta_sel_pool(sub, cand, std, der, dr)
                    else:
                        th = S.theta_sel(sub, noms[(b, s)], std, der, dr)
                    vals.append(th.get("theta_sel", np.nan))
            crit.append(float(np.nanmean(vals)) if np.isfinite(vals).any() else -np.inf)
        best = max(range(len(confs)), key=lambda k: (crit[k], -k))
        out = {}
        for s in cfg.seeds:
            sub = {}
            for v in cfg.gate_tune_years:
                sub.update(fits[(best, s, v)])
            for Y in cfg.eval_years:
                sub.update(ctxs[(b, s)].gate_year(m, confs[best], Y))
            out[s] = sub
        return b, m, {"configs": confs, "criterion_mean_theta_sel": crit, "chosen": best}, out

    from concurrent.futures import ThreadPoolExecutor
    tasks = [(b, m, kind) for b in cfg.bases for m, kind in learned.items()]
    with ThreadPoolExecutor(max_workers=max(1, cfg.n_jobs)) as ex:      # LightGBM / numpy release the GIL
        for b, m, tl, out in ex.map(lambda t: learn(*t), tasks):
            tuning_log[(b, m)] = tl
            for s, sub in out.items():
                subs[(b, s, m)] = sub
            log(f"[gates {b}] {m}: tuned over {len(tl['configs'])} configurations")
    done("8_gates")

    if dump_decisions:
        # diagnostics only: daily nominations (with rho, stratum, base score) and every gate's submissions
        rows = []
        for (b, s), nm in noms.items():
            sc = bases[b][s]["score"]
            for i, v in nm.items():
                if i < yb[cfg.gate_tune_years[0]][0]:
                    continue
                cell = S.strata(v, i, der)
                for pos_, c in enumerate(v):
                    st_ = std[(i, c)]
                    rows.append((b, s, int(i), days[i].isoformat(), c, pos_, float(sc[fr.row[(int(i), c)]]),
                                 st_["rho"], st_["filled"], cell[c]))
        pd.DataFrame(rows, columns=["base", "seed", "i", "date", "code", "pos", "score", "rho", "filled", "cell"]
                     ).to_parquet(outdir / "nominations.parquet")
        rows = [(b, s, m, int(i), c) for (b, s, m), sub in subs.items() for i, (names, _sc) in sub.items() for c in names]
        pd.DataFrame(rows, columns=["base", "seed", "method", "i", "code"]).to_parquet(outdir / "submissions.parquet")
        rows = []
        for b in cfg.bases:
            for s in cfg.seeds:
                ic = M.spearman_by_day(fr.day, bases[b][s]["score"], der_fwd_rows(fr, der))
                rows += [(b, s, int(i), days[int(i)].isoformat(), float(v)) for i, v in ic.items()]
        pd.DataFrame(rows, columns=["base", "seed", "i", "date", "rank_ic"]).to_parquet(outdir / "base_ic.parquet")
        res["tuning"] = {f"{b}|{m}": v for (b, m), v in tuning_log.items()}
        log("decisions dumped: nominations.parquet, submissions.parquet, base_ic.parquet")
    if stop_after == "8":
        res["timing"] = timing
        return res

    # ---------------------------------------------------------------- 9 backtests
    stage("9_backtests")
    sim_lo = yb[cfg.gate_tune_years[0]][0]
    sim_hi = market.T - 1
    ev_lo, ev_hi = eval_days[0], eval_days[-1]
    tu_lo, tu_hi = tune_days[0], tune_days[-1]

    def plan_of(sub, lo=sim_lo, hi=last_dec, noms_bs=None):
        out = {}
        for i in range(lo, hi + 1):
            if i in sub:
                names, scale = sub[i]
                order = noms_bs.get(i, sorted(names)) if noms_bs is not None else sorted(names)
                lst = [(c, scale) for c in order if c in names]
                extra = sorted(set(names) - {c for c, _ in lst})
                out[i] = (lst + [(c, scale) for c in extra])[:cfg.K]
        return out

    # TREND / PERF tuning by AR over the tuning years (PLAN 6.3 item 3)
    # equal-weight index of the universe (the month's members), daily close-to-close (TREND, PLAN 6.1)
    ew = np.full(market.T, np.nan)
    for i in range(1, market.T):
        mem = by_month.get((days[i].year, days[i].month), [])
        jj = [der.k[c] for c in mem if c in der.k]
        if jj:
            v = der.ret1[i, jj]
            v = v[np.isfinite(v)]
            if len(v):
                ew[i] = v.mean()
    grid_methods = [m for m in cfg.methods if m in ("TREND", "PERF")]
    ic_series = {}
    for b in cfg.bases:
        for s in cfg.seeds:
            sc = bases[b][s]["score"]
            ic = M.spearman_by_day(fr.day, sc, der_fwd_rows(fr, der))
            ic_series[(b, s)] = ic

    def grid_sub(m, conf, b, s, lo, hi):
        sub = {}
        nm = noms[(b, s)]
        if m == "TREND":
            L, thr = conf["L"], conf["thr"]
            for i in range(lo, hi + 1):
                if i not in nm:
                    continue
                seg = ew[max(0, i - L):i]
                seg = seg[np.isfinite(seg)]
                tr = np.prod(1 + seg) - 1 if len(seg) == L else np.nan
                sub[i] = (set(nm[i]) if (np.isfinite(tr) and tr >= thr) else set(), 1.0)
        else:
            hl, thr = conf["halflife"], conf["thr"]
            ic = ic_series[(b, s)]
            for i in range(lo, hi + 1):
                if i not in nm:
                    continue
                hist = ic[ic.index <= i - cfg.H - 2]
                ew_ic = hist.ewm(halflife=hl).mean().iloc[-1] if len(hist) else np.nan
                sub[i] = (set(nm[i]) if (np.isfinite(ew_ic) and ew_ic >= thr) else set(), 1.0)
        return sub

    jobs, keys = [], []
    for b in cfg.bases:
        for m in grid_methods:
            confs = M.draw_configs(m.lower(), cfg.n_configs)
            for k, conf in enumerate(confs):
                for s in cfg.seeds:
                    sub = grid_sub(m, conf, b, s, tu_lo, tu_hi)
                    jobs.append((plan_of(sub, tu_lo, tu_hi, noms[(b, s)]), tu_lo, min(tu_hi + cfg.H + 10, sim_hi),
                                 tu_lo, tu_hi, f"tune|{b}|{m}|{k}|{s}", cfg.delta_mon, False))
                    keys.append((b, m, k, s))
    tune_res = BT.run_many(market, ecfg, jobs, cfg.n_jobs) if jobs else []
    for b in cfg.bases:
        for m in grid_methods:
            confs = M.draw_configs(m.lower(), cfg.n_configs)
            crit = []
            for k in range(len(confs)):
                ars = []
                for (bb, mm, kk, s), r in zip(keys, tune_res):
                    if (bb, mm, kk) == (b, m, k):
                        W, Wp = r["W_close"], r["W_prev"]
                        rr = (W / Wp - 1.0)[: tu_hi - tu_lo + 1]
                        ars.append(E.wealth_metrics(rr)["AR"])
                crit.append(float(np.mean(ars)))
            best = max(range(len(confs)), key=lambda k: (crit[k], -k))
            tuning_log[(b, m)] = {"configs": confs, "criterion_mean_AR": crit, "chosen": best}
            for s in cfg.seeds:
                subs[(b, s, m)] = grid_sub(m, confs[best], b, s, sim_lo, last_dec)

    # main runs
    main_methods = [m for m in cfg.methods if m != "VT"]
    jobs, keys = [], []
    for b in cfg.bases:
        for s in cfg.seeds:
            for m in main_methods:
                jobs.append((plan_of(subs[(b, s, m)], noms_bs=noms[(b, s)]), sim_lo, sim_hi, ev_lo, ev_hi,
                             f"{b}|{m}|{s}", cfg.delta_mon))
                keys.append((b, s, m))
    log(f"main backtests: {len(jobs)} runs")
    runs = dict(zip(keys, BT.run_many(market, ecfg, jobs, cfg.n_jobs)))

    # VT and E-const-dev (need G0 / gate exposures and returns), RND
    jobs, keys = [], []
    for b in cfg.bases:
        for s in cfg.seeds:
            g0 = runs[(b, s, "G0")]
            r0 = g0["W_close"] / g0["W_prev"] - 1.0
            sig = pd.Series(r0).rolling(60, min_periods=60).std().shift(1).to_numpy()     # through t-1
            dd = np.arange(sim_lo, sim_hi + 1)
            tmask = (dd >= tu_lo) & (dd <= tu_hi) & np.isfinite(sig)
            lo_s, hi_s = 1e-8, 1.0
            for _ in range(80):                                   # sigma*: mean s_t = c on the tuning days
                mid = 0.5 * (lo_s + hi_s)
                if np.mean(np.minimum(1.0, mid / sig[tmask])) < cfg.c:
                    lo_s = mid
                else:
                    hi_s = mid
            sstar = 0.5 * (lo_s + hi_s)
            vt = {}
            for k, i in enumerate(dd):
                if i in noms[(b, s)] and i <= last_dec:
                    sc = 1.0 if not np.isfinite(sig[k]) else min(1.0, sstar / sig[k])
                    vt[i] = (set(noms[(b, s)][i]), sc)
            subs[(b, s, "VT")] = vt
            if "VT" in cfg.methods:
                jobs.append((plan_of(vt, noms_bs=noms[(b, s)]), sim_lo, sim_hi, ev_lo, ev_hi, f"{b}|VT|{s}", cfg.delta_mon))
                keys.append((b, s, "VT"))
            e0 = pd.Series(g0["exposure"], index=dd)
            for g in cfg.e_const_dev_for:
                if (b, s, g) not in runs:
                    continue
                eg = pd.Series(runs[(b, s, g)]["exposure"], index=dd)
                sub = {}
                for Y in cfg.eval_years:
                    prev = list(cfg.gate_tune_years) if Y == cfg.eval_years[0] else [Y - 1]
                    msk = np.zeros(len(dd), bool)
                    for v in prev:
                        msk |= (dd >= yb[v][0]) & (dd <= yb[v][1])
                    lam = min(1.0, float(eg[msk].mean() / e0[msk].mean())) if e0[msk].mean() > 0 else 1.0
                    for i in range(yb[Y][0], min(yb[Y][1], last_dec) + 1):
                        if i in noms[(b, s)]:
                            sub[i] = (set(noms[(b, s)][i]), lam)
                for i in range(sim_lo, ev_lo):                      # tuning years: lambda = 1 (declared)
                    if i in noms[(b, s)]:
                        sub[i] = (set(noms[(b, s)][i]), 1.0)
                subs[(b, s, f"E-const-dev[{g}]")] = sub
                jobs.append((plan_of(sub, noms_bs=noms[(b, s)]), sim_lo, sim_hi, ev_lo, ev_hi, f"{b}|E-const-dev[{g}]|{s}", cfg.delta_mon))
                keys.append((b, s, f"E-const-dev[{g}]"))
            for g in cfg.rnd_for:
                if (b, s, g) not in subs:
                    continue
                for rep in range(cfg.rnd_reps):
                    rng = np.random.default_rng(10_000 * s + 100 * rep + hash_str(g) % 97)
                    sub = {}
                    for i, (names, _sc) in subs[(b, s, g)].items():
                        if i < sim_lo or i > last_dec or i not in noms[(b, s)]:
                            continue
                        nm = noms[(b, s)][i]
                        cell = S.strata(nm, i, der)
                        pick = set()
                        for cl in set(cell.values()):
                            pool = [x for x in nm if cell[x] == cl]
                            kk = sum(1 for x in pool if x in names)
                            if kk:
                                pick |= set(rng.choice(pool, size=kk, replace=False).tolist())
                        sub[i] = (pick, 1.0)
                    jobs.append((plan_of(sub, noms_bs=noms[(b, s)]), sim_lo, sim_hi, ev_lo, ev_hi, f"{b}|RND[{g}]#{rep}|{s}",
                                 cfg.delta_mon, False))
                    keys.append((b, s, f"RND[{g}]#{rep}"))
    log(f"second-stage backtests: {len(jobs)} runs")
    runs.update(dict(zip(keys, BT.run_many(market, ecfg, jobs, cfg.n_jobs))))
    done("9_backtests")

    # ---------------------------------------------------------------- 10 estimands
    stage("10_estimands")
    res["estimates"] = estimates(cfg, runs, subs, noms, cand, std, der, eval_days, sim_lo, ev_lo, ev_hi, market)
    res["tuning"] = {f"{b}|{m}": v for (b, m), v in tuning_log.items()}
    res["reconciliation"] = {f"{b}|{m}|{s}": r["recon"] for (b, s, m), r in runs.items()}
    res["recon_max"] = recon_max(runs)
    res["sim_seconds"] = {f"{b}|{m}|{s}": r["total_seconds"] for (b, s, m), r in runs.items()}
    res["result_records"] = {f"{b}|{m}|{s}": r["result_record"] for (b, s, m), r in runs.items()}
    done("10_estimands")
    res["timing"] = timing
    return res


def hash_str(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16)


def der_fwd_rows(fr, der):
    return np.array([der.fwd[i, der.k[c]] if c in der.k else np.nan for i, c in zip(fr.day, fr.code)], dtype=float)


def recon_max(runs: dict) -> dict:
    keys = ("R2_daily_rel", "R2_cum_rel", "cost_total_vs_lot_costs_rel", "turnover_identity_rel", "naive_vs_ledger_rel")
    out = {}
    for k in keys:
        vals = [r["recon"][k] for r in runs.values() if isinstance(r["recon"][k], (int, float))]
        out[k] = max(vals) if vals else None
    out["naive_not_covered_runs"] = sum(1 for r in runs.values() if not isinstance(r["recon"]["naive_vs_ledger_rel"], (int, float)))
    out["R2_days_over_tolerance"] = sum(r["recon"]["R2_days_over_tolerance"] for r in runs.values())
    out["R3_unexplained"] = sum(r["recon"]["R3_unexplained"] for r in runs.values())
    return out


def estimates(cfg, runs, subs, noms, cand, std, der, eval_days, sim_lo, ev_lo, ev_hi, market) -> dict:
    from engine import attribution as AT
    out = {"note": "exploratory pilot (PLAN 13A); not confirmatory evidence for C1-C4"}
    n = len(eval_days)
    idx = E.stationary_indices(n, cfg.bootstrap_B, cfg.block_mean, seed=20261115)
    pos = {i: k for k, i in enumerate(eval_days)}
    dd = np.arange(sim_lo, market.T)
    ev_mask = (dd >= ev_lo) & (dd <= ev_hi)
    bound = 1.0 * 0.01 * (cfg.H + 1) / (E.A * cfg.c)               # Delta_ord from Delta_cap = 1%/year (PLAN 9.3)
    out["Delta_ord"] = bound
    methods = sorted({m for (_b, _s, m) in runs})
    for b in cfg.bases:
        ob = out.setdefault(b, {})
        # ---- theta_sel per within-batch method, seed-averaged series
        series = {}
        for m in sorted({m for (bb, s, m) in subs if bb == b}):
            per_seed, U, Ssum = [], np.zeros(n), np.zeros(n)
            rep = {}
            for s in cfg.seeds:
                if (b, s, m) not in subs:
                    continue
                if m.startswith("NET-U"):
                    th = S.theta_sel_pool(subs[(b, s, m)], cand, std, der, eval_days)
                else:
                    th = S.theta_sel(subs[(b, s, m)], noms[(b, s)], std, der, eval_days)
                if th.get("days", 0) == 0:
                    continue
                per_seed.append(th["theta_sel"])
                ser = th["series"].set_index("i")
                for i, row in ser.iterrows():
                    U[pos[i]] += row["u"] / len(cfg.seeds)
                    Ssum[pos[i]] += row["S"] / len(cfg.seeds)
                for k in ("iota", "theta_PF", "theta_WF", "share_days_S_0_or_K", "submission_coverage", "abstained_mean_rho"):
                    rep.setdefault(k, []).append(th[k])
            if not per_seed:
                continue
            series[m] = (U, Ssum)
            ent = {"theta_sel_seedavg": E.ratio_boot(U, Ssum, idx), "theta_sel_per_seed": per_seed,
                   "theta_sel_seed_mean_sd": [float(np.mean(per_seed)), float(np.std(per_seed, ddof=1)) if len(per_seed) > 1 else None]}
            for k, v in rep.items():
                ent[k] = float(np.nanmean(v))
            if np.isfinite(ent.get("theta_PF", np.nan)) and ent["theta_PF"] > 0:
                ent["Delta_ord_over_theta_PF"] = bound / ent["theta_PF"]
            ob.setdefault("theta_sel", {})[m] = ent
        # ---- psi contrasts (cards C3, C4 and the exploratory ones)
        ref = "LOSS(-Z)"
        for a, name in (("LOSS(+Z_H)", "psi_H"), ("LOSS(+Z_O)", "psi_O"), ("LOSS(+perm Z_H)", "psi_permH"),
                        ("LOSS(+perm Z_O)", "psi_permO"), ("NET-K(+Z_H)", "psi_H_NETK"), ("NET-K(+Z_O)", "psi_O_NETK")):
            r_ = "NET-K(-Z)" if a.startswith("NET-K") else ref
            if a in series and r_ in series:
                ob.setdefault("psi", {})[name] = E.diff_ratio_boot(series[a][0], series[a][1], series[r_][0], series[r_][1], idx)
        if all(m in series for m in ("LOSS(+Z_H+Z_O)", "LOSS(+Z_H)", "LOSS(+Z_O)", ref)):
            (u1, s1), (u2, s2), (u3, s3), (u4, s4) = (series[m] for m in ("LOSS(+Z_H+Z_O)", "LOSS(+Z_H)", "LOSS(+Z_O)", ref))
            est = (u1.sum() / s1.sum() - u2.sum() / s2.sum() - u3.sum() / s3.sum() + u4.sum() / s4.sum())
            boot = (u1[idx].sum(1) / s1[idx].sum(1) - u2[idx].sum(1) / s2[idx].sum(1) - u3[idx].sum(1) / s3[idx].sum(1)
                    + u4[idx].sum(1) / s4[idx].sum(1))
            ob.setdefault("psi", {})["interaction_HO"] = E.summarize(float(est), boot)
        # ---- cards (exploratory read-out of the pre-specified statistics)
        th_ = ob.get("theta_sel", {})
        cards = {}
        for card, m in (("C1", "CONF"), ("C2", "LOSS(-Z)")):
            if m in th_:
                e = th_[m]["theta_sel_seedavg"]
                cards[card] = {"method": m, **e, "tost_vs_Delta_ord": E.tost(e["estimate"], e["se"], bound)}
        for card, k in (("C3", "psi_H"), ("C4", "psi_O")):
            if k in ob.get("psi", {}):
                e = ob["psi"][k]
                cards[card] = {"contrast": k, **e, "p_two_sided": E.two_sided_p(e["estimate"], e["se"])}
        ob["cards_exploratory"] = cards
        # ---- Q-total, attribution, coverage, loss shares, monitoring
        q = ob.setdefault("deployed", {})
        r_by = {}
        for m in methods:
            seeds_r = [(s, runs[(b, s, m)]) for s in cfg.seeds if (b, s, m) in runs]
            if not seeds_r:
                continue
            rs = np.array([(r["W_close"] / r["W_prev"] - 1.0)[ev_mask] for _, r in seeds_r])
            r_by[m] = rs.mean(axis=0)
            ent = {"per_seed": [E.wealth_metrics(x) for x in rs], "seedavg_AR": E.mean_boot(rs.mean(axis=0), idx, E.A)}
            fills = [r["order_totals"] for _, r in seeds_r]
            S_tot = sum(f["S"] for f in fills)
            ent["orders"] = {"S": S_tot, "n": sum(f["n"] for f in fills),
                             "buy_nonfill": merge_counts([f["buy_nonfill"] for f in fills]),
                             "unsubmitted": merge_counts([f["unsubmitted"] for f in fills]),
                             "sell_nonfill": merge_counts([f["sell_nonfill"] for f in fills])}
            n_ev = sum(sum(v for i, v in r["n_by_day"].items() if ev_lo <= i <= ev_hi) for _, r in seeds_r)
            ent["executed_coverage"] = n_ev / (cfg.K * len(eval_days) * len(seeds_r))
            ent["invested_fraction_mean"] = float(np.mean([r["exposure"][ev_mask].mean() for _, r in seeds_r]))
            X1 = np.zeros(n); X2 = np.zeros(n); N1 = np.zeros(n)
            for _, r in seeds_r:
                for i, v in r["n_by_day"].items():
                    if i in pos:
                        N1[pos[i]] += v
                        X1[pos[i]] += r["x1_by_day"].get(i, 0)
                        X2[pos[i]] += r["x2_by_day"].get(i, 0)
            ent["loss_share_O1"] = E.ratio_boot(X1, N1, idx)
            ent["loss_share_O2"] = E.ratio_boot(X2, N1, idx)
            ent["theorem1_per_seed"] = [r["theorem1"] for _, r in seeds_r]
            ent["turnover_and_cost"] = [r["result_record"]["turnover_total"] for _, r in seeds_r]
            q[m] = ent
        for m, rr in r_by.items():
            if m == "G0" or "G0" not in r_by:
                continue
            q[m]["dAR_vs_G0"] = E.mean_boot(rr - r_by["G0"], idx, E.A)
            for comp in ("SCORE", "VT", f"E-const-dev[{m}]"):
                if comp in r_by and comp != m:
                    q[m][f"dAR_vs_{comp}"] = E.mean_boot(rr - r_by[comp], idx, E.A)
        # Lemma 3 attribution against G0, per seed (two intervals per day, wealth-normalised)
        att = {}
        for m in methods:
            if m == "G0" or m.startswith("RND") or m.startswith("tune") or "periods" not in runs.get((b, cfg.seeds[0], m), {}):
                continue
            per = []
            for s in cfg.seeds:
                if (b, s, m) not in runs or (b, s, "G0") not in runs:
                    continue
                G, B0 = runs[(b, s, m)], runs[(b, s, "G0")]
                l3 = AT.lemma3(BT.expand_periods(G["periods"]), BT.expand_periods(B0["periods"]), G["C_norm"], B0["C_norm"])
                T_ = len(eval_days)
                per.append({"exposure_AR": l3["exposure"] * E.A / T_, "composition_AR": l3["composition"] * E.A / T_,
                            "cost_AR": l3["cost"] * E.A / T_, "residual": l3["residual"], "residual_alt": l3["residual_alt"],
                            "zero_baseline_intervals": l3["zero_baseline_intervals"],
                            "sum_terms_minus_return_diff": float(l3["sum_terms"] - np.sum(
                                (G["W_close"] / G["W_prev"] - 1.0)[ev_mask] - (B0["W_close"] / B0["W_prev"] - 1.0)[ev_mask]))})
            if per:
                att[m] = per
        ob["attribution_vs_G0"] = att
    return out


def merge_counts(dicts):
    out = {}
    for d in dicts:
        for k, v in d.items():
            out[k] = out.get(k, 0) + v
    return out


# ====================================================================================== main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-cutoff", required=True, help="no raw row after this date is read (PLAN v0.8 C-8)")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--smoke-n", type=int, default=100)
    ap.add_argument("--out", default="")
    ap.add_argument("--panel-dir", default="")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--bases", default="")
    ap.add_argument("--raw-root", default="", help="tests only: an alternative raw tree (cut-off invariance test)")
    ap.add_argument("--codes-file", default="", help="smoke only: the exact list of names to use")
    ap.add_argument("--gate-rule", default="threshold", choices=("threshold", "fixed_count"))
    ap.add_argument("--keep-awake", action="store_true",
                    help="Windows: ask the system not to idle-sleep while this process runs (released at exit)")
    ap.add_argument("--dump-decisions", action="store_true",
                    help="diagnostics: save daily nominations, every gate's submissions and the base RankIC series")
    ap.add_argument("--stop-after-gates", action="store_true", help="diagnostics: stop after stage 8 (no backtests)")
    ap.add_argument("--reuse-tuning", default="",
                    help="diagnostics: results.json of an earlier identical run; refit only its chosen gate configurations")
    a = ap.parse_args(argv)
    if a.keep_awake and sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    cut = dc.require_cutoff(a.data_cutoff)
    raw = Path(a.raw_root) if a.raw_root else D.RAW
    if a.smoke:
        if a.codes_file:
            codes = [l.strip() for l in open(a.codes_file, encoding="utf-8") if l.strip()]
        else:
            allc, _ = D.pilot_list(PilotConfig(data_cutoff=str(cut)))
            rd = D.readiness(allc)
            codes = list(rd.loc[rd["ready"], "code"])[: a.smoke_n]
        out = a.out or "experiments/results/pilot/smoke"
        cfg = smoke_config(str(cut), tuple(codes), out, a.panel_dir or f"{out}/feature_panel")
    else:
        out = a.out or "experiments/results/pilot/run"
        cfg = PilotConfig(data_cutoff=str(cut), out_dir=out, panel_dir=a.panel_dir or "experiments/data/derived/feature_panel_pilot")
    kw = {"n_jobs": a.jobs, "lgbm_threads": a.threads, "gate_rule": a.gate_rule}
    if a.bases:
        kw["bases"] = tuple(a.bases.split(","))
    from dataclasses import replace
    cfg = replace(cfg, **kw)
    outdir = ROOT / cfg.out_dir
    outdir.mkdir(parents=True, exist_ok=True)
    log = Log(outdir / "logs" / "run.log")
    started = datetime.now().isoformat(timespec="seconds")
    manifest = {"started": started, "argv": sys.argv, "python": platform.python_version(), "config": cfg.to_json(),
                "config_hash": cfg.hash(), "seeds": list(cfg.seeds), "conventions_hash": conventions_hash(),
                "search_spaces_hash": M.spaces_hash(), "code_hash": code_hash(), "data_cutoff": str(cut),
                "raw_root": str(raw)}
    (outdir / "run_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    log(f"run '{cfg.name}' started; data cut-off {cut}; out {outdir}")
    status = "ok"
    try:
        reuse = json.load(open(a.reuse_tuning, encoding="utf-8"))["tuning"] if a.reuse_tuning else None
        res = run(cfg, log, outdir, raw, stop_after="8" if a.stop_after_gates else "",
                  dump_decisions=a.dump_decisions, reuse_tuning=reuse)
    except Exception:
        status = "error"
        res = {"error": traceback.format_exc()}
        log("ERROR\n" + res["error"])
    manifest["finished"] = datetime.now().isoformat(timespec="seconds")
    manifest["status"] = status
    manifest["timing"] = res.get("timing")
    codes_used = list(cfg.codes_subset) if cfg.codes_subset else D.pilot_list(cfg)[0]
    manifest["data_files_sha256"] = data_hashes(codes_used, cut) if raw == D.RAW else "alternative raw tree (test)"
    (outdir / "run_manifest.json").write_text(json.dumps(to_jsonable(manifest), indent=1), encoding="utf-8")
    res["data_cutoff"] = str(cut)
    res["conventions_hash"] = conventions_hash()
    with open(outdir / "results.json", "w", encoding="utf-8") as fh:
        json.dump(to_jsonable(res), fh, indent=1, ensure_ascii=False, default=str)
    log(f"run finished: {status}")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())

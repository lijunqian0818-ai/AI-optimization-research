"""Confirmatory pipeline (amendment v0.9.3, DRAFT; DEVELOPMENT DATA ONLY until the user opens the hold-out).

Copied from pilot/run_pilot.py on 2026-11-17 and extended (every change is marked "confirm:"):
  * standard orders are computed BEFORE the base predictors, additionally for the base tuning years
    (BASE-V needs rho on its validation folds); the pilot range is computed by an identical separate call;
  * BASE-V per base class, BASEV-RERANK and NET-U15(-Z) (A7; plan_review_5 row 2);
  * fixed-count gates fitted through Y-1 (cfg.gate_window), tuned by pooled V (cfg.gate_criterion);
  * Z_O* feature set (LHB + BLK);
  * tuning log per method and trial (configuration, criterion per fold, wall time) -> tuning_matrix.py;
  * decision dump for every policy and seed (submissions with rho and fill flag) -> overlap_diagnostic.py;
  * checkpoints (--resume) for standard orders, base predictors and every (base, gate) tuning task;
  * a hold-out guard: a data cut-off after 2021-12-31 is refused unless --holdout-approved is given.

    experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/run_confirm.py --data-cutoff 2021-12-31 \
        [--smoke --codes-file F] [--n-configs T] [--seeds 0,1,...] [--gate-window y1|y2] [--gate-criterion V|theta_sel]
        [--pilot-compat] [--dump-decisions] [--resume] [--jobs N] [--threads N] [--keep-awake]

Original header of the pilot runner:
  Stages (timed; logged to <out>/logs/run.log): 1 list and readiness; 2 engine market; 3 feature panel;
  4 universe U-LIQ-P and candidate sets; 5 feature rows; 6 standard orders; 7 base predictors (+ BASE-V);
  8 gates; 9 deployment backtests; 10 estimands; 11 results file and run manifest.
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

# confirm (round 2, Q6 / D6): the BLAS / OpenMP thread count is a FIXED configuration value (config.blas_threads,
# default 2; --blas-threads only to reproduce other settings, and recorded).  It is forced (not setdefault) before
# numpy is imported and inherited by worker processes; main() also applies threadpoolctl and records the result.
def _int_from_argv(flag: str, default: int) -> int:
    for k, x in enumerate(sys.argv):
        if x == flag and k + 1 < len(sys.argv):
            return int(sys.argv[k + 1])
        if x.startswith(flag + "="):
            return int(x.split("=", 1)[1])
    return default


BLAS_THREADS = _int_from_argv("--blas-threads", 2)
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = str(BLAS_THREADS)

HERE = Path(__file__).resolve().parent
SRC = HERE.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np          # noqa: E402
import pandas as pd         # noqa: E402

from engine import datacut as dc                         # noqa: E402
from engine.config import conventions_hash               # noqa: E402
from confirm import backtest as BT                         # noqa: E402
from confirm import data as D                              # noqa: E402
from confirm import estimands as E                         # noqa: E402
from confirm import models as M                            # noqa: E402
from confirm import stdorders as SO                        # noqa: E402
from confirm import strategy as S                          # noqa: E402
from confirm.config import (CONFIRM_METHODS, PILOT_METHODS, POOL_METHODS, PRIMARY_CONTRASTS,   # noqa: E402
                            REDUCTIONS, SECONDARY_CONTRASTS, PilotConfig, smoke_config)

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


class Checkpoints:
    """--resume support: pickles of completed units (standard orders, each base predictor, each (base, gate)
    tuning task) under <out>/checkpoints/, keyed by the configuration hash without compute settings and by
    the code hash.  A checkpoint written under another configuration or other code is ignored.  These are
    files written by this program (never third-party data), so pickle is acceptable here."""

    def __init__(self, outdir: Path, cfg, enabled: bool):
        self.dir = outdir / "checkpoints"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.key = cfg.hash_without_compute() + "|" + code_hash()["combined"]
        self.enabled = enabled
        self.loaded: list = []

    def _path(self, name: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in name)
        return self.dir / f"{safe}.pkl"

    def load(self, name: str):
        p = self._path(name)
        if not (self.enabled and p.exists()):
            return None
        with open(p, "rb") as fh:
            key, obj = pickle.load(fh)
        if key != self.key:
            return None
        self.loaded.append(name)
        return obj

    def save(self, name: str, obj) -> None:
        p = self._path(name)
        tmp = p.with_suffix(".tmp")
        with open(tmp, "wb") as fh:
            pickle.dump((self.key, obj), fh, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp, p)


def code_hash() -> dict:
    out, h = {}, hashlib.sha256()
    for sub in ("engine", "features", "confirm"):
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
        dump_decisions: bool = False, reuse_tuning: dict | None = None, resume: bool = False,
        raw_hash: str = "", archive: dict | None = None, tune_only: bool = False) -> dict:
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
    # round 2, D7: the population is the frozen list itself (no file mtimes, no fetch manifest); the raw-file
    # hashes are recorded in the run manifest (main)
    rd = D.frozen_population(codes, raw)
    skipped = rd[~rd["ready"]]
    use = [c for c in codes if c in set(rd.loc[rd["ready"], "code"])]
    res["list"] = linfo
    res["readiness"] = {"n_ready": len(use), "n_skipped": int(len(skipped)),
                        "skipped": skipped.drop(columns=[x for x in ("ready",) if x in skipped.columns]).to_dict("records")}
    res["readiness"]["names_without_bar_file"] = [c for c, b in zip(rd["code"], rd["bar_file"]) if not b]
    log(f"list: {len(codes)} names (frozen list), without bar file {len(res['readiness']['names_without_bar_file'])}")
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
    man, panel_action = D.build_panel_checked(cfg, use, pdir, raw, raw_hash, log)     # round 2, D2
    res["panel_provenance_action"] = panel_action
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
    colsets["Z_O*"] = S.zo_star_columns(colsets["Z_O"])          # confirm: LHB + BLK classes (A4.1 P3)
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

    # ---------------------------------------------------------------- 6 standard orders (confirm: before the base)
    stage("6_standard_orders")
    first_dep = yb_all[cfg.base_deploy_start][0]
    want_basev = any(m in cfg.methods for m in ("BASE-V", "BASEV-RERANK"))
    want_netu15 = "NET-U15(-Z)" in cfg.methods
    ecfg = D.engine_config(cfg)
    ck = Checkpoints(outdir, cfg, enabled=resume)
    std_df = ck.load("standard_orders")
    if std_df is None:
        # the pilot range (first base deployment day .. last decision day), by the same call as the pilot
        asks = {i: list(cand[i]) for i in range(first_dep, last_dec + 1) if i in cand}
        std_df = SO.standard_orders(market, ecfg, asks, market.T - 1, cfg.n_jobs)
        std_df["range"] = "deploy"
        if want_basev or want_netu15:
            # confirm: the days before the first base deployment day - the base validation years (BASE-V) and,
            # round 2, every candidate day from the first feature year (NET-U15 trains on rho); a separate call so
            # that the pilot range is computed exactly as in the pilot
            if want_netu15:
                tdays = [i for i in range(first_i, first_dep) if i in cand]
            else:
                tdays = [i for v in cfg.base_tune_years for i in range(yb_all[v][0], yb_all[v][1] + 1)
                         if i in cand and i < first_dep]
            asks_t = {i: list(cand[i]) for i in tdays}
            if asks_t:
                st = SO.standard_orders(market, ecfg, asks_t, market.T - 1, cfg.n_jobs)
                st["range"] = "pre_deploy"
                std_df = pd.concat([st, std_df], ignore_index=True)
        ck.save("standard_orders", std_df)
    std = {(int(r.i), r.code): {"filled": bool(r.filled), "rho": float(r.rho), "o1": float(r.o1) if r.o1 == r.o1 else np.nan,
                                "exit_i": int(r.exit_i), "unresolved": bool(r.unresolved), "reason": r.reason}
           for r in std_df.itertuples()}
    std_df.to_parquet(outdir / "standard_orders.parquet")
    dep_df = std_df[std_df["range"] == "deploy"]
    res["standard_orders"] = {"n": int(len(dep_df)), "filled": int(dep_df["filled"].sum()),
                              "by_reason": dep_df["reason"].value_counts().to_dict(),
                              "unresolved": int(dep_df["unresolved"].sum()),
                              "o1_outcome": dep_df["o1_outcome"].value_counts().to_dict(),
                              "pre_deploy_range_n": int((std_df["range"] == "pre_deploy").sum())}
    done("6_standard_orders")

    # ---------------------------------------------------------------- 7 base predictors (+ BASE-V, NET-U15) and nominations
    stage("7_base")
    y = S.base_target(fr, der)
    # order outcomes aligned with the feature rows (NaN / False where a row has no standard order)
    key_rows = [(int(i), c) for i, c in zip(fr.day, fr.code)]
    orders = {"rho": np.array([std[k]["rho"] if k in std else np.nan for k in key_rows]),
              "filled": np.array([bool(std[k]["filled"]) if k in std else False for k in key_rows]),
              "exit_i": np.array([int(std[k]["exit_i"]) if k in std else -1 for k in key_rows]),
              "unresolved": np.array([bool(std[k]["unresolved"]) if k in std else False for k in key_rows])}
    # round 2: the base predictor, BASE-V and NET-U15 use the -Z feature set (B0 + R; amendment A7).  The pilot's
    # base_scores used fr.X, i.e. all columns INCLUDING Z_H and Z_O (cfg.base_features = "all" reproduces it).
    minus_z_idx = [fr.cols.index(c_) for c_ in colsets["-Z"]]
    base_cols = np.arange(len(fr.cols)) if cfg.base_features == "all" else np.array(minus_z_idx)
    bases, basev, model_recs = {}, {}, {}
    for b in cfg.bases:
        got = ck.load(f"base_{b}")
        if got is None:
            fx = arch_get(archive, f"base|{b}", M.draw_configs("lgbm" if b == "lgbm" else "linear", cfg.n_configs),
                          ("rank_ic", "V") if want_basev else ("rank_ic",)) if archive is not None else None
            out_b, out_v, rec = S.base_scores(fr, y, days, cfg, b, cfg.seeds, log, orders=orders, want_basev=want_basev,
                                              col_idx=base_cols, fixed=fx, workers=cfg.base_workers)
            got = (out_b, out_v, {"confs": rec["confs"], "chosen": rec["chosen"], "tuning": rec["tuning"]})
            ck.save(f"base_{b}", got)
        else:
            log(f"[base {b}] loaded from checkpoint")
        bases[b], basev[b], model_recs[f"base|{b}"] = got
    netu15 = None
    if want_netu15:
        got = ck.load("netu15")
        dep_years_n = list(cfg.gate_tune_years) + list(cfg.eval_years)
        if got is None:
            fx = arch_get(archive, "netu15", M.draw_configs("lgbm", cfg.n_configs), ("V",)) if archive is not None else None
            out_n, rec = S.netu15_scores(fr, days, cfg, cfg.seeds, log, orders, np.array(minus_z_idx), dep_years_n,
                                         fixed=fx, workers=cfg.base_workers)
            got = (out_n, {"confs": rec["confs"], "chosen": rec["chosen"], "tuning": rec["tuning"]})
            ck.save("netu15", got)
        else:
            log("[NET-U15] loaded from checkpoint")
        netu15, model_recs["netu15"] = got
    noms, ktr = {}, {}
    for b in cfg.bases:
        for s in cfg.seeds:
            rk = bases[b][s]["rank"]
            noms[(b, s)] = {i: v for i, v in S.nominations(fr, rk, cand, cfg.K, first_dep).items() if i <= last_dec}
            ktr[(b, s)] = {i: v for i, v in S.nominations(fr, rk, cand, cfg.K_tr, first_dep).items() if i <= last_dec}
    res["base"] = {b: {"chosen": bases[b][cfg.seeds[0]]["config"], "tuning": bases[b][cfg.seeds[0]]["tuning"],
                       "feature_columns": int(len(base_cols))} for b in cfg.bases}
    if want_basev:
        res["base_v"] = {b: {"chosen": basev[b][cfg.seeds[0]]["config"], "chosen_index": basev[b][cfg.seeds[0]]["chosen_index"],
                             "same_configuration_as_base": basev[b][cfg.seeds[0]]["chosen_index"] == bases[b][cfg.seeds[0]]["chosen_index"]}
                         for b in cfg.bases}
    if netu15 is not None:
        res["netu15"] = {"chosen": netu15[cfg.seeds[0]]["config"], "chosen_index": netu15[cfg.seeds[0]]["chosen_index"],
                         "feature_columns": len(minus_z_idx), "validation_years": list(cfg.base_tune_years)}
    res["base_deploy_fits"] = {f"{b}|{s}": bases[b][s].get("deploy_fits") for b in cfg.bases for s in cfg.seeds}
    res["nominations_fewer_than_K_days"] = {f"{b}|{s}": int(sum(len(v) < cfg.K for v in noms[(b, s)].values()))
                                            for b in cfg.bases for s in cfg.seeds}
    done("7_base")

    # ---------------------------------------------------------------- 8 gates
    stage("8_gates")
    yb = yb_all
    tune_days = [i for v in cfg.gate_tune_years for i in range(yb[v][0], min(yb[v][1], last_dec) + 1)]
    eval_days = [i for v in cfg.eval_years for i in range(yb[v][0], min(yb[v][1], last_dec) + 1)]
    dep_years = list(cfg.gate_tune_years) + list(cfg.eval_years)
    # round 2: NET-U15 is no longer a gate (stage 7); the tuned "+perm" gates of the pilot are only run when
    # they are listed (pilot-compat); the A4.3 item 6 follow-up draws are generated below
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
    # the pilot's single cached permutation draw (tuned "+perm" gates, pilot-compat only), made before any thread
    if any("+perm" in m and "#" not in m for m in learned):
        for ctx in ctxs.values():
            for grp in ("Z_H", "Z_O", "Z_O*"):
                ctx._permuted(np.zeros(0, dtype=int), grp)

    # BASE-V, BASEV-RERANK, NET-U15 (no tuning here: they were tuned in stage 7)
    dep_days = {(b, s): [i for Y in dep_years for i in range(yb[Y][0], yb[Y][1] + 1) if i in noms[(b, s)]]
                for b in cfg.bases for s in cfg.seeds}
    policy_flags = {}

    def model_log(key, crit_key, crit_name, note=""):
        rec = model_recs[key]
        tb = rec["tuning"] or []
        return {"criterion": crit_name, "configs": rec["confs"], "trials": tb,
                "criterion_values": [t.get({"rank_ic": "mean_rank_ic", "V": "criterion_V"}[crit_key]) for t in tb] or None,
                "chosen": rec["chosen"][crit_key], "loaded_from_archive": rec["tuning"] is None, "note": note}
    for b in cfg.bases:
        tuning_log[(b, "BASE")] = model_log(f"base|{b}", "rank_ic", "mean validation RankIC")
        tuning_log[(b, "BASE")]["deploy_seconds"] = [bases[b][s].get("deploy_seconds") for s in cfg.seeds]
        if want_basev:
            tuning_log[(b, "BASE-V")] = model_log(f"base|{b}", "V", "V", "same validation fits as BASE")
            tuning_log[(b, "BASE-V")]["deploy_seconds"] = [basev[b][s].get("deploy_seconds") for s in cfg.seeds]
        if netu15 is not None:
            tuning_log[(b, "NET-U15(-Z)")] = model_log("netu15", "V", "V",
                                                       "end-to-end model shared by both bases (no base input)")
            tuning_log[(b, "NET-U15(-Z)")]["deploy_seconds"] = [netu15[s].get("deploy_seconds") for s in cfg.seeds]
        for s in cfg.seeds:
            if want_basev:
                sc_v = basev[b][s]["score"]
                if "BASE-V" in cfg.methods:
                    subs[(b, s, "BASE-V")], nb1 = S.basev_subs(fr, sc_v, cand, dep_days[(b, s)], cfg.c, cfg.K,
                                                               cfg.failed_score)
                    policy_flags[f"{b}|{s}|BASE-V"] = {"failed_scores": nb1}
                if "BASEV-RERANK" in cfg.methods:
                    subs[(b, s, "BASEV-RERANK")], nb2 = S.rerank_subs(fr, sc_v, noms[(b, s)], dep_days[(b, s)], cfg.c,
                                                                      cfg.K, cfg.failed_score)
                    policy_flags[f"{b}|{s}|BASEV-RERANK"] = {"failed_scores": nb2}
            if netu15 is not None:
                subs[(b, s, "NET-U15(-Z)")], nb3 = S.basev_subs(fr, netu15[s]["score"], cand, dep_days[(b, s)], cfg.c,
                                                                cfg.K, cfg.failed_score)
                policy_flags[f"{b}|{s}|NET-U15(-Z)"] = {"failed_scores": nb3}

    def criterion_of(m):
        fam, _fs, thr_, _d = S.GateContext.parse_method(m)
        if cfg.gate_rule == "fixed_count" and not thr_ and fam in ("LOSS", "LOSS-LR", "NET-K") and cfg.gate_criterion == "V":
            return "V"
        return "theta_sel"

    def fold_stats(b, s, m, sub, v, conf):
        """Criterion values of one (seed, tuning year) fold.  Round 2, D4: only orders resolved before the first
        decision day of v + 1 enter (the submitted set and, for theta_sel, the nomination pool are filtered);
        the dropped orders are counted."""
        dr = [i for i in range(yb[v][0], min(yb[v][1], last_dec) + 1)]
        lo_next = yb[v + 1][0] if (v + 1) in yb else market.T
        pool_src = cand if m in POOL_METHODS else noms[(b, s)]

        def ok(i, c_):
            r_ = std[(i, c_)]
            return (not r_["filled"]) or ((not r_["unresolved"]) and 0 <= r_["exit_i"] < lo_next)
        drop_sub = drop_pool = 0
        if cfg.criterion_resolved_only:
            sub_f, pool_f = {}, {}
            for i in dr:
                if i in sub:
                    names, sc_ = sub[i]
                    keep = {c_ for c_ in names if ok(i, c_)}
                    drop_sub += len(names) - len(keep)
                    sub_f[i] = (keep, sc_)
                if pool_src.get(i):
                    pk = [c_ for c_ in pool_src[i] if ok(i, c_)]
                    drop_pool += len(pool_src[i]) - len(pk)
                    pool_f[i] = pk
        else:
            sub_f, pool_f = sub, pool_src
        th = S.theta_sel(sub_f, pool_f, std, der, dr)
        num, den, nd = S.v_parts(sub_f, std, dr)
        fi = ctxs[(b, s)].fit_info.get((m, v, S.json_key(conf)), {})
        return {"seed": s, "year": v, "V_num": num, "V_den": den, "V": S.pooled_V(num, den)[0], "days": nd,
                "theta_sel": th.get("theta_sel", np.nan), "S_total_theta": th.get("S_total", 0),
                "dropped_unresolved_submitted": drop_sub, "dropped_unresolved_pool": drop_pool,
                "fit_failed": bool(fi.get("failed", False)), "train_rows": fi.get("rows"),
                "train_last_row_day": fi.get("last_row_day"), "label_known_before": fi.get("label_known_before"),
                "window": fi.get("window"), "logit_converged": fi.get("logit_converged"),
                "logit_n_iter": fi.get("logit_n_iter")}

    def learn(b, m, kind):
        confs = M.draw_configs(kind, cfg.n_configs)
        got = ck.load(f"gate_{b}_{m}")
        if got is not None:
            tl, out, fails, fsc = got
            for s in cfg.seeds:
                ctxs[(b, s)].failures.extend(fails.get(s, []))
                if fsc.get(s):
                    ctxs[(b, s)].failed_scores[m] = fsc[s]
            tl["loaded_from_checkpoint"] = True
            return b, m, tl, out
        fixed_k = None
        if archive is not None:                                    # D1: --load-tuning, no tuning fit
            fixed_k = arch_get(archive, f"gate|{b}|{m}", confs, None)
        elif reuse_tuning is not None:
            prev = reuse_tuning[f"{b}|{m}"]
            if to_jsonable(prev["configs"]) != to_jsonable(confs):
                raise RuntimeError(f"reuse-tuning: configurations of {b}|{m} differ from the earlier run")
            fixed_k = int(prev["chosen"])
        if fixed_k is not None:
            out, dep_fits = {}, []
            for s in cfg.seeds:
                sub = {}
                for Y in list(cfg.gate_tune_years) + list(cfg.eval_years):
                    sub.update(ctxs[(b, s)].gate_year(m, confs[fixed_k], Y))
                    dep_fits.append({"seed": s, "year": Y, **ctxs[(b, s)].fit_info.get((m, Y, S.json_key(confs[fixed_k])), {})})
                out[s] = sub
            tl = {"criterion": criterion_of(m), "configs": confs, "criterion_values": None, "chosen": fixed_k,
                  "loaded_from_archive": archive is not None, "reused": reuse_tuning is not None, "deploy_fits": dep_fits}
            return b, m, tl, out
        crit_name = criterion_of(m)
        fits, crit, trials = {}, [], []
        for k, conf in enumerate(confs):
            t0 = time.time()
            folds = []
            for s in cfg.seeds:
                for v in cfg.gate_tune_years:
                    sub = ctxs[(b, s)].gate_year(m, conf, v)
                    fits[(k, s, v)] = sub
                    folds.append(fold_stats(b, s, m, sub, v, conf))
            vps = {}
            for s in cfg.seeds:
                nn = sum(f["V_num"] for f in folds if f["seed"] == s)
                dd_ = sum(f["V_den"] for f in folds if f["seed"] == s)
                vps[s] = S.pooled_V(nn, dd_)
            any_fail = any(f["fit_failed"] for f in folds)
            zero_sub = any(fl for _, fl in vps.values())
            ths = [f["theta_sel"] for f in folds]
            th_rep = float(np.nanmean(ths)) if np.isfinite(ths).any() else -np.inf
            v_rep = float(np.mean([v_[0] for v_ in vps.values()]))
            excluded = any_fail or zero_sub                               # round 2, Q3
            v_crit = -np.inf if excluded else v_rep
            th_crit = -np.inf if excluded else th_rep
            crit.append(v_crit if crit_name == "V" else th_crit)
            trials.append({"config": conf, "folds": folds, "V_pooled_by_seed": {str(s): v_[0] for s, v_ in vps.items()},
                           "V_zero_submission_flag": zero_sub, "any_fit_failed": any_fail,
                           "criterion_V": v_crit, "criterion_V_reported": v_rep,
                           "criterion_theta_sel": th_crit, "criterion_theta_sel_reported": th_rep,
                           "dropped_unresolved_submitted": int(sum(f["dropped_unresolved_submitted"] for f in folds)),
                           "seconds": round(time.time() - t0, 2)})
        best = max(range(len(confs)), key=lambda k: (crit[k], -k))
        out, dep_fits = {}, []
        t0 = time.time()
        for s in cfg.seeds:
            sub = {}
            for v in cfg.gate_tune_years:
                sub.update(fits[(best, s, v)])
            for Y in cfg.eval_years:
                sub.update(ctxs[(b, s)].gate_year(m, confs[best], Y))
                fi = ctxs[(b, s)].fit_info.get((m, Y, S.json_key(confs[best])), {})
                dep_fits.append({"seed": s, "year": Y, **fi})
            out[s] = sub
        tl = {"criterion": crit_name, "configs": confs, "criterion_values": crit, "chosen": best, "trials": trials,
              "deploy_fits": dep_fits, "deploy_seconds": round(time.time() - t0, 2)}
        fails = {s: [f for f in ctxs[(b, s)].failures if f["method"] == m] for s in cfg.seeds}
        fsc = {s: ctxs[(b, s)].failed_scores.get(m, 0) for s in cfg.seeds}
        ck.save(f"gate_{b}_{m}", (tl, out, fails, fsc))
        return b, m, tl, out

    from concurrent.futures import ThreadPoolExecutor
    tasks = [(b, m, kind) for b in cfg.bases for m, kind in learned.items()]
    with ThreadPoolExecutor(max_workers=max(1, cfg.n_jobs)) as ex:      # LightGBM / numpy release the GIL
        for b, m, tl, out in ex.map(lambda t: learn(*t), tasks):
            tuning_log[(b, m)] = tl
            for s, sub in out.items():
                subs[(b, s, m)] = sub
            log(f"[gates {b}] {m}: tuned over {len(tl['configs'])} configurations")

    # round 2: A4.3 item 6 follow-up - for each group G of cfg.perm_groups, perm_draws draws per seed of the LOSS
    # gate with G permuted ("+perm G") and with G replaced by standard-normal columns ("+noise G"), each refitted
    # on the evaluation years at the configuration chosen for the real gate LOSS(+G) (no tuning).
    perm_tasks = []
    if cfg.perm_draws > 0 and not tune_only:
        for b in cfg.bases:
            for g in cfg.perm_groups:
                real = f"LOSS(+{g})"
                if (b, real) not in tuning_log:
                    continue
                for kind_ in ("perm", "noise"):
                    perm_tasks.append((b, g, kind_, real))

    def follow_up(t):
        b, g, kind_, real = t
        tl = tuning_log[(b, real)]
        conf = tl["configs"][tl["chosen"]]
        res_ = {}
        t0 = time.time()
        for d in range(cfg.perm_draws):
            name = f"LOSS(+{kind_} {g})#{d}"
            for s in cfg.seeds:
                sub = {}
                for Y in cfg.eval_years:
                    sub.update(ctxs[(b, s)].gate_year(name, conf, Y))
                res_[(s, name)] = sub
                ctxs[(b, s)].drop_draw(g, kind_, d)
        return b, g, kind_, real, res_, round(time.time() - t0, 1)
    if perm_tasks:
        with ThreadPoolExecutor(max_workers=max(1, cfg.n_jobs)) as ex:
            for b, g, kind_, real, res_, sec in ex.map(follow_up, perm_tasks):
                for (s, name), sub in res_.items():
                    subs[(b, s, name)] = sub
                tuning_log[(b, f"follow-up {kind_} {g}")] = {
                    "criterion": "none (configuration of the real gate)", "configs": [tuning_log[(b, real)]["configs"][tuning_log[(b, real)]["chosen"]]],
                    "chosen": 0, "real_gate": real, "draws": cfg.perm_draws, "seconds": sec}
                log(f"[follow-up {b}] {kind_} {g}: {cfg.perm_draws} draws x {len(cfg.seeds)} seeds refitted ({sec} s)")
    res["gate_failures"] = {f"{b}|{s}": ctxs[(b, s)].failures for b in cfg.bases for s in cfg.seeds}
    res["failed_scores"] = {f"{b}|{s}": ctxs[(b, s)].failed_scores for b in cfg.bases for s in cfg.seeds}
    res["policy_flags"] = policy_flags
    # round 2, Q6: convergence of every logistic fit
    lg = [(m_, fi_) for ctx in ctxs.values() for (m_, _Y, _c), fi_ in ctx.fit_info.items() if "logit_converged" in fi_]
    res["logit_convergence"] = {"fits": len(lg), "not_converged": int(sum(1 for _, fi_ in lg if not fi_["logit_converged"])),
                                "max_n_iter": int(max((fi_["logit_n_iter"] for _, fi_ in lg), default=0)),
                                "max_iter": int(max((fi_["logit_max_iter"] for _, fi_ in lg), default=0))}
    # days on which the policies of the primary family differ in their submitted count
    cnt = {}
    for (b, s, m), sub in subs.items():
        for i, (names, _sc) in sub.items():
            cnt.setdefault((b, s, i), {})[m] = len(names)
    prim = ("SCORE", "LOSS(-Z)", "LOSS(+Z_H)", "LOSS(+Z_O*)", "NET-K(-Z)", "BASE-V")
    res["days_with_unequal_counts_primary"] = {
        b: int(sum(1 for (bb, s, i), d in cnt.items() if bb == b and len({d[m] for m in prim if m in d}) > 1))
        for b in cfg.bases}
    res["zero_submission_policies"] = sorted({f"{b}|{s}|{m}" for (b, s, m), sub in subs.items()
                                              if sum(len(n) for n, _ in sub.values()) == 0})
    res["tuning"] = {f"{b}|{m}": v for (b, m), v in tuning_log.items()}
    done("8_gates")

    def write_dump_submissions(subs_):
        """Every policy's submissions with rho, fill flag and scale (confirm); decision days incl. zero-submission
        days.  Written after stage 8 (selection policies) and again after stage 9 (all policies, incl. TREND,
        PERF, VT, E-const-dev and RND, which are defined there)."""
        rows_ = []
        for (b_, s_, m_), sub_ in sorted(subs_.items(), key=lambda kv: kv[0]):
            nm_ = noms[(b_, s_)]
            for i_, (names_, sc_) in sorted(sub_.items()):
                inn_ = set(nm_.get(i_, ()))
                for c_ in sorted(names_):
                    st2 = std[(i_, c_)]
                    rows_.append((b_, s_, m_, int(i_), days[i_].isoformat(), c_, st2["rho"], st2["filled"], c_ in inn_,
                                  len(names_), float(sc_)))
        pd.DataFrame(rows_, columns=["base", "seed", "method", "i", "date", "code", "rho", "filled", "in_nominations",
                                     "S_day", "scale"]).to_parquet(outdir / "submissions.parquet")
        rows_ = [(b_, s_, m_, int(i_), len(names_)) for (b_, s_, m_), sub_ in subs_.items() for i_, (names_, _sc) in sub_.items()]
        pd.DataFrame(rows_, columns=["base", "seed", "method", "i", "S_day"]).to_parquet(outdir / "decision_days.parquet")

    if dump_decisions:
        # decision dump for every policy and seed (confirm: submissions carry rho and the fill flag)
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
        write_dump_submissions(subs)
        rows = []
        for b in cfg.bases:
            for s in cfg.seeds:
                ic = M.spearman_by_day(fr.day, bases[b][s]["score"], der_fwd_rows(fr, der))
                rows += [(b, s, int(i), days[int(i)].isoformat(), float(v)) for i, v in ic.items()]
        pd.DataFrame(rows, columns=["base", "seed", "i", "date", "rank_ic"]).to_parquet(outdir / "base_ic.parquet")
        (outdir / "dump_meta.json").write_text(json.dumps({
            "gate_tune_years": list(cfg.gate_tune_years), "eval_years": list(cfg.eval_years),
            "seeds": list(cfg.seeds), "bases": list(cfg.bases),
            "year_first_last_i": {str(Y): list(yb[Y]) for Y in dep_years}, "last_decision_i": int(last_dec),
            "primary_contrasts": [list(x) for x in PRIMARY_CONTRASTS],
            "secondary_contrasts": [list(x) for x in SECONDARY_CONTRASTS]}, indent=1), encoding="utf-8")
        log("decisions dumped: nominations, submissions, decision_days, base_ic, dump_meta")
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
            if archive is not None:                        # D1: loaded, no tuning backtest
                continue
            for k, conf in enumerate(confs):
                for s in cfg.seeds:
                    sub = grid_sub(m, conf, b, s, tu_lo, tu_hi)
                    jobs.append((plan_of(sub, tu_lo, tu_hi, noms[(b, s)]), tu_lo, min(tu_hi + cfg.H + 10, sim_hi),
                                 tu_lo, tu_hi, f"tune|{b}|{m}|{k}|{s}", cfg.delta_mon, False))
                    keys.append((b, m, k, s))
    t_tune = time.time()
    tune_res = BT.run_many(market, ecfg, jobs, cfg.n_jobs) if jobs else []
    tune_seconds = round(time.time() - t_tune, 1)
    ar_of = {}
    for b in cfg.bases:
        for m in grid_methods:
            confs = M.draw_configs(m.lower(), cfg.n_configs)
            if archive is not None:
                best = arch_get(archive, f"grid|{b}|{m}", confs, None)
                tuning_log[(b, m)] = {"criterion": "mean AR over tuning years x seeds", "configs": confs,
                                      "criterion_values": None, "chosen": best, "loaded_from_archive": True}
                for s in cfg.seeds:
                    subs[(b, s, m)] = grid_sub(m, confs[best], b, s, sim_lo, last_dec)
                continue
            crit = []
            for k in range(len(confs)):
                ars = []
                for (bb, mm, kk, s), r in zip(keys, tune_res):
                    if (bb, mm, kk) == (b, m, k):
                        W, Wp = r["W_close"], r["W_prev"]
                        rr = (W / Wp - 1.0)[: tu_hi - tu_lo + 1]
                        ars.append(E.wealth_metrics(rr)["AR"])
                        ar_of[(bb, mm, kk, s)] = ars[-1]
                crit.append(float(np.mean(ars)))
            best = max(range(len(confs)), key=lambda k: (crit[k], -k))
            tuning_log[(b, m)] = {"criterion": "mean AR over tuning years x seeds", "configs": confs,
                                  "criterion_values": crit, "criterion_mean_AR": crit, "chosen": best,
                                  "trials": [{"config": confs[k], "AR_by_seed": {str(s): ar_of.get((b, m, k, s))
                                                                                  for s in cfg.seeds},
                                              "seconds": None} for k in range(len(confs))],
                                  "batch_seconds": tune_seconds}
            for s in cfg.seeds:
                subs[(b, s, m)] = grid_sub(m, confs[best], b, s, sim_lo, last_dec)

    # main runs (round 2, --tune-only: only G0, which VT's sigma* needs)
    main_methods = [m for m in cfg.methods if m != "VT"] if not tune_only else ["G0"]
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
    sstars = {}
    for b in cfg.bases:
        for s in cfg.seeds:
            g0 = runs[(b, s, "G0")]
            r0 = g0["W_close"] / g0["W_prev"] - 1.0
            sig = pd.Series(r0).rolling(60, min_periods=60).std().shift(1).to_numpy()     # through t-1
            dd = np.arange(sim_lo, sim_hi + 1)
            if archive is not None:                               # D1: sigma* loaded, not re-tuned
                sstar = float(arch_get(archive, f"vt|{b}|{s}", None, None))
            else:
                tmask = (dd >= tu_lo) & (dd <= tu_hi) & np.isfinite(sig)
                lo_s, hi_s = 1e-8, 1.0
                for _ in range(80):                               # sigma*: mean s_t = c on the tuning days
                    mid = 0.5 * (lo_s + hi_s)
                    if np.mean(np.minimum(1.0, mid / sig[tmask])) < cfg.c:
                        lo_s = mid
                    else:
                        hi_s = mid
                sstar = 0.5 * (lo_s + hi_s)
            sstars[(b, s)] = sstar
            if tune_only:
                continue
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
    # round 2, D1: the archive of every chosen configuration (and sigma*), written by every tuning run
    if archive is None:
        res["tuning_archive"] = write_archive(outdir, cfg, model_recs, tuning_log, sstars)
        log(f"tuning archive written: sha256 {res['tuning_archive']['sha256']}")
    else:
        res["tuning_archive"] = {"loaded": True, "sha256": archive["_sha256"], "used_keys": sorted(archive["_used"]),
                                 "unused_keys": sorted(set(archive["entries"]) - archive["_used"])}
    if tune_only:
        done("9_backtests")
        res["timing"] = timing
        res["tune_only"] = True
        return res
    log(f"second-stage backtests: {len(jobs)} runs")
    runs.update(dict(zip(keys, BT.run_many(market, ecfg, jobs, cfg.n_jobs))))
    done("9_backtests")
    if dump_decisions:
        write_dump_submissions(subs)          # confirm: now with every policy of the run
        log("decisions dumped again after stage 9 (all policies)")

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


# ====================================================================================== round 2, D1: tuning archive
ARCHIVE_NAME = "tuning_archive.json"
TUNING_CUTOFF = "2021-12-31"
GATE_FAMS = ("LOSS", "LOSS-LR", "NET-K", "NET-U")


def required_archive_keys(cfg) -> list:
    """Every tuned unit a run of this configuration needs (completeness check of --load-tuning)."""
    keys = [f"base|{b}" for b in cfg.bases]
    if "NET-U15(-Z)" in cfg.methods:
        keys.append("netu15")
    for b in cfg.bases:
        for m in cfg.methods:
            if S.GateContext.parse_method(m)[0] in GATE_FAMS and "(" in m:
                keys.append(f"gate|{b}|{m}")
            if m in ("TREND", "PERF"):
                keys.append(f"grid|{b}|{m}")
        for s in cfg.seeds:
            keys.append(f"vt|{b}|{s}")
    return keys


def write_archive(outdir: Path, cfg, model_recs: dict, tuning_log: dict, sstars: dict) -> dict:
    """Chosen configurations of every hyperparameter search of the run (with the full configuration lists, so
    that a loading run can assert equality) and VT's sigma*; canonical JSON, SHA-256 in a side file."""
    ent = {}
    for key, rec in model_recs.items():
        ent[key] = {"configs": rec["confs"], "chosen": {k: int(v) for k, v in rec["chosen"].items()}}
    for (b, m), tl in tuning_log.items():
        fam = S.GateContext.parse_method(m)[0] if "(" in m else m
        if fam in GATE_FAMS and "(" in m:
            ent[f"gate|{b}|{m}"] = {"configs": tl["configs"], "chosen": int(tl["chosen"]), "criterion": tl["criterion"]}
        elif m in ("TREND", "PERF"):
            ent[f"grid|{b}|{m}"] = {"configs": tl["configs"], "chosen": int(tl["chosen"])}
    for (b, s), x in sstars.items():
        ent[f"vt|{b}|{s}"] = {"sigma_star": float(x)}
    obj = {"format": "confirm tuning archive v1", "data_cutoff": str(cfg.cut()), "tuning_spec": to_jsonable(cfg.tuning_spec()),
           "tuning_spec_hash": cfg.tuning_spec_hash(), "code_hash": code_hash()["combined"],
           "created": datetime.now().isoformat(timespec="seconds"), "entries": to_jsonable(ent)}
    blob = json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False).encode("utf-8")
    sha = hashlib.sha256(blob).hexdigest()
    (outdir / ARCHIVE_NAME).write_bytes(blob)
    (outdir / (ARCHIVE_NAME + ".sha256")).write_text(sha + "\n", encoding="utf-8")
    missing = [k for k in required_archive_keys(cfg) if k not in ent]
    return {"path": str(outdir / ARCHIVE_NAME), "sha256": sha, "entries": len(ent), "missing_required": missing}


def load_archive(path: Path, cfg, expect_sha: str = "") -> dict:
    """Load and verify an archive: SHA-256 (side file, and --tuning-sha if given), tuning at cut-off 2021-12-31,
    the same tuning spec and code hash as this run, and every required unit present.  Raises otherwise."""
    blob = Path(path).read_bytes()
    sha = hashlib.sha256(blob).hexdigest()
    side = Path(str(path) + ".sha256")
    if not side.exists() or side.read_text(encoding="utf-8").strip() != sha:
        raise RuntimeError(f"tuning archive {path}: SHA-256 {sha} does not match its side file")
    if expect_sha and expect_sha != sha:
        raise RuntimeError(f"tuning archive {path}: SHA-256 {sha} differs from --tuning-sha {expect_sha}")
    obj = json.loads(blob.decode("utf-8"))
    if obj.get("data_cutoff") != TUNING_CUTOFF:
        raise RuntimeError(f"tuning archive was made at cut-off {obj.get('data_cutoff')}, not {TUNING_CUTOFF}")
    if obj.get("tuning_spec_hash") != cfg.tuning_spec_hash():
        a, b = obj.get("tuning_spec", {}), to_jsonable(cfg.tuning_spec())
        diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        raise RuntimeError(f"tuning archive: tuning spec differs from this run in {diff}")
    if obj.get("code_hash") != code_hash()["combined"]:
        raise RuntimeError("tuning archive: written by different code (code hash differs)")
    missing = [k for k in required_archive_keys(cfg) if k not in obj["entries"]]
    if missing:
        raise RuntimeError(f"tuning archive incomplete: {missing}")
    obj["_sha256"] = sha
    obj["_used"] = set()
    return obj


def arch_get(archive: dict, key: str, confs, crit_keys):
    """The archived choice of one tuned unit; asserts that the configuration list equals this run's draws.
    crit_keys: tuple -> {criterion: index}; None -> index (or sigma* for 'vt|...')."""
    if key not in archive["entries"]:
        raise RuntimeError(f"--load-tuning: no archived choice for {key}; the run refuses to re-tune")
    e = archive["entries"][key]
    archive["_used"].add(key)
    if key.startswith("vt|"):
        return e["sigma_star"]
    if confs is not None and to_jsonable(e["configs"]) != to_jsonable(confs):
        raise RuntimeError(f"--load-tuning: configuration list of {key} differs from this run's draws")
    if crit_keys is None:
        return int(e["chosen"])
    ch = e["chosen"]
    if any(k not in ch for k in crit_keys):
        raise RuntimeError(f"--load-tuning: {key} lacks the choice for {crit_keys}")
    return {k: int(ch[k]) for k in crit_keys}


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
    out = {"note": "development-period run of the confirmatory code; development data were seen in the pilot "
                   "(amendment A8 item 2), so nothing here is confirmatory evidence"}
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
        for m in sorted({m for (bb, s, m) in subs if bb == b and "#" not in m}):     # follow-up draws: V only
            per_seed, U, Ssum = [], np.zeros(n), np.zeros(n)
            rep = {}
            for s in cfg.seeds:
                if (b, s, m) not in subs:
                    continue
                if m in POOL_METHODS:          # confirm: every policy that picks from C_t (NET-U, NET-U15, BASE-V)
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
        # ---- confirm: direct policy value V (A3.1) and the contrasts of A4.1 (marginal bootstrap only; the
        # simultaneous intervals of A4.1 are computed elsewhere, after the freeze)
        vser = {}
        for m in sorted({m for (bb, s, m) in subs if bb == b}):
            num, den = np.zeros(n), np.zeros(n)
            for s in cfg.seeds:
                sub = subs.get((b, s, m))
                if sub is None:
                    continue
                for i in eval_days:
                    if i in sub:
                        names = sorted(sub[i][0])
                        num[pos[i]] += sum(std[(i, c)]["rho"] for c in names) / len(cfg.seeds)
                        den[pos[i]] += len(names) / len(cfg.seeds)
            vser[m] = (num, den)
            Vv, flag = S.pooled_V(num.sum(), den.sum())
            ob.setdefault("V", {})[m] = {**E.ratio_boot(num, den, idx), "estimate": Vv, "zero_submissions": flag,
                                         "S_total_seedavg": float(den.sum())}
        for cid, g, h in list(PRIMARY_CONTRASTS) + list(SECONDARY_CONTRASTS):
            if g in vser and h in vser:
                e = E.diff_ratio_boot(vser[g][0], vser[g][1], vser[h][0], vser[h][1], idx)
                e["equal_daily_counts"] = bool(np.allclose(vser[g][1], vser[h][1]))
                ob.setdefault("delta", {})[f"{cid}: {g} - {h}"] = e
        # round 2: A4.3 item 6 follow-up (point estimates on the evaluation window; descriptive)
        BPx = 1e4

        def dlt(g, h):
            return (vser[g][0].sum() / vser[g][1].sum() - vser[h][0].sum() / vser[h][1].sum()) * BPx                 if vser[g][1].sum() and vser[h][1].sum() else None
        for g_ in cfg.perm_groups:
            real = f"LOSS(+{g_})"
            if real not in vser or "LOSS(-Z)" not in vser:
                continue
            fu = {"delta_real_minus_noZ_bp": dlt(real, "LOSS(-Z)")}
            for kind_ in ("perm", "noise"):
                names = [m for m in vser if m.startswith(f"LOSS(+{kind_} {g_})#")]
                if not names:
                    continue
                a_ = np.array([dlt(m, "LOSS(-Z)") for m in names], dtype=float)
                r_ = np.array([dlt(real, m) for m in names], dtype=float)
                fu[kind_] = {"draws": len(names),
                             "delta_draw_minus_noZ_bp": {"mean": float(np.mean(a_)), "sd": float(np.std(a_, ddof=1)) if len(a_) > 1 else None,
                                                         "min": float(np.min(a_)), "max": float(np.max(a_))},
                             "delta_real_minus_draw_bp": {"mean": float(np.mean(r_)), "sd": float(np.std(r_, ddof=1)) if len(r_) > 1 else None,
                                                          "min": float(np.min(r_)), "max": float(np.max(r_))}}
            ob.setdefault("follow_up_A4_3_item6", {})[g_] = fu
        # ---- psi contrasts (cards C3, C4 and the exploratory ones)
        ref = "LOSS(-Z)"
        for a, name in (("LOSS(+Z_H)", "psi_H"), ("LOSS(+Z_O)", "psi_O"), ("LOSS(+perm Z_H)", "psi_permH"),
                        ("LOSS(+perm Z_O)", "psi_permO"), ("NET-K(+Z_H)", "psi_H_NETK"), ("NET-K(+Z_O)", "psi_O_NETK"),
                        ("LOSS(+Z_O*)", "psi_Ostar"), ("LOSS(+perm Z_O*)", "psi_permOstar"),
                        ("NET-K(+Z_O*)", "psi_Ostar_NETK"), ("LOSS(+Z_H+Z_O*)", "psi_HOstar")):
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
HOLDOUT_START = "2022-01-01"


def _split_methods(s: str) -> tuple:
    """Methods contain commas only never; they contain '+', '(' and spaces, so a comma list is safe."""
    return tuple(x.strip() for x in s.split(",") if x.strip())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-cutoff", required=True, help="no raw row after this date is read (PLAN v0.8 C-8)")
    ap.add_argument("--holdout-approved", action="store_true",
                    help="required for a data cut-off on or after 2022-01-01 (the sealed hold-out); only after the "
                         "user's recorded decision to open it")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--smoke-n", type=int, default=100)
    ap.add_argument("--out", default="")
    ap.add_argument("--panel-dir", default="")
    ap.add_argument("--jobs", type=int, default=5)
    ap.add_argument("--threads", type=int, default=0,
                    help="LightGBM threads per fit; default = config.lgbm_threads (FIXED, D6; change only to reproduce)")
    ap.add_argument("--blas-threads", type=int, default=2,
                    help="BLAS threads (read before numpy is imported); must equal config.blas_threads unless overridden "
                         "for a reproduction test, in which case it is recorded in the configuration")
    ap.add_argument("--base-workers", type=int, default=0, help="parallel base / NET-U15 fits (memory)")
    ap.add_argument("--perm-draws", type=int, default=-1, help="A4.3 item 6 draws per seed (default: configuration)")
    ap.add_argument("--tune-only", action="store_true",
                    help="D1: run every hyperparameter search (base, BASE-V, NET-U15, gates, TREND, PERF, VT sigma*) and "
                         "write the tuning archive; no evaluation")
    ap.add_argument("--load-tuning", default="",
                    help="D1: tuning archive (json) to load; the run refuses to re-tune anything")
    ap.add_argument("--tuning-sha", default="", help="expected SHA-256 of the archive (optional additional check)")
    ap.add_argument("--bases", default="")
    ap.add_argument("--raw-root", default="", help="tests only: an alternative raw tree (cut-off invariance test)")
    ap.add_argument("--codes-file", default="", help="smoke only: the exact list of names to use")
    ap.add_argument("--gate-rule", default="fixed_count", choices=("threshold", "fixed_count"))
    ap.add_argument("--gate-window", default="", choices=("", "y1", "y2"),
                    help="fixed-count gate training window: y1 (A2.1 primary, default) or y2 (v0.8; sensitivity)")
    ap.add_argument("--gate-criterion", default="", choices=("", "V", "theta_sel"),
                    help="tuning criterion of fixed-count gates: V (A2.2, default) or theta_sel (pilot)")
    ap.add_argument("--n-configs", type=int, default=0, help="budget T (default 30; smoke default 2)")
    ap.add_argument("--seeds", default="", help="comma-separated seeds (default 0,1,2,3,4; smoke default 0,1,2)")
    ap.add_argument("--rnd-reps", type=int, default=0)
    ap.add_argument("--bootstrap-B", type=int, default=0)
    ap.add_argument("--methods", default="", help="comma-separated subset of methods (default: the configuration's)")
    ap.add_argument("--pilot-compat", action="store_true",
                    help="reproduction mode: the pilot's method list, gate window y2 and criterion theta_sel")
    ap.add_argument("--resume", action="store_true",
                    help="reuse checkpoints in <out>/checkpoints written by an interrupted run of the same configuration")
    ap.add_argument("--keep-awake", action="store_true",
                    help="Windows: ask the system not to idle-sleep while this process runs (released at exit)")
    ap.add_argument("--dump-decisions", action="store_true",
                    help="save daily nominations, every policy's submissions (with rho and fill flag) and the base RankIC")
    ap.add_argument("--stop-after-gates", action="store_true", help="diagnostics: stop after stage 8 (no backtests)")
    ap.add_argument("--reuse-tuning", default="",
                    help="diagnostics: results.json of an earlier identical run; refit only its chosen gate configurations")
    a = ap.parse_args(argv)
    cut = dc.require_cutoff(a.data_cutoff)
    if str(cut) >= HOLDOUT_START and not a.holdout_approved:
        print(f"refused: data cut-off {cut} reaches into the sealed hold-out (from {HOLDOUT_START}); "
              "development runs use --data-cutoff 2021-12-31", file=sys.stderr)
        return 2
    if str(cut) > TUNING_CUTOFF and not a.load_tuning:                      # round 2, D1
        print(f"refused: a run with a data cut-off after {TUNING_CUTOFF} must load the frozen tuning archive "
              "(--load-tuning); it may not tune", file=sys.stderr)
        return 2
    if a.tune_only and (a.load_tuning or str(cut) != TUNING_CUTOFF):
        print(f"refused: --tune-only runs at data cut-off {TUNING_CUTOFF} and cannot load an archive", file=sys.stderr)
        return 2
    if a.keep_awake and sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    raw = Path(a.raw_root) if a.raw_root else D.RAW
    if a.smoke:
        if a.codes_file:
            codes = [l.strip() for l in open(a.codes_file, encoding="utf-8") if l.strip()]
        else:
            allc, _ = D.pilot_list(PilotConfig(data_cutoff=str(cut)))
            codes = list(allc)[: a.smoke_n]                       # round 2, D7: no readiness / mtime test
        out = a.out or "experiments/results/confirm/smoke"
        cfg = smoke_config(str(cut), tuple(codes), out, a.panel_dir or f"{out}/feature_panel")
    else:
        out = a.out or "experiments/results/confirm/run"
        cfg = PilotConfig(data_cutoff=str(cut), out_dir=out, panel_dir=a.panel_dir or "experiments/data/derived/feature_panel")
    kw = {"n_jobs": a.jobs, "gate_rule": a.gate_rule, "blas_threads": BLAS_THREADS}
    if a.threads:
        kw["lgbm_threads"] = a.threads
    if a.base_workers:
        kw["base_workers"] = a.base_workers
    if a.perm_draws >= 0:
        kw["perm_draws"] = a.perm_draws
    if a.pilot_compat:
        kw.update(methods=PILOT_METHODS, gate_window="y2", gate_criterion="theta_sel", base_features="all",
                  criterion_resolved_only=False, perm_draws=0,
                  e_const_dev_for=("SCORE", "CONF", "LOSS(-Z)", "LOSS(+Z_H)", "LOSS(+Z_O)"),
                  rnd_for=("CONF", "LOSS(-Z)", "LOSS(+Z_H)", "LOSS(+Z_O)"))
    if a.gate_window:
        kw["gate_window"] = a.gate_window
    if a.gate_criterion:
        kw["gate_criterion"] = a.gate_criterion
    if a.n_configs:
        kw["n_configs"] = a.n_configs
    if a.seeds:
        kw["seeds"] = tuple(int(x) for x in a.seeds.split(","))
    if a.rnd_reps:
        kw["rnd_reps"] = a.rnd_reps
    if a.bootstrap_B:
        kw["bootstrap_B"] = a.bootstrap_B
    if a.methods:
        kw["methods"] = _split_methods(a.methods)
    if a.bases:
        kw["bases"] = tuple(a.bases.split(","))
    from dataclasses import replace
    cfg = replace(cfg, **kw)
    outdir = ROOT / cfg.out_dir
    outdir.mkdir(parents=True, exist_ok=True)
    log = Log(outdir / "logs" / "run.log")
    # round 2, Q6 / D6: apply and verify the fixed BLAS thread count
    from threadpoolctl import threadpool_info, threadpool_limits
    threadpool_limits(limits=cfg.blas_threads)
    blas_info = [{"api": x.get("internal_api"), "threads": x.get("num_threads")} for x in threadpool_info()]
    if any(x["threads"] != cfg.blas_threads for x in blas_info):
        log(f"WARNING: thread pools {blas_info} differ from blas_threads = {cfg.blas_threads}")
    # round 2, D7 / D2: raw-file hashes of the frozen population at the START of the run (raw-tree identity)
    D.install_listing_cut(cut)                                                 # round 2, D8
    codes_used = list(cfg.codes_subset) if cfg.codes_subset else D.pilot_list(cfg)[0]
    raw_files, raw_hash = D.raw_identity(codes_used, cut, raw)
    archive = None
    if a.load_tuning:
        archive = load_archive(Path(a.load_tuning), cfg, a.tuning_sha)
        log(f"tuning archive loaded and verified: {a.load_tuning} sha256 {archive['_sha256']}")
    started = datetime.now().isoformat(timespec="seconds")
    manifest = {"started": started, "argv": sys.argv, "python": platform.python_version(), "config": cfg.to_json(),
                "config_hash": cfg.hash(), "config_hash_without_compute": cfg.hash_without_compute(),
                "seeds": list(cfg.seeds), "conventions_hash": conventions_hash(),
                "search_spaces_hash": M.spaces_hash(), "code_hash": code_hash(), "data_cutoff": str(cut),
                "raw_root": str(raw), "blas_env": os.environ.get("OMP_NUM_THREADS"), "blas_pools": blas_info,
                "lgbm_threads": cfg.lgbm_threads, "resume": a.resume, "raw_identity": raw_hash,
                "raw_files_sha256": raw_files, "n_raw_files": len(raw_files),
                "tune_only": a.tune_only, "load_tuning": a.load_tuning,
                "tuning_archive_sha256": archive["_sha256"] if archive else None}
    (outdir / "run_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    log(f"run '{cfg.name}' started; data cut-off {cut}; out {outdir}; T = {cfg.n_configs}; seeds {cfg.seeds}; "
        f"gate window {cfg.gate_window}; criterion {cfg.gate_criterion}")
    status = "ok"
    try:
        reuse = json.load(open(a.reuse_tuning, encoding="utf-8"))["tuning"] if a.reuse_tuning else None
        res = run(cfg, log, outdir, raw, stop_after="8" if a.stop_after_gates else "",
                  dump_decisions=a.dump_decisions, reuse_tuning=reuse, resume=a.resume, raw_hash=raw_hash,
                  archive=archive, tune_only=a.tune_only)
    except Exception:
        status = "error"
        res = {"error": traceback.format_exc()}
        log("ERROR\n" + res["error"])
    manifest["finished"] = datetime.now().isoformat(timespec="seconds")
    manifest["status"] = status
    manifest["timing"] = res.get("timing")
    manifest["listing_reads_blanked"] = D._LISTING_CUT.get("blanked_reads", 0)
    (outdir / "run_manifest.json").write_text(json.dumps(to_jsonable(manifest), indent=1), encoding="utf-8")
    res["data_cutoff"] = str(cut)
    res["conventions_hash"] = conventions_hash()
    with open(outdir / "results.json", "w", encoding="utf-8") as fh:
        json.dump(to_jsonable(res), fh, indent=1, ensure_ascii=False, default=str)
    log(f"run finished: {status}")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())

"""Compute estimate of the full development-period run (1,000-name list, top-300 screen, T = 30, five seeds,
all policies of config.CONFIRM_METHODS, both bases), extrapolated from MEASURED timings.

    experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/estimate_compute.py \\
        --pilot-full experiments/results/pilot/run_fixedcount --smoke experiments/results/confirm/smoke \\
        [--threads 10] [--jobs 5]

Inputs (read-only): the full pilot run (fixed-count rule, T = 4, three seeds, jobs 6 x LightGBM threads 4; its
log gives per-step times), and the confirm smoke run (per-trial wall times per method).  Every factor of the
extrapolation is printed with its basis; all outputs are ESTIMATES (the machine is shared and the measured
times include contention from other jobs).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from confirm.config import CONFIRM_METHODS, PILOT_METHODS   # noqa: E402

HEAVY = ("NET-U", "NET-U15")          # population = all ~295 candidates instead of the top 90
HEAVY_WEIGHT = 295 / 90               # LightGBM cost ~ linear in rows (pilot: median 294 candidates per day)


def learned(methods):
    return [m for m in methods if m.split("(")[0] in ("LOSS", "LOSS-LR", "NET-K", "NET-U", "NET-U15")]


def log_times(run_dir: Path) -> dict:
    """Seconds between consecutive base log lines of the full pilot (tuning per config, deployment per seed)."""
    lines = (run_dir / "logs" / "run.log").read_text(encoding="utf-8").splitlines()
    t = []
    for ln in lines:
        m = re.match(r"(\d\d:\d\d:\d\d) \+\s*(\d+)s (.*)", ln)
        if m:
            t.append((int(m.group(2)), m.group(3)))
    out = {"lgbm_tune": [], "lgbm_deploy": [], "ridge_tune": [], "ridge_deploy": []}
    prev = None
    for sec, msg in t:
        if prev is not None:
            dt = sec - prev
            if msg.startswith("[base lgbm] config"):
                out["lgbm_tune"].append(dt)
            elif msg.startswith("[base lgbm] seed"):
                out["lgbm_deploy"].append(dt)
            elif msg.startswith("[base ridge] config"):
                out["ridge_tune"].append(dt)
            elif msg.startswith("[base ridge] seed"):
                out["ridge_deploy"].append(dt)
        prev = sec
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot-full", required=True)
    ap.add_argument("--smoke", default="")
    ap.add_argument("--threads", type=int, default=10, help="total CPU threads available to the run")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    P = Path(a.pilot_full)
    man = json.loads((P / "run_manifest.json").read_text(encoding="utf-8"))
    tim = {k: v["seconds"] for k, v in man["timing"].items()}
    pcfg = man["config"]
    pthreads = pcfg["n_jobs"] * pcfg["lgbm_threads"]                 # 6 x 4 = 24 in the pilot
    lt = log_times(P)
    T, seeds, tune_years, eval_years = 30, 5, 2, 5
    pT, pseeds = pcfg["n_configs"], len(pcfg["seeds"])
    rep = {"inputs": {"pilot_full_timing_s": tim, "pilot_threads": pthreads, "pilot_T": pT, "pilot_seeds": pseeds,
                      "pilot_base_log_s": lt}}
    # ---------------- base predictors (serial stage; LightGBM at 4 threads in the pilot)
    lg_fit_tune = sum(lt["lgbm_tune"]) / (pT * tune_years * pseeds)            # s per tuning fit
    lg_seed_dep = float(np.mean(lt["lgbm_deploy"]))                            # s per seed (9 annual fits)
    rg_tune = sum(lt["ridge_tune"])                                            # s for pT configs (1 seed)
    rg_dep = float(np.mean(lt["ridge_deploy"])) if lt["ridge_deploy"] else 0.0
    n_lin = 8                                                                  # LINEAR_SPACE has 8 points < T
    base = {"lgbm_tuning_s": lg_fit_tune * T * tune_years * seeds,
            "lgbm_deploy_base_s": lg_seed_dep * seeds,
            "lgbm_deploy_basev_s_if_other_config": lg_seed_dep * seeds,
            "ridge_tuning_s": rg_tune / pT * n_lin,
            "ridge_deploy_base_s": rg_dep, "ridge_deploy_basev_s_if_other_config": rg_dep,
            "basis": "pilot full-run log: per tuning fit and per deployment seed at 4 LightGBM threads; ridge "
                     "tuning scaled from 4 to 8 configurations (enet configurations dominate); "
                     "the 30-configuration mean cost is assumed equal to the 4-configuration mean (UNVERIFIED)"}
    tun = base["lgbm_tuning_s"]
    base["total_s_at_4_threads_range"] = [
        base["lgbm_tuning_s"] * 1.2 + base["lgbm_deploy_base_s"] + base["ridge_tuning_s"] + base["ridge_deploy_base_s"],
        tun * 1.55 + (base["lgbm_deploy_base_s"] + base["lgbm_deploy_basev_s_if_other_config"]) * 1.55
        + base["ridge_tuning_s"] + base["ridge_deploy_base_s"] * 2 * 8]
    base["range_note"] = ("low: BASE-V picks the base's configuration (fits reused), cheap configurations; high: other "
                          "configuration for BASE-V, configuration cost x1.55, an elastic-net ridge deployment 8x a ridge one")
    rep["base"] = base
    # ---------------- gates (thread pool; pilot 6 workers x 4 threads)
    pl, cl = learned(PILOT_METHODS), learned(CONFIRM_METHODS)
    w = lambda ms: sum(HEAVY_WEIGHT if m.split("(")[0] in HEAVY else 1.0 for m in ms)       # noqa: E731
    fits_p = pT * pseeds * tune_years + pseeds * eval_years
    fits_c = T * seeds * tune_years + seeds * eval_years
    rows_factor = 1.5          # y1 window: tuning folds 2015 / 2016 train on 2 / 3 instead of 1 / 2 years of rows
    thread_s = tim["8_gates"] * pthreads
    # configuration cost: the pilot's 4 LightGBM draws all have feature_fraction 0.5 and mean n_estimators 200;
    # a cost proxy n_estimators x (0.5 + feature_fraction) x log2(num_leaves + 1) is 1.55 times larger for the
    # 30 draws (computed from models.draw_configs); range 1.2 (n_estimators only) .. 1.55
    cfg_lo, cfg_hi = 1.2, 1.55
    gate_thread_s = thread_s * (fits_c / fits_p) * (w(cl) / w(pl)) * rows_factor
    gate_lo, gate_hi = 0.6 * gate_thread_s * cfg_lo, gate_thread_s * cfg_hi
    rep["gates"] = {"pilot_thread_seconds_upper": thread_s, "fits_per_method_pilot": fits_p, "fits_per_method_confirm": fits_c,
                    "method_weight_pilot": w(pl), "method_weight_confirm": w(cl), "rows_factor": rows_factor,
                    "config_cost_factor": [cfg_lo, cfg_hi], "confirm_thread_seconds_range": [gate_lo, gate_hi],
                    "wall_hours_at_threads": {str(n): [gate_lo / n / 3600, gate_hi / n / 3600] for n in (10, 16, 24)},
                    "basis": "pilot stage-8 wall time x 24 threads (an upper bound on the CPU actually used) scaled by "
                             "fits per method, a heavy-method weight of 4 for the all-candidate NET-U / NET-U15, and the "
                             "larger Y-1 training windows; the lower end of the range assumes 60% pilot utilisation"}
    # ---------------- backtests (process pool; pilot 6 processes)
    n_runs_pilot = 264
    proc_s_per_run = tim["9_backtests"] * pcfg["n_jobs"] / n_runs_pilot
    main_methods = [m for m in CONFIRM_METHODS if m != "VT"]
    runs_main = 2 * seeds * (len(main_methods) + 1 + 5)            # + VT + E-const-dev (5)
    runs_rnd = 2 * seeds * 4 * 200                                  # RND for 4 gates x 200 repetitions (PLAN 6.1)
    runs_tune = 2 * 2 * 9 * seeds                                   # TREND / PERF grids (9 points each)
    rep["backtests"] = {"proc_s_per_run_pilot": proc_s_per_run, "runs_main": runs_main, "runs_rnd_200": runs_rnd,
                        "runs_trend_perf_tuning": runs_tune,
                        "proc_s_without_rnd": proc_s_per_run * (runs_main + runs_tune),
                        "proc_s_rnd_200": proc_s_per_run * runs_rnd}
    # ---------------- other stages
    rep["other_s"] = {"market_panel_features": tim["2_market"] + tim["3_panel"] + tim["5_features"],
                      "standard_orders": tim["7_standard_orders"] * 11 / 9,
                      "estimands_B10000": tim["10_estimands"] * 5}
    # ---------------- smoke cross-check: per-trial wall seconds by method
    if a.smoke:
        r = json.loads((Path(a.smoke) / "results.json").read_text(encoding="utf-8"))
        tr = {}
        for k, v in r.get("tuning", {}).items():
            ts = [x.get("seconds") for x in v.get("trials", []) if isinstance(x, dict) and x.get("seconds") is not None]
            if ts:
                tr[k] = {"trials": len(ts), "mean_s_per_trial": float(np.mean(ts)), "deploy_s": v.get("deploy_seconds")}
        rep["smoke_per_trial"] = tr
        rep["smoke_timing"] = json.loads((Path(a.smoke) / "run_manifest.json").read_text(encoding="utf-8")).get("timing")
    n = a.threads
    jobs = max(1, n // 2)
    tot_lo = (base["total_s_at_4_threads_range"][0] + gate_lo / n
              + rep["backtests"]["proc_s_without_rnd"] / jobs + sum(rep["other_s"].values()))
    tot_hi = (base["total_s_at_4_threads_range"][1] + gate_hi / n
              + rep["backtests"]["proc_s_without_rnd"] / jobs + sum(rep["other_s"].values()))
    rep["total_hours_without_rnd200"] = [tot_lo / 3600, tot_hi / 3600]
    rep["rnd200_extra_hours"] = rep["backtests"]["proc_s_rnd_200"] / jobs / 3600
    rep["threads"] = n
    rep["written"] = datetime.now().isoformat(timespec="seconds")
    text = json.dumps(rep, indent=1, default=float)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Round 2: compute estimate of the full development run from the full-size calibration run
(experiments/results/confirm/calibration: 969 names, T = 2, one seed, lgbm base, LightGBM 2 threads per fit).

    experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/estimate_from_calibration.py \\
        --calib experiments/results/confirm/calibration --pilot-full experiments/results/pilot/run_fixedcount

Model: wall time of one LightGBM fit (incl. design, prediction) = a * rows * proxy(conf), proxy = n_estimators *
(0.5 + feature_fraction) * log2(num_leaves + 1); `a` is fitted per model family (base-like on the -Z set, top-90
gates, all-candidate NET-U) from the measured fits.  The full run's fits are enumerated from the configuration
(T = 30 draws, 5 seeds, years, measured row counts); unknown chosen configurations are given the mean proxy of the
30 draws.  Every fit runs with 2 threads, so thread-seconds = 2 * fit seconds.  ESTIMATES only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))
from confirm import models as M          # noqa: E402


def proxy(c):
    return c["n_estimators"] * (0.5 + c["feature_fraction"]) * np.log2(c["num_leaves"] + 1)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calib", required=True)
    ap.add_argument("--pilot-full", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    r = json.loads((Path(a.calib) / "results.json").read_text(encoding="utf-8"))
    man = json.loads((Path(a.calib) / "run_manifest.json").read_text(encoding="utf-8"))
    t = r["tuning"]
    conf30 = M.draw_configs("lgbm", 30)
    pmean = float(np.mean([proxy(c) for c in conf30]))
    # ---- per-family rate a (seconds per row per proxy unit)
    obs = {"base": [], "gate90": [], "netu": []}
    for key in ("lgbm|BASE", "lgbm|NET-U15(-Z)"):
        for tr in t[key]["trials"]:
            for f in tr["folds"]:
                obs["base"].append(f["seconds"] / (f["train_rows"] * proxy(tr["config"])))
    for f in r["base_deploy_fits"]["lgbm|0"]:
        obs["base"].append(f["seconds"] / (f["train_rows"] * proxy(r["base"]["lgbm"]["chosen"])))
    for key, fam in (("lgbm|LOSS(-Z)", "gate90"), ("lgbm|NET-U(-Z)", "netu")):
        for tr in t[key]["trials"]:
            rows = sum(f["train_rows"] for f in tr["folds"])
            obs[fam].append(tr["seconds"] / (rows * proxy(tr["config"])))
        x = t[key]
        conf = x["configs"][x["chosen"]]
        rows = sum(d["rows"] for d in x["deploy_fits"])
        obs[fam].append(x["deploy_seconds"] / (rows * proxy(conf)))
    rate = {k: (float(np.min(v)), float(np.median(v)), float(np.max(v))) for k, v in obs.items()}
    # ---- rows of the full run (measured in the calibration)
    base_tune_rows = [f["train_rows"] for f in t["lgbm|BASE"]["trials"][0]["folds"]]          # 2011, 2012
    netu15_tune_rows = [f["train_rows"] for f in t["lgbm|NET-U15(-Z)"]["trials"][0]["folds"]]
    base_dep_rows = [f["train_rows"] for f in r["base_deploy_fits"]["lgbm|0"]]                  # 2013..2021
    netu15_dep_rows = base_dep_rows[2:]                                                          # 2015..2021 (approx.)
    g_tune = t["lgbm|LOSS(-Z)"]["trials"][0]["folds"]
    g_tune_rows = [f["train_rows"] for f in g_tune]                                              # y1: 2015, 2016
    g_dep_rows = [d["rows"] for d in t["lgbm|LOSS(-Z)"]["deploy_fits"]]                         # 2017..2021
    u_tune_rows = [f["train_rows"] for f in t["lgbm|NET-U(-Z)"]["trials"][0]["folds"]]
    u_dep_rows = [d["rows"] for d in t["lgbm|NET-U(-Z)"]["deploy_fits"]]
    # y2 (-thr) rows: one year older window ~ the y1 rows of the previous year
    thr_tune_rows = [g_tune_rows[0] / 2, g_tune_rows[0]]
    thr_dep_rows = [g_tune_rows[1]] + g_dep_rows[:-1]
    S, T = 5, 30

    def fits(rate_a):
        out = {}
        # base LightGBM: tuning, deployment of base and (if another configuration) BASE-V
        out["base_lgbm_tuning"] = sum(rate_a["base"] * n * pmean for n in base_tune_rows) * T * S
        out["base_lgbm_deploy"] = sum(rate_a["base"] * n * pmean for n in base_dep_rows) * S
        out["basev_lgbm_deploy_if_other_config"] = out["base_lgbm_deploy"]
        out["netu15_tuning"] = sum(rate_a["base"] * n * pmean for n in netu15_tune_rows) * T * S
        out["netu15_deploy"] = sum(rate_a["base"] * n * pmean for n in netu15_dep_rows) * S
        light = sum(rate_a["gate90"] * n * pmean for n in g_tune_rows) * T * S + \
            sum(rate_a["gate90"] * n * pmean for n in g_dep_rows) * S
        thr = sum(rate_a["gate90"] * n * pmean for n in thr_tune_rows) * T * S + \
            sum(rate_a["gate90"] * n * pmean for n in thr_dep_rows) * S
        heavy = sum(rate_a["netu"] * n * pmean for n in u_tune_rows) * T * S + \
            sum(rate_a["netu"] * n * pmean for n in u_dep_rows) * S
        # per base: 8 LightGBM top-90 gates (LOSS x5, NET-K x3), LOSS-LR (logit, ~1/3 of a LOSS gate in the smoke),
        # 3 -thr gates, NET-U
        out["gates_per_base"] = 8 * light + light / 3 + 3 * thr + heavy
        out["gates_both_bases"] = 2 * out["gates_per_base"]
        # follow-up: 2 groups x 2 kinds x 20 draws x 5 seeds x evaluation-year fits at the chosen configuration
        out["follow_up_both_bases"] = 2 * 2 * 2 * 20 * S * sum(rate_a["gate90"] * n * pmean for n in g_dep_rows)
        return out
    lo, mid, hi = ({k: v[i] for k, v in rate.items()} for i in range(3))
    est = {"low": fits(lo), "median": fits(mid), "high": fits(hi)}
    # ridge base (pilot measured: tuning 4 configs 271 s at 4 threads, deployment 206 s) - all 8 points, two configs
    ridge_s = 271 / 4 * 8 + 206 * 2
    pil = json.loads((Path(a.pilot_full) / "run_manifest.json").read_text(encoding="utf-8"))["timing"]
    bt_proc_s = pil["9_backtests"]["seconds"] * 6 / 264
    n_main = 2 * 5 * (23 + 1 + 5) + 180
    n_rnd = 2 * 5 * 4 * 200
    rep = {"rates_s_per_row_proxy": rate, "mean_proxy_T30": pmean, "fit_seconds": est,
           "ridge_base_seconds_at_4_threads_pilot": ridge_s,
           "calibration_stage_seconds": {k: v["seconds"] for k, v in man["timing"].items()},
           "backtest_process_seconds_per_run_pilot": bt_proc_s, "backtest_runs_without_rnd": n_main, "rnd_runs": n_rnd}
    # wall clock: fits use 2 threads; the base / NET-U15 stage runs base_workers fits at a time (memory)
    out = {}
    for threads in (10, 24):
        jobs = threads // 2
        for label, e in est.items():
            base_workers = 2 if threads == 10 else 4
            base_part = (e["base_lgbm_tuning"] + e["base_lgbm_deploy"] + e["basev_lgbm_deploy_if_other_config"]
                         + e["netu15_tuning"] + e["netu15_deploy"]) / base_workers + ridge_s
            gate_part = (e["gates_both_bases"] + e["follow_up_both_bases"]) / jobs
            bt = bt_proc_s * n_main / jobs
            rnd = bt_proc_s * n_rnd / jobs
            other = 1060 * 0 + 106 + 92 + 136 + 1800          # panel exists (provenance-checked); market, features, orders, estimands
            out[f"{threads}_threads_{label}"] = {"base_h": base_part / 3600, "gates_h": gate_part / 3600,
                                                 "follow_up_h_included": est[label]["follow_up_both_bases"] / jobs / 3600,
                                                 "backtests_h": bt / 3600, "rnd200_h": rnd / 3600, "other_h": other / 3600,
                                                 "total_without_rnd_h": (base_part + gate_part + bt + other) / 3600,
                                                 "total_with_rnd_h": (base_part + gate_part + bt + rnd + other) / 3600}
    rep["wall"] = out
    text = json.dumps(rep, indent=1, default=float)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

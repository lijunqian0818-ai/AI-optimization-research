"""Phase E evaluation.

python analyze_phaseE.py
"""
import os

for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[_v] = "1"

import glob
import json

import numpy as np
import pandas as pd

from analyze_phaseD import cp, load as load_d, truth_region
from pipeline2 import CONTRASTS2, policy_level_truth

RES = "C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/results/precision_v9"
OUT = os.path.join(RES, "phaseE")
NAMES = [c[0] for c in CONTRASTS2]
J = len(NAMES)
SCEN = ["S0", "S1", "S2", "F1", "F2", "F2c", "F3a", "F3b"]
LIT = ["M1a_nw_fixedb_bonf", "M1b_nw_fixedb_maxt", "M2_ewc_tnu_bonf", "M4a_prewhite_nw_bonf",
       "M4b_prewhite_nw_maxt", "M5_sn_bonf"]
M3_L = (48, 100)
M3_B = (43, 100, 200)


def load(scen):
    rows = []
    for fn in sorted(glob.glob(os.path.join(OUT, "raw", f"{scen}_*.json"))):
        with open(fn) as f:
            rows += json.load(f)
    rows.sort(key=lambda r: r["rep"])
    return rows


def methods_of(rows):
    A = lambda k: np.array([r[k] for r in rows])
    out = {}
    for m in LIT:
        out[m] = (A(f"hw_{m}"), A(f"se_{m}") if f"se_{m}" in rows[0] else None)
    for L in M3_L:
        for b in M3_B:
            se = A(f"se_bt_b{b}")
            out[f"M3_bt_L{L}_b{b}"] = (A(f"q_M3_L{L}_b{b}")[:, None] * se, se)
    se = A("se_bt_b20")
    out["bench_bt_L24_b20"] = (A("q_bench_bt_L24_b20")[:, None] * se, se)
    se = A("se_bench_old_L24")
    out["bench_old_L24"] = (A("q_bench_old_L24")[:, None] * se, se)
    return out


def flatten(rows):
    flat = []
    for r in rows:
        d = {}
        for k, v in r.items():
            if isinstance(v, list):
                for j, x in enumerate(v):
                    d[f"{k}_{NAMES[j] if len(v) == J else j}"] = x
            else:
                d[k] = v
        flat.append(d)
    return pd.DataFrame(flat)


def main():
    summ = {"notes": "Phase E exploratory (no verdict, nothing frozen). Paired with Phase D: same histories.",
            "scenarios": {}}
    crit = dict(np.load(os.path.join(OUT, "crit_values.npz")))
    summ["critical_values"] = {k: float(v) for k, v in crit.items()}
    for scen in SCEN:
        rows = load(scen)
        if not rows:
            continue
        flatten(rows).to_csv(os.path.join(OUT, f"per_rep_{scen}.csv"), index=False)
        if scen in ("S0", "S1", "S2"):
            th0, mc, c, exact = policy_level_truth(), np.zeros(J), 0.0, True
        elif scen in ("F3a", "F3b"):
            th0, mc, c, exact = np.zeros(J), np.zeros(J), 0.0, True
        else:
            tr = load_d(os.path.join(RES, "phaseD", "raw"), scen, "truth")
            th0, mc, c = truth_region(tr)
            exact = False
        TH = np.array([r["th"] for r in rows])
        R = len(rows)
        err = TH - th0
        sd = err.std(0, ddof=1)
        lo_b, hi_b = th0 - c * mc, th0 + c * mc
        allowance = 0.0 if exact else 0.01
        ms = methods_of(rows)
        hw_ref = ms["bench_bt_L24_b20"][0]
        ev = {"R": R, "exact_truth": exact, "truth_bp": (th0 * 1e4).tolist(), "truth_mcse_bp": (mc * 1e4).tolist(),
              "truth_region_c": c, "truth_region_allowance": allowance, "methods": {},
              "runtime_s": {k: float(np.mean([r[k] for r in rows])) for k in ("t_gen", "t_lit", "t_bt", "t_old")},
              "mean_rho_prewhite": np.mean([r["rho_pw"] for r in rows], 0).tolist(),
              "mean_q_maxt": float(np.mean([r["q_maxt"] for r in rows]))}
        for m, (hw, se) in ms.items():
            L_, U_ = TH - hw, TH + hw
            pm = (th0 < L_) | (th0 > U_)
            cm = (lo_b < L_) | (hi_b > U_)
            kp, kc = int(pm.any(1).sum()), int(cm.any(1).sum())
            e = {"point": {"k": kp, "rate": kp / R, "cp": cp(kp, R)},
                 "conservative": {"k": kc, "rate": kc / R, "cp": cp(kc, R)},
                 "conservative_ub_plus_allowance": cp(kc, R)[2] + allowance,
                 "marginal_point_rate": pm.mean(0).tolist(),
                 "mean_halfwidth_bp": float(hw.mean() * 1e4),
                 "halfwidth_ratio_to_bench_bt": float(np.mean(hw / hw_ref)),
                 "halfwidth_bp_by_contrast": (hw.mean(0) * 1e4).tolist()}
            if se is not None:
                e["se_ratio_mean"] = float(np.mean(se.mean(0) / sd))
                e["se_ratio_by_contrast"] = (se.mean(0) / sd).tolist()
            ev["methods"][m] = e
        summ["scenarios"][scen] = ev
        print(scen, {m: round(v["point"]["rate"], 3) for m, v in ev["methods"].items()}, flush=True)
    # cross-scenario overview
    scs = summ["scenarios"]
    meths = list(next(iter(scs.values()))["methods"]) if scs else []
    summ["overview"] = {m: {s: scs[s]["methods"][m]["point"]["rate"] for s in scs} for m in meths}
    summ["le_6pct_point"] = {m: [s for s in scs if scs[s]["methods"][m]["point"]["rate"] <= 0.06] for m in meths}
    with open(os.path.join(OUT, "summary_phaseE.json"), "w") as f:
        json.dump(summ, f, indent=1)


if __name__ == "__main__":
    main()

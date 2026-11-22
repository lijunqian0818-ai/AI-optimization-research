"""Analysis of the S0 audit (parts A, C, D, E).

python analyze_audit_s0.py --raw ../../results/precision_v9/audit_s0/raw --out ../../results/precision_v9/audit_s0
"""
import os

for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[_v] = "1"

import argparse
import glob
import json

import numpy as np
import pandas as pd
from scipy.stats import beta

from audit_s0 import STEPS, ladder_contrasts, ladder_masks

RES = "C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/results/precision_v9"
METHODS = {"i_student_bonf": ("se_t", "crit_t"), "ii_iid_bt": ("se_iid", "q_iid"),
           "iii_bt_L24_b20": ("se_hac20", "q_bt24"), "iv_old_L24": ("se_old", "q_old")}


def cp(k, n, conf=0.95):
    lo = 0.0 if k == 0 else beta.ppf((1 - conf) / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - (1 - conf) / 2, k + 1, n - k)
    up1 = 1.0 if k == n else beta.ppf(conf, k + 1, n - k)
    return float(lo), float(hi), float(up1)


def load(raw, pattern):
    rows = []
    for fn in sorted(glob.glob(os.path.join(raw, pattern))):
        with open(fn) as f:
            rows += json.load(f)
    rows.sort(key=lambda r: r["rep"])
    return rows


def evaluate(rows, names):
    th = np.array([r["th"] for r in rows])
    truth = np.array(rows[0]["truth"])
    err = th - truth
    sd = err.std(0, ddof=1)
    R = len(rows)
    out = {"R": R, "std_bias": (err.mean(0) / sd).tolist(),
           "std_bias_se": (1 / np.sqrt(R)), "sd_theta_bp": (sd * 1e4).tolist()}
    for m, (sek, qk) in METHODS.items():
        se = np.array([r[sek] for r in rows])
        q = np.array([r[qk] for r in rows])
        mult = q if q.ndim == 2 else q[:, None]
        hw = mult * se
        miss = np.abs(err) > hw
        k = int(miss.any(1).sum())
        tj = err / se
        lev = np.abs(tj) / (mult if mult.shape[1] > 1 else mult)
        arg = lev.argmax(1)
        e = {"k": k, "rate": k / R, "cp": cp(k, R),
             "marginal_rate": miss.mean(0).tolist(),
             "marginal_below": (err < -hw).mean(0).tolist(), "marginal_above": (err > hw).mean(0).tolist(),
             "t_quantiles": {str(p): np.quantile(tj, p, axis=0).tolist() for p in (0.005, 0.025, 0.5, 0.975, 0.995)},
             "t_sd": tj.std(0, ddof=1).tolist(),
             "argmax_freq_all": np.bincount(arg, minlength=len(names)).tolist(),
             "argmax_freq_misses": np.bincount(arg[miss.any(1)], minlength=len(names)).tolist(),
             "mean_mult": float(np.mean(q)), "sd_mult": float(np.std(q)),
             "mean_hw_bp": float(hw.mean() * 1e4),
             "se_ratio": (se.mean(0) / sd).tolist(), "se_ratio_mean": float(np.mean(se.mean(0) / sd)),
             "se_cv": (se.std(0) / se.mean(0)).tolist()}
        out[m] = e
    out["any_inapplicable"] = int(sum(not r["app"] for r in rows))
    return out


def ratio_gap(path, pols, contrasts):
    """E[sum U / sum V] - E[sum U] / E[sum V] per contrast, from independent truth histories."""
    df = pd.read_csv(path)
    out = {}
    rng = np.random.default_rng(30_888_001)
    for name, g, h, late in contrasts:
        sfx = "late" if late else ""
        Ug, Vg = df[f"sumN{sfx}_{pols[g]}"].values, df[f"sumS{sfx}_{pols[g]}"].values
        Uh, Vh = df[f"sumN{sfx}_{pols[h]}"].values, df[f"sumS{sfx}_{pols[h]}"].values
        per = Ug / Vg - Uh / Vh
        roe = Ug.mean() / Vg.mean() - Uh.mean() / Vh.mean()
        gap = per.mean() - roe
        bs = []
        n = len(df)
        for _ in range(2000):
            i = rng.integers(0, n, n)
            bs.append((Ug[i] / Vg[i] - Uh[i] / Vh[i]).mean() - (Ug[i].mean() / Vg[i].mean() - Uh[i].mean() / Vh[i].mean()))
        out[name] = {"E_ratio_bp": per.mean() * 1e4, "ratio_of_E_bp": roe * 1e4, "gap_bp": gap * 1e4,
                     "gap_se_bp": float(np.std(bs, ddof=1) * 1e4), "R": n,
                     "cv_of_sumV": float(Vg.std() / Vg.mean())}
    return out


def mask_resampling_stats():
    from intervals import stationary_bootstrap_indices
    T = 1075
    m = ladder_masks(ladder_contrasts("L3"))[2]
    out = {}
    for L in (1, 24):
        idx = stationary_bootstrap_indices(T, 4000, L, np.random.default_rng(30_888_002))
        k = m[idx].sum(1)
        out[f"L{L}"] = {"fixed_window_days": int(m.sum()), "mean": float(k.mean()), "sd": float(k.std()),
                        "p01": float(np.quantile(k, .01)), "p99": float(np.quantile(k, .99))}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    summ = {"steps": {}, "notes": "S0 audit. Rates are simultaneous non-coverage over J = 12 at nominal 5%."}
    cells = []
    for st in STEPS:
        rows = load(a.raw, f"{st}_0*.json")
        if not rows:
            continue
        names = [c[0] for c in ladder_contrasts(st)]
        ev = evaluate(rows, names)
        ev["names"] = names
        summ["steps"][st] = ev
        for m in METHODS:
            e = ev[m]
            cells.append({"step": st, "method": m, "R": ev["R"], "k": e["k"], "rate": e["rate"],
                          "cp_lo": e["cp"][0], "cp_hi": e["cp"][1], "cp_up1": e["cp"][2],
                          "mean_mult": e["mean_mult"], "mean_hw_bp": e["mean_hw_bp"],
                          "se_ratio_mean": e["se_ratio_mean"], "max_marginal": max(e["marginal_rate"]),
                          "argmax_top": names[int(np.argmax(e["argmax_freq_misses"]))] if e["k"] else ""})
        print(st, {m: round(ev[m]["rate"], 4) for m in METHODS}, flush=True)
    pd.DataFrame(cells).to_csv(os.path.join(a.out, "per_cell.csv"), index=False)
    # B effect on the L4 subset
    rb = load(a.raw, "L4_B5k_*.json")
    if rb:
        th = np.array([r["th"] for r in rb])
        err = th - np.array(rb[0]["truth"])
        R = len(rb)
        be = {"R": R}
        for lab, sek, q1, q2 in (("ii_iid_bt", "se_iid", "q_iid", "q_iid_B5k"),
                                 ("iii_bt_L24_b20", "se_hac20", "q_bt24", "q_bt24_B5k")):
            se = np.array([r[sek] for r in rb])
            a1 = np.array([r[q1] for r in rb])
            a2 = np.array([r[q2] for r in rb])
            k1 = int((np.abs(err) > a1[:, None] * se).any(1).sum())
            k2 = int((np.abs(err) > a2[:, None] * se).any(1).sum())
            be[lab] = {"B999": {"k": k1, "rate": k1 / R, "cp": cp(k1, R), "mean_q": float(a1.mean())},
                       "B4999": {"k": k2, "rate": k2 / R, "cp": cp(k2, R), "mean_q": float(a2.mean())},
                       "mean_q_diff": float((a2 - a1).mean()), "sd_q_diff": float((a2 - a1).std())}
        summ["B_effect_L4_subset"] = be
    summ["mask_resampling"] = mask_resampling_stats()
    # E: ratio target
    from pipeline import CONTRASTS as C6, POLICIES as P6
    from pipeline2 import CONTRASTS2, POLICIES2
    gaps = {}
    for sc in ("F1", "F2", "F2c"):
        p1 = os.path.join(RES, f"per_rep_{sc}_truth.csv")
        if os.path.exists(p1):
            gaps[f"first_run_{sc}"] = ratio_gap(p1, P6, C6)
        p2 = os.path.join(RES, "phaseD", f"per_rep_{sc}_truth.csv")
        if os.path.exists(p2):
            gaps[f"phaseD_{sc}"] = ratio_gap(p2, POLICIES2, CONTRASTS2)
    summ["ratio_target_gap"] = gaps
    with open(os.path.join(a.out, "summary_audit_s0.json"), "w") as f:
        json.dump(summ, f, indent=1)


if __name__ == "__main__":
    main()

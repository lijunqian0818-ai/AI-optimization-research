"""Evaluation of precision_v9 coverage runs (SPEC §4-§5).

python analyze.py --raw ../../results/precision_v9/raw --out ../../results/precision_v9
Writes per-replication CSVs, summary.json and tables.md.
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

from intervals import simultaneous_intervals
from pipeline import CONTRASTS, POLICIES, Params, contrast_list
from run_sim import s0_truth

P_MAX = 0.06
NAMES = [c[0] for c in CONTRASTS]


def load(raw, scen, mode):
    rows = []
    for fn in sorted(glob.glob(os.path.join(raw, f"{scen}_{mode}_*.json"))):
        if fn.endswith("_series.npz"):
            continue
        with open(fn) as f:
            rows += json.load(f)
    if not rows:
        return None
    return pd.DataFrame(rows).sort_values("rep").reset_index(drop=True)


def cp(k, n, conf=0.95):
    lo = 0.0 if k == 0 else beta.ppf((1 - conf) / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - (1 - conf) / 2, k + 1, n - k)
    up1 = 1.0 if k == n else beta.ppf(conf, k + 1, n - k)
    return lo, hi, up1


def truth_from(df):
    th, mc = np.zeros(len(CONTRASTS)), np.zeros(len(CONTRASTS))
    R = len(df)
    for j, (nm, g, h, late) in enumerate(CONTRASTS):
        sfx = "late" if late else ""
        Ng, Sg = df[f"sumN{sfx}_{POLICIES[g]}"].values, df[f"sumS{sfx}_{POLICIES[g]}"].values
        Nh, Sh = df[f"sumN{sfx}_{POLICIES[h]}"].values, df[f"sumS{sfx}_{POLICIES[h]}"].values
        Vg, Vh = Ng.mean() / Sg.mean(), Nh.mean() / Sh.mean()
        th[j] = Vg - Vh
        psi = (Ng - Vg * Sg) / Sg.mean() - (Nh - Vh * Sh) / Sh.mean()
        mc[j] = psi.std(ddof=1) / np.sqrt(R)
    return th, mc


def evaluate(cov, th, mc):
    R = len(cov)
    TH = np.stack([cov[f"th_{n}"].values for n in NAMES], 1)
    SE = np.stack([cov[f"se_{n}"].values for n in NAMES], 1)
    q = cov["q"].values
    z = cov["z_bonf"].values
    app = cov["primary_applicable"].values.astype(bool)
    out = {"R": R, "truth_bp": (th * 1e4).tolist(), "truth_mcse_bp": (mc * 1e4).tolist(),
           "primary_inapplicable": int((~app).sum()),
           "zero_se_count": int(sum(cov[f"zse_{n}"].sum() for n in NAMES)),
           "void_total": int(sum(cov[f"void_{n}"].sum() for n in NAMES))}
    err = TH - th[None, :]
    out["bias_bp"] = (err.mean(0) * 1e4).tolist()
    out["bias_se_bp"] = (np.sqrt(err.std(0, ddof=1) ** 2 / R + mc ** 2) * 1e4).tolist()
    out["rmse_bp"] = (np.sqrt((err ** 2).mean(0)) * 1e4).tolist()
    out["sd_thetahat_bp"] = (TH.std(0, ddof=1) * 1e4).tolist()
    out["mean_se_bp"] = (SE.mean(0) * 1e4).tolist()
    out["se_ratio"] = (SE.mean(0) / TH.std(0, ddof=1)).tolist()
    out["rms_se_ratio"] = (np.sqrt((SE ** 2).mean(0)) / TH.std(0, ddof=1)).tolist()
    out["q"] = {"mean": float(q.mean()), "p05": float(np.quantile(q, .05)),
                "p50": float(np.median(q)), "p95": float(np.quantile(q, .95)),
                "min": float(q.min()), "max": float(q.max()), "z_bonf": float(z[0])}
    lo_b, hi_b = th - 2 * mc, th + 2 * mc
    for rule in ("primary", "fallback"):
        mult = np.where(app, q, z) if rule == "primary" else z
        hw = mult[:, None] * SE
        L, U = TH - hw, TH + hw
        miss = {"point": (th[None] < L) | (th[None] > U),
                "lenient": (hi_b[None] < L) | (lo_b[None] > U),
                "conservative": (lo_b[None] < L) | (hi_b[None] > U)}
        res = {}
        for kind, M in miss.items():
            k = int(M.any(1).sum())
            lo, hi, up1 = cp(k, R)
            res[f"sim_{kind}"] = {"k": k, "rate": k / R, "cp_lo": lo, "cp_hi": hi, "cp_up1": up1}
            res[f"marg_{kind}"] = []
            for j in range(len(NAMES)):
                kj = int(M[:, j].sum())
                l2, h2, u2 = cp(kj, R)
                res[f"marg_{kind}"].append({"k": kj, "rate": kj / R, "cp_lo": l2, "cp_hi": h2})
            # one-sided misses (point truth) for the direction of failure
        Mp = miss["point"]
        res["miss_below"] = [int((th[j] < L[:, j]).sum()) for j in range(len(NAMES))]
        res["miss_above"] = [int((th[j] > U[:, j]).sum()) for j in range(len(NAMES))]
        res["halfwidth_bp"] = {n: {"mean": float(hw[:, j].mean() * 1e4),
                                   "p05": float(np.quantile(hw[:, j], .05) * 1e4),
                                   "p50": float(np.median(hw[:, j]) * 1e4),
                                   "p95": float(np.quantile(hw[:, j], .95) * 1e4)}
                               for j, n in enumerate(NAMES)}
        up = res["sim_conservative"]["cp_up1"]
        pt = res["sim_lenient"]["rate"]
        res["verdict"] = "PASS" if up <= P_MAX else ("FAIL" if pt > P_MAX else "UNDETERMINED")
        out[rule] = res
    return out


def block_sensitivity(raw, scen, th, mc, n_max=500):
    p = Params()
    cs = contrast_list(p)
    files = sorted(glob.glob(os.path.join(raw, f"{scen}_cov_*_series.npz")))
    Ns, Ss, reps = [], [], []
    for fn in files:
        d = np.load(fn)
        Ns.append(d["N"]); Ss.append(d["S"]); reps.append(d["reps"])
    if not Ns:
        return None
    N = np.concatenate(Ns); S = np.concatenate(Ss); reps = np.concatenate(reps)
    o = np.argsort(reps)
    N, S, reps = N[o][:n_max], S[o][:n_max], reps[o][:n_max]
    from run_sim import seeds_for
    out = {}
    lo_b, hi_b = th - 2 * mc, th + 2 * mc
    for L, tag in ((12, 4243), (24, None), (48, 4244)):
        if tag is None:
            continue
        kp = {"point": 0, "conservative": 0}
        kf = {"point": 0, "conservative": 0}
        qs = []
        for i in range(len(reps)):
            _, hold = seeds_for(scen, "cov", int(reps[i]))
            r = simultaneous_intervals(N[i][:, None, :].astype(float), S[i][:, None, :].astype(float),
                                       cs, B=2000, mean_block=L, rng=np.random.default_rng([hold, tag]))
            qs.append(r.q)
            for rule, k in (("p", kp), ("f", kf)):
                lo = r.lo if rule == "p" else r.lo_fallback
                hi = r.hi if rule == "p" else r.hi_fallback
                k["point"] += int(np.any((th < lo) | (th > hi)))
                k["conservative"] += int(np.any((lo_b < lo) | (hi_b > hi)))
        n = len(reps)
        out[f"L{L}"] = {"n": n, "q_mean": float(np.mean(qs)),
                        "primary": {kk: {"k": v, "rate": v / n, "cp": cp(v, n)[:2]} for kk, v in kp.items()},
                        "fallback": {kk: {"k": v, "rate": v / n, "cp": cp(v, n)[:2]} for kk, v in kf.items()}}
    # the same 500 reps at L = 24 from the stored primary results, for comparison
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scen", nargs="*", default=["S0", "F1", "F2", "F3a", "F3b", "F2c"])
    ap.add_argument("--no-block", action="store_true")
    a = ap.parse_args()
    summary = {}
    for scen in a.scen:
        cov = load(a.raw, scen, "cov")
        if cov is None:
            print("no coverage data for", scen)
            continue
        cov.to_csv(os.path.join(a.out, f"per_rep_{scen}_cov.csv"), index=False)
        if scen == "S0":
            th, mc = s0_truth(), np.zeros(len(NAMES))
        elif scen in ("F3a", "F3b"):
            th, mc = np.zeros(len(NAMES)), np.zeros(len(NAMES))
        else:
            tr = load(a.raw, scen, "truth")
            if tr is None:
                print("no truth data for", scen)
                continue
            tr.to_csv(os.path.join(a.out, f"per_rep_{scen}_truth.csv"), index=False)
            th, mc = truth_from(tr)
            # also: the coverage replications' own pooled ratio (a check of the truth estimate)
        ev = evaluate(cov, th, mc)
        if scen not in ("S0", "F3a", "F3b"):
            th2, mc2 = truth_from(cov)
            ev["truth_from_cov_reps_bp"] = (th2 * 1e4).tolist()
            ev["truth_from_cov_reps_mcse_bp"] = (mc2 * 1e4).tolist()
            ev["R_truth"] = len(tr)
        # first-500 L=24 for the block comparison
        sub = cov[cov.rep < 500]
        if len(sub):
            e24 = evaluate(sub.reset_index(drop=True), th, mc)
            ev["first500_L24"] = {r: {kk: e24[r][f"sim_{kk}"] for kk in ("point", "conservative")}
                                  for r in ("primary", "fallback")}
        if not a.no_block:
            ev["block"] = block_sensitivity(a.raw, scen, th, mc)
        summary[scen] = ev
        print(scen, "R", ev["R"], "primary", ev["primary"]["sim_point"]["rate"], ev["primary"]["verdict"],
              "fallback", ev["fallback"]["sim_point"]["rate"], ev["fallback"]["verdict"], flush=True)
    with open(os.path.join(a.out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)


if __name__ == "__main__":
    main()

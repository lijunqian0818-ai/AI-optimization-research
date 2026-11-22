"""Phase D evaluation and Phase C replication count.

python analyze_phaseD.py --raw ../../results/precision_v9/phaseD/raw --out ../../results/precision_v9/phaseD
"""
import os

for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[_v] = "1"

import argparse
import glob
import json

import numpy as np
import pandas as pd
from scipy.stats import beta, binom, norm

from pipeline2 import CONTRASTS2, POLICIES2, policy_level_truth

NAMES = [c[0] for c in CONTRASTS2]
J = len(NAMES)
LS = (10, 24, 48)
BANDS = (5, 10, 20)
TYPES = ("stat", "circ")
P_MAX = 0.06
REGION_LEVEL = 0.99
Z_BONF = float(norm.ppf(1 - 0.05 / (2 * J)))
SCEN = ["S0", "S1", "S2", "F1", "F2", "F2c", "F3a", "F3b"]


def load(raw, scen, mode):
    rows = []
    for fn in sorted(glob.glob(os.path.join(raw, f"{scen}_{mode}_*.json"))):
        with open(fn) as f:
            rows += json.load(f)
    return pd.DataFrame(rows).sort_values("rep").reset_index(drop=True) if rows else None


def cp(k, n, conf=0.95):
    lo = 0.0 if k == 0 else beta.ppf((1 - conf) / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - (1 - conf) / 2, k + 1, n - k)
    up1 = 1.0 if k == n else beta.ppf(conf, k + 1, n - k)
    return float(lo), float(hi), float(up1)


def truth_region(tr, level=REGION_LEVEL, seed=10_999_999):
    """Ratio-of-means truth, delta-method MC s.e., and a simultaneous (max-type) region
    theta_j +- c * mcse_j with c the `level` quantile of max_j |Z_j|, Z ~ N(0, Corr(psi))."""
    R = len(tr)
    th = np.zeros(J)
    psi = np.zeros((R, J))
    for j, (nm, g, h, late) in enumerate(CONTRASTS2):
        sfx = "late" if late else ""
        Ng, Sg = tr[f"sumN{sfx}_{POLICIES2[g]}"].values, tr[f"sumS{sfx}_{POLICIES2[g]}"].values
        Nh, Sh = tr[f"sumN{sfx}_{POLICIES2[h]}"].values, tr[f"sumS{sfx}_{POLICIES2[h]}"].values
        Vg, Vh = Ng.mean() / Sg.mean(), Nh.mean() / Sh.mean()
        th[j] = Vg - Vh
        psi[:, j] = (Ng - Vg * Sg) / Sg.mean() - (Nh - Vh * Sh) / Sh.mean()
    mc = psi.std(0, ddof=1) / np.sqrt(R)
    C = np.corrcoef(psi.T)
    w, U = np.linalg.eigh(C)
    w = np.clip(w, 0, None)
    rng = np.random.default_rng(seed)
    Z = rng.standard_normal((200_000, J)) @ (U * np.sqrt(w)).T
    c = float(np.quantile(np.abs(Z).max(1), level))
    return th, mc, c


def rule_columns(df):
    """{config label: (multiplier array (R,) or scalar, se matrix (R, J))}."""
    out = {}
    for typ in TYPES:
        for L in LS:
            for b in BANDS:
                qc = f"q_{typ}{L}_b{b}"
                if qc not in df:
                    continue
                se = np.stack([df[f"hse{b}_{n}"].values for n in NAMES], 1)
                app = df[f"app_{typ}{L}_b{b}"].values.astype(bool)
                mult = np.where(app, df[qc].values, Z_BONF)
                out[f"bt_{typ}_L{L}_b{b}"] = (mult, se)
    for b in BANDS:
        se = np.stack([df[f"hse{b}_{n}"].values for n in NAMES], 1)
        out[f"fallback_hac_b{b}"] = (np.full(len(df), Z_BONF), se)
    for L in (24, 10):
        se = np.stack([df[f"oldse{L}_{n}"].values for n in NAMES], 1)
        out[f"old_stat_L{L}"] = (df[f"oldq_L{L}"].values, se)
    return out


def evaluate(df, th, mc, c_region, exact):
    R = len(df)
    TH = np.stack([df[f"th_{n}"].values for n in NAMES], 1)
    sd = TH.std(0, ddof=1)
    lo_b, hi_b = th - c_region * mc, th + c_region * mc
    res = {"R": R, "bias_bp": ((TH - th).mean(0) * 1e4).tolist(), "sd_thetahat_bp": (sd * 1e4).tolist()}
    cfg = {}
    for lab, (mult, se) in rule_columns(df).items():
        hw = np.asarray(mult)[:, None] * se
        L_, U_ = TH - hw, TH + hw
        miss = {"point": ((th < L_) | (th > U_)).any(1),
                "lenient": ((hi_b < L_) | (lo_b > U_)).any(1),
                "conservative": ((lo_b < L_) | (hi_b > U_)).any(1)}
        e = {}
        for k, m in miss.items():
            kk = int(m.sum())
            e[k] = {"k": kk, "rate": kk / R, "cp": cp(kk, R)}
        add = 0.0 if exact else 1 - REGION_LEVEL
        e["ub_conservative_plus_region"] = e["conservative"]["cp"][2] + add
        e["se_ratio_mean"] = float(np.mean(se.mean(0) / sd))
        e["se_ratio_min"] = float(np.min(se.mean(0) / sd))
        e["se_ratio_by_contrast"] = (se.mean(0) / sd).tolist()
        e["halfwidth_bp_mean"] = float(hw.mean() * 1e4)
        e["halfwidth_bp_by_contrast"] = (hw.mean(0) * 1e4).tolist()
        e["mult_mean"] = float(np.mean(mult))
        e["marg_point_rate"] = ((th < L_) | (th > U_)).mean(0).tolist()
        cfg[lab] = e
    res["configs"] = cfg
    for c in ("t_gen", "t_bt", "t_old"):
        if c in df:
            res[f"mean_{c}_s"] = float(df[c].mean())
    res["any_inapplicable"] = int(sum((~df[c].astype(bool)).sum() for c in df.columns if c.startswith("app_")))
    res["zero_den_any"] = int(df["zero_den_any"].sum())
    res["zero_hse_any"] = int(df["zero_hse_any"].sum())
    return res


def pass_prob(n, p, thr=P_MAX):
    """P(one-sided 95% exact upper bound of k/n <= thr) for k ~ Bin(n, p)."""
    ks = np.arange(n + 1)
    ub = np.where(ks == n, 1.0, beta.ppf(0.95, ks + 1, n - ks))
    kmax = ks[ub <= thr]
    if kmax.size == 0:
        return 0.0, -1
    km = int(kmax.max())
    return float(binom.cdf(km, n, p)), km


def phase_c_count(n_scen=8, p=0.05, target=0.9):
    out = {}
    for delta in (0.0, 0.001, 0.0025, 0.005, 0.01):
        thr = P_MAX - delta
        found = None
        for n in list(range(1000, 40001, 250)):
            pp, km = pass_prob(n, p, thr)
            if pp ** n_scen >= target:
                found = {"n": n, "per_scenario_pass_prob": pp, "all_pass_prob": pp ** n_scen,
                         "max_misses_allowed": km}
                break
        out[f"delta_{delta}"] = found
    # mixed: 5 exact-truth scenarios (delta 0) and 3 estimated-truth scenarios with delta
    mixed = {}
    for delta in (0.001, 0.0025, 0.005, 0.01):
        found = None
        for n in range(1000, 40001, 250):
            p0, _ = pass_prob(n, p, P_MAX)
            p1, _ = pass_prob(n, p, P_MAX - delta)
            if p0 ** 5 * p1 ** 3 >= target:
                found = {"n": n, "all_pass_prob": p0 ** 5 * p1 ** 3}
                break
        mixed[f"delta_{delta}"] = found
    out["mixed_5exact_3estimated"] = mixed
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    summ = {"notes": "Phase D exploratory; no verdict. Rates are simultaneous non-coverage over 12 contrasts.",
            "z_bonf": Z_BONF, "region_level": REGION_LEVEL, "scenarios": {}}
    for scen in SCEN:
        df = load(a.raw, scen, "cov")
        if df is None:
            continue
        df.to_csv(os.path.join(a.out, f"per_rep_{scen}_cov.csv"), index=False)
        if scen in ("S0", "S1", "S2"):
            th, mc, c, exact = policy_level_truth(), np.zeros(J), 0.0, True
        elif scen in ("F3a", "F3b"):
            th, mc, c, exact = np.zeros(J), np.zeros(J), 0.0, True
        else:
            tr = load(a.raw, scen, "truth")
            if tr is None:
                print("no truth for", scen)
                continue
            tr.to_csv(os.path.join(a.out, f"per_rep_{scen}_truth.csv"), index=False)
            th, mc, c = truth_region(tr)
            exact = False
        ev = evaluate(df, th, mc, c, exact)
        ev["truth_bp"] = (th * 1e4).tolist()
        ev["truth_mcse_bp"] = (mc * 1e4).tolist()
        ev["truth_region_c"] = c
        ev["exact_truth"] = exact
        if not exact:
            ev["R_truth"] = len(tr)
        summ["scenarios"][scen] = ev
        print(scen, len(df), flush=True)
    # cross-scenario: configurations with every scenario's UB <= 6%
    scs = summ["scenarios"]
    labels = sorted(set.intersection(*[set(v["configs"]) for v in scs.values()])) if scs else []
    tab = {}
    for lab in labels:
        ubs = {s: scs[s]["configs"][lab]["conservative"]["cp"][2] for s in scs}
        ubr = {s: scs[s]["configs"][lab]["ub_conservative_plus_region"] for s in scs}
        tab[lab] = {"max_ub_conservative": max(ubs.values()), "worst_scenario": max(ubs, key=ubs.get),
                    "all_ub_le_6pct": all(v <= P_MAX for v in ubs.values()),
                    "all_ub_plus_region_le_6pct": all(v <= P_MAX for v in ubr.values()),
                    "max_point_rate": max(scs[s]["configs"][lab]["point"]["rate"] for s in scs)}
    summ["cross_scenario"] = tab
    summ["scenarios_included"] = list(scs)
    summ["phase_c_replications"] = phase_c_count(n_scen=8)
    with open(os.path.join(a.out, "summary_phaseD.json"), "w") as f:
        json.dump(summ, f, indent=1)


if __name__ == "__main__":
    main()

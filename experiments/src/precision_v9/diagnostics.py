"""Post-hoc diagnostics (added AFTER the coverage results were seen; logged in SPEC Deviations).

(a) S0 with mean block 1, 6 and 24 on fresh replications (implementation check: with i.i.d. data and
    L = 1 the rule should be close to nominal).
(b) Oracle decomposition on the stored per-replication results of every scenario: non-coverage
    when the bootstrap s.e. is replaced by the Monte-Carlo sd of theta_hat (oracle), and when it is
    only rescaled by its average bias (sd / mean se), with the same multiplier q (per replication)
    or z_bonf.
(c) Distribution of the studentised error (theta_hat - theta)/se: sd and tail frequencies.
"""
import os

for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[_v] = "1"

import json
import sys

import numpy as np
import pandas as pd

from analyze import NAMES, cp
from intervals import simultaneous_intervals
from pipeline import Params, contrast_list
from run_sim import s0_series, s0_truth

OUT = sys.argv[1]


def s0_blocks(n=1000):
    p = Params()
    cs = contrast_list(p)
    th = s0_truth()
    res = {}
    for L in (1, 6, 24):
        k_p = k_f = 0
        for rep in range(n):
            hold = 5_000_000 + rep          # fresh seeds, disjoint from the S0 coverage run
            N, S = s0_series(hold, p.holdout_days)
            r = simultaneous_intervals(N, S, cs, B=2000, mean_block=L,
                                       rng=np.random.default_rng([hold, 77]))
            k_p += int(np.any((th < r.lo) | (th > r.hi)))
            k_f += int(np.any((th < r.lo_fallback) | (th > r.hi_fallback)))
        res[f"L{L}"] = {"n": n, "primary": [k_p, k_p / n, *cp(k_p, n)[:2]],
                        "fallback": [k_f, k_f / n, *cp(k_f, n)[:2]]}
        print("S0 block", L, res[f"L{L}"], flush=True)
    return res


def oracle(summary):
    out = {}
    for scen, ev in summary.items():
        df = pd.read_csv(os.path.join(OUT, f"per_rep_{scen}_cov.csv"))
        th = np.array(ev["truth_bp"]) * 1e-4
        TH = np.stack([df[f"th_{n}"].values for n in NAMES], 1)
        SE = np.stack([df[f"se_{n}"].values for n in NAMES], 1)
        q = df["q"].values[:, None]
        z = df["z_bonf"].values[0]
        R = len(df)
        err = TH - th[None]
        sd = err.std(0, ddof=1)
        t = err / SE
        o = {}
        for lab, scale in (("bootstrap_se", SE), ("bias_rescaled_se", SE * (sd / SE.mean(0))[None]),
                           ("oracle_sd", np.repeat(sd[None], R, 0))):
            for mlab, mult in (("q", q), ("z_bonf", z)):
                k = int((np.abs(err) > mult * scale).any(1).sum())
                o[f"{lab}|{mlab}"] = [k, k / R, *cp(k, R)[:2]]
        o["t_sd"] = t.std(0, ddof=1).tolist()
        o["t_tail_gt_2.55"] = (np.abs(t) > 2.55).mean(0).tolist()
        o["se_cv"] = (SE.std(0, ddof=1) / SE.mean(0)).tolist()
        out[scen] = o
        print(scen, {k: v for k, v in o.items() if "|" in k}, flush=True)
    return out


if __name__ == "__main__":
    with open(os.path.join(OUT, "summary.json")) as f:
        summary = json.load(f)
    res = {"oracle": oracle(summary), "s0_blocks": s0_blocks()}
    with open(os.path.join(OUT, "diagnostics.json"), "w") as f:
        json.dump(res, f, indent=1)

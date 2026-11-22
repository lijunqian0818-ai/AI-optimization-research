"""Estimands, metrics and the date-block bootstrap of the pilot (PLAN 8, 9, 10).

All statistics are functions of date-indexed records; the bootstrap resamples decision dates jointly
for every series (stationary bootstrap, mean block length 4 (H+1) = 24), ratio statistics are
recomputed as ratios of resampled sums (PLAN 10).  Seeds: the series are averaged over seeds before
the bootstrap; the spread over seeds is reported separately (mean and standard deviation of the
per-seed statistic), never merged with a bootstrap interval.
"""
from __future__ import annotations

import numpy as np

A = 242.0                                    # annualisation constant (PLAN 8)


def stationary_indices(n: int, B: int, mean_block: float, seed: int) -> np.ndarray:
    """B x n index matrix of the stationary bootstrap (Politis-Romano), wrap-around."""
    rng = np.random.default_rng(seed)
    p = 1.0 / mean_block
    idx = np.empty((B, n), dtype=np.int64)
    for b in range(B):
        start = rng.integers(n, size=n)
        new = rng.random(n) < p
        new[0] = True
        cur = 0
        for t in range(n):
            cur = start[t] if new[t] else (cur + 1) % n
            idx[b, t] = cur
    return idx


def summarize(est: float, boot: np.ndarray) -> dict:
    b = boot[np.isfinite(boot)]
    if not len(b):
        return {"estimate": est, "se": np.nan, "ci95": [np.nan, np.nan], "ci90": [np.nan, np.nan], "B_valid": 0}
    return {"estimate": est, "se": float(b.std(ddof=1)) if len(b) > 1 else np.nan,
            "ci95": [float(np.quantile(b, 0.025)), float(np.quantile(b, 0.975))],
            "ci90": [float(np.quantile(b, 0.05)), float(np.quantile(b, 0.95))], "B_valid": int(len(b))}


def ratio_boot(num: np.ndarray, den: np.ndarray, idx: np.ndarray) -> dict:
    est = float(num.sum() / den.sum()) if den.sum() else np.nan
    with np.errstate(all="ignore"):
        boot = num[idx].sum(axis=1) / den[idx].sum(axis=1)
    return summarize(est, boot)


def diff_ratio_boot(n1, d1, n2, d2, idx) -> dict:
    with np.errstate(all="ignore"):
        est = float(n1.sum() / d1.sum() - n2.sum() / d2.sum())
        boot = n1[idx].sum(1) / d1[idx].sum(1) - n2[idx].sum(1) / d2[idx].sum(1)
    return summarize(est, boot)


def mean_boot(x: np.ndarray, idx: np.ndarray, scale: float = 1.0) -> dict:
    return summarize(float(x.mean() * scale), x[idx].mean(axis=1) * scale)


def wealth_metrics(r: np.ndarray) -> dict:
    """Q-total descriptive metrics of a daily return series (PLAN 8.1, 9.1)."""
    T = len(r)
    if T == 0:
        return {}
    w = np.cumprod(1.0 + r)
    peak = np.maximum.accumulate(np.r_[1.0, w])[1:]
    dd = 1.0 - w / peak
    sd = r.std(ddof=1) if T > 1 else np.nan
    return {"AR": float(A / T * r.sum()), "TW": float(w[-1]), "CAGR": float(w[-1] ** (A / T) - 1.0),
            "MDD": float(dd.max()), "Sharpe_desc": float(r.mean() / sd * np.sqrt(A)) if sd and sd > 0 else np.nan,
            "days": int(T)}


def tost(est: float, se: float, bound: float) -> dict:
    """Two one-sided tests at bound +-Delta_ord (PLAN 8.4 card C1 / C2 form), normal approximation;
    exploratory in the pilot (no Holm family is formed)."""
    from math import erf, sqrt
    if not (np.isfinite(est) and np.isfinite(se) and se > 0):
        return {"p_eq": np.nan}
    Phi = lambda z: 0.5 * (1 + erf(z / sqrt(2)))                      # noqa: E731
    tL, tU = (est + bound) / se, (bound - est) / se
    return {"p_eq": float(max(1 - Phi(tL), 1 - Phi(tU))), "bound": bound}


def two_sided_p(est: float, se: float) -> float:
    from math import erf, sqrt
    if not (np.isfinite(est) and np.isfinite(se) and se > 0):
        return np.nan
    z = abs(est / se)
    return float(2 * (1 - 0.5 * (1 + erf(z / sqrt(2)))))

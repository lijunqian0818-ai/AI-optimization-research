"""Simultaneous-interval rule of PLAN v0.9.3 §A4.1 (experiment precision_v9).

Input per policy g and seed s: daily numerator N[g, s, t] (sum of net returns of the
submitted orders, unfilled = 0) and daily submitted count S[g, s, t], t = 0..T-1.

* Seed averaging: daily totals are averaged over seeds BEFORE any ratio (§A8 (c)).
* Policy value on a contrast window m_j (0/1 per date): V_j^g = sum_t m N^g / sum_t m S^g.
* Contrast delta_j = V_j^g - V_j^h (always a difference of two ratios).
* Paired stationary bootstrap over dates (Politis & Romano 1994), circular, mean block L;
  the SAME resampled dates for every policy, seed and contrast; both ratios recomputed.
* se_j = sd of theta*_j over valid resamples; q = 95% quantile of
  max_j |theta*_j - theta_hat_j| / se_j; interval theta_hat_j +- q se_j.
* Fallback: theta_hat_j +- z_{1 - 0.05/(2m)} se_j (Bonferroni-normal).

Edge-case rulings (PI, 2026-11-17):
 (1) se_j == 0 -> degenerate interval [theta_hat_j, theta_hat_j]; excluded from the max
     statistic; the Bonferroni m stays the family size J. If decisions are identical on every day theta_hat_j == 0 exactly.
     If se_j == 0 but the numerators are not identical the flag `zero_se_nonidentical` is set.
 (2) a policy with zero total submissions on a window has V = 0 and is flagged; a resample in
     which a needed denominator is zero is void for that contrast only and counted; if more
     than 0.1% of resamples are void for any contrast, the primary rule is inapplicable for the
     study and the fallback is used.
 (3) a contrast with a later start: dates outside its window carry zero numerator and zero
     count for BOTH of its policies (the window mask m_j).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.stats import norm

VOID_FRACTION_LIMIT = 0.001  # 0.1% of resamples


def stationary_bootstrap_counts(T: int, B: int, mean_block: float, rng: np.random.Generator) -> np.ndarray:
    """Return a (B, T) int32 matrix: how often each date appears in each resample.

    Circular stationary bootstrap: position 0 starts a block; each later position starts a new
    block with probability p = 1/mean_block, otherwise continues with the next date (mod T).
    Block starts are uniform on {0..T-1}. Each resample has exactly T dates.
    """
    idx = stationary_bootstrap_indices(T, B, mean_block, rng)
    flat = (np.arange(B)[:, None] * T + idx).ravel()
    return np.bincount(flat, minlength=B * T).reshape(B, T).astype(np.int32)


def stationary_bootstrap_indices(T: int, B: int, mean_block: float, rng: np.random.Generator) -> np.ndarray:
    """Same construction as `stationary_bootstrap_counts` but returns the (B, T) date indices."""
    if T <= 0 or B <= 0:
        raise ValueError("T and B must be positive")
    p = 1.0 / float(mean_block)
    new = rng.random((B, T)) < p
    new[:, 0] = True
    pos = np.arange(T)
    last_start = np.maximum.accumulate(np.where(new, pos[None, :], 0), axis=1)
    offset = pos[None, :] - last_start
    block_id = np.cumsum(new, axis=1) - 1
    starts = rng.integers(0, T, size=(B, T))
    start_of = np.take_along_axis(starts, block_id, axis=1)
    return (start_of + offset) % T


@dataclass
class Contrast:
    name: str
    g: int          # index of the first policy
    h: int          # index of the second policy
    mask: np.ndarray | None = None  # 0/1 per date; None = whole window


@dataclass
class IntervalResult:
    names: list
    theta_hat: np.ndarray
    se: np.ndarray
    q: float
    z_bonf: float
    lo: np.ndarray            # primary (or fallback if primary inapplicable) lower bound
    hi: np.ndarray
    lo_primary: np.ndarray    # primary rule bounds (nan if inapplicable)
    hi_primary: np.ndarray
    lo_fallback: np.ndarray
    hi_fallback: np.ndarray
    primary_applicable: bool
    void_counts: np.ndarray   # per contrast, number of void resamples
    zero_se: np.ndarray       # bool per contrast
    zero_se_nonidentical: np.ndarray
    zero_policy_flags: dict = field(default_factory=dict)  # (contrast, policy) -> True if zero submissions
    V_hat: dict = field(default_factory=dict)
    B: int = 0


def seed_average(N: np.ndarray, S: np.ndarray):
    """N, S of shape (P, n_seeds, T) or (P, T). Returns (P, T) seed averages."""
    N = np.asarray(N, dtype=float)
    S = np.asarray(S, dtype=float)
    if N.ndim == 3:
        N = N.mean(axis=1)
        S = S.mean(axis=1)
    return N, S


def _ratio(num, den):
    """Ratio with the V = 0 convention for zero denominators; returns (value, zero_flag)."""
    num = np.asarray(num, dtype=float)
    den = np.asarray(den, dtype=float)
    zero = den == 0
    with np.errstate(divide="ignore", invalid="ignore"):
        v = np.where(zero, 0.0, num / np.where(zero, 1.0, den))
    return v, zero


def point_estimates(N, S, contrasts):
    """theta_hat per contrast and V per (contrast, policy); flags zero-submission policies."""
    Nbar, Sbar = seed_average(N, S)
    T = Nbar.shape[1]
    th = np.empty(len(contrasts))
    V, zf = {}, {}
    for j, c in enumerate(contrasts):
        m = np.ones(T) if c.mask is None else np.asarray(c.mask, dtype=float)
        vg, zg = _ratio((Nbar[c.g] * m).sum(), (Sbar[c.g] * m).sum())
        vh, zh = _ratio((Nbar[c.h] * m).sum(), (Sbar[c.h] * m).sum())
        th[j] = float(vg) - float(vh)
        V[(c.name, c.g)] = float(vg)
        V[(c.name, c.h)] = float(vh)
        zf[(c.name, c.g)] = bool(zg)
        zf[(c.name, c.h)] = bool(zh)
    return th, V, zf


def bootstrap_contrasts(N, S, contrasts, counts):
    """theta*_{jb} for each resample (rows of `counts`), with void mask.

    Returns theta_star (B, J) (nan where void) and void (B, J) bool.
    """
    Nbar, Sbar = seed_average(N, S)
    T = Nbar.shape[1]
    J = len(contrasts)
    # build columns: for every contrast the masked series of its two policies
    cols = []
    for c in contrasts:
        m = np.ones(T) if c.mask is None else np.asarray(c.mask, dtype=float)
        cols += [Nbar[c.g] * m, Sbar[c.g] * m, Nbar[c.h] * m, Sbar[c.h] * m]
    M = np.stack(cols, axis=1)                      # (T, 4J)
    sums = counts.astype(float) @ M                 # (B, 4J)
    sums = sums.reshape(-1, J, 4)
    ng, sg, nh, sh = sums[..., 0], sums[..., 1], sums[..., 2], sums[..., 3]
    # a denominator is "zero" if the resampled count total is zero (counts are >= 0)
    void = (sg <= 0) | (sh <= 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        ts = ng / sg - nh / sh
    ts = np.where(void, np.nan, ts)
    return ts, void


def simultaneous_intervals(N, S, contrasts, B=2000, mean_block=24.0, alpha=0.05,
                           rng=None, counts=None, se_tol=1e-12) -> IntervalResult:
    """Scaled max-statistic simultaneous intervals and the Bonferroni-normal fallback."""
    if rng is None:
        rng = np.random.default_rng(0)
    Nbar, Sbar = seed_average(N, S)
    T = Nbar.shape[1]
    J = len(contrasts)
    th, V, zf = point_estimates(Nbar, Sbar, contrasts)
    if counts is None:
        counts = stationary_bootstrap_counts(T, B, mean_block, rng)
    B = counts.shape[0]
    ts, void = bootstrap_contrasts(Nbar, Sbar, contrasts, counts)
    void_counts = void.sum(axis=0)
    se = np.array([np.nanstd(ts[:, j], ddof=1) if (~void[:, j]).sum() > 1 else np.nan
                   for j in range(J)])
    # identical-decision detection: numerators and counts identical on every day of the window
    zero_se = np.zeros(J, bool)
    zero_se_nonid = np.zeros(J, bool)
    for j, c in enumerate(contrasts):
        scale = max(1.0, np.nanmax(np.abs(ts[:, j])) if np.isfinite(ts[:, j]).any() else 1.0)
        if not np.isfinite(se[j]) or se[j] <= se_tol * scale:
            zero_se[j] = True
            m = np.ones(T) if c.mask is None else np.asarray(c.mask, dtype=float)
            ident = np.array_equal(Nbar[c.g] * m, Nbar[c.h] * m) and np.array_equal(Sbar[c.g] * m, Sbar[c.h] * m)
            if ident:
                th[j] = 0.0
            else:
                zero_se_nonid[j] = True
            se[j] = 0.0
    active = ~zero_se
    primary_ok = bool(np.all(void_counts <= VOID_FRACTION_LIMIT * B))
    # max statistic over active, non-void contrasts of each resample
    if active.any():
        dev = np.abs(ts[:, active] - th[None, active]) / se[None, active]
        mstat = np.nanmax(np.where(np.isnan(dev), -np.inf, dev), axis=1)
        mstat = mstat[np.isfinite(mstat)]
        q = float(np.quantile(mstat, 1 - alpha)) if mstat.size else np.nan
    else:
        q = 0.0
    z = float(norm.ppf(1 - alpha / (2 * J)))
    lo_p, hi_p = th - q * se, th + q * se
    lo_f, hi_f = th - z * se, th + z * se
    if primary_ok:
        lo, hi = lo_p.copy(), hi_p.copy()
    else:
        lo, hi = lo_f.copy(), hi_f.copy()
        lo_p = np.full(J, np.nan)
        hi_p = np.full(J, np.nan)
    return IntervalResult(names=[c.name for c in contrasts], theta_hat=th, se=se, q=q, z_bonf=z,
                          lo=lo, hi=hi, lo_primary=lo_p, hi_primary=hi_p,
                          lo_fallback=lo_f, hi_fallback=hi_f, primary_applicable=primary_ok,
                          void_counts=void_counts, zero_se=zero_se,
                          zero_se_nonidentical=zero_se_nonid, zero_policy_flags=zf, V_hat=V, B=B)

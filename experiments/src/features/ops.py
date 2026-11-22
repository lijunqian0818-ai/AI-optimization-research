"""Causal rolling operators on numpy arrays.

Every operator returns an array of the input length whose element i depends on
elements i-n+1 .. i only, and is NaN unless that full window is available and
finite (PLAN 2.3: "a feature is NaN until its full window is available; no
partial-window values"). Each window is evaluated on its own (no running
sums), so a value does not depend on anything outside its window -- neither
on later rows (look-ahead) nor on where the series starts.
"""
from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def _roll(x: np.ndarray, n: int, fn) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    w = sliding_window_view(x, n)
    with np.errstate(all="ignore"):
        r = fn(w)
    out[n - 1:] = np.where(np.isfinite(w).all(axis=1), r, np.nan)
    return out


def _roll2(x: np.ndarray, y: np.ndarray, n: int, fn) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    wx, wy = sliding_window_view(x, n), sliding_window_view(y, n)
    with np.errstate(all="ignore"):
        r = fn(wx, wy)
    ok = np.isfinite(wx).all(axis=1) & np.isfinite(wy).all(axis=1)
    out[n - 1:] = np.where(ok, r, np.nan)
    return out


def ref(x: np.ndarray, d: int) -> np.ndarray:
    """Value d rows earlier (NaN for the first d rows)."""
    x = np.asarray(x, dtype=np.float64)
    out = np.full(len(x), np.nan)
    if d == 0:
        return x.copy()
    if len(x) > d:
        out[d:] = x[:-d]
    return out


def r_mean(x, n):
    return _roll(x, n, lambda w: w.mean(axis=1))


def r_sum(x, n):
    return _roll(x, n, lambda w: w.sum(axis=1))


def r_std(x, n):
    """Sample standard deviation (ddof = 1), as pandas / Qlib `Std`."""
    return _roll(x, n, lambda w: w.std(axis=1, ddof=1))


def r_max(x, n):
    return _roll(x, n, lambda w: w.max(axis=1))


def r_min(x, n):
    return _roll(x, n, lambda w: w.min(axis=1))


def r_quantile(x, n, q):
    """Linear-interpolation quantile (pandas default)."""
    return _roll(x, n, lambda w: np.quantile(w, q, axis=1))


def r_rank(x, n):
    """Percentile rank of the last value in its window (average rank / n)."""
    def fn(w):
        last = w[:, -1:]
        less = (w < last).sum(axis=1)
        eq = (w == last).sum(axis=1)
        return (less + (eq + 1) / 2.0) / n
    return _roll(x, n, fn)


def r_idxmax(x, n):
    """1-based position of the first maximum in the window (oldest = 1)."""
    return _roll(x, n, lambda w: w.argmax(axis=1) + 1.0)


def r_idxmin(x, n):
    return _roll(x, n, lambda w: w.argmin(axis=1) + 1.0)


def _reg(w):
    n = w.shape[1]
    xs = np.arange(n, dtype=np.float64)
    xc = xs - xs.mean()
    sxx = (xc * xc).sum()
    ym = w.mean(axis=1)
    # elementwise product and a per-row sum, NOT a BLAS matrix-vector product: BLAS results for a
    # given row can depend on the number of rows, which would break bit-reproducibility under truncation
    sxy = ((w - ym[:, None]) * xc).sum(axis=1)
    slope = sxy / sxx
    syy = ((w - ym[:, None]) ** 2).sum(axis=1)
    return slope, ym, xs.mean(), sxy, sxx, syy


def r_slope(x, n):
    """OLS slope of the window on 0..n-1."""
    return _roll(x, n, lambda w: _reg(w)[0])


def r_rsquare(x, n):
    """R-squared of that regression (NaN for a constant window)."""
    def fn(w):
        _, _, _, sxy, sxx, syy = _reg(w)
        return (sxy * sxy) / (sxx * syy)
    return _roll(x, n, fn)


def r_resi(x, n):
    """Residual of the last point of the window in that regression."""
    def fn(w):
        slope, ym, xm, _, _, _ = _reg(w)
        fitted_last = ym + slope * ((w.shape[1] - 1) - xm)
        return w[:, -1] - fitted_last
    return _roll(x, n, fn)


def r_corr(x, y, n):
    """Pearson correlation (NaN when either window is constant)."""
    def fn(wx, wy):
        dx = wx - wx.mean(axis=1, keepdims=True)
        dy = wy - wy.mean(axis=1, keepdims=True)
        return (dx * dy).sum(axis=1) / np.sqrt((dx * dx).sum(axis=1) * (dy * dy).sum(axis=1))
    return _roll2(x, y, n, fn)


def r_count(flag, n):
    """Number of True (1.0) values in the window; NaN flags make the window NaN."""
    return _roll(np.asarray(flag, dtype=np.float64), n, lambda w: w.sum(axis=1))

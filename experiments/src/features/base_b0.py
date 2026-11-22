"""B0 -- Alpha158-style price-volume features (PLAN 4.1), own pandas/numpy code.

Definitions are re-implemented from the public expressions in Qlib's
`qlib/contrib/data/loader.py` (class Alpha158DL, MIT licence; read as a
reference, nothing copied or executed). 9 candlestick ratios, 4 price ratios
(window 0) and 29 rolling families x windows {5, 10, 20, 30, 60} = 158.

Known differences from Qlib's own output (not testable locally: pyqlib has no
Python 3.14 wheel):
  * prices are adjusted by our own preclose-chain factor (PLAN 3.11), volume
    is volume / F; Qlib uses the vendor factor of its data bundle;
  * full windows only (Qlib's rolling operators use min_periods = 1);
  * suspended-day rows stay in the windows (flat price, zero volume) -- Qlib
    data have NaN on such days; all B0 values are NaN when day t-1 itself was
    not traded;
  * VWAP is amount / volume of the day.
This is not a claim of exact Alpha158 replication.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import ops
from .config import B0_WINDOWS
from .registry import FeatureSpec, BAR_TIMING
from .timing import TradingCalendar, check_cutoff, truncate_bars, to_decision_index

EPS = 1e-12
_SRC = ("Qlib Alpha158DL expression (loader.py) read and re-implemented; numerical agreement with Qlib NOT tested. "
        "Declared deviations from Qlib, confirmed by PLAN v0.7 ruling F-16: full windows only; suspended-day rows "
        "stay in the windows (flat price, zero volume), nothing is filled; all B0 are NaN when t-1 did not trade "
        "(so CORD is NaN in windows containing the first traded day after a suspension; missing rates are reported)")

# name -> (formula text, fields, extra warm-up rows beyond the window)
_ROLLING = {
    "ROC": ("Ref(close, d) / close", "close", 1),
    "MA": ("Mean(close, d) / close", "close", 0),
    "STD": ("Std(close, d) / close  (ddof 1)", "close", 0),
    "BETA": ("Slope(close, d) / close  (OLS on 0..d-1)", "close", 0),
    "RSQR": ("Rsquare(close, d)", "close", 0),
    "RESI": ("Resi(close, d) / close  (residual of the last point)", "close", 0),
    "MAX": ("Max(high, d) / close", "high, close", 0),
    "MIN": ("Min(low, d) / close", "low, close", 0),
    "QTLU": ("Quantile(close, d, 0.8) / close", "close", 0),
    "QTLD": ("Quantile(close, d, 0.2) / close", "close", 0),
    "RANK": ("percentile rank of close in its last d values", "close", 0),
    "RSV": ("(close - Min(low, d)) / (Max(high, d) - Min(low, d) + 1e-12)", "high, low, close", 0),
    "IMAX": ("IdxMax(high, d) / d  (1-based, oldest = 1)", "high", 0),
    "IMIN": ("IdxMin(low, d) / d", "low", 0),
    "IMXD": ("(IdxMax(high, d) - IdxMin(low, d)) / d", "high, low", 0),
    "CORR": ("Corr(close, log(volume + 1), d)", "close, volume", 0),
    "CORD": ("Corr(close / Ref(close, 1), log(volume / Ref(volume, 1) + 1), d)", "close, volume", 1),
    "CNTP": ("Mean(close > Ref(close, 1), d)", "close", 1),
    "CNTN": ("Mean(close < Ref(close, 1), d)", "close", 1),
    "CNTD": ("CNTP - CNTN", "close", 1),
    "SUMP": ("Sum(max(dclose, 0), d) / (Sum(|dclose|, d) + 1e-12)", "close", 1),
    "SUMN": ("Sum(max(-dclose, 0), d) / (Sum(|dclose|, d) + 1e-12)", "close", 1),
    "SUMD": ("SUMP - SUMN (same denominator)", "close", 1),
    "VMA": ("Mean(volume, d) / (volume + 1e-12)", "volume", 0),
    "VSTD": ("Std(volume, d) / (volume + 1e-12)", "volume", 0),
    "WVMA": ("Std(|ret| * volume, d) / (Mean(|ret| * volume, d) + 1e-12)", "close, volume", 1),
    "VSUMP": ("Sum(max(dvolume, 0), d) / (Sum(|dvolume|, d) + 1e-12)", "volume", 1),
    "VSUMN": ("Sum(max(-dvolume, 0), d) / (Sum(|dvolume|, d) + 1e-12)", "volume", 1),
    "VSUMD": ("VSUMP - VSUMN (same denominator)", "volume", 1),
}
_KBAR = {
    "KMID": "(close - open) / open",
    "KLEN": "(high - low) / open",
    "KMID2": "(close - open) / (high - low + 1e-12)",
    "KUP": "(high - max(open, close)) / open",
    "KUP2": "(high - max(open, close)) / (high - low + 1e-12)",
    "KLOW": "(min(open, close) - low) / open",
    "KLOW2": "(min(open, close) - low) / (high - low + 1e-12)",
    "KSFT": "(2 close - high - low) / open",
    "KSFT2": "(2 close - high - low) / (high - low + 1e-12)",
}
_PRICE0 = {"OPEN0": "open / close", "HIGH0": "high / close", "LOW0": "low / close",
           "VWAP0": "(amount / volume) / close"}


def specs() -> list[FeatureSpec]:
    out = []
    for k, f in _KBAR.items():
        out.append(FeatureSpec("b0_" + k, "B0", "primary", f, "1", "open, high, low, close", 1, BAR_TIMING, _SRC))
    for k, f in _PRICE0.items():
        fields = "amount, volume, close" if k == "VWAP0" else "open/high/low, close"
        out.append(FeatureSpec("b0_" + k, "B0", "primary", f, "1", fields, 1, BAR_TIMING, _SRC))
    for k, (f, fields, extra) in _ROLLING.items():
        for d in B0_WINDOWS:
            out.append(FeatureSpec(f"b0_{k}{d}", "B0", "primary", f, str(d), fields + " (adjusted)", d + extra,
                                   BAR_TIMING, _SRC))
    return out


def b0_on_data_dates(b: pd.DataFrame) -> pd.DataFrame:
    """B0 as of each data date s (uses rows <= s of `b` only). `b` is a frame
    from `bars.prepare_bars`."""
    o, h, l, c = (b[k].values for k in ("aopen", "ahigh", "alow", "aclose"))
    v = b["avolume"].values
    vwap = b["avwap"].values
    cols: dict[str, np.ndarray] = {}
    with np.errstate(all="ignore"):
        hl = h - l + EPS
        cols["b0_KMID"] = (c - o) / o
        cols["b0_KLEN"] = (h - l) / o
        cols["b0_KMID2"] = (c - o) / hl
        cols["b0_KUP"] = (h - np.maximum(o, c)) / o
        cols["b0_KUP2"] = (h - np.maximum(o, c)) / hl
        cols["b0_KLOW"] = (np.minimum(o, c) - l) / o
        cols["b0_KLOW2"] = (np.minimum(o, c) - l) / hl
        cols["b0_KSFT"] = (2 * c - h - l) / o
        cols["b0_KSFT2"] = (2 * c - h - l) / hl
        cols["b0_OPEN0"] = o / c
        cols["b0_HIGH0"] = h / c
        cols["b0_LOW0"] = l / c
        cols["b0_VWAP0"] = vwap / c
        c1 = ops.ref(c, 1)
        v1 = ops.ref(v, 1)
        dc = c - c1
        dv = v - v1
        up = np.where(np.isnan(dc), np.nan, (dc > 0).astype(float))
        dn = np.where(np.isnan(dc), np.nan, (dc < 0).astype(float))
        logv = np.log(v + 1.0)
        cret = c / c1
        lvr = np.log(v / v1 + 1.0)
        absret_v = np.abs(c / c1 - 1.0) * v
        for d in B0_WINDOWS:
            cols[f"b0_ROC{d}"] = ops.ref(c, d) / c
            cols[f"b0_MA{d}"] = ops.r_mean(c, d) / c
            cols[f"b0_STD{d}"] = ops.r_std(c, d) / c
            cols[f"b0_BETA{d}"] = ops.r_slope(c, d) / c
            cols[f"b0_RSQR{d}"] = ops.r_rsquare(c, d)
            cols[f"b0_RESI{d}"] = ops.r_resi(c, d) / c
            mx, mn = ops.r_max(h, d), ops.r_min(l, d)
            cols[f"b0_MAX{d}"] = mx / c
            cols[f"b0_MIN{d}"] = mn / c
            cols[f"b0_QTLU{d}"] = ops.r_quantile(c, d, 0.8) / c
            cols[f"b0_QTLD{d}"] = ops.r_quantile(c, d, 0.2) / c
            cols[f"b0_RANK{d}"] = ops.r_rank(c, d)
            cols[f"b0_RSV{d}"] = (c - mn) / (mx - mn + EPS)
            imax, imin = ops.r_idxmax(h, d), ops.r_idxmin(l, d)
            cols[f"b0_IMAX{d}"] = imax / d
            cols[f"b0_IMIN{d}"] = imin / d
            cols[f"b0_IMXD{d}"] = (imax - imin) / d
            cols[f"b0_CORR{d}"] = ops.r_corr(c, logv, d)
            cols[f"b0_CORD{d}"] = ops.r_corr(cret, lvr, d)
            cp, cn = ops.r_mean(up, d), ops.r_mean(dn, d)
            cols[f"b0_CNTP{d}"] = cp
            cols[f"b0_CNTN{d}"] = cn
            cols[f"b0_CNTD{d}"] = cp - cn
            sp = ops.r_sum(np.maximum(dc, 0), d)
            sn = ops.r_sum(np.maximum(-dc, 0), d)
            sa = ops.r_sum(np.abs(dc), d) + EPS
            cols[f"b0_SUMP{d}"] = sp / sa
            cols[f"b0_SUMN{d}"] = sn / sa
            cols[f"b0_SUMD{d}"] = (sp - sn) / sa
            cols[f"b0_VMA{d}"] = ops.r_mean(v, d) / (v + EPS)
            cols[f"b0_VSTD{d}"] = ops.r_std(v, d) / (v + EPS)
            cols[f"b0_WVMA{d}"] = ops.r_std(absret_v, d) / (ops.r_mean(absret_v, d) + EPS)
            vp = ops.r_sum(np.maximum(dv, 0), d)
            vn = ops.r_sum(np.maximum(-dv, 0), d)
            va = ops.r_sum(np.abs(dv), d) + EPS
            cols[f"b0_VSUMP{d}"] = vp / va
            cols[f"b0_VSUMN{d}"] = vn / va
            cols[f"b0_VSUMD{d}"] = (vp - vn) / va
    out = pd.DataFrame(cols, index=b.index)
    # not traded on the data date itself -> no B0 value
    out.loc[~b["traded"].values] = np.nan
    out = out.replace([np.inf, -np.inf], np.nan)
    return out[[s.name for s in specs()]]


def b0_features(bars: pd.DataFrame, cal: TradingCalendar, cutoff) -> pd.DataFrame:
    """B0 for decision days <= `cutoff`. Uses bar rows dated < cutoff only."""
    t = check_cutoff(cal, cutoff)
    return to_decision_index(b0_on_data_dates(truncate_bars(bars, t)), cal)

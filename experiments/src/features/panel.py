"""Assemble all feature groups of one stock for decision days <= cut-off.

    build_stock_features(code, raw_bars, cal, cutoff, ...)

`cutoff` is a decision day t. Row t of the result is a function of G_t only:
bar rows dated < t, index rows dated < t, the calendar, and event records
whose availability day is <= t (timing.py, zo.py).

The full-market loop, storage and the missing-rate / warm-up report are in
`market_panel.py`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from . import base_b0, zh, controls, zo, rules
from .bars import prepare_bars, prepare_index
from .config import LHB_PROXY_INDEX, ZO_ADV_WINDOW, DIAG_XSRC_WINDOW
from .timing import TradingCalendar, check_cutoff, truncate_bars, to_decision_index

GROUPS = ("B0", "Z_H", "R_H-sum", "R_H-hist", "Z_O", "R_O", "DIAG")


def float_market_value(b: pd.DataFrame) -> pd.Series:
    """Unadjusted close x float shares as of each data date; float shares =
    volume / V on the last traded day <= s (carried forward causally)."""
    with np.errstate(all="ignore"):
        fs = np.where(b["traded"].values & (b["V"].values > 0), b["volume"].values / b["V"].values, np.nan)
    fs = pd.Series(fs, index=b.index).ffill()
    return fs * b["close"]


def adv_on_data_dates(b: pd.DataFrame, n: int = ZO_ADV_WINDOW) -> pd.Series:
    """ADV as of each data date s (PLAN U40; rulings E-5 / F-7 -- the same
    definition as `engine.fills.adv`, the capacity cap): the mean unadjusted
    traded amount (yuan) over the `n` most recent TRADED rows dated <= s.
    Rows without a trade are skipped, not counted as zero; with fewer than
    `n` traded rows in the history the mean is over those that exist. As in
    the engine, a traded row is one with tradestatus 1 and volume > 0, and a
    missing amount on such a row counts as 0. Where the engine returns 0 (no
    traded row yet) this returns NaN, and a non-positive mean is NaN: the LHB
    intensity is then NaN when its window has an event.
    Each window is summed on its own (no running sums), so the value at s
    depends on rows <= s only and not on the length of the history."""
    use = b["traded"].values.astype(bool)
    a = np.nan_to_num(b["amount"].values.astype(np.float64)[use])
    k = len(a)
    m = np.full(k, np.nan)
    if k:
        for j in range(min(k, n - 1)):              # fewer than n traded rows so far
            m[j] = a[:j + 1].sum() / (j + 1)
        if k >= n:
            m[n - 1:] = sliding_window_view(a, n).sum(axis=1) / n
    cnt = np.cumsum(use)                            # traded rows dated <= s
    out = np.full(len(b), np.nan)
    has = cnt > 0
    if k:
        out[has] = m[cnt[has] - 1]
    return pd.Series(np.where(out > 0, out, np.nan), index=b.index)


def filled_xsrc_in_window(b: pd.DataFrame, w: int = DIAG_XSRC_WINDOW) -> pd.Series:
    """Diagnostic (not a model feature): 1.0 if a row inserted from the
    cross-check source lies in the last `w` rows ending s, else 0.0."""
    f = b["filled_xsrc"].values.astype(bool) if "filled_xsrc" in b.columns else np.zeros(len(b), dtype=bool)
    pos = np.arange(len(b))
    last = np.maximum.accumulate(np.where(f, pos, -1))
    return pd.Series(((last >= 0) & (pos - last < w)).astype(float), index=b.index)


def build_stock_features(code: str, raw_bars: pd.DataFrame, cal: TradingCalendar, cutoff,
                         raw_index: pd.DataFrame | None = None, zo_tables: zo.ZOTables | None = None,
                         ipo_date=None, groups=GROUPS, zh_kwargs: dict | None = None,
                         zo_lags: dict | None = None, zo_strict: bool | None = None) -> pd.DataFrame:
    """Feature frame indexed by decision day (<= cutoff). `raw_bars` is the
    vendor's daily table of the name (strings; it may contain rows repaired
    by the fetch pipeline, flagged `filled_from_xsrc`); `raw_index` the daily
    table of its proxy index; `zo_tables` the whitelisted event tables of all
    names. `zo_strict` -> zo.coverage_array (None = config default: strict).
    `zh_kwargs` is for the pre-declared sensitivities only (chip_init,
    v_mode); the defaults are the primary definitions of PLAN v0.7."""
    t = check_cutoff(cal, cutoff)
    bars = prepare_bars(raw_bars, cal)
    b = truncate_bars(bars, t)
    if len(b) == 0:
        return pd.DataFrame()
    parts = []
    if "B0" in groups:
        parts.append(base_b0.b0_on_data_dates(b))
    if "Z_H" in groups:
        parts.append(zh.zh_on_data_dates(b, cal, **(zh_kwargs or {})))
    if "R_H-sum" in groups:
        parts.append(controls.rh_sum_on_data_dates(b))
    if "R_H-hist" in groups:
        parts.append(controls.rh_hist_on_data_dates(b))
    if "R_O" in groups:
        ir = None
        if raw_index is not None:
            ir = prepare_index(raw_index)
            ir = ir.loc[ir.index < t]
        parts.append(controls.ro_on_data_dates(b, code, ir, ipo_date, cal))
    if "DIAG" in groups:
        parts.append(filled_xsrc_in_window(b).to_frame("diag_filled_xsrc_in_window"))
    out = to_decision_index(pd.concat(parts, axis=1) if parts else pd.DataFrame(index=b.index), cal)
    if "R_O" in groups:
        out = pd.concat([out, controls.ro_regime_columns(out.index, code)], axis=1)
    if "Z_O" in groups:
        if zo_tables is None:
            raise ValueError("Z_O requested without event tables")
        adv = to_decision_index(adv_on_data_dates(b).to_frame("adv"), cal)["adv"]
        z = zo.zo_features(code, out.index, cal, t, zo_tables, adv, float_market_value(b), zo_lags, zo_strict,
                           bars=b)
        zattrs = dict(z.attrs)
        if "R_O" not in groups:
            z = z[zo.ZO_NAMES]
        out = pd.concat([out, z], axis=1)
        out.attrs = dict(bars.attrs)
        out.attrs["zo_lhb_stats"] = zattrs.get("lhb_stats", {})
        out.attrs["zo_ins_stats"] = zattrs.get("ins_stats", {})
        out.attrs["zo_blk_stats"] = zattrs.get("blk_stats", {})
    else:
        out.attrs = dict(bars.attrs)
    return out


def proxy_index_code(code: str) -> str:
    return LHB_PROXY_INDEX[rules.board_of(code)]


def column_order() -> list[str]:
    from .registry import catalogue
    return catalogue()["name"].tolist()

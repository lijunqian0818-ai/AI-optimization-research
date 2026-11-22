"""Control set R = R_H-sum, R_H-hist, R_O (PLAN 5.4) from daily bars.

"Without Z" never means "without the raw material of Z": these columns are
in every feature set. The window lists of R_H-sum (config.py) were chosen by
the implementer before any modelling and are confirmed and frozen by PLAN
v0.7 ruling F-15. R_H-hist keeps four quantities per bin (F-15: cumulative
turnover dropped, collinear with the mean). Bands, thresholds and regime
dates come from the rule calendar through rules.py (F-20).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from . import ops, rules
from .config import (RH_RET_WINDOWS, RH_MA_WINDOWS, RH_RANGE_WINDOWS, RH_TURN_WINDOWS, RH_UNDECAYED_WINDOWS,
                     RH_HIST_WINDOWS, RH_HIST_BINS, RH_HIST_STATS, RH_TURN_STD_WINDOWS, RH_TURN_CUM_WINDOWS,
                     RH_HL_WINDOWS, ZO_LOOKBACKS, INS_REGIME_NAMES)
from .registry import FeatureSpec, BAR_TIMING
from .timing import TradingCalendar, check_cutoff, truncate_bars, to_decision_index

_PLAN = "PLAN 5.4 (own definition; no literature source claimed); window list confirmed by PLAN v0.7 ruling F-15"
RO_AMOUNT_BASE = 60


# ============================================================ R_H-sum
def rh_sum_specs() -> list[FeatureSpec]:
    S = FeatureSpec
    out = []
    for w in RH_RET_WINDOWS:
        out.append(S(f"rh_ret_{w}", "R_H-sum", "control", "P_{t-1} / P_{t-1-w} - 1", str(w), "close (adj)", w + 1,
                     BAR_TIMING, _PLAN))
    for w in RH_MA_WINDOWS:
        out.append(S(f"rh_ma_gap_{w}", "R_H-sum", "control", "P_{t-1} / mean(P, w) - 1", str(w), "close (adj)", w,
                     BAR_TIMING, _PLAN))
    for w in RH_UNDECAYED_WINDOWS:
        out.append(S(f"rh_uwap_gap_{w}", "R_H-sum", "control",
                     "P_{t-1} / (sum V P / sum V over w) - 1  (undecayed turnover-weighted average price)", str(w),
                     "close (adj), turn", w, BAR_TIMING, _PLAN))
    for w in RH_RANGE_WINDOWS:
        out.append(S(f"rh_pos_{w}", "R_H-sum", "control", "(P_{t-1} - min low) / (max high - min low) over w", str(w),
                     "high, low, close (adj)", w, BAR_TIMING, _PLAN))
    out.append(S("rh_turn_1", "R_H-sum", "control", "V_{t-1}", "1", "turn", 1, BAR_TIMING, _PLAN))
    for w in RH_TURN_WINDOWS:
        out.append(S(f"rh_turn_mean_{w}", "R_H-sum", "control", "mean(V, w)", str(w), "turn", w, BAR_TIMING, _PLAN))
    for w in RH_TURN_STD_WINDOWS:
        out.append(S(f"rh_turn_std_{w}", "R_H-sum", "control", "std(V, w), ddof 1", str(w), "turn", w, BAR_TIMING,
                     _PLAN))
    for w in RH_TURN_CUM_WINDOWS:
        out.append(S(f"rh_turn_cum_{w}", "R_H-sum", "control", "sum(V, w)", str(w), "turn", w, BAR_TIMING, _PLAN))
    out.append(S("rh_hl_1", "R_H-sum", "control", "(high - low) / close on t-1", "1", "high, low, close", 1,
                 BAR_TIMING, _PLAN))
    for w in RH_HL_WINDOWS:
        out.append(S(f"rh_hl_mean_{w}", "R_H-sum", "control", "mean((high - low) / close, w)", str(w),
                     "high, low, close", w, BAR_TIMING, _PLAN))
    return out


def rh_sum_on_data_dates(b: pd.DataFrame) -> pd.DataFrame:
    c, h, l, v = b["aclose"].values, b["ahigh"].values, b["alow"].values, b["V"].values
    cols = {}
    with np.errstate(all="ignore"):
        for w in RH_RET_WINDOWS:
            cols[f"rh_ret_{w}"] = c / ops.ref(c, w) - 1.0
        for w in RH_MA_WINDOWS:
            cols[f"rh_ma_gap_{w}"] = c / ops.r_mean(c, w) - 1.0
        for w in RH_UNDECAYED_WINDOWS:
            cols[f"rh_uwap_gap_{w}"] = c / (ops.r_sum(v * c, w) / ops.r_sum(v, w)) - 1.0
        for w in RH_RANGE_WINDOWS:
            mx, mn = ops.r_max(h, w), ops.r_min(l, w)
            cols[f"rh_pos_{w}"] = (c - mn) / (mx - mn)
        cols["rh_turn_1"] = v.copy()
        for w in RH_TURN_WINDOWS:
            cols[f"rh_turn_mean_{w}"] = ops.r_mean(v, w)
        for w in RH_TURN_STD_WINDOWS:
            cols[f"rh_turn_std_{w}"] = ops.r_std(v, w)
        for w in RH_TURN_CUM_WINDOWS:
            cols[f"rh_turn_cum_{w}"] = ops.r_sum(v, w)
        hl = (h - l) / c
        cols["rh_hl_1"] = hl
        for w in RH_HL_WINDOWS:
            cols[f"rh_hl_mean_{w}"] = ops.r_mean(hl, w)
    out = pd.DataFrame(cols, index=b.index).replace([np.inf, -np.inf], np.nan)
    return out[[s.name for s in rh_sum_specs()]]


# ============================================================ R_H-hist
_HIST_FORMULA = {
    "ret": "cumulative return over the bin: P_end / P_(day before the bin) - 1",
    "turn_mean": "mean V in the bin",
    "vwp": "(sum V P / sum V in the bin) / P_{t-1} - 1",
    "hl": "mean (high - low) / close in the bin",
}
_HIST_STATS = {k: _HIST_FORMULA[k] for k in RH_HIST_STATS}     # F-15: no cumulative-turnover bins


def rh_hist_specs() -> list[FeatureSpec]:
    out = []
    for w in RH_HIST_WINDOWS:
        for k, f in _HIST_STATS.items():
            for j in range(1, RH_HIST_BINS + 1):
                out.append(FeatureSpec(
                    f"rhh{w}_{k}_{j:02d}", "R_H-hist", "control",
                    f"window of {w} days ending t-1 cut into {RH_HIST_BINS} consecutive bins of {w // RH_HIST_BINS} "
                    f"days (bin 01 = oldest); {f}", str(w), "high, low, close (adj), turn",
                    w + (1 if k == "ret" else 0), BAR_TIMING,
                    _PLAN + "; matched-window history control (P8); 4 quantities per bin (F-15)"))
    return out


def rh_hist_on_data_dates(b: pd.DataFrame) -> pd.DataFrame:
    c, h, l, v = b["aclose"].values, b["ahigh"].values, b["alow"].values, b["V"].values
    n = len(b)
    cols = {}
    with np.errstate(all="ignore"):
        hl = (h - l) / c
        vc = v * c
        for w in RH_HIST_WINDOWS:
            nb = RH_HIST_BINS
            if w % nb:
                raise ValueError("window must be a multiple of the number of bins")
            m = w // nb
            blank = np.full((n, nb), np.nan)
            res = {k: blank.copy() for k in _HIST_STATS}
            if n >= w:
                def binned(x):
                    return sliding_window_view(x, w).reshape(-1, nb, m)
                bv, bvc, bhl, bc = binned(v), binned(vc), binned(hl), binned(c)
                ok = (np.isfinite(sliding_window_view(v, w)).all(axis=1)
                      & np.isfinite(sliding_window_view(c, w)).all(axis=1)
                      & np.isfinite(sliding_window_view(hl, w)).all(axis=1))[:, None]
                last = c[w - 1:][:, None]
                sv = bv.sum(axis=2)
                res["turn_mean"][w - 1:] = np.where(ok, bv.mean(axis=2), np.nan)
                res["vwp"][w - 1:] = np.where(ok, (bvc.sum(axis=2) / sv) / last - 1.0, np.nan)
                res["hl"][w - 1:] = np.where(ok, bhl.mean(axis=2), np.nan)
                # returns need the close of the day before each bin: w + 1 rows
                if n >= w + 1:
                    end = bc[1:, :, -1]                                    # windows ending at rows w .. n-1
                    start = sliding_window_view(c, w + 1)[:, 0:w:m]        # close before each bin
                    okr = ok[1:] & np.isfinite(start[:, :1])
                    res["ret"][w:] = np.where(okr, end / start - 1.0, np.nan)
            for k in _HIST_STATS:
                for j in range(nb):
                    cols[f"rhh{w}_{k}_{j + 1:02d}"] = res[k][:, j]
    out = pd.DataFrame(cols, index=b.index).replace([np.inf, -np.inf], np.nan)
    return out[[s.name for s in rh_hist_specs()]]


# ============================================================ R_O (bar part)
def ro_specs() -> list[FeatureSpec]:
    S = FeatureSpec
    rule = ("PLAN 5.4; thresholds read from the rule calendar (RC-18: conditions verified for the rule versions "
            "opened; dates of regime changes unverified; ST-specific thresholds not implemented); PROXY only: the "
            "top-N ranking across the exchange is not reproduced, the index is a board proxy (list item 20), the "
            "turnover denominator is the bar source's. Amplitude here is the rule's (high - low) / low, on purpose "
            "different from the control ro_amp_* (PLAN v0.7 ruling F-12)")
    out = []
    for w in ZO_LOOKBACKS:
        out.append(S(f"ro_xret_{w}", "R_O", "control", "stock return over w days minus proxy-index return over w days",
                     str(w), "close (adj), index close/preclose", w + 1, BAR_TIMING, _PLAN + "; proxy index by board"))
    amp_src = ("PLAN 5.4: the control uses (high - low) / preclose as written in the plan; the trigger proxy "
               "ro_trig_amp_* uses the rule's (high - low) / low (PLAN v0.7 ruling F-12)")
    out.append(S("ro_amp_1", "R_O", "control", "(high - low) / preclose on t-1", "1", "high, low, preclose", 1,
                 BAR_TIMING, amp_src))
    for w in ZO_LOOKBACKS[1:]:
        out.append(S(f"ro_amp_max_{w}", "R_O", "control", "max over w of (high - low) / preclose", str(w),
                     "high, low, preclose", w, BAR_TIMING, amp_src))
        out.append(S(f"ro_turn_max_{w}", "R_O", "control", "max over w of V", str(w), "turn", w, BAR_TIMING, _PLAN))
    for side in ("up", "dn"):
        for w in ZO_LOOKBACKS:
            out.append(S(f"ro_limit_{side}_cnt_{w}", "R_O", "control",
                         f"number of days in w with close = limit-{side} price (preclose*(1+-band), half-up to 0.01); "
                         "NaN while the window contains any of the name's first 5 trading days",
                         str(w), "close, preclose, isST, listing day", w + 5, BAR_TIMING,
                         "RC-5 / RC-6 bands from the rule calendar; first-5-days rule = PLAN v0.7 ruling F-20 (no "
                         "registration-reform date used); no-limit days of seasoned stocks (RC-6 g) not identified"))
    for trig, f in (("devup", "deviation >= +7% (or raw change >= +15% in the 15/30/30 regime)"),
                    ("devdn", "deviation <= -7% (or raw change <= -15%)"),
                    ("amp", "(high - low) / low >= 15% (30%)"),
                    ("turn", "V >= 20% (30%)"),
                    ("cum3", "|3-day cumulative deviation| >= 20% (30%) [threshold: rule calendar RC-18 cum3 "
                             "(unverified, item 22)]")):
        for w in ZO_LOOKBACKS:
            out.append(S(f"ro_trig_{trig}_cnt_{w}", "R_O", "control", f"number of days in w with {f}", str(w),
                         "close, preclose, high, low, turn, index", w + (2 if trig == "cum3" else 0), BAR_TIMING,
                         "rule calendar RC-18 cum3 (unverified, item 22)" if trig == "cum3" else rule))
    for w in ZO_LOOKBACKS:
        out.append(S(f"ro_amt_max_to_mean60_{w}", "R_O", "control", "max(amount over w) / mean(amount over 60)",
                     "60", "amount", 60, BAR_TIMING, _PLAN))
    out.append(S("ro_lhb_thr15", "R_O", "control", "1 if the 15/30/30 Dragon-Tiger criteria apply on day t-1", "0",
                 "code, date", 0, "calendar and board only",
                 "RC-18 via the rule calendar; ChiNext implementing document not opened (list item 7)"))
    out.append(S("ro_exch_sse", "R_O", "control", "1 for an SSE name, 0 for an SZSE name (with ro_lhb_top5 it spans exchange x {top-3, top-5})",
                 "0", "code", 0, "code prefix only", "PLAN 5.6.2a (i)"))
    out.append(S("ro_lhb_top5", "R_O", "control",
                 "1 if five names per criterion are listed, 0 if three, NaN = unknown. SSE: 0 before 2021-09-17, "
                 "NaN 2021-09-17..2021-10-07, 1 from 2021-10-08; SZSE: NaN before 2013-12-01, 1 from then",
                 "0", "code, date", 0, "calendar and exchange only",
                 "RC-18 via the rule calendar; PLAN v0.7 ruling F-13: dates unverified (list items 7, 19), the "
                 "indicator does not assert them over the uncertain intervals"))
    for k, nm in enumerate(INS_REGIME_NAMES):
        out.append(S(f"ro_ins_regime_{k}", "R_O", "control", f"1 if decision day t is in regime '{nm}'", "0", "date", 0,
                     "calendar only", "RC-20 via the rule calendar (CSRC documents verified in rule_verification.md C3)"))
    for cls in ("lhb", "blk", "ins"):
        out.append(S(f"ro_{cls}_data", "R_O", "control",
                     f"1 if the {cls} table covers the newest usable event day t - lag: analysis start of the class "
                     "(max(OA3 start, 2008-01-01)) <= t - lag",
                     "0", "table coverage", 0, "coverage of the raw pull",
                     "PLAN 5.6.3; PLAN v0.7 ruling F-14 (coverage; a missing file inside the analysis period is an "
                     "error in production, strict=True)"))
    return out


RO_BAR_NAMES = [s.name for s in ro_specs() if not s.name.endswith("_data")]


def ro_on_data_dates(b: pd.DataFrame, code: str, index_ret: pd.Series | None, ipo_date=None,
                     cal: TradingCalendar | None = None) -> pd.DataFrame:
    """Bar part of R_O as of each data date s. `index_ret` = daily return of
    the proxy index (it is truncated to the dates of `b`). `ipo_date` / `cal`
    locate the name's first 5 trading days (rules.first_trading_rows): the
    limit counts are NaN while their window contains one of them (F-20)."""
    exch, board = rules.board_of(code)
    dates = b.index
    c, h, l, pc, v, amt = (b[k].values for k in ("close", "high", "low", "preclose", "V", "amount"))
    ac = b["aclose"].values
    traded = b["traded"].values
    present = b["present"].values
    if index_ret is None:
        ir = np.full(len(b), np.nan)
    else:
        ir = index_ret.reindex(dates).values.astype(np.float64)
    cols = {}
    with np.errstate(all="ignore"):
        for w in ZO_LOOKBACKS:
            stock = ac / ops.ref(ac, w) - 1.0
            idx = np.exp(ops.r_sum(np.log1p(ir), w)) - 1.0
            cols[f"ro_xret_{w}"] = stock - idx
        amp = (h - l) / pc
        cols["ro_amp_1"] = amp
        for w in ZO_LOOKBACKS[1:]:
            cols[f"ro_amp_max_{w}"] = ops.r_max(amp, w)
            cols[f"ro_turn_max_{w}"] = ops.r_max(v, w)
        band = rules.limit_band(board, b["is_st"].values, dates)
        up, dn = rules.limit_prices(pc, band)
        first5 = rules.first_trading_rows(dates, ipo_date, cal)
        nanrow = ~present
        nan_lim = nanrow | first5 | ~np.isfinite(band)
        f_up = np.where(nan_lim, np.nan, (traded & (np.abs(c - up) < 0.005)).astype(float))
        f_dn = np.where(nan_lim, np.nan, (traded & (np.abs(c - dn) < 0.005)).astype(float))
        thr = rules.lhb_thresholds(board, dates)
        thr15 = thr["raw"] > 0
        pct = c / pc - 1.0
        dev = np.where(thr15, pct, pct - ir)                 # 15/30/30 regime uses the raw change
        t_dev, t_amp, t_turn = thr["dev"], thr["amp"], thr["turn"]
        t_cum = thr["cum3"]                                  # RC-18 element cum3 (PLAN v0.8 J-1)
        amp_rule = (h - l) / l
        cum3 = ops.r_sum(pct - ir, 3)

        def flag(cond, basis):
            return np.where(nanrow | ~np.isfinite(basis), np.nan, (traded & cond).astype(float))
        trig = {"devup": flag(dev >= t_dev, dev), "devdn": flag(dev <= -t_dev, dev),
                "amp": flag(amp_rule >= t_amp, amp_rule), "turn": flag(v >= t_turn, v),
                "cum3": flag(np.abs(cum3) >= t_cum, cum3)}
        for w in ZO_LOOKBACKS:
            cols[f"ro_limit_up_cnt_{w}"] = ops.r_count(f_up, w)
            cols[f"ro_limit_dn_cnt_{w}"] = ops.r_count(f_dn, w)
            for k, f in trig.items():
                cols[f"ro_trig_{k}_cnt_{w}"] = ops.r_count(f, w)
            cols[f"ro_amt_max_to_mean60_{w}"] = ops.r_max(amt, w) / ops.r_mean(amt, RO_AMOUNT_BASE)
        cols["ro_lhb_thr15"] = thr["raw"]
    out = pd.DataFrame(cols, index=dates).replace([np.inf, -np.inf], np.nan)
    return out


def ro_regime_columns(decision_days: pd.DatetimeIndex, code: str) -> pd.DataFrame:
    """Regime indicators that depend on the calendar date of the decision day
    and on the exchange only (read from the rule calendar; NaN on a decision
    day outside its window 2008-01-01 .. 2026-06-30)."""
    exch, _ = rules.board_of(code)
    cols = {"ro_exch_sse": np.full(len(decision_days), 1.0 if exch == "sse" else 0.0),
            "ro_lhb_top5": rules.lhb_top5_regime(exch, decision_days)}
    reg = rules.ins_regime(decision_days)
    for k in range(len(INS_REGIME_NAMES)):
        cols[f"ro_ins_regime_{k}"] = np.where(np.isnan(reg), np.nan, (reg == k).astype(float))
    return pd.DataFrame(cols, index=decision_days)


def ro_bar_features(bars: pd.DataFrame, cal: TradingCalendar, cutoff, code: str, index_ret=None,
                    ipo_date=None) -> pd.DataFrame:
    """Bar and regime part of R_O for decision days <= cutoff."""
    t = check_cutoff(cal, cutoff)
    b = truncate_bars(bars, t)
    ir = None if index_ret is None else index_ret.loc[index_ret.index < t]
    out = to_decision_index(ro_on_data_dates(b, code, ir, ipo_date, cal), cal)
    reg = ro_regime_columns(out.index, code)
    out = pd.concat([out, reg], axis=1)
    return out[RO_BAR_NAMES]


def rh_sum_features(bars, cal, cutoff):
    t = check_cutoff(cal, cutoff)
    return to_decision_index(rh_sum_on_data_dates(truncate_bars(bars, t)), cal)


def rh_hist_features(bars, cal, cutoff):
    t = check_cutoff(cal, cutoff)
    return to_decision_index(rh_hist_on_data_dates(truncate_bars(bars, t)), cal)

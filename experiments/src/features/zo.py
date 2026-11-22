"""Z_O -- stock-day aggregates of public disclosure events (PLAN v0.7 5.6).

Classes: LHB (Dragon-Tiger list), BLK (block trades), INS (executed share
changes of large shareholders and insiders, dated by ANNOUNCEMENT date).

Timing (PLAN 5.6.2; rulings F-8, F-9). An event of trading day s -- for INS:
announced on calendar day a, s = the first trading day >= a (an announcement
dated on a non-trading day is rolled FORWARD, then the lag is counted) -- is
usable for decision days t >= s + lag, lag in trading days (config.ZO_LAG; 2
for every class). The event day, never the transaction day, dates an INS
record; START_DATE / END_DATE are not used for timing (END_DATE only in the
cleaning rule), and EITIME (the vendor's entry time) never enters a feature:
a back-filled row is used exactly like any other row, from its announcement
day + lag on. Whether the vendor's announcement dates are right cannot be
checked from free data (audit OA10).

Encoding (PLAN 5.6.3), per class and look-back W in {1, 5, 20}. Windows are
ordered by availability (ruling F-4):

    window(t, W) = event days s with  t - lag - W + 1 <= s <= t - lag.

  * indicator   1{an event in window(t, W)}
  * days since  (ruling F-5, U60) t - s* for the latest usable event day s*
                with t - 250 <= s* <= t - lag, capped at 60; 0 when there is
                none (the true minimum is lag >= 1, so 0 is unambiguous)
  * has_prior   1{a usable event day s with t - 250 <= s <= t - lag}
                Both are NaN until the class has 250 + lag trading days of
                coverage before t; neither depends on where the raw pull
                starts.
  * intensity   exactly 0 when the indicator is 0; see each class.
No value is imputed. Where the class table does not cover the window the
features are NaN and `ro_<class>_data` is 0.

Coverage (ruling F-14): the class covers trading day d if its analysis start
(config.ZO_CLASS_START = max(OA3 start, 2008-01-01)) <= d <= the end of the
raw pull and the raw file of d's period is in the snapshot. With strict=True
(production default) a missing file inside that period raises
`MissingRawFile`; strict=False (tests while a pull is running) gives NaN.

Several LHB rows per stock-day (ruling F-6): see `lhb_stock_day`.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from . import config
from .config import ZO_LOOKBACKS, ZO_DAYS_SINCE_CAP, ZO_LAG, ZO_CLASS_START, ZO_PRIOR_LOOKBACK, ZO_RAW_END
from .registry import FeatureSpec
from .timing import TradingCalendar, check_cutoff

REASON_MAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lhb_reason_map.csv")
REASON_CLASSES = ("single", "multi", "unclassified")
_REASON_MAP: dict | None = None


class MissingRawFile(RuntimeError):
    """A raw Z_O file of the analysis period is not in the snapshot (strict coverage, ruling F-14)."""


def load_reason_map(path: str = REASON_MAP_FILE) -> dict:
    """Frozen table listing-reason string -> 'single' | 'multi' |
    'unclassified' (ruling F-6). Built from the strings alone by
    `build_lhb_reason_map.py`; hashed with the first snapshot."""
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["class"] not in REASON_CLASSES:
                raise ValueError("bad class in the reason map: " + row["class"])
            out[row["reason"]] = row["class"]
    return out


def reason_class(reason) -> str:
    """Class of a listing-reason string by the frozen table; a string that is
    not in the table is 'unclassified' (counted, indicator only)."""
    global _REASON_MAP
    if _REASON_MAP is None:
        _REASON_MAP = load_reason_map()
    return _REASON_MAP.get(reason if isinstance(reason, str) else "", "unclassified")


def is_multi_day_reason(reason: str) -> bool:
    """True if the frozen table classifies the reason as a multi-day
    criterion (its seat amounts are cumulated over the days of the
    criterion)."""
    return reason_class(reason) == "multi"


def to_bs_code(code6: str):
    """6-digit code -> BaoStock code; None for B-shares, Beijing Stock
    Exchange codes, bonds and anything else outside the universe."""
    c = str(code6)
    if len(c) != 6 or not c.isdigit():
        return None
    if c.startswith(("600", "601", "603", "605", "688", "689")):
        return "sh." + c
    if c.startswith(("000", "001", "002", "003", "300", "301", "302")):
        return "sz." + c
    return None


@dataclass
class ZOTables:
    """Whitelisted columns of the vendor tables (all names), plus coverage:
    the set of periods for which a raw file is in the snapshot -- 'YYYYMM'
    for lhb / jg / blk, 'YYYY' (announcement year) for ins."""
    lhb: pd.DataFrame
    jg: pd.DataFrame
    blk: pd.DataFrame
    ins: pd.DataFrame
    coverage: dict = field(default_factory=dict)
    # data cut-off of the snapshot the tables were read from (PLAN v0.8 C-8; set by
    # store.RawStore). None only for tables built in memory by tests: then the analysis
    # period ends at the end of the raw window ZO_RAW_END.
    data_cutoff: object = None

    def analysis_end(self) -> pd.Timestamp:
        if self.data_cutoff is None:
            return ZO_RAW_END
        return min(ZO_RAW_END, pd.Timestamp(self.data_cutoff))

    def restrict(self, codes) -> "ZOTables":
        """The tables filtered to a list of names (BaoStock codes); coverage and cut-off unchanged.
        Features of a name read only that name's rows, so the result is the same for those names."""
        c6 = {str(c).split(".")[-1] for c in codes}
        return ZOTables(self.lhb[self.lhb["代码"].isin(c6)].reset_index(drop=True),
                        self.jg[self.jg["代码"].isin(c6)].reset_index(drop=True),
                        self.blk[self.blk["证券代码"].isin(c6)].reset_index(drop=True),
                        self.ins[self.ins["SECURITY_CODE"].isin(c6)].reset_index(drop=True),
                        self.coverage, self.data_cutoff)

    def for_code(self, code: str) -> "ZOTables":
        c6 = code.split(".")[1]
        return ZOTables(self.lhb[self.lhb["代码"] == c6], self.jg[self.jg["代码"] == c6],
                        self.blk[self.blk["证券代码"] == c6], self.ins[self.ins["SECURITY_CODE"] == c6],
                        self.coverage, self.data_cutoff)


# ----------------------------------------------------------------------------
# generic helpers on calendar positions
# ----------------------------------------------------------------------------
def coverage_array(cal: TradingCalendar, cls: str, periods, start=None, strict: bool | None = None,
                   end=None) -> np.ndarray:
    """cov[pos] = True if the class table covers trading day `pos`: the day
    lies in the analysis period [start, end] of the class and the raw file of
    its period is in `periods`.

    INS files are per announcement year; an announcement dated on a
    non-trading day rolls forward, so trading day d also needs the file(s) of
    the calendar days since the previous trading day.

    strict (default config.ZO_STRICT_COVERAGE = True, production): a file of
    the analysis period that is not in `periods` raises MissingRawFile.
    strict=False: the days concerned are simply not covered (NaN features).
    """
    strict = config.ZO_STRICT_COVERAGE if strict is None else strict
    start = ZO_CLASS_START[cls] if start is None else pd.Timestamp(start)
    end = ZO_RAW_END if end is None else pd.Timestamp(end)
    d = cal.days
    periods = set(periods)
    in_period = (d.values >= np.datetime64(start)) & (d.values <= np.datetime64(end))
    if cls == "ins":
        key = np.asarray(d.strftime("%Y"))
        first_new = d[:-1] + pd.Timedelta(days=1)                    # first calendar day after the previous trading day
        prev_key = np.r_[key[:1], np.asarray(first_new.strftime("%Y"))] if len(d) else key
        need = set(key[in_period]) | set(prev_key[in_period])
        ok = np.isin(key, list(periods)) & np.isin(prev_key, list(periods))
    else:
        key = np.asarray(d.strftime("%Y%m"))
        need = set(key[in_period])
        ok = np.isin(key, list(periods))
    if strict:
        missing = sorted(need - periods)
        if missing:
            raise MissingRawFile(f"class {cls}: raw files missing from the snapshot inside the analysis period "
                                 f"{start.date()}..{end.date()}: {missing[:12]}{' ...' if len(missing) > 12 else ''} "
                                 f"({len(missing)} periods)")
    return ok & in_period


def _win_sum(arr: np.ndarray, end: np.ndarray, w: int) -> np.ndarray:
    """Sum of arr over positions [end - w + 1, end]; NaN if the window leaves
    the array. Evaluated window by window (an all-zero window gives exactly 0)."""
    out = np.full(len(end), np.nan)
    if len(arr) < w:
        return out
    s = sliding_window_view(arr, w).sum(axis=1)          # s[k] = sum arr[k .. k+w-1]
    k = end - w + 1
    ok = (k >= 0) & (end < len(arr))
    out[ok] = s[k[ok]]
    return out


def _encode_timing(cnt: np.ndarray, cov: np.ndarray, dec_pos: np.ndarray, lag: int,
                   lookback: int = ZO_PRIOR_LOOKBACK):
    """Indicators, days-since / has_prior and coverage flags shared by all
    classes. cnt[pos] = number of event records on trading day pos (already
    truncated at the cut-off).

    days_since / has_prior (ruling F-5): the latest event day s* <= t - lag;
    it counts if t - s* <= lookback (250). Both are NaN unless the class
    covers the lookback + 1 event days t - lookback - lag .. t - lag, i.e.
    unless it has lookback + lag trading days of coverage before t."""
    end = dec_pos - lag
    L = len(cnt)
    covf = cov.astype(np.float64)
    res = {}
    valid = {}
    for w in ZO_LOOKBACKS:
        n_ev = _win_sum(cnt.astype(np.float64), end, w)
        n_cov = _win_sum(covf, end, w)
        ok = n_cov == w
        valid[w] = ok
        res[f"ind_{w}"] = np.where(ok, (n_ev > 0).astype(float), np.nan)
    last = np.maximum.accumulate(np.where(cnt > 0, np.arange(L), -1))
    inb = (end >= 0) & (end < L)
    last_e = np.where(inb, last[np.clip(end, 0, L - 1)], -1)
    recent = (last_e >= 0) & (dec_pos - last_e <= lookback)
    cap = ZO_DAYS_SINCE_CAP
    span = lookback + 1
    ok_ds = _win_sum(covf, end, span) == span
    d = np.where(recent, np.minimum(dec_pos - last_e, cap), 0).astype(float)
    res["days_since"] = np.where(ok_ds, d, np.nan)
    res["has_prior"] = np.where(ok_ds, recent.astype(float), np.nan)
    data = np.where(inb, cov[np.clip(end, 0, L - 1)], False).astype(float)
    return res, valid, data


def _daily(pos: np.ndarray, values: np.ndarray, L: int) -> np.ndarray:
    """Sum of `values` per calendar position (0 where there is no record;
    NaN values propagate)."""
    out = np.zeros(L)
    np.add.at(out, pos, values)
    return out


def _truncate_events(pos: np.ndarray, cal: TradingCalendar, cutoff: pd.Timestamp, lag: int) -> np.ndarray:
    """Mask of events usable at the cut-off: event day position + lag <= pos(cutoff)."""
    return (pos >= 0) & (pos < len(cal)) & (pos + lag <= cal.pos(cutoff))


# ----------------------------------------------------------------------------
# LHB
# ----------------------------------------------------------------------------
def _pick_single_rows(df: pd.DataFrame, size_col: str, net_col: str) -> pd.DataFrame:
    """One single-day-reason row per (code, date): the largest `size_col`,
    ties broken by the larger |net| and then by the reason string (ruling
    F-6). Missing sizes sort last."""
    x = df.loc[df["cls"] == "single"].copy()
    x["_size"] = x[size_col].astype(float).fillna(-np.inf)
    x["_absnet"] = x[net_col].astype(float).abs().fillna(-np.inf)
    x = x.sort_values(["代码", "date", "_size", "_absnet", "上榜原因"], ascending=[True, True, False, False, True],
                      kind="mergesort")
    return x.groupby(["代码", "date"], sort=False).head(1)


def lhb_stock_day(lhb: pd.DataFrame, jg: pd.DataFrame) -> pd.DataFrame:
    """One record per (stock, listing day) (PLAN v0.7 5.6.3, ruling F-6).

    A stock can be listed for several reasons on one day; each row carries
    the seat amounts of its criterion, and the amounts of a multi-day reason
    ("three consecutive trading days ...") are cumulative over those days.

      n_rows         number of rows of the stock-day (any row = listed)
      multi          True if a multi-day-reason row is present
      has_single     True if a single-day-reason row is present
      n_unclassified rows whose reason the frozen table does not classify
                     (they count for the listing indicator only)
      net            龙虎榜净买额 of ONE single-day row: the one with the
                     largest seat traded amount (龙虎榜成交额), ties broken by
                     the larger |net buy|, then by the reason string. 0.0 when
                     the stock-day has no single-day row -- a cumulative
                     amount is never added to the daily amounts it contains.
      inst_net       机构买入净额 by the same rule on the institutional table
                     (size = 机构买入总额 + 机构卖出总额); 0.0 when it has no
                     single-day row for the stock-day.
    """
    a = lhb.copy()
    a["date"] = pd.to_datetime(a["上榜日"])
    a["cls"] = a["上榜原因"].map(reason_class) if len(a) else pd.Series([], dtype=object)
    a["_m"] = a["cls"] == "multi"
    a["_s"] = a["cls"] == "single"
    a["_u"] = (a["cls"] == "unclassified").astype(np.int64)
    g = a.groupby(["代码", "date"], sort=True)
    out = g.agg(n_rows=("cls", "size"), multi=("_m", "any"), has_single=("_s", "any"),
                n_unclassified=("_u", "sum")).reset_index()
    if not len(out):
        out = pd.DataFrame({"代码": pd.Series([], dtype=object), "date": pd.Series([], dtype="datetime64[ns]"),
                            "n_rows": pd.Series([], dtype=np.int64), "multi": pd.Series([], dtype=bool),
                            "has_single": pd.Series([], dtype=bool), "n_unclassified": pd.Series([], dtype=np.int64)})
    pick = _pick_single_rows(a, "龙虎榜成交额", "龙虎榜净买额")[["代码", "date", "龙虎榜净买额"]]
    out = out.merge(pick.rename(columns={"龙虎榜净买额": "net"}), on=["代码", "date"], how="left")
    out["net"] = np.where(out["has_single"].values.astype(bool), out["net"].astype(float), 0.0)
    b = jg.copy()
    if len(b):
        b["date"] = pd.to_datetime(b["上榜日期"])
        b["cls"] = b["上榜原因"].map(reason_class)
        b["turn"] = b["机构买入总额"].astype(float).fillna(0) + b["机构卖出总额"].astype(float).fillna(0)
        pj = _pick_single_rows(b, "turn", "机构买入净额")[["代码", "date", "机构买入净额"]]
        pj = pj.rename(columns={"机构买入净额": "inst_net"})
        pj["_has_inst"] = True
        out = out.merge(pj, on=["代码", "date"], how="left")
        out["inst_net"] = np.where(out["_has_inst"].eq(True).values, out["inst_net"].astype(float), 0.0)
        out = out.drop(columns="_has_inst")
    else:
        out["inst_net"] = 0.0                               # no institutional row = no institutional seat
    return out.reset_index(drop=True)


def lhb_features(lhb: pd.DataFrame, jg: pd.DataFrame, decision_days: pd.DatetimeIndex, cal: TradingCalendar,
                 cutoff, adv: pd.Series, cov_lhb: np.ndarray, cov_jg: np.ndarray, lag: int = ZO_LAG["lhb"]):
    """LHB features of ONE stock for the given decision days (<= cutoff).

    `adv` = ADV_t (PLAN U40, ruling F-7): mean traded amount of the 20 most
    recent TRADED days ending t-1, indexed by decision day
    (panel.adv_on_data_dates). Indicator and days-since: any row. Intensity:
    sum over the window of the stock-day `net` (resp. `inst_net`) of
    `lhb_stock_day`, divided by ADV_t; a missing ADV or amount with an event
    in the window gives NaN. `zo_lhb_multi_W` = 1{a multi-day-reason row in
    the window}."""
    t = check_cutoff(cal, cutoff)
    L = len(cal)
    dec_pos = cal.pos_array(decision_days)
    sd = lhb_stock_day(lhb, jg)
    pos = cal.pos_array(sd["date"]) if len(sd) else np.zeros(0, dtype=np.int64)
    keep = _truncate_events(pos, cal, t, lag)
    n_off = int((pos < 0).sum())
    pos = pos[keep]
    net, inst = sd["net"].values[keep].astype(float), sd["inst_net"].values[keep].astype(float)
    multi = sd["multi"].values[keep].astype(bool)
    cnt = np.bincount(pos, minlength=L)[:L]
    cnt_multi = np.bincount(pos[multi], minlength=L)[:L].astype(np.float64)
    res, valid, data = _encode_timing(cnt, cov_lhb, dec_pos, lag)
    end = dec_pos - lag
    a = adv.reindex(decision_days).values.astype(float)
    out = {}
    for w in ZO_LOOKBACKS:
        ind = res[f"ind_{w}"]
        out[f"zo_lhb_ind_{w}"] = ind
        with np.errstate(all="ignore"):
            s_net = _win_sum(_daily(pos, net, L), end, w) / a
            s_inst = _win_sum(_daily(pos, inst, L), end, w) / a
        ok_inst = valid[w] & (_win_sum(cov_jg.astype(float), end, w) == w)
        out[f"zo_lhb_net_{w}"] = np.where(ind == 0, 0.0, np.where(valid[w] & np.isfinite(s_net), s_net, np.nan))
        out[f"zo_lhb_inst_net_{w}"] = np.where(~ok_inst, np.nan,
                                               np.where(ind == 0, 0.0, np.where(np.isfinite(s_inst), s_inst, np.nan)))
        out[f"zo_lhb_multi_{w}"] = np.where(valid[w], (_win_sum(cnt_multi, end, w) > 0).astype(float), np.nan)
    out["zo_lhb_days_since"] = res["days_since"]
    out["zo_lhb_has_prior"] = res["has_prior"]
    out["ro_lhb_data"] = data
    df = pd.DataFrame(out, index=decision_days)
    df.attrs["n_event_days_off_calendar"] = n_off
    df.attrs["n_unclassified_rows"] = int(sd["n_unclassified"].sum()) if len(sd) else 0
    df.attrs["n_stock_days_multi_only"] = int((sd["multi"] & ~sd["has_single"]).sum()) if len(sd) else 0
    return df


# ----------------------------------------------------------------------------
# BLK
# ----------------------------------------------------------------------------
def blk_plausibility(code: str, days: pd.DatetimeIndex, price: np.ndarray, bars: pd.DataFrame):
    """(premium, plausible) of block trades of ONE stock (PLAN v0.8 ruling J-7, U64; task C-4).

    premium = trade price / the stock's UNADJUSTED close of the trade day - 1, from our own
    bars (the vendor's 折溢率 column is not read).  A trade is "implausible" if the stock has no
    traded row on the trade day, or the trade price lies outside the day's [P_down, P_up],
    computed from our own `preclose` and the rule calendar's band with the engine's
    limit-price function (decimal half-up rounding to 0.01; no copy of the formula here).
    Implausible trades get premium NaN; they still count for the indicator, days-since and
    the amount intensity (blk_features)."""
    from decimal import Decimal
    from engine import rule_calendar as rc
    n = len(price)
    prem = np.full(n, np.nan)
    ok = np.zeros(n, dtype=bool)
    if n == 0:
        return prem, ok
    b = bars.reindex(days)
    close = b["close"].to_numpy(dtype=np.float64)
    pre = b["preclose"].to_numpy(dtype=np.float64)
    traded = b["traded"].fillna(False).to_numpy(dtype=bool)
    st = b["is_st"].fillna(False).to_numpy(dtype=bool)
    for j in range(n):
        if not (traded[j] and np.isfinite(close[j]) and close[j] > 0 and np.isfinite(pre[j]) and pre[j] > 0
                and np.isfinite(price[j]) and price[j] > 0):
            continue
        up, dn, _band = rc.limit_prices_for(code, days[j].date(), Decimal(repr(float(pre[j]))), bool(st[j]))
        p = Decimal(repr(float(price[j])))
        if dn <= p <= up:
            ok[j] = True
            prem[j] = price[j] / close[j] - 1.0
    return prem, ok


def blk_features(blk: pd.DataFrame, decision_days: pd.DatetimeIndex, cal: TradingCalendar, cutoff,
                 float_mv: pd.Series, cov: np.ndarray, lag: int = ZO_LAG["blk"], bars: pd.DataFrame | None = None,
                 code: str | None = None):
    """BLK features of ONE stock from the per-trade table.
    Intensities: (i) sum over the window of traded amount / float market value
    of the trade day (float market value = unadjusted close x float shares,
    float shares = volume / V of the last traded day, from our own bars -- the
    vendor's ratio column is not used; ruling F-11); (ii) amount-weighted
    premium of the trade price over the UNADJUSTED close of the trade day,
    recomputed from our own bars (PLAN v0.8 ruling J-7, U64; the vendor column
    折溢率 is not read), over the PLAUSIBLE trades of the window only
    (blk_plausibility); NaN if the window has trades but none is plausible.
    `bars` = the stock's standardised bar frame (bars.prepare_bars) and `code`
    are required."""
    if bars is None or code is None:
        raise ValueError("blk_features needs the stock's own bars and code (PLAN v0.8 J-7: premium from own bars)")
    t = check_cutoff(cal, cutoff)
    L = len(cal)
    dec_pos = cal.pos_array(decision_days)
    d = pd.to_datetime(blk["交易日期"]) if len(blk) else pd.DatetimeIndex([])
    pos = cal.pos_array(d) if len(blk) else np.zeros(0, dtype=np.int64)
    keep = _truncate_events(pos, cal, t, lag)
    n_off = int((pos < 0).sum())
    pos = pos[keep]
    amt = blk["成交额"].values[keep].astype(float)
    price = pd.to_numeric(pd.Series(blk["成交价"].values[keep]), errors="coerce").to_numpy(dtype=np.float64)
    tdays = cal.days[pos]
    prem, plaus = blk_plausibility(code, tdays, price, bars.loc[bars.index < t])
    fmv = float_mv.reindex(tdays).values.astype(float) if len(pos) else np.zeros(0)
    cnt = np.bincount(pos, minlength=L)[:L]
    res, valid, data = _encode_timing(cnt, cov, dec_pos, lag)
    end = dec_pos - lag
    out = {}
    with np.errstate(all="ignore"):
        d_ratio = _daily(pos, amt / fmv, L)
        d_amt = _daily(pos[plaus], amt[plaus], L)                 # plausible trades only (J-7)
        d_ap = _daily(pos[plaus], amt[plaus] * prem[plaus], L)
        for w in ZO_LOOKBACKS:
            ind = res[f"ind_{w}"]
            out[f"zo_blk_ind_{w}"] = ind
            ratio = _win_sum(d_ratio, end, w)
            wprem = _win_sum(d_ap, end, w) / _win_sum(d_amt, end, w)
            out[f"zo_blk_amt_{w}"] = np.where(ind == 0, 0.0, np.where(valid[w] & np.isfinite(ratio), ratio, np.nan))
            out[f"zo_blk_prem_{w}"] = np.where(ind == 0, 0.0, np.where(valid[w] & np.isfinite(wprem), wprem, np.nan))
    out["zo_blk_days_since"] = res["days_since"]
    out["zo_blk_has_prior"] = res["has_prior"]
    out["ro_blk_data"] = data
    df = pd.DataFrame(out, index=decision_days)
    df.attrs["n_event_days_off_calendar"] = n_off
    yrs = tdays.year if len(tdays) else np.zeros(0, dtype=int)
    by_year = {}
    for y in np.unique(yrs):
        m = yrs == y
        by_year[int(y)] = [int(m.sum()), int((m & ~plaus).sum())]
    df.attrs["blk_stats"] = {"trades": int(len(pos)), "implausible": int((~plaus).sum()), "by_year": by_year}
    return df


# ----------------------------------------------------------------------------
# INS
# ----------------------------------------------------------------------------
def clean_ins(ins: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Rows usable as events (ruling F-9). Dropped and counted: no
    announcement date; a direction other than 增持 / 减持; announcement date
    before the end date of the change (cannot be an announcement of that
    change; such a row may have been overwritten with later information)."""
    x = ins.copy()
    x["notice"] = pd.to_datetime(x["NOTICE_DATE"], errors="coerce")
    x["end"] = pd.to_datetime(x["END_DATE"], errors="coerce")
    n0 = len(x)
    no_date = x["notice"].isna()
    bad_dir = ~x["DIRECTION"].isin(["增持", "减持"])
    early = x["notice"] < x["end"]
    keep = ~(no_date | bad_dir | early)
    stats = {"rows": n0, "dropped_no_notice_date": int(no_date.sum()), "dropped_direction": int(bad_dir.sum()),
             "dropped_notice_before_end": int(early.sum()), "kept": int(keep.sum())}
    if "EITIME" in x.columns and n0:
        ei = pd.to_datetime(x["EITIME"], errors="coerce")
        stats["share_entered_gt30d_after_notice"] = float(((ei - x["notice"]).dt.days > 30)[keep].mean()) if keep.any() else float("nan")
    return x.loc[keep], stats


def ins_features(ins: pd.DataFrame, decision_days: pd.DatetimeIndex, cal: TradingCalendar, cutoff,
                 cov: np.ndarray, lag: int = ZO_LAG["ins"], intensity_enabled: bool | None = None):
    """INS features of ONE stock. Event day = first trading day >= the
    announcement date. Intensity: change as a share of float shares (vendor
    column CHANGE_FREE_RATIO, in percent, unsigned; divided by 100), summed
    over the window; purchases positive, sales negative; buys and sells kept
    separate (PLAN 5.6.2a (ii)).

    `intensity_enabled` (default config.INS_INTENSITY_ENABLED; ruling F-10):
    when False -- the value check OA5 of CHANGE_FREE_RATIO failed -- the four
    x three intensity columns are all-NaN; the indicator, days-since and
    has_prior columns are unaffected."""
    intensity_enabled = config.INS_INTENSITY_ENABLED if intensity_enabled is None else intensity_enabled
    t = check_cutoff(cal, cutoff)
    L = len(cal)
    dec_pos = cal.pos_array(decision_days)
    x, stats = clean_ins(ins)
    pos_all = cal.roll_forward_pos(x["notice"]) if len(x) else np.zeros(0, dtype=np.int64)
    keep = _truncate_events(pos_all, cal, t, lag)
    ratio = x["CHANGE_FREE_RATIO"].values.astype(float) / 100.0
    is_buy = (x["DIRECTION"].values == "增持")
    end = dec_pos - lag
    out = {}
    data = None
    for side, mask, sign in (("buy", is_buy, 1.0), ("sell", ~is_buy, -1.0)):
        m = keep & mask
        pos = pos_all[m]
        cnt = np.bincount(pos, minlength=L)[:L]
        res, valid, data = _encode_timing(cnt, cov, dec_pos, lag)
        dly = _daily(pos, sign * ratio[m], L)
        for w in ZO_LOOKBACKS:
            ind = res[f"ind_{w}"]
            s = _win_sum(dly, end, w)
            out[f"zo_ins_{side}_ind_{w}"] = ind
            if intensity_enabled:
                out[f"zo_ins_{side}_{w}"] = np.where(ind == 0, 0.0, np.where(valid[w] & np.isfinite(s), s, np.nan))
            else:
                out[f"zo_ins_{side}_{w}"] = np.full(len(dec_pos), np.nan)
        out[f"zo_ins_{side}_days_since"] = res["days_since"]
        out[f"zo_ins_{side}_has_prior"] = res["has_prior"]
    out["ro_ins_data"] = data
    df = pd.DataFrame(out, index=decision_days)
    df.attrs.update(stats)
    return df


# ----------------------------------------------------------------------------
# assembly
# ----------------------------------------------------------------------------
def specs() -> list[FeatureSpec]:
    S = FeatureSpec
    out = []
    tim = {c: (f"event day s usable for t >= s + {ZO_LAG[c]} trading days (PLAN 5.6.2); windows ordered by "
               "availability: s in [t-lag-W+1, t-lag] (PLAN v0.7 ruling F-4)") for c in ZO_LAG}
    tim["ins"] += "; announcement date rolled FORWARD to a trading day, then the lag (F-9)"
    src = {"lhb": "PLAN 5.6.3; RC-18: no clock time in the rule -> lag 2; several rows per stock-day: PLAN v0.7 "
                  "ruling F-6 (frozen reason table lhb_reason_map.csv)",
           "blk": "PLAN 5.6.3; RC-19: clause archived only for SZSE 2013/2026 and SSE 2023/2026 texts -> lag 2 "
                  "(PLAN v0.7 ruling F-8)",
           "ins": "PLAN 5.6.3; announcement date as in the vendor table, NOT audited (OA10 pending); cleaning rule: "
                  "rows with a missing date, another direction or an announcement before the end of the change are "
                  "dropped and counted (PLAN v0.7 ruling F-9); about 59% of rows back-filled, used like any row"}
    ds = (f"t - s* for the latest usable event day s* with t-{ZO_PRIOR_LOOKBACK} <= s* <= t-lag, capped at "
          f"{ZO_DAYS_SINCE_CAP}; 0 if none; NaN until {ZO_PRIOR_LOOKBACK}+lag days of coverage")
    hp = f"1{{a usable event day s with t-{ZO_PRIOR_LOOKBACK} <= s <= t-lag}}; NaN until {ZO_PRIOR_LOOKBACK}+lag days of coverage"
    f5 = "; PLAN v0.7 ruling F-5 (U60)"
    adv = "ADV_t = mean traded amount of the 20 most recent traded days ending t-1 (U40; PLAN v0.7 ruling F-7)"
    for w in ZO_LOOKBACKS:
        out += [
            S(f"zo_lhb_ind_{w}", "Z_O", "primary", "1{listed (any row) on a day in window(t, w)}", str(w),
              "lhb_detail: 上榜日", 0, tim["lhb"], src["lhb"]),
            S(f"zo_lhb_net_{w}", "Z_O", "primary",
              "sum over window of 龙虎榜净买额 of one single-day-reason row per stock-day (largest 龙虎榜成交额; ties: "
              "larger |net|, then reason string; 0 for a stock-day with multi-day rows only) / " + adv,
              str(w), "lhb_detail: 龙虎榜净买额, 龙虎榜成交额, 上榜原因; bars: amount", 1, tim["lhb"], src["lhb"]),
            S(f"zo_lhb_inst_net_{w}", "Z_O", "primary",
              "sum over window of 机构买入净额 of one single-day-reason row per stock-day (largest 机构买入总额 + "
              "机构卖出总额; same tie-breaks; 0 if none) / " + adv,
              str(w), "lhb_jgmmtj: 机构买入净额, 机构买入总额, 机构卖出总额, 上榜原因; bars: amount", 1,
              tim["lhb"], src["lhb"]),
            S(f"zo_lhb_multi_{w}", "Z_O", "primary", "1{a row with a multi-day listing reason on a day in window(t, w)}",
              str(w), "lhb_detail: 上榜日, 上榜原因", 0, tim["lhb"], src["lhb"]),
        ]
    out += [S("zo_lhb_days_since", "Z_O", "primary", ds.replace("event day", "listing day"), str(ZO_PRIOR_LOOKBACK),
              "lhb_detail: 上榜日", 0, tim["lhb"], src["lhb"] + f5),
            S("zo_lhb_has_prior", "Z_O", "primary", hp.replace("event day", "listing day"), str(ZO_PRIOR_LOOKBACK),
              "lhb_detail: 上榜日", 0, tim["lhb"], src["lhb"] + f5),
            ]
    blk_mv = "; float market value from own bars, the vendor's ratio column is not used (PLAN v0.7 ruling F-11)"
    for w in ZO_LOOKBACKS:
        out += [
            S(f"zo_blk_ind_{w}", "Z_O", "primary", "1{block trade on a day in window(t, w)}", str(w),
              "dzjy_mrmx: 交易日期", 0, tim["blk"], src["blk"]),
            S(f"zo_blk_amt_{w}", "Z_O", "primary", "sum over window of 成交额 / (close x float shares of the trade day)",
              str(w), "dzjy_mrmx: 成交额; bars: close, volume, turn", 1, tim["blk"], src["blk"] + blk_mv),
            S(f"zo_blk_prem_{w}", "Z_O", "primary",
              "amount-weighted (trade price / own unadjusted close of the trade day - 1) over the plausible trades "
              "of the window (negative = discount); NaN if none is plausible",
              str(w), "dzjy_mrmx: 成交价, 成交额; bars: close, preclose, isST", 0, tim["blk"],
              src["blk"] + "; premium recomputed from own bars with the plausibility rule of PLAN v0.8 ruling J-7 "
              "(U64): outside [P_down, P_up] or no traded row -> excluded"),
        ]
    out += [S("zo_blk_days_since", "Z_O", "primary", ds.replace("event day", "block-trade day"), str(ZO_PRIOR_LOOKBACK),
              "dzjy_mrmx: 交易日期", 0, tim["blk"], src["blk"] + f5),
            S("zo_blk_has_prior", "Z_O", "primary", hp.replace("event day", "block-trade day"), str(ZO_PRIOR_LOOKBACK),
              "dzjy_mrmx: 交易日期", 0, tim["blk"], src["blk"] + f5)]
    oa5 = ("; CHANGE_FREE_RATIO's meaning is inferred from column positions and pending OA5: if it fails the "
           "intensity is dropped (config.INS_INTENSITY_ENABLED) and the indicator kept (PLAN v0.7 ruling F-10)")
    for side, word in (("buy", "增持"), ("sell", "减持")):
        for w in ZO_LOOKBACKS:
            out += [
                S(f"zo_ins_{side}_ind_{w}", "Z_O", "primary", f"1{{a {word} announcement on a day in window(t, w)}}",
                  str(w), "ins_raw: NOTICE_DATE, DIRECTION, END_DATE", 0, tim["ins"], src["ins"]),
                S(f"zo_ins_{side}_{w}", "Z_O", "primary",
                  f"signed sum over window of CHANGE_FREE_RATIO / 100 of {word} records", str(w),
                  "ins_raw: NOTICE_DATE, DIRECTION, CHANGE_FREE_RATIO, END_DATE", 0, tim["ins"], src["ins"] + oa5),
            ]
        out += [S(f"zo_ins_{side}_days_since", "Z_O", "primary", ds.replace("event day", f"{word} announcement day"),
                  str(ZO_PRIOR_LOOKBACK), "ins_raw: NOTICE_DATE, DIRECTION", 0, tim["ins"], src["ins"] + f5),
                S(f"zo_ins_{side}_has_prior", "Z_O", "primary", hp.replace("event day", f"{word} announcement day"),
                  str(ZO_PRIOR_LOOKBACK), "ins_raw: NOTICE_DATE, DIRECTION", 0, tim["ins"], src["ins"] + f5)]
    return out


ZO_NAMES = [s.name for s in specs()]
ZO_CLASS_OF = {n: n.split("_")[1] for n in ZO_NAMES}
RO_DATA_NAMES = ["ro_lhb_data", "ro_blk_data", "ro_ins_data"]
INS_INTENSITY_NAMES = [f"zo_ins_{side}_{w}" for side in ("buy", "sell") for w in ZO_LOOKBACKS]


def zo_features(code: str, decision_days: pd.DatetimeIndex, cal: TradingCalendar, cutoff, tables: ZOTables,
                adv: pd.Series, float_mv: pd.Series, lags: dict | None = None, strict: bool | None = None,
                ins_intensity_enabled: bool | None = None, bars: pd.DataFrame | None = None) -> pd.DataFrame:
    """All Z_O columns and the three `ro_<class>_data` indicators of one
    stock, for decision days <= cutoff. `strict`: see coverage_array
    (production default True: a raw file missing inside the analysis period
    raises MissingRawFile). The analysis period of every class ends at the
    data cut-off of the tables (ZOTables.data_cutoff, PLAN v0.8 C-8). `bars`
    = the stock's bar frame (needed for the BLK premium, J-7)."""
    lags = dict(ZO_LAG) if lags is None else lags
    t = check_cutoff(cal, cutoff)
    decision_days = decision_days[decision_days <= t]
    tb = tables.for_code(code)
    cov = tables.coverage
    end = tables.analysis_end()
    c_lhb = coverage_array(cal, "lhb", cov.get("lhb", ()), strict=strict, end=end)
    c_jg = coverage_array(cal, "lhb", cov.get("jg", ()), strict=strict, end=end)
    c_blk = coverage_array(cal, "blk", cov.get("blk", ()), strict=strict, end=end)
    c_ins = coverage_array(cal, "ins", cov.get("ins", ()), strict=strict, end=end)
    a = lhb_features(tb.lhb, tb.jg, decision_days, cal, t, adv, c_lhb, c_jg, lags["lhb"])
    b = blk_features(tb.blk, decision_days, cal, t, float_mv, c_blk, lags["blk"], bars=bars, code=code)
    c = ins_features(tb.ins, decision_days, cal, t, c_ins, lags["ins"], ins_intensity_enabled)
    out = pd.concat([a, b, c], axis=1)[ZO_NAMES + RO_DATA_NAMES]
    out.attrs["ins_stats"] = dict(c.attrs)
    out.attrs["lhb_stats"] = dict(a.attrs)
    out.attrs["blk_stats"] = dict(b.attrs.get("blk_stats", {}))
    return out

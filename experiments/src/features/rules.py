"""Adapter between the feature library and the ONE rule calendar
(`experiments/src/engine/rule_calendar.py`; PLAN v0.7 section 3.10, rulings
E-20 / F-20: "a second copy of a band, threshold or regime date anywhere in
the code is a defect").

This module holds NO band, threshold or regime date. Everything is read from
the engine calendar through `rule_calendar.intervals(key)`:

    band:<board>:<st>      price-limit bands RC-6 (a)-(e)
    lhb_thr:<board>        Dragon-Tiger criteria RC-18 (kind, price, amplitude, turnover)
    lhb_topn:<sh|sz>       (N, top-5 indicator), None = unknown (ruling F-13)
    ins_regime             index 0..4 of the share-reduction disclosure regime RC-20

and the board / exchange classification. What it adds is vectorisation over
a DatetimeIndex and one convention: a date outside the calendar window
2008-01-01 .. 2026-06-30 gives NaN ("unknown") instead of raising, because
decision day 2026-07-01 (the day after the last data day) exists in the
panels.

Not read from the calendar, and why:
  * the calendar rows `ipo_nolimit5:<board>` (RC-6 (f)) are deliberately NOT
    used: by ruling F-20 the limit-count controls are NaN while their window
    contains any of a name's first 5 trading days, for every board and every
    listing date, so that the unverified date of the main-board registration
    reform (list item 21) enters no computation. The count 5 is
    config.FIRST_DAYS_NAN.
  * (v0.8, J-1 / C-3) the threshold of the "three consecutive days,
    cumulative deviation" criterion is now the element `cum3` of the RC-18
    rows (`lhb_thresholds(...)["cum3"]`); the former copy
    config.RO_CUM3_THRESHOLD is deleted.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine import rule_calendar as rc

from .config import FIRST_DAYS_NAN

_EXCH = {"sh": "sse", "sz": "szse"}
_EXCH_KEY = {"sse": "sh", "szse": "sz"}


def _lookup_values(key: str, dates: pd.DatetimeIndex) -> np.ndarray:
    """Object array: the calendar value of `key` on each date; None where no
    row applies (outside the calendar window)."""
    d = pd.DatetimeIndex(dates).values.astype("datetime64[D]")
    out = np.full(len(d), None, dtype=object)
    hit = np.zeros(len(d), dtype=np.int64)
    for start, end, value in rc.intervals(key):
        m = (d >= np.datetime64(start)) & (d <= np.datetime64(end))
        hit += m
        for i in np.nonzero(m)[0]:
            out[i] = value
    if (hit > 1).any():
        raise rc.CalendarError(f"overlapping rule rows for key {key!r}")
    return out


def _as_float(vals) -> np.ndarray:
    return np.array([np.nan if v is None else float(v) for v in vals], dtype=np.float64)


# ---------------------------------------------------------------- classification
def board_of(code: str) -> tuple[str, str]:
    """('sse' | 'szse', 'main' | 'star' | 'chinext') from a BaoStock code such
    as 'sh.600000' (engine calendar; prefix 302 -> ChiNext is the fetch
    author's judgement, unverified). Raises ValueError for anything else."""
    return _EXCH[rc.exchange_of(code)], rc.board_of(code)


# ---------------------------------------------------------------- price limits (RC-5, RC-6)
def limit_band(board: str, is_st: np.ndarray, dates: pd.DatetimeIndex) -> np.ndarray:
    """Daily price-limit band from the calendar rows `band:<board>:<st>`
    (RC-6 a-e). NaN outside the calendar window."""
    is_st = np.asarray(is_st, dtype=bool)
    b0 = _as_float(_lookup_values(f"band:{board}:0", dates))
    b1 = _as_float(_lookup_values(f"band:{board}:1", dates))
    return np.where(is_st, b1, b0)


def round_half_up_cent(x: np.ndarray) -> np.ndarray:
    return np.floor(np.asarray(x, dtype=np.float64) * 100.0 + 0.5 + 1e-6) / 100.0


def limit_prices(preclose: np.ndarray, band: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Limit-up / limit-down prices: preclose * (1 +- band) rounded half-up to
    0.01 yuan; if the distance is below 0.01 yuan, preclose +- 0.01 (RC-5).
    Vectorised float version of `rule_calendar.limit_prices` (exact decimal
    arithmetic on one price); the two are compared in the tests."""
    up = round_half_up_cent(preclose * (1.0 + band))
    dn = round_half_up_cent(preclose * (1.0 - band))
    up = np.where(up - preclose < 0.01 - 1e-9, preclose + 0.01, up)
    dn = np.where(preclose - dn < 0.01 - 1e-9, preclose - 0.01, dn)
    return up, dn


def first_trading_rows(dates: pd.DatetimeIndex, ipo_date, cal=None) -> np.ndarray:
    """True on the rows that fall on the name's first FIRST_DAYS_NAN (5)
    trading days (ruling F-20). The limit-count controls are NaN while their
    window contains such a row, whatever the board and the listing date -- no
    date of a registration reform is used.

    The first 5 trading days are the 5 market trading days from the listing
    day. With a calendar they are counted on it; without one, on the name's
    rows (the standardised bar frame has one row per market day). If the
    listing day is unknown, the first 5 rows are flagged (it cannot be
    excluded that the history starts at the listing)."""
    n_days = FIRST_DAYS_NAN
    out = np.zeros(len(dates), dtype=bool)
    if len(dates) == 0:
        return out
    if ipo_date is None or pd.isna(ipo_date):
        out[:n_days] = True
        return out
    ipo = pd.Timestamp(ipo_date)
    if cal is not None:
        p0 = int(cal.roll_forward_pos([ipo])[0])
        last = p0 + n_days - 1
        if last >= len(cal):
            return np.ones(len(dates), dtype=bool)
        return dates.values <= np.datetime64(cal.days[last])
    k = int(np.searchsorted(dates.values, np.datetime64(ipo), side="left"))   # rows dated before the listing day
    if k == 0 and dates[0] > ipo:
        return out                       # history starts after the listing day; days in between unknown without a calendar
    out[:k + n_days] = True
    return out


# ---------------------------------------------------------------- Dragon-Tiger list (RC-18)
def lhb_thresholds(board: str, dates: pd.DatetimeIndex) -> dict:
    """Arrays 'dev' (price criterion), 'amp', 'turn' and 'raw' (1.0 where the
    price criterion is on the raw close-to-close change -- calendar kind
    'change', the 15/30/30 regime; 0.0 where it is on the deviation from the
    index -- kind 'deviation', 7/15/20). NaN outside the calendar window."""
    vals = _lookup_values(f"lhb_thr:{board}", dates)
    n = len(vals)
    out = {k: np.full(n, np.nan) for k in ("dev", "amp", "turn", "raw", "cum3")}
    for i, v in enumerate(vals):
        if v is None:
            continue
        if v["kind"] not in ("deviation", "change"):
            raise rc.CalendarError("unknown kind of Dragon-Tiger criterion: " + str(v["kind"]))
        out["dev"][i], out["amp"][i], out["turn"][i] = v["price"], v["amplitude"], v["turnover"]
        out["raw"][i] = 1.0 if v["kind"] == "change" else 0.0
        out["cum3"][i] = v["cum3"]          # PLAN v0.8 J-1: element 'cum3' of RC-18 (unverified, list item 22)
    return out


def lhb_threshold_regime(board: str, dates: pd.DatetimeIndex) -> np.ndarray:
    """1.0 where the criteria are +-15% / 30% / 30% on the raw change, 0.0
    where they are +-7% deviation / 15% / 20% (RC-18)."""
    return lhb_thresholds(board, dates)["raw"]


def lhb_top5_regime(exchange: str, dates: pd.DatetimeIndex) -> np.ndarray:
    """Three-valued (ruling F-13): 1.0 where five names are listed per
    criterion, 0.0 where three, NaN where unknown. Per the calendar -- SSE: 0
    before 2021-09-17, unknown 2021-09-17 .. 2021-10-07, 1 from 2021-10-08;
    SZSE: unknown before 2013-12-01, 1 from then. The dates are unverified
    (list items 7, 19)."""
    vals = _lookup_values(f"lhb_topn:{_EXCH_KEY[exchange]}", dates)
    return _as_float([None if v is None else v[1] for v in vals])


# ---------------------------------------------------------------- share-change disclosure (RC-20)
def ins_regime(dates: pd.DatetimeIndex) -> np.ndarray:
    """Index 0..4 of the INS disclosure regime in force on each date (RC-20);
    NaN outside the calendar window."""
    return _as_float(_lookup_values("ins_regime", dates))


E_GROUP_KEYS = ("lhb_thr:main", "lhb_thr:chinext", "lhb_thr:star", "lhb_topn:sh", "lhb_topn:sz", "ins_regime")


def boundary_dates() -> list[tuple[str, pd.Timestamp]]:
    """(key, first day of a new row) of the group-(e) keys read here, from
    the calendar."""
    return [(k, pd.Timestamp(d)) for k, d in rc.boundary_dates() if k in E_GROUP_KEYS]

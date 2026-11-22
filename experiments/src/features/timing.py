"""Trading calendar and the information cut-off G_t (PLAN 3.1).

Convention used by every feature function in this package
----------------------------------------------------------
`cutoff` is a **decision day t** (a trading day). The function may use

  * bar rows dated strictly before t (data through the close of t-1);
  * the trading calendar (pre-open public information);
  * event records whose availability day is <= t, where the availability day
    of an event of trading day s is s + lag (lag in trading days, PLAN 5.6.2).

Bar-based features are computed "as of data date s" (using rows <= s) and are
then re-indexed to the decision day next(s). A feature frame is therefore
always indexed by decision day, and row t depends on G_t only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class TradingCalendar:
    """Sorted array of market trading days."""

    def __init__(self, days):
        d = pd.DatetimeIndex(pd.to_datetime(list(days))).sort_values().unique()
        self.days = d
        self._v = d.values

    def __len__(self):
        return len(self.days)

    def pos(self, day) -> int:
        """Position of a trading day; raises if `day` is not a trading day."""
        day = np.datetime64(pd.Timestamp(day))
        i = int(np.searchsorted(self._v, day))
        if i >= len(self._v) or self._v[i] != day:
            raise KeyError(f"{pd.Timestamp(day).date()} is not a trading day")
        return i

    def is_trading_day(self, day) -> bool:
        day = np.datetime64(pd.Timestamp(day))
        i = int(np.searchsorted(self._v, day))
        return i < len(self._v) and self._v[i] == day

    def pos_array(self, dates) -> np.ndarray:
        """Positions of trading days (vectorised); -1 where not a trading day."""
        v = pd.DatetimeIndex(dates).values
        i = np.searchsorted(self._v, v)
        ok = (i < len(self._v))
        out = np.full(len(v), -1, dtype=np.int64)
        ii = np.where(ok, i, 0)
        hit = ok & (self._v[ii] == v)
        out[hit] = i[hit]
        return out

    def roll_forward_pos(self, dates) -> np.ndarray:
        """Position of the first trading day >= date; len(calendar) if none."""
        v = pd.DatetimeIndex(dates).values
        return np.searchsorted(self._v, v, side="left").astype(np.int64)

    def prev(self, day) -> pd.Timestamp:
        """Last trading day strictly before `day`."""
        i = int(np.searchsorted(self._v, np.datetime64(pd.Timestamp(day)), side="left")) - 1
        if i < 0:
            raise KeyError("no trading day before " + str(day))
        return self.days[i]

    def next(self, day) -> pd.Timestamp:
        """First trading day strictly after `day`."""
        i = int(np.searchsorted(self._v, np.datetime64(pd.Timestamp(day)), side="right"))
        if i >= len(self._v):
            raise KeyError("no trading day after " + str(day))
        return self.days[i]

    def next_index(self, data_dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
        """Decision day next(s) for each data date s (vectorised)."""
        i = np.searchsorted(self._v, pd.DatetimeIndex(data_dates).values, side="right")
        if len(i) and i.max() >= len(self._v):
            raise KeyError("calendar ends before the day after the last data date")
        return self.days[i]


def check_cutoff(cal: TradingCalendar, cutoff) -> pd.Timestamp:
    """Validate a cut-off: it must be a trading day (a decision day)."""
    if cutoff is None:
        raise ValueError("an explicit information cut-off (decision day) is required")
    t = pd.Timestamp(cutoff)
    if not cal.is_trading_day(t):
        raise ValueError(f"cut-off {t.date()} is not a trading day")
    return t


def truncate_bars(bars: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    """Rows dated strictly before the decision day `cutoff` (G_t, PLAN 3.1)."""
    return bars.loc[bars.index < cutoff]


def to_decision_index(frame: pd.DataFrame, cal: TradingCalendar) -> pd.DataFrame:
    """Re-index a frame computed 'as of data date s' to decision day next(s)."""
    out = frame.copy()
    out.index = cal.next_index(frame.index)
    out.index.name = "decision_day"
    return out

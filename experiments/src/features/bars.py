"""Standardised per-stock bar frame and the feature-level adjustment factor.

Feature-level adjustment (PLAN 3.11; features only, never accounting)
---------------------------------------------------------------------
    F_t = prod_{s <= t} close_{s-1} / preclose_s      (F = 1 on the first row)
    adjusted price_t = unadjusted price_t * F_t

over all rows of the name, suspended-day rows included; "s-1" is the name's
previous row. The series is anchored at the first row, so a value never
changes when a later event occurs. F_t uses preclose_t, which is pre-open
public information of day t; features for decision day t use adjusted prices
through t-1 only.

Difference from a vendor factor: no vendor table is read. The series is the
total-return index implied by the exchange's reference prices (cash dividends
gross of tax and as if reinvested at the reference price; rights as if
subscribed). It inherits every error of the `preclose` field. It is anchored
at the first row (a vendor "forward" factor is anchored at the last row and
rewrites its own past; a vendor "backward" factor is anchored at the listing
day, so levels differ from ours by a constant when our first row is not the
listing day -- every feature here is a ratio within a name, so the anchor
cancels up to floating-point rounding).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .timing import TradingCalendar

NUMERIC = ["open", "high", "low", "close", "preclose", "volume", "amount", "turn", "tradestatus", "isST"]

# FC-A4 in the feature library (PLAN v0.8 ruling J-15, task C-6; mirror of the engine loader)
FORBIDDEN_COLUMN_PARTS = ("factor", "adj_", "_adj", "adjclose", "adjopen", "hfq", "qfq", "foreadjust", "backadjust")


class AdjustedDataError(ValueError):
    """A vendor adjustment factor or adjusted price reached the feature library (FC-A4)."""


def check_unadjusted(df: pd.DataFrame, what: str = "") -> None:
    """Refuse factor / adjusted-price columns and any adjustflag other than '3' (FC-A4)."""
    bad = [c for c in df.columns if any(p in str(c).lower() for p in FORBIDDEN_COLUMN_PARTS)]
    if bad:
        raise AdjustedDataError(f"{what}: bar data carry factor / adjusted-price columns {bad}; refused (FC-A4)")
    if "adjustflag" in df.columns and len(df):
        vals = sorted(set(df["adjustflag"].astype(str).str.strip()))
        if vals != ["3"]:
            raise AdjustedDataError(f"{what}: adjustflag values {vals}; only unadjusted bars ('3') are accepted (FC-A4)")


def own_adjust_factor(close: np.ndarray, preclose: np.ndarray) -> np.ndarray:
    """F_t of PLAN 3.11 over consecutive rows. NaN from the first row whose
    ratio cannot be formed (missing or non-positive close / preclose)."""
    n = len(close)
    ratio = np.ones(n, dtype=np.float64)
    if n > 1:
        with np.errstate(all="ignore"):
            r = close[:-1] / preclose[1:]
        bad = ~(np.isfinite(r) & (r > 0))
        r = np.where(bad, np.nan, r)
        ratio[1:] = r
    return np.cumprod(ratio)


def prepare_bars(raw: pd.DataFrame, cal: TradingCalendar, data_cutoff=None) -> pd.DataFrame:
    """Raw BaoStock daily rows (all strings) -> float frame on the market
    calendar between the name's first and last row.

    Columns: open high low close preclose volume amount (unadjusted; volume in
    shares, amount in yuan), V (turnover as a fraction of float shares,
    = `turn` / 100, audit A10), traded (tradestatus == 1 and volume > 0),
    is_st, present (a vendor row exists for the day), F, aopen ahigh alow
    aclose (adjusted), avwap (amount / volume * F), avolume (volume / F).

    Rules (AUDIT_REPORT 3.1 A8, section 6 item 8): empty strings are missing;
    on a day that is not `traded`, volume = amount = V = 0. A market trading
    day inside the span without a vendor row is inserted with NaN prices and
    present = False -- nothing is carried forward, so every window that
    contains it is NaN. `attrs` records the counts.

    Repaired rows (PLAN v0.7 section 3.11 rule 12; rulings F-18 / E-16). The
    FETCH pipeline may insert a row taken from the cross-check source for a
    day the bar source lacks; such a row arrives in `raw` like any other row,
    with the optional column `filled_from_xsrc` set (1 / "1" / True). It is
    used as an ordinary row; the flag is carried in the column `filled_xsrc`
    and surfaces in the panel as the diagnostic column
    `diag_filled_xsrc_in_window`. This library itself inserts nothing, fills
    nothing forward and never goes online.

    FC-A4 (PLAN v0.8 J-15): a frame with a factor / adjusted-price column or
    an adjustflag other than "3" is refused. `data_cutoff` (PLAN v0.8 C-8;
    store.RawStore applies it when reading): if given, a row dated after it
    is refused (CutoffError).
    """
    check_unadjusted(raw, str(raw["code"].iloc[0]) if "code" in raw.columns and len(raw) else "")
    if data_cutoff is not None:
        from engine.datacut import assert_no_row_after
        assert_no_row_after(raw, "date", data_cutoff, "prepare_bars")
    df = raw.copy()
    df["date"] = pd.to_datetime(df["date"])
    n_dup = int(df["date"].duplicated().sum())
    df = df.drop_duplicates("date", keep="first").sort_values("date").set_index("date")
    for c in NUMERIC:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    n_off_cal = int((cal.pos_array(df.index) < 0).sum())
    if n_off_cal:
        df = df.loc[cal.pos_array(df.index) >= 0]
    out = pd.DataFrame(index=df.index)
    for c in ["open", "high", "low", "close", "preclose"]:
        out[c] = df[c].astype(np.float64)
    traded = (df["tradestatus"] == 1) & (df["volume"] > 0)
    out["volume"] = np.where(traded, df["volume"], 0.0)
    out["amount"] = np.where(traded, df["amount"], 0.0)
    out["V"] = np.where(traded, df["turn"] / 100.0, 0.0)
    out["traded"] = traded.values
    out["is_st"] = (df["isST"] == 1).values
    if "filled_from_xsrc" in df.columns:
        out["filled_xsrc"] = df["filled_from_xsrc"].astype(str).str.strip().str.lower().isin(["1", "1.0", "true"]).values
    else:
        out["filled_xsrc"] = False
    out["F"] = own_adjust_factor(out["close"].values, out["preclose"].values)
    out["present"] = True
    # market calendar between first and last row
    if len(out):
        p0, p1 = cal.pos(out.index[0]), cal.pos(out.index[-1])
        full = cal.days[p0:p1 + 1]
        n_missing = len(full) - len(out)
        if n_missing:
            out = out.reindex(full)
            out["present"] = out["present"].eq(True)
            out["traded"] = out["traded"].eq(True)
            out["is_st"] = out["is_st"].eq(True)
            out["filled_xsrc"] = out["filled_xsrc"].eq(True)
    else:
        n_missing = 0
    with np.errstate(all="ignore"):
        for c in ["open", "high", "low", "close"]:
            out["a" + c] = out[c] * out["F"]
        out["avwap"] = np.where(out["volume"] > 0, out["amount"] / out["volume"], np.nan) * out["F"]
        out["avolume"] = out["volume"] / out["F"]
    out["traded"] = out["traded"].astype(bool)
    out["is_st"] = out["is_st"].astype(bool)
    out["present"] = out["present"].astype(bool)
    out["filled_xsrc"] = out["filled_xsrc"].astype(bool)
    out.index.name = "date"
    out.attrs = {"n_duplicate_dates": n_dup, "n_rows_off_calendar": n_off_cal,
                 "n_missing_rows": int(n_missing), "n_filled_xsrc_rows": int(out["filled_xsrc"].sum()),
                 "n_V_gt_1": int((out["V"] > 1).sum()), "n_V_lt_0": int((out["V"] < 0).sum()),
                 "n_traded_V_nan": int((out["traded"] & out["V"].isna()).sum())}
    return out


def prepare_index(raw: pd.DataFrame) -> pd.Series:
    """Daily close-to-preclose return of an index, indexed by date."""
    d = pd.to_datetime(raw["date"])
    c = pd.to_numeric(raw["close"], errors="coerce").values
    p = pd.to_numeric(raw["preclose"], errors="coerce").values
    with np.errstate(all="ignore"):
        r = c / p - 1.0
    s = pd.Series(r, index=pd.DatetimeIndex(d), name="index_ret")
    return s[~s.index.duplicated()].sort_index()

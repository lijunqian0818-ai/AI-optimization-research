"""Generic look-ahead test (audit A11; PLAN 3.1 "truncation test").

For a decision day t the feature row must be a function of G_t only. The test
recomputes the row after everything outside G_t has been destroyed and
requires the result to be identical bit for bit:

  truncate   the pipeline is run on the intact data with cut-off t (tests that the
             cut-off argument is honoured; it cannot catch a function that
             ignores its cut-off -- the checks below do);
  nan        every value dated outside G_t is blanked;
  shuffle    the values outside G_t are permuted among the rows outside G_t;
  noise      the values outside G_t are multiplied by random factors;
  drop       the rows outside G_t are deleted;
  inject     (event tables only) fabricated events of the tested stock are
             added outside G_t.

"Outside G_t": bar and index rows dated >= t; event records under one of two
scopes -- 'calendar' (event day >= t) or 'availability' (event day + lag > t,
i.e. also the records dated before t that the lag rule declares unusable).
The reference is the row computed from the intact data with a cut-off far in
the future.

Comparison: NaN positions must coincide; every non-NaN value must have the
same 64-bit pattern.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import ZO_LAG
from .timing import TradingCalendar
from .zo import ZOTables

BAR_VALUE_COLS = ["open", "high", "low", "close", "preclose", "volume", "amount", "turn", "tradestatus", "pctChg", "isST",
                  "filled_from_xsrc"]     # the repair flag of PLAN 3.11 rule 12, when the raw table carries it
INDEX_VALUE_COLS = ["open", "high", "low", "close", "preclose", "volume", "amount", "pctChg"]
EVENT_DATE_COL = {"lhb": "上榜日", "jg": "上榜日期", "blk": "交易日期", "ins": "NOTICE_DATE"}
EVENT_CODE_COL = {"lhb": "代码", "jg": "代码", "blk": "证券代码", "ins": "SECURITY_CODE"}
EVENT_CLASS = {"lhb": "lhb", "jg": "lhb", "blk": "blk", "ins": "ins"}
MODES = ("nan", "shuffle", "noise", "drop", "inject")


def bitwise_equal(a: pd.Series, b: pd.Series) -> tuple[bool, list[str]]:
    """Compare two feature rows; returns (equal, names of differing columns)."""
    if list(a.index) != list(b.index):
        return False, ["<column sets differ>"]
    x = a.values.astype(np.float64)
    y = b.values.astype(np.float64)
    nx, ny = np.isnan(x), np.isnan(y)
    same = (nx & ny) | (~nx & ~ny & (x.view(np.uint64) == y.view(np.uint64)))
    return bool(same.all()), [str(c) for c in a.index[~same]]


def _corrupt_table(df: pd.DataFrame, mask: np.ndarray, value_cols: list[str], mode: str, rng) -> pd.DataFrame:
    """Destroy `value_cols` on the rows selected by `mask`."""
    if mode == "drop":
        return df.loc[~mask].reset_index(drop=True)
    out = df.copy()
    idx = np.nonzero(mask)[0]
    if len(idx) == 0:
        return out
    for c in value_cols:
        col = out[c].to_numpy(dtype=object, copy=True)
        if mode == "nan":
            is_str = isinstance(col[idx[0]], str) or pd.api.types.is_string_dtype(df[c].dtype)
            col[idx] = "" if is_str else np.nan
        elif mode == "shuffle":
            col[idx] = col[rng.permutation(idx)]
        elif mode == "noise":
            new = []
            for v in col[idx]:
                try:
                    f = float(v)
                    f = f * float(np.exp(rng.normal(0.0, 1.0))) * (-1.0 if rng.random() < 0.2 else 1.0) + rng.normal()
                    new.append(str(f) if isinstance(v, str) else f)
                except (TypeError, ValueError):
                    new.append(v)
            col[idx] = new
        else:
            raise ValueError(mode)
        try:
            out[c] = pd.Series(col, index=out.index).astype(df[c].dtype)
        except (TypeError, ValueError):
            out[c] = pd.Series(col, index=out.index)
    return out


def corrupt_bars(raw: pd.DataFrame, t: pd.Timestamp, mode: str, rng, value_cols=None) -> pd.DataFrame:
    """Destroy every bar / index row dated >= t."""
    mask = (pd.to_datetime(raw["date"]) >= t).values
    cols = [c for c in (value_cols or BAR_VALUE_COLS) if c in raw.columns]
    if mode == "inject":
        mode = "noise"
    return _corrupt_table(raw, mask, cols, mode, rng)


def _event_outside_mask(df, key, cal: TradingCalendar, t: pd.Timestamp, scope: str, lags: dict) -> np.ndarray:
    d = pd.to_datetime(df[EVENT_DATE_COL[key]], errors="coerce")
    if scope == "calendar":
        return (d >= t).values
    if scope == "availability":
        pos = cal.roll_forward_pos(d.fillna(pd.Timestamp("2262-01-01")))
        return pos + lags[EVENT_CLASS[key]] > cal.pos(t)
    raise ValueError(scope)


def corrupt_events(tables: ZOTables, cal: TradingCalendar, t: pd.Timestamp, mode: str, rng, scope: str,
                   code: str, lags: dict | None = None) -> ZOTables:
    """Destroy every event record outside G_t (see module docstring)."""
    lags = dict(ZO_LAG) if lags is None else lags
    new = {}
    c6 = code.split(".")[1]
    for key in ("lhb", "jg", "blk", "ins"):
        df = getattr(tables, key)
        mask = _event_outside_mask(df, key, cal, t, scope, lags)
        date_c, code_c = EVENT_DATE_COL[key], EVENT_CODE_COL[key]
        vcols = [c for c in df.columns if c not in (date_c,)]
        if mode == "inject":
            idx = np.nonzero(mask)[0]
            if len(idx):
                add = df.iloc[rng.choice(idx, size=min(50, len(idx)), replace=True)].copy()
                add[code_c] = c6                                   # fabricated records of the tested stock
                for c in add.columns:
                    if c not in (date_c, code_c) and pd.api.types.is_numeric_dtype(add[c]):
                        add[c] = add[c].astype(float) * 1e3 + 1.0
                df = pd.concat([df, add], ignore_index=True)
            new[key] = df
        elif mode == "shuffle":
            # values AND codes move among the rows outside G_t; dates stay outside G_t
            new[key] = _corrupt_table(df, mask, vcols, "shuffle", rng)
        elif mode in ("nan", "noise"):
            new[key] = _corrupt_table(df, mask, [c for c in vcols if c != code_c], mode, rng)
        elif mode == "drop":
            new[key] = _corrupt_table(df, mask, vcols, "drop", rng)
        else:
            raise ValueError(mode)
    return ZOTables(new["lhb"], new["jg"], new["blk"], new["ins"], tables.coverage)


def check_lookahead(build, code: str, raw_bars: pd.DataFrame, cal: TradingCalendar, decision_days,
                    raw_index: pd.DataFrame | None = None, tables: ZOTables | None = None,
                    far_cutoff=None, modes=MODES, scopes=("calendar", "availability"), seed: int = 0,
                    reference: pd.DataFrame | None = None) -> list[dict]:
    """Run the look-ahead test for one stock.

    build(code, raw_bars, cal, cutoff, raw_index, tables) -> feature frame
    indexed by decision day. Returns one record per (decision day, check).
    """
    rng = np.random.default_rng(seed)
    if far_cutoff is None:
        last = pd.to_datetime(raw_bars["date"]).max()
        far_cutoff = cal.next(last)
    ref = build(code, raw_bars, cal, far_cutoff, raw_index, tables) if reference is None else reference
    records = []
    for t in decision_days:
        t = pd.Timestamp(t)
        if t not in ref.index:
            records.append({"code": code, "decision_day": t, "check": "reference", "equal": False,
                            "n_cols": 0, "n_nonnan": 0, "diff_cols": "decision day not in the frame"})
            continue
        row = ref.loc[t]
        nn = int(row.notna().sum())

        def rec(name, frame):
            if t not in frame.index:
                records.append({"code": code, "decision_day": t, "check": name, "equal": False, "n_cols": len(row),
                                "n_nonnan": nn, "diff_cols": "row missing"})
                return
            eq, diff = bitwise_equal(row, frame.loc[t])
            records.append({"code": code, "decision_day": t, "check": name, "equal": eq, "n_cols": len(row),
                            "n_nonnan": nn, "diff_cols": ";".join(diff[:20])})

        rec("truncate", build(code, raw_bars, cal, t, raw_index, tables))
        for mode in modes:
            cb = corrupt_bars(raw_bars, t, mode, rng)
            ci = None if raw_index is None else corrupt_bars(raw_index, t, mode, rng, INDEX_VALUE_COLS)
            if tables is None:
                rec(mode, build(code, cb, cal, far_cutoff, ci, None))
                continue
            for scope in scopes:
                ct = corrupt_events(tables, cal, t, mode, rng, scope, code)
                rec(f"{mode}/{scope}", build(code, cb, cal, far_cutoff, ci, ct))
    return records

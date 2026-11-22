"""Hard data cut-off of the loaders (PLAN v0.8 section 13A; task list C-8, U-PILOT).

Every loader that opens a raw file (engine: io_baostock; feature library: features/store.py)
takes a data cut-off date and goes through the functions of this module:

  * `read_parquet_cut(path, date_col, cutoff)` reads a per-name table with a row filter
    `date_col <= cutoff` that is applied by pyarrow while the file is read, so that a row
    dated after the cut-off never becomes part of a DataFrame.  The result is checked again
    (`assert_no_row_after`); a row after the cut-off raises CutoffError.
  * `read_events_cut` does the same for an event table with an ex-date and an announcement
    date: a row is kept iff its ex-date is <= cutoff, or it has no ex-date and its
    announcement date is <= cutoff.  Rows without any of the two dates are dropped (they
    cannot be placed in time).  Every other date column that is read and lies after the
    cut-off is set to missing (counted): no fact dated after the cut-off survives.
  * `period_ok(period, cutoff)` decides from a FILE NAME ('YYYYMM' or 'YYYY') whether a
    period file may be opened at all; files of later periods are never opened.

There is no default cut-off: `require_cutoff(None)` raises.  The pilot passes 2021-12-31
explicitly (PILOT_CUTOFF is the documented value, not a default of any loader).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq

PILOT_CUTOFF = date(2021, 12, 31)       # PLAN v0.8 section 13A (the lead's hard constraint)


class CutoffError(ValueError):
    pass


def require_cutoff(cutoff) -> date:
    """The cut-off as a date; None (no cut-off) is refused."""
    if cutoff is None:
        raise CutoffError("a data cut-off date is required (PLAN v0.8 C-8: there is no 'no cut-off' default)")
    if isinstance(cutoff, pd.Timestamp):
        return cutoff.date()
    if isinstance(cutoff, date):
        return cutoff
    return date.fromisoformat(str(cutoff)[:10])


def _scalar_for(field_type: pa.DataType, cutoff: date):
    if pa.types.is_string(field_type) or pa.types.is_large_string(field_type):
        return pa.scalar(cutoff.isoformat(), type=field_type)
    if pa.types.is_date(field_type):
        return pa.scalar(cutoff, type=field_type)
    if pa.types.is_timestamp(field_type):
        # the whole cut-off day is admitted
        return pa.scalar(pd.Timestamp(cutoff) + pd.Timedelta(hours=23, minutes=59, seconds=59), type=field_type)
    raise CutoffError(f"cannot compare a column of type {field_type} with a date")


def _string_le(col: str, cutoff: date) -> ds.Expression:
    # ISO dates compare lexicographically; only the first 10 characters are compared
    return pc.utf8_slice_codeunits(ds.field(col), 0, 10) <= pa.scalar(cutoff.isoformat())


def _le(schema: pa.Schema, col: str, cutoff: date) -> ds.Expression:
    t = schema.field(col).type
    if pa.types.is_null(t):               # an all-null (e.g. empty) column: no row can be placed in time
        return ds.scalar(False)
    if pa.types.is_string(t) or pa.types.is_large_string(t):
        return _string_le(col, cutoff)
    return ds.field(col) <= _scalar_for(t, cutoff)


def _nonempty(schema: pa.Schema, col: str) -> ds.Expression:
    t = schema.field(col).type
    if pa.types.is_null(t):
        return ds.scalar(False)
    e = ~ds.field(col).is_null()
    if pa.types.is_string(t) or pa.types.is_large_string(t):
        e = e & (pc.utf8_length(ds.field(col)) > 0)
    return e


def read_parquet_cut(path, date_col: str, cutoff, columns: Optional[list] = None) -> pd.DataFrame:
    """Rows of `path` with `date_col` <= cutoff (filter applied while reading)."""
    cut = require_cutoff(cutoff)
    p = Path(path)
    schema = pq.read_schema(p)
    if date_col not in schema.names:
        raise CutoffError(f"{p}: no date column {date_col!r}; cannot apply the cut-off")
    tab = ds.dataset(str(p), format="parquet").to_table(columns=columns, filter=_le(schema, date_col, cut))
    df = tab.to_pandas()
    assert_no_row_after(df, date_col, cut, str(p))
    return df


def read_events_cut(path, ex_col, ann_col, cutoff, other_date_cols: Iterable = (), counts: Optional[dict] = None,
                    by_position: bool = False) -> pd.DataFrame:
    """Event table: keep rows with ex-date <= cutoff, or without ex-date and with announcement
    date <= cutoff.  `ex_col` / `ann_col` / `other_date_cols` are column names, or positions
    if `by_position` (the Chinese column names of the vendor tables are addressed by
    position in io_baostock).  Other date columns after the cut-off are set to missing."""
    cut = require_cutoff(cutoff)
    p = Path(path)
    schema = pq.read_schema(p)
    names = schema.names
    name = (lambda c: names[c]) if by_position else (lambda c: c)
    ex, ann = name(ex_col), (name(ann_col) if ann_col is not None else None)
    flt = _nonempty(schema, ex) & _le(schema, ex, cut)
    if ann is not None:
        flt = flt | ((~_nonempty(schema, ex)) & _nonempty(schema, ann) & _le(schema, ann, cut))
    tab = ds.dataset(str(p), format="parquet").to_table(filter=flt)
    df = tab.to_pandas()
    n_nulled = 0
    for c in [ex] + ([ann] if ann else []) + [name(x) for x in other_date_cols]:
        if c not in df.columns or not len(df):
            continue
        d = pd.to_datetime(df[c].astype(str).str.slice(0, 10), errors="coerce")
        late = (d > pd.Timestamp(cut)).to_numpy()
        if late.any():
            if c == ex:
                raise CutoffError(f"{p}: ex-date after the cut-off survived the filter")
            n_nulled += int(late.sum())
            df[c] = df[c].astype(object)
            df.loc[late, c] = None
    if counts is not None:
        counts["event_date_fields_after_cutoff_set_missing"] = counts.get("event_date_fields_after_cutoff_set_missing", 0) + n_nulled
    return df


def assert_no_row_after(df: pd.DataFrame, date_col: str, cutoff, what: str = "") -> None:
    cut = require_cutoff(cutoff)
    if not len(df):
        return
    d = pd.to_datetime(df[date_col].astype(str).str.slice(0, 10), errors="coerce")
    if (d > pd.Timestamp(cut)).any():
        raise CutoffError(f"{what}: a row dated after the data cut-off {cut} reached a loader")


def period_ok(period: str, cutoff) -> bool:
    """File-name period 'YYYYMM' or 'YYYY' -> may the file be opened under the cut-off?"""
    cut = require_cutoff(cutoff)
    s = str(period)
    if len(s) == 6 and s.isdigit():
        return (int(s[:4]), int(s[4:])) <= (cut.year, cut.month)
    if len(s) == 4 and s.isdigit():
        return int(s) <= cut.year
    return False


def clip_date(x, cutoff) -> Optional[date]:
    """A date field read from a snapshot table (e.g. a delisting date): None if after the cut-off."""
    cut = require_cutoff(cutoff)
    if x is None:
        return None
    try:
        d = x if isinstance(x, date) and not isinstance(x, pd.Timestamp) else date.fromisoformat(str(x).strip()[:10])
    except Exception:
        return None
    return d if d <= cut else None


def file_sha256(path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _np_dates(series) -> np.ndarray:
    return pd.to_datetime(pd.Series(series).astype(str).str.slice(0, 10), errors="coerce").to_numpy()

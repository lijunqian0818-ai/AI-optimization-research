"""Read-only access to `experiments/data/raw` (never writes, never fetches).

Vendor tables are read through the whitelist of config.py (audit OA2): the
ex-post fields ("上榜后 N 日", "解读"), snapshot fields ("最新价", "涨跌幅" of
the share-change table) and names are never loaded.

Data cut-off (PLAN v0.8 section 13A; task C-8). `RawStore(root, data_cutoff=...)`
needs an explicit cut-off date; there is no "no cut-off" default. Under it
  * bars, index bars and the calendar are read with a row filter
    date <= cutoff applied while the file is read (engine.datacut);
  * Z_O period files ('YYYYMM' / 'YYYY') of later periods are never opened,
    and the analysis period of every Z_O class ends at the cut-off;
  * snapshot dates of the listing table (delisting, listing) after the
    cut-off are blanked.

No adjustment factor (PLAN v0.8 ruling J-15, task C-6; mirror of the engine's
FC-A4): the vendor factor directory is never opened (`_guard`), and a bar
file with a factor / adjusted-price column or an `adjustflag` other than "3"
is refused (`check_unadjusted`, also called by bars.prepare_bars).
"""
from __future__ import annotations

import glob
import os

import pandas as pd
import pyarrow.parquet as pq

from engine import datacut as dc

from .bars import AdjustedDataError, check_unadjusted   # noqa: F401
from .config import WHITELIST, BLACKLIST
from .timing import TradingCalendar
from .zo import ZOTables

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "raw")

# FC-A4 (mirror of engine/io_baostock.py; PLAN v0.8 J-15): see bars.check_unadjusted
FORBIDDEN_DIRS = ("bs_adjust_factor",)


def _guard(path: str) -> None:
    parts = os.path.normpath(path).split(os.sep)
    if any(p in FORBIDDEN_DIRS for p in parts):
        raise AdjustedDataError(f"the feature library does not read vendor adjustment factors: {path}")


def read_whitelisted(path: str, table: str, date_col: str | None = None, data_cutoff=None) -> pd.DataFrame:
    """Read only the whitelisted columns of a vendor table file (rows <= the cut-off
    if `date_col` and `data_cutoff` are given)."""
    _guard(path)
    cols = WHITELIST[table]
    if set(cols) & set(BLACKLIST[table]):
        raise AssertionError("whitelist and blacklist overlap for " + table)
    have = pq.ParquetFile(path).schema_arrow.names
    missing = [c for c in cols if c not in have]
    if missing:
        raise KeyError(f"{path}: whitelisted columns missing: {missing}")
    if date_col is not None and data_cutoff is not None:
        return dc.read_parquet_cut(path, date_col, data_cutoff, columns=cols)
    return pd.read_parquet(path, columns=cols)


ZO_DATE_COL = {"lhb_detail": "上榜日", "lhb_jgmmtj": "上榜日期", "dzjy_mrmx": "交易日期", "ins_raw": "NOTICE_DATE"}


class RawStore:
    def __init__(self, root: str = RAW, *, data_cutoff):
        self.root = os.path.normpath(root)
        self.data_cutoff = dc.require_cutoff(data_cutoff)
        self.opened: list[str] = []          # every file opened (tests: later Z_O files never appear)

    def _note(self, path: str) -> str:
        _guard(path)
        self.opened.append(os.path.normpath(path))
        return path

    # ---- universe / calendar
    def calendar(self) -> TradingCalendar:
        p = self._note(os.path.join(self.root, "universe", "bs_trade_dates.parquet"))
        d = dc.read_parquet_cut(p, "calendar_date", self.data_cutoff)
        return TradingCalendar(d.loc[d["is_trading_day"].astype(str) == "1", "calendar_date"])

    def stock_basic(self) -> pd.DataFrame:
        b = pd.read_parquet(self._note(os.path.join(self.root, "universe", "bs_stock_basic.parquet")))
        for c in ("ipoDate", "outDate"):
            if c in b.columns:
                b[c] = [("" if dc.clip_date(x, self.data_cutoff) is None else str(x)) if (x is not None and str(x).strip())
                        else "" for x in b[c]]
        return b

    def ipo_date(self, code: str):
        b = self.stock_basic()
        r = b.loc[b["code"] == code, "ipoDate"]
        return pd.Timestamp(r.iloc[0]) if len(r) and r.iloc[0] else None

    # ---- bars
    def bar_codes(self) -> list[str]:
        return sorted(os.path.basename(f)[:-8] for f in glob.glob(os.path.join(self.root, "bars", "bs_daily", "*.parquet")))

    def raw_bars(self, code: str) -> pd.DataFrame:
        p = self._note(os.path.join(self.root, "bars", "bs_daily", code + ".parquet"))
        df = dc.read_parquet_cut(p, "date", self.data_cutoff)
        check_unadjusted(df, code)
        return df

    def raw_index(self, code: str):
        p = os.path.join(self.root, "index", "bs_index_daily", code + ".parquet")
        return dc.read_parquet_cut(self._note(p), "date", self.data_cutoff) if os.path.exists(p) else None

    # ---- Z_O
    def _concat(self, sub: str, table: str):
        files = sorted(f for f in glob.glob(os.path.join(self.root, "zo", sub, "*.parquet"))
                       if os.path.basename(f)[:-8].isdigit())
        # files of periods after the cut-off are never opened (C-8)
        files = [f for f in files if dc.period_ok(os.path.basename(f)[:-8], self.data_cutoff)]
        periods = [os.path.basename(f)[:-8] for f in files]
        frames = [read_whitelisted(self._note(f), table, ZO_DATE_COL[table], self.data_cutoff) for f in files]
        frames = [f for f in frames if len(f)]
        df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=WHITELIST[table])
        return df, set(periods)

    def zo_tables(self) -> ZOTables:
        """Whitelisted Z_O tables with the set of periods whose raw file is
        in the snapshot (periods up to the data cut-off only). Whether a missing
        period is an error is decided by `zo.coverage_array(strict=...)`
        (production default: error, ruling F-14); `check_zo_coverage` runs that
        check once for all classes, over the analysis period ending at the cut-off."""
        lhb, p_lhb = self._concat("lhb_detail", "lhb_detail")
        jg, p_jg = self._concat("lhb_jgmmtj", "lhb_jgmmtj")
        blk, p_blk = self._concat("dzjy_mrmx", "dzjy_mrmx")
        ins, p_ins = self._concat("ins_raw", "ins_raw")
        return ZOTables(lhb, jg, blk, ins, {"lhb": p_lhb, "jg": p_jg, "blk": p_blk, "ins": p_ins},
                        data_cutoff=pd.Timestamp(self.data_cutoff))

    def check_zo_coverage(self, tables: ZOTables | None = None, strict: bool = True) -> dict:
        """Run the strict coverage check of every class against the calendar
        (raises zo.MissingRawFile on a missing file inside the analysis
        period when strict). Returns the number of covered trading days."""
        from . import zo
        tables = self.zo_tables() if tables is None else tables
        cal = self.calendar()
        end = tables.analysis_end()
        return {k: int(zo.coverage_array(cal, cls, tables.coverage.get(k, ()), strict=strict, end=end).sum())
                for k, cls in (("lhb", "lhb"), ("jg", "lhb"), ("blk", "blk"), ("ins", "ins"))}

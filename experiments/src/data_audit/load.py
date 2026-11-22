"""Loaders for the cached raw pulls (read-only; raw cache files are never modified)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from harness import CACHE, LOGS, OUT, _key, bs_code, sina_code

S, E = "20080101", "20261113"
BS_FIELDS = "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST"


def _get(name, *args, **kwargs):
    base = CACHE / _key(name, args, kwargs)
    p = Path(str(base) + ".parquet")
    if p.exists():
        return pd.read_parquet(p)
    c = Path(str(base) + ".csv")
    if c.exists():
        return pd.read_csv(c, dtype=str)
    return None


def sample() -> pd.DataFrame:
    return pd.read_csv(OUT / "sample_list.csv", dtype=str)


def calendar() -> pd.DatetimeIndex:
    c = _get("bs_query_trade_dates", start_date="2008-01-01", end_date="2026-11-13")
    return pd.DatetimeIndex(pd.to_datetime(c[c.is_trading_day == "1"].calendar_date))


def bs_raw(code):
    d = _get("bs_query_history_k_data_plus", bs_code(code), BS_FIELDS, start_date="2008-01-01", end_date="2026-11-13",
             frequency="d", adjustflag="3")
    if d is None or d.empty:
        return d
    d = d.copy()
    d["date"] = pd.to_datetime(d["date"])
    for c in ["open", "high", "low", "close", "preclose", "volume", "amount", "turn", "pctChg"]:
        d[c + "_blank"] = d[c].astype(str).str.strip() == ""
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["tradestatus"] = pd.to_numeric(d["tradestatus"], errors="coerce")
    d["isST"] = pd.to_numeric(d["isST"], errors="coerce")
    return d.set_index("date")


def bs_hfq(code):
    d = _get("bs_query_history_k_data_plus", bs_code(code), "date,code,open,high,low,close,preclose",
             start_date="2008-01-01", end_date="2026-11-13", frequency="d", adjustflag="1")
    if d is None or d.empty:
        return d
    d = d.copy()
    d["date"] = pd.to_datetime(d["date"])
    for c in ["open", "high", "low", "close", "preclose"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.set_index("date")


def bs_factor(code):
    d = _get("bs_query_adjust_factor", bs_code(code), start_date="2008-01-01", end_date="2026-11-13")
    if d is None or d.empty:
        return d
    d = d.copy()
    d["dividOperateDate"] = pd.to_datetime(d["dividOperateDate"])
    for c in ["foreAdjustFactor", "backAdjustFactor", "adjustFactor"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d


def em(code, adjust=""):
    d = _get("stock_zh_a_hist_em", code, "daily", S, E, adjust)
    if d is None or d.empty:
        return d
    d = d.rename(columns={"日期": "date", "开盘": "open", "收盘": "close", "最高": "high", "最低": "low", "成交量": "volume",
                          "成交额": "amount", "振幅": "amp", "涨跌幅": "pct", "涨跌额": "chg", "换手率": "turn"}).copy()
    d["date"] = pd.to_datetime(d["date"])
    for c in ["open", "close", "high", "low", "volume", "amount", "pct", "chg", "turn"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.set_index("date")


def sina(code):
    d = _get("stock_zh_a_daily_sina", sina_code(code), S, E, "")
    if d is None or d.empty:
        return d
    d = d.copy()
    d["date"] = pd.to_datetime(d["date"])
    for c in d.columns:
        if c != "date":
            d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.set_index("date")


def sina_factor(code):
    d = _get("stock_zh_a_daily_sina", sina_code(code), S, E, "hfq-factor")
    if d is None or d.empty:
        return d
    d = d.copy()
    d["date"] = pd.to_datetime(d["date"])
    d["hfq_factor"] = pd.to_numeric(d["hfq_factor"], errors="coerce")
    return d.sort_values("date")


def tx(code):
    d = _get("stock_zh_a_hist_tx", sina_code(code), "20190101", "20201231", "")
    if d is None or d.empty:
        return d
    d = d.copy()
    d["date"] = pd.to_datetime(d["date"])
    return d.set_index("date")


def fhps(code):
    d = _get("stock_fhps_detail_em", code)
    if d is None or d.empty:
        return d
    d = d.copy()
    for c in ["报告期", "业绩披露日期", "预案公告日", "股权登记日", "除权除息日", "最新公告日期"]:
        d[c] = pd.to_datetime(d[c], errors="coerce")
    for c in ["送转股份-送转总比例", "送转股份-送股比例", "送转股份-转股比例", "现金分红-现金分红比例"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d


def sina_div(code, kind="分红"):
    d = _get("stock_history_dividend_detail", code, kind, "")
    if d is None or d.empty:
        return d
    d = d.copy()
    for c in d.columns:
        if "日" in c:
            d[c] = pd.to_datetime(d[c], errors="coerce")
    return d


def call_log() -> pd.DataFrame:
    rows = [json.loads(x) for x in (LOGS / "call_log.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    return pd.DataFrame(rows)


def board(code: str) -> str:
    if code.startswith("688") or code.startswith("689"):
        return "star"
    if code.startswith("30"):
        return "chinext"
    return "main"


def round_half_up(x, nd=2):
    """Round half up to `nd` decimals, robust to binary representation (x is price * (1 +/- band))."""
    return np.floor(np.asarray(x, dtype=float) * 10 ** nd + 0.5 + 1e-9) / 10 ** nd

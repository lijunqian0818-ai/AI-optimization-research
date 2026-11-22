"""Synthetic inputs in the vendors' raw schemas (no real data, no outcomes).

The generator plants the awkward cases the audit found in real data:
suspension spells with empty volume strings, ex-dates (preclose != previous
close), a turnover above 100%, an ST spell, limit-up closes, a missing row.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from features.timing import TradingCalendar
from features.zo import ZOTables


def make_calendar(start="2012-01-02", n=1500) -> TradingCalendar:
    days = pd.bdate_range(start, periods=n + 400)
    # remove a few weekdays to imitate holidays
    rng = np.random.default_rng(12345)
    drop = rng.choice(len(days), size=40, replace=False)
    keep = np.ones(len(days), dtype=bool)
    keep[drop] = False
    return TradingCalendar(days[keep][:n + 300])


def make_raw_bars(code: str, cal: TradingCalendar, seed: int = 0, n_rows: int = 1200, start_pos: int = 5,
                  missing_row: int | None = None, long_suspension: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = cal.days[start_pos:start_pos + n_rows]
    close = np.empty(n_rows)
    pre = np.empty(n_rows)
    op = np.empty(n_rows); hi = np.empty(n_rows); lo = np.empty(n_rows)
    vol = np.empty(n_rows); amt = np.empty(n_rows); turn = np.empty(n_rows)
    status = np.ones(n_rows, dtype=int); st = np.zeros(n_rows, dtype=int)
    susp = np.zeros(n_rows, dtype=bool)
    for a in rng.choice(np.arange(50, n_rows - 30), size=6, replace=False):
        susp[a:a + int(rng.integers(1, 12))] = True
    if long_suspension:
        susp[600:600 + 130] = True
    exdates = set(rng.choice(np.arange(20, n_rows - 5), size=8, replace=False).tolist())
    st[300:380] = 1
    float_shares = 5e8
    prev_close = 10.0
    for i in range(n_rows):
        ref = prev_close
        if i in exdates:
            ref = round(prev_close * (0.5 if rng.random() < 0.3 else float(rng.uniform(0.95, 0.995))), 2)
            if ref != prev_close and rng.random() < 0.3:
                float_shares *= prev_close / ref
        pre[i] = ref
        if susp[i]:
            op[i] = hi[i] = lo[i] = close[i] = ref
            vol[i] = amt[i] = turn[i] = np.nan
            status[i] = 0
        else:
            band = 0.05 if st[i] else 0.10
            r = float(np.clip(rng.normal(0.0003, 0.025), -band, band))
            if rng.random() < 0.02:
                r = band
            c = round(ref * (1 + r), 2)
            o = round(ref * (1 + float(np.clip(rng.normal(0, 0.01), -band, band))), 2)
            h = round(max(o, c) * (1 + abs(rng.normal(0, 0.006))), 2)
            l = round(min(o, c) * (1 - abs(rng.normal(0, 0.006))), 2)
            if rng.random() < 0.01:            # one-price day
                o = h = l = c
            tr = float(np.exp(rng.normal(np.log(1.5), 0.8)))
            if i == 450:
                tr = 130.0                      # turnover above 100% (percent units)
            v = round(float_shares * tr / 100.0)
            op[i], hi[i], lo[i], close[i] = o, h, l, c
            vol[i], turn[i] = v, tr
            amt[i] = v * (o + h + l + c) / 4
        prev_close = close[i]

    def fmt(x, nd):
        return ["" if not np.isfinite(v) else f"{v:.{nd}f}" for v in x]
    raw = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"), "code": code,
        "open": fmt(op, 4), "high": fmt(hi, 4), "low": fmt(lo, 4), "close": fmt(close, 4), "preclose": fmt(pre, 4),
        "volume": ["" if not np.isfinite(v) else str(int(v)) for v in vol], "amount": fmt(amt, 4),
        "adjustflag": "3", "turn": fmt(turn, 6), "tradestatus": status.astype(str),
        "pctChg": fmt((close / pre - 1) * 100, 6), "isST": st.astype(str),
    })
    if missing_row is not None:
        raw = raw.drop(index=missing_row).reset_index(drop=True)
    return raw


def make_raw_index(cal: TradingCalendar, seed: int = 99, code: str = "sh.000001") -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(cal)
    r = rng.normal(0.0002, 0.012, n)
    close = 3000 * np.cumprod(1 + r)
    pre = np.r_[3000.0, close[:-1]]
    return pd.DataFrame({"date": cal.days.strftime("%Y-%m-%d"), "code": code,
                         "open": [f"{x:.4f}" for x in pre], "high": [f"{x:.4f}" for x in np.maximum(pre, close)],
                         "low": [f"{x:.4f}" for x in np.minimum(pre, close)], "close": [f"{x:.4f}" for x in close],
                         "preclose": [f"{x:.4f}" for x in pre], "volume": "1000", "amount": "1000.0",
                         "pctChg": [f"{x:.6f}" for x in r * 100]})


REASONS_SINGLE = ["日涨幅偏离值达到7%的前五只证券", "日换手率达到20%的前五只证券", "日跌幅偏离值达到7%的前三只证券"]
REASONS_MULTI = ["连续三个交易日内，涨幅偏离值累计达到20%的证券"]


def make_zo_tables(codes: list[str], cal: TradingCalendar, seed: int = 0, n_per_code: int = 60,
                   first_pos: int = 10, last_pos: int | None = None) -> ZOTables:
    """Event tables with the whitelisted vendor columns. Coverage = every
    month / year of the calendar."""
    rng = np.random.default_rng(seed)
    last_pos = len(cal) - 5 if last_pos is None else last_pos
    lhb, jg, blk, ins = [], [], [], []
    for code in codes:
        c6 = code.split(".")[1]
        for p in rng.choice(np.arange(first_pos, last_pos), size=n_per_code, replace=False):
            d = cal.days[p].date()
            k = int(rng.integers(1, 3))
            for j in range(k):
                buy, sell = rng.uniform(1e6, 5e7, 2)
                reason = REASONS_SINGLE[int(rng.integers(0, 3))] if j == 0 else REASONS_MULTI[0]
                lhb.append({"代码": c6, "上榜日": d, "龙虎榜净买额": buy - sell, "龙虎榜买入额": buy, "龙虎榜卖出额": sell,
                            "龙虎榜成交额": buy + sell, "市场总成交额": int(5e8), "净买额占总成交比": (buy - sell) / 5e6,
                            "成交额占总成交比": (buy + sell) / 5e6, "上榜原因": reason})
                if rng.random() < 0.5:
                    ib, isell = rng.uniform(0, 2e7, 2)
                    jg.append({"代码": c6, "上榜日期": d, "买方机构数": int(rng.integers(0, 4)),
                               "卖方机构数": int(rng.integers(0, 4)), "机构买入总额": ib, "机构卖出总额": isell,
                               "机构买入净额": ib - isell, "上榜原因": reason})
        for p in rng.choice(np.arange(first_pos, last_pos), size=n_per_code, replace=False):
            d = cal.days[p].date()
            for _ in range(int(rng.integers(1, 4))):
                price = float(rng.uniform(5, 20)); q = int(rng.integers(3e5, 5e6))
                blk.append({"证券代码": c6, "交易日期": d, "成交价": price, "折溢率": float(rng.uniform(-0.12, 0.03)),
                            "成交量": q, "成交额": int(price * q), "成交额/流通市值": float(rng.uniform(0.001, 0.5))})
        for p in rng.choice(np.arange(first_pos, last_pos), size=n_per_code, replace=False):
            nd = cal.days[p] + pd.Timedelta(days=int(rng.integers(0, 3)))      # some fall on non-trading days
            end = nd - pd.Timedelta(days=int(rng.integers(0, 20)))
            ins.append({"SECURITY_CODE": c6, "NOTICE_DATE": nd.strftime("%Y-%m-%d 00:00:00"),
                        "DIRECTION": "增持" if rng.random() < 0.4 else "减持", "CHANGE_NUM": float(rng.uniform(1, 500)),
                        "AFTER_CHANGE_RATE": float(rng.uniform(0, 1)), "CHANGE_FREE_RATIO": float(rng.uniform(0, 2)),
                        "START_DATE": (end - pd.Timedelta(days=5)).strftime("%Y-%m-%d 00:00:00"),
                        "END_DATE": end.strftime("%Y-%m-%d 00:00:00"),
                        "EITIME": (nd + pd.Timedelta(days=int(rng.integers(-1, 900)))).strftime("%Y-%m-%d %H:%M:%S")})
    months = set(cal.days.strftime("%Y%m"))
    years = set(cal.days.strftime("%Y"))
    return ZOTables(pd.DataFrame(lhb), pd.DataFrame(jg), pd.DataFrame(blk), pd.DataFrame(ins),
                    {"lhb": months, "jg": months, "blk": months, "ins": years})


def write_raw_store(root: str, codes: list[str], cal: TradingCalendar, n_rows: int = 700, seed: int = 0,
                    drop_zo_period: tuple | None = None, missing_row: dict | None = None,
                    n_per_code: int = 40) -> dict:
    """Write a synthetic raw-data tree in the on-disk layout that
    `store.RawStore` reads (universe / bars / index / zo), into a temporary
    directory -- never into experiments/data/raw. The Z_O files carry the
    whitelisted columns plus blacklisted ones, as the vendor files do.
    `drop_zo_period` = (sub-directory, period) leaves one file out.
    Returns {code: raw bar frame}."""
    import os
    for sub in ("universe", "bars/bs_daily", "index/bs_index_daily", "zo/lhb_detail", "zo/lhb_jgmmtj",
                "zo/dzjy_mrmx", "zo/ins_raw"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    all_days = pd.date_range(cal.days[0], cal.days[-1], freq="D")
    td = pd.DataFrame({"calendar_date": all_days.strftime("%Y-%m-%d"),
                       "is_trading_day": np.where(all_days.isin(cal.days), "1", "0")})
    td.to_parquet(os.path.join(root, "universe", "bs_trade_dates.parquet"))
    raws = {}
    basic = []
    for k, code in enumerate(codes):
        raw = make_raw_bars(code, cal, seed=seed + k, n_rows=n_rows, missing_row=(missing_row or {}).get(code))
        raw.to_parquet(os.path.join(root, "bars", "bs_daily", code + ".parquet"))
        raws[code] = raw
        basic.append({"code": code, "ipoDate": raw["date"].iloc[0] if k % 2 == 0 else "2001-01-02"})
    pd.DataFrame(basic).to_parquet(os.path.join(root, "universe", "bs_stock_basic.parquet"))
    for idx in ("sh.000001", "sz.399001", "sz.399006"):
        make_raw_index(cal, code=idx).to_parquet(os.path.join(root, "index", "bs_index_daily", idx + ".parquet"))
    tb = make_zo_tables(codes, cal, seed=seed + 50, n_per_code=n_per_code, last_pos=5 + n_rows - 10)
    extra = {"lhb_detail": {"名称": "x", "解读": "y", "上榜后1日": 1.0},
             "lhb_jgmmtj": {"名称": "x"}, "dzjy_mrmx": {"证券简称": "x", "买方营业部": "a", "卖方营业部": "b"},
             "ins_raw": {"NEWEST_PRICE": 1.0, "CHANGE_RATE_QUOTES": 0.1, "HOLDER_NAME": "z"}}
    months = sorted(set(cal.days.strftime("%Y%m")))
    years = sorted(set(cal.days.strftime("%Y")))
    for sub, df, col, periods, fmt in (("lhb_detail", tb.lhb, "上榜日", months, "%Y%m"),
                                       ("lhb_jgmmtj", tb.jg, "上榜日期", months, "%Y%m"),
                                       ("dzjy_mrmx", tb.blk, "交易日期", months, "%Y%m"),
                                       ("ins_raw", tb.ins, "NOTICE_DATE", years, "%Y")):
        df = df.assign(**extra[sub])
        key = pd.to_datetime(df[col]).dt.strftime(fmt)
        for per in sorted(set(periods) | set(key)):
            if drop_zo_period == (sub, per):
                continue
            df[key == per].reset_index(drop=True).to_parquet(os.path.join(root, "zo", sub, per + ".parquet"))
    return raws

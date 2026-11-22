"""Unit builders for the six stages. Each unit = one file under experiments/data/raw/.

Nothing here cleans, merges or computes features. The only derived file is the work list
`universe/a_share_worklist.csv` (a filter of BaoStock's basic table by security type, code prefix and dates),
which the other stages need in order to know what to request.
"""
from __future__ import annotations

import calendar
import json

import pandas as pd

from core import BS, NoData, PermanentError, Http, Unit, RAW, OUT, log

# ---- PLAN 2.1: fields of the unadjusted daily bar (same 14 fields as the smoke test)
BS_BAR_FIELDS = "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST"
BS_INDEX_FIELDS = "date,code,open,high,low,close,preclose,volume,amount,pctChg"
# index bars: descriptive use only (PLAN 2.3 item 3; 11 "market state"); the plan names no list, this one is ours
INDEX_CODES = ["sh.000001", "sh.000300", "sh.000905", "sh.000852", "sh.000985", "sh.000016", "sz.399001", "sz.399006"]

# A-share code prefixes (no B-shares, no Beijing Stock Exchange): PLAN 2.3
BOARD = {"sh.600": "sse_main", "sh.601": "sse_main", "sh.603": "sse_main", "sh.605": "sse_main",
         "sh.688": "star", "sh.689": "star",
         "sz.000": "szse_main", "sz.001": "szse_main", "sz.002": "szse_main(sme_until_2021)", "sz.003": "szse_main",
         "sz.300": "chinext", "sz.301": "chinext", "sz.302": "chinext(prefix_302_unverified)"}

EM_EMPTY_MARKS = ('"result":null', "返回数据为空", '"code":9201')


def code6(c: str) -> str:
    return c.split(".")[-1]


def to_bs(c: str) -> str:
    c = c.strip()
    if "." in c:
        return c.lower()
    return ("sh." if c.startswith(("6", "9")) else "sz.") + c


def sina_symbol(c: str) -> str:
    return to_bs(c).replace(".", "")


def em_guard(fn, *a, **k):
    """AKShare raises TypeError / KeyError when Eastmoney's data centre answers 'no data'. That is 'no record'
    only if the last HTTP answer was a 200 carrying Eastmoney's empty-result marker; otherwise it is an error."""
    try:
        return fn(*a, **k)
    except (TypeError, KeyError, IndexError, ValueError) as e:
        lr = Http.last_resp or {}
        head = str(lr.get("head", ""))
        if lr.get("status") == 200 and any(m in head for m in EM_EMPTY_MARKS):
            raise NoData(f"upstream empty-result answer: {head[:120]}") from e
        raise


# ------------------------------------------------------------------ universe
def universe_units(a) -> list:
    import akshare as ak
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    return [
        Unit("universe", "bs_stock_basic", "all", "universe/bs_stock_basic.parquet",
             lambda: BS.query("query_stock_basic"), {"method": "query_stock_basic"}, ("ipoDate",)),
        Unit("universe", "bs_trade_dates", "all", "universe/bs_trade_dates.parquet",
             lambda: BS.query("query_trade_dates", start_date="2005-01-01", end_date=today),
             {"start": "2005-01-01", "end": today}, ("calendar_date",)),
        Unit("universe", "bs_stock_industry", "all", "universe/bs_stock_industry.parquet",
             lambda: BS.query("query_stock_industry"), {"method": "query_stock_industry"}, ("updateDate",)),
        Unit("universe", "sse_delist", "all", "universe/sse_delist.parquet",
             lambda: ak.stock_info_sh_delist("全部"), {"fn": "stock_info_sh_delist", "symbol": "全部"}, (), host="sse"),
        Unit("universe", "szse_delist", "all", "universe/szse_delist.parquet",
             lambda: ak.stock_info_sz_delist("终止上市公司"), {"fn": "stock_info_sz_delist", "symbol": "终止上市公司"},
             (), host="szse"),
    ]


def build_worklist(start: str, end: str) -> dict:
    """Filter BaoStock's basic table to A-shares listed at any time in [start, end]; write the work list and a summary."""
    p = RAW / "universe" / "bs_stock_basic.parquet"
    if not p.exists():
        raise FileNotFoundError("universe/bs_stock_basic.parquet missing: run --stage universe first")
    b = pd.read_parquet(p).astype(str)
    b["prefix"] = b["code"].str[:6]
    a = b[(b["type"] == "1") & b["prefix"].isin(BOARD)].copy()
    a["board"] = a["prefix"].map(BOARD)
    a["exchange"] = a["code"].str[:2]
    n_a_all = len(a)
    keep = (a["ipoDate"] <= end) & ((a["outDate"] == "") | (a["outDate"] >= start))
    w = a[keep].sort_values("code")[["code", "code_name", "ipoDate", "outDate", "status", "board", "exchange"]]
    (RAW / "universe").mkdir(parents=True, exist_ok=True)
    w.to_csv(RAW / "universe" / "a_share_worklist.csv", index=False, encoding="utf-8-sig")
    summ = {"built_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), "start": start, "end": end,
            "bs_basic_rows": int(len(b)), "bs_basic_by_type": b["type"].value_counts().to_dict(),
            "type1_rows": int((b["type"] == "1").sum()),
            "type1_other_prefix": b[(b["type"] == "1") & ~b["prefix"].isin(BOARD)]["prefix"].value_counts().to_dict(),
            "a_shares_in_basic_table": int(n_a_all),
            "excluded_delisted_before_start": int(((a["outDate"] != "") & (a["outDate"] < start)).sum()),
            "excluded_listed_after_end": int((a["ipoDate"] > end).sum()),
            "worklist_n": int(len(w)),
            "worklist_delisted_by_end": int(((w["outDate"] != "") & (w["outDate"] <= end)).sum()),
            "worklist_outdate_nonempty": int((w["outDate"] != "").sum()),
            "worklist_by_board": w["board"].value_counts().to_dict(),
            "worklist_by_exchange": w["exchange"].value_counts().to_dict()}
    # completeness against the exchanges' own termination lists (first column = code, last column = date)
    miss = {}
    for name in ("sse_delist", "szse_delist"):
        q = RAW / "universe" / f"{name}.parquet"
        if not q.exists():
            miss[name] = "list not fetched"
            continue
        d = pd.read_parquet(q).astype(str)
        codes = d.iloc[:, 0].str.zfill(6)
        dates = d.iloc[:, -1].str[:10]
        ex = "sh." if name.startswith("sse") else "sz."
        full = ex + codes
        is_a = full.str[:6].isin(BOARD)
        in_window = is_a & (dates >= start)
        absent = sorted(set(full[in_window]) - set(a["code"]))
        miss[name] = {"rows": int(len(d)), "a_share_rows": int(is_a.sum()),
                      "a_share_terminated_since_start": int(in_window.sum()),
                      "of_those_absent_from_bs_basic": absent,
                      "of_those_in_worklist": int(full[in_window].isin(w["code"]).sum())}
    summ["exchange_delist_lists"] = miss
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "universe_summary.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"[universe] work list: {len(w)} A-shares listed at any time in [{start}, {end}] -> universe/a_share_worklist.csv")
    return summ


def load_codes(a) -> pd.DataFrame:
    """Work list (optionally restricted by --codes-file), first --limit rows."""
    p = RAW / "universe" / "a_share_worklist.csv"
    if not p.exists():
        raise FileNotFoundError("universe/a_share_worklist.csv missing: run --stage universe first")
    w = pd.read_csv(p, dtype=str, keep_default_na=False)
    if a.codes_file:
        want = []
        for line in open(a.codes_file, encoding="utf-8-sig"):
            line = line.split("#")[0].strip()          # '#' starts a comment
            if line:
                want.append(to_bs(line.split()[0]))
        bad = [c for c in want if len(c) != 9 or c[:3] not in ("sh.", "sz.") or not c[3:].isdigit()]
        if bad:
            raise SystemExit(f"--codes-file: not security codes: {bad[:5]}")
        known = w.set_index("code")
        rows = []
        for c in want:
            if c in known.index:
                r = known.loc[c].to_dict()
                r["code"] = c
            else:
                r = {"code": c, "code_name": "", "ipoDate": "", "outDate": "", "status": "", "board": "", "exchange": c[:2]}
                log(f"[warn] {c} from --codes-file is not in the work list; requested with the full date range")
            rows.append(r)
        w = pd.DataFrame(rows)
    if a.limit:
        w = w.head(a.limit)
    return w.reset_index(drop=True)


# ------------------------------------------------------------------ bars
def bars_units(a) -> list:
    out = []
    for c in load_codes(a)["code"]:
        out.append(Unit("bars", "bs_daily", c, f"bars/bs_daily/{c}.parquet",
                        (lambda c=c: BS.query("query_history_k_data_plus", c, BS_BAR_FIELDS, start_date=a.start,
                                              end_date=a.end, frequency="d", adjustflag="3")),
                        {"fields": BS_BAR_FIELDS, "start": a.start, "end": a.end, "frequency": "d", "adjustflag": "3"},
                        ("date",)))
    return out


# ------------------------------------------------------------------ factors and events (four sources, stored apart)
def _bs_dividend(code, years):
    frames, per_year = [], {}
    for y in years:
        d = BS.query("query_dividend_data", code=code, year=str(y), yearType="operate")
        per_year[str(y)] = int(len(d))
        frames.append(d)
    df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return df, {"rows_per_year": per_year, "yearType": "operate"}


def factors_events_units(a) -> list:
    import akshare as ak
    w = load_codes(a)
    y0, y1 = int(a.start[:4]), int(a.end[:4])
    if a.div_years:
        y0, y1 = (int(x) for x in a.div_years.split(":"))
    src = a.sources
    out = []
    if "bs_factor" in src:
        for c in w["code"]:
            out.append(Unit("factors_events", "bs_factor", c, f"factors_events/bs_adjust_factor/{c}.parquet",
                            (lambda c=c: BS.query("query_adjust_factor", code=c, start_date=a.start, end_date=a.end)),
                            {"start": a.start, "end": a.end}, ("dividOperateDate",)))
    if "bs_dividend" in src:
        for _, r in w.iterrows():
            c = r["code"]
            lo = max(y0, int(r["ipoDate"][:4])) if r["ipoDate"] else y0
            hi = min(y1, int(r["outDate"][:4])) if r["outDate"] else y1
            years = list(range(lo, hi + 1))
            out.append(Unit("factors_events", "bs_dividend", c, f"factors_events/bs_dividend/{c}.parquet",
                            (lambda c=c, years=years: _bs_dividend(c, years)),
                            {"years": [lo, hi], "yearType": "operate"}, ("dividOperateDate",)))
    if "em_fhps" in src:
        for c in w["code"]:
            s = code6(c)
            out.append(Unit("factors_events", "em_fhps", c, f"factors_events/em_fhps/{c}.parquet",
                            (lambda s=s: em_guard(ak.stock_fhps_detail_em, s)),
                            {"fn": "stock_fhps_detail_em"}, ("除权除息日",), host="eastmoney"))
    for c in w["code"]:     # the two Sina tables come from one page: fetched once per name (memo group)
        s = code6(c)
        if "sina_dividend" in src:
            out.append(Unit("factors_events", "sina_dividend", c, f"factors_events/sina_dividend/{c}.parquet",
                            (lambda s=s: ak.stock_history_dividend_detail(s, "分红", "")),
                            {"fn": "stock_history_dividend_detail", "indicator": "分红"}, ("除权除息日",),
                            host="sina", memo_group="sina_bonus_" + s))
        if "sina_rights" in src:
            out.append(Unit("factors_events", "sina_rights", c, f"factors_events/sina_rights/{c}.parquet",
                            (lambda s=s: ak.stock_history_dividend_detail(s, "配股", "")),
                            {"fn": "stock_history_dividend_detail", "indicator": "配股"}, ("除权日",),
                            host="sina", memo_group="sina_bonus_" + s))
    return out


# ------------------------------------------------------------------ index
def _spread(items: list, n: int) -> list:
    """n evenly spaced items (first and last included): trial runs of date-keyed sources."""
    if not n or n >= len(items):
        return items
    if n == 1:
        return [items[len(items) // 2]]
    idx = sorted({round(i * (len(items) - 1) / (n - 1)) for i in range(n)})
    return [items[i] for i in idx]


def weekly_dates(start: str, end: str) -> list:
    p = RAW / "universe" / "bs_trade_dates.parquet"
    if not p.exists():
        raise FileNotFoundError("universe/bs_trade_dates.parquet missing: run --stage universe first")
    cal = pd.read_parquet(p).astype(str)
    d = cal[(cal["is_trading_day"] == "1") & (cal["calendar_date"] >= start) & (cal["calendar_date"] <= end)]["calendar_date"]
    iso = pd.to_datetime(d).dt.isocalendar()
    wk = iso["year"].astype(str) + "-" + iso["week"].astype(str)
    return d.groupby(wk.values).max().sort_values().tolist()      # last trading day of each ISO week


def index_units(a) -> list:
    src = a.sources
    out = []
    if "bs_index_daily" in src:
        for c in INDEX_CODES:
            out.append(Unit("index", "bs_index_daily", c, f"index/bs_index_daily/{c}.parquet",
                            (lambda c=c: BS.query("query_history_k_data_plus", c, BS_INDEX_FIELDS, start_date=a.start,
                                                  end_date=a.end, frequency="d", adjustflag="3")),
                            {"fields": BS_INDEX_FIELDS, "start": a.start, "end": a.end}, ("date",)))
    dates = _spread(weekly_dates(a.start, a.end), a.limit)
    for name, method in (("bs_hs300", "query_hs300_stocks"), ("bs_zz500", "query_zz500_stocks")):
        if name in src:
            for d in dates:
                out.append(Unit("index", name, d, f"index/{name}/{d}.parquet",
                                (lambda d=d, method=method: BS.query(method, date=d)),
                                {"method": method, "date": d}, ("updateDate",)))
    return out


# ------------------------------------------------------------------ cross-check bars (Sina, via AKShare)
def _sina_daily(sym, s, e):
    import akshare as ak
    try:
        return ak.stock_zh_a_daily_sina(sym, s, e, "")
    except Exception as ex:
        if type(ex).__name__ == "InvalidParameterError":      # AKShare: Sina answered 404 for this symbol
            raise NoData(f"sina has no history for {sym}: {str(ex)[:100]}") from ex
        raise


def crosscheck_units(a) -> list:
    if not a.codes_file and not a.limit and not a.all_names:
        raise SystemExit("crosscheck: PLAN 2.1 restricts the Sina cross-check to names that are ever in the universe. "
                         "Pass --codes-file <list> (or --limit N for a trial; --all-names to override).")
    s, e = a.start.replace("-", ""), a.end.replace("-", "")
    out = []
    for c in load_codes(a)["code"]:
        sym = sina_symbol(c)
        out.append(Unit("crosscheck", "sina_daily", c, f"crosscheck/sina_daily/{c}.parquet",
                        (lambda sym=sym: _sina_daily(sym, s, e)),
                        {"fn": "stock_zh_a_daily_sina", "start": s, "end": e, "adjust": ""}, ("date",), host="sina"))
    return out


# ------------------------------------------------------------------ Z_O
EM_DC = "https://datacenter-web.eastmoney.com/api/data/v1/get"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}


def _em_ins(flt: str, page_size: int = 500, only_count: bool = False):
    """Executed share changes, straight from the upstream table that AKShare's stock_ggcg_em reads
    (RPT_SHARE_HOLDER_INCREASE, all columns, same sort), one NOTICE_DATE window at a time so that the pull is resumable.
    The row count is checked against the count the upstream reports."""
    import requests
    params = {"sortColumns": "END_DATE,SECURITY_CODE,EITIME", "sortTypes": "-1,-1,-1", "pageSize": 1 if only_count else page_size,
              "pageNumber": 1, "reportName": "RPT_SHARE_HOLDER_INCREASE", "columns": "ALL", "source": "WEB", "client": "WEB",
              "filter": flt}
    frames, count, pages, page = [], None, 1, 1
    while page <= pages:
        params["pageNumber"] = page
        r = requests.get(EM_DC, params=params, headers=UA, timeout=30)
        r.raise_for_status()
        j = r.json()
        if not j.get("result"):
            if page == 1 and any(m in r.text[:300] for m in EM_EMPTY_MARKS):
                raise NoData(f"upstream empty-result answer: {r.text[:120]}")
            raise ConnectionError(f"eastmoney datacenter: no result on page {page}: {r.text[:160]}")
        count, pages = int(j["result"]["count"]), int(j["result"]["pages"])
        frames.append(pd.DataFrame(j["result"]["data"]))
        if only_count:
            break
        page += 1
    df = pd.concat(frames, ignore_index=True)
    if not only_count and len(df) != count:
        raise ConnectionError(f"row count {len(df)} differs from upstream count {count}")
    extra = {"upstream_count": count, "pages": pages, "filter": flt}
    if only_count:
        df = pd.DataFrame({"upstream_count": [count], "filter": [flt]})
    return df, extra


def _months(start: str, end: str) -> list:
    out = []
    y, m = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    while (y, m) <= (ey, em):
        a = f"{y}{m:02d}01" if (y, m) != (int(start[:4]), int(start[5:7])) else start.replace("-", "")
        b = f"{y}{m:02d}{calendar.monthrange(y, m)[1]:02d}" if (y, m) != (ey, em) else end.replace("-", "")
        out.append((f"{y}{m:02d}", a, b))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


DZJY_PAGE = 5000      # AKShare's two block-trade functions send ONE request with pageSize 5000 and do not page


def _dzjy(fn, x, y):
    """Block-trade window. A result of 5000 rows or more may be cut by the upstream page size: the window is then
    requested again as two halves; if a half is still at the limit the unit fails (never stored truncated)."""
    df = em_guard(fn, x, y)
    if len(df) < DZJY_PAGE:
        return df, {"split": False}
    mid = x[:6] + "15"
    parts = []
    for p, q in ((x, mid), (x[:6] + "16", y)):
        if p > q:
            continue
        try:
            d = em_guard(fn, p, q)
        except NoData:
            continue
        if len(d) >= DZJY_PAGE:
            raise PermanentError(f"block-trade window {p}-{q} returned {len(d)} rows (page limit {DZJY_PAGE}): possibly truncated")
        parts.append(d)
    return pd.concat(parts, ignore_index=True), {"split": True, "rows_unsplit_request": int(len(df))}


def zo_units(a) -> list:
    import akshare as ak
    src = a.sources
    months = _spread(_months(a.start, a.end), a.limit)
    out = []
    table = [("lhb_detail", lambda x, y: em_guard(ak.stock_lhb_detail_em, x, y), "stock_lhb_detail_em", ("上榜日",)),
             ("lhb_jgmmtj", lambda x, y: em_guard(ak.stock_lhb_jgmmtj_em, x, y), "stock_lhb_jgmmtj_em", ("上榜日期",)),
             ("dzjy_mrtj", lambda x, y: _dzjy(ak.stock_dzjy_mrtj, x, y), "stock_dzjy_mrtj", ("交易日期",)),
             ("dzjy_mrmx", lambda x, y: _dzjy(lambda p, q: ak.stock_dzjy_mrmx("A股", p, q), x, y), "stock_dzjy_mrmx", ("交易日期",))]
    for name, fn, akname, dcols in table:
        if name in src:
            for ym, x, y in months:
                out.append(Unit("zo", name, ym, f"zo/{name}/{ym}.parquet", (lambda fn=fn, x=x, y=y: fn(x, y)),
                                {"fn": akname, "start": x, "end": y}, dcols, host="eastmoney"))
    if "ins_raw" in src:
        this_year = pd.Timestamp.today().year
        years = _spread(list(range(a.ins_first_year, this_year + 1)), a.limit)
        out.append(Unit("zo", "ins_raw", "TOTAL", "zo/ins_raw/TOTAL_count.parquet",
                        (lambda: _em_ins("", only_count=True)), {"report": "RPT_SHARE_HOLDER_INCREASE", "filter": ""},
                        (), host="eastmoney"))
        for y in years:
            flt = f"(NOTICE_DATE>='{y}-01-01')(NOTICE_DATE<='{y}-12-31')"
            out.append(Unit("zo", "ins_raw", str(y), f"zo/ins_raw/{y}.parquet", (lambda flt=flt: _em_ins(flt)),
                            {"report": "RPT_SHARE_HOLDER_INCREASE", "filter": flt, "page_size": 500}, ("NOTICE_DATE",),
                            host="eastmoney"))
    return out


STAGES = {
    "universe": (universe_units, ["bs_stock_basic", "bs_trade_dates", "bs_stock_industry", "sse_delist", "szse_delist"]),
    "bars": (bars_units, ["bs_daily"]),
    "factors_events": (factors_events_units, ["bs_factor", "bs_dividend", "em_fhps", "sina_dividend", "sina_rights"]),
    "index": (index_units, ["bs_index_daily", "bs_hs300", "bs_zz500"]),
    "crosscheck": (crosscheck_units, ["sina_daily"]),
    "zo": (zo_units, ["lhb_detail", "lhb_jgmmtj", "dzjy_mrtj", "dzjy_mrmx", "ins_raw"]),
}

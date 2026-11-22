"""Lightweight feasibility probe of AKShare 'opponent action' interfaces.

Not an experiment: <= 40 small calls, >= 1.5 s sleep between calls, raw output logged verbatim.
Usage: experiments/.venv/Scripts/python.exe experiments/src/data_feasibility/probe_akshare.py
"""
import json, sys, time, traceback, datetime as dt
from pathlib import Path
import pandas as pd
import requests
import akshare as ak

OUT = Path(__file__).resolve().parents[2] / "results" / "data_feasibility"
OUT.mkdir(parents=True, exist_ok=True)
LOG = open(OUT / "probe_log.txt", "w", encoding="utf-8")
SUMMARY = []
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60); pd.set_option("display.max_colwidth", 40)

def log(*a):
    s = " ".join(str(x) for x in a)
    LOG.write(s + "\n"); LOG.flush()

def date_ranges(df):
    out = {}
    for c in df.columns:
        name = str(c)
        if any(k in name for k in ("日", "时间", "DATE", "date", "TIME")):
            try:
                s = pd.to_datetime(df[c], errors="coerce").dropna()
                if len(s):
                    out[name] = [str(s.min().date()), str(s.max().date()), int(len(s))]
            except Exception:
                pass
    return out

def em_probe(report, sort_col, sort_type, flt=""):
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {"sortColumns": sort_col, "sortTypes": sort_type, "pageSize": "5", "pageNumber": "1",
              "reportName": report, "columns": "ALL", "source": "WEB", "client": "WEB", "filter": flt}
    r = requests.get(url, params=params, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    j = r.json()
    res = j.get("result") or {}
    df = pd.DataFrame(res.get("data") or [])
    df.attrs["total_count"] = res.get("count"); df.attrs["pages"] = res.get("pages"); df.attrs["message"] = j.get("message")
    return df

CALLS = [
 ("a", "stock_restricted_release_queue_em", dict(symbol="600000")),
 ("a", "stock_restricted_release_queue_em", dict(symbol="300104")),
 ("a", "stock_restricted_release_detail_em", dict(start_date="20120104", end_date="20120110")),
 ("a", "stock_restricted_release_queue_sina", dict(symbol="600000")),
 ("a", "stock_restricted_release_stockholder_em", dict(symbol="600000", date="20200904")),
 ("b", "EM_PROBE", dict(report="RPT_SHARE_HOLDER_INCREASE", sort_col="END_DATE", sort_type="1")),
 ("b", "EM_PROBE", dict(report="RPT_SHARE_HOLDER_INCREASE", sort_col="END_DATE", sort_type="-1")),
 ("b", "EM_PROBE", dict(report="RPT_EXECUTIVE_HOLD_DETAILS", sort_col="CHANGE_DATE", sort_type="1")),
 ("b", "stock_share_hold_change_sse", dict(symbol="600000")),
 ("b", "stock_share_hold_change_szse", dict(symbol="000001")),
 ("b", "stock_shareholder_change_ths", dict(symbol="600000")),
 ("b", "stock_notice_report", dict(symbol="持股变动", date="20150105")),
 ("c", "stock_lhb_detail_em", dict(start_date="20120104", end_date="20120106")),
 ("c", "stock_lhb_detail_em", dict(start_date="20240102", end_date="20240102")),
 ("c", "stock_lhb_stock_detail_date_em", dict(symbol="300104")),
 ("c", "stock_lhb_stock_detail_em", dict(symbol="000788", date="20220315", flag="买入")),
 ("c", "stock_lhb_jgmmtj_em", dict(start_date="20120104", end_date="20120110")),
 ("d", "stock_margin_detail_sse", dict(date="20120104")),
 ("d", "stock_margin_detail_szse", dict(date="20120104")),
 ("d", "stock_margin_detail_sse", dict(date="20240102")),
 ("d", "stock_margin_detail_szse", dict(date="20240102")),
 ("d", "stock_margin_underlying_info_szse", dict(date="20150105")),
 ("e", "stock_dzjy_mrmx", dict(symbol="A股", start_date="20120104", end_date="20120106")),
 ("e", "stock_dzjy_mrmx", dict(symbol="A股", start_date="20240102", end_date="20240102")),
 ("e", "stock_dzjy_mrtj", dict(start_date="20120104", end_date="20120104")),
 ("f", "stock_zh_a_gdhs_detail_em", dict(symbol="000001")),
 ("f", "stock_zh_a_gdhs_detail_em", dict(symbol="300104")),
 ("f", "stock_zh_a_gdhs", dict(symbol="20120331")),
 ("f", "stock_hold_num_cninfo", dict(date="20170331")),
 ("g", "stock_hsgt_individual_em", dict(symbol="600519")),
 ("g", "stock_hsgt_individual_detail_em", dict(symbol="600519", start_date="20170103", end_date="20170110")),
 ("g", "stock_hsgt_stock_statistics_em", dict(symbol="北向持股", start_date="20170315", end_date="20170315")),
 ("g", "stock_hsgt_stock_statistics_em", dict(symbol="北向持股", start_date="20261110", end_date="20261110")),
 ("g", "stock_hsgt_hist_em", dict(symbol="北向资金")),
 ("h", "stock_gpzy_pledge_ratio_em", dict(date="20180105")),
 ("h", "stock_gpzy_individual_pledge_ratio_detail_em", dict(symbol="300104")),
 ("h", "stock_jgdy_tj_em", dict(date="20261101")),
 ("h", "EM_PROBE", dict(report="RPTA_WEB_GETHGLIST_NEW", sort_col="DIM_DATE", sort_type="1")),
 ("h", "EM_PROBE", dict(report="RPTA_WEB_GETHGLIST_NEW", sort_col="DIM_DATE", sort_type="-1")),
]
assert len(CALLS) <= 40

only = set(sys.argv[1:])
log("akshare", ak.__version__, "| python", sys.version.split()[0], "| started", dt.datetime.now().isoformat(timespec="seconds"))
for i, (cls, fn, kw) in enumerate(CALLS, 1):
    if only and str(i) not in only:
        continue
    rec = {"id": i, "class": cls, "function": fn, "kwargs": kw}
    log("\n" + "=" * 100); log(f"[{i}] class={cls} {fn}({kw})")
    t0 = time.time()
    try:
        df = em_probe(**kw) if fn == "EM_PROBE" else getattr(ak, fn)(**kw)
        rec["elapsed_s"] = round(time.time() - t0, 2)
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"returned {type(df)}")
        rec.update(ok=True, rows=int(len(df)), columns=[str(c) for c in df.columns], date_ranges=date_ranges(df), attrs={k: v for k, v in df.attrs.items()})
        log("OK elapsed_s=", rec["elapsed_s"], "rows=", len(df), "attrs=", dict(df.attrs))
        log("columns:", rec["columns"]); log("date_ranges[min,max,n]:", json.dumps(rec["date_ranges"], ensure_ascii=False))
        log("head(3):\n" + df.head(3).to_string()); log("tail(3):\n" + df.tail(3).to_string())
    except Exception as e:
        rec.update(ok=False, elapsed_s=round(time.time() - t0, 2), error=f"{type(e).__name__}: {e}"[:600])
        log("FAILED elapsed_s=", rec["elapsed_s"], rec["error"]); log(traceback.format_exc()[-1500:])
    SUMMARY.append(rec)
    json.dump(SUMMARY, open(OUT / ("probe_summary.json" if not only else "probe_summary_partial.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(i, fn, "OK" if rec["ok"] else "FAILED", rec["elapsed_s"], rec.get("rows"), flush=True)
    time.sleep(1.5)
log("\nfinished", dt.datetime.now().isoformat(timespec="seconds"))

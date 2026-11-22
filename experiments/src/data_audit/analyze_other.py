"""Analysis of index constituents, suspension records, ST flag, Z_O tables, originals, and call statistics (no network)."""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import pandas as pd

import load as L
from harness import OUT, CACHE

pd.set_option("display.width", 280); pd.set_option("display.max_columns", 60); pd.set_option("display.max_colwidth", 70)
TAB = OUT / "tables"; TAB.mkdir(exist_ok=True)
R = {}
log = L.call_log()
log = log[log.get("attempt").notna()].copy()


def cached(group=None, name=None):
    g = log[(log.cache.notna())]
    if group:
        g = g[g.group == group]
    if name:
        g = g[g.name == name]
    out = []
    for _, x in g.iterrows():
        p = CACHE / x.cache
        d = pd.read_parquet(p) if x.cache.endswith(".parquet") else pd.read_csv(p, dtype=str)
        out.append((x, d))
    return out


# ------------------------------------------------------------------ call statistics
st = log.groupby("group").agg(calls=("status", "size"), ok=("status", lambda s: int((s == "ok").sum())), empty=("status", lambda s: int((s == "empty").sum())),
                              err_net=("status", lambda s: int((s == "error_net").sum())), err_parse=("status", lambda s: int((s == "error_parse").sum())),
                              http=("http_requests", "sum"), mean_s=("elapsed_s", "mean"), median_s=("elapsed_s", "median"), max_s=("elapsed_s", "max")).round(2)
st.to_csv(TAB / "call_stats_by_group.csv", encoding="utf-8-sig")
print(st.to_string())
first = log[log.attempt == 0]
R["calls"] = {"logical_calls_incl_retries": int(len(log)), "distinct_requests": int(len(first)), "http_requests": int(log.http_requests.sum()),
              "first_attempt_ok_or_empty": int(first.status.isin(["ok", "empty"]).sum()), "first_attempt_net_error": int((first.status == "error_net").sum()),
              "first_attempt_parse_error": int((first.status == "error_parse").sum())}
host = {"em_raw": "eastmoney push2his (quotes)", "em_hfq": "eastmoney push2his (quotes)", "em_qfq": "eastmoney push2his (quotes)", "probe": "eastmoney push2his (quotes)"}
p2 = log[log.group.isin(host.keys())]
R["calls"]["push2_attempts"] = int(len(p2)); R["calls"]["push2_ok"] = int((p2.status == "ok").sum())
print(json.dumps(R["calls"], indent=1))

# ------------------------------------------------------------------ index constituents (A2)
rows = []
mem = {}
for x, d in cached(group="bs_index"):
    idx = "hs300" if "hs300" in x["name"] else "zz500"
    day = x.kwargs["date"]
    upd = sorted(d.updateDate.unique()) if len(d) else []
    mem[(idx, day)] = set(d.code.str[3:]) if len(d) else set()
    rows.append({"index": idx, "query_date": day, "n": len(d), "updateDate": ",".join(upd)})
a2 = pd.DataFrame(rows).sort_values(["index", "query_date"])
for idx in ["hs300", "zz500"]:
    days = sorted([k[1] for k in mem if k[0] == idx])
    for a, b in zip(days[:-1], days[1:]):
        a2.loc[(a2["index"] == idx) & (a2.query_date == b), "changed_vs_prev_query"] = len(mem[(idx, b)] - mem[(idx, a)])
a2.to_csv(TAB / "A2_index_counts.csv", index=False, encoding="utf-8-sig")
print(a2.to_string())
exp = {"hs300": 300, "zz500": 500}
R["A2"] = {"queries": int(len(a2)), "count_exact": int(sum(a2.n == a2["index"].map(exp))), "counts": a2.groupby("index").n.agg(["min", "max"]).to_dict(),
           "distinct_updateDates": sorted(set(sum([u.split(",") for u in a2.updateDate if u], [])))}
# delisted sample names that were ever members on the sampled dates
smp = L.sample()
dl = set(smp[smp.exch_delist_date.notna()].code)
ever = set().union(*mem.values()) if mem else set()
R["A2"]["sampled_dates_union_members"] = len(ever)
R["A2"]["delisted_sample_names_seen_as_members"] = sorted(ever & dl)
allst = set(pd.read_parquet(next(CACHE.glob("bs_query_stock_basic__*.parquet"))).code.str[3:])
R["A2"]["members_missing_in_bs_basic"] = sorted(ever - allst)
basic = pd.read_parquet(next(CACHE.glob("bs_query_stock_basic__*.parquet"))); basic["c"] = basic.code.str[3:]
R["A2"]["members_now_delisted_per_bs_basic"] = int(basic[basic.c.isin(ever) & (basic.status == "0")].shape[0])
# membership after delisting / before listing (point-in-time sanity)
bad = []
bb = basic[basic.type == "1"].drop_duplicates("c").set_index("c")
for (idx, day), s in mem.items():
    for c in s:
        if c in bb.index:
            if bb.ipoDate[c] > day or (bb.outDate[c] and bb.outDate[c] < day):
                bad.append((idx, day, c, bb.ipoDate[c], bb.outDate[c]))
R["A2"]["member_on_date_outside_listing_span"] = bad[:20]
# AKShare side
for x, d in cached(group="ak_index"):
    print("##", x["name"], x.args, len(d), list(d.columns)[:10]); print(d.head(3).to_string())
    key = f"{x['name']}({x.args[0]})"
    R["A2"][key] = {"rows": int(len(d)), "columns": list(d.columns)}
    for c in d.columns:
        if "日期" in c:
            dd = pd.to_datetime(d[c], errors="coerce")
            R["A2"][key][c] = [str(dd.min().date()), str(dd.max().date()), int(dd.nunique())]
    if x["name"] == "index_stock_cons" and len(d):
        cur = set(d.iloc[:, 0].astype(str).str.zfill(6))
        last = max([k[1] for k in mem if k[0] == ("hs300" if x.args[0] == "000300" else "zz500")], default=None)
        if last:
            m = mem[("hs300" if x.args[0] == "000300" else "zz500", last)]
            R["A2"][key]["overlap_with_bs_" + last] = len(cur & m)
    if x["name"] == "index_stock_cons_csindex" and len(d):
        cur = set(d["成分券代码"].astype(str).str.zfill(6))
        idx = "hs300" if x.args[0] == "000300" else "zz500"
        last = max([k[1] for k in mem if k[0] == idx], default=None)
        if last:
            R["A2"][key]["overlap_with_bs_" + last] = len(cur & mem[(idx, last)])
print(json.dumps(R["A2"], ensure_ascii=False, indent=1, default=str))

# ------------------------------------------------------------------ suspension records: Eastmoney tfp vs BaoStock all_stock (A8 / A22)
rows = []
tfp = {x.args[0]: d for x, d in cached(group="em_tfp")}
alls = {x.kwargs["day"].replace("-", ""): d for x, d in cached(group="bs_allstock")}
for day in sorted(set(tfp) | set(alls)):
    t, a = tfp.get(day), alls.get(day)
    row = {"date": day, "em_tfp_rows": None if t is None else len(t), "bs_all_rows": None if a is None else len(a)}
    if t is not None and len(t):
        t = t.copy()
        t["停牌时间"] = pd.to_datetime(t["停牌时间"], errors="coerce"); t["停牌截止时间"] = pd.to_datetime(t["停牌截止时间"], errors="coerce")
        row["em_tfp_start_min"] = str(t["停牌时间"].min().date()); row["em_tfp_start_max"] = str(t["停牌时间"].max().date())
        d0 = pd.Timestamp(day)
        act = t[(t["停牌时间"].dt.normalize() <= d0) & (t["停牌截止时间"].isna() | (t["停牌截止时间"].dt.normalize() >= d0))]
        row["em_tfp_active_on_date"] = len(act)
        row["em_tfp_period_values"] = dict(t["停牌期限"].value_counts().head(6))
        ems = set(act["代码"].astype(str).str.zfill(6))
        ems = {c for c in ems if re.match(r"^(60|68|00|30)", c)}
        row["em_active_A"] = len(ems)
        if a is not None and len(a):
            a = a.copy(); a["c"] = a.code.str[3:]
            a = a[a.code.str.match(r"^(sh\.6|sz\.0|sz\.3)") & ~a.code.str.match(r"^sz\.399")]
            bss = set(a[a.tradeStatus == "0"].c)
            row.update({"bs_stocks": len(a), "bs_suspended": len(bss), "both": len(ems & bss), "em_only": len(ems - bss), "bs_only": len(bss - ems)})
    elif a is not None and len(a):
        a = a.copy(); a = a[a.code.str.match(r"^(sh\.6|sz\.0|sz\.3)") & ~a.code.str.match(r"^sz\.399")]
        row.update({"bs_stocks": len(a), "bs_suspended": int((a.tradeStatus == "0").sum())})
    rows.append(row)
s8 = pd.DataFrame(rows)
s8.to_csv(TAB / "A8_tfp_vs_baostock.csv", index=False, encoding="utf-8-sig")
print(s8.to_string())
R["A8_tfp"] = s8.to_dict("records")
for x, d in cached(group="em_tfp")[:1]:
    print(d.head(5).to_string()); print(d.tail(3).to_string())
for x, d in cached(group="bs_allstock")[:1]:
    print(d.head(3).to_string())

# ------------------------------------------------------------------ ST flag (A9)
rows = []
for c in smp.code:
    b = L.bs_raw(c)
    if b is None or b.empty:
        continue
    f = b.isST.fillna(0).astype(int)
    ch = f[f != f.shift()].iloc[1:]
    for t, v in ch.items():
        rows.append({"code": c, "flag_change_date": t.date(), "to": int(v)})
stc = pd.DataFrame(rows)
stc.to_csv(TAB / "A9_bs_isST_changes.csv", index=False, encoding="utf-8-sig")
R["A9"] = {"bs_isST_changes_in_sample": int(len(stc)), "stocks_with_changes": int(stc.code.nunique()) if len(stc) else 0,
           "stock_days_isST1": int(sum((L.bs_raw(c).isST == 1).sum() for c in smp.code if L.bs_raw(c) is not None))}
nm = cached(group="szse_names")
if nm:
    d = nm[0][1]
    print("SZSE name-change table:", d.shape, list(d.columns)); print(d.head(3).to_string())
    codecol = [c for c in d.columns if "代码" in c][0]; datecol = [c for c in d.columns if "日期" in c][0]
    newcol = [c for c in d.columns if "变更后" in c][0]; oldcol = [c for c in d.columns if "变更前" in c][0]
    d = d.copy(); d[codecol] = d[codecol].astype(str).str.zfill(6); d[datecol] = pd.to_datetime(d[datecol], errors="coerce")
    R["A9"]["szse_name_changes_rows"] = int(len(d)); R["A9"]["szse_name_change_dates"] = [str(d[datecol].min().date()), str(d[datecol].max().date())]
    isst = lambda s: bool(re.search(r"ST", str(s).upper()))
    ev = d[d[codecol].isin(set(smp.code))].copy()
    ev["to_st"] = ev[newcol].map(isst); ev["from_st"] = ev[oldcol].map(isst)
    ev = ev[ev.to_st != ev.from_st]
    cal = L.calendar()
    out = []
    for _, r in ev.iterrows():
        c = r[codecol]; b = L.bs_raw(c)
        if b is None or r[datecol] < b.index.min() or r[datecol] > b.index.max():
            continue
        want = 1 if r.to_st else 0
        cand = stc[(stc.code == c) & (stc.to == want)]
        if len(cand):
            diffs = [(int(np.searchsorted(cal, pd.Timestamp(x)) - np.searchsorted(cal, r[datecol]))) for x in cand.flag_change_date]
            k = int(np.argmin(np.abs(diffs)))
            out.append({"code": c, "szse_date": r[datecol].date(), "old": r[oldcol], "new": r[newcol], "bs_flag_date": cand.flag_change_date.iloc[k], "flag_minus_szse_tdays": diffs[k]})
        else:
            out.append({"code": c, "szse_date": r[datecol].date(), "old": r[oldcol], "new": r[newcol], "bs_flag_date": None, "flag_minus_szse_tdays": None})
    o = pd.DataFrame(out); o.to_csv(TAB / "A9_st_events_szse_vs_bs.csv", index=False, encoding="utf-8-sig")
    print(o.to_string())
    if len(o):
        dd = o.flag_minus_szse_tdays
        R["A9"]["szse_events_in_sample"] = int(len(o)); R["A9"]["exact_same_day"] = int((dd == 0).sum()); R["A9"]["within_1_tday"] = int((dd.abs() <= 1).sum())
        R["A9"]["flag_earlier_than_szse_date"] = int((dd < 0).sum()); R["A9"]["flag_later"] = int((dd > 0).sum()); R["A9"]["no_flag_change_found"] = int(dd.isna().sum())
for x, d in cached(group="sina_names"):
    print("sina names", x.args, d.name.tolist() if "name" in d else d.shape)
for x, d in cached(group="em_st"):
    R["A9"]["em_current_st_board_rows"] = int(len(d)); print("EM ST board now:", d.shape)
print(json.dumps(R["A9"], ensure_ascii=False, indent=1, default=str))

# ------------------------------------------------------------------ Z_O
Z = {}
cnt = []
for x, d in cached(group="zo_count"):
    y = re.search(r">='(\d{4})", x.args[1]).group(1)
    cnt.append({"class": x["name"].replace("em_count_", ""), "year": int(y), "rows": int(d["_count"].iloc[0]), "first_date": str(d.iloc[0].get("TRADE_DATE", d.iloc[0].get("NOTICE_DATE", "")))[:10]})
cnt = pd.DataFrame(cnt)
if len(cnt):
    pv = cnt.pivot(index="year", columns="class", values="rows"); pv.to_csv(TAB / "OA3_yearly_counts.csv", encoding="utf-8-sig"); print(pv.to_string())
    Z["yearly_counts"] = {str(k): v for k, v in pv.to_dict("index").items()}
# columns of each table and ex-post classification is written in the report by hand; store the column lists
cols = {}
for x, d in cached():
    if x.group.startswith("zo_") and x.group != "zo_count":
        cols.setdefault(x["name"], list(d.columns))
Z["columns"] = cols
# LHB: Eastmoney vs Sina vs exchange originals on 2015-07-06
lhb = {tuple(x.args): d for x, d in cached(name="stock_lhb_detail_em")}
sina = {x.args[0]: d for x, d in cached(name="stock_lhb_detail_daily_sina")}
orig = {}
for x, d in cached(group="orig"):
    if "text" in d:
        orig[(x["name"], json.dumps(x.args, ensure_ascii=False))] = d.iloc[0]
cmp = {}
for day, win in [("20150706", ("20150706", "20150708")), ("20240102", ("20240102", "20240103"))]:
    e = lhb.get(win)
    if e is None:
        continue
    dd = pd.to_datetime(e["上榜日"]).dt.strftime("%Y%m%d")
    em_codes = set(e[dd == day]["代码"].astype(str).str.zfill(6))
    o = {"em_codes": len(em_codes)}
    if day in sina:
        sc = set(sina[day]["股票代码"].astype(str).str.zfill(6))
        o.update({"sina_codes": len(sc), "em_and_sina": len(em_codes & sc), "em_only": len(em_codes - sc), "sina_only": len(sc - em_codes)})
    # SZSE main-board original text
    for k, r in orig.items():
        if k[0] == "orig_szse_lhb_txt" and f"jy{day[2:]}" in k[1]:
            body = r.text.split("详细信息")[0]
            oc = set(re.findall(r"\n\s*(\d{6})\s", body))
            sub = {c for c in em_codes if c.startswith(("000", "001"))}
            o.update({"szse_main_orig_codes": len(oc), "em_szse_main_codes(000/001)": len(sub), "orig_in_em": len(oc & em_codes), "orig_not_in_em": sorted(oc - em_codes)[:10],
                      "em_main_not_in_orig": sorted(sub - oc)[:10], "szse_file_last_modified": r.last_modified})
        if k[0] == "orig_sse_lhb" and f"{day[:4]}-{day[4:6]}-{day[6:]}" in k[1]:
            oc = set(re.findall(r"\(\d+\)\s+(6\d{5})\s", r.text))
            sub = {c for c in em_codes if c.startswith("6")}
            o.update({"sse_orig_codes": len(oc), "em_sse_codes": len(sub), "sse_orig_in_em": len(oc & em_codes), "sse_orig_not_in_em": sorted(oc - em_codes)[:10], "em_sse_not_in_orig": sorted(sub - oc)[:10]})
    cmp[day] = o
Z["lhb_cross_check"] = cmp
for k, r in orig.items():
    if k[0] == "orig_szse_lhb_txt":
        Z.setdefault("szse_lhb_file_last_modified", {})[re.search(r"jy\d{6}", k[1]).group(0)] = r.last_modified
# BLK: Eastmoney vs SSE original
blk = {tuple(x.args): d for x, d in cached(name="stock_dzjy_mrmx")}
bc = {}
for k, r in orig.items():
    if k[0] == "orig_sse_blk":
        day = re.search(r'"startDate": "(\d{4}-\d{2}-\d{2})"', k[1]).group(1)
        try:
            j = json.loads(r.text)
            od = pd.DataFrame(j["pageHelp"]["data"]); total = j["pageHelp"].get("total")
        except Exception as ex:
            bc[day] = {"parse_error": str(ex)[:100]}; continue
        e = None
        for win, d in blk.items():
            if win[1] <= day.replace("-", "") <= win[2]:
                e = d[pd.to_datetime(d["交易日期"]).dt.strftime("%Y-%m-%d") == day]
        o = {"sse_orig_rows_returned": int(len(od)), "sse_orig_total": total}
        if e is not None and len(od):
            es = e[e["证券代码"].astype(str).str.startswith("6")]
            ek = set(zip(es["证券代码"].astype(str), es["成交价"].astype(float).round(2), (es["成交量"].astype(float) / 1e4).round(2)))
            ok_ = set(zip(od.stockid.astype(str), od.tradeprice.astype(float).round(2), od.tradeqty.astype(float).round(2)))
            ok_a = {k2 for k2 in ok_ if k2[0].startswith("6")}
            o.update({"em_sse_rows": int(len(es)), "em_distinct_keys": len(ek), "orig_distinct_keys(6xxxxx)": len(ok_a), "matched_keys": len(ek & ok_a),
                      "orig_not_in_em": sorted(ok_a - ek)[:5], "em_not_in_orig": sorted(ek - ok_a)[:5]})
        bc[day] = o
Z["blk_cross_check_sse"] = bc
# INS: Eastmoney by code
ins = []
em_ins = {}
for x, d in cached(name="em_ins_by_code"):
    c = re.search(r'"(\d{6})"', x.args[1]).group(1)
    if "NOTICE_DATE" not in d:
        ins.append({"code": c, "rows": 0}); continue
    nd, ed, ei = pd.to_datetime(d.NOTICE_DATE), pd.to_datetime(d.END_DATE), pd.to_datetime(d.EITIME)
    em_ins[c] = d
    gap = (ei.dt.normalize() - nd).dt.days
    ins.append({"code": c, "rows": len(d), "notice_min": nd.min().date(), "notice_max": nd.max().date(), "notice_missing": int(nd.isna().sum()), "notice_before_end": int((nd < ed).sum()),
                "notice_minus_end_days_median": float((nd - ed).dt.days.median()), "entry_before_notice(-1d)": int((gap == -1).sum()), "entry_same_day": int((gap == 0).sum()),
                "entry_1_to_7d": int(((gap >= 1) & (gap <= 7)).sum()), "entry_gt_30d_after": int((gap > 30).sum()), "entry_min": str(ei.min())})
ins = pd.DataFrame(ins); ins.to_csv(TAB / "OA_ins_by_code.csv", index=False, encoding="utf-8-sig"); print(ins.to_string())
Z["ins_by_code"] = ins.to_dict("records")
tot = ins[ins.rows > 0]
Z["ins_totals"] = {"rows": int(tot.rows.sum()), "notice_missing": int(tot.notice_missing.sum()), "notice_before_end": int(tot.notice_before_end.sum()),
                   "entry_gt_30d_after_notice": int(tot["entry_gt_30d_after"].sum()), "entry_day_before_notice": int(tot["entry_before_notice(-1d)"].sum())}
# INS: Eastmoney vs 10jqka announcement dates (match on holder-period end date)
m3 = []
for x, d in cached(name="stock_shareholder_change_ths"):
    c = x.args[0]
    if c not in em_ins or not len(d):
        continue
    t = d.copy()
    t["end"] = pd.to_datetime(t["变动期间"].str.split("-").str[-1], format="%Y.%m.%d", errors="coerce")
    t["notice"] = pd.to_datetime(t["公告日期"], errors="coerce")
    e = em_ins[c].copy(); e["end"] = pd.to_datetime(e.END_DATE); e["notice"] = pd.to_datetime(e.NOTICE_DATE)
    tk = t.groupby("end").notice.min(); ek = e.groupby("end").notice.min()
    common = tk.index.intersection(ek.index)
    dd = (ek[common] - tk[common]).dt.days
    m3.append({"code": c, "ths_rows": len(t), "em_rows": len(e), "ths_end_dates": len(tk), "em_end_dates": len(ek), "common_end_dates": len(common),
               "notice_equal": int((dd == 0).sum()), "em_earlier": int((dd < 0).sum()), "em_later": int((dd > 0).sum())})
Z["ins_em_vs_ths"] = m3
for x, d in cached(group="zo_ins_sse") + cached(group="zo_ins_szse"):
    dc = [c for c in d.columns if "日期" in c]
    Z.setdefault("ins_exchange_tables", []).append({"name": x["name"], "code": x.args[0], "rows": int(len(d)), "date_cols": dc,
                                                    "range": [str(pd.to_datetime(d[dc[0]], errors="coerce").min())[:10], str(pd.to_datetime(d[dc[0]], errors="coerce").max())[:10]] if len(d) else None})
dls = []
for x, d in cached(group="zo_delisted"):
    c = re.search(r'"(\d{6})"', x.args[1]).group(1)
    td = pd.to_datetime(d.TRADE_DATE) if "TRADE_DATE" in d else None
    dls.append({"table": x["name"], "code": c, "rows": int(d["_count"].iloc[0]), "first": None if td is None else str(td.min().date()), "last": None if td is None else str(td.max().date())})
Z["delisted_in_lhb_blk"] = dls
# cninfo originals: timestamps
ci = []
for k, r in orig.items():
    if k[0] == "orig_cninfo_ann":
        try:
            j = json.loads(r.text)
            for a in (j.get("announcements") or []):
                ts = pd.Timestamp(a["announcementTime"], unit="ms", tz="UTC").tz_convert("Asia/Shanghai")
                ci.append({"code": a["secCode"], "title": re.sub("<.*?>", "", a["announcementTitle"])[:40], "time_cst": str(ts), "has_clock_time": bool(ts.hour or ts.minute or ts.second > 1), "url": "http://static.cninfo.com.cn/" + a["adjunctUrl"]})
        except Exception as ex:
            ci.append({"parse_error": str(ex)[:100]})
Z["cninfo_samples"] = ci
print(json.dumps(Z, ensure_ascii=False, indent=1, default=str)[:9000])
R["ZO"] = Z
json.dump(R, open(OUT / "analysis_other.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("written analysis_other.json")

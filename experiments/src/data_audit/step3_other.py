"""Step 3: index constituents, suspension records, ST / name history, and the three Z_O classes.
Stages: I (index), S (suspension + ST), Z (Z_O tables), O (availability of original disclosures)."""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import requests
import akshare as ak
from harness import call, bs_call, bs_logout, calls_used, OUT, LOGS, BudgetExceeded

stage = sys.argv[1]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
EM = "https://datacenter-web.eastmoney.com/api/data/v1/get"


def em_dc(report, flt, sort="", sort_types="-1", page_size=500, page=1, columns="ALL"):
    """One page of an Eastmoney datacenter report; returns rows plus the upstream total count in column `_count`."""
    params = {"reportName": report, "columns": columns, "filter": flt, "pageSize": page_size, "pageNumber": page,
              "source": "WEB", "client": "WEB"}
    if sort:
        params.update({"sortColumns": sort, "sortTypes": sort_types})
    r = requests.get(EM, params=params, headers=UA, timeout=20)
    j = r.json()
    if not j.get("result"):
        return pd.DataFrame({"_count": [0], "_message": [str(j.get("message"))]})
    df = pd.DataFrame(j["result"]["data"])
    df["_count"] = j["result"]["count"]
    return df.astype(str)


def raw_get(url, params=None, headers=None, encoding=None):
    h = dict(UA); h.update(headers or {})
    r = requests.get(url, params=params, headers=h, timeout=20)
    if encoding:
        r.encoding = encoding
    return pd.DataFrame({"status": [r.status_code], "url": [r.url], "content_type": [r.headers.get("Content-Type", "")],
                         "last_modified": [r.headers.get("Last-Modified", "")], "length": [len(r.content)],
                         "text": [r.text[:60000]]})


def raw_post(url, data=None, headers=None):
    h = dict(UA); h.update(headers or {})
    r = requests.post(url, data=data, headers=h, timeout=20)
    return pd.DataFrame({"status": [r.status_code], "url": [r.url], "length": [len(r.content)], "text": [r.text[:60000]]})


try:
    if stage == "I":
        dates = ["2010-01-04", "2011-07-01", "2013-01-04", "2014-12-12", "2014-12-15", "2016-06-08", "2016-06-13",
                 "2018-06-11", "2019-12-16", "2021-06-11", "2021-06-15", "2022-12-12", "2024-12-13", "2024-12-16",
                 "2025-06-16", "2026-06-30"]
        for d in dates:
            bs_call("query_hs300_stocks", date=d, group="bs_index")
            bs_call("query_zz500_stocks", date=d, group="bs_index")
        call("index_stock_cons_csindex", ak.index_stock_cons_csindex, "000300", group="ak_index")
        call("index_stock_cons_csindex", ak.index_stock_cons_csindex, "000905", group="ak_index")
        call("index_stock_cons_weight_csindex", ak.index_stock_cons_weight_csindex, "000300", group="ak_index")
        call("index_stock_cons", ak.index_stock_cons, "000300", group="ak_index")
        call("index_stock_cons", ak.index_stock_cons, "000905", group="ak_index")
    if stage == "S":
        for d in ["2010-01-04", "2015-07-08", "2016-01-04", "2018-06-20", "2020-02-03", "2024-01-02"]:
            call("stock_tfp_em", ak.stock_tfp_em, d.replace("-", ""), group="em_tfp")
            bs_call("query_all_stock", day=d, group="bs_allstock")
        call("stock_info_sz_change_name", ak.stock_info_sz_change_name, "简称变更", group="szse_names")
        for c in ["000792", "600485", "300104", "600710", "001872"]:
            call("stock_info_change_name", ak.stock_info_change_name, c, group="sina_names")
        call("stock_zh_a_st_em", ak.stock_zh_a_st_em, group="em_st")
    if stage == "Z":
        # --- Dragon-Tiger (LHB), block trades (BLK): AKShare date-window calls
        for a, b in [("20100104", "20100108"), ("20110104", "20110107"), ("20150706", "20150708"),
                     ("20200203", "20200205"), ("20240102", "20240103"), ("20260629", "20260630")]:
            call("stock_lhb_detail_em", ak.stock_lhb_detail_em, a, b, group="zo_lhb")
            call("stock_dzjy_mrmx", ak.stock_dzjy_mrmx, "A股", a, b, group="zo_blk")
        for a, b in [("20100104", "20100108"), ("20150706", "20150708"), ("20260629", "20260630")]:
            call("stock_lhb_jgmmtj_em", ak.stock_lhb_jgmmtj_em, a, b, group="zo_lhb")
            call("stock_dzjy_mrtj", ak.stock_dzjy_mrtj, a, b, group="zo_blk")
        for d in ["20150706", "20240102"]:
            call("stock_lhb_detail_daily_sina", ak.stock_lhb_detail_daily_sina, d, group="zo_lhb_sina")
        # --- yearly row counts straight from the upstream (1 row per request; the count field is what we read)
        for y in [2005, 2008, 2009, 2010, 2011, 2012, 2016, 2021, 2025]:
            call("em_count_lhb", em_dc, "RPT_DAILYBILLBOARD_DETAILSNEW", f"(TRADE_DATE>='{y}-01-01')(TRADE_DATE<='{y}-12-31')",
                 "TRADE_DATE", "1", 1, group="zo_count")
            call("em_count_blk", em_dc, "RPT_DATA_BLOCKTRADE", f"(SECURITY_TYPE_WEB=1)(TRADE_DATE>='{y}-01-01')(TRADE_DATE<='{y}-12-31')",
                 "TRADE_DATE", "1", 1, group="zo_count")
            call("em_count_ins", em_dc, "RPT_SHARE_HOLDER_INCREASE", f"(NOTICE_DATE>='{y}-01-01')(NOTICE_DATE<='{y}-12-31')",
                 "NOTICE_DATE", "1", 1, group="zo_count")
        # --- executed share changes (INS): all upstream columns for sample names (incl. delisted)
        for c in ["300104", "600485", "002450", "600074", "000002", "300059", "600519", "000651", "002594", "688111"]:
            call("em_ins_by_code", em_dc, "RPT_SHARE_HOLDER_INCREASE", f'(SECURITY_CODE="{c}")', "NOTICE_DATE", "-1", 500, group="zo_ins")
        # --- delisted names in LHB / BLK tables
        for c in ["300104", "600485", "002450", "600074"]:
            call("em_lhb_by_code", em_dc, "RPT_DAILYBILLBOARD_DETAILSNEW", f'(SECURITY_CODE="{c}")', "TRADE_DATE", "1", 500, group="zo_delisted")
            call("em_blk_by_code", em_dc, "RPT_DATA_BLOCKTRADE", f'(SECURITY_CODE="{c}")', "TRADE_DATE", "1", 500, group="zo_delisted")
        # --- second / third upstream for INS
        for c in ["600519", "600036", "600485"]:
            call("stock_share_hold_change_sse", ak.stock_share_hold_change_sse, c, group="zo_ins_sse")
        for c in ["000002", "300104"]:
            call("stock_share_hold_change_szse", ak.stock_share_hold_change_szse, c, group="zo_ins_szse")
        for c in ["600519", "000002", "300104"]:
            call("stock_shareholder_change_ths", ak.stock_shareholder_change_ths, c, group="zo_ins_ths")
    if stage == "O":
        # Are the ORIGINAL disclosures retrievable from official sites, and do they carry a publication time?
        # (a) SZSE daily public trading information text files (Dragon-Tiger), old and recent
        for u in ["http://reportdocs.static.szse.cn/files/text/jy/jy150706.txt",
                  "http://reportdocs.static.szse.cn/files/text/jy/jy100104.txt",
                  "http://reportdocs.static.szse.cn/files/text/jy/jy240102.txt"]:
            call("orig_szse_lhb_txt", raw_get, u, None, None, "gbk", group="orig")
        # (b) SSE daily public trading information
        for d in ["2015-07-06", "2024-01-02"]:
            call("orig_sse_lhb", raw_get, "http://query.sse.com.cn/infodisplay/showTradePublicFile.do",
                 {"dateTx": d}, {"Referer": "http://www.sse.com.cn/"}, group="orig")
        # (c) SZSE block trades by date
        for d in ["2015-07-06", "2010-01-05"]:
            call("orig_szse_blk", raw_get, "https://www.szse.cn/api/report/ShowReport/data",
                 {"SHOWTYPE": "JSON", "CATALOGID": "1842_xxpl", "TABKEY": "tab1", "txtStart": d, "txtEnd": d},
                 {"Referer": "https://www.szse.cn/disclosure/deal/block/index.html"}, group="orig")
        # (d) SSE block trades by date
        for d in ["2015-07-06", "2010-01-05"]:
            call("orig_sse_blk", raw_get, "http://query.sse.com.cn/commonQuery.do",
                 {"sqlId": "COMMON_SSE_XXPL_JYXXPL_DZJYXX_L", "isPagination": "true", "stockId": "", "startDate": d,
                  "endDate": d, "pageHelp.pageSize": "25", "pageHelp.pageNo": "1", "pageHelp.beginPage": "1",
                  "pageHelp.endPage": "5", "pageHelp.cacheSize": "1"}, {"Referer": "http://www.sse.com.cn/"}, group="orig")
        # (e) company announcements with time stamps: cninfo full-text index (statutory disclosure platform)
        for stock, a, b in [("000002,gssz0000002", "2015-07-01", "2015-12-31"), ("600519,gssh0600519", "2012-01-01", "2014-12-31")]:
            call("orig_cninfo_ann", raw_post, "http://www.cninfo.com.cn/new/hisAnnouncement/query",
                 {"stock": stock, "tabName": "fulltext", "pageSize": "30", "pageNum": "1", "column": "szse" if stock.startswith("0") else "sse",
                  "category": "", "plate": "", "seDate": f"{a}~{b}", "searchkey": "增持", "secid": "", "sortName": "", "sortType": "", "isHLtitle": "true"},
                 {"X-Requested-With": "XMLHttpRequest", "Referer": "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search"},
                 group="orig")
        # (f) Eastmoney announcement index for share-change notices on two dates (URL to the notice text)
        for d in ["20120601", "20240103"]:
            call("stock_notice_report", ak.stock_notice_report, "持股变动", d, group="orig")
except BudgetExceeded as e:
    print("STOP:", e)
bs_logout()
print("stage", stage, "calls used", calls_used())

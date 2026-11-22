"""Step 2: price / adjustment / corporate-action pulls for the sample.
Stage A BaoStock; stage B Eastmoney datacenter + Sina; stage C Eastmoney push2 quotes (rate-limit breaker); stage D Tencent.
(First attempt at 12:59 hit a push2 rate-limit on the 2nd request; the stage order was changed afterwards, see call_log.jsonl.)"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import akshare as ak
from harness import call, bs_call, bs_logout, calls_used, OUT, LOGS, bs_code, sina_code, BudgetExceeded, Push2Breaker

S, E = "20080101", "20261113"
BS_FIELDS = "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST"
smp = pd.read_csv(OUT / "sample_list.csv", dtype=str)
core = smp[smp.tier == "core"].code.tolist()
light = smp[smp.tier == "light"].code.tolist()
SUB = ["600519", "000651", "600036", "601318", "000002", "300750", "688111", "000792", "300104", "600485", "600005", "001872"]
stage = sys.argv[1]
br = Push2Breaker()
try:
    if stage == "A":
        for c in core + light:
            bs_call("query_history_k_data_plus", bs_code(c), BS_FIELDS, start_date="2008-01-01", end_date="2026-11-13",
                    frequency="d", adjustflag="3", group="bs_raw")
        for c in core:
            bs_call("query_adjust_factor", bs_code(c), start_date="2008-01-01", end_date="2026-11-13", group="bs_factor")
        for c in SUB:
            bs_call("query_history_k_data_plus", bs_code(c), "date,code,open,high,low,close,preclose", start_date="2008-01-01",
                    end_date="2026-11-13", frequency="d", adjustflag="1", group="bs_hfq")
        for c in ["600519", "600036", "000651"]:
            for y in ["2015", "2023"]:
                bs_call("query_dividend_data", code=bs_code(c), year=y, yearType="operate", group="bs_div")
    if stage == "B":
        for c in core:
            call("stock_fhps_detail_em", ak.stock_fhps_detail_em, c, group="em_fhps")
        for c in SUB:
            call("stock_zh_a_daily_sina", ak.stock_zh_a_daily_sina, sina_code(c), S, E, "", group="sina_raw")
            call("stock_zh_a_daily_sina", ak.stock_zh_a_daily_sina, sina_code(c), S, E, "hfq-factor", group="sina_factor")
            call("stock_history_dividend_detail", ak.stock_history_dividend_detail, c, "分红", "", group="sina_div")
        call("stock_history_dividend_detail", ak.stock_history_dividend_detail, "600036", "配股", "", group="sina_div")
    if stage == "C":
        order = ["600519", "300104"] + [c for c in core + light if c not in ("600519", "300104", "600000")]
        for c in order:
            br.call("stock_zh_a_hist_em", ak.stock_zh_a_hist_em, c, "daily", S, E, "", group="em_raw")
        for c in SUB + [c for c in core if c not in SUB]:
            br.call("stock_zh_a_hist_em", ak.stock_zh_a_hist_em, c, "daily", S, E, "hfq", group="em_hfq")
        for c in SUB:
            br.call("stock_zh_a_hist_em", ak.stock_zh_a_hist_em, c, "daily", S, E, "qfq", group="em_qfq")
        (LOGS / "push2_breaker.json").write_text(json.dumps({"trips": br.trips, "dead": br.dead, "skipped": br.skipped}, ensure_ascii=False), encoding="utf-8")
    if stage == "D":
        for c in ["600519", "000651", "300104", "600036"]:
            call("stock_zh_a_hist_tx", ak.stock_zh_a_hist_tx, sina_code(c), "20190101", "20201231", "", group="tx_raw")
except BudgetExceeded as e:
    print("STOP:", e)
bs_logout()
print("stage", stage, "calls used", calls_used(), "push2 trips", br.trips, "dead", br.dead, "skipped", len(br.skipped))

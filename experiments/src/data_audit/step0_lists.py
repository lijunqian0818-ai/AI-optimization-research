"""Step 0: reference lists (exchange delisting lists, BaoStock basic table, trade calendar) + connectivity probe."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import akshare as ak
from harness import call, bs_call, bs_logout, calls_used

sh = call("stock_info_sh_delist", ak.stock_info_sh_delist, "全部", group="lists")
sz = call("stock_info_sz_delist", ak.stock_info_sz_delist, "终止上市公司", group="lists")
basic = bs_call("query_stock_basic", group="lists")
cal = bs_call("query_trade_dates", start_date="2008-01-01", end_date="2026-11-13", group="lists")
for n, d in [("sh_delist", sh), ("sz_delist", sz), ("bs_basic", basic), ("bs_cal", cal)]:
    print("==", n, None if d is None else d.shape)
    if d is not None: print(d.head(5).to_string()); print(d.tail(3).to_string())
p = call("stock_zh_a_hist_em", ak.stock_zh_a_hist_em, "600000", "daily", "20080101", "20261113", "", group="probe")
print("em hist 600000:", None if p is None else (p.shape, p.head(2).to_string(), p.tail(2).to_string()))
bs_logout(); print("calls used", calls_used())

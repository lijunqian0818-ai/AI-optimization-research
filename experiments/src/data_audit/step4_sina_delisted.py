"""Step 4: because the Eastmoney quote host (push2his) rate-limited every attempt but one, the A1 check for the AKShare side is
repeated on AKShare's Sina interface for all sampled delisted names; then one last probe of the Eastmoney host (alive + delisted name)."""
import sys, time
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import akshare as ak
from harness import call, calls_used, OUT, sina_code, BudgetExceeded, clear_failed

S, E = "20080101", "20261113"
smp = pd.read_csv(OUT / "sample_list.csv", dtype=str)
dl = smp[smp.exch_delist_date.notna()].code.tolist()
try:
    for c in dl:
        call("stock_zh_a_daily_sina", ak.stock_zh_a_daily_sina, sina_code(c), S, E, "", group="sina_raw")
        time.sleep(1.0)
    for c in ["600519", "300104"]:
        clear_failed("stock_zh_a_hist_em", c, "daily", S, E, "")
        call("stock_zh_a_hist_em", ak.stock_zh_a_hist_em, c, "daily", S, E, "", group="em_raw", _net_retries=0)
        time.sleep(5)
except BudgetExceeded as e:
    print("STOP:", e)
print("step4 calls used", calls_used())

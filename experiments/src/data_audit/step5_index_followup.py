"""Step 5: follow-up on two index observations of step 3 (no change at 2021-06-15; updateDate 2022-08-01 returned for 2022-12-12)."""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from harness import bs_call, bs_logout, calls_used
prev = None
for d in ["2021-06-11", "2021-06-15", "2021-06-21", "2021-06-28", "2022-06-10", "2022-06-13", "2022-07-25", "2022-08-08", "2022-12-12", "2022-12-19", "2023-01-03", "2023-06-12"]:
    x = bs_call("query_hs300_stocks", date=d, group="bs_index")
    s = set(x.code)
    print(d, len(x), sorted(x.updateDate.unique()), "changed vs previous query:", None if prev is None else len(s - prev))
    prev = s
bs_logout(); print("calls used", calls_used())

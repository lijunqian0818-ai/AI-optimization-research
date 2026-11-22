import sys, os
sys.path.insert(0, r"C:\Users\lijun\Desktop\AI-Optimization-Research\experiments\src")
import pandas as pd, pyarrow.parquet as pq
from features import panel, store
from features.timing import TradingCalendar
out = sys.argv[1]
st = store.RawStore()
d = pd.read_parquet(os.path.join(st.root, "universe", "bs_trade_dates.parquet"))
d = d[d["calendar_date"] <= "2021-12-31"]
cal = TradingCalendar(d.loc[d["is_trading_day"].astype(str) == "1", "calendar_date"])
codes = [("sh." if s.startswith("6") else "sz.") + s for s in (l.split("#")[0].strip() for l in open(r"C:\Users\lijun\Desktop\AI-Optimization-Research\experiments\results\data_fetch\trial_codes.txt", encoding="utf-8")) if s]
frames = []
for c in codes:
    raw = pd.read_parquet(os.path.join(st.root, "bars", "bs_daily", c + ".parquet"), filters=[("date", "<=", "2021-12-31")])
    ic = panel.proxy_index_code(c)
    ri = pd.read_parquet(os.path.join(st.root, "index", "bs_index_daily", ic + ".parquet"), filters=[("date", "<=", "2021-12-31")])
    f = panel.build_stock_features(c, raw, cal, cal.days[-1], ri, None, groups=("R_O",))
    f = f[[x for x in f.columns if x.startswith("ro_trig_cum3")]].copy()
    f["code"] = c
    frames.append(f.reset_index())
pd.concat(frames).to_parquet(out)
print(len(codes), sum(len(x) for x in frames))

"""Step 1: build the audit sample (seeded) and store it with the reason for each name. No network."""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
from harness import CACHE, OUT, SEED
rng = np.random.default_rng(SEED)
sh = pd.read_parquet(next(CACHE.glob("stock_info_sh_delist__*.parquet")))
sz = pd.read_parquet(next(CACHE.glob("stock_info_sz_delist__*.parquet")))
basic = pd.read_parquet(next(CACHE.glob("bs_query_stock_basic__*.parquet")))
sh = sh.rename(columns={"公司代码": "code", "公司简称": "name", "上市日期": "list_date", "暂停上市日期": "delist_date"})
sz = sz.rename(columns={"证券代码": "code", "证券简称": "name", "上市日期": "list_date", "终止上市日期": "delist_date"})
sh["src"] = "SSE 终止上市公司列表 (query.sse.com.cn, via ak.stock_info_sh_delist)"
sz["src"] = "SZSE 终止上市公司列表 (www.szse.cn, via ak.stock_info_sz_delist)"
dl = pd.concat([sh, sz], ignore_index=True)[["code", "name", "list_date", "delist_date", "src"]]
dl["delist_date"] = pd.to_datetime(dl["delist_date"]); dl["list_date"] = pd.to_datetime(dl["list_date"])
dl.to_csv(OUT / "delist_lists_exchange.csv", index=False, encoding="utf-8-sig")
a = dl[dl.code.str.match(r"^(60|68|00|30)")]            # A shares only (drop 900 / 200 B shares)
frame = a[(a.delist_date >= "2010-01-01") & (a.delist_date <= "2025-12-31")]
print("delisted A-share frame 2010-2025:", len(frame), "| SH", (frame.code.str[0] == "6").sum(), "SZ", (frame.code.str[0] != "6").sum())
print(frame.groupby(frame.delist_date.dt.year).size().to_string())
# 30 random delisted names, stratified by exchange (15 / 15)
pick_sh = frame[frame.code.str[0] == "6"].sample(15, random_state=SEED)
pick_sz = frame[frame.code.str[0] != "6"].sample(15, random_state=SEED + 1)
rand_del = pd.concat([pick_sh, pick_sz])
hand = [  # (code, categories, reason) -- hand-picked informative cases; delisted ones must also be in the exchange lists
 ("300104", "delisted,chinext,long_susp,st", "乐视网: 创业板, 长期停牌(2017-2018), 2020 退市; 可行性报告里的退市样例"),
 ("600485", "delisted,main,long_susp,st", "信威集团: 2016-12 起停牌约两年半, 复牌后连续跌停, 2021 退市 (A15 对抗性样例)"),
 ("002450", "delisted,main,st", "康得新: 财务造假 ST, 2021 退市"),
 ("600005", "delisted,main,merger", "武钢股份: 2017 被吸收合并而终止上市 (非强制退市, 检验 A14 终值)"),
 ("000792", "main,st,long_susp", "盐湖股份: ST -> 暂停上市 2020-05 至 2021-08 恢复上市 (长期无行情后恢复, 首日无涨跌幅限制)"),
 ("000002", "main,large,long_susp,div", "万科A: 2015-12 至 2016-07 重组停牌约半年; 大盘; 持续现金分红"),
 ("600519", "main,large,div,bonus", "贵州茅台: 高额现金分红 + 2011-2015 送股, 复权是否含现金分红的首选样例"),
 ("000651", "main,large,div,bonus", "格力电器: 高现金分红, 多次送转, 2016 停牌"),
 ("600036", "main,large,div,rights", "招商银行: 2010 / 2013 配股 (S-c 类事件) + 现金分红"),
 ("601318", "main,large,div,bonus", "中国平安: 2015 年 10 转 10"),
 ("601398", "main,large,div", "工商银行: 超大盘, 只有现金分红, 低换手 (检验换手率口径)"),
 ("000001", "main,large,div,bonus", "平安银行: 可行性报告用过; 送转 + 分红; 更名 (深发展A)"),
 ("600000", "main,large,div,bonus", "浦发银行: 连通性测试用过; 送转 + 分红"),
 ("000858", "main,large,div", "五粮液: 大盘, 现金分红"),
 ("002594", "main,large,div,bonus", "比亚迪: 2025 年送转 (样本期末的大比例送转)"),
 ("300750", "chinext,large,div,bonus", "宁德时代: 创业板大盘, 2018 上市 (10% 板 -> 2020-08 起 20%), 2023 转增"),
 ("300059", "chinext,large,div,bonus", "东方财富: 创业板, 多次送转, 跨 2020-08 涨跌幅制度变更"),
 ("300015", "chinext,div,bonus", "爱尔眼科: 创业板, 多次送转"),
 ("688981", "star,large,new_at_ipo", "中芯国际: 科创板 2020 上市 (前 5 日无涨跌幅限制, 20% 板)"),
 ("688111", "star,div,bonus", "金山办公: 科创板 2019 上市, 有分红与转增"),
 ("688599", "star,div", "天合光能: 科创板 2020 上市"),
 ("688009", "star,large,div", "中国通号: 科创板首批 (2019-07-22)"),
 ("001872", "main,code_change", "招商港口: 原深赤湾A (000022), 2018 年变更证券代码 (检验历史代码 / OA9)"),
 ("601360", "main,name_change,long_susp", "三六零: 原江南嘉捷, 2017 借壳长期停牌并更名"),
 ("600710", "main,st", "苏美达: 原 *ST 常林, 经历 ST 与重组摘帽"),
 ("000725", "main,large,lowprice", "京东方A: 大盘低价股 (涨跌停价取整的分辨率最敏感)"),
 ("601899", "main,large,div,bonus", "紫金矿业: 大盘低价, 2011 年 10 转 5"),
]
hand_df = pd.DataFrame(hand, columns=["code", "cats", "reason"])
# survivors: random small caps and recent IPOs from the BaoStock basic table (type 1 = stock, status 1 = listed)
st = basic[(basic.type == "1")].copy(); st["c"] = st.code.str[3:]
alive = st[(st.status == "1") & st.c.str.match(r"^(60|68|00|30)")]
old = alive[(alive.ipoDate < "2012-01-01")]
rand_old = old.sample(6, random_state=SEED + 2)
new = alive[(alive.ipoDate >= "2025-01-01")].sample(3, random_state=SEED + 3)
mid = alive[(alive.ipoDate >= "2020-09-01") & (alive.ipoDate < "2023-01-01") & alive.c.str.startswith("30")].sample(2, random_state=SEED + 4)
rows = []
for _, r in hand_df.iterrows(): rows.append((r.code, r.cats, r.reason, "hand", "core"))
for _, r in rand_old.iterrows(): rows.append((r.c, "random_old", f"随机抽取的 2012 年前上市存续股 ({r.code_name}, ipo {r.ipoDate}); 多为普通中小盘", "random", "core"))
for _, r in new.iterrows(): rows.append((r.c, "new", f"随机抽取的 2025 年起上市新股 ({r.code_name}, ipo {r.ipoDate})", "random", "core"))
for _, r in mid.iterrows(): rows.append((r.c, "chinext,new_at_ipo", f"随机抽取的注册制创业板新股 ({r.code_name}, ipo {r.ipoDate}); 上市前 5 日无涨跌幅限制", "random", "core"))
have = {r[0] for r in rows}
k = 0
for _, r in rand_del.iterrows():
    if r.code in have: continue
    tier = "core" if k < 8 else "light"; k += 1
    rows.append((r.code, "delisted,random", f"交易所终止上市列表随机抽取 ({r['name']}, 终止上市 {r.delist_date.date()})", "random", tier))
smp = pd.DataFrame(rows, columns=["code", "cats", "reason", "how", "tier"])
smp = smp.merge(dl.drop_duplicates("code")[["code", "name", "list_date", "delist_date"]].rename(columns={"name": "exch_delist_name", "list_date": "exch_list_date", "delist_date": "exch_delist_date"}), on="code", how="left")
b = st.set_index("c")[["code_name", "ipoDate", "outDate", "status"]]
smp = smp.join(b, on="code")
smp.to_csv(OUT / "sample_list.csv", index=False, encoding="utf-8-sig")
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 40)
print(smp.drop(columns=["reason"]).to_string())
print("n =", len(smp), "core", (smp.tier == "core").sum(), "| delisted (exchange list):", smp.exch_delist_date.notna().sum(), "| missing in BaoStock basic:", smp.code_name.isna().sum())
print("BaoStock basic: stocks type1", len(st), "status0 (delisted)", (st.status == "0").sum())

# 全量数据抓取：使用说明与估算

> researcher，2026-11-15。对应 `experiments/PLAN.md` v0.6 §2.1、§2.2、§2.3（U-LIQ）、§2.5、§3.11。
> **全量抓取尚未启动**；本文件里的数字全部来自 2026-11-15 17:06–17:32 的一次小规模试跑（20 只股票，共 335 次请求：BaoStock 查询 168 次、HTTP 请求 167 次，上限 400）。逐条记录在 `manifest.jsonl`，可用 `--status` 重新汇总。
> 抓取程序只抓原始数据：不清洗、不合并、不算特征。没有训练模型，没有回测。

## 1. 文件位置

```
experiments/src/data_fetch/
  run_fetch.py          入口
  core.py               限速、BaoStock 会话、manifest、可续传的执行循环
  sources.py            六个 stage 的请求清单（每个"单元"= 一个落盘文件）
  selftest_offline.py   不联网的自检（重试、失败记录、暂停、停止、续传、文件被改后重抓）
experiments/data/raw/                     原始数据（Parquet；抓取元数据写在每个文件的 schema metadata 的 fetch_meta 里）
  universe/   bs_stock_basic, bs_trade_dates, bs_stock_industry, sse_delist, szse_delist, a_share_worklist.csv
  bars/bs_daily/<代码>.parquet
  factors_events/{bs_adjust_factor,bs_dividend,em_fhps,sina_dividend,sina_rights}/<代码>.parquet   四源分开存，不合并
  index/{bs_index_daily/<指数>,bs_hs300/<日期>,bs_zz500/<日期>}.parquet
  crosscheck/sina_daily/<代码>.parquet
  zo/{lhb_detail,lhb_jgmmtj,dzjy_mrtj,dzjy_mrmx}/<YYYYMM>.parquet, zo/ins_raw/<公告年>.parquet
experiments/results/data_fetch/
  manifest.jsonl        每个 (stage, source, 单元) 每次运行一条记录（只追加）
  universe_summary.json 股票池清单的计数与完整性核对
  logs/<stage>_<时间>.log   每次运行的日志（与屏幕输出相同）
  state/                主机锁文件、各 HTTP 主机当日请求计数
  trial_codes.txt       试跑用的 20 只
```

`manifest.jsonl` 每条记录的字段：`ts`、`run_id`、`stage`、`source`、`unit`、`ok`、`status`（ok / empty / failed）、`rows`、`cols`、`date_min`、`date_max`、`elapsed_s`（含重试等待）、`fetch_s`（最后一次尝试）、`attempts`、`n_bs_queries`、`n_http`、`error`（每次失败尝试的报错）、`file`、`bytes`、`sha256`、`params`、`params_hash`、`versions`、`extra`。

唯一的派生文件是 `universe/a_share_worklist.csv`：从 BaoStock 基本信息表里按"证券类型 = 股票、A 股代码前缀、2008-01-01 至 2026-06-30 期间上市过"筛出的清单，其他 stage 靠它知道要请求哪些代码。它不是清洗后的数据。

## 2. 启动、续传、看进度

所有命令在项目根目录运行。

- **看进度（不发请求）：** `experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --status`
- **看某个 stage 还剩多少（不发请求）：** 在该 stage 的命令后加 `--plan`
- **续传：** 原样重跑同一条命令。已落盘、且文件 sha256 与 manifest 一致、且参数相同的单元跳过；失败的单元自动重试；被记为"空"的单元默认不重抓（加 `--retry-empty` 才重抓）。
- **中断：** 可以随时结束进程（Ctrl+C 或直接杀进程）。文件先写临时文件再改名，manifest 每个单元写完即落盘，最多丢正在抓的那一个单元。
- **日志里的进度行**（每 20 个单元或每 5 分钟一行）：`[progress] bars: done=已完成/总数 (this run …: ok= empty= failed=; resumed-skip=) success=成功率 mean=每单元秒数 ETA=预计剩余 requests …`
- **退出码：** 0 全部完成；1 跑完但有失败单元（重跑即重试）；3 达到 `--max-requests`；4 连续失败、暂停次数用完后停止（上游可能在封锁）；5 另一个进程正在用同一上游主机；130 被 Ctrl+C 中断。

### 各 stage 的启动命令

```
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage universe
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage bars
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage index
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage factors_events --source bs_factor,bs_dividend
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage zo
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage factors_events --source em_fhps
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage factors_events --source sina_dividend,sina_rights
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage crosscheck --codes-file <曾入选股票池的代码清单.txt>
```

`universe` 已在试跑中跑完（见 §4），不需要再跑；重跑会被续传跳过。
`--codes-file`（一行一个代码，`600000` 或 `sh.600000` 均可，`#` 起注释）对 bars / factors_events / crosscheck 都有效；`--limit N` 只取清单的前 N 只。对按日期抓的来源（index 的成分快照、zo），`--limit N` 表示每个来源取均匀间隔的 N 个单元（试跑用）。

### 建议的运行顺序

同一上游主机只允许一个进程（程序用锁文件强制，抢不到锁以退出码 5 退出）；不同主机可以并行（PLAN §2.5）。

| 进程 | 主机 | 顺序 |
|---|---|---|
| A | BaoStock | `bars` → `index` → `factors_events --source bs_factor,bs_dividend` |
| B | 东方财富数据中心 | `zo` → `factors_events --source em_fhps` |
| C | 新浪 | `factors_events --source sina_dividend,sina_rights` →（清单有了以后）`crosscheck` |

- `crosscheck` 需要"曾进入股票池的代码清单"。这份清单要等 `bars` 抓完、按 PLAN §2.3 做完每月流动性筛选才有；**筛选不属于抓取程序，本任务没有做**。不给 `--codes-file` 时该 stage 拒绝运行（`--all-names` 可强制抓全市场，PLAN 没有这样规定）。
- PLAN §2.5 写的是事件表只需抓"曾进入股票池的股票"。上面的命令默认抓全部 5,478 只；若想按 PLAN 缩小，等清单出来后给 `factors_events` 加 `--codes-file`。`bs_dividend` 是最耗时的一项（见 §5），是否抓全市场请组长定。

## 3. 限速与失败处理（参数及依据）

| 参数 | 默认值 | 依据 |
|---|---|---|
| `--bs-gap` | 1.0 秒 | PLAN §2.5："BaoStock 单会话、顺序查询、间隔至少 1 秒"。试跑 168 次查询在此间隔下 0 次网络失败（8 次失败全是我传错代码，见 §6-1） |
| `--http-gap` | 1.5 秒（同一主机相邻两次 HTTP 请求） | PLAN §2.5 的关卡 2 采用值。冒烟审计用 0.6–1 秒，除东财 push2 外 402 次首次请求失败 2 次；本次 167 次 HTTP 请求首次失败 1 次（深交所连接被重置，重试成功） |
| `--http-daily-cap` | 每主机每自然日 3,000 次 | PLAN §2.5。到上限后程序睡到次日 00:01 再继续 |
| `--daily-unit-cap` | crosscheck 为 1,000 只 / 日，其余无 | PLAN §2.5："新浪每天至多 1,000 只（占位值）" |
| `--backoff` | 5,20,60 秒，至多重试 3 次 | PLAN §2.5 |
| `--max-consec-fail` / `--pause-seconds` / `--max-pauses` | 连续 5 个单元失败 → 暂停 1,800 秒；暂停满 6 次后停止（退出码 4）。crosscheck：连续 3 个失败即停止，不暂停 | 阈值与时长是我定的占位值（任务要求写成参数）。crosscheck 的取值对应 PLAN "新浪出现封锁迹象即停" |
| `--ratelimit-wait` | 330 秒 | PLAN §2.5：AKShare 抛出限流异常时不退避重试，直接等 330 秒并计一次暂停 |
| `--bs-timeout` | 180 秒 | BaoStock 库的 socket 不设超时，断线会永久挂起；这里设了全局 socket 超时 |
| `--bs-relogin-every` / `--bs-relogin-minutes` | 每 400 次查询或 25 分钟主动重新登录 | 我定的保守值；任何查询出错后也会先登出、下次查询前重新登录 |
| `--max-requests` | 0（不限） | 试跑时用来限制请求数 |
| `--start` / `--end` | 2008-01-01 / 2026-06-30 | PLAN §2.2 |

单线程顺序请求，没有并发。AKShare 同一单元内对同一地址的重复 GET（它先取第 1 页看页数、再从第 1 页取起；新浪分红与配股是同一个网页）只发一次。

"空"与"失败"的区分：AKShare 在东财返回"无数据"时抛 TypeError。只有当最后一次 HTTP 应答是 200 且带东财的空结果标记（`"result":null` / `返回数据为空` / `9201`）时才记为 `empty`，否则按失败重试。BaoStock 返回 0 行记为 `empty`。

## 4. 试跑结果（`--limit 20`，2026-11-15）

试跑的 20 只（`trial_codes.txt`）：退市 4（乐视网 300104、信威 600485、康得新 002450、武钢 600005）、科创板 3（688111、688981、689009）、创业板 4（300750、300059、301001、302132）、ST / 曾 ST 2（*ST 九鼎 600053、盐湖 000792）、主板 7（含代码变更的招商港口 001872、两次配股的招商银行 600036）。

| stage / 来源 | 单元 | 结果 | 行数 | 每单元秒数（均值；最小–最大） | 请求数 |
|---|---|---|---|---|---|
| universe（5 个表） | 5 | 5 成功；深交所退市名单第 1 次连接被重置，重试成功 | — | 2.6–57.2 | BaoStock 3，HTTP 3 |
| bars / bs_daily | 20 | 20 成功 | 65,513 | 6.49（2.5–9.5） | 20（另有 8 次是我的错误造成的失败请求，§6-1） |
| factors_events / bs_factor | 20 | 20 成功 | 242 | 3.42（1.8–6.7） | 20 |
| factors_events / bs_dividend（只查 2019–2023 年；另对武钢查 2008–2016） | 20 + 1 | 12 有记录，8 为空（7 只这几年确实没有分红记录返回，武钢 2017 年已退市所以无年份可查）；武钢 2008–2016 返回 8 条、派息日齐全 | 59 + 8 | 每次查询 2.55 秒（93 次查询） | 93 |
| factors_events / em_fhps | 20 | 15 有记录，5 为空（4 只退市股 + 中芯国际），均为东财的"返回数据为空" | 288 | 3.17 | 20 |
| factors_events / sina_dividend + sina_rights | 40 | 分红表 20 成功（退市股有记录）；配股表 5 有记录、15 为空 | 397 + 8 | 3.27（每只一次请求，两表共用） | 20 |
| index / bs_index_daily | 8 | 7 成功，**中证全指 sh.000985 返回 0 行** | 30,612 | 12.8 | 8 |
| index / bs_hs300、bs_zz500 | 8 + 8 | 全部成功，每次 300 / 500 行 | 2,400 + 4,000 | 4.31 / 3.29 | 16 |
| crosscheck / sina_daily | 20 | 20 成功 | 58,909 | 6.14（4.6–7.2） | 40 |
| zo / lhb_detail | 4 个月 | 成功 | 5,387 | 每次 HTTP 请求 4.04 秒 | 24（含验证去重的 2 次重抓） |
| zo / lhb_jgmmtj | 4 个月 | 成功 | 2,328 | 3.97 秒 / 请求 | 10 |
| zo / dzjy_mrtj、dzjy_mrmx | 4 + 4 个月 | 成功 | 2,493 + 5,226 | 3.68 / 4.77 秒 | 4 + 6 |
| zo / ins_raw（公告年 1994、2005、2015、2026 + 总数） | 5 | 成功；每年的行数与上游报告的 count 一致；上游全表 147,458 行 | 18,070 | 4.06 秒 / 请求 | 40 |

断点续传与失败记录：
- bars 先用 `--max-requests 7` 跑到中途停下，重跑时跳过 7 只、只抓剩下 13 只。
- index 运行中被强制杀进程（已完成 12 个单元），重跑时跳过 12 个、抓剩下 12 个；没有残留的临时文件。
- 六个 stage 全部跑完后各原样重跑一次：发出的请求数都是 0。
- 失败记录：深交所那次失败后重试成功（`attempts` = 2，报错留在 `error`）；我自己的错误造成的 2 个失败单元各 4 次尝试，都在 manifest 里。
- 暂停 / 停止 / 文件被改后重抓这几条路径只在不联网的自检里验证过（`selftest_offline.py`，通过）。"到每日上限后睡到次日"和"每 400 次查询主动重新登录"**没有被实际触发过**。

数据核对（只做了行数层面的检查，没有核对数值）：20 只的日线行数与"上市日（或 2008-01-02）到退市日（或 2026-06-30）之间的交易日数"相比，18 只完全相等，2 只各少 1 行（§6-3）。

## 5. 全量估算

**实际证券只数（`universe_summary.json`）：** BaoStock 基本信息表 9,038 行，其中类型为股票的 5,566 只，全部是沪深 A 股代码前缀（表里没有 B 股和北交所股票）。去掉 2008-01-01 前已退市的 57 只和 2026-06-30 后上市的 31 只，**清单 N = 5,478 只**（沪 2,429、深 3,049；沪主板 1,816、深主板 1,609、创业板 1,440、科创板 613）；其中 2026-06-30 前已退市 273 只。两家交易所终止上市名单里 2008 年以来终止上市的 A 股（沪 127、深 159）全部在清单内，缺 0 只。基本信息表是 2026-11-15 的版本。

估算方法：单元数来自 `--plan`（按实际清单与交易日历数出来的）；每单元耗时用上表的试跑均值。

| stage / 来源 | 单元数 | 请求数 | 按试跑速度的耗时 | 区间与说明 | 磁盘 |
|---|---|---|---|---|---|
| bars | 5,478 | 5,478 | 按行数折算 8.2 小时（全量预计 1,496 万行；试跑 65,513 行用 129.9 秒）；按只数折算 9.9 小时 | **8–39 小时。** 上限用的是冒烟审计当天下午实测的 25.5 秒 / 只（5,478 × 25.5 秒 = 38.8 小时）。同一天、同一台机器，两次实测相差约 4 倍，原因不明；全量时落在哪一头无法预知 | 约 630 MB |
| index | 8 + 947 × 2 | 1,902 | 2.0 小时 | 1.5–4 小时（同上，BaoStock 速度不稳） | 约 17 MB |
| factors_events / bs_factor | 5,478 | 5,478 | 5.2 小时 | PLAN 说因子表只用于审计报告；可只抓子样本 | 约 25 MB |
| factors_events / bs_dividend | 5,478 | **66,390**（每只每个上市年份一次，平均 12.1 年） | **47 小时** | 40–60 小时。每 1,000 只约 8.6 小时。按 PLAN 只抓曾入选股票池的股票可按比例缩短 | 约 60 MB |
| factors_events / em_fhps | 5,478 | 5,478 | 净耗时 4.8 小时 | 受每日 3,000 次上限约束，跨 2 个自然日（与 zo 同主机，合计约 7,300 次，跨 3 个自然日） | 约 70 MB |
| factors_events / sina_dividend + sina_rights | 10,956 | 5,478 | 净耗时 5.0 小时 | 受每日 3,000 次上限约束，跨 2 个自然日 | 约 50 MB |
| crosscheck | 取决于清单 | 每只 2 次 | 每 1,000 只 1.7 小时 | 每日上限 1,000 只：清单有几千只就要几天。若抓全市场 5,478 只：10,956 次请求、净耗时 9.3 小时、跨 6 个自然日 | 每 1,000 只约 110 MB |
| zo | 4 × 222 个月 + 34 | 约 1,800（1,500–2,500） | 约 2.1 小时 | 1.5–3 小时。请求数取决于每月行数（龙虎榜每页 500 行）；只抽了 4 个月，外推粗 | 约 85 MB |
| universe | 5 | 6 | 已完成（1.9 分钟） | — | 0.3 MB |

合计：
- **BaoStock 一条线（bars → index → bs_factor → bs_dividend）：约 62–93 小时（2.6–3.9 天）**，其中 bs_dividend 占 47 小时。这个区间只计入了 bars 的速度不确定性（8.2 对 38.8 小时），其余各项按试跑均值；如果 BaoStock 整体变慢，其余各项也会相应变长。只跑 bars + index 是 10–43 小时。
- 东财一条线（zo → em_fhps）：净耗时约 7 小时，因每日上限跨 3 个自然日。
- 新浪一条线（分红配股）：净耗时约 5 小时，跨 2 个自然日；crosscheck 另算。
- 三条线并行时，总挂机时间由 BaoStock 一条线决定。
- 磁盘：不含 crosscheck 约 0.9 GB；加上全市场 crosscheck 不超过 1.5 GB。
- 请求总数（全市场、不含 crosscheck）：BaoStock 约 79,200 次查询，东财约 7,300 次，新浪约 5,500 次。

主要风险：
1. BaoStock 响应速度不稳（上面的 4 倍差）。耗时区间很宽，这是实测结果，不是保守估计。
2. 试跑是周日傍晚做的；交易日白天上游的速度和限流可能不同，**未测**。
3. 新浪：试跑 60 次请求（行情 40、分红 20）没有被封；几千次的量级**未测**。AKShare 源码注明该行情接口"大量抓取容易封 IP"。
4. 东财数据中心：试跑 104 次请求 0 失败；7,000 次量级**未测**。
5. 长时间无人值守：电脑睡眠 / 休眠会让进程停住（恢复后 BaoStock 连接超时，会重连续跑，但睡着的时间白费）。需要关掉自动睡眠。
6. 首次失败率：试跑 327 次有效请求里 1 次（0.3%，重试成功）。样本小，不能据此断言全量的失败率。

## 6. 已知问题

1. **manifest 里有 2 条垃圾失败记录**（`bars/bs_daily/sz.trial`、`sz.list`）。我第一版读代码清单时把注释行里的单词当成了代码，发出 8 次无效的 BaoStock 查询（都被服务器以"代码应为 9 位"拒绝）。已修复（代码清单现在逐行解析并校验格式；参数错误不再重试）。这两条记录保留在 manifest 里（只追加），`--status` 会一直把它们列为失败，可以忽略——它们不在任何清单里，不会被重试。
2. **BaoStock 没有中证全指（sh.000985）的行情**：返回 0 行，记为 `empty`。指数清单是我选的（上证综指、沪深 300、中证 500、中证 1000、中证全指、上证 50、深证成指、创业板指）——PLAN 没有列出需要哪些指数，只说指数成分用于描述性表格。
3. **两只代码变更过的股票各少 1 个交易日的行**：招商港口 001872 与中航成飞 302132 都缺 2012-09-10。冒烟审计里"招商港口 2012-09-11 的 preclose 与前收盘不等、原因不明"可能就是因为前一天的行缺失——这是推测，未核实。全量抓完后应对每只股票做"行数对交易日数"的检查。
4. **新浪对代码变更股只有变更后的历史**：招商港口新浪 1,818 行（2018-12-26 起），BaoStock 是 4,491 行（2008 年起）。交叉核对这类股票要另外用旧代码抓，程序没有做代码映射（PLAN OA9）。
5. **新浪日线不是完全的原始返回**：AKShare 的函数会删掉上游的 `prevclose` 字段、对同一日期只留一行。乐视网的新浪数据里仍有审计报告提到的 2021-06-27 那一行。
6. **ins_raw 没有走 AKShare 的函数**：`stock_ggcg_em` 只能一次翻完约 295 页，无法续传；改为直接请求它所用的同一个上游表（`RPT_SHARE_HOLDER_INCREASE`，同样的排序，全部字段），按公告年份分单元，并核对行数与上游 count。这是对"Z_O 用 AKShare"的一处偏离，数据来源相同。返回里含 `NEWEST_PRICE`、`CHANGE_RATE_QUOTES`、`CLOSE_PRICE` 等字段，按 PLAN OA2 白名单使用时必须排除。按公告年 1994 年起抓；公告日为空或早于 1994 年的行（若有）会漏掉——全部年份抓完后，用各年行数之和对 `TOTAL_count`（147,458）即可检查，**试跑只抓了 4 个年份，没有做这项检查**。
7. **龙虎榜、大宗交易经 AKShare 取回的是它挑选并改名后的列**，不是上游全部字段。龙虎榜表里有"上榜后 N 日""解读"等事后字段，抓取阶段原样保存，使用时按 OA2 排除。
8. **大宗交易两个接口不翻页**（一次请求、每页 5,000 行）。程序在返回 ≥ 5,000 行时会把该月拆成上下半月重抓，半月仍 ≥ 5,000 行则记为失败、不落盘。试跑的 4 个月最多 3,356 行，**拆分这条路径没有被触发过**。
9. **bs_dividend 按"除权除息年份"查询**（`yearType="operate"`）：只有预案、还没有除权除息日的分红不会出现。年份范围是每只股票的上市年到退市年（与 2008–2026 取交集）。试跑为了省请求只查了 2019–2023 年；全量运行参数不同，这 20 只会重抓（设计如此）。
10. **东财分红表对退市股为空**：试跑 4 只退市股 4 只为空，与审计报告一致；另有中芯国际为空。
11. **行业分类表是当前快照**（`bs_stock_industry`，更新日期 2026-11-09），不是历史时点数据。板块按代码前缀标注；302 开头的前缀归为创业板是我的判断，未核实。
12. **清单的截止日是 2026-06-30**（PLAN §2.2）：此后上市的 31 只不在清单里；此后退市的 12 只在清单里，行情抓到 2026-06-30。
13. **续传开始时要对已落盘文件逐个算 sha256**。20 只时不到 1 秒；5,478 个文件（约 630 MB）要多久**未测**。
14. **没有实现**：腾讯日线抽样（PLAN §2.1 提到的第三来源）、交易所官网原文（OA10）、OA6 / A13 的第二次抓取。全量抓取的"首个快照哈希"可由 manifest 里每个文件的 sha256 汇总得到，本任务没有生成汇总哈希。
15. 没有读到写给自动化程序的指令。

## 7. 复现试跑

```
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/selftest_offline.py
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage universe
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage bars --limit 20 --codes-file experiments/results/data_fetch/trial_codes.txt
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage factors_events --limit 20 --codes-file experiments/results/data_fetch/trial_codes.txt --div-years 2019:2023
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage index --limit 8
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage crosscheck --limit 20 --codes-file experiments/results/data_fetch/trial_codes.txt
experiments/.venv/Scripts/python.exe experiments/src/data_fetch/run_fetch.py --stage zo --limit 4
```

已落盘的单元会被跳过；要重新发请求须加 `--no-resume`，结果取决于上游当时的状态。

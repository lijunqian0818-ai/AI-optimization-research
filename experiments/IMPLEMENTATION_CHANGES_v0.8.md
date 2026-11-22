# 实现修改任务书（对应 PLAN v0.8 的裁决）

> researcher，2026-11-15。依据：`experiments/PLAN.md` v0.8 的 "Revision log (v0.7 → v0.8)"（H-1…H-16、J-1…J-15、U-PILOT）。
> **本文件只是任务书：没有改任何代码，没有运行任何测试，没有向数据源发请求。** 代码位置取自对 `engine/event_table.py`、`engine/simulate.py`、`engine/rule_calendar.py`、`features/controls.py`、`features/config.py` 相关段落的阅读；其余"现状"以两份测试报告为准，动手前请核对源码。本文件未经其他模型审查。
> PLAN 与本文件不一致时以 PLAN v0.8 为准。v0.7 任务书 §0 的六条要求（不看结果、不碰抓取进程、命令被拒即停、改期望前先判断、参数进 config 并标注裁决编号、更新测试报告）继续适用；标注写"PLAN v0.8 裁决 X-n"。

**本轮确认了实现者读法的条目（不需要改代码）：** H-1、H-3 – H-13、H-15、H-16；J-2 – J-6、J-8 – J-14。下表只列需要改的。

优先级：**P0** = 试点（PLAN §13A）开跑之前必须完成；**P1** = Freeze-1 之前；**P2** = 有条件。

| 编号 | 裁决 | 模块 / 函数 | 改成什么行为 | 测试 | 优先级 |
|---|---|---|---|---|---|
| C-1 | H-2 | `engine/event_table.py` 的 `build`（规则 2、3、6 那一段与 rule 9 之前） | **新增规则 2a "由参考价确认"**：某 (code, ex-date) 没有两源一致（`pair is None`）且**没有同源重复行**（`dup` 为假）时，对每个来源的取值算隐含参考价 (prev_close − g)/(1 + bonus)；参考步取 ex-date 当日的 EV4 步，若 ex-date 那天无成交则取其后首个成交日的未解释步（与规则 9(a) 相同的取法）。**恰有一个**来源的值与该步 `preclose` 之差 ≤ `ev_tol_flag`（0.005 元），且对 S-a/S-b 登记日 = 除权日前一交易日 ⇒ 状态 `confirmed_by_price`，按该来源取值记账，打标记 `"single source / disagreement, confirmed by the reference price"`，新计数 `confirmed_by_price_single`、`confirmed_by_price_disagreement`；0 个或 ≥ 2 个来源符合 ⇒ 维持现在的 `unconfirmed`（走待核对规则 U）。已经由规则 2 确认的事件不受影响（规则 6 的 0.02 元检查照旧，超限仍转 `unconfirmed`）。**生产配置**固定为 `resolutions=None`、`pending="U"`、`undated_rights="exclude"`，写进 `config`（标注 PLAN v0.8 H-2）；`pending="provisional"` 改名或注释为"预先声明的探索性敏感性"（不再写"never used for a result"）。计数输出补齐 PLAN §3.11 "Mechanical rule" 第 4 条列的各项（按年、按在市 / 退市） | (a) 单源事件、当日步与隐含参考价差 0.003 元 ⇒ 记账并带标记；差 0.008 ⇒ U；(b) 两源不一致、其中恰一个与步相符 ⇒ 按该源记账；两个都相符或都不相符 ⇒ U；(c) 除权日在停牌期内、复牌日步相符 ⇒ 记账且该步被解释（不重复计入 9(a)）；(d) 同源重复行 ⇒ 仍为 U；(e) 两源已确认的事件结果与 v0.7 逐位相同；(f) 试跑 20 只重跑计数（报告新的确认 / 待核对分布） | P0 |
| C-2 | H-2 | `engine/event_table.py`（读入函数） | **仅当**组长决定在 Freeze-1 之前对**完整**核对清单做人工核对时才写：把核对结论从 CSV（列：code, date, kind ∈ {event, step}, status ∈ {announcement, unclassifiable, reject, explained}, gross_cash, bonus, record_date, date_choice ∈ {event, step, undecided}, url）读成现有的 `resolutions` 字典；只用于敏感性"with hand checks" | CSV 往返与字典逐项相同 | P2（有条件） |
| C-3 | J-1 | `engine/rule_calendar.py` 的 `lhb_thr:*` 四行；`features/rules.py`（适配层）、`features/controls.py`（`t_cum`）、`features/config.py` | 每行的 value 字典增加 `"cum3"`：`kind="deviation"` 的行 0.20，`kind="change"` 的行 0.30（即现 `RO_CUM3_THRESHOLD` 的取值与现有的分段方式）；该元素的出处状态为 unverified、清单第 22 项（若一行只能有一个状态，在 `note` 里写明 "cum3: unverified, PLAN §3.10 item 22"）。特征库经适配层读取 `cum3`，删除 `config.RO_CUM3_THRESHOLD`；清单 `feature_catalog.csv` 中 `ro_trig_cum3_*` 的出处栏改为"rule calendar RC-18 cum3（unverified, item 22）" | 引擎：边界日测试覆盖新元素（2020-08-23 / 24 的创业板切换）；特征：源码中不再出现 0.20/0.30 字面量（沿用"无制度常数"测试），`ro_trig_cum3_*` 在试跑数据上与修改前逐位相同 | P0 |
| C-4 | J-7 | `features/zo.py`（BLK 部分） | 折溢率改为用自有日线重算：成交价 ÷ 该股成交当日未复权收盘价 − 1（不再读供应商折溢率列）。**合理性规则**：成交价不在当日 [P^down, P^up] 内（由自有 `preclose` 与规则日历涨跌幅、十进制四舍五入算出——调用引擎的涨跌停价函数，不复制公式），或该股当日无成交行 ⇒ 该笔"implausible"：不进入成交额加权折溢率，仍计入指示变量、days_since、成交额强度；窗口内全部为 implausible ⇒ 折溢率 NaN。输出计数（按年、交易所）；参数进 `config`（标注 U64） | (a) 手算：一笔在涨停价之上、一笔在区间内 ⇒ 折溢率只用后者；(b) 全部越界 ⇒ NaN 而指示变量为 1；(c) 重算折溢率与供应商列在正常行上的差（只描述，写入报告）；(d) 前视检测重跑 | P0 |
| C-5 | H-14 | `engine/simulate.py` / `ledger.py`（卖出记账处） | 计数：佣金（含最低佣金）超过该笔卖单成交金额的卖单数，以及因此袖套现金为负的天数；写入 `simulate.result_record` | 构造用例：一笔金额 < 5 元的卖出，计数为 1，之后该袖套的买单原因为 `no_cash` | P1 |
| C-6 | J-15 | `features/tests/`（新测试） | 镜像引擎的 `FC_A4_no_factor_or_adjusted_price_is_read`：特征库装载日线时遇到复权因子列 / 复权价列或 `adjustflag ≠ 3` 即报错；复权因子目录从不被打开 | 新测试（合成目录） | P1 |
| C-7 | 全部 | 两个库 | C-1、C-3 – C-6 完成后重跑**全部**测试与干跑（引擎 `run_all.py`、特征 `run_all.py` + `dryrun_trial.py` + `zo_real_validation.py`）；约定哈希会变（`rule_calendar.py` 改了），所有结果文件带新哈希；在两份测试报告各加一节 "v0.8 changes" | — | P0 |
| C-8 | U-PILOT | 引擎装载器 `io_baostock.load_market`、事件装载、特征库 `bars.prepare_bars` / Z_O 读取 / `market_panel` | **数据截止日参数**（试点 = 2021-12-31）：装载时丢弃并拒绝该日之后的任何行；Z_O 只打开截止日所在月 / 年及之前的文件；面板与结果文件记录截止日。试点名单 `experiments/data/universe_pilot_v1.csv` 作为代码过滤（Z_O 按代码过滤）。默认值不得是"无截止"——试点配置里必须显式写 2021-12-31 | (a) 截止日之后的合成行被拒；(b) 截止日之后的 Z_O 文件从未被打开（打开即报错的测试替身）；(c) 结果文件含截止日字段 | P0 |

**不做的事（本轮明确不需要）：** 人工核对清单的处理、`undated_rights="include"`、代码变更映射（OA9）、"全所前 N 名"排序代理（TODO-F5）、规则日历延长到 2026-07-01。

**仍按 v0.7 任务书待做、未因本轮改变的：** TODO-E5、E8 – E11（策略层、交叉检验、补位等）；TODO-F4（URS 诊断列，待事件表）；抓取管线的补行（TODO-D1）。试点（PLAN §13A）需要其中的策略层。

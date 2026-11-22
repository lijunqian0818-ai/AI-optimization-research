# 主张 ↔ 证据对照表

论文中每一个主张都必须在这里有出处，否则不能写进论文。

> 版本：writer，2026-11-15，对应 `paper/main.tex` 的"不依赖实验结果"初稿。**此时没有任何实验结果**：`experiments/RESULTS.md` 不存在，所有经验性主张要么是引文支持的背景陈述，要么标为 `PENDING (no result yet)`（在 main.tex 中对应 `\todo{results: ...}`）。
> 定理编号对照（论文里一律不称 Theorem，见 `STATUS.md` 定理状态表）：
> 论文 Proposition 1 = theorems.md Theorem 1(a)(b)(c)；Proposition 2 = Corollary 1.1；Proposition 3 = Corollary 1.2；Proposition 4 = theorems.md Proposition 2；Lemma 5 = Lemma 3；Remark 1 = Remark 4。Corollary 1.3（`草稿`）只在注释块中出现，不进正文陈述。
> "状态"列的写法：`定理状态` 照抄 `STATUS.md`；引文类写 `references.bib` 的 note 所示阅读深度；设计类写出处文件；`PENDING` = 尚无结果。
> 审查状态简写 **[S]** = "`GPT 审过`（半独立）、`Gemini 审过`（Flash）；三轮均未被判错；第 3 轮后的修改未复审；作者自标 `自查通过`"。

## 1. Abstract 与 Introduction

| # | 论文中的主张 | 位置（章节） | 证据（定理编号 / RESULTS.md 表图 / bib key） | 状态 |
|---|---|---|---|---|
| 1 | 门控使交易变少，而少交易本身改变市场暴露与成本，所以加门控后的改善难以解读为选股更好 | Abstract；§1 "Why an improvement…" | Lemma 5（= Lemma 3）的恒等式 (2)：P&L 差恰好分为暴露时间表 / 构成 / 成本三项；限定条件 3（构成 ≠ 选股） | [S]；恒等式两方确认，记账解释末轮未复审；不主张新颖性 |
| 2 | 研究设定：A 股、只做多、日频、T+1、含成本；所有成交均为由日线构造的 retrospective synthetic fills | Abstract；§1 "Questions"；§3.4 | `research_question.md` v4；`instantiation_ashare.md` I-§2.4；PLAN v0.5 §1、§3.2 | 设计事实；PLAN v0.5 未经外部审查 |
| 3 | 预先设定了三样东西：批次内选股价值估计对象；两组变量的增量检验；描述性的三项分解 | Abstract；§1 | v4 "问题的每一部分对应什么证据"表；PLAN §8.3、§8.4、§8.2 | 设计事实 |
| 4 | 方法性补充：定义入场时亏损概率、把时间一致置信序列适配到延迟到期标签、给出最坏情形下界 | Abstract；§1 贡献 2 | Proposition 1、2、4（= Thm 1、Cor 1.1、Prop 2） | [S]；Prop 4 新颖性未验证 |
| 5 | 全管线在打开留出期之前由零假设模拟检查 | Abstract；§1 贡献 1；§5.6 | PLAN §10.2（`null_pipeline`，mandatory before the hold-out is opened） | 设计事实；尚未运行 → 结果 `PENDING` |
| 6 | 扑克程序已达到超人水平，使"没把握就不出手"的推理为人熟知 | §1 "Motivation" | `brown2018libratus`、`brown2019pluribus` | 均 metadata only；只用到标题层面的"superhuman AI for poker" |
| 7 | 本文不建模博弈、不求均衡、不作博弈论主张；扑克只作动机 | §1 | v4 措辞约束；PLAN §1 Non-goals | 自我限定（不是经验主张） |
| 8 | 选择性分类器已被做成弃权即空仓的交易策略 | §1；§2 | `pidan2011selective`（abstract only）、`chalkidis2021trading`（full text）、`nabar2023conservative`（abstract + introduction） | 引文支持 |
| 9 | 已有工作在截面选股排序器之上加了策略层门控 | §1；§2 | `sanderink2026alpha` | Sections 1–4, 8 通读，5–7 扫读 |
| 10 | 业界称二级过滤模型为 meta-labeling | §1；§2 | `joubert2022metalabeling`、`meyer2023metalabeling` | 均 abstract only（付费墙）；不引 `lopezdeprado2018advances`（章节未核实，main.tex 留 todo） |
| 11 | 控制已接受样本错误率的统计工具已存在：独立 / 可交换数据下，以及序贯 anytime-valid 形式 | §1 | `geifman2017selective`、`bates2021rcps`、`angelopoulos2022crc`；`howard2021timeuniform`、`ramdas2023savi`、`xu2024arcps`、`khosravi2026csa` | 全部 abstract only；只陈述到"存在此类工具"的程度 |
| 12 | 我们不把门控结构或弃权想法作为贡献 | §1；§2 | `novelty_report.md` §0 第 1 条、§5（弃权层撞车风险：高） | 自我限定；novelty_report 经 GPT / Gemini / ARS 三路检查（`reviews/novelty_check_1.md`） |
| 13 | 构成项还含行业 / 规模 / 流动性倾斜与重叠入场批次的组合变化 | §1；§4.3 限定 1；§6 | theorems.md Lemma 3 限定条件 3；PLAN §8.2（"Aggregate composition is not the Q-select estimand"） | [S]（限定条件属陈述的一部分） |
| 14 | 同日结果相关、持仓重叠、结果延迟已知，所以交易笔数高估了证据量 | §1 | Proposition 4（= Prop 2）：块环境中 N 笔交易只相当于 N/(Md) 笔独立交易（最坏情形） | [S]；最坏情形陈述，不是对某个市场的断言 |
| 15 | RQ-1、RQ-2、RQ-3 的表述；Z_H、Z_O 的组成；两组都不视为私有信息的度量 | §1 "Questions" | `research_question.md` v4 "研究问题"与"措辞约束"；PLAN §1 | 设计事实（逐句对应 v4） |
| 16 | 贡献 1：评估协议（合成成交定义、基准价记账与台账对账、精确期望的匹配下单机会随机对照、冻结的逐年部署算法、全管线零假设模拟） | §1 | v4 "不依赖任何结果的贡献" (i)；PLAN §3.2、§3.6、§3.9、§8.3、§4.3、§10.2 | 设计事实；协议尚未执行，PLAN v0.5 未经审查 |
| 17 | 贡献 2：估计对象 + 监控区间 + 下界；区间是已有工具（时间一致置信序列 + 延迟反馈子采样）的适配，不主张新保证类型 | §1；§2；§4 开头 | v4 贡献 (ii)；theorems.md "Relation to prior work"（`prior_theorems_audit.md` §8.1）；`howard2021timeuniform` | [S]；审计本身未经外审；Howard et al. abstract only；子采样约化的出处（Weinberger–Ordentlich 2002、Joulani et al. 2013）不在 bib → main.tex 留 todo，未引用 |
| 18 | 贡献 3：两组变量与两个参考门控的预先设定检验完整报告，含阴性与无定论结果 | §1 | v4 贡献 (iii)；PLAN §8.4、§9.3 | 设计承诺；结果 `PENDING` |
| 19 | 结果摘要段 | §1 末 | — | `PENDING (no result yet)` |

## 2. Related Work

| # | 论文中的主张 | 位置 | 证据 | 状态（阅读深度） |
|---|---|---|---|---|
| 20 | Pidan & El-Yaniv 用 HMM 做金融趋势的选择性预测 | §2 ¶1 | `pidan2011selective` | abstract only；只到标题 / 摘要层面 |
| 21 | Chalkidis & Savani：二元 / 三元选择性分类器 → 弃权即空仓；用 Geifman & El-Yaniv 的程序构造选择函数；5 个 CME 金属期货 30 分钟线、anchored walk-forward；弃权在所有配置下提高已交易子集的准确率，多数配置在 0.3 tick 滑点下不盈利 | §2 ¶1 | `chalkidis2021trading`；`related_work.md` §1；`novelty_report.md` §2.2 | full text (arXiv v2) |
| 22 | 其保证是 i.i.d. 下的陈述，未讨论时间依赖 | §2 ¶1 | `chalkidis2021trading`；`novelty_report.md` N6（置信度：高） | full text |
| 23 | Nabar & Shroff：模型级联，级联拒绝预测时不交易；印度股票市场 | §2 ¶1 | `nabar2023conservative`；`related_work.md` §1 | abstract + introduction；其余扫读 |
| 24 | Sanderink：梯度提升截面排序器上的两个决策（基于已到期 RankIC 的策略层门控；个股层截尾）；至多 100 只美股；报告门控预测模型失效优于波动率类代理；无形式化保证 | §2 ¶2 | `sanderink2026alpha`；`novelty_report.md` §2.1、N7 | Sections 1–4, 8 通读；5–7 扫读（"报告优于波动率代理"出自扫读的结果节，措辞为 "reports"） |
| 25 | Fang & Ślepaczuk（沪深 300）：朴素预测策略扣成本后失败，低波动门控与阈值校准改善防御性表现 | §2 ¶2 | `fang2026volatility` | abstract only |
| 26 | 选择性预测还用于加密货币事件合约、限价订单簿预测、检索增强的金融预测 | §2 ¶2 | `hao2026coverage`、`manoharan2026uqlob`、`torres2026finabstain` | 均 abstract only；只到标题层面；未复述 Torres 的结果（其摘要自述为模拟） |
| 27 | Guo (2026)：研究 ML 因子 / 行业轮动策略何时应拒绝交易；验证改进超过校准阈值才部署；有收益与均值–方差效用分解和验证误差部署界 | §2 ¶2 | `guo2026whennot` | abstract only（Crossref 存入的摘要）；全文未读；正文写明 "according to its abstract"；与 Lemma 5 是否重合未知 → todo |
| 28 | meta-labeling 是同一结构；Meyer et al. 研究二级模型的校准与仓位 | §2 ¶3 | `joubert2022metalabeling`、`meyer2023metalabeling` | 均 abstract only |
| 29 | 本文的门控结构上属于这一类工作 | §2 ¶3 | PLAN §6.1（CONF、LOSS 的定义）；`related_work.md` §1 末段 | 自我定位 |
| 30 | 拒识选项可追溯到 Chow；Cortes et al. 给出带拒识学习的理论 | §2 ¶4 | `chow1970optimum`、`cortes2016learning` | 均 metadata only；只到标题层面 |
| 31 | Geifman & El-Yaniv 选阈值并给已接受集风险的保证；SelectiveNet 把拒识选项集成进网络 | §2 ¶4 | `geifman2017selective`、`geifman2019selectivenet` | 均 abstract only |
| 32 | Deep Gamblers 把选择性分类改写为下注问题，弃权 = 保留部分赌注；定理刻画最优下注解 | §2 ¶4 | `ziyin2019deepgamblers` | abstract、introduction、theorem statements |
| 33 | Zhang et al.：金融动机；部分样本无信息的生成过程；i.i.d. 下恢复有信息区域；无交易评估 | §2 ¶4 | `zhang2023abstain`；`novelty_report.md` N9（高） | Sections 1–2 通读；假设 / 定理陈述与实验节扫读 |
| 34 | 训练后校准阈值以控制用户指定风险：RCPS、LTT、CRC；以及对被选样本控制风险的扩展 | §2 ¶5 | `bates2021rcps`、`angelopoulos2021ltt`、`angelopoulos2022crc`、`xu2025scrc`、`bai2026score` | 全部 abstract only |
| 35 | ACI 处理分布漂移；时间一致置信序列与 anytime-valid 推断在任意停时成立；anytime-valid 构造用于序贯数据的风险控制与 LLM 部署中的选择性行动 | §2 ¶5 | `gibbs2021aci`、`howard2021timeuniform`、`ramdas2023savi`、`xu2024arcps`、`hultberg2026anytime`、`khosravi2026csa` | 全部 abstract only |
| 36 | 延迟反馈下的在线 CRC；有限反馈的在线选择性分类；分布漂移下的选择性分类 | §2 ¶5 | `wang2026caocrc`、`gangrade2021online`、`liang2024selective` | 全部 abstract only；只到标题层面 |
| 37 | 我们的监控命题应读作已有工具的适配，不是新保证类型 | §2 ¶6 | 同 #17 | [S] |
| 38 | MohammadpourAzari et al.：控制器在 Safe 组合与两个信号叠加层之间选择，证据门控把无支持的方向性仓位转到 Safe；陈述是延迟反馈下的跟踪遗憾界与路径式安全界，不是已选交易的亏损概率 | §2 ¶7 | `mohammadpourazari2026safe`；`novelty_report.md` N8（高） | Section 1、Section 3 的假设与定理陈述、数据描述；其余扫读；证明未读 |
| 39 | Zarei et al.：用 conformal 校准的风险预算门控 RL 配置器的提议 | §2 ¶7 | `zarei2026conformal` | abstract + introduction |
| 40 | conformal 方法用于组合选择、选股、仓位、组合尾部风险校准；anytime-valid 检验用于决定何时提升交易规则 | §2 ¶7 | `kato2024conformal`、`kaya2025conformal`、`ryan2026conformalkelly`、`schmitt2026taming`、`chen2026cvar`、`benhamou2026promote` | 全部 abstract only；只到标题层面 |
| 41 | 我们监控的量不同（已出手入场的入场时亏损概率）；不对回撤或组合尾部风险作陈述 | §2 ¶7；§6 | `setup.md` §5；v4（最大回撤和组合 CVaR 不作为定理目标） | 自我限定 |
| 42 | 信息劣势方为何犹豫交易是经济理论与微观结构的经典主题（共同知识下的交易；面对知情对手方；新股定价；模糊性下的组合选择与不参与） | §2 ¶8 | `milgrom1982information`、`kyle1985continuous`、`glosten1985bid`、`rock1986new`、`dow1992uncertainty`、`easley2009ambiguity` | 全部 metadata only；每篇只用标题能支持的主题词，不陈述定理内容 |
| 43 | 信息风险是否被定价本身是个实证问题 | §2 ¶8 | `easley2002information` | bib note：metadata only（标题即为该问题）；未写 PIN 的数值结论 |
| 44 | Choi, Jin & Yan：上交所账户级持仓；机构持股波动高的股票四因子 alpha 更高；原始收益差不显著；小盘股无效应 | §2 ¶8 | `choi2013informed`；`novelty_report.md` §10（NBER 版正文已读） | bib note 写 abstract only，但 `choi2025informed` 的 note 与 `lead_verification.md` 记录 NBER 版正文通读、表格未逐一核对 → **bib note 不一致，见文末** |
| 45 | 因此设计中报告门控未提交订单的收益 | §2 ¶8；§5.3 | PLAN §9.1 P5；`novelty_report.md` §6 第 10 项 | 设计事实 |
| 46 | Chakraborty & Yilmaz：两期模型（内幕者、理性跟随者、竞争性做市商），内幕者在每个均衡中诈唬；结果关于知情方，未刻画劣势方何时应不交易 | §2 ¶8 | `chakraborty2008bluffing`；`novelty_report.md` §11.3 | 正文通读；在线附录证明未读 |
| 47 | Huddart et al. 分析内部人交易披露作为策略性信号 | §2 ¶8 | `huddart2001disclosure`；`opponent_action_variables.md` M9 | abstract only；模型细节未读 |
| 48 | 建仓作为不完全信息博弈；经纪商检测有毒订单流 | §2 ¶8 | `chriss2025position`、`cartea2026toxic`、`cartea2025simple` | 均 abstract only（`cartea2026toxic` 为期刊版，只读 arXiv 摘要；未同时引 `cartea2023toxic`） |
| 49 | 筹码分布由价格与换手历史估计持有人成本分布；其学术对应物是资本利得悬挂，文献将其与 Grinblatt & Han、Wang et al. 联系 | §2 ¶9 | `related_work.md` §5；`grinblatt2005prospect`、`wang2017reference` | 均 metadata only → 措辞弱化为 "the literature associates with"，并留 todo 要求读全文确认定义 |
| 50 | Xu (2025) 在中国数据上复现 Wang et al.，考察资本利得悬挂与风险代理的交互；Pan et al. 考察 A 股资本利得与收益 | §2 ¶9 | `xu2025replication`、`pan2025overreaction` | 均 abstract only（后者期刊质量未评估）；未写符号结论 |
| 51 | 龙虎榜、大宗交易、内部人卖出在中国市场已被研究（与价格 / 收益的关系）；美股有 Lakonishok & Lee | §2 ¶9 | `hong2025dragontiger`、`fan2012block`、`du2024fastsales`、`lakonishok2001insider` | 均 abstract only；只到标题层面 |
| 52 | 这些变量的预测力不是本文的发现；本文只检验加入门控是否改变批次内选股价值，并控制构造原料与披露触发条件 | §2 ¶9 | `opponent_action_variables.md` §4(i)（变量预测力 = 已知结果）；PLAN §5.4、§7.4 | 自我限定 + 设计事实 |
| 53 | Leippold et al. 研究中国股市的 ML 收益预测；Gu et al. 研究实证资产定价中的 ML | §2 ¶9 | `leippold2022machine`、`gu2020empirical` | 均 metadata only；只到标题层面 |
| 54 | T+1 规则被纳入学习式交易系统；涨跌停可预测性被研究 | §2 ¶9 | `zhang2022t1`、`liang2024pricelimit` | 均 abstract only |

## 3. Problem Setup

| # | 论文中的主张 | 位置 | 证据 | 状态 |
|---|---|---|---|---|
| 55 | 抽象设定：G_t / F_t、候选集、入场、标签、X_t、μ_t | §3.1 | `theory/setup.md` §1–§2 | 定义；第 3 轮后的重构未复审 |
| 56 | 假设 A1、A1-G、A2(a)(b)(c)、A3、A4、A5 的陈述；A1-G 不用于任何证明；A3 不蕴含 A5；每条假设都需数据审计或书面约定支持 | §3.2 | `theory/setup.md` §3 | 定义 / 假设；A1-G、A2(b) 为第 3 轮新增，未复审 |
| 57 | 两个滞后；更大的预先设定监控滞后不改变目标；半径对 d 不单调，d 须在看数据前固定 | §3.2 "Two lags" | `theory/setup.md` §4；`theory/checks/check_lag_monotonicity.py`（数值例） | 作者自查；未复审 |
| 58 | 目标 r_T^entry 的定义及"不是什么"六条；监控是对过去入场流的推断，不是对未来风险的控制 | §3.3 | `theory/setup.md` §5 | 定义 |
| 59 | A 股落地是建模假设，不属于任何陈述；所依赖的交易所规则尚未对照官方规则原文核对 | §3.4；§6 | `instantiation_ashare.md` 开头 STATUS 声明、I-§9；`STATUS.md` 未解决问题 | 如实声明（literature-scout 的规则核对进行中 → todo） |
| 60 | 订单只读 t−1 及之前的数据与 t 日开盘前公开信息；每日至多 M 单 | §3.4 | I-§2.1；PLAN §3.1 | 实现要求，待截断测试（audit A11）验证 → `PENDING` |
| 61 | 日线不记录集合竞价是否成交及成交量，故由日线构造的入场指示相对竞价时点信息不可测 | §3.4 | I-§2.4 第 1–6 条 | 建模分析；"日线开盘价在无竞价成交时的含义"为 [rule: tbv] |
| 62 | 合成成交规则 (S1)–(S3) 与声明的信息集 F_t^syn；它是人为信息集；与真实成交的差异无法由日线估计；所有监控量指合成成交流，不是可执行策略 | §3.4；§6 | I-§2.4；PLAN §3.2 及 Standing qualifier (T1) | 设计事实 / 如实限定 |
| 63 | 主标签：t+H 开盘盯市的净亏损，由书面决策树对每笔入场赋值；不支持事件与缺失输入记为亏损并计数；d_label = d = H+1 在看数据前固定；可得性是待审计的假设 | §3.4 | I-§3、I-§4；`STATUS.md` 决策记录（d = H+1） | 约定；可得性（OA-next）未审计 |
| 64 | 基准价记账：所有策略同一时点同一基准价（日线开盘价）；费用与滑点只经成本项、各计一次 | §3.4；§4.3 限定 4 | theorems.md Lemma 3 Convention B；`STATUS.md` 决策记录 | 约定（组长决定）；记账解释末轮未复审 |

## 4. 理论陈述

| # | 论文中的主张 | 位置 | 证据 | 状态 |
|---|---|---|---|---|
| 65 | 审查状态说明：三轮、两个外部模型，未报告证明或常数有错；末轮修改未复审；因此称 proposition | §4 开头；§6 | `STATUS.md` 定理状态表及其下说明 | 如实声明 |
| 66 | Proposition 1（延迟监控）：(1) 式与 (a)(b)(c) | §4.1 | theorems.md Theorem 1；证明 `theory/proofs.md` §1 | `GPT 审过`（半独立）、`Gemini 审过`（Flash）；三轮均未被判错；第 3 轮后的修改未复审；(c) 的单侧水平无单独数值检查 |
| 67 | M 不进入半径；不覆盖事后选择的滞后；是带可预测范围时钟与二进拼接的 Hoeffding 型界；不比已知置信序列更尖锐；无经验方差自适应 | §4.1 | theorems.md Theorem 1 "Comparison with existing results"、setup §3 "Role of M" | 同 #66 |
| 68 | 直观解释（车道内为公平博弈；未揭示标签两头计） | §4.1 | theorems.md "In plain words" | 解释性文字 |
| 69 | Proposition 2（速率与总宽度）(a)(b) | §4.1 | theorems.md Corollary 1.1 | 同 Theorem 1；非贡献；(b) 无专门数值检查 |
| 70 | 无 A5 时不主张总宽度为 √(dM/N) 阶 | §4.1 | theorems.md Corollary 1.1(a) 后的说明 | 同上 |
| 71 | Proposition 3（已实现亏损比例的确定性括号；与目标的比较） | §4.1 | theorems.md Corollary 1.2 | 同 Theorem 1；非贡献 |
| 72 | "仅到期"比率不被任何陈述覆盖且可能有偏；两笔入场的例子 | §4.1 | theorems.md Corollary 1.2（例子来自 GPT 独立推导） | 同上 |
| 73 | 对解决时间无界的标签的扩展是草稿、未通过审查，不在正文陈述；Proposition 1 不用于此类标签 | §4.1 末；§6 | theorems.md Corollary 1.3；`STATUS.md` | `草稿`；第 3 轮 Gemini 判正确、GPT 给出反例；重写未复审 |
| 74 | 块环境的定义与性质（A1–A5 成立，μ_t = Mp，r = p） | §4.2 | theorems.md Proposition 2 "Block environment" | 见 #75 |
| 75 | Proposition 4（最坏情形有效样本量下界）及方差比较 | §4.2 | theorems.md Proposition 2；证明 `proofs.md` §2 | `GPT 审过`（半独立）、`Gemini 审过`（Flash）；三轮均未被判错；**新颖性未验证**（须先读 Weinberger–Ordentlich 2002） |
| 76 | 在 A1–A5 环境类上，宽度对 dM/N 的依赖在最坏情形下除 √ℓ_T 与常数外不可改进；N 笔入场相当于 N/(Md) 笔独立入场 | §4.2 | theorems.md Proposition 2 "Scope" | 同 #75 |
| 77 | 论证是标准的两点比较；构造与延迟反馈在线学习的下界构造相似；对该界是否已知不作主张 | §4.2 | theorems.md Proposition 2 "Comparison with existing results"、"Relation to prior work" | 审计（未外审）的转述；W–O 2002 未读 → `\todo{verify novelty against Weinberger--Ordentlich 2002}`；未引用任何不在 bib 的文献 |
| 78 | Proposition 4 的局限（对数因子、最坏情形、整除条件、常数未优化、只关于 r_T^entry） | §4.2 | theorems.md Proposition 2 "What it does not show" 1、3、5、6 | 同 #75 |
| 79 | Lemma 5（可加归因恒等式）及参考组合的毛 / 净关系 | §4.3 | theorems.md Lemma 3 | `GPT 审过`（半独立）、`Gemini 审过`（Flash）；恒等式两方确认；记账解释经三轮修改，末轮未复审；不主张新颖性；与 Guo 2026 的分解是否重合未知 |
| 80 | 恒等式是路径代数；与教科书绩效归因同类；不主张新颖性 | §4.3 | theorems.md Lemma 3 "Comparison with existing results" | Brinson et al. 1986 未核实、不在 bib → 未引用，留 todo |
| 81 | Lemma 5 的六条限定（构成 ≠ 选股；约定与非唯一性；参考不必可行；成本只计一次；财富解释的充分条件；非可加指标与非因果） | §4.3 | theorems.md Lemma 3 限定条件 1–7、W1–W4、Convention B | 同 #79 |
| 82 | Remark 1：全亏损环境下任何策略 R_T = r = 1；无策略能在所有 A1–A4 环境中保证"风险 ≤ α 且正概率交易" | §4.4 | theorems.md Remark 4 (i)(ii) | `GPT 审过`（半独立）、`Gemini 审过`（Flash）；陈述在第 1 轮后改弱；不主张新颖性 |
| 83 | Remark 不意味着唯一安全策略是不交易；此类保证需要对环境的限制或可行性假设 | §4.4 | theorems.md Remark 4 "What is not claimed"、"Conclusion" | 同 #82 |

## 5. Experimental Design（只有设计，没有结果）

| # | 论文中的主张 | 位置 | 证据 | 状态 |
|---|---|---|---|---|
| 84 | 数据为免费日线；计划股票池为沪深 300 ∪ 中证 500 的时点成分；开发段截至 2021-12-31，留出期 2022-01 至 2026-06，冻结且只打开一次；逐年重拟合，purge 间隔 H+1 | §5.1 | PLAN §2.1–§2.3、§4.3、§4.4、§8.4 | 计划（proposal，待审计确认）→ todo；数据来源与许可证 todo |
| 85 | 基础预测器的 top-K 为提名名单；确认性检验的提名名单来自不含两组变量的基础预测器 | §5.2 | PLAN §6 开头、§7.1 | 设计事实 |
| 86 | 标准订单收益 ρ_ti 的定义；只依赖股票与日期 | §5.2 | PLAN §8.3 | 设计事实 |
| 87 | u_t^g、θ_sel^g 的定义；第二个和是分层随机选择的精确期望；匹配的是下单机会而非暴露；对整日回避不给分；报告选择份额与可达范围 | §5.3 | PLAN §8.3 | 设计事实 |
| 88 | ψ_H、ψ_O 的定义 | §5.3 | PLAN §8.4 Cards C3、C4 | 设计事实 |
| 89 | 描述性量（年化算术收益、期末财富、回撤、交易级亏损幅度、换手、未提交订单收益）；只比较可行策略；三项分解；监控区间不用于比较方法 | §5.3 | PLAN §8.1、§8.2、§9.1、§1 "Monitoring" | 设计事实 |
| 90 | 表 1 的方法清单与定义 | §5.4 | PLAN §6.1 | 设计事实；PERF "after `sanderink2026alpha`"（PLAN 注明编码前须重读该文） |
| 91 | CONF 与 LOSS(−Z) 是本管线内的自有实现，不代表已有弃权方法这一类；已发表方法留到可选的第二轮 | §5.4；§6 | PLAN §1 "Not hypotheses" (ii)、§6.2；引用 `geifman2017selective`、`geifman2019selectivenet`、`ziyin2019deepgamblers`、`zhang2023abstain`、`khosravi2026csa`、`xu2024arcps` 仅作"第二轮候选"列举 | 设计事实 |
| 92 | 相同试验次数不等于相同优化投入；报告搜索空间、不同配置数、调参成本 | §5.4 | PLAN §6.3 第 5、6 条 | 设计事实 |
| 93 | Z_H、Z_O 的特征构成；无参与者身份进入特征；各配控制特征（Z_H 所用窗口的价格 / 换手路径；Z_O 披露的触发条件）；Z_O 类别须先过数据审计（含公告日审计） | §5.4 | PLAN §1、§5.1–§5.4、§5.6、§8.4 Card C4 | 设计事实 |
| 94 | 析因结构：确认性对比固定基础预测器只在门控中加一组；其余单元探索性；容量匹配的置换对照 | §5.4 | PLAN §7.1–§7.3 | 设计事实 |
| 95 | C1–C4 的陈述；留出期只评估一次；主参数 H = 5、c = 0.5、五个种子平均 | §5.5 | PLAN §8.4、§3.3、§6.1、§10 | 设计事实；参数待冻结确认 → todo |
| 96 | 等价界 Δ_ord = Δ_cap (H+1)/(A c)；Δ_cap = 每年 1%，约合每单 5bp；看数据前固定 | §5.5 | PLAN §9.3；`STATUS.md` 决策记录（关卡 2 默认值 (2)） | 设计事实（组长对"默认值"的解读，用户可否决） |
| 97 | C1 / C2 是确认性等价检验还是预先声明的估计目标，由不用任何门控输出的设计阶段方差计算机械决定（80% 功效、最持久的参考选择器） | §5.5 | PLAN §10.1 | 设计事实；状态尚未记录 → `PENDING` |
| 98 | Holm 族，族水平 5%，大小 1–4，在看到门控结果前固定；其余均为探索性或描述性 | §5.5 | PLAN §8.4、§10 | 设计事实；Holm / TOST / stationary bootstrap 的参考文献不在 bib → 未引用，留 todo |
| 99 | 推断：按交易日重抽样的成对平稳块自助法；块长与 H+1 成比例；种子变异单列；块自助法的假设及其局限 | §5.5；§6 | PLAN §10 | 设计事实 |
| 100 | 零假设模拟的四类世界（结果置换、特征互换、单组置换、边界版本）及其性质 | §5.6 | PLAN §10.2 | 设计事实 |
| 101 | "前两个世界选股价值为零"的论证是我们自己的、未经独立审查；通过准则不能证明错误率不超过名义水平；各重复共用一条已实现价格历史；失败时至多三次的固定阶梯 | §5.6 | PLAN §10.2（"the plan's own argument and has not been reviewed"；pass criterion 的说明；ladder） | 如实限定 |
| 102 | 成交判定敏感性（更严 / 更松）界定对 (S2)(S3) 的依赖，不度量合成与真实成交的差距；其他预设分析均为探索性（持有期、覆盖率、成本、调参预算） | §5.7 | PLAN §3.2、§11 | 设计事实 |
| 103 | 结果措辞规则（negligible / difference detected / inconclusive；界外估计不是裁决；范围限定语） | §5.7 | PLAN §9.3、§7.4 | 设计事实 |
| 104 | 全部结果小节（7 处） | §5.8 | — | `PENDING (no result yet)` |

## 6. Limitations 与 Conclusion

| # | 论文中的主张 | 位置 | 证据 | 状态 |
|---|---|---|---|---|
| 105 | 合成成交的局限；无竞价数据；敏感性分析不能弥合差距 | §6 | I-§2.4；PLAN §3.2；`STATUS.md` 未解决问题（日线模拟开盘成交存在前视） | 如实限定 |
| 106 | 单一市场 / 股票池 / 时期 / 基础信号；重抽样与零假设模拟都以一条已实现历史为条件；免费数据是下载日快照；事件日历完整性待审计；Z_O 仅限免费数据 | §6 | v4 "每种结果下论文的贡献"表；PLAN §10、§2；I-§2.4 第 6 条、I-§9；`STATUS.md` 决策记录 | 如实限定；审计结果 `PENDING` |
| 107 | 操作性假设未经官方规则原文核对 | §6 | 同 #59 | 如实限定 |
| 108 | 理论陈述的状态：两个外部模型（一个参与过设计讨论，一个不是该厂商最强模型）；末轮未复审；Cor 1.3 为草稿且审稿人意见不一；Prop 1 是适配；Prop 4 新颖性未验证；尚未与"延迟结果下 anytime-valid 推断"的近作比较 | §6 | `STATUS.md` 定理状态表与未解决问题（Lindon & Kallus arXiv:2603.25971 未读、不在 bib → 正文不点名、不引用）；`CLAUDE.md` 外部审稿一节 | 如实限定 |
| 109 | 监控量不是对未来交易、回撤或尾部风险的保证；区间宽；设计阶段公式估算留出期末半宽约 0.17–0.22；不用于比较方法 | §6 | `setup.md` §5；Proposition 4；PLAN §1（"estimated half-width about 0.17–0.22"，ESTIMATE，§9.4：公式代入假定样本量，无数据） | 估算值，非结果；实测宽度 `PENDING` |
| 110 | θ_sel 对整日回避不给分；构成项不是选股、归因非因果；C1 / C2 不能推广到整类方法；等价界可能超出设计的分辨能力；无定论是可能结果；块自助法与零假设模拟的局限 | §6 | PLAN §8.3、§8.2、§1、§10.1（方法审查 R6：功效很可能不足）、§10 | 如实限定 |
| 111 | 文献覆盖的局限：中文文献与研报未检索；若干文献只读摘要；Guo (2026) 全文未读且可能与 Lemma 5 重合；因此不对任何部分主张优先权 | §6 | `novelty_report.md` §1、§11.2；`STATUS.md` 未解决问题 | 如实限定 |
| 112 | 不利结果清单；结论 | §6 末；§7 | — | `PENDING (no result yet)` |

---

## 需要 literature-scout 补充核实的文献（不在 `references.bib`，main.tex 中未引用、以 `\todo` 标出）

1. **Weinberger & Ordentlich (2002)**，延迟反馈的子采样约化与下界构造——关系到 Proposition 1 的出处和 Proposition 4 的新颖性（须读原文）。
2. **Joulani, György & Szepesvári (2013)**，延迟反馈在线学习（审计引用其 Sec. 3.1）。
3. **Lindon & Kallus (arXiv:2603.25971)**，延迟结果 + 交错入组下的 anytime-valid 推断——从标题看与 Proposition 1 是同一组合，未读。
4. **Brinson, Hood & Beebower (1986)**，经典绩效归因（Lemma 5 的出处说明；作者与内容均未核实）。
5. **Holm (1979)** step-down 多重比较；**TOST 等价检验**的出处（通常归于 Schuirmann 1987，未核实）；**stationary bootstrap**（PLAN 提到 Politis & Romano；Künsch）。
6. **Pinsker 不等式的教科书出处**（theorems.md 提到 Tsybakov 2009，引理编号待核实）——附录证明若引用则需要。
7. **LightGBM** 原始论文、**AKShare / BaoStock** 的引用方式与许可证（`resources/MANIFEST.md`；本轮未写入正文，留 todo）。
8. `lopezdeprado2018advances` 已在 bib，但只核实了题录：需确认 meta-labeling 所在章节后才能作为该术语的出处引用。
9. `grinblatt2005prospect`、`wang2017reference`（metadata only）：需读到全文 / 摘要，确认资本利得悬挂的定义后，去掉 main.tex §2 的弱化措辞与 todo。`liu2019size`（metadata only）：related_work.md 中"异常换手进入中国因子模型"一句因超出阅读深度**未写入** main.tex；读后可恢复。
10. `guo2026whennot` 全文（SSRN 7021298）：决定 Lemma 5 是否须改写为"沿用 / 扩展"。

## references.bib 中发现的不一致（未改动 bib，请组长 / literature-scout 处理）

- `choi2013informed` 的 note 为 "Read: abstract only"，但 `choi2025informed` 的 note、`related_work.md` §4 与 `novelty_report.md` §10 都记录 NBER 版正文已通读。main.tex 引的是实际读过的 NBER 版（`choi2013informed`），其 note 应更新。
- `easley2002information` 的 note 为 "metadata only"，而 `novelty_report.md` §10 称已升为"仅读摘要"。main.tex 按 bib 的较保守深度写（只引为"信息风险是否被定价是实证问题"，未写 2.5% 等数值）。

## 本稿有意没有写的主张（因为没有合格出处）

- 任何"首次 / first / novel framework"类表述；任何"未见前人把这些变量用于弃权层"的否定性存在主张（N4、N10、M1–M5 置信度低–中，中文文献未检索，尚未事实核查）。
- 任何实验结果、任何对结果方向的预告。
- Cor 1.3 的正文陈述（草稿）。
- 把 Z_O / Z_H 解释为私有信息度量或博弈机制的任何句子。

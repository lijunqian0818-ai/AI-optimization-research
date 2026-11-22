# 外部模型文献线索核实（第 1 轮新颖性检查之后）

> 撰写：literature-scout，2026-11-15。对象：`reviews/novelty_check_1.md` §3 列出的线索。
> 核实方式：Crossref REST API（按 DOI 或按题录检索）、OpenAlex API、arXiv API（按 ID）、doi.org handle API、PMLR / NeurIPS 官方页面的 `citation_*` 元数据、Open Library（按 ISBN）。每条都是本轮实际查询得到的返回，不是凭记忆。
> "核实结果"只表示**题录信息**是否正确；除 §2 的两篇外，本轮没有读这些文献的正文。
> 读到的网页、API 返回与 PDF 中**没有发现写给自动化 agent 的指令**。

## 1. 线索逐条核实

| # | 线索 | 来源方 | 核实结果 | 正确的 DOI / arXiv ID | 备注 |
|---|---|---|---|---|---|
| 1 | López de Prado 2018, *Advances in Financial Machine Learning* | GPT、Gemini | **存在且信息正确**（书） | 无 DOI（Crossref、OpenAlex 均未登记该书的 DOI）；ISBN 978-1-119-48208-6 | Open Library 按 ISBN 返回：标题 "Advances in financial machine learning"，作者 Marcos López de Prado，Wiley，2018，366 页。OpenAlex 另有一条 type=book、2018、无 DOI 的记录。**正文未读**：meta-labeling 出自该书哪一章本轮未核实，引用时不要写章节号。 |
| 2 | Ramdas, Grünwald, Vovk & Shafer 2023, Game-theoretic statistics and safe anytime-valid inference | GPT、Gemini | **存在且信息正确** | doi:10.1214/23-STS894；arXiv:2210.01948 | Crossref：*Statistical Science* 38(4), 576–601, 2023-11。arXiv API 标题、四位作者一致。 |
| 3 | Howard et al. 2021, Time-uniform confidence sequences | GPT、Gemini | **存在且信息正确**（完整标题见备注） | doi:10.1214/20-AOS1991；arXiv:1810.08240 | 完整标题 "Time-uniform, nonparametric, nonasymptotic confidence sequences"；Howard, Ramdas, McAuliffe, Sekhon；*The Annals of Statistics* 49(2), 1055–1080, 2021-04。PDF 已在 `literature/pdfs/arxiv_1810.08240.pdf`（本轮未读）。 |
| 4 | Easley, López de Prado & O'Hara 2012（VPIN） | GPT、Gemini | **存在且信息正确** | doi:10.1093/rfs/hhs053 | "Flow Toxicity and Liquidity in a High-frequency World"，*Review of Financial Studies* 25(5), 1457–1493。bib 中已有 `easley2012flow`，与 Crossref 一致。 |
| 5 | Easley, Hvidkjaer & O'Hara 2002 | Gemini | **存在且信息正确** | doi:10.1111/1540-6261.00493 | "Is Information Risk a Determinant of Asset Returns?"，*The Journal of Finance* 57(5), 2185–2221, 2002-10。bib 中已有 `easley2002information`。内容见 §2。 |
| 6 | Wang, Yan & Yu 2017 | GPT、Gemini | **存在且信息正确** | doi:10.1016/j.jfineco.2016.09.010 | "Reference-dependent preferences and the risk–return trade-off"，*JFE* 123(2), 395–414。bib 中已有 `wang2017reference`。 |
| 7 | Liu, Stambaugh & Yuan 2019, Size and value in China | GPT、Gemini | **存在且信息正确** | doi:10.1016/j.jfineco.2019.03.008 | *JFE* 134(1), 48–69。bib 中已有 `liu2019size`。正文未读："异常换手是情绪因子 PMO 的构造变量"这一说法仍只有题录级别的支持。 |
| 8 | Dow & Werlang 1992 的 DOI | GPT 给 10.2307/2951525；Gemini 给 10.2307/2951599 | **存在，但两个外部模型给的 DOI 都是错的** | **doi:10.2307/2951685** | Crossref：10.2307/2951685 = Dow & Werlang, "Uncertainty Aversion, Risk Aversion, and the Optimal Choice of Portfolio", *Econometrica* 60(1), 197, 1992-01（Crossref 只给起始页）。GPT 的 10.2307/2951525 实为 Galor, "A Two-Sector Overlapping-Generations Model…", *Econometrica* 60(6), 1351。Gemini 的 10.2307/2951599 实为 Aghion & Howitt, "A Model of Growth Through Creative Destruction", *Econometrica* 60(2), 323。bib 中 `dow1992uncertainty` 的 DOI 本来就是正确的。 |
| 9 | Easley & O'Hara 2009, Ambiguity and Nonparticipation | GPT、Gemini | **存在且信息正确** | doi:10.1093/rfs/hhn100 | 完整标题 "Ambiguity and Nonparticipation: The Role of Regulation"，*Review of Financial Studies* 22(5), 1817–1843。bib 中已有 `easley2009ambiguity`。 |
| 10 | Cartea, Duran-Martin & Sánchez-Betancourt, Detecting Toxic Flow 的正式发表信息 | GPT | **存在；已正式发表**（我们此前只登记了预印本） | **doi:10.1080/14697688.2026.2619539**；arXiv:2312.05827；SSRN doi:10.2139/ssrn.4597879 | Crossref：*Quantitative Finance* 26(4), 541–561，在线发表日期 2026-02-11。作者与 arXiv 记录一致。novelty_report 中写作 "Cartea et al. (2023)" 指的是预印本年份。期刊版正文未读（仅读 arXiv 摘要）。 |
| 11 | "Angelopoulos et al. 2024, Learn to Defer with Conformal Risk Control, arXiv:2404.14376" | Gemini | **未找到（标识符指向一篇无关论文）** | — | arXiv:2404.14376 实为 Oh, Tran & Kim, "The Life and Legacy of Bui Tuong Phong"（计算机图形学史，2024-04-22）。arXiv 标题检索 `ti:defer AND ti:conformal` 只返回 Verma, Barrejón & Nalisnick 2022（arXiv:2210.16955）与 Bary, Macq & Petit 2025（arXiv:2509.12573），都不是 Angelopoulos 的论文。**判定为 Gemini 编造或混淆，不得引用。** Gemini 同时给的 "A-RCPS 的 OpenReview 链接"本轮未核实；A-RCPS 以 arXiv:2406.10490 为准。 |
| 12 | Geifman & El-Yaniv 2019, SelectiveNet, arXiv:1901.09192 | GPT、Gemini | **存在且信息正确** | arXiv:1901.09192；PMLR v97, pp. 2151–2159 | PMLR 页面 `proceedings.mlr.press/v97/geifman19a.html`：ICML 2019，Yonatan Geifman、Ran El-Yaniv。bib 中 `geifman2019selectivenet` 为 @misc，建议定稿时改为 @inproceedings 并补页码（本轮按"只追加"的要求未改动）。 |
| 13 | Pidan & El-Yaniv 2011（NIPS） | Gemini；scout 此前已收 | **存在且信息正确** | 无 DOI；官方页 `papers.nips.cc/paper/2011/hash/dd458505749b2941217ddd59394240e8-Abstract.html` | 页面元数据：标题 "Selective Prediction of Financial Trends with Hidden Markov Models"，作者 Pidan, Dmitry；El-Yaniv, Ran；Advances in Neural Information Processing Systems，2011。这解决了 fact-check 里 N12 "Pidan & El-Yaniv 未查"的遗留（存在性已确认；正文仍只读过摘要）。 |
| 14 | Chalkidis & Savani 2021 的 DOI | Gemini 给 10.1145/3460340.3482500，作者首字母 "I." | **存在，但 Gemini 的 DOI 与首字母都有误** | **doi:10.1145/3490354.3494379**；arXiv:2110.14914 | Crossref：10.1145/3490354.3494379 = "Trading via selective classification"，Nestoras Chalkidis、Rahul Savani，ICAIF '21 论文集，pp. 1–9，2021-11-03；arXiv 记录自带同一 DOI。Gemini 的 10.1145/3460340.3482500 **不存在**：Crossref 无记录，doi.org 返回 HTTP 404，handle API 返回 responseCode 100（handle not found）。 |

### 核实中顺带发现的问题（不在线索清单内，报告给组长）

1. **Guo (2026) 的作者名有出入。** Crossref（SSRN 存入、带已认证 ORCID 0009-0008-7577-674X）给出的作者是 **Yifan Guo**；OpenAlex 显示为 "Yi Guo"；`paper/references.bib` 的 `guo2026whennot` 写的是 "Guo, Yi"。Crossref 是出版方直接存入的记录，更可信；建议把 bib 改为 "Guo, Yifan"。本轮按"只追加"的要求**没有改动**已有条目，由组长决定。
2. **Guo (2026) 的 Crossref 摘要本轮读到了完整版**（fact-check 只读到前约 1,200 字符）。被截掉的后半段内容是：作者把选择性策略形式化为可预测的组合规则，推出收益与均值–方差效用分解，**给出一个"验证误差部署界"（validation-error deployment bound），并展示"零假设校准的门控如何在安慰剂信号下控制错误部署"**；基准行业轮动实验中，选择性梯度提升把净 Sharpe 从 0.55 提到 0.78、最大回撤从 −39.0% 降到 −21.4%、换手减半以上。含义：它不只是弃权层的又一先例，**还带有形式化的部署界与错误部署控制**——与我们 H-T（监控界）在"选择性部署 + 形式保证"这一层有重合的可能，程度要读全文才能判断。全文仍未读（SSRN 对自动访问返回 403）。
3. **Choi, Jin & Yan 已正式发表**：*The Journal of Finance and Data Science* 11 (2025), 100174, doi:10.1016/j.jfds.2025.100174（Crossref 核实标题与三位作者；许可证字段含 CC BY-NC-ND 4.0）。此前我们只引 NBER 工作论文版。
4. `references.bib` 中 `guo2026whennot` 的 note 仍写 "abstract NOT read"，已过时；同样因"只追加"未改。

---

## 2. 信息不对称与期望收益

这两篇决定了"在信息劣势指标高时弃权"是在回避损失还是在放弃溢价。结论先说：**两篇的方向一致——信息不对称越高，期望收益越高**；其中 Choi–Jin–Yan 是在上交所（A 股）上做的。但两篇的度量都需要我们拿不到的数据（账户级持仓 / 逐笔订单流），且结论针对的是"信息不对称"，不是我们的 Z（筹码成本、异常换手）。

### 2.1 Choi, Jin & Yan — Informed Trading and Expected Returns

- **题录**：NBER Working Paper 18680，2013-01（PDF 首页注明 2016-08 修订），doi:10.3386/w18680；正式发表于 *The Journal of Finance and Data Science* 11 (2025), 100174, doi:10.1016/j.jfds.2025.100174。
- **阅读深度**：**NBER 版全文的正文**（引言、第 I–VIII 节至 VIII.D 开头）通读；结论节、表格与图未逐一核对（文中数字取自正文叙述，不是从表格里重新读的）。期刊版未读，未比对两版差异。PDF 在 `literature/pdfs/www.nber.org_system_files_working_papers_w18680_w18680.pdf.pdf`。
- **样本与市场**：上海证券交易所可流通 A 股，1996-01-02 至 2007-05-31。数据是交易所抽取的账户随机样本的**每日持仓**（机构账户过抽样后加权还原），在交易所内汇总成个股层面的每日机构持股比例；样本含已不活跃账户，作者称无幸存者偏差。股票数从 186 只增至 802 只，年均 573 只。样本期内不允许卖空，"多空收益"只是收益差。**该机构持股序列不对外公开，作者明确说不能用于实际交易。**
- **信息不对称怎么度量**：分两步。(1) 先证明机构有信息优势：按上周机构持股比例的对数变化分五组，最高组减最低组的四因子 alpha 为每月 1.44%（t = 5.62），约合年化 17.3%；多空组合只有 23% 的月份为负。(2) 用**"此前机构持股波动率"**作为个股信息不对称的事前预测量——最近 50 个周度机构持股比例绝对变化的平均值。依据是：它能预测下个月机构在该股上的交易利润（最高组比最低组每周高 0.52 个基点的流通市值，t = 3.53）。
- **效应方向与量级**：**正向。** 按该预测量分五组、流通市值加权、持有一个月：
  - 原始超额收益：最高组 1.70%/月，其余四组 1.27%–1.39%/月；最高减最低 0.32%/月，**不显著**。
  - 单因子 alpha 差 0.51%/月，不显著。
  - 三因子 alpha 差 1.13%/月（t = 4.00），且 alpha 随分组单调上升（最低组 −0.58%/月，最高组 +0.55%/月）。
  - 四因子 alpha 差 **0.90%/月（t = 3.51），即摘要里的年化 10.8%**；剔除 1998 年后为 0.79%/月（t = 3.40）。
  - 分市值：小盘股中不显著（t < 0.7）；中盘 1.03%/月，大盘 1.45%/月（四因子，0.1% 水平显著；引言处另给出年化 12.4% 与 17.4%）。作者把小盘股当作证伪检验：该预测量在小盘股里预测不了机构利润，也就预测不了收益。
  - 持续性：收益差与信息优势差都持续到组合形成后第 10 个月，之后消失，无反转。
  - 稳健性：高组的股票流动性**更好**、其后一个月机构净买入**更少**，所以流动性溢价和机构买入的价格压力都解释不了结果；控制机构持股水平后结果增强。
- **对我们的含义（scout 的判断，不是论文的话）**
  1. novelty_report 里"年化 10.8%"的数字与方向**核实无误**，但要加两条限定：这是控制规模、价值、动量后的 alpha 差；**原始收益差只有 0.32%/月且不显著**。说成"高信息不对称的股票收益高 10.8%"会夸大。
  2. 高信息不对称组的特征是**大市值、低账面市值比、高换手、高流动性、近期收益高**（正文对 Table 5 的叙述）。也就是说，在这篇论文的样本里，高换手与高信息不对称正相关，而高换手本身负向预测下月收益（作者的未列表回归，1% 水平）。这对"异常换手 = 信息劣势，应当弃权"的设想是两面的：换手类变量混着方向相反的两种效应，单看符号无法归因。
  3. 效应集中在中大盘股、小盘股没有；而散户式的筹码 / 换手变量通常在小盘股上最活跃。两者重叠的样本可能很小。
  4. 论文研究的是截面期望收益（月频、组合层面），不是单笔交易的亏损概率。"期望收益更高"和"亏损概率更高"可以同时成立，论文没有报告后者。所以它**没有否定**弃权能降低亏损频率，但它直接支持"必须报告被弃交易的平均收益"这条要求（v3 已列为主要指标）。
  5. 样本止于 2007 年，早于融资融券、股指期货、沪港通；结论能否外推到当前 A 股，**未验证**。

### 2.2 Easley, Hvidkjaer & O'Hara (2002) — Is Information Risk a Determinant of Asset Returns?

- **题录**：*The Journal of Finance* 57(5), 2185–2221, doi:10.1111/1540-6261.00493。
- **阅读深度**：**仅读摘要**（OpenAlex 提供的官方摘要）。原因：期刊版在 Wiley / JSTOR 付费墙后；OpenAlex 与 Unpaywall 登记的唯一开放版本是 SSRN 工作论文（doi:10.2139/ssrn.249072），SSRN 对自动访问返回 HTTP 403；CiteSeerX 的三个镜像链接返回 404，Wayback Machine 无存档。网络搜索找到一个第三方站点（typeset.io）上的 PDF，来源与授权不明，**没有下载**。请用户通过图书馆或 SSRN 手动获取。
- **样本与市场**（据摘要）：纽约证券交易所（NYSE）上市的个股，1983–1998 年。
- **信息不对称怎么度量**（据摘要）：由市场微观结构模型导出的**知情交易概率（PIN）**，逐股估计，然后放入 Fama–French (1992) 的资产定价框架。摘要没有说明估计所用的数据频率与具体输入；PIN 需要买卖订单数这一点来自 Choi et al. 正文的转述（"use the temporal clustering of buy and sell orders"），不是我们从原文读到的。
- **效应方向与量级**（据摘要）：**正向。** "两只股票的 PIN 相差 10 个百分点，期望收益相差每年 2.5%"；作者的主结论是信息确实影响资产价格。
- **争议（二手信息，来自 Choi et al. 正文的文献回顾，所涉论文本轮均未核实）**：Choi et al. 称该实证文献"有争议"——Duarte & Young (2009) 认为 PIN 被定价是因为它与流动性相关而非信息不对称，Easley, Hvidkjaer & O'Hara (2010) 反驳；Mohanram & Rajgopal (2009) 认为 PIN–收益关系对设定和时段不稳健，Aslan et al. (2011) 持相反看法。理论上方向也不统一（Easley & O'Hara 2004 预测正向；Hughes, Liu & Liu 2007 认为在大经济体中因分散化而消失）。这些只能作为待查线索，不能直接引用。
- **对我们的含义**：方向与 Choi–Jin–Yan 一致，市场不同（美国、订单流度量）。它支持 Gemini 的提醒（"高逆向选择时弃权可能丢掉溢价"），但证据强度只到摘要；且 PIN 无法用日频免费数据构造，我们的 Z 不是 PIN 的替代品。

### 2.3 两篇合起来的结论

| | Choi, Jin & Yan | Easley, Hvidkjaer & O'Hara |
|---|---|---|
| 市场 / 样本 | 上交所 A 股，1996–2007 | NYSE，1983–1998 |
| 度量 | 机构持股波动率（需账户级持仓，不公开） | PIN（需订单流） |
| 方向 | 正（信息不对称高 → 期望收益高） | 正 |
| 量级 | 四因子 alpha 差 0.90%/月（年化 10.8%）；原始收益差 0.32%/月不显著 | PIN 差 10 个百分点 ↔ 年收益差 2.5% |
| 阅读深度 | NBER 版正文通读，表格未逐一核对 | 仅读摘要 |

- 对 v3 的影响：两篇都**不直接检验我们的 Z**，也都不涉及单笔亏损概率，所以不构成对 RQ-v3 的否定；但它们使"Z 高时弃权"的默认预期变成**不确定符号**，H-Z 的析因检验必须同时报告亏损频率和被弃交易的平均净收益。v3 "Z 称为持有人状态 / 行为变量，不称对手私有信息的度量"的措辞约束与这里的证据一致——文献里真正度量信息不对称的变量都需要我们没有的数据。
- 仍未做的：EHO 2002 全文；Choi et al. 期刊版与 NBER 版的差异；PIN 争议所涉四篇论文的核实。

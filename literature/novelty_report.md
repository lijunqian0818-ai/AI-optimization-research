# 新颖性报告（阶段 1 第三波）

> 撰写：literature-scout，2026-11-15。对象：`00_idea/research_question.md` 的 **v2 修订**版设想——在 A 股日频多因子信号之上叠加"出手 / 弃权"决策层，动机是扑克式不完全信息博弈（推断自己是否处于信息劣势，没把握就不出手），目标是降低已出手交易的亏损概率与下行风险。
> BibTeX key 对应 `paper/references.bib`。本报告的结论**尚未经过跨模型审查**（GPT / Gemini 的 `--task novelty` 与 ARS `fact-check` 是下一波的事）。

## 0. 结论先行

1. **"弃权层"本身已被多次发表，撞车风险：高。** 不只是 Chalkidis & Savani (2021)。2026 年 2 月的 Sanderink（arXiv:2603.13252）已经做了"LightGBM 截面选股排序器 + 策略层是否交易的门控 + 个股层不确定性截尾"，并且采用了时点安全（PIT）、walk-forward、purging / embargo、冻结留出集——与我们 v2 的实验设计几乎逐项重合，只是市场是美股、没有理论、没有博弈。量化业界的 meta-labeling（Joubert 2022）是同一结构的通行名称。**"在因子信号上加一个决定出手 / 不出手的二级模型"不能再作为贡献来写。**
2. **"博弈机制 + 弃权"层面，撞车风险：中。** 没有检索到"从知情交易者 / 逆向选择模型推导出股票入场弃权规则并检验其可证伪限制"的论文（直接撞车证据：未发现）。但评级不给"低"，理由有三：(a) 理论部件全是经典结果（Milgrom–Stokey 无交易定理、Glosten–Milgrom 逆向选择、Dow–Werlang 与 Easley–O'Hara 的不参与区间），审稿人很容易认为是旧结论的重新包装；(b) 检索范围有硬缺口（SSRN 全文、知网、Google Scholar、券商研报都没查）；(c) 经验证据的方向对我们不利——Choi, Jin & Yan (2013) 用上交所持仓数据报告"信息不对称越高，期望收益越高"，即"劣势时弃权"可能恰好放弃了风险溢价。
3. **理论工具也不是空白。** 我们 v2 设想的"对已选交易风险做序贯（鞅）监控、不需要可交换性"在通用机器学习文献里已有现成结果：Conformal Selective Acting（Khosravi & Huo 2026，arXiv:2605.20270；**场景是 LLM 部署，不是金融**；按阈值维护 e-process、对 **selective risk** 给 anytime-pathwise 保证）和 A-RCPS（Xu et al. 2024，NeurIPS）。金融侧，MohammadpourAzari et al. (2026) 已给出带延迟反馈与弃权的对抗性遗憾界和路径式安全界。**能声称的理论新意只剩"把这类工具适配到交易流"**（同日多股按日聚合、标签延迟与重叠持仓、漂移项），这是增量，不是新定理类型。
4. **剩余空间**（按把握从大到小）：G3（筹码 / 换手类变量对弃权层的增量价值，A 股、样本外、匹配覆盖率）——英文文献内未见，属于干净的实证问题；G1（机制导出的可检验限制）——未见，但难度和被质疑的风险都高；G2 的"交易流适配"——增量；G4（A 股约束）——未见但单独不构成贡献。
5. **建议**：见 §7。简言之，论文不能以"弃权层"立论；主打应是 (i) 一个最小知情交易者模型导出的、通用亏损预测器给不出的限制，加 (ii) G3 的严格增量检验，理论保证定位为"已有 anytime-valid selective risk 工具在交易流上的适配"。若 (i) 在试点中站不住，就老实降级为"Z 是否有增量预测力"的实证论文。

---

## 1. 检索范围与局限

**已做（2026-11-15）**

| 来源 | 做了什么 |
|---|---|
| 既有材料 | `literature/candidates.csv`（156 篇，排除 C013/C014/C065/C068/C070 后 151 篇）、`literature/ars_lit_review.md`、`literature/resources.md` |
| arXiv API 字段检索 | 30 条查询（`abs:` / `ti:` / `cat:` 组合），覆盖：selective classification / selective prediction / abstain / abstention / reject option / meta-labeling / conformal / learning to defer × trading / stock / portfolio / financial；adverse selection / informed trading × no-trade / abstain / uninformed；A-share / Chinese stock × price limit / T+1 / abstain / selective / conformal；chip distribution / capital gains overhang；poker × trading；selective risk / risk control × non-exchangeable / distribution shift / martingale / e-process；q-fin 各子类里标题含 abstain / abstention；trade filter；Glosten × RL / bandit |
| OpenAlex（`tools/search_resources.py papers`） | 8 条查询：chip distribution、capital gains overhang China、meta-labeling、selective classification stock trading、abnormal turnover informed trading China、T+1 / price limit ML、adverse selection nonparticipation、conformal stock selection A-share |
| WebSearch | 9 条查询（含 1 条中文：筹码分布 因子 A股 机器学习） |
| 逐条核实 | 本报告引用的每篇文献都用 arXiv API（按 ID）或 OpenAlex / Crossref（按 DOI）核对了标题与作者；PMLR 与 NeurIPS 页面用 WebFetch 打开 |
| 全文阅读 | 见 §2 各篇的"阅读深度" |

**没做 / 做不到（这些缺口直接限制 §4、§8 里"未发现"类说法的强度）**

- **知网 / 万方 / 维普等中文数据库：未检索**（无访问途径）。筹码分布、因子择时、A 股量化的中文期刊论文和硕博论文完全没覆盖。这对 G3、G4 是实质性缺口。
- **券商金工研报：未检索。** 筹码类因子在国内卖方研报中很可能已有系统回测。
- **SSRN 全文：未检索**（SSRN 页面对自动访问返回 403）。只通过 OpenAlex 看到题录。其中一篇标题高度相关：Guo (2026), *When Not to Trade: Leakage-Aware Selective Machine Learning for Factor Rotation*, doi:10.2139/ssrn.7021298——撰写本报告时摘要读不到；第 1 轮检查后经 Crossref 读到了摘要（见 §2.6、§10），**全文仍未读，需要用户人工打开**。
- **Google Scholar、Semantic Scholar：未检索**；因此没有做引用链追踪（谁引用了 Chalkidis & Savani 2021）。
- **付费墙**：Joubert (2022)、Meyer et al. (2023)、Chakraborty & Yilmaz (2008) 只读了摘要。
- arXiv API 对带括号的布尔查询噪声很大，有 3 条查询返回的全是无关结果（已在下文按"无有效结果"处理，不当作"不存在"的证据）。
- 所有读过的网页、论文、摘要中**没有发现写给自动化 agent 的指令**。

---

## 2. 最接近的 5 篇工作

选取标准：与"因子信号之上的出手 / 弃权层 + 保证 + 机制"三个要素的重合度。

### 2.1 Sanderink (2026) — When Alpha Breaks: Two-Level Uncertainty for Safe Deployment of Cross-Sectional Stock Rankers 〔`sanderink2026alpha`，arXiv:2603.13252〕

- **阅读深度**：第 1–4 节（引言、相关工作、问题设定、方法）和第 8 节（局限）通读；第 5–7 节（实验、结果、讨论）按关键词扫读。单作者预印本，未见同行评议信息。
- **解决什么问题**：截面选股排序模型在非平稳下会"失灵"（2024 年 AI 主题行情中 60 / 90 日 RankIC 转负）。把部署拆成两个决策：(i) 哪些个股头寸要谨慎；(ii) 今天策略**该不该交易**。
- **方法**：基础模型是 LightGBM 排序器（7 个 PIT 特征）。个股层：把 DEUP 改到排序损失上，用二级 LightGBM 预测 rank displacement，得到认知不确定性 ê(x)；发现 ê 与 |score| 结构性相关（中位 Spearman 0.616），所以反向不确定性加权会削掉最强信号，改用"只截最不确定的 15% 尾部、减仓 30%"。策略层：regime-trust gate G(t)，由**已到期的滚动 RankIC**（EWMA）、特征 / 得分漂移、模型间分歧合成；G(t) < 0.2 则全仓现金。报告 80% 精度、47% 弃权率。
- **理论保证**：**无**定理。只有一个补充实验用 split conformal 区间（可交换性假设），不是主张。
- **数据与市场**：美股，最多 100 只 AI 主题股票，2016-02 至 2025-02，多空组合（top / bottom 10），20 日持有期，10 bp 成本。Walk-forward 109 折、90 日 embargo、purging；DEV（2016–2023）/ FINAL（2024+）冻结留出。
- **博弈 / 知情交易者机制**：无。明确是"模型可靠性"视角。
- **筹码成本 / 换手等"他人状态"变量**：无。误差预测器特征是得分、截面排名、波动率、动量、ADV、VIX 与市场状态。
- **与我们的区别（逐点）**
  1. 市场：美股主题池 vs A 股；多空 vs 只做多；无 T+1 / 涨跌停。
  2. 弃权依据：模型自身的历史效力与认知不确定性 vs 我们设想的"逆向选择代理变量 Z"。**它的结论对我们是警示**：VIX 等市场状态代理预测"模型是否失灵"的 AUROC 只有 0.449，比随机还差；有效的是"模型最近到底灵不灵"。这意味着我们的 Z 必须打赢一个很强的、简单的对照——滚动已实现效力门控。
  3. 保证：它没有；我们打算有（H2b）。
  4. 机制：它没有；我们打算有（H1-机制）。
  5. 目标量：它看 Sharpe 与危机期回撤；我们看已出手交易的亏损概率。
  6. **重合部分（不能再当贡献）**：因子 / 排序信号之上的两级出手门控、二级模型预测一级模型的错误、PIT 安全、purging、冻结留出、与波动率 / VIX 过滤的对比、"二值门控优于连续缩放"的发现。
- **可作基线吗**：**必须**。至少复现其策略层门控的核心（已到期 RankIC 的 EWMA 阈值）和个股层 DEUP 截尾。

### 2.2 Chalkidis & Savani (2021) — Trading via Selective Classification 〔`chalkidis2021trading`，ICAIF '21，arXiv:2110.14914〕

- **阅读深度**：全文通读（arXiv v2，8 页）。
- **解决什么问题**：二分类器预测涨跌会"永远持仓"；让分类器可以弃权，弃权即不持仓。作者自称"据我们所知，选择性分类用于交易策略设计此前未被探索"（原文第 1 节）。
- **方法**：逻辑回归、随机森林、前馈网络、LSTM 四种分类器 × 二分类 / 三分类（第三类为小幅波动）× 四套特征（OHLCV、均线、volume-at-price、买卖方向与主动性）。弃权用 Geifman & El-Yaniv (2017) 的 **SGR 算法**（对最大类概率设阈值，使 selective risk 以高概率不超过目标值），阈值按验证集 MCC 选。
- **理论保证**：自身无新理论。沿用 SGR 的保证，其前提是**训练 / 校准样本 i.i.d.**（原文第 3 节照搬该设定）；论文没有讨论金融时间序列违反 i.i.d. 的问题。
- **数据与市场**：CME 五种金属期货（金、铜、钯、铂、银），30 分钟 bar，2011-02 至 2019-05；锚定 walk-forward（训练 6 个月起、验证 2 个月、测试 16 个月）；多空；滑点 0–0.5 tick。
- **结果要点**：弃权后准确率在所有配置下都提高（二分类约 +1.5–3 个百分点，覆盖率 37–63%）；回测 Sharpe 多数改善，但在 0.3 tick 滑点下多数配置不盈利；更丰富的特征（含 volume-at-price）没有带来好处。
- **博弈 / 知情交易者机制**：无。
- **"他人状态"变量**：没有筹码成本 / 换手。但 **volume-at-price 特征（过去 6 小时成交量在过去 1 个月价格区间 12 个桶里的分布）在形式上就是日内版的"筹码分布"**，买卖主动性特征接近订单流毒性。这些是分类器的普通输入特征：弃权由分类器的最大类概率决定，所以它们已间接影响弃权，但没有针对它们的专门增量检验；作者报告它们无增益。
- **与我们的区别（逐点）**
  1. 资产与频率：商品期货 30 分钟 vs A 股个股日频截面。
  2. 弃权依据：分类器自身的最大类概率 vs 外部状态变量 Z。
  3. 架构：分类器直接弃权 vs 在既有多因子打分之上叠加独立的弃权层。
  4. 保证：i.i.d. 下的 SGR vs 我们要处理时间依赖 / 漂移。
  5. 没有与非弃权式风控（波动率过滤、随机稀疏化到同覆盖率）比较；我们的 v2 要求匹配覆盖率的对照。
  6. 目标量：它报告准确率与 Sharpe；"亏损概率"在它那里就是 1 − 准确率——**所以"弃权降低已出手交易的错误率"这个核心现象它已经展示过了**。
- **可作基线吗**：**必须**（即"置信度阈值 + SGR"基线）。

### 2.3 MohammadpourAzari, Zarei & Fazli (2026) — Safe Portfolio Learning from Untrusted Predictions 〔`mohammadpourazari2026safe`，arXiv:2611.04826〕

- **阅读深度**：第 1 节（含相关文献）通读；第 2–3 节的门控定义、六条假设、定理 1–4 的陈述读过；数据与局限部分按关键词扫读；证明未读。预印本（2026-11-03）。
- **解决什么问题**：机器预测的方向、可靠性、时机都不可信，且多期重叠持仓的反馈有延迟时，如何安全地使用预测。
- **方法**：每个决策日在三个候选组合间选择——Safe（与预测无关的锚定组合，**满仓**）、Follow（按信号方向）、Reverse（反向）。Fixed-Share + 外层 Hedge 的 share-adaptive master 学三者的概率；**证据门控**（evidence gate）在到期证据的单侧下界统计量不过关时把方向性概率质量转给 Safe——这就是它的"弃权"；延迟抵押预算为每个未结清头寸预留最坏损失；隔离账户限制可动用资金比例。
- **理论保证**：有，且**不需要任何分布假设**（对任意有界奖励序列成立）。定理 1：相对任意切换比较序列的 tracking regret；定理 2：延迟反馈的精确约化；定理 3：anytime 路径式抵押安全界；定理 4：端到端合成。六条假设都是"架构不变量"（可在实现中逐条审计），不是统计假设。
- **数据与市场**：美股，24 只开发池 + 82 只冻结留出池，日频，2014-02 至 2025-09，只做多、满仓、5 bp 成本。**实证结果是负面的**：预先指定的 Reverse 方向和事后的 Follow 方向都没有跑赢等权；作者明确说贡献是"安全地使用不可信预测，而非展示 alpha"。
- **博弈 / 知情交易者机制**：理论上把市场当作对抗性序列（在线学习意义上的"对手"），但**没有**信息集、知情交易者或逆向选择的建模。
- **"他人状态"变量**：无（40 个价格与会计特征）。
- **与我们的区别（逐点）**
  1. 保证的对象：相对 Safe 的累计财富 / 遗憾 vs 我们的"已出手交易的亏损概率"。它**不**控制已选交易的亏损率。
  2. 弃权的含义：转到满仓的 Safe 组合 vs 我们的不买（空仓 / 现金）。
  3. 粒度：组合层三选一 vs 逐笔 / 逐股的买不买。
  4. 假设：对抗性（最弱）vs 我们打算用的"鞅 / 漂移项"随机假设——它的假设比我们弱，因而界也更保守（实证里财富与 Safe 的差距最多 15.9 bp，等于几乎不承担方向风险）。
  5. **重合部分**：延迟到期反馈、重叠持仓、弃权作为显式动作、"不假设预测有效"的保证。v2 里"标签延迟 + 重叠持仓下的序贯保证"这一点**它已经处理过**，只是目标量不同。
  6. 市场与机制：美股、无博弈机制 vs A 股、机制导出。
- **可作基线吗**：部分。完整复现成本高；建议把"证据门控"（到期奖励的单侧下界不过关就不出手）抽出来当一个基线，并在相关工作中明确对比保证类型。

### 2.4 Zhang et al. (2023) — Learning to Abstain From Uninformative Data 〔`zhang2023abstain`，arXiv:2309.14240〕

- **阅读深度**：第 1–2 节通读；假设、定理 1–4 的陈述、实验数据集部分读过；证明未读。预印本（作者多来自 Morgan Stanley；正式发表情况**未验证**）。
- **解决什么问题**：金融等高噪声领域里，大部分样本是"无信息的"（标签近乎随机），只有少数"口袋"可预测；要同时学预测器和选择器，在无信息样本上弃权。引言用统计套利中 OU 价差"近零处不可预测、超阈值才可预测"作动机。
- **方法**：在 Massart 型数据依赖标签噪声模型上加一个"有信息 / 无信息"二分结构；提出新的 selector loss（选中的样本拟合好，未选中的样本上预测器表现接近随机），交替优化预测器与选择器（ISA 算法）。
- **理论保证**：有。选择器风险的 minimax 最优样本复杂度界、PAC 式恢复有信息样本、在选中子集上训练的分类器有更好的风险上界。**假设 1 明确要求样本 i.i.d.**，且假设存在真实的有信息 / 无信息指示函数。
- **数据与市场**：半合成（MNIST + Fashion-MNIST、SVHN）；真实数据三个：Oxford realized volatility、乳腺超声图像、Lending Club。**没有交易回测**，没有收益 / 成本指标。
- **博弈 / 知情交易者机制**：无。"无信息"是统计意义（高标签噪声），不是"对手有信息而我没有"。
- **"他人状态"变量**：无。
- **与我们的区别（逐点）**
  1. "无信息"的来源：数据生成过程里的噪声结构 vs 我们设想的"对手方信息优势"。两者可能观测等价——**如果我们的 Z 只是在识别"高噪声样本"，那就落在这篇论文的框架里**，这正是 H3′ 要防的情形。
  2. 假设：i.i.d. vs 时间依赖 / 漂移。
  3. 实证：无交易 vs A 股回测。
  4. 选择器：从预测器的错误中学出来（纯统计）vs 机制导出 + 可检验限制。
- **可作基线吗**：**应该**。ISA 是"学习式弃权"的最强金融动机基线，比 SelectiveNet / Deep Gamblers 更贴题。

### 2.5 Joubert (2022) — Meta-Labeling: Theory and Framework 〔`joubert2022metalabeling`，J. Financial Data Science 4(3)〕

- **阅读深度**：**仅读摘要**（付费墙，未找到免费全文）。配套的 Meyer, Barziy & Joubert (2023)〔`meyer2023metalabeling`〕也仅读摘要。
- **解决什么问题 / 方法**（据摘要）：meta-labeling 是"叠在基础主策略之上的 ML 层，用来确定仓位、过滤假阳性信号、改善 Sharpe 与最大回撤"；论文把此前散见的做法整合成框架，解释二分类指标与策略表现的关系，把 meta-labeling 拆成三个组件并用受控实验展示各自作用，讨论该用哪类特征。2023 年的续篇研究二级模型输出概率的校准与六种仓位算法。
- **理论保证**：摘要未提及形式化保证；标题中的 "Theory" 指框架性阐述（**未验证**，需读全文确认）。
- **数据与市场**：摘要称"受控实验"；具体数据**未验证**。
- **博弈 / "他人状态"变量**：摘要未提及。
- **与我们的区别**
  1. **结构上没有区别**：我们的"多因子信号 → 二级模型决定出手 / 不出手"就是 meta-labeling。v2 已把它列为必须比较的基线（"通用监督亏损预测器，含与不含 Z"），这个定位是对的。
  2. 我们可能的差异只在：二级模型的**输入从哪来**（机制导出的 Z 及其函数形式限制）和**阈值怎么定**（带保证的序贯校准 vs 经验阈值）。
  3. 市场：A 股及其约束。
- **可作基线吗**：**必须**，而且是 H3′ 的核心对照。
- **待办**：请用户通过图书馆获取这两篇 JFDS 全文放入 `literature/pdfs/`。

### 2.6 评估过但未列入前 5 的候选（及取舍理由）

| 文献 | 核实 / 阅读深度 | 为什么不在前 5 |
|---|---|---|
| Zarei et al. (2026), Conformal Risk Certificates… Gated RL〔`zarei2026conformal`，arXiv:2611.14699〕 | 摘要与引言通读，其余扫读 | "门"是对 PPO 提出的组合权重做二阶锥**投影**（超出语义风险预算才干预），不是买 / 不买的弃权；资产是 9 只美国行业 ETF；风险状态来自 LLM 读新闻；conformal 半径在滚动两年窗口的分桶里校准，作者自己承认依赖"局部近似可交换性"，没有时间依赖下的定理。与 2.3 同一作者群，2.3 更接近。可在相关工作里作为"RL + conformal 门"的代表。 |
| Nabar & Shroff (2023), Conservative Predictions on Noisy Financial Data〔`nabar2023conservative`，ICAIF '23〕 | 摘要与引言通读，其余扫读 | 级联模型在不确定样本上弃权，"模型拒绝预测就不交易"；印度股票 5 分钟 K 线；自定义"每笔平均收益"效用。无理论、无博弈、日内。与 2.2 同类且更弱，作为"弃权 = 不交易"的第三个独立先例引用。 |
| Pidan & El-Yaniv (2011), Selective Prediction of Financial Trends with HMMs〔`pidan2011selective`，NIPS 2011〕 | 仅读摘要 | 最早的"弃权 + 金融趋势预测"（Chow 式拒绝 vs 在低质量隐状态弃权）。说明这个想法至少有 15 年历史。**注意它比 Chalkidis & Savani 早 10 年**，后者"首次"的说法只限于"交易策略设计"。 |
| Ziyin et al. (2019), Deep Gamblers〔`ziyin2019deepgamblers`，NeurIPS 2019〕 | 摘要、引言、定理陈述读过 | 把 m 类选择性分类改成 m+1 类，损失取赛马下注的 doubling rate，弃权 = 保留赌注。它证明的是下注问题的最优解性质，**不是** selective risk 的保证；实验是 SVHN / CIFAR-10。对我们的意义是叙事上的：**"赌博 / 下注思维 → 弃权"已被占用**，但那是 Kelly 式的单人下注，没有对手、没有信息集。可作学习式弃权基线。 |
| Chakraborty & Yilmaz (2008), Microstructure Bluffing with Nested Information〔`chakraborty2008bluffing`，AER 98(2)〕 | **仅读摘要**（付费墙） | 证明拥有长期私有信息的内幕者有动机"诈唬"——早期做亏本交易，以便之后以更有利的价格交易；并且存在一群信息比内幕者粗、比做市商细的理性交易者，均衡中"跟随"内幕者。**这是文献里与"扑克"最贴近的正式模型**，但研究的是知情方的操纵，不是劣势方的入场 / 弃权规则，也没有数据。对我们的意义：(a) 可作为最小知情交易者模型的出发点之一；(b) 它提醒"跟随知情资金"在均衡中可能正是被诈唬的对象——支持"没把握就不出手"的直觉，但推不出可用的日频规则。 |
| Khosravi & Huo (2026), Conformal Selective Acting〔`khosravi2026csa`，arXiv:2605.20270〕 | 仅读摘要 | 非金融（LLM 部署），但**理论上最接近我们的 H2b**，见 §4 G2。 |
| Hao et al. (2026)〔`hao2026coverage`〕、Torres et al. (2026)〔`torres2026finabstain`〕、Manoharan et al. (2026)〔`manoharan2026uqlob`〕 | 仅读摘要 | 加密货币事件合约 / LLM-RAG（摘要自述结果为模拟）/ 加密货币订单簿上的选择性预测。说明 2026 年这个框架很活跃，但都不是股票日频、无机制。 |
| Guo (2026), When Not to Trade: Leakage-Aware Selective ML for Factor Rotation〔`guo2026whennot`，SSRN doi:10.2139/ssrn.7021298〕 | **仅读摘要**（Crossref 存入的摘要；SSRN 页面 403，**全文未读**） | **弃权层的又一先例（策略层）。** 据摘要：研究"机器学习策略何时应当拒绝交易"；对象是**因子与行业轮动**；滚动起点协议；只有当 ML 信号在验证窗口上相对回落基准的改进超过校准阈值时才部署，否则**弃权并回落到基准组合**；形式化为可预测的组合规则，给出收益 / 均值–方差效用分解。读到的摘要里没有博弈或知情交易者机制，也没有筹码 / 换手变量。未列入前 5 的原因：是因子 / 行业轮动的策略层开关，不是个股入场；且只读到摘要。全文读后可能需要调整排位（见 §10）。 |

---

## 3. 对比总表

| | 弃权 / 不交易决策 | 作用在因子 / 排序信号之上 | 形式化保证（假设） | 博弈 / 知情交易者机制 | 筹码 / 换手类"他人状态"变量 | 市场与频率 |
|---|---|---|---|---|---|---|
| Sanderink 2026 | 是（策略层 + 个股层） | 是（LightGBM 排序器） | 无 | 无 | 无 | 美股 100 只，日频信号，20 日持有，多空 |
| Chalkidis & Savani 2021 | 是 | 否（分类器自身弃权） | 沿用 SGR（i.i.d.） | 无 | 有 volume-at-price 特征，但只是普通特征 | 金属期货，30 分钟，多空 |
| MohammadpourAzari et al. 2026 | 是（转到 Safe 组合） | 是（不可信预测之上） | 有：遗憾界 + 路径式安全界（对抗性，无分布假设） | 无（对抗序列，无信息结构） | 无 | 美股 24 + 82 只，日频，只做多 |
| Zhang et al. 2023 | 是（统计弃权） | 否 | 有：minimax / PAC（i.i.d. + Massart 型噪声） | 无 | 无 | 无交易实验 |
| Joubert 2022（仅摘要） | 是（过滤假阳性 + 仓位） | 是 | 摘要未提 | 摘要未提 | 摘要未提 | 未验证 |
| **我们（v2 设想）** | 是 | 是 | 目标：已出手交易亏损概率的序贯 / 带漂移项保证 | 目标：最小知情交易者模型 → 可检验限制 | 是（核心检验对象） | A 股，日频，只做多，T+1，涨跌停 |

---

## 4. 四个"可能的空白"逐条检验

### G1 从知情交易者 / 逆向选择机制**推导出**的股票入场弃权规则，且给出通用亏损预测器得不到的可检验限制

- **结论：部分成立。**
- **支持"空白存在"的证据**
  - 所有检索到的"弃权用于交易"的论文（§2 的 2.1–2.5、Nabar & Shroff、Pidan & El-Yaniv、Hao et al.、Torres et al.、Manoharan et al.）弃权依据都是统计量：分类器置信度、认知不确定性、滚动已实现效力、隐状态质量。没有一篇从信息结构出发。
  - arXiv 字段检索 `abs:"adverse selection" AND (no-trade / abstain / "not to trade") AND (learning / uninformed)` 返回 10 条，全部是做市 / AMM / 执行层面（如 Jafree et al. 2025、Cartea & Sánchez-Betancourt 2025），没有方向性入场决策。`abs:"informed trad" AND (uninformed / retail) AND (entry / abstain / participation) AND learning`：无结果。`abs:"informed traders" AND "machine learning" AND daily`：无结果。`abs:Glosten AND (RL / bandit / online learning)`：只有 DeFi 做市一篇。
  - `abs:poker AND (stock / trading / financial market)`：7 条结果里只有 C012（Cherednik 2019）涉及交易，其余是纯博弈算法。WebSearch 找到的"扑克 × 投资"全是从业者评论和博客，没有学术论文把弃牌形式化为入场规则。
- **削弱"空白"的证据（必须正视）**
  - **理论部件是现成的经典结果**：Milgrom & Stokey (1982) 无交易定理；Glosten & Milgrom (1985) 逆向选择下的价差与市场崩溃；Rock (1986) 中未知情投资者在 IPO 配售里的赢家诅咒；Dow & Werlang (1992) 与 Easley & O'Hara (2009) 在模糊厌恶下的不参与区间。"信息劣势方在一个区间内最优地不交易"是教科书级结论（以上经典文献本次**只核实了题录**，具体定理形式要由 `researcher` 读原文确认）。我们能新增的只能是：把它落到"给定基础 alpha 与可观测代理变量 Z 的入场阈值"，并推出**对函数形式的限制**（例如阈值对 Z 的单调性、与流动性的交互符号）。这是窄的贡献。
  - **最接近的"学习式逆向选择过滤器"**：Cartea, Duran-Martin & Sánchez-Betancourt (2023, *Detecting Toxic Flow*) 让经纪商用在线贝叶斯神经网络预测客户成交是否"有毒"，据此决定内部化还是对冲出去。这是"按逆向选择概率决定接不接这笔单"的学习规则——结构同构，但主体是外汇经纪商、数据是专有逐笔成交、规则是学出来的不是推导出来的。
  - **经验方向可能相反**：Choi, Jin & Yan (2013, NBER w18680) 用上交所代表性持仓数据，按"机构交易激进程度"排序，报告最高五分位下月年化收益比最低五分位高 10.8%，结论是"信息不对称提高期望收益"（据摘要）。Easley, Hvidkjaer & O'Hara (2002) 的 PIN 定价是同一方向（仅题录）。**如果高逆向选择暴露对应的是更高的期望收益，那么"在 Z 高时弃权"降低亏损概率的同时可能系统性地放弃溢价**——这恰好是一条可检验的、通用亏损预测器不会自动给出的限制（亏损概率与期望收益在 Z 上反向变动），但也可能直接否定 idea 的实用价值。
  - **日频公共数据的识别问题**没有任何检索到的论文解决：PIN / VPIN 需要订单流（Easley et al. 1996, 2012）；筹码成本在文献里是行为金融变量（处置效应、参考点），不是信息不对称度量（Grinblatt & Han 2005）。
- **没检索的**：SSRN 全文、金融学期刊全文库（JF / JFE / RFS 的近年工作论文可能有"散户最优不参与"的结构估计）、中文文献。

### G2 时间依赖 / 分布漂移下对"已出手交易的亏损概率"的保证（序贯监控或带漂移项的界）用于交易

- **结论：部分成立——"用于交易"成立，"保证类型本身"不成立。**
- **已有的通用理论（削弱空白）**
  - Khosravi & Huo (2026), *Conformal Selective Acting*（arXiv:2605.20270；完整标题后半为 "Anytime-Valid Risk Control for RLVR-Trained LLMs"，**场景是 LLM 部署，不是金融**，没有交易实验）：摘要明确把问题定位为"离线 conformal-risk 需要可交换性；在线 conformal 只控制长期平均；非可交换扩展只有边际有效性；A-RCPS 控制的是边际风险而非 selective risk"，然后给出"每个阈值一个 Ville 型 e-process、Bonferroni 网格、对 **selective risk** 的 anytime-pathwise 界 R_T^act ≤ α + O(N_T^{-1/2})"，条件是可预测更新 + 保序校准的单调风险。**这基本就是我们 v2 里 H2b 的候选路线**（仅读摘要；条件是否适用于交易流要读全文）。
  - Xu, Karampatziakis & Mineiro (2024, NeurIPS), A-RCPS：序贯、数据自适应收集下的 anytime-valid 风险控制（边际风险）。
  - Hultberg et al. (2026), Anytime-Valid Conformal Risk Control；Bai & Jin (2026), SCoRE（用 e-value 做 selective risk 控制，基于可交换性，称可扩展到分布漂移）；Xu, Guo & Wei (2025), Selective CRC（可交换）；Gibbs & Candès (2021), ACI（任意数据生成过程下的长期覆盖频率）；Wang & Simeone (2026), 延迟且有损反馈下的在线 CRC；Gangrade et al. (2021), 对抗环境下的在线选择性分类。（以上均仅读摘要。）
- **已有的金融侧保证（削弱空白）**
  - MohammadpourAzari et al. (2026)：延迟 + 重叠持仓 + 弃权下的对抗性遗憾界与路径式安全界（§2.3）。目标量是财富 / 遗憾，不是亏损概率。
  - Benhamou et al. (2026, ICAIF 2026 接收), PROMOTE：用成本感知的 e-process 对"交易规则是否有正期望"做 anytime-valid 检验，允许候选规则相关、自适应出现、无限期监控。它控制的是"错误提拔一条无效规则"的概率——**鞅 / e-process 方法已经进入交易研究**，只是对象是规则而不是逐笔交易。
  - Zarei et al. (2026)、Schmitt (2026, 非平稳组合 VaR 的 conformal 校准)、Chen et al. (2026, 对抗环境下的在线 CVaR conformal 控制)：下行风险的 conformal 控制，对象是组合尾部损失。
- **仍然没找到的（空白的剩余部分）**
  - 把"已出手交易中亏损的比例"作为被控制的 selective risk，在**交易流**上给出保证，并处理：同一天多只股票不独立（按日聚合）、标签在持有期结束后才到期、重叠持仓、漂移项。arXiv 上 q-fin 各子类 × (selective + coverage) 的 10 条结果、q-fin × conformal 的 10 条结果里都没有。
  - Chalkidis & Savani (2021) 直接把 i.i.d. 的 SGR 用在金融时间序列上，没有讨论假设违背。
- **对定位的含义**：H2b 不能写成"首个不依赖可交换性的 selected-risk 保证"。准确的说法是"把 anytime-valid selective risk 控制（CSA / A-RCPS 一系）适配到带延迟标签和日内截面相关的交易流"。定理的新意要落在适配带来的具体困难上，否则会被审稿人指为已知结果的直接推论。`researcher` 开工前**必须读 CSA 和 A-RCPS 全文**。
- **没检索的**：统计学期刊（JASA / AoS / JRSSB）的全文库；Google Scholar 引用链。

### G3 筹码成本 / 换手异常等变量对弃权层的**增量**价值（在置信度、波动率、流动性过滤之外），A 股、样本外、匹配覆盖率

- **结论：英文文献范围内成立；总体无法判断（中文文献与研报未检索）。**
- **证据**
  - arXiv：`abs:"chip distribution" OR "cost distribution of holders" OR ("capital gains overhang" AND China)` 返回的全是半导体 / 量子芯片论文；`abs:"capital gains overhang"` 只有 Xu (2025)——一篇 A 股上复现 Wang, Yan & Yu (2017) 的论文，研究的是 CGO 与风险–收益关系的交互，不涉及弃权、ML 或样本外交易。
  - OpenAlex `chip distribution stock China…`：无相关结果。候选清单里唯一直接以筹码分布指标选股的英文论文是 Zhang (2020, IEEE CDS 会议，C105)，**仅核实题录**，内容未读；从标题看是选股策略而非弃权层的增量检验。
  - WebSearch（中文关键词"筹码分布 因子 A股 机器学习 选股 实证"）：没有返回学术论文，只有软件说明和泰迪杯竞赛论文（多因子 ML 选股，与筹码无关）。**这不能说明中文文献里没有**——搜索引擎对知网内容几乎无覆盖。
  - 已知的相关证据是关于"收益预测"而非"弃权增量"：A 股上 CGO 的符号与美国不一致（Pan et al. 2025 报告资本利得与截面收益负相关；Xu 2025 报告 CGO × 风险代理的交互项在中国多为负）；异常换手率在 Liu, Stambaugh & Yuan (2019) 的中国因子模型里是情绪因子 PMO 的构造变量（仅题录），Xing et al. (2024) 研究 PMO 拥挤度（仅题录）。
  - Sanderink (2026) 的误差预测器用了波动率、ADV、动量、VIX、市场状态，**没有**成本基础或换手异常变量；Chalkidis & Savani (2021) 的 volume-at-price 特征无增益（但那是期货、日内、且没做增量检验设计）。
- **判断**：这是四个空白里最"干净"的一个实证问题，而且 v2 的 H1′ / H3′ 已经把它设计成可证伪的形式。风险在于：(a) 国内研报 / 硕博论文很可能做过筹码因子的分层回测，我们的差异必须落在"对弃权层的增量、匹配覆盖率、严格样本外"上；(b) 结果可能是阴性的。
- **没检索的**：知网、万方、券商金工研报、聚宽 / 米筐等社区的因子研究、SSRN。

### G4 A 股特有约束（T+1、涨跌停、只做多）下的选择性交易

- **结论：部分成立（未发现直接先例，但单独不足以构成贡献）。**
- **证据**
  - 未找到"A 股个股 + 弃权 / 选择性预测 + T+1 / 涨跌停"的论文。arXiv `(A-share / Chinese stock) AND (abstain / selective / uncertainty-aware / conformal)` 与 `abs:"A-share" AND ("price limit" OR "T+1")` 两条查询返回的几乎全是无关结果（API 布尔解析问题），**按"无有效结果"处理，不作为不存在的证据**；WebSearch 的对应查询只返回下面几篇邻近工作。
  - 邻近工作：
    - Zhang et al. (2022/2023, IEEE Access)：RL + T+1 规则，把"受限的卖出仓位"写进奖励函数；是日内高频框架的参数自适应，不是弃权（仅读摘要）。
    - Fang & Ślepaczuk (2026, arXiv:2606.09478)：沪深 300 **指数**高频数据，XGBoost 收益预测 + "低波动门控、阈值校准、换手控制"；摘要称朴素策略扣成本后失败，带门控和阈值的设计能改善防御性表现。这是"A 股 + 门控 / 阈值"最近的一篇，但对象是指数、依据是波动率状态、无 T+1 / 涨跌停讨论（仅读摘要）。
    - Liang & Hu (2024, J. Forecasting)：预测 A 股个股是否触及涨跌停（仅读摘要）——与"涨停买不进"的可成交性建模相关。
    - Liu et al. (2026), AStockArena：A 股实时交易的 LLM 智能体审计基准，含"历史交易过滤回放"（仅读摘要）。
    - Leippold, Wang & Zhou (2022)：A 股 ML 因子基准（仅题录）。
  - T+1 对弃权层有一个结构性含义，检索到的文献都没处理：买入当日不能卖出，所以"出手"是至少隔夜的承诺，弃权的期权价值更高；涨停日买不进则使"出手集合"被可成交性内生截断（选择偏差）。这可以写成一小节，但更像实验设计的严谨性要求，而不是独立贡献。
- **没检索的**：中文文献（T+1 与涨跌停制度的实证研究主要在中文期刊）。

---

## 5. 撞车风险评级

| 层面 | 评级 | 理由 |
|---|---|---|
| **弃权层本身**（在信号之上决定出手 / 不出手，以降低已出手交易的错误率） | **高** | 至少 7 篇独立工作已发表或公开同一结构：Pidan & El-Yaniv 2011（NIPS）、Chalkidis & Savani 2021（ICAIF）、Nabar & Shroff 2023（ICAIF）、Sanderink 2026（股票截面排序器 + 门控，实验规范与我们 v2 高度重合）、Hao et al. 2026、Torres et al. 2026、Guo 2026（SSRN 预印本，因子 / 行业轮动的"弃权并回落到基准"，仅读摘要）；业界有通行名称 meta-labeling（Joubert 2022；Meyer et al. 2023）。"选择性降低已出手样本的错误率"这一现象本身是选择性分类的定义性结果。换到 A 股不改变这一判断。 |
| **博弈机制 + 弃权**（从知情交易者模型导出入场规则 + 可检验限制 + Z 的增量价值） | **中** | 直接撞车：未发现（见 G1、G3）。不给"低"的原因：(1) 理论部件为经典结果，"新"只在落地形式，容易被判为重新包装；(2) SSRN / 知网 / 研报 / Google Scholar 未检索，一篇高度相关的 SSRN 预印本（Guo 2026）只读到摘要、全文未读；(3) 该方向 2026 年发文密度很高（仅 2026 年 2–11 月就有 Sanderink、Torres、Hao、Manoharan、Fang & Ślepaczuk、MohammadpourAzari、Zarei、Benhamou×2 等），半年内出现更近的工作的概率不低；(4) 若机制最终推不出通用预测器给不出的限制（H3′ 失败），这一层就塌回"弃权层本身"——那是高风险层。 |

补充一个单列的风险：**理论保证层面，中–高**。anytime-valid selective risk（CSA）与金融侧的延迟反馈弃权保证（MohammadpourAzari et al.）都已存在，见 G2。

---

## 6. 必须比较的更强基线

v2 已列的基线（未过滤多因子、匹配覆盖率的随机稀疏化、置信度阈值、波动率 / 流动性 / 市场状态过滤、meta-labeling 含与不含 Z、期望净收益过滤、现金缩放与波动率目标、滚动 selective-risk 校准）都保留。本次调研后**新增或需要加强**的：

1. **滚动已实现效力门控**（Sanderink 2026 的策略层 G(t) 的核心：已到期 RankIC 的 EWMA 低于阈值则当日全部不出手）。它在该文里显著优于 VIX / 波动率门控，是比"波动率过滤"强得多的非博弈对照。
2. **个股层误差预测 + 尾部截尾**（DEUP 式二级模型预测一级模型的排序误差，截最不确定的尾部）。并检查它报告的"不确定性与信号强度结构性相关"在 A 股是否同样出现——若出现，任何"按 Z 弃权"都要先对 |score| 做残差化。
3. **SGR 阈值**（Geifman & El-Yaniv 2017；即 Chalkidis & Savani 2021 的做法），作为"i.i.d. 保证直接套用"的对照，用来展示时间依赖下名义保证是否失效。
4. **ISA**（Zhang et al. 2023）作为金融动机的学习式弃权基线；SelectiveNet 与 Deep Gamblers 保留为次要对照。
5. **证据门控**（MohammadpourAzari et al. 2026 的 evidence gate：到期奖励的单侧下界统计量不过关则不出手）。
6. **Anytime-valid selective risk 校准**（CSA 式 e-process 阈值；A-RCPS。两者都是通用 ML 方法，CSA 的原始场景是 LLM 部署，不是金融）——如果我们的校准程序是它们的适配，就必须和"不适配的原版"比，说明适配带来了什么。
7. **ACI / 在线 CRC**（Gibbs & Candès 2021；Angelopoulos et al. 2022）作为"只保证长期平均"的对照。
8. **同容量通用模型 + Z**：一个不带任何机制约束的 GBDT 亏损预测器，输入 B ∪ Z（v2 的 H3′ 已要求；这里强调它是**决定论文能否主张"博弈"的唯一对照**）。
9. **Z 的学术对应物**：Grinblatt–Han 的 CGO、Liu–Stambaugh–Yuan 的异常换手率，与软件版筹码分布并列，避免"自造变量"的质疑。
10. **收益侧的反向检验**：报告弃权掉的交易的平均收益（而不只是亏损概率），直接回应 Choi, Jin & Yan (2013) 式的"高信息不对称 = 高期望收益"。

---

## 7. 可能的调整方向

- **方向 A（机制为主，风险高、上限高）**：写出最小知情交易者模型，目标不是"证明该弃权"（那是已知的），而是推出**符号 / 单调性 / 交互项**层面的限制，例如"入场所需 alpha 阈值随逆向选择暴露单调上升，且在低流动性股票上斜率更大"，并且这些限制是通用 GBDT 在同样输入下不会强制满足的。然后检验：施加限制的模型在样本外是否不劣于无约束模型（形状约束 = 正则化的论证）。**前提是先做 v2 里说的小规模按时间试点**。
- **方向 B（实证为主，稳）**：论文定位为"A 股上逆向选择代理变量对选择性交易的增量价值：一个预注册式的检验"，贡献是 G3 + G4 + 严格的匹配覆盖率评估协议。扑克只作动机。理论部分只做 G2 的适配。投稿目标偏 ICAIF / Quantitative Finance。
- **方向 C（方法为主）**：把 G2 的适配做扎实——"延迟、重叠、日内截面相关的交易流上的 anytime-valid selected-trade risk 控制"，博弈与筹码都降为实验中的一个特征组。需要 `researcher` 读完 CSA / A-RCPS / MohammadpourAzari 后判断还剩多少可证的新东西。
- **不建议**：以"首次把弃权 / 扑克思维用于股票交易"立论；以 RL 调权重为卖点（检索到的 RL 交易文献很多，且 v2 已判断 RL 在此不必要）。

---

## 8. "前人没有做过 X"说法清单（供逐条事实核查）

说明：下面每条都是**在所列检索范围内未发现反例**，不是"已证明不存在"。所有条目共同的未检索范围：知网 / 万方、券商研报、SSRN 全文、Google Scholar / Semantic Scholar 引用链。置信度是 scout 的主观判断。

| 编号 | 说法 | 依据 | 检索范围 | 置信度 | 已知的最近反例 / 需重点核查 |
|---|---|---|---|---|---|
| N1 | 未发现从知情交易者 / 逆向选择模型**推导**出股票方向性入场弃权规则、并检验其可证伪限制的论文。 | G1；§2 五篇均为统计弃权 | arXiv 字段检索 5 条（adverse selection / informed trading × abstain / no-trade / learning；Glosten × RL）；OpenAlex 2 条；WebSearch 1 条；candidates.csv 方向 1、3 | 中 | 经典理论（Milgrom–Stokey、Glosten–Milgrom、Dow–Werlang、Easley–O'Hara 2009）已给出不交易 / 不参与结果；Cartea et al. 2023 是经纪商侧的学习式毒性过滤。需核查金融学期刊里是否有散户不参与的结构估计。 |
| N2 | 未发现把扑克 / 不完全信息博弈的"弃牌"形式化为交易入场规则的学术论文。 | G1 | arXiv `abs:poker AND (stock / trading / financial market)`；WebSearch 1 条；candidates.csv 方向 1（C001–C012） | 中 | Chakraborty & Yilmaz 2008（知情方诈唬，仅摘要）；Deep Gamblers（赛马下注 → 弃权，非博弈）；C012 Cherednik 2019（摘要命中 poker，**全文未读**，需核查）。 |
| N3 | 在已检索到的"弃权用于交易"的论文中，**没有针对这类变量（筹码成本分布 / 资本利得悬挂 / 换手异常）的专门增量检验**。（第 1 轮检查后收窄：原说法"没有一篇用作弃权依据"过强，见 §10。） | §2、§3 对比表 | 本报告引用的 A 组全部文献（读摘要或全文） | 中–高（限于这些论文） | Chalkidis & Savani 2021 有 volume-at-price 特征（形式上的日内筹码分布）；它进入分类器，而分类器的置信度决定弃权，所以已**间接**影响弃权，只是没有单独的增量检验。Guo 2026（SSRN）摘要已读、未见此类变量，全文未读。 |
| N4 | 未发现检验筹码 / 成本基础 / 换手异常变量对弃权层**增量**价值（控制置信度、波动率、流动性；A 股；样本外；匹配覆盖率）的论文。 | G3 | arXiv 2 条；OpenAlex 3 条；WebSearch 2 条（1 条中文） | 低–中（英文内中等；中文未检索） | Zhang 2020（IEEE CDS，筹码分布选股，仅题录，**需读全文**）；国内研报与硕博论文很可能有筹码因子回测。 |
| N5 | 未发现在交易流上、不依赖可交换性地控制"已出手交易亏损比例"（selected-trade risk）的保证。 | G2 | arXiv 4 条（selective risk / risk control × non-exchangeable / martingale / e-process；q-fin × conformal；q-fin × selective + coverage）；WebSearch 2 条 | 中 | **通用工具已存在**：Khosravi & Huo 2026（anytime-valid selective risk；LLM 部署场景，非金融）、Xu et al. 2024（A-RCPS）。金融侧：MohammadpourAzari et al. 2026（财富 / 遗憾，非亏损概率）、Benhamou et al. 2026（规则层面的 e-process）。此条只能在"交易流 + 亏损概率"这个窄范围内成立。 |
| N6 | 已发表的"选择性分类用于交易"工作（Chalkidis & Savani 2021）直接沿用 i.i.d. 假设下的 SGR 保证，未讨论时间依赖。 | 全文通读 | 该论文全文 | 高 | — |
| N7 | Sanderink (2026) 没有形式化保证，没有博弈 / 知情交易者机制，没有成本基础或换手异常变量，市场为美股。 | 第 1–4、8 节通读，5–7 节扫读 | 该论文 | 高（第 5–7 节若有补充理论则需修正，关键词扫读未见 theorem / guarantee） | — |
| N8 | MohammadpourAzari et al. (2026) 的保证对象是相对 Safe 组合的遗憾与财富下界，不是已选交易的亏损概率；其"弃权"是转到满仓的 Safe 组合。 | 第 1 节、假设与定理陈述 | 该论文（证明未读） | 高 | — |
| N9 | Zhang et al. (2023) 的保证要求 i.i.d. 样本，且没有交易回测。 | 假设 1、定理陈述、实验部分 | 该论文 | 高 | 正式发表版本若有新增实验，需核查（发表情况未验证）。 |
| N10 | 未发现 A 股个股日频、显式处理 T+1 与涨跌停不可成交的选择性交易 / 弃权研究。 | G4 | arXiv 2 条（返回基本无效）；OpenAlex 2 条；WebSearch 1 条 | 低–中 | Fang & Ślepaczuk 2026（沪深 300 指数 + 门控 / 阈值）；Zhang et al. 2022（RL + T+1，非弃权）。中文文献未检索。 |
| N11 | 未发现同时具备以下四项的论文：(a) 因子信号之上的弃权层，(b) 机制导出的弃权依据，(c) 时间依赖下的已选交易风险保证，(d) A 股样本外证据。 | N1、N4、N5、N10 的合取 | 同上 | 中（合取命题更容易成立，但也最不能说明价值——四项各自都有先例或经典来源） | Sanderink 2026 具备 (a)；MohammadpourAzari et al. 2026 具备 (a) 与对抗性版本的 (c)。 |
| N12 | Chalkidis & Savani (2021) 自称"选择性分类用于交易策略设计此前未被探索"；但 Pidan & El-Yaniv (2011) 已在 NIPS 发表可弃权的金融趋势预测。 | 前者全文、后者摘要 | 两篇论文 | 高 | 这条是"前人的'首次'说法不准确"的记录：我们自己不要重复类似措辞。 |

---

## 9. 需要用户协助的事项

1. 通过图书馆获取并放入 `literature/pdfs/`（2026-11-15 更新，详见 §11）：
   - Joubert (2022) doi:10.3905/jfds.2022.1.098 —— **用户未能获取**；仍为"仅读摘要"。
   - Meyer, Barziy & Joubert (2023) doi:10.3905/jfds.2023.1.119 —— **未收到**（`literature/pdfs/` 里没有这份 PDF）；仍为"仅读摘要"。
   - Chakraborty & Yilmaz (2008) doi:10.1257/aer.98.2.280 —— **已收到并通读正文**（在线附录里的引理证明未读）。此项关闭。
2. 人工打开 SSRN：Guo (2026) doi:10.2139/ssrn.7021298。**仍未解决。** 用户放入的 `ssrn-7599578.pdf` 是另一篇论文（Li Guo 等四人的 A 股高频交易论文，doi:10.2139/ssrn.7599578），不是这一篇，见 §11。需要重新下载：SSRN abstract id **7021298**，标题 *When Not to Trade: Leakage-Aware Selective Machine Learning for Factor Rotation*，作者 Yifan Guo。全文仍未读，其形式化部分与我们的重合程度仍无法判断。
3. 用 `literature/deep_research_prompt.md` 在 Gemini / ChatGPT Deep Research 以及知网上做补充检索，重点是筹码分布因子的中文实证和券商研报。

---

## 10. 修订记录（第 1 轮检查后）

> 2026-11-15，literature-scout。依据：`reviews/novelty_check_1.md`（GPT、Gemini、ARS fact-check 三路汇总）与 `reviews/novelty_factcheck_1.md`。只做了检查意见要求的最小改动；§0–§9 的其余内容（包括针对 v2 设想的表述）保持原样，方向调整见 `00_idea/research_question.md` 的"v3 调整方向"。

**四处改动**

1. **N3 收窄。** 原说法"没有一篇用筹码成本分布 / 资本利得悬挂 / 换手异常作为弃权依据"过强：Chalkidis & Savani (2021) 的 volume-at-price 特征进入分类器，而分类器的置信度决定弃权，所以这类变量已经间接影响了弃权（GPT 指出，组长接受，见 novelty_check_1.md §2）。现改为"**没有针对这类变量的专门增量检验**"。改动位置：§8 的 N3 行；§2.2 "他人状态变量"一条的措辞同步修改。
2. **Guo (2026) 补入弃权层先例。** doi:10.2139/ssrn.7021298，*When Not to Trade: Leakage-Aware Selective Machine Learning for Factor Rotation*。内容以 novelty_factcheck_1.md §A 为准（Crossref 存入的摘要，读到前约 1,200 字符）：研究"机器学习策略何时应当拒绝交易"；因子与行业轮动；滚动起点协议；验证改进超过校准阈值才部署 ML 信号，否则弃权并回落到基准组合；形式化为可预测的组合规则并给出收益 / 均值–方差效用分解；读到的部分里没有博弈或知情交易者机制，也没有筹码 / 换手变量。**全文未读。** 改动位置：§1（SSRN 一条）、§2.6（表格行由"仅题录"改为"仅读摘要"）、§5（弃权层先例由 6 篇改为 7 篇；"中"评级理由 (2) 的措辞）。评级不变：弃权层"高"、博弈机制 + 弃权"中"。
3. **CSA 的场景注明。** Khosravi & Huo (2026), arXiv:2605.20270，完整标题为 *Conformal Selective Acting: Anytime-Valid Risk Control for RLVR-Trained LLMs*，场景是 LLM 部署，不是金融。改动位置：§0 第 3 条、§4 G2、§6 第 6 项、§8 的 N5 行（§2.6 原本已注明"非金融"）。
4. **§9 第 2 项**更新为"摘要已部分读到，全文仍未读"。

**本轮核实线索时新增的信息**（细节与出处见 `literature/lead_verification.md`；以下内容未经跨模型审查）

- **Guo (2026) 的摘要后半段**：本轮直接查询 Crossref 时读到了完整的存入摘要。fact-check 没读到的部分是：作者"给出一个验证误差部署界（validation-error deployment bound），并展示零假设校准的门控如何在安慰剂信号下控制错误部署"，并报告行业轮动实验中净 Sharpe 0.55 → 0.78、最大回撤 −39.0% → −21.4%、换手减半以上。也就是说它带有形式化保证成分，与我们 H-T 在"选择性部署 + 形式保证"层面可能有重合，**程度要读全文才能判断**。这不改变两级评级，但提高了"请用户打开全文"的优先级。
- **Guo (2026) 的作者名**：Crossref（带已认证 ORCID）为 Yifan Guo；OpenAlex 与我们的 bib 为 "Yi Guo"。待组长决定是否改 bib。
- **Choi, Jin & Yan (2013) 已读 NBER 版正文**：§4 G1 引用的"年化 10.8%"与方向核实无误，但那是控制规模、价值、动量后的四因子 alpha 差（0.90%/月，t = 3.51）；**原始收益差只有 0.32%/月且不显著**；效应只在中大盘股中存在。该文已正式发表于 *The Journal of Finance and Data Science* 11 (2025), 100174。
- **Easley, Hvidkjaer & O'Hara (2002)**：由"仅题录"升为"仅读摘要"——NYSE 1983–1998，PIN 相差 10 个百分点对应年期望收益相差 2.5%，方向同为正。全文未读（付费墙；SSRN 403）。
- **Cartea, Duran-Martin & Sánchez-Betancourt, *Detecting Toxic Flow*** 已正式发表：*Quantitative Finance* 26(4), 541–561, 2026, doi:10.1080/14697688.2026.2619539。本报告中的 "Cartea et al. (2023)" 指其预印本。
- **外部模型给出的错误标识符**（均不得采用）：Dow & Werlang 1992 的 DOI，GPT 的 10.2307/2951525（实为 Galor 1992）与 Gemini 的 10.2307/2951599（实为 Aghion & Howitt 1992）都错，正确的是 10.2307/2951685（我们的 bib 原本正确）；Gemini 的 "Angelopoulos et al. 2024, Learn to Defer with Conformal Risk Control, arXiv:2404.14376" 查无此文，该编号是一篇计算机图形学史论文；Gemini 给 Chalkidis & Savani 的 DOI 10.1145/3460340.3482500 不存在。
- **N12 的遗留**：Pidan & El-Yaniv (2011) 的存在与题录已在 NeurIPS 官方页面核实；正文仍只读过摘要。

**仍未解决**

- 中文文献（知网、券商研报）未检索；N4、N10 仍无法判断。
- Guo (2026) 全文、EHO (2002) 全文、Joubert (2022) 等三篇付费论文全文未读。
- arXiv:2603.13252 的"2026 年 2 月"与编号前缀 2603 的出入（§0 第 1 条）：组长给出的解释未经进一步验证，本轮未处理。

---

## 11. 用户提供全文后的更新

> 2026-11-15，literature-scout。对象：用户放入 `literature/pdfs/` 的两份 PDF。精读笔记见 `literature/fulltext_notes_user_pdfs.md`。本节未经跨模型审查。§0–§10 的原文不动；与本节冲突处以本节为准。

### 11.1 `ssrn-7599578.pdf` 不是 Guo (2026) "When Not to Trade"

- 该 PDF 是 **Li Guo, Frank Weikai Li, Ding Qi & Lijian Sun, "Tracking High-Frequency Trading Activity in China and Its Effects on Market Quality"**，首页标注 "This draft: October 2026"，doi:10.2139/ssrn.7599578。依据：PDF 第 1 页；Crossref 对 10.2139/ssrn.7599578 的记录（标题、四位作者一致，记录创建于 2026-10-12）。
- 我们要的论文是 **Yifan Guo**（单作者）, doi:10.2139/ssrn.7021298（Crossref 记录创建于 2026-07-21）。两篇只是第一作者同姓，内容无关。
- 收到的这篇论文：深交所 Level-2 数据，用"报价恰好等于对手方最优价的限价单"作 HFT 代理变量；验证其反应更快、撤单更快、能预测 100 ms 到 10 分钟的中间价收益；用开盘时通道间行情延迟差做 DID，得到延迟降低 → 该类订单占比上升 → 秒内价格波动、宽价差发生率、逆向选择暴露上升。**它不是弃权 / 选择性交易论文，没有定理，没有归因分解，没有筹码 / 资本利得悬挂变量，没有博弈模型**（阅读深度：正文通读，附录文字通读，附表部分核对）。
- 对本报告的影响：**无撞车**，不进入 §2 的最接近工作，也不改变任何"未发现"类说法。可在相关工作中作背景引用一句（A 股日内信息劣势的直接证据；T+1 使速度优势偏向方向性吃单），但其时间尺度是毫秒到分钟，不能用来支持"日频变量 Z 度量信息劣势"。已登记为 bib 条目 `guo2026hft`，是否引用由组长定。

### 11.2 Guo (2026) "When Not to Trade"：状态没有变化

- **阅读深度仍为"仅读摘要"。** 本轮再次查询 Crossref，确认标题、作者（Yifan Guo，带认证 ORCID）与摘要要点，没有读到任何新内容。
- 因此，组长要求的逐条比较**无法基于全文完成**。基于摘要的暂定判断（详见 `fulltext_notes_user_pdfs.md` §2）：

| 我们的结果 | 暂定判断（未验证） | 一句话理由 |
|---|---|---|
| Theorem 1（延迟标签下 r_T^entry 的时间一致监控区间） | 未见重合迹象 | 摘要里的保证对象是"是否部署信号"的决策，不是已出手交易的亏损概率；没有 anytime / 延迟标签字样。假设与形式未读。 |
| Proposition 2（√(dM/N) 下界） | 未见重合迹象 | 摘要未提任何下界。 |
| Lemma 3（暴露时间表 / 构成 / 成本的 P&L 归因恒等式） | **可能部分重合，最需核对** | 摘要明确有"return and mean-variance utility decomposition"，对象是"门控策略相对回落基准"的可预测组合规则，与我们的分解结构同类；它拆成哪几项、有无成本项与暴露项，未读。 |
| v3 主问题（弃权收益来自降暴露还是来自选择） | 未知 | 它的弃权是回落到基准组合（据摘要并非现金），"降暴露"在其设定里未必是一个成分；摘要报告换手减半以上，成本渠道可能被讨论。未读。 |

- **撞车评级：不上调，也不下调。** 理由是没有新证据，而不是风险已排除。三层评级维持 §5 与 §10：弃权层本身"高"；博弈机制 + 弃权"中"；理论保证层面"中–高"。
- **必须如实保留的风险提示**：v3 把主贡献改成了"评价 / 归因协议"。如果 Guo (2026) 的收益与效用分解确实把"选择性部署的增量"与基准、成本分开，那么**受影响的是 v3 的主问题这一层（归因协议的新颖性），而不是 Theorem 1 / Proposition 2**。这一层目前没有单独的评级；在读到全文之前，建议按"中，未关闭"对待，并且论文里不要写"首次对选择性交易的表观改善做归因"之类的话。读到全文后若确认是同一分解，这一层应上调为"高"，Lemma 3 须改写为"沿用 / 扩展 Guo (2026) 的分解"。

### 11.3 Chakraborty & Yılmaz (2008)：由"仅读摘要"升为"正文通读"

- **阅读深度**：正文 5 页全文通读；引理 1、2 的证明在 AER 网站的在线附录，**未读**。
- 模型：两期、v ∈ {−1, 1}、市价单。三类交易者——(1) leader：以概率 α 是知道 v 的内幕者，否则是噪声交易者；(2) followers：质量 Δ > 1 的连续统理性交易者，知道 leader 是否知情但**不知道 v**；(3) 只知道先验的竞争性做市商。
- 诈唬者是**内幕者**，被诈唬的是 followers 和做市商。**Proposition 1**："For any α ∈ (0, 1), the insider must bluff in every equilibrium."——若内幕者不诈唬，followers 会在第 2 期跟随第 1 期订单流并把利润竞争掉，于是内幕者有利可图地偏离：第 1 期逆着自己的信息交易，第 2 期逆着 followers 的订单流平仓。
- **需要更正 §2.6 表格里的一句话**：原写"存在一群……理性交易者，均衡中'跟随'内幕者"。全文显示，followers 的跟随是**候选的非诈唬均衡**里的行为，正是它导致非诈唬均衡不存在；均衡中 followers 实际怎么做，论文没有刻画。另外 followers 的信息不是"比内幕者粗的基本面信息"，他们对基本面一无所知，只知道订单流里有没有知情者。
- 与"信息劣势方该不该出手 / 该不该跟随订单流"的关系：**间接**。它证明"跟随订单流可被知情者利用"，支持"跟进疑似知情资金并不安全"的直觉；但它**没有**推导劣势方的最优不参与或入场阈值，没有比较"跟"与"不跟"的均衡收益，没有数据。不能引用它来说"劣势方弃权是最优反应"。
- **对 N2 的影响**：不构成反例——它形式化的是诈唬，不是弃牌，没有入场规则。"Chakraborty & Yilmaz 2008 不是 N2 的反例"这一判断由"仅据摘要"升为"已读正文确认"。**N2 的总体置信度维持"中"**，不上调：其余缺口（金融学期刊全文库、SSRN、中文文献未检索；C012 Cherednik 2019 全文未读）没有变化。它同时说明扑克式诈唬在微观结构理论里早有正式模型，论文里用扑克作动机时应当引用，不要显得是我们首创。
- 其参考文献里与我们相关、**尚未核实**的线索：Chakraborty & Yılmaz (2004a) "Informed Manipulation", *JET* 114(1)；(2004b) "Manipulation in Market Order Models", *J. Financial Markets* 7(2)；Kyle & Viswanathan (2008) "How to Define Illegal Price Manipulation", *AER* 98(2)；Foster & Viswanathan (1994), *JFQA* 29(4)。核实前不得引用。

### 11.4 待办清单现状（§9 已同步修改）

| 文献 | 状态 |
|---|---|
| Chakraborty & Yilmaz (2008) | 已收到，正文通读；在线附录证明未读。关闭。 |
| Guo (2026) *When Not to Trade*, doi:10.2139/ssrn.7021298 | **未收到**（收到的是另一篇）。全文未读。**优先级最高**：关卡 2 之前应读到，否则 Lemma 3 与 v3 主问题的新颖性无法定论。 |
| Joubert (2022), doi:10.3905/jfds.2022.1.098 | 用户未能获取。仅读摘要。 |
| Meyer, Barziy & Joubert (2023), doi:10.3905/jfds.2023.1.119 | 未收到（PDF 不在 `literature/pdfs/`）。仅读摘要。 |
| Easley, Hvidkjaer & O'Hara (2002) 全文 | 未读（§10 已记）。 |
| 中文文献（知网、券商研报） | 未检索（§10 已记）。 |

两份 PDF 中没有发现写给自动化程序的指令。

# 新颖性三路检查汇总（第 1 轮，2026-11-15）

被审对象：`literature/novelty_report.md`（literature-scout 撰写）。
三路：GPT（`reviews/raw/novelty_novelty_report_gpt_20261115-012805.md`）、Gemini 3.8 Flash High（`reviews/raw/novelty_novelty_report_gemini_20261115-012807.md`）、组长的 ARS fact-check（`reviews/novelty_factcheck_1.md`）。三路各自独立，互相没看过对方意见。

**评级：GPT — HIGH；Gemini — HIGH；scout 自评 — 弃权层"高"、博弈机制 + 弃权"中"；fact-check — 维持 scout 的两级评级，但所有"未发现"都受检索范围限制。**

## 1. 共识问题（多方都指出 → 高优先级）

1. **"在信号上加一个出手 / 弃权的二级模型"已是既有工作，不能作为贡献。**（GPT、Gemini、scout、fact-check 一致。）先例：Chalkidis & Savani 2021；meta-labeling（López de Prado 2018；Joubert 2022）；选择性分类（Geifman & El-Yaniv 2017/2019）；Deep Gamblers 2019 已把下注理论与弃权联系起来。fact-check 另补一篇：Guo 2026（SSRN 7021298，因子 / 行业轮动的"弃权并回落到基准"）。
2. **"信息劣势方不交易"的理论是经典结果。**（GPT、Gemini、scout。）Milgrom–Stokey 1982、Glosten–Milgrom 1985、Dow–Werlang 1992、Easley–O'Hara 2009。我们能新增的只能是落到可观测日频入场规则上的、**有区分力**的限制。
3. **序贯 / 不依赖可交换性的风险控制工具已经成熟。**（GPT、Gemini、scout、fact-check。）ACI（Gibbs & Candès 2021）、时间一致置信序列（Howard et al. 2021）、anytime-valid 推断（Ramdas et al. 2023）、A-RCPS（Xu et al. 2024，arXiv:2406.10490 已核实）、CSA（arXiv:2605.20270 已核实，场景是 LLM 部署）。适配到交易流是增量。
4. **换到 A 股、加 T+1 和涨跌停，不构成独立贡献**，是回测可信度的必要条件。（Gemini、scout；GPT："只换市场不够"。）
5. **剩余的可能新意只有三处**，且都未被证实：有区分力的机制限制；在明确陈述的依赖与延迟假设下真正新的已选交易保证；筹码 / 换手变量在 A 股上的增量证据。（GPT 明确列出；Gemini 把后两项评为"中"；scout 的 G1–G3。）

## 2. 分歧点（只有一方指出 → 组长判断）

| 问题 | 提出方 | 组长判断与理由 |
|---|---|---|
| **Z 的经济含义是范畴错误**：筹码分布 / CGO / 异常换手来自行为金融（处置效应、情绪），刻画的是散户自己，不是"对手的私有信息"；把它当作逆向选择代理"在经济学上不成立"。 | Gemini（措辞最重）；GPT 在阶段 0 讨论里提过识别问题；scout 在 G1 里承认 | **接受，高优先级。** 这直接打在 idea.md 的核心设想上。Liu–Stambaugh–Yuan 2019 把异常换手作为情绪因子的构造变量，Grinblatt–Han 把 CGO 归为处置效应，都支持 Gemini。后果：要么换 Z（需要订单流类数据，日频免费数据做不到 PIN / VPIN），要么放弃"推断对手信息"的叙事，把 Z 老实称为行为 / 拥挤状态变量。交给用户在关卡 1 决定。 |
| **信息不对称可能带正的风险溢价**：高逆向选择时弃权可能恰好丢掉最高 alpha。 | Gemini（引 Easley–Hvidkjaer–O'Hara 2002）；scout（引 Choi–Jin–Yan 2013） | **接受为必须检验的风险，但证据强度有限。** 两篇的方向性结论我们都只核实了题录 / 摘要（fact-check C.3）。必须在实验里报告"被弃掉的交易的平均收益"。 |
| **弃权不会自动降低错误率；预测错误 ≠ 交易亏损；监控 ≠ 控制；机制限制要有区分力而不只是约束。** | GPT（四条"重要更正"） | **全部接受。** 这四条是对 research_question v2 的进一步收紧：标签必须是净亏损；定理必须说清是事后监控还是事前控制；"施加形状约束后更好"只能说明正则化有用，不能证明逆向选择机制成立。 |
| **N3 说得太强**：volume-at-price 若进入分类器、而置信度决定弃权，就已间接影响弃权。 | GPT | **接受。** novelty_report 的 N3 应改为"没有针对这类变量的专门增量检验"。小改，关卡通过后由 scout 修订。 |
| **建议彻底放弃博弈叙事，转为应用实证论文（方向 B）**，目标 JFDS / Quantitative Finance / ICAIF。 | Gemini | **部分接受。** 作为默认路线合理；但 GPT 与 scout 都认为"有区分力的机制限制"若能推出来仍有价值。组长建议：方向 B 为主线，方向 A 作为一个有明确止损条件的试探（见 `literature/positioning.md`）。由用户决定。 |
| **2026 年的几篇近作未被外部模型核实**（Sanderink、MohammadpourAzari、CSA、Zarei、Guo 等），GPT 还指出"2026 年 2 月"与 arXiv 编号 2603 不一致。 | GPT、Gemini（都标 UNVERIFIED） | **部分已解决。** 组长用 arXiv API 逐一按编号查到了 2603.13252、2611.04826、2611.14699、2605.20270、2611.03384，标题与作者吻合；Guo 2026 经 Crossref 核实并读到部分摘要。日期问题：arXiv API 返回 2603.13252 的 published 日期为 2026-02-24，而编号前缀是 2603——API 的 published 是首次提交日期，编号按公告月份分配，二者可以不同；**此解释未经进一步验证**，引用时以 arXiv 页面为准。外部模型本身无法联网核实，这一点如实记录。 |

## 3. 外部模型给出的文献线索（一律待核实，不得直接引用）

- Gemini 给的若干标识符与我们已核实的不一致或可疑，**不要采用**，交 `literature-scout` 核实：
  - Chalkidis & Savani 的 DOI 写成 10.1145/3460340.3482500、作者首字母写成 "I."（我们经 OpenAlex / arXiv 核实的是 Nestoras Chalkidis，doi:10.1145/3490354.3494379）。
  - Dow & Werlang 1992 的 DOI：GPT 给 10.2307/2951525，Gemini 给 10.2307/2951599，互相矛盾，均未核实。
  - "Angelopoulos et al. 2024, Learn to Defer with Conformal Risk Control, arXiv:2404.14376" 与 A-RCPS 的 OpenReview 链接：未核实，可疑。
- 值得核实后纳入的线索：López de Prado 2018（meta-labeling 原始出处）；Ramdas et al. 2023；Howard et al. 2021；Easley–López de Prado–O'Hara 2012（VPIN）；Easley–Hvidkjaer–O'Hara 2002；Wang–Yan–Yu 2017；Liu–Stambaugh–Yuan 2019；Cartea et al.《Detecting Toxic Flow》的正式发表信息。

## 4. 总体结论

- **撞车风险：高**（两个外部模型一致；scout 与 fact-check 认为"博弈机制 + 弃权"这一窄层为"中"，但该层同时面临"Z 的经济含义站不住"和"可能丢掉风险溢价"两个实质问题）。
- 原始设想（"扑克思维 + 博弈因子 + RL 调权重"）按原样做，不具备可发表的新颖性。
- 仍可做的方向及各自风险见 `literature/positioning.md`。
- 未解决事项：中文文献（知网、券商研报）完全未检索；N4、N10 无法判断；Choi–Jin–Yan 2013 与 Easley–Hvidkjaer–O'Hara 2002 的方向性结论未读原文；Guo 2026 全文未读；Joubert 2022 等三篇付费论文只读了摘要。
- 审查独立性：GPT 参与过阶段 0 的研究问题讨论，本次审稿为单独调用、未附讨论记录，按"半独立"计；Gemini 未参与任何讨论。Gemini 为 Flash 模型。

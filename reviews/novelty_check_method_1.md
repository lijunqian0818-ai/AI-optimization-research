# 新颖性检查汇总（方法学主线）第 1 轮

日期：2026-11-18。被审文件：`literature/method_pivot/novelty_report_method.md`、`00_idea/research_question_v5_draft.md`。

| 审查方 | 状态 | 结论 | 原文 |
|---|---|---|---|
| literature-scout | 完成；72 条候选，除一篇外仅读摘要 | 风险 高 | `literature/method_pivot/novelty_report_method.md` |
| GPT（gpt-6-astra，low） | 完成。半独立（同日参与过 `research-question` 讨论；本次为不带讨论记录的单独调用） | 风险 高 | `reviews/raw/novelty_novelty_report_method_gpt_20261118-170535.md` |
| Gemini 3.8 Flash (High) | 完成，独立 | 风险 高 | `reviews/raw/novelty_novelty_report_method_gemini_20261118-170538.md` |
| ARS fact-check | **未做**（三方结论一致为"高"，待用户定方向后只对保留下来的"无人做过"说法做） | — | — |

## 一、共识
1. **一般性的方法学贡献已被占据。** 有限样本下 HAC / 块自助法覆盖不足及其修正（fixed-b、学生化块自助、自归一化、双重自助）、多策略同时推断、比值型业绩指标的学生化自助、重拟合下的样本外推断，都有成熟文献。
2. **Phase D 的主要现象是已知结论的复现**：小带宽 HAC 偏松、bootstrap-t 优于正态近似、强自相关下失效。不能当作贡献。
3. **"事先登记的模拟关卡"是研究规范，不是方法贡献**（Gemini 最明确；GPT："本身不是实质性的新统计方法"）。
4. **剩下最站得住的是应用基准研究**：在含重拟合、重叠持有期、随机分母比值的机器学习选股流程上，系统比较现有各类区间规则的实测覆盖率。三方都没有找到做过这整套基准的文章；贡献主要是实证和流程层面。Gemini 认为这撑不起顶级机器学习或统计期刊的方法论文，可投金融计量 / 金融数据科学类期刊。
5. **独立同分布数据下的不覆盖必须先查清**（GPT 两次提出；审计进行中）。

## 二、分歧
- **窄的理论结果是否还有空间。** scout 和 GPT：比值型多对比 max-t 在 fixed-b 下的覆盖误差展开"可能仍新"，但未确认。Gemini：已被 Chen 等 (arXiv:2609.05883) 加上标准的影响函数线性化所覆盖，只是增量。GPT 无法确认该预印本存在，认为读到原文前不应以它为决定性依据。组长判断：该预印本 scout 读过部分正文，存在性可信；它是否覆盖我们的情形需精读，**未验证**。
- **GPT 在讨论中建议的角度**（重抽样已实现的策略结果何时漏掉"学习过程"的不确定性）：scout 和 Gemini 指出 West、Giacomini–White、Corradi–Swanson、Bates 等已处理估计与重拟合效应；GPT 自己也标为未核实并给了放弃条件。
- **文献细节不一致。** Gemini 给出的若干条目（Kiefer–Vogelsang 2005 的题名、Sun 2014 与 Shao–Politis 2013 的 DOI、Gonçalves–Vogelsang 2011 的题名与 DOI、Müller 2014 的期刊）与 GPT 和 scout 的记录不一致。一律当作线索，以 scout 核实的 `references_method.bib` 为准。

## 三、总体结论
三方一致：**撞车风险 高**。把"区间覆盖不足及修正"作为有理论创新的方法学主线，按现有证据站不住。可行的定位是一篇应用基准 / 压力测试研究，必须与 Ledoit–Wolf、LLSW、Romano–Wolf、Gonçalves–Vogelsang（大带宽）、Shao–Politis、自归一化、Müller 等现有方法逐一比较。本汇总未经 ARS fact-check。

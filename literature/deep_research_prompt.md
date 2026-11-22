# Deep Research 补充检索提示词

## 怎么用（中文说明）

1. 把下面"提示词正文"整段（从 `=== PROMPT START ===` 到 `=== PROMPT END ===`）复制到 **Gemini Deep Research** 或 **ChatGPT Deep Research**。两个都跑更好，结果互相对照。
2. 提示词是英文的，但已要求对方同时检索中文来源（知网、万方、券商金工研报等）。如果对方中文检索做得不好，可以把"Part C"单独拿出来，用中文再问一次，或者直接在知网用这些关键词手工检索：`筹码分布 因子`、`筹码集中度 选股`、`获利盘比例 收益预测`、`资本利得悬挂 A股`、`异常换手率 知情交易`、`因子择时 A股`、`T+1 交易制度 量化策略`、`涨跌停 可成交性 回测`、`元标签 meta-labeling`、`选择性预测 股票`。
3. 把对方的完整报告存成 Markdown 文件放进 `literature/external/`（文件名随意，例如 `gemini_deep_research_2026-11-16.md`）。组长会派 literature-scout 逐条核实后再合并——**Deep Research 给出的文献可能不存在或信息有误，未核实前不能引用。**
4. 另外有两件事需要你亲自做（自动工具做不了）：
   - 在浏览器里打开 SSRN：<https://doi.org/10.2139/ssrn.7021298>（Yi Guo, *When Not to Trade: Leakage-Aware Selective Machine Learning for Factor Rotation*, 2026），把摘要贴进 `literature/external/`。这篇标题与我们高度相关，但我们读不到摘要。
   - 通过学校图书馆下载三篇付费论文放进 `literature/pdfs/`：doi:10.3905/jfds.2022.1.098、doi:10.3905/jfds.2023.1.119、doi:10.1257/aer.98.2.280。
5. 提示词里没有包含任何个人信息或项目名称，可以放心粘贴。

---

## 提示词正文

```
=== PROMPT START ===

You are assisting with a prior-art search for an academic research project at the intersection of machine learning, statistics and quantitative finance. Your job is to FIND WORK WE HAVE MISSED, especially work that contradicts our belief that certain things have not been done. Counterexamples are more valuable to us than confirmations. Do not summarise the papers we already list below; use them only to understand what "close" means.

## 1. The research idea (short)

We study a daily-frequency, long-only equity strategy on Chinese A-shares (T+1 settlement, daily price limits, transaction costs). A conventional multi-factor model produces buy signals. On top of it we add an "act / abstain" decision layer: for each candidate trade, decide whether to execute or to skip it. The motivation is poker-style reasoning under imperfect information: a trader who suspects she is at an informational disadvantage should fold. Concretely:

- The abstention decision conditions on public variables intended to proxy adverse-selection exposure or "other holders' state", such as the estimated cost-basis distribution of current holders (called "chip distribution" / 筹码分布 in Chinese retail software; the academic analogue is capital gains overhang), abnormal turnover, and holder-cost concentration.
- We want the abstention rule to be DERIVED from a minimal informed-trader / adverse-selection model that yields a testable restriction (for example, a monotone relation between the required signal strength and the adverse-selection proxy) which a generic supervised loss predictor would not impose.
- We want a statistical guarantee on the LOSS PROBABILITY OF EXECUTED TRADES (selective risk) that remains valid under temporal dependence and distribution drift, via sequential (martingale / e-process) monitoring or bounds with an explicit drift term, accounting for delayed labels, overlapping holding periods and cross-sectional dependence within a day.
- The key empirical question is INCREMENTAL value: do the cost-basis / turnover variables improve the abstention layer beyond calibrated model confidence, volatility, liquidity and market-regime filters, out of sample, at matched coverage (same fraction of trades executed)?

## 2. Work we already know (do NOT just repeat these)

Abstention / selective prediction applied to trading:
- Chalkidis & Savani, "Trading via Selective Classification", ICAIF 2021, arXiv:2110.14914
- Pidan & El-Yaniv, "Selective Prediction of Financial Trends with Hidden Markov Models", NIPS 2011
- Nabar & Shroff, "Conservative Predictions on Noisy Financial Data", ICAIF 2023, arXiv:2310.11815
- Sanderink, "When Alpha Breaks: Two-Level Uncertainty for Safe Deployment of Cross-Sectional Stock Rankers", arXiv:2603.13252
- MohammadpourAzari, Zarei & Fazli, "Safe Portfolio Learning from Untrusted Predictions: Signed Trust, Abstention, and Cross-Universe Polarity Failure", arXiv:2611.04826
- Zarei, MohammadpourAzari & Habibi, "Conformal Risk Certificates for Portfolio Optimization Under Uncertainty: A Gated Reinforcement-Learning Approach", arXiv:2611.14699
- Zhang et al., "Learning to Abstain From Uninformative Data", arXiv:2309.14240
- Joubert, "Meta-Labeling: Theory and Framework", J. Financial Data Science 2022, doi:10.3905/jfds.2022.1.098; Meyer, Barziy & Joubert, "Meta-Labeling: Calibration and Position Sizing", 2023, doi:10.3905/jfds.2023.1.119
- Torres et al., "FinAbstain", arXiv:2607.24875; Hao et al., Algorithms 2026, doi:10.3390/a19080704; Manoharan et al., "UQ-LOB", arXiv:2609.31491; Fang & Ślepaczuk, arXiv:2606.09478
- Ziyin et al., "Deep Gamblers", arXiv:1907.00208; Geifman & El-Yaniv, arXiv:1705.08500 and arXiv:1901.09192

Risk-control theory:
- Angelopoulos et al., "Conformal Risk Control", arXiv:2208.02814; "Learn then Test", arXiv:2110.01052; Bates et al., RCPS, arXiv:2101.02703
- Gibbs & Candès, "Adaptive Conformal Inference Under Distribution Shift", arXiv:2106.00170
- Xu, Karampatziakis & Mineiro, "Active, anytime-valid risk controlling prediction sets", arXiv:2406.10490
- Khosravi & Huo, "Conformal Selective Acting: Anytime-Valid Risk Control…", arXiv:2605.20270
- Bai & Jin, arXiv:2603.24704; Xu, Guo & Wei, arXiv:2512.12844; Hultberg et al., arXiv:2602.04364
- Benhamou et al., "Can We Stop the Backtest Yet? Anytime-Valid Promotion Tests…", arXiv:2611.03384

Strategic / informed trading:
- Milgrom & Stokey 1982; Kyle 1985; Glosten & Milgrom 1985; Rock 1986; Dow & Werlang 1992; Easley & O'Hara 2009 (ambiguity and nonparticipation); Easley et al. 1996 (PIN), 2012 (VPIN)
- Chakraborty & Yilmaz, "Microstructure Bluffing with Nested Information", AER 2008, doi:10.1257/aer.98.2.280
- Choi, Jin & Yan, "Informed Trading and Expected Returns", NBER w18680
- Cartea, Duran-Martin & Sánchez-Betancourt, "Detecting Toxic Flow", arXiv:2312.05827
- Chriss, arXiv:2501.01241; Li & Deng, arXiv:2512.17952

Cost-basis variables and China:
- Grinblatt & Han 2005 (capital gains overhang); Wang, Yan & Yu 2017; Xu, arXiv:2505.20608; Pan, Fan & Zhang 2025, doi:10.18178/joebm.2025.13.3.877
- Zhang, "Stock Picking Strategy Based on Exploration of Chip Distribution Indicators", IEEE CDS 2020, doi:10.1109/cds49703.2020.00061
- Liu, Stambaugh & Yuan 2019; Leippold, Wang & Zhou 2022; Zhang et al., IEEE Access, doi:10.1109/access.2022.3197165 (RL with T+1 rules)

## 3. What we want you to find

Search arXiv, SSRN, Google Scholar, Semantic Scholar, OpenReview, NBER, RePEc, major finance journals (JF, JFE, RFS, JFQA, Management Science, Review of Finance, Journal of Financial Markets, Quantitative Finance, Journal of Financial Data Science, Journal of Portfolio Management), ML venues (NeurIPS, ICML, ICLR, AISTATS, COLT, KDD, AAAI, ICAIF), statistics journals, AND Chinese-language sources (CNKI 知网, Wanfang 万方, CQVIP 维普, Chinese journals such as 《金融研究》《经济研究》《管理科学学报》《系统工程理论与实践》《中国管理科学》《数量经济技术经济研究》, master's and doctoral theses, and sell-side quantitative research reports 券商金工研报 from firms such as 华泰, 中信, 国泰君安/国泰海通, 广发, 海通, 东方, 兴业, 招商, 天风, 开源, 方正).

Part A — Counterexamples to gap G1 (mechanism-derived abstention):
Any paper that derives an entry / no-entry / participation rule for a directional equity investor from a model with informed traders or adverse selection (Kyle, Glosten–Milgrom, rational-expectations, ambiguity, winner's-curse models) AND takes it to data or to a learning algorithm. Include: structural estimates of retail non-participation or optimal inaction under information disadvantage; "trade only when not adversely selected" rules; papers that use PIN / VPIN / order-imbalance / institutional-flow proxies as a FILTER on whether to act on an alpha signal; papers formalising a poker "fold" or imperfect-information-game equilibrium as a trading entry rule; papers that test whether signals work worse when informed trading is high.

Part B — Counterexamples to gap G2 (guarantees under dependence, for trading):
Any paper giving a guarantee on the error rate / loss rate / precision of the SELECTED (executed) trades or selected predictions in a financial time series without assuming i.i.d. or exchangeability: anytime-valid or e-process monitoring of a strategy's hit rate; online conformal or risk-control methods applied to trade selection; selective classification under mixing / martingale-difference / drift assumptions; sequential tests of "win rate of executed trades ≥ target"; treatment of delayed labels, overlapping holding periods, or clustering by date in such guarantees. Also list the strongest general (non-finance) results on anytime-valid SELECTIVE risk control that we have not listed.

Part C — Counterexamples to gap G3 (cost-basis / turnover variables), with emphasis on Chinese-language literature:
(i) Empirical studies of chip distribution (筹码分布, 筹码集中度, 获利盘比例, 平均持仓成本, 成本分布), capital gains overhang (资本利得悬挂 / 未实现盈亏), or abnormal turnover (异常换手率) as return predictors or risk indicators in A-shares — journal papers, theses, and broker reports. For each: sample period, universe, whether out-of-sample, sign of the effect.
(ii) Any study using such variables as a FILTER, TIMING or VETO condition on top of another signal (factor timing 因子择时, signal filtering, "avoid crowded / high-chip-concentration stocks"), especially with comparison to volatility or liquidity filters.
(iii) Any study interpreting cost-basis or turnover variables as proxies for information asymmetry or informed trading rather than as behavioural (disposition-effect) variables.
(iv) Evidence on whether these variables predict the PROBABILITY OF LOSS or downside risk of a trade, as opposed to mean return.

Part D — Counterexamples to gap G4 (A-share constraints):
Selective / abstention / confidence-thresholded / meta-labeling strategies evaluated on individual A-shares at daily frequency, especially those that model T+1, limit-up non-executability (涨停买不进), limit-down non-exit, suspensions, ST stocks, or survivorship. Also: Chinese-language work on meta-labeling (元标签) or "trade only when confident" ML strategies.

Part E — Recent preprints (January 2025 – present):
Anything on selective prediction, abstention, gating, "when not to trade", uncertainty-aware deployment, or safe use of predictions in equity or factor strategies that is not in our list. In particular, please locate and summarise: Yi Guo, "When Not to Trade: Leakage-Aware Selective Machine Learning for Factor Rotation", SSRN, doi:10.2139/ssrn.7021298 — we could not read its abstract and need to know its market, method, guarantees, and whether it overlaps with the idea in Section 1.

Part F — Stronger baselines:
Methods we should compare against that are stronger than: confidence thresholding, volatility / liquidity / regime filters, meta-labeling, SelectiveNet, Deep Gamblers, conformal risk control, adaptive conformal inference, and a trailing-realised-efficacy gate.

Part G — Evidence against the premise:
Papers showing that (a) abstention / meta-labeling / selective trading FAILS out of sample or adds nothing beyond random thinning at matched coverage; (b) high information asymmetry or informed trading predicts HIGHER subsequent returns (so abstaining forgoes a premium); (c) chip-distribution or capital-gains-overhang effects are absent, unstable, or sign-reversed in A-shares.

## 4. Output format (strict)

For every item return:
1. Full title (original language; add an English translation for Chinese titles)
2. Authors, year, venue (journal / conference / preprint server / brokerage name for reports)
3. A resolvable identifier: DOI, arXiv ID, SSRN ID, CNKI record link, or a direct URL. If you cannot provide one, say "NO IDENTIFIER FOUND" — do not invent one.
4. One sentence: what it does.
5. One sentence: which Part (A–G) it bears on and whether it is a counterexample (it DID the thing we believe is undone), a partial overlap, or supporting background.
6. Your confidence that the item exists exactly as described: high / medium / low, and whether you opened the source page or are relying on a secondary mention.

Group the items by Part. Put the most damaging counterexamples first within each Part. At the end, give (i) a five-line verdict on which of G1–G4 survive, and (ii) a list of search queries you ran and the databases you could NOT access, so we know what remains unchecked.

Rules: Do not fabricate references. If unsure whether a paper exists, mark it low confidence and say why. Prefer primary sources over blog posts; include practitioner reports only in Parts C, D and G and label them as such. Quote no more than one short sentence from any source.

=== PROMPT END ===
```

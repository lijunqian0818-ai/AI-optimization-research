# Three-way scan (WHY / HOW / WHAT) of the closest prior work

> Produced by the lead with ARS `deep-research` · `three-way-scan`, 2026-11-15. **Read scope: arXiv abstracts only** (retrieved via the arXiv API the same day). Full-text reading of these papers is being done separately by `literature-scout` for `novelty_report.md`; where the two disagree, the full-text reading governs. AI-assisted.

## 1. Trading via Selective Classification
Source: arXiv:2110.14914 (ICAIF 2021, doi:10.1145/3490354.3494379) | Year: 2021 | Chalkidis & Savani | https://arxiv.org/abs/2110.14914

- WHY: A directional classifier forces the strategy to always hold a position; some inputs should not be traded.
- HOW: Binary and ternary selective classification (ternary adds a "small move" class); the strategy takes no position when the classifier abstains. Walk-forward train–validate–test with logistic regression, random forests, feed-forward and recurrent nets over several feature sets.
- WHAT: Backtests on commodity futures; authors report results "demonstrate the potential" of selective classification for trading. No guarantee, game model, equities or A-share setting is mentioned in the abstract.
  - **Method weaknesses**: not assessed (read scope: abstract_only)

## 2. When Alpha Breaks: Two-Level Uncertainty for Safe Deployment of Cross-Sectional Stock Rankers
Source: arXiv:2603.13252 | Year: 2026 | Sanderink | https://arxiv.org/abs/2603.13252

- WHY: Cross-sectional stock rankers fail in regime shifts; deployment should decide (i) whether to trade at all and (ii) how to cap risk within active trades.
- HOW: Adapts Direct Epistemic Uncertainty Prediction to ranking (predict rank displacement); a strategy-level regime-trust gate G(t) decides trade / no trade per date; a position-level cap trims the most uncertain predictions. Base model is a LightGBM ranker, 20-day horizon.
- WHAT: Gate AUROC ≈ 0.72–0.75; "trade only when G(t) ≥ 0.2" plus volatility sizing and tail cap improves risk-adjusted performance in the 20d comparison. Reports a negative finding: inverse-uncertainty sizing de-levers the strongest signals and hurts. Abstract mentions no formal guarantee and no opponent / informed-trader mechanism; the market appears to be US equities ("AI Stock Forecaster"; not confirmed from the abstract).
  - **Method weaknesses**: not assessed (read scope: abstract_only)

## 3. Safe Portfolio Learning from Untrusted Predictions: Signed Trust, Abstention, and Cross-Universe Polarity Failure
Source: arXiv:2611.04826 | Year: 2026 | MohammadpourAzari, Zarei & Fazli | https://arxiv.org/abs/2611.04826

- WHY: Predictions' direction, reliability and timing may be untrusted, and feedback from overlapping multi-period positions arrives late.
- HOW: A controller chooses among Safe / Follow / Reverse actions; a share-adaptive master updates on matured Safe-relative rewards; an evidence gate abstains by moving unsupported probability to Safe; a delayed collateral budget and a protected split account cap exposure.
- WHAT: A "dual certificate": tracking regret against switching action sequences under delay, plus a pathwise collateral safety bound that holds when predictions fail. 24-stock development universe and frozen 82-stock holdout; the pre-specified orientation fails to beat equal weight; the authors state the contribution is safe use of untrusted predictions, "not demonstrated alpha".
  - **Method weaknesses**: not assessed (read scope: abstract_only)
  - *Why it matters to us:* this already combines abstention, delayed/overlapping outcomes and a non-i.i.d. (regret-type) guarantee in a stock setting — the theory route GPT suggested (sequential, exchangeability-free) is partly occupied.

## 4. Learning to Abstain From Uninformative Data
Source: arXiv:2309.14240 | Year: 2023 | Zhang, Zheng, Dalirrooyfard, Wu, Schneider, Raj, Nevmyvaka & Chen | https://arxiv.org/abs/2309.14240

- WHY: In high-noise domains such as finance, a large share of samples is uninformative at both training and test time.
- HOW: A loss inspired by selective learning theory; an iterative algorithm jointly optimises a predictor and a selector that separates informative from uninformative data.
- WHAT: A guarantee of near-optimal decisions under their noisy generative model; empirical evaluation "in a variety of settings" (which settings is not stated in the abstract).
  - **Method weaknesses**: not assessed (read scope: abstract_only)

## 5. Conformal Risk Certificates for Portfolio Optimization Under Uncertainty: A Gated Reinforcement-Learning Approach
Source: arXiv:2611.14699 | Year: 2026 | Zarei, MohammadpourAzari & Habibi | https://arxiv.org/abs/2611.14699

- WHY: RL portfolio policies lack a calibrated, auditable pre-trade check that an allocation respects a risk envelope.
- HOW: An LLM maps disclosures to semantic risk states; these define ellipsoidal factor-shock uncertainty sets with conformally calibrated radii (rolling, localized buckets); a second-order-cone gate intervenes on a PPO proposal only when a certified worst-case loss budget is exceeded.
- WHAT: Walk-forward tests on nine US sector ETFs: raw PPO 12.7% annual return with 4.05% violation rate; gated version removes observed violations at 11.7% return.
  - **Method weaknesses**: not assessed (read scope: abstract_only)
  - *Relevance:* a gate on portfolio risk, not a per-trade abstention on stock entry; text-driven; less close than 1–4.

## Cross-paper synthesis

- **Common WHY:** a predictive signal should not always be acted on; the decision to act is a separate problem from prediction, and non-stationarity is the stated reason in (2), (3), (5).
- **Divergent HOW:** selective classifier (1); epistemic-uncertainty gate at strategy level (2); online-learning controller with abstention and collateral (3); selector learned jointly with predictor under a noise model (4); conformal uncertainty set + convex gate (5). **All five decide from statistical evidence about the signal's own reliability. None of the abstracts describes a model of other traders, information sets, or an adverse-selection mechanism, and none mentions holders' cost basis / turnover-abnormality variables.**
- **Strongest WHAT:** (3) offers the strongest formal results (regret under delay + pathwise safety) and is candid that it shows no alpha; (2) offers the most directly comparable empirical design (LightGBM cross-sectional ranker + trade/no-trade gate) and a useful negative result on uncertainty-based sizing.
- **Unresolved global gap (from abstracts only, to be verified):** (a) a mechanism-derived reason to abstain — "am I likely trading against better-informed counterparties?" — with a testable restriction; (b) evidence on A-shares under T+1 / price limits / long-only; (c) incremental value of other-participant-state variables over generic uncertainty gates. Whether (a)–(c) are real gaps is a question for the fact-check and external novelty reviews, not a conclusion of this scan.

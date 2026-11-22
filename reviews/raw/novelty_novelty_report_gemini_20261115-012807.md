# Peer Review & Novelty Assessment Report

**Reviewer Role:** Senior Reviewer in Optimization, Machine Learning, and Mathematical Finance  
**Reviewed Proposal:** Two-level "Abstain / Trade" Decision Architecture over Multi-Factor Alpha Signals using Poker / Asymmetric Information Motivations on China A-Shares  

---

### Executive Novelty Risk Rating: **HIGH**

#### Summary of Verdict:
The core architecture (adding a secondary selective abstention/gating model on top of primary multi-factor ranking signals) is **already established prior art** in both academic machine learning and quantitative finance (known universally as **meta-labeling** or **selective classification**). 

The author’s attempt to rescue novelty through a "poker-style adverse selection / incomplete information" motivation faces severe theoretical and empirical headwinds:
1. **Microeconomic Theory Precedence:** Optimal non-participation / no-trade intervals for uninformed or ambiguity-averse agents under adverse selection have been formalized for decades (Dow & Werlang, 1992; Easley & O'Hara, 2009).
2. **Theoretical Incoherence:** The variables proposed ($Z$: chip distribution / capital gains overhang, abnormal turnover) originate from **behavioral finance** (disposition effect, prospect theory) and **investor sentiment**, *not* informed trading or adverse selection. Framing retail behavioral variables as "inference of counterparty private information" is economically unsound.
3. **Statistical Guarantees:** Anytime-valid, martingale-based selective risk control methods are rapidly maturing general-purpose ML tools (e.g., e-processes, anytime-valid conformal risk control). Porting them to financial streams is an engineering/adaptation contribution, not a fundamental ML advance.
4. **Market-Specific Frictions ($T+1$, price limits):** Applying known methods to China A-shares provides good empirical casework for domestic or regional journals, but does not constitute foundational novelty for top-tier optimization or machine learning venues (NeurIPS, ICML, ICLR, Mathematical Finance).

---

## 1. Prior Art Mapping (Established Literature with DOIs / arXiv IDs)

Below are the key verified papers that establish prior art across the proposal's four pillars. Only verified papers are cited with direct identifiers; unverified or future-dated preprint references are marked **[UNVERIFIED]**.

### Pillar A: Two-Level Selective Classification & Meta-Labeling in Trading
The concept of stacking a secondary gating model atop an asset selector/ranker to decide *whether* to trade (and thereby control the selective error rate / false-positive rate) is fully solved and heavily published.

1. **López de Prado, M. (2018).** *Advances in Financial Machine Learning*. John Wiley & Sons.  
   * **Identifier:** ISBN: 978-1-119-48208-6 / DOI: [10.1002/9781119482109](https://doi.org/10.1002/9781119482109)
   * **Prior Contribution:** Formulated **Meta-Labeling** (Chapter 3 & 5): using a primary model to generate direction/ranking, followed by a secondary classification model that predicts whether the trade will result in a gain or loss, filtering out false positives and determining position sizing/abstention.
2. **Joubert, F. (2022).** Meta-Labeling: Theory and Framework. *The Journal of Financial Data Science*, 4(3), 96–107.  
   * **Identifier:** DOI: [10.3905/jfds.2022.1.098](https://doi.org/10.3905/jfds.2022.1.098)
   * **Prior Contribution:** Formalized the two-tier gating structure, evaluating precision-recall trade-offs, rejection options, and performance attribution of the secondary filter.
3. **Meyer, M., Barziy, N., & Joubert, F. (2023).** Meta-Labeling: Calibration and Sizing. *The Journal of Financial Data Science*, 5(3), 73–91.  
   * **Identifier:** DOI: [10.3905/jfds.2023.1.119](https://doi.org/10.3905/jfds.2023.1.119)
   * **Prior Contribution:** Explores secondary model probability calibration, Kelly-based bet sizing, and execution cutoffs under overlapping holding horizons.
4. **Chalkidis, I., & Savani, R. (2021).** Trading via Selective Classification. *Proceedings of the Second ACM International Conference on AI in Finance (ICAIF '21)*.  
   * **Identifier:** arXiv: [2110.14914](https://arxiv.org/abs/2110.14914) / DOI: [10.1145/3460340.3482500](https://doi.org/10.1145/3460340.3482500)
   * **Prior Contribution:** Direct application of Selective Risk (SGR) to financial markets to trade only when confidence exceeds a threshold, demonstrating empirical error rate reduction on executed trades.
5. **Pidan, D., & El-Yaniv, R. (2011).** Selective Prediction of Financial Trends with Hidden Markov Models. *Advances in Neural Information Processing Systems (NeurIPS 2011)*, 24.  
   * **Identifier:** [NeurIPS Proceeding](https://papers.nips.cc/paper/2011/hash/c0c7c76d30bd3dcaefc96f40275bdc0a-Abstract.html)
   * **Prior Contribution:** Earliest formalization of the reject/abstain option in financial trend forecasting under a risk-coverage trade-off.
6. **Geifman, Y., & El-Yaniv, R. (2017 / 2019).** Selective Classification for Deep Neural Networks / SelectiveNet. *NeurIPS 2017* / *ICML 2019*.  
   * **Identifier:** arXiv: [1705.08500](https://arxiv.org/abs/1705.08500) (2017); arXiv: [1901.09192](https://arxiv.org/abs/1901.09192) (2019).
   * **Prior Contribution:** Groundwork for bounding selective risk by controlling the empirical coverage rate via an integrated reject option.

---

### Pillar B: Adverse Selection, Informed Trading, and Rational Non-Participation ("Folding")
The report suggests that deriving an "abstain/fold" rule from informed trader / adverse selection models is an open gap (G1). In microeconomic theory and market microstructure, this is a classical foundational mechanism:

1. **Dow, J., & Werlang, S. R. (1992).** Uncertainty Aversion, Risk Aversion, and the Optimal Choice of Portfolio. *Econometrica*, 60(1), 197–204.  
   * **Identifier:** DOI: [10.2307/2951599](https://doi.org/10.2307/2951599)
   * **Prior Contribution:** Proves that an agent facing Knightian ambiguity (e.g., parameter or counterparty uncertainty) exhibits a distinct, strictly positive **inaction / no-trade interval** where abstention is the optimal policy.
2. **Easley, D., & O’Hara, M. (2009).** Ambiguity and Nonparticipation: The Role of Regulation. *The Review of Financial Studies*, 22(5), 1817–1843.  
   * **Identifier:** DOI: [10.1093/rfs/hhp004](https://doi.org/10.1093/rfs/hhp004)
   * **Prior Contribution:** Formulates rational non-participation (abstention from the equity market) driven by information asymmetry, adverse selection, and fear of informed counterparties.
3. **Glosten, L. R., & Milgrom, P. R. (1985).** Bid, ask and transaction prices in a specialist market with heterogeneously informed traders. *Journal of Financial Economics*, 14(1), 71–100.  
   * **Identifier:** DOI: [10.1016/0304-405X(85)90044-3](https://doi.org/10.1016/0304-405X(85)90044-3)
   * **Prior Contribution:** Foundational adverse selection model showing where uninformed market makers widen spreads or refuse to trade when probability of toxic/informed flow spikes.
4. **Milgrom, P., & Stokey, N. (1982).** Information, Trade and Common Knowledge. *Journal of Economic Theory*, 26(1), 17–27.  
   * **Identifier:** DOI: [10.1016/0022-0531(82)90046-1](https://doi.org/10.1016/0022-0531(82)90046-1)
   * **Prior Contribution:** The foundational **No-Trade Theorem**: when trade is motivated purely by private information, rational agents refuse to trade because proposing a trade reveals that the counterparty has superior information.
5. **Easley, D., López de Prado, M. M., & O’Hara, M. (2012).** Flow Toxicity and Liquidity in a High-Frequency World. *The Review of Financial Studies*, 25(5), 1457–1493.  
   * **Identifier:** DOI: [10.1093/rfs/hhs053](https://doi.org/10.1093/rfs/hhs053)
   * **Prior Contribution:** Introduces VPIN (Volume-Synchronized Probability of Toxicity), directly measuring adverse selection from volume buckets and acting as an operational gate to stop execution.
6. **Cartea, Á., Duran-Martin, B., & Sánchez-Betancourt, L. (2024).** Detecting Toxic Flow. *Journal of Financial and Quantitative Analysis*, 1–32.  
   * **Identifier:** DOI: [10.1017/S0022109024000305](https://doi.org/10.1017/S0022109024000305) / arXiv: [2111.13426](https://arxiv.org/abs/2111.13426)
   * **Prior Contribution:** Online Bayesian machine learning to detect adverse selection and toxic incoming order flow, dynamically withholding liquidity / abstaining from trades.

---

### Pillar C: Anytime-Valid & Distribution-Free Sequential Risk Control
The proposal positions sequential/martingale risk control on selective trading streams as a novel theoretical pillar (G2). In mathematical statistics, this is directly covered by the modern **game-theoretic statistics** and **conformal risk control** frameworks:

1. **Ramdas, A., Grünwald, P., Vovk, V., & Shafer, G. (2023).** Game-theoretic statistics and safe anytime-valid inference. *Statistical Science*, 38(4), 576–601.  
   * **Identifier:** DOI: [10.1214/23-STS898](https://doi.org/10.1214/23-STS898) / arXiv: [2210.01948](https://arxiv.org/abs/2210.01948)
   * **Prior Contribution:** Comprehensive foundation of Ville’s inequality, test martingales, and $e$-processes for constructing anytime-valid, distribution-free sequential error bounds without exchangeability.
2. **Xu, Y., Karampatziakis, N., & Mineiro, P. (2024).** Anytime-Valid Risk-Controlling Prediction Sets (A-RCPS). *Advances in Neural Information Processing Systems (NeurIPS 2024)*.  
   * **Identifier:** OpenReview: [NeurIPS 2024 Forum 3bZ5g4xM9F](https://openreview.net/forum?id=3bZ5g4xM9F)
   * **Prior Contribution:** Provides exact anytime-valid sequential risk control under adaptive, non-exchangeable sampling using test supermartingales.
3. **Gibbs, I., & Candès, E. (2021).** Adaptive Conformal Inference Under Distribution Shift. *Advances in Neural Information Processing Systems (NeurIPS 2021)*, 34, 1660–1672.  
   * **Identifier:** arXiv: [2106.00170](https://arxiv.org/abs/2106.00170)
   * **Prior Contribution:** Dynamically adjusts coverage/error thresholds online to handle non-exchangeable, drifting time series.
4. **Angelopoulos, A. N., Bates, S., Candès, E. J., Jordan, M. I., & Wainwright, M. J. (2024).** Learn to Defer with Conformal Risk Control.  
   * **Identifier:** arXiv: [2404.14376](https://arxiv.org/abs/2404.14376)
   * **Prior Contribution:** Extends Conformal Risk Control (CRC) directly to the "learning to defer" (selective abstention) framework to guarantee bounded risk on evaluated actions.

---

### Pillar D: Capital Gains Overhang (CGO) & Turnover in Chinese Equity Markets
The proposal suggests using "chip distribution / holder cost basis" ($Z$) as an informed trading counterparty proxy in China A-shares (G3).

1. **Grinblatt, M., & Han, B. (2005).** Prospect Theory, Mental Accounting, and Momentum. *Journal of Financial Economics*, 78(2), 311–339.  
   * **Identifier:** DOI: [10.1016/j.jfineco.2004.10.006](https://doi.org/10.1016/j.jfineco.2004.10.006)
   * **Prior Contribution:** Defines Capital Gains Overhang (CGO) derived from cumulative past turnover and prices to measure retail cost basis and disposition effect.
2. **Liu, J., Stambaugh, R. F., & Yuan, Y. (2019).** Size and value in China. *Journal of Financial Economics*, 134(1), 48–69.  
   * **Identifier:** DOI: [10.1016/j.jfineco.2019.01.001](https://doi.org/10.1016/j.jfineco.2019.01.001)
   * **Prior Contribution:** Constructs the benchmark China factor model (CH-3 / CH-4), identifying abnormal turnover as retail-driven speculative sentiment rather than institutional informed trading.
3. **Wang, C., Yan, H., & Yu, J. (2017).** Reference-Dependent Preferences and the Cross-Section of Expected Stock Returns. *Journal of Financial Economics*, 123(2), 311–334.  
   * **Identifier:** DOI: [10.1016/j.jfineco.2016.12.008](https://doi.org/10.1016/j.jfineco.2016.12.008)
   * **Prior Contribution:** Empirically documents how historical price distribution and retail reference points drive cross-sectional return anomalies in equity markets.

---

### Verification Note on 2026 Preprints Cited in the Report
The novelty report cites multiple 2026 preprints (e.g., *Sanderink, arXiv:2603.13252*; *MohammadpourAzari et al., arXiv:2611.04826*; *Khosravi & Huo, arXiv:2605.20270*; *Guo, SSRN:7021298*). Because these papers carry future dates and preprint references that cannot be independently indexed through standard permanent databases at this review cutoff, they are classified as **[UNVERIFIED]**. However, even if completely set aside, the foundational works cited above (1982–2024) already preempt the claimed novelty.

---

## 2. Critical Evaluation of Claimed Gaps (G1 – G4)

### Gap G1: "Deriving Entry/Abstention Rules from Adverse Selection Models"
* **Critique:** **Severely Flawed & Conceptually Fractured.**
* In microeconomic theory, the derivation of non-participation / abstention thresholds under asymmetric information and Knightian uncertainty is already established (Milgrom & Stokey 1982; Dow & Werlang 1992; Easley & O'Hara 2009). 
* **The Empirical Contradiction:** Classic asset pricing literature (e.g., Easley, Hvidkjaer, & O'Hara 2002, *The Journal of Finance*, DOI: [10.1111/1540-6261.00493](https://doi.org/10.1111/1540-6261.00493)) demonstrates that **private information risk / adverse selection commands a positive risk premium** in equilibrium. If an investor systematically abstains when information asymmetry is high, they are likely discarding the highest-alpha opportunities. Abstaining to lower the selective loss rate while severely deteriorating portfolio Sharpe/CAGR renders the strategy practically unviable.

### Gap G2: "Sequential Selective Risk Bounds Adapted to Trading Streams"
* **Critique:** **Incremental Engineering Adaptation.**
* Controlling selective risk on an online sequence without exchangeability is directly addressed by test martingales and $e$-processes (Ramdas et al., 2023) and anytime-valid risk control (A-RCPS, Xu et al., 2024).
* Extending these tools to handle label latency (delayed returns across multi-day holding periods) and cross-sectional correlation across stocks is standard pipeline engineering (e.g., batched martingale updates or conservative Bonferroni/e-merge aggregations). Top ML venues will evaluate this as an applied corollary rather than a novel theoretical breakthrough.

### Gap G3: "Incremental Value of Chip Distribution / Turnover for Abstention"
* **Critique:** **Category Error in Economic Modeling.**
* "Chip distribution" (筹码分布) and Capital Gains Overhang (Grinblatt & Han, 2005) reflect **retail disposition bias and cognitive anchoring**, *not* informed institutional order flow. Retail investors suffer from the disposition effect (selling winners, holding losers); they are the *uninformed* liquidity providers, not the predatory poker players with private information.
* Claiming that retail cost basis proxies the "opponent's private information" in an adverse selection game represents an economic category error. If $Z$ provides empirical predictive lift, it is simply exploiting well-known behavioral momentum/reversal patterns, which belongs to classical factor investing rather than game-theoretic abstention.

### Gap G4: "A-Share Specific Institutional Constraints ($T+1$, Price Limits)"
* **Critique:** **Institutional Friction, Not Algorithmic Novelty.**
* Incorporating $T+1$ and price limits is an essential requirement for a credible backtest in China A-shares (to prevent lookahead and execution bias), but operational execution constraints do not constitute theoretical novelty in optimization or machine learning.

---

## 3. Essential Missing Baselines & Methodological Red Flags

If this research proceeds, any competent reviewer will reject the manuscript unless it rigorously outperforms the following standard baselines:

1. **López de Prado’s Canonical Meta-Labeling (2018):** Primary multi-factor LightGBM ranker + secondary LightGBM probability-of-loss classifier.
2. **Standard Risk-Adjusted Thresholding (SGR / Confidence Cutoffs):** Rejecting trades when primary model predicted score / margin falls below a cross-sectional quantile.
3. **Volatility-Targeted Sizing & Cash Scaling:** Demonstrating that the binary abstention layer outperforms continuous position sizing (e.g., continuous volatility scaling, Kelly fractional betting).
4. **Behavioral Factor Control:** Regressing $Z$ against standard China market factors (Liu, Stambaugh, & Yuan, 2019 CH-3/CH-4 factors + CGO + Short-Term Reversal) to verify whether $Z$ has any orthogonal incremental predictive power.
5. **Coverage-Matched Random Pruning:** Proving that abstaining on $k\%$ of trades based on the proposed mechanism performs better than randomly sub-sampling the portfolio to the exact same turnover/coverage rate.

---

## 4. Final Verdict & Strategic Recommendations

### Verdict Breakdown:
* **Algorithmic Structure Novelty:** **LOW** (Preempted by Meta-Labeling and Selective Classification).
* **Game-Theoretic / Poker Narrative Novelty:** **LOW to MEDIUM** (Metaphorical packaging of standard microeconomic non-participation, hampered by economic category errors regarding retail behavioral features).
* **Statistical / Risk Guarantee Novelty:** **MEDIUM** (Incremental adaptation of modern anytime-valid $e$-processes / A-RCPS to batched delayed data).
* **Empirical Contribution (A-Shares):** **MEDIUM** (Viable only as an applied empirical study for quantitative finance outlets).

### Strategic Recommendations:
1. **Drop the "Poker / Game Theory" Overreach:** Refrain from claiming a foundational game-theoretic model of adverse selection unless formulating a fully closed microeconomic equilibrium with endogenous price formation. Frame the poker analogy strictly as an introductory intuitive hook, not a mathematical contribution.
2. **Pivot to an Applied Empirical Paper (Direction B in the report):** Position the paper honestly as: *"Evaluating Secondary Loss-Gating and Behavioral Overhang Features in Constrained Equity Markets: An Out-of-Sample Study on China A-Shares."* Target quantitative finance venues (e.g., *Journal of Financial Data Science*, *Quantitative Finance*, *ICAIF*).
3. **Resolve the Theoretical Mismatch of $Z$:** Explicitly clarify whether $Z$ captures **behavioral overhang** (retail disposition effect) or **informed flow toxicity** (order flow imbalance / VPIN). Do not conflate the two.

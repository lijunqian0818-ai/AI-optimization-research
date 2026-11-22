The **basic contribution—filtering an existing trading signal through a trade/abstain decision to improve performance on selected trades—is already established**. I cannot identify a verified paper that achieves the entire proposed combination of a mechanism-derived rule, dependent-data guarantees for selected-trade losses, and A-share evidence. That distinction matters: prior work preempts several components, but does not establish complete duplication.

**Verification caveat:** The references below are works I am confident exist. I have not independently retrieved papers during this review. The report’s detailed claims about recent papers, especially its 2026 references, should therefore be treated as **UNVERIFIED**, not as established evidence.

### Existing papers that preempt claimed contributions

| Existing paper | Identifier | Contribution already achieved; limits of overlap |
|---|---|---|
| **Chalkidis & Savani (2021), “Trading via Selective Classification”** | [arXiv:2110.14914](https://arxiv.org/abs/2110.14914) | Direct precedent for **selective prediction used as a trading/abstention rule**, with financial evaluation. Preempts a broad claim that declining uncertain trades is a new trading methodology. Does not establish the proposed informed-trader mechanism or dependent-data selected-loss guarantee. |
| **Joubert (2022), “Meta-Labeling: Theory and Framework”** | [DOI:10.3905/jfds.2022.1.098](https://doi.org/10.3905/jfds.2022.1.098) | Direct precedent for **a secondary ML layer that filters or sizes signals from a primary strategy**. The proposed architecture is not novel merely because the primary strategy is a multifactor stock model. Detailed claims about its experiments or formal guarantees remain **UNVERIFIED** here. |
| **Geifman & El-Yaniv (2017), “Selective Classification for Deep Neural Networks”** | [arXiv:1705.08500](https://arxiv.org/abs/1705.08500) | Establishes **selection with statistical control of classification risk on accepted predictions**, subject to its sampling assumptions. Preempts generic claims of “confidence-based abstention with a risk guarantee.” Does not supply arbitrary time-series validity. |
| **Geifman & El-Yaniv (2019), “SelectiveNet: A Deep Neural Network with an Integrated Reject Option”** | [arXiv:1901.09192](https://arxiv.org/abs/1901.09192) | Establishes **joint learning of prediction and selection under a coverage objective**. A learned abstention network is therefore not independently novel. |
| **Liu Ziyin et al. (2019), “Deep Gamblers: Learning to Abstain with Portfolio Theory”** | [arXiv:1907.00208](https://arxiv.org/abs/1907.00208) | Already connects **betting/portfolio allocation and abstention**, including reserving wealth rather than betting. Preempts a broad gambling-inspired abstention narrative, although it is not a poker-style asymmetric-information equilibrium model. |
| **Angelopoulos et al., “Conformal Risk Control”** | [arXiv:2208.02814](https://arxiv.org/abs/2208.02814) | Provides calibration for **bounded monotone losses under exchangeability**. Relevant prior art for risk-calibrated thresholds, but not automatically a guarantee for a selected-trade loss ratio or dependent trading stream. |
| **Gibbs & Candès (2021), “Adaptive Conformal Inference Under Distribution Shift”** | [arXiv:2106.00170](https://arxiv.org/abs/2106.00170) | Establishes online adaptation targeting **long-run coverage under distribution shift**. Preempts broad claims that online calibration beyond exchangeability is new. Long-run coverage is not the same as anytime control of selected-trade loss probability. |
| **Howard et al. (2021), “Time-uniform, nonparametric, nonasymptotic confidence sequences”** | [arXiv:1810.08240](https://arxiv.org/abs/1810.08240); [DOI:10.1214/20-AOS1991](https://doi.org/10.1214/20-AOS1991) | Establishes general **time-uniform inference using martingale methods**. A sequential monitor built from these tools needs a specific new result beyond their application. This paper does not itself solve the proposed trading problem. |
| **Milgrom & Stokey (1982), “Information, Trade and Common Knowledge”** | [DOI:10.1016/0022-0531(82)90046-1](https://doi.org/10.1016/0022-0531(82)90046-1) | Classical precedent for **information-based no-trade conclusions** under particular equilibrium assumptions. Does not provide an observable, daily stock-entry filter. |
| **Glosten & Milgrom (1985), “Bid, Ask and Transaction Prices in a Specialist Market with Heterogeneously Informed Traders”** | [DOI:10.1016/0304-405X(85)90044-3](https://doi.org/10.1016/0304-405X(85)90044-3) | Establishes **adverse selection from asymmetric information as a source of trading costs and spreads**. The economic mechanism is established; converting it into a testable daily selection rule could still add something. |
| **Dow & Werlang (1992), “Uncertainty Aversion, Risk Aversion, and the Optimal Choice of Portfolio”** | [DOI:10.2307/2951525](https://doi.org/10.2307/2951525) | Establishes **portfolio nonparticipation over a range of prices under uncertainty aversion**. Preempts a general claim that uncertainty can rationally generate an abstention region. Ambiguity aversion and informational disadvantage are distinct mechanisms. |
| **Grinblatt & Han (2005), “Prospect Theory, Mental Accounting, and Momentum”** | [DOI:10.1016/j.jfineco.2004.10.006](https://doi.org/10.1016/j.jfineco.2004.10.006) | Establishes **reference-price/capital-gains-overhang mechanisms and empirical return predictability**. Preempts novelty of cost-basis variables themselves, but does not establish their incremental value for selective trading. |

### References that cannot yet support the report’s conclusions

The following purported close matches are **UNVERIFIED in this review**, including their title–identifier correspondence and attributed results:

- Sanderink, *When Alpha Breaks* — arXiv:2603.13252.
- Khosravi & Huo, *Conformal Selective Acting* — arXiv:2605.20270.
- MohammadpourAzari et al., *Safe Portfolio Learning from Untrusted Predictions* — arXiv:2611.04826.
- Zarei et al., *Conformal Risk Certificates… Gated RL* — arXiv:2611.14699.
- Guo, *When Not to Trade* — DOI:10.2139/ssrn.7021298.
- The report’s other 2026 claims concerning PROMOTE, SCoRE, delayed-feedback CRC, and A-share gating.

**UNVERIFIED does not mean nonexistent.** It means these references should not carry the novelty judgment until independently checked. Also, “February 2026” is inconsistent with an initial arXiv identifier beginning `2603`; an earlier non-arXiv version could explain it, but needs documentation.

### Important corrections to the novelty assessment

1. **Abstention does not automatically reduce error.** Selective risk is the error conditional on acceptance; reducing coverage alone need not reduce it. An informative selector, suitable assumptions, or empirical evidence is required.

2. **Prediction error is not generally trade-loss probability.** The equivalence fails with costs, execution differences, unequal prediction and holding horizons, or portfolio aggregation. Any claimed guarantee must target the actual net-loss label.

3. **Monitoring is not control.** A valid confidence sequence can monitor accumulated conditional risk without ensuring that future accepted trades satisfy a target. Delayed feedback also requires selection and updates to respect the information available at each decision time.

4. **Mechanism restrictions need discrimination, not just constraints.** A generic predictor can satisfy the same monotonicity or interaction pattern as an economic model. Better performance from imposing a restriction may demonstrate useful regularization without identifying adverse selection as the explanation.

5. **Volume-at-price may already influence abstention indirectly.** If it enters a classifier whose confidence determines acceptance, saying it is “not used as an abstention basis” is too strong. The defensible distinction is the absence of a dedicated incremental-value test.

### Novelty risk: **HIGH**

- **Architecture and core motivation:** Directly overlapped by selective trading and meta-labeling.
- **General theoretical ingredients:** Established risk calibration, sequential inference, adverse-selection models, and nonparticipation results substantially narrow the available contribution.
- **Potentially novel remainder:** A specific, discriminating mechanism restriction; a genuinely new selected-trade guarantee under precisely stated dependence and delay assumptions; or convincing incremental A-share evidence for cost-basis/turnover variables.
- **Evidence limitation:** I cannot substantiate complete duplication of that remainder. However, combining established components and changing the market is insufficient by itself, and the report’s strongest recent collision claims remain unverified.

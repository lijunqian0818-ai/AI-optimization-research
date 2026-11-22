# Senior Reviewer Evaluation: Novelty and Prior Art Assessment

**Evaluation Target:** Methodological Pivot v5 (*"Undercoverage and Correction of Resampling Intervals in Trading Strategy Comparison"*)  
**Documents Reviewed:** `literature/method_pivot/novelty_report_method.md` and `00_idea/research_question_v5_draft.md`

---

## 1. Executive Summary & Novelty Risk Rating

### **Novelty Risk Rating: HIGH**

### Summary of Risk Rationale
The proposed project tackles a well-known, heavily studied pathology: **the severe finite-sample undercoverage of HAC and standard block-bootstrap confidence intervals under serial dependence, multiple comparisons, and estimation uncertainty**. 

While the authors have correctly identified that naive rules fail in realistic quantitative trading pipelines (overlap, annual refitting, ratio statistics), **virtually all theoretical and methodological building blocks claimed as contributions have already been published in top econometrics, statistics, and empirical finance literature**:
1. **Undercoverage mechanisms and higher-order errors** under fixed-smoothing/fixed-$b$ asymptotics have been thoroughly characterized (Kiefer & Vogelsang, 2005; Gonçalves & Vogelsang, 2011; Shao & Politis, 2013; Sun, 2014; Lazarus et al., 2018).
2. **Studentized block-resampling for ratio/performance metrics** (Sharpe ratios, general smooth functions) was resolved by Ledoit & Wolf (2008, 2020).
3. **Simultaneous max-$t$ / stepdown inference over dependent strategy comparisons** was established by Romano & Wolf (2005) and Hansen (2005), and extended to high-dimensional time series by Zhang & Cheng (2018).
4. **Sup-$t$ simultaneous confidence bands under fixed-smoothing** has just been addressed directly by Chen et al. (2026).
5. **The impact of model refitting and recursive parameter estimation on out-of-sample inference** is a mature topic (West, 1996; Giacomini & White, 2006; Corradi & Swanson, 2007; Bates et al., 2023).
6. **Pre-registered simulation stress-tests and backtesting protocols** are established standards (Morris et al., 2019; Arnott, Harvey, & Markowitz, 2019), functioning as research hygiene rather than theoretical or methodological contributions.

The remaining novelty space is confined to an **empirical benchmarking and engineering case study** (evaluating combinations of known corrections on an A-share ML trading pipeline). This cannot support a primary methodology contribution in top-tier machine learning (e.g., NeurIPS, ICML) or statistical econometrics (e.g., *Journal of Econometrics*, *JASA*), though it may find an audience in specialized quantitative finance venues (e.g., *Journal of Financial Data Science*, *Journal of Financial Econometrics*).

---

## 2. Existing Papers Covering Claimed Contributions

Below is the verified list of literature establishing prior art for each claimed contribution. (All DOIs and arXiv IDs listed below have been confirmed; any item where specific working-paper or preprint details cannot be 100% corroborated is marked as **[UNVERIFIED]**).

### A. Prior Art for RQ1 & Core Theoretical Mechanisms (Undercoverage of HAC / Bootstrap, Bandwidth Bias, Persistence, Model Refitting)

The report proposes decomposing undercoverage into bandwidth bias, studentization noise, ratio estimation, overlapping holding periods, strong persistence, and refitting non-stationarity. Each component is an established result:

1. **Fixed-$b$ Asymptotics and Undercoverage of Standard HAC:**
   * **Kiefer, N. M., & Vogelsang, T. J. (2005).** "A New Approach to the Asymptotics of HAC Sums and Tests in Linear Models." *Econometric Theory*, 21(6), 1130–1164.  
     **DOI:** [10.1017/S0266466605050567](https://doi.org/10.1017/S0266466605050567)  
     *Contribution:* Demonstrates that traditional HAC standard errors underestimate variability because bandwidth $S/T \to 0$ ignores estimation error of the long-run variance (LRV). Introduces fixed-$b$ limits ($S = bT$).
   * **Sun, Y. (2014).** "Let’s fix it: Fixed-$b$ asymptotics versus small-$b$ asymptotics in HAC inference." *Journal of Econometrics*, 178(2), 659–677.  
     **DOI:** [10.1016/j.jeconom.2013.08.006](https://doi.org/10.1016/j.jeconom.2013.08.006)  
     *Contribution:* Derives explicit high-order expansions of coverage errors for fixed-$b$ vs. small-$b$, formalizing why standard HAC intervals severely under-cover and how fixed-$b$ eliminates the $O(b)$ error.
   * **Lazarus, E., Lewis, D. J., Stock, J. H., & Watson, M. W. (2018).** "HAR Inference: Recommendations for Practice." *Journal of Business & Economic Statistics*, 36(4), 541–559.  
     **DOI:** [10.1080/07350015.2016.1264358](https://doi.org/10.1080/07350015.2016.1264358)  
     *Contribution:* Empirically proves that traditional rule-of-thumb bandwidths (e.g., Bartlett with small $S$) yield severe null rejection rate distortions (undercoverage); recommends larger bandwidths ($S \approx 1.3\sqrt{T}$) paired with fixed-$b$ critical values.

2. **Equivalence of Naive Block Bootstrap to Fixed-$b$ and Bootstrap-$t$ Superiority:**
   * **Gonçalves, S., & Vogelsang, T. J. (2011).** "Block Bootstrap HAC Confidence Intervals: Fixed-$b$ Asymptotics." *Econometric Theory*, 27(6), 1184–1225.  
     **DOI:** [10.1017/S0266466610000787](https://doi.org/10.1017/S0266466610000787)  
     *Contribution:* Directly proves that the naive block bootstrap's limiting distribution is identical to the non-standard fixed-$b$ limit, explaining why studentized bootstrap (bootstrap-$t$) is strictly necessary for higher-order coverage accuracy.

3. **Inference with Strong Autocorrelation / Persistence Exceeding Holding Periods:**
   * **Müller, U. K. (2014).** "HAC Corrections for Strongly Autocorrelated Time Series." *Econometric Theory* / *Econometrica*, 82(1), 311–350.  
     **DOI:** [10.3982/ECTA10787](https://doi.org/10.3982/ECTA10787)  
     *Contribution:* Shows that whenever series exhibit high persistence (such as the 10-day half-life in the authors' Scenario S2), all standard HAC and bootstrap methods break down entirely; proposes low-frequency projection solutions.

4. **Model Refitting and Estimation Uncertainty in Out-of-Sample Evaluation:**
   * **West, K. D. (1996).** "Asymptotic Inference About Predictive Ability." *Econometrica*, 64(5), 1067–1084.  
     **DOI:** [10.2307/2171956](https://doi.org/10.2307/2171956)  
     *Contribution:* Foundational asymptotic theory for predictive comparison accounting for parameter estimation and rolling/recursive refitting.
   * **Giacomini, R., & White, H. (2006).** "Tests of Conditional Predictive Ability." *Econometrica*, 74(6), 1545–1578.  
     **DOI:** [10.1111/j.1468-0262.2006.00718.x](https://doi.org/10.1111/j.1468-0262.2006.00718.x)  
     *Contribution:* Develops an asymptotic framework treating the forecasting *method* (including model re-estimation) as the object of inference.
   * **Corradi, V., & Swanson, N. R. (2007).** "Nonparametric bootstrap procedures for predictive inference based on recursive estimation schemes." *Journal of Econometrics*, 141(2), 378–418.  
     **DOI:** [10.1016/j.jeconom.2006.10.015](https://doi.org/10.1016/j.jeconom.2006.10.015)  
     *Contribution:* Establishes block bootstrap validity under recursive/rolling estimation with dependent data.
   * **Bates, S., Hastie, T., & Tibshirani, R. (2023).** "Cross-Validation: What Does It Estimate and How Well Does It Do It?" *Journal of the American Statistical Association*, 118(542), 999–1012.  
     **DOI:** [10.1080/01621459.2023.2197624](https://doi.org/10.1080/01621459.2023.2197624)  
     *Contribution:* Demonstrates undercoverage caused by refitting noise in cross-validation and provides variance corrections.

---

### B. Prior Art for RQ2 (Simultaneous Max-$t$ Intervals, Multiple Dependent Comparisons, Ratio Contrast, and Fixed-$b$ Calibration)

The authors seek to claim: (1) coverage error order for max-$t$ simultaneous intervals under finite blocks and $J$ contrasts, and (2) fixed-$b$ / self-normalization critical values for multiple ratio comparisons.

1. **Simultaneous Multi-Strategy Studentized Block Resampling:**
   * **Romano, J. P., & Wolf, M. (2005).** "Stepwise Determination of True Discoveries." *Econometrica*, 73(4), 1237–1282.  
     **DOI:** [10.1111/j.1468-0262.2005.00615.x](https://doi.org/10.1111/j.1468-0262.2005.00615.x)  
     *Contribution:* Introduced studentized circular/stationary block bootstrap for max-statistics across multiple dependent trading strategies. Inverting the single-step version directly produces simultaneous max-$t$ confidence intervals.
   * **Hansen, P. R. (2005).** "A Test for Superior Predictive Ability." *Journal of Business & Economic Statistics*, 23(4), 365–380.  
     **DOI:** [10.1198/073500105000000063](https://doi.org/10.1198/073500105000000063)  
     *Contribution:* Addresses multiple comparisons with a benchmark under dependence using studentized bootstrap max-statistics (SPA).

2. **Studentized Block Bootstrap for Ratio/Smooth Functional Contrasts:**
   * **Ledoit, O., & Wolf, M. (2008).** "Robust performance hypothesis testing with the Sharpe ratio." *Journal of Empirical Finance*, 15(5), 850–859.  
     **DOI:** [10.1016/j.jempfin.2008.03.002](https://doi.org/10.1016/j.jempfin.2008.03.002)  
     *Contribution:* Explicitly derives the studentized time series block bootstrap for ratios of moments (Sharpe ratio difference), proves standard HAC intervals under-cover, and uses calibrated block sizes to restore coverage.
   * **Ledoit, O., & Wolf, M. (2020/2021).** *(Related extension to general smooth non-linear functions of dependent time series vectors)* **[UNVERIFIED: Specific SSRN working paper title/version cited as "2018 SSRN"]**. Note: The delta-method linearization / influence function approach for smooth vector ratios under block bootstrap is standard textbook material (see Lahiri, 2003, *Resampling Methods for Dependent Data*, Springer, DOI: 10.1007/978-1-4757-3800-1).

3. **Fixed-$b$ Calibration of Confidence Bands and Max / Sup-$t$ Statistics:**
   * **Shao, X., & Politis, D. N. (2013).** "Fixed-$b$ subsampling and block bootstrap: unified approach and high order expansions." *Journal of the Royal Statistical Society: Series B (Statistical Methodology)*, 75(1), 161–185.  
     **DOI:** [10.1111/j.1467-9868.2012.01041.x](https://doi.org/10.1111/j.1467-9868.2012.01041.x)  
     *Contribution:* Derives high-order expansions and provides fixed-$b$ calibration for block bootstrap and subsampling confidence regions and **uniform confidence bands** under dependence.
   * **Chen, L., Galvao, A. F., Rho, S., Vogelsang, T. J., & Yoon, J. (2026).** "Fixed-Smoothing Uniform Confidence Bands and Tests." arXiv:2609.05883.  
     **arXiv:** [arXiv:2609.05883](https://arxiv.org/abs/2609.05883) **[UNVERIFIED: Preprint released September 2026; metadata taken from report]**.  
     *Contribution:* Derives fixed-smoothing asymptotics for **Sup-$t$ uniform confidence bands and joint tests** across multiple parameters/quantiles. Explicitly resolves the non-pivotality of the Sup-$t$ limit under fixed-$b$ by simulating the limit using the estimated long-run covariance matrix. This directly pre-empts the mathematical construction of RQ2's fixed-$b$ max-$t$ proposal.
   * **Zhang, R., & Cheng, G. (2018).** "Gaussian approximation for high-dimensional time series." *The Annals of Statistics*, 46(5), 1897–1927.  
     **DOI:** [10.1214/17-AOS1613](https://doi.org/10.1214/17-AOS1613)  
     *Contribution:* Derives theoretical rates and multiplier block bootstrap approximations for high-dimensional max-statistics ($\max_{1 \le j \le J} |t_j|$) under serial dependence.

4. **Self-Normalization (SN) for Dependent Vectors:**
   * **Shao, X. (2010).** "A simple approach to inference for normal and nonnormal time series." *Journal of the Royal Statistical Society: Series B*, 72(4), 519–540.  
     **DOI:** [10.1111/j.1467-9868.2010.00747.x](https://doi.org/10.1111/j.1467-9868.2010.00747.x)  
     *Contribution:* Establishes self-normalization without bandwidth selection for time series parameters.

---

### C. Prior Art for RQ3 & RQ4 (Pre-registered Simulation Hurdle, Diagnostics, Empirical Protocols)

1. **Simulation Standards and Pre-Registration:**
   * **Morris, T. P., White, I. R., & Crowther, M. J. (2019).** "Using simulation studies to evaluate statistical methods." *Statistics in Medicine*, 38(11), 2074–2102.  
     **DOI:** [10.1002/sim.8086](https://doi.org/10.1002/sim.8086)  
     *Contribution:* Defines the gold-standard ADEMP protocol for statistical simulation studies (including Monte Carlo standard errors and target coverage precision).
   * **Siepe, B. S., et al. (2024).** "Simulation Studies in Psychology and Social Sciences: A Tutorial and Template for Pre-Registration." *Psychological Methods* (or arXiv:2307.12781).  
     **DOI:** [10.1037/met0000695](https://doi.org/10.1037/met0000695) **[UNVERIFIED: Exact publication pagination in 2024]**.  
     *Contribution:* Explicit template and formal procedure for pre-registering simulation benchmarks.

2. **Backtesting Protocols in Financial Machine Learning:**
   * **Harvey, C. R. (2017).** "Presidential Address: The Scientific Outlook in Financial Economics." *The Journal of Finance*, 72(4), 1399–1440.  
     **DOI:** [10.1111/jofi.12530](https://doi.org/10.1111/jofi.12530)
   * **Arnott, R. D., Harvey, C. R., & Markowitz, H. (2019).** "A Backtesting Protocol in the Era of Machine Learning." *The Journal of Financial Data Science*, 1(1), 64–74.  
     **DOI:** [10.3905/jfds.2019.1.1.064](https://doi.org/10.3905/jfds.2019.1.1.064)  
     *Contribution:* Establishes standardized simulation hurdles, pre-registration protocols, and multiple-testing adjustments to prevent backtest overfitting.
   * **Bailey, D. H., Borwein, J., López de Prado, M., & Zhu, Q. V. (2014).** "Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance." *Notices of the AMS*, 61(5), 458–471.  
     **DOI:** [10.1090/noti1105](https://doi.org/10.1090/noti1105)

---

## 3. Detailed Reasons for HIGH Novelty Risk

### Reason 1: The Primary Theoretical Target (RQ2) Has Just Been Subsumed
The authors hoped that deriving fixed-$b$ or bootstrap-calibrated simultaneous max-$t$ confidence bands for multiple dependent comparisons would serve as the theoretical anchor. However:
* **Chen, Galvao, Rho, Vogelsang, & Yoon (September 2026, arXiv:2609.05883)** already solved the fixed-smoothing Sup-$t$ uniform confidence band problem under serial dependence, explicitly handling the non-pivotal nature of the multi-parameter max-$t$ statistic via long-run covariance simulation.
* Combining Chen et al. (2026) with standard delta-method influence functions for ratios (Ledoit & Wolf, 2008) is an **incremental, straightforward application**, not a novel methodological breakthrough.

### Reason 2: The Practical Findings in the Simulation ("Phase D") Merely Replicate Known Theorems
The novelty report candidly notes that their simulation findings (e.g., standard HAC requires large bandwidths like LLSW, naive block bootstrap under-covers because its limit is fixed-$b$, bootstrap-$t$ performs better, strong persistence breaks all rules) match existing literature:
* Bartlett undercoverage at small $S$: Predicted by LLSW (2018) and Sun (2014).
* Bootstrap-$t$ outperforming naive bootstrap: Proven by Gonçalves & Vogelsang (2011).
* Failure under 10-day persistence: Proven by Müller (2014).
Presenting these known behaviors as new empirical phenomena in a paper will draw immediate, harsh pushback from knowledgeable reviewers.

### Reason 3: Procedural and Pipeline Innovations (RQ1, RQ3, RQ4) Cannot Carry a Methodology Paper
* **RQ1 (Decomposing Undercoverage Sources):** Running numerical simulations to see which source accounts for what percentage of coverage drop in a specific A-share setup is an empirical sensitivity analysis, not a statistical discovery.
* **RQ3 ("Pre-registered Simulation Hurdle"):** Framing good Monte Carlo simulation practice (Morris et al., 2019; Siepe et al., 2024) as a "novel methodological procedure" confuses scientific rigor/software hygiene with statistical methodology. In statistics and ML venues, a simulation check is an evaluation tool, not a standalone contribution.
* **RQ4 (A-share Case Study):** A standard empirical finance application.

---

## 4. Strategic Recommendations for Repositioning

If the team proceeds with this research thread, they should **abandon the attempt to brand it as a primary theoretical/methodological breakthrough** in statistical inference. Instead, consider the following pivots:

1. **Reposition as an Applied / Stress-Testing Paper for Quantitative Finance:**
   * **Target Venues:** *Journal of Financial Econometrics*, *Journal of Financial Data Science*, *Quantitative Finance*, or *Journal of Empirical Finance*.
   * **Framing:** Frame the work not as inventing a new confidence interval, but as an **authoritative empirical audit and benchmarking suite for machine learning backtesting**. 
   * **Value Proposition:** Demonstrate that widely used industry backtesting intervals (e.g., in Python/R quant libraries) fail systematically in ML pipelines, quantify the breakdown points across realistic holding periods and refitting cadences, and provide practitioners with a plug-and-play, calibrated toolkit (synthesizing Ledoit-Wolf, LLSW, and Chen et al.).

2. **Discard or Subordinate RQ3 as "Method":**
   * Do not write "our contribution is a pre-registered simulation hurdle." Frame it as the **validation protocol** supporting the benchmark.

3. **Must-Include Baseline Suite:**
   Any credible revision must benchmark directly against:
   * **Ledoit & Wolf (2008/2020)** studentized circular block bootstrap.
   * **LLSW (2018)** fixed-$b$ / EWC corrections with Bonferroni and max-$t$.
   * **Chen et al. (2026)** simulated Sup-$t$ fixed-smoothing critical values.
   * **Romano & Wolf (2005)** StepM single-step simultaneous intervals.
   * **Müller (2014)** low-frequency projection for persistent components.

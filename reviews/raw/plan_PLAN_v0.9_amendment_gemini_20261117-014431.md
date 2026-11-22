# Skeptical Review of Experiment Plan Amendment v0.9

This review evaluates [PLAN_v0.9_amendment.md](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md) from the perspective of an independent, skeptical reviewer. While the amendment correctly diagnoses severe empirical failures from the pilot round (e.g., threshold gate degeneracy, stratification dilution, loss of candidate-set RankIC in 2021), the proposed revisions introduce severe inferential contradictions, compound baseline asymmetries, and finalize a near-total disconnect between the theoretical framework and the empirical pipeline.

---

## 1. Executive Summary & Assessment of Core Questions

### Are the baselines strong and fairly tuned?
* **Strength:** **SCORE** (taking top $\lceil cK \rceil$ by base predictor score) is a strong, necessary, and competitive baseline. In the pilot, it beat the learned gate `LOSS(-Z)` by 6.07 bp on LightGBM.
* **Fairness:** **No.** Tuning fairness is severely compromised:
  1. **Data-Age Asymmetry:** In [§A2.1](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L47-L57), fixed-count gates are trained on base out-of-sample data only through year $Y-2$, whereas the base predictor powering `SCORE` uses data through $Y-1$. The $Y-2$ restriction was originally introduced in [PLAN.md §4.3](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN.md) to hold out $Y-1$ for probability threshold calibration. Now that threshold calibration is abolished, retaining a $Y-2$ training cutoff arbitrarily penalizes learned gates with 1-year stale training data.
  2. **Surrogate Objective Mismatch:** Fixed-count gates (`LOSS`) are trained to minimize binary classification log-loss on $L^{(1)} \in \{0, 1\}$, but are evaluated and tuned on mean net return $V^g$ ([§A2.2](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L58-L64)). A classifier penalized solely for 0/1 accuracy can actively discard high-alpha trades with moderate loss risk or retain low-return trades with low loss risk. The regression gate `NET-K` directly optimizes the economic objective, yet it is excluded from the primary confirmatory family.
  3. **Equal Iteration Budget $\neq$ Equal Search Coverage:** An identical budget of $T=30$ random search iterations is assigned across vastly disparate model spaces (Ridge vs. LightGBM) and feature dimensionalities ($-Z$ vs. $+Z_H$ vs. $+Z_O$).

### Are the metrics appropriate?
* **Partially appropriate for order execution, but fundamentally flawed for statistical inference and risk assessment:**
  1. **The Equivalence Testing Paradox:** Concluding that an effect is "economically negligible" requires the simultaneous 95% confidence interval $[L, U]$ to fall entirely within $[-\Delta, \Delta]$ with $\Delta = 4.96\text{ bp}$ ([§A4.1](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L94-L122)). With a pilot standard error of $3.0\text{–}3.8\text{ bp}$, a studentized simultaneous 95% interval has a half-width of $\sim 7.5\text{–}9.5\text{ bp}$ (total width $15\text{–}19\text{ bp}$). It is **mathematically impossible** for an interval of width $\ge 15\text{ bp}$ to fall inside a target window of width $9.92\text{ bp}$, even if the true and estimated effect is exactly zero. The classification rule guarantees an "inconclusive" verdict for any null effect.
  2. **Disappearance of Downside Risk Metrics:** The primary research question in [research_question.md v4](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/00_idea/research_question.md#L93-L146) was whether abstention reduces loss probability and tail risk. The primary estimand $V^g$ ([§A3.1](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L68-L76)) is strictly an average net return per submitted order. Win rate, tail risk (CVaR), and drawdown are completely omitted from the confirmatory family.
  3. **Unfilled Order Penalty ($\rho = 0$):** In $V^g$, unfilled orders are treated as $\rho = 0$. While operationally realistic, this confounds selection quality with execution friction: an alpha signal that picks volatile stocks hitting price limits or liquidity caps is heavily penalized by cash drag rather than assessed on prediction accuracy.

### Do the experiments actually test the stated theorems and claims?
* **No. There is an almost complete operational disconnect between the theory files and Amendment v0.9:**
  1. [Theorem 1 and Corollaries 1.1–1.3](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/theorems.md#L44-L150) define time-uniform, sequential confidence bounds for monitoring the conditional entry-time loss probability $r_T^{\text{entry}}$ under delayed feedback. Primary contrasts P1–P3 test fixed-horizon average net returns $V^g$. Theorem 1 is not tested, validated, or utilized in P1–P3.
  2. [Proposition 2](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/theorems.md#L19) establishes minimax lower bounds for honest intervals; it is never compared against empirical results.
  3. [Lemma 3](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/theorems.md#L20) provides an additive portfolio attribution for deployed strategies ($\Delta\text{AR}$). In v0.9, deployed strategies are relegated to descriptive secondary analyses ([§A3.3](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L83-L87)).
  4. The proposed "accounting identity" $\theta_{\text{uns}} = \theta_{\text{sel}} + A^g$ ([§A3.2](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L77-L82)) is an algebraic tautology, not an empirical test of economic behavior.
  5. The foundational motivation—game-theoretic poker reasoning regarding private information—is explicitly disclaimed as rhetoric ([PLAN.md §1](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN.md#L97-L100)).

---

## 2. Issues Ranked by Severity

### Critical Severity (Fatal Flaws / Blinding Compromised)

#### Issue 1: The Equivalence Power Paradox Guarantees Inconclusive Results
* **Analysis:** [§A4.1](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L94-L122) eliminates Two One-Sided Tests (TOST) because "pilot SE of P1 (about 3 bp) leaves an equivalence test at 4.96 bp without power." To replace it, the author requires that the simultaneous 95% block-bootstrap interval $[L, U]$ satisfy $-\Delta < L$ and $U < \Delta$.
* **The Flaw:** This is statistically backwards. A simultaneous 95% confidence interval over 4 to 6 contrasts has a critical multiplier $z^* \approx 2.5\text{–}2.8$. At $\text{SE} \approx 3.0\text{–}3.8\text{ bp}$, the confidence interval half-width is:
  $$\text{Half-width} = z^* \times \text{SE} \ge 2.5 \times 3.0\text{ bp} = 7.5\text{ bp} > 4.96\text{ bp}$$
  Because the half-width exceeds $\Delta$, the total interval width is at least $15\text{ bp}$. It is **algebraically impossible** for $[L, U]$ to fall inside $[-4.96, +4.96]\text{ bp}$. Thus, if the true effect of a gate is zero, the probability of concluding "negligible" is **exactly 0%**. The procedure guarantees that any true null effect will be labeled "inconclusive".
* **Remediation:** Either:
  1. Retain an explicit pre-specified TOST at an unadjusted 90% level ($z_{0.05} = 1.645$) alongside simultaneous intervals, acknowledging the power constraint; or
  2. Economically re-anchor $\Delta$ to a realistic bound where the study has defined power ($\ge 80\%$), derived from `precision_v9` ([§A6](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L143-L168)).

#### Issue 2: Confirmatory Integrity Compromised by Peeking and Convenience Universe
* **Analysis:** [§A8](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L180-L215) confirms that the confirmatory population is the pilot list of 1,000 stocks (screened to the top 300 by liquidity), and development data (2017–2021) has already been thoroughly examined across three pilot rounds.
* **The Flaw:**
  - Every modification in v0.9 (switching from thresholding to fixed-count, dropping cell stratification, introducing SCORE as primary benchmark, changing the tuning metric to $V^g$) was designed after observing pilot outcomes on these exact 1,000 stocks.
  - The universe is an SSE-heavy convenience sample (898 SSE vs. 38 SZSE, 45 ChiNext, 19 STAR). Main board SSE names have different trading limits, listing rules, and liquidity profiles than the broader A-share market.
  - Re-tuning base predictors and gates on this exact data ([§A7](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L170-L179)) introduces pre-test bias. The unopened hold-out (2022–2026) is the sole remaining defense against total data-snooping, but its base predictor RankIC already showed severe decay in 2021 (dropping to 0.03).
* **Remediation:** The manuscript must explicitly disclose that the hypothesis, primary contrasts, and model architecture were informed by the development data of this specific convenience cohort. Preregister the hold-out analysis protocol with an immutable SHA-256 hash before touching the 2022–2026 data.

#### Issue 3: Complete Theorem-to-Experiment Disconnect
* **Analysis:** The mathematical theory in [theory/theorems.md](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/theorems.md) focuses on:
  - Time-uniform martingale concentration for delayed labels ($r_T^{\text{entry}}$ bounds in Theorem 1).
  - Effective sample size reductions due to daily batching and delay (Proposition 2).
  - Certified liquidation bounds under missing data (Corollary 1.3).
* **The Flaw:** None of the primary empirical hypotheses (P1, P2, P3 in [§A4.1](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L94-L122)) test any implication of these theorems. P1–P3 test the static cross-sectional ranking ability of LightGBM/Ridge models on net return. Theorem 1 is relegated to a passive descriptive appendix script running on synthetic fills ([PLAN.md §9.4](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN.md#L1043-L1072)).
* **Remediation:** Provide an explicit mapping table:
  - If Theorem 1 is a core contribution, include dedicated synthetic and semi-empirical experiments testing interval coverage under optional stopping, adversarial delay patterns, and correlated arrivals.
  - If Theorem 1 is merely an ancillary monitoring tool, explicitly reposition the paper as an empirical asset pricing / selective prediction paper and demote the theorem to an appendix note.

---

### High Severity (Methodological & Baseline Threats)

#### Issue 4: Artificial 1-Year Stale Training Disadvantage for Fixed-Count Gates
* **Analysis:** In [PLAN.md §4.3](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN.md), gate models were trained on out-of-sample base predictions through year $Y-2$, because year $Y-1$ was required to calibrate the threshold $\tau$.
* **The Flaw:** In [§A2.1](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L47-L57), the threshold rule is abolished for fixed-count gates: "No threshold is calibrated; the gate model is fitted exactly as in §4.3, with unchanged fitting windows (deployment year Y: fitted on base out-of-sample rows through Y−2)."
  Meanwhile, the base predictor generating the `SCORE` baseline is retrained annually using data up to $Y-1$. Consequently, `LOSS(-Z)` is making predictions using a model trained on data that is one year older than the model used by `SCORE`. In financial time-series with concept drift, this gives `SCORE` an unearned competitive advantage.
* **Remediation:** Train fixed-count gates on all legally available out-of-sample base predictions up to $Y-1$ (with appropriate purging/embargoing of length $H+1$), eliminating the obsolete 1-year calibration lag.

#### Issue 5: Exclusion of NET-K from Primary Contrasts Confounds the Research Claim
* **Analysis:** `LOSS(-Z)` trains a LightGBM classifier on binary loss labels $L^{(1)} \in \{0, 1\}$. `SCORE` ranks stocks by expected return from the base model. `NET-K` trains a LightGBM regressor directly on net return $\rho$.
* **The Flaw:** P1 compares `LOSS(-Z)` against `SCORE`. If P1 fails (as it did in the pilot by $-6.07\text{ bp}$), the author cannot determine whether:
  1. Learned selection adds no value over the base score; or
  2. Optimizing a 0/1 binary classification loss is misaligned with maximizing expected net return (e.g., pruning trades with a 51% loss probability that have massive right-tail upside).
  `NET-K` directly solves the objective mismatch. Relegating `NET-K` to secondary analysis ([§A4.3](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L123-L141)) prevents the paper from answering whether a learned model can beat `SCORE`.
* **Remediation:** Elevate `NET-K` into the primary family or co-primary contrast:
  $$\delta(\text{NET-K}(-Z), \text{SCORE})$$

#### Issue 6: Omission of Risk & Loss Mitigation Metrics from Primary Inference
* **Analysis:** The founding premise of the project ([research_question.md](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/00_idea/research_question.md#L12-L25)) was selective abstention to control downside risk ("folding bad hands").
* **The Flaw:** In Amendment v0.9, the primary estimands are purely return differences $\delta(g, h)$ on submitted orders. If a gate successfully lowers the trade loss rate from 55% to 45% and cuts max drawdown in half, but yields a neutral net return ($\delta \approx 0$), P1 will classify it as "negligible" or "inconclusive". The primary evaluation completely ignores the primary stated mechanism.
* **Remediation:** Define a joint primary or co-primary risk estimand:
  - Trade-level loss frequency difference $\Delta \text{LossRate} = \mathbb{P}(\text{Loss} \mid \text{Submit}_g) - \mathbb{P}(\text{Loss} \mid \text{Submit}_h)$;
  - Tail risk difference (Expected Shortfall of trade returns at 5% level).

#### Issue 7: Unvalidated Studentized Maximum Bootstrap Multiplicity Correction
* **Analysis:** [§A4.1](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L94-L122) adopts a simultaneous 95% confidence interval via the maximum absolute studentized statistic across the 6 primary contrasts. The text itself notes this procedure is `PLACEHOLDER` and `UNVERIFIED`.
* **The Flaw:** Studentized block bootstrapping on dependent financial ratio statistics with heavy tails and cross-strategy correlation can suffer from severe variance-estimation instability in the denominator. If the bootstrap variance estimate in the studentization is noisy, studentized bootstrap intervals have notorious undercoverage. Furthermore, fallback to Bonferroni percentile intervals does not solve coverage distortions if the underlying block bootstrap violates weak stationarity across regime breaks (such as the 2020–2021 volatility shifts).
* **Remediation:** Pre-freeze the exact studentization formula and variance estimator. In `precision_v9` ([§A6](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L143-L168)), establish strict synthetic simulation benchmarks (DGP with known covariance and student-t tails) proving empirical family-wise coverage $\ge 95\%$ before approving the hold-out run.

---

### Medium Severity (Experimental Specification & Feature Validity)

#### Issue 8: Unconditional Feature Permutation Breaks Covariance Structure
* **Analysis:** [§A4.3 item 6](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L129-L134) evaluates the information content of $Z_H$ and $Z_O$ using 20 permutation draws per seed, shuffling $Z$ columns unconditionally across nominated stocks within each day.
* **The Flaw:** Unconditional permutation destroys the correlation between $Z$ (e.g., turnover, block trade volume) and baseline control variables $R$ (e.g., standard turnover, market cap, volatility). When a tree model splits on a permuted feature that breaks natural collinearity, it can degrade tree structure and artificially harm performance. A drop in performance from real $Z$ to permuted $Z$ does not prove that $Z$ contains private/holder information; it may merely prove that permuting $Z$ created out-of-distribution feature combinations.
* **Remediation:** Implement a capacity-matched noise control (adding pure independent Gaussian/uniform noise features) and, if testing incremental information, use conditional permutation or residualized feature shuffling.

#### Issue 9: Event-Conditional Estimand for Sparse $Z_O$ Lacks Common Denominator
* **Analysis:** [§A4.3 item 7](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L135-L141) specifies an event-conditional analysis for $Z_O$ restricted to days with at least 3 nominations having usable events.
* **The Flaw:** Conditioning on days with $\ge 3$ event nominations alters the denominator $\sum_t S_t$ and changes the sample composition. Restricting subsets across policies breaks the paired-difference structure of $V^g - V^h$.
* **Remediation:** Decompose the full-sample policy value contrast additively into event-active and event-inactive contributions over a common denominator:
  $$\delta = \frac{\sum_{t, i \in \text{Event}} (\mathbb{I}_i^{+Z} - \mathbb{I}_i^{-Z})\rho_{ti}}{\sum_t S_t} + \frac{\sum_{t, i \notin \text{Event}} (\mathbb{I}_i^{+Z} - \mathbb{I}_i^{-Z})\rho_{ti}}{\sum_t S_t}$$

#### Issue 10: Point-in-Time Vulnerability of Insider Share Changes (INS)
* **Analysis:** In [PLAN.md §5.6.1](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN.md#L800-L808), the audit revealed that 41.2% of retained INS rows were back-filled, and announcement timestamps cannot be validated from free data.
* **The Flaw:** Rolling non-trading day announcements forward by 2 trading days is a heuristic, not a point-in-time proof. If a transaction date was entered as an announcement date in the upstream scraped table, information leakage into $Z_O$ is guaranteed.
* **Remediation:** Make passing audit item OA10 mandatory before Freeze-1. If announcement dates cannot be externally audited against primary exchange disclosure feeds, exclude the INS class from the primary $Z_O$ feature set and retain it only as an unverified sensitivity check.

#### Issue 11: Rigid Single Operating Point ($c = 0.5, K = 30$)
* **Analysis:** The plan freezes coverage strictly at $c = 0.5$ (abstaining on exactly 50% of names) and $K = 30$.
* **The Flaw:** Selective prediction performance is rarely monotonic or uniform across coverage levels. A gate might provide exceptional risk reduction at $c = 0.8$ (filtering the worst 20% toxic trades) or $c = 0.2$ (concentrating on top conviction), but fail at an arbitrary $c = 0.5$. Freezing a single cutoff prevents discovery of the risk-coverage Pareto frontier.
* **Remediation:** Pre-specify a deterministic secondary sweep across $c \in \{0.3, 0.5, 0.7, 0.9\}$ to map the empirical coverage-return and coverage-risk curves.

---

## 3. Prioritized Checklist of Missing Experiments

Before `PLAN_v0.9_amendment.md` is approved and the hold-out is opened, the following experiments must be added:

| Priority | Missing Experiment | Purpose |
|---|---|---|
| **P0 (Mandatory)** | **Synthetic DGP Validation for Theorem 1 & Prop 2** | Simulate trade streams with known conditional loss probabilities $\mu_t$, synthetic delays $d$, and cross-asset correlations. Verify empirical coverage of Theorem 1 intervals under optional stopping and check tightness against Proposition 2 bounds. |
| **P0 (Mandatory)** | **Precision Simulation with Realistic Class Distributions** | Run `precision_v9` ([§A6](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/PLAN_v0.9_amendment.md#L143-L168)) specifically measuring the probability of the "negligible" classification under true effects $\delta \in \{0, \pm 2, \pm 4.96\}\text{ bp}$ given studentized simultaneous intervals. Prove that the test has $>0\%$ power to declare equivalence. |
| **P1 (High)** | **Objective-Aligned Baseline Contrast: NET-K vs. SCORE** | Evaluate whether direct expected return regression on top-$K$ nominations beats the base score ranking, isolating model architecture value from surrogate loss function mismatch. |
| **P1 (High)** | **Training Data Recency Sensitivity ($Y-1$ vs. $Y-2$)** | Retrain fixed-count gates on base out-of-sample data up to $Y-1$ on development data to quantify the exact performance penalty imposed by the obsolete $Y-2$ calibration holdout. |
| **P1 (High)** | **Downside Risk & Loss Frequency Contrasts** | Evaluate paired differences in trade loss rate ($\Delta \text{LossRate}$), CVaR(5%), and Maximum Drawdown between `LOSS(-Z)`, `SCORE`, and `G0`. |
| **P2 (Medium)** | **Coverage Sensitivity Grid ($c \in \{0.3, 0.5, 0.7, 0.9\}$)** | Map the empirical risk-coverage frontier to determine whether abstention value is concentrated in extreme tail truncation rather than median splits. |
| **P2 (Medium)** | **Formal Timestamp & Point-in-Time Audit (OA10 / Chronology)** | Execute line-by-line audit of base score out-of-sample indexing and third-party verification of INS disclosure announcement timestamps prior to freezing code hashes. |

---

## 4. Final Recommendation

**Verdict: Reject in present form; require targeted revisions before freeze.**

Amendment v0.9 makes commendable progress by adopting count-matched contrasts against `SCORE` and transparently acknowledging the exploratory nature of the pilot findings. However, it cannot be approved as written because:
1. The simultaneous interval classification rule creates a mathematical impossibility for demonstrating economic negligibility at current sample sizes.
2. The core theoretical theorems remain decorative, with no empirical validation or connection to the primary contrasts.
3. The learned gates are unfairly disadvantaged against `SCORE` by a 1-year stale training cutoff and an unaligned classification surrogate loss.

Addressing the P0 and P1 items listed above will restore methodological rigor, align the empirical tests with the research questions, and protect the project from an uninterpretable hold-out failure.

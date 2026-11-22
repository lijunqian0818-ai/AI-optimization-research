# Skeptical Review of Experiment Plan Amendment v0.9.2 (Part 3: §A6–§A11)

---

## Executive Summary

This amendment reflects an admirable degree of technical transparency—the authors candidly document pilot failures, statistical limitations, and the post-hoc origins of their revisions. However, from the perspective of an independent, skeptical scientific reviewer, **this experiment plan formalizes a methodological dead-end**. 

The plan is caught in a profound contradiction: while attempting to maintain the outward apparatus of rigorous confirmatory hypothesis testing (simultaneous intervals, economic bounds $\pm\Delta$, family-wise error control), the authors explicitly acknowledge that **the primary contrasts are almost mathematically guaranteed to return "inconclusive at $\pm\Delta$"**, that **the theoretical theorems in `theory/theorems.md` are not tested by any primary experiment**, and that **the baseline is tuned on an objective different from the one it is judged on**.

Below is a detailed evaluation answering each of your specific questions, followed by a ranked severity hierarchy of the issues identified.

---

## 1. Are the Baselines Strong and Fairly Tuned?

**No. The baselines are structurally handicapped, tuned on mismatched objectives, and arbitrarily restricted in feature access.**

### A. Asymmetric Tuning Objectives (Straw-Manning the Baseline)
* **The Discrepancy (§A7):** The base predictor (`SCORE`) is tuned strictly on **RankIC** of within-day return ranks across the candidate set. In contrast, the gating models (`LOSS`, `NET-K`) are hyperparameter-tuned directly on **$V$ (mean net standard-order return per submitted order)**, which is the exact endpoint used to evaluate the primary contrasts $P1$ and $P4$.
* **The Confound:** A ranking model optimized for cross-sectional RankIC optimizes linear correlation across all $K$ candidates; it is not optimized to ensure that the top $\lceil cK \rceil$ orders maximize net post-cost return. When `LOSS` or `NET-K` beats `SCORE`, one cannot distinguish between:
  1. A structural architectural benefit of a two-stage "nomination + abstention" system.
  2. The trivial artifact that the gate was tuned on the test metric ($V$) while the base was tuned on an auxiliary proxy (RankIC).
* **The "Narrowed Claim" Evasion (§A7, §A10):** The authors attempt to sidestep this by claiming $P1$ and $P4$ only ask: *"Can a gate improve on **this** base, tuned as specified since v0.8?"* rather than *"Is gating better than an end-to-end model?"* In an empirical study, this answers an uninteresting, artificial question. Why would a practitioner deploy a two-stage gating architecture to fix a RankIC-tuned base instead of simply tuning the base ranker directly on top-$K$ net return? The proposal to tune a base model on $V$ was explicitly rejected in §A10 on the procedural ground that it was a "new design element after outcomes were seen." While procedurally defensible against p-hacking, it leaves the baseline fundamentally uncompetitive.

### B. Feature Asymmetry (Withholding $Z$ from the Baseline)
* In §A4.1 and §A10, contrasts $P2$ and $P3$ test adding proprietary/event features ($Z_H$ and $Z_O^*$) to the *gate*. However, the authors rejected adding a matched-budget `Base(+Z)` baseline.
* If $Z$ contains genuine predictive information, withholding $Z$ from the base predictor forces the base to make suboptimal nominations. A downstream gate utilizing $Z$ might simply be rescuing the strategy using alpha signals that should have been in the base ranker from the start.

### C. Frozen, Degraded Base Performance
* In §A7, the authors note that the base predictor's candidate-set RankIC collapsed in 2021 (from 0.09–0.14 down to 0.03–0.04), and the nomination-minus-candidate return spread fell to approximately zero.
* Yet, the authors state: *"The feature set B0 + R is not changed. No feature search is opened in response to the 2021 decline."* Freezing a known-degraded base predictor risks feeding noise into the gates during the 2022–2026 holdout. If the base nominations are near-random, gating on noise produces uninterpretable results.

---

## 2. Are the Metrics Appropriate?

**Partially appropriate in statistical rigor, but structurally mismatched with the study's power and economic goals.**

### A. The "All Inconclusive" Trap ($\Delta = 4.96\text{ bp}$ vs. Power)
* **Mathematical Impossibility of "Negligible" (§A4.1, §A6, §A10 D4):** The economic bound is fixed at $\Delta = 4.96\text{ bp}$ per order (derived from $\Delta_{\text{cap}} = 1\%$ annual return on capital). However, the pilot standard errors for $P1$ and $P4$ are $3.0\text{--}3.8\text{ bp}$. With a simultaneous 95% critical value $q \ge 1.96$ (typically $2.5\text{--}2.7$), the interval half-width is **at least $5.9\text{--}10.4\text{ bp}$**.
* Because the half-width ($> 5.9\text{ bp}$) is strictly larger than $\Delta$ ($4.96\text{ bp}$), the confidence interval can **never** fit within $[-\Delta, \Delta]$. **The probability of classifying $P1$ or $P4$ as "negligible" is identically zero**, even if the true difference is exactly zero.
* **Unreachable "Material Benefit":** Detecting a "material benefit" ($L > \Delta$) requires an empirical point estimate exceeding $+10.8\text{ to }+15.3\text{ bp}$. Yet exploratory pilot estimates ranged from $-6.1\text{ to }+1.7\text{ bp}$.
* **The Verdict:** The classification framework is hollow. The authors admit in §A0 and §A10 (D7) that the expected outcome is that **all eight primary contrasts will be labeled "inconclusive at $\pm\Delta$."** Relabeling this as an "estimation study" does not cure the fact that the pre-specified classification decision rule is statistically paralyzed.

### B. Metric Misalignment with Abstention's Core Purpose
* The foundational premise of an abstention gate (especially `LOSS`, trained on a binary 0/1 loss label) is risk reduction: **to lose less often and protect against left-tail catastrophes**.
* However, the primary metric is strictly $V$ (mean net return per submitted order). A gate could significantly reduce drawdowns and cut loss frequency, but if its mean net return remains flat or slightly negative due to lost upside in bull regimes, the primary metric classifies it as "inconclusive" or "harmful."
* Demoting loss frequency and tail loss to unadjusted, secondary exploratory metrics (§A4.3 item 0, §A10 D5) severs the primary evaluation from the mechanism's primary raison d'être.

### C. Ratio Estimator and Denominator Instability
* $V^g = \sum_t \sum_{i} \rho_{ti} / \sum_t S_t^g$ is a pooled ratio estimator across days and seeds. In §A6, the synthetic validation acknowledges varying daily counts and ratio forms.
* However, in market regimes with heavy trading suspensions or limit-up/limit-down events, $S_t^g$ varies substantially. Ratio estimators with time-varying denominators are sensitive to temporal clustering, where high-activity days exert outsized leverage on the overall point estimate.

---

## 3. Do the Experiments Actually Test the Stated Theorems and Claims?

**No. There is a complete decoupling between the theory files and the empirical experiment plan.**

* **Explicit Disconnection (§A11):** §A11 opens with the stark admission:
  > *"No primary contrast, key secondary or classification of this amendment uses a result of `theory/theorems.md`. P1–P4 are comparisons of fitted selection policies by mean net return with bootstrap inference; they neither test nor rely on Theorem 1, its corollaries, Proposition 2 or Lemma 3."*
* **Theorem 1 is Operationally Useless:** Theorem 1 provides a time-uniform confidence sequence for the entry loss rate under delayed feedback. But in the pilot, this honest interval had an empirical width of **$\pm 0.17$** (§A11). An uncertainty band spanning 34 percentage points on a bounded probability metric $[0, 1]$ is far too loose for real-time risk gating. As a result, the authors demote Theorem 1 to an inert "monitoring tool" that dictates no actions.
* **Proposition 2 & Lemma 3:** Proposition 2 has no empirical test whatsoever ("stated as theory only"). Lemma 3 is merely an accounting/ledger identity decomposing returns into exposure, composition, and cost, not an empirical test of a causal hypothesis.
* **Draft Status of Identity:** The identity $\theta_{\text{uns}} = \theta_{\text{sel}} + A$ (§A3.2) is still noted as a draft (`草稿`), with the algebraic proof yet to be completed.
* **Summary:** The paper presents two entirely separate intellectual tracks: a theoretical track proving generic martingale-based confidence bounds under delay, and an empirical backtest of machine-learning abstention gates. Neither informs or validates the other.

---

## 4. What Experiments Are Missing?

To transform this plan into a rigorous, scientifically informative study, several critical experiments are missing:

1. **End-to-End Base Tuned on Net Value / Top-K ($V$):**
   * A baseline where the base predictor is tuned directly on top-$\lceil cK \rceil$ net return or loss avoidance (e.g., using pairwise/listwise ranking objectives like LambdaMART or top-tier weighted MSE) with the same compute budget. Without this, one cannot assert that gating is superior to proper objective alignment in the primary ranker.
2. **Feature-Matched Baseline (`Base(+Z)`):**
   * A primary experiment testing whether feeding $Z_H$ and $Z_O^*$ directly into the base predictor eliminates the need for an abstention gate. If `Base(+Z)` achieves equal or superior $V$ to `Base(-Z) + Gate(+Z)`, the gating architecture is redundant.
3. **Generalization Across a Representative Market Universe:**
   * In §A8.1, the authors admit that the universe is an arbitrary **convenience sample**: 889 names were fetched in *stock code order* (resulting in 898 Shanghai Main Board stocks and only 45 ChiNext and 19 STAR stocks). 
   * Experiments on a representative universe (e.g., the CSI 300, CSI 500, or a stratified liquid cross-section across both Shanghai and Shenzhen exchanges) are entirely missing.
4. **Base Predictor Failure Diagnostic / Regime Ablation:**
   * Given the collapse of base RankIC in 2021, an experiment evaluating gate performance under simulated base degradation (e.g., adding progressive noise to base scores) is missing. Can gates actually rescue a dying base model, or do they collapse with it?
5. **Simple Heuristic Abstention Ablations:**
   * Testing complex learned gates (`LOSS`, `NET-K`) against trivial rule-based heuristics (e.g., abstaining from names with extreme 5-day realized volatility, names near earnings announcements, or high bid-ask spread) without machine learning.
6. **Execution Slippage & Market Impact Sensitivity:**
   * The cost model is fixed ($c = 0.5$, synthetic fills). Sensitivity checks varying transaction costs, slippage under market impact, and limit-order queue dynamics across liquidity tiers are missing.

---

## 5. Ranking Issues by Severity

### Severity 1: Critical Flaws (Threatens Scientific Validity & Core Value)

1. **Structurally Underpowered Hypotheses & The "Guaranteed Inconclusive" Illusion (§A0, §A4.1, §A6, §A10 D4/D7):**
   * The economic bound $\Delta = 4.96\text{ bp}$ is irreconcilable with the pilot sampling error ($SE \approx 3.0\text{--}3.8\text{ bp}$). Because the simultaneous confidence interval width exceeds $2\Delta$, the outcome "negligible" cannot occur, and detecting "beneficial" requires an effect 6 to 10 times larger than anything observed. Running an elaborate multi-year confirmatory freeze whose pre-calculated primary verdict is guaranteed to be "inconclusive" renders the confirmatory testing machinery theatrical rather than scientific.
2. **Complete Schism Between Theory and Empirical Experiments (§A11):**
   * No empirical contrast tests, validates, or relies on the theoretical theorems (`theory/theorems.md`). Theorem 1 produces bounds too loose ($\pm 17\%$) for operational use. The paper packages unvalidated theory alongside empirical experiments that ignore it.
3. **Unfair Baseline Calibration via Mismatched Optimization Objectives (§A7, §A10):**
   * Gating models are tuned directly on the test metric ($V$), whereas the base model baseline is tuned on RankIC. Concurrently, $Z$ features are withheld from the base model. This creates an unlevel playing field that confounds architectural claims with simple objective alignment and feature withholding.

### Severity 2: High Severity (Methodological Weaknesses & External Validity Risks)

4. **Severely Biased Convenience Population (§A8.1):**
   * The universe was assembled by fetching stock codes sequentially, resulting in 89.8% Shanghai Main Board names (traditional SOEs, cyclicals, banking) and virtually no Shenzhen growth/tech representation. Conclusions will apply only to an arbitrary, unrepresentative list of 300 stocks, not the A-share market.
5. **Demotion of Downside Risk Metrics from the Primary Family (§A4.3 item 0, §A10 D5):**
   * The primary family evaluates only mean return ($V$). Abstention is fundamentally a tail-risk and loss-frequency management tool. Relegating loss frequency, worst-5% tail returns, and drawdown to unadjusted exploratory secondary metrics misaligns the confirmatory evaluation with the core problem statement.
6. **Extensive Post-Hoc Adaptations on Seen Data (§A8.2, §A10):**
   * The transition from threshold gates to fixed-count gates, the exclusion of the `INS` feature group, the shift to Y−1 training windows, and the definition of primary contrasts P1–P4 were all chosen after inspecting exploratory rounds 1, 2, and post-hoc data on the 2017–2021 period. The unopened 2022–2026 holdout is the sole remaining barrier against massive historical overfitting.

### Severity 3: Medium Severity (Technical & Implementation Vulnerabilities)

7. **Narrowed Target of Inference in `precision_v9` (§A6):**
   * In the synthetic check, the "truth" is defined as the realized time-average of the generated path in that replication, rather than the unconditional mean of the data-generating process. This artificially inflates coverage statistics under regime shifts and reduces the inference's applicability to future out-of-sample periods.
8. **Critical Parameters Remain Unfrozen Placeholders (§A6, §A10):**
   * Several pivotal parameters—such as simulation replication counts (5,000), pass criteria (94.0% coverage, 5% FWER, 1% wrong-direction, 2.5% negligible error), and the 5-day event window—are still marked `PLACEHOLDER`. Leaving these unfrozen allows potential researcher degrees of freedom prior to opening the holdout.
9. **Unaddressed Base Collapse in Holdout Regime (§A7):**
   * The base model's RankIC collapsed to near zero in 2021. If this structural break persisted into the 2022–2026 holdout, the entire confirmatory pipeline will be evaluating gates applied to uninformative nominations.

---

## Recommendation

If this plan is to be approved, the authors must abandon the pretense that this is a confirmatory hypothesis test of theoretical bounds. Instead:
1. Formally drop the binary classification verdicts ($\pm\Delta$) and present the work purely as an **empirical estimation and error-budgeting study**.
2. Either integrate a **$V$-tuned base ranker** and a **`Base(+Z)` baseline**, or explicitly constrain the title and abstract to state that the paper investigates *post-hoc re-ranking of suboptimal RankIC-tuned models under restricted feature sets*.
3. Explicitly state in the introduction that the **theorems provide conceptual bounds rather than empirical decision rules**, preventing reviewers from expecting an empirical validation of Theorem 1.

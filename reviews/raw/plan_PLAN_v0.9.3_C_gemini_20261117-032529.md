# Skeptical Review: Experiment Plan Amendment (PLAN_v0.9.3 Part 5: §§A8–A11)

> **Review Scope & Context**: This review evaluates **Part 5 (§§A8–A11)** of the plan amendment on its own merits. Where references point to earlier sections (§§A0–A7, §12, §13, §18), these are noted as **"not visible in this part"** while evaluating the explicit downstream decisions, assumptions, and constraints documented in §§A8–A11.

---

## Executive Summary

As a skeptical reviewer, this document presents several **fatal methodological vulnerabilities, severe statistical limitations, and an almost complete decoupling between the stated theoretical contributions and the empirical design**. 

While the authors deserve credit for intellectual honesty regarding pilot data leakage (§A8.2), known underpowering (D4, D7), and acknowledging convenience sampling limitations (§A8.1), acknowledging a methodological flaw does not neutralize its scientific damage. The plan effectively pre-programs an inconclusive confirmatory experiment on a non-representative equity universe, evaluates a downside-risk abstention mechanism purely on mean return, and concedes that its primary experimental contrasts neither test nor rely on any of the theoretical theorems developed in the project.

---

## 1. Are the Baselines Strong and Fairly Tuned?

**Verdict: Weak, asymmetrical, and compromised by tuning/information leakage.**

1. **Unfair Tuning Asymmetry Between Base Predictor and Gates:**
   - In P1–P4, the baseline is `SCORE` (taking top nominations from the base model), which was tuned on RankIC or a general objective, while the abstention gates (`LOSS`, `NET-K`) are fitted directly to loss or net-return objectives. 
   - A single-stage comparator tuned directly on the policy endpoint (`BASE-V`, D8) was only added at the 11th hour in v0.9.3 under reviewer pressure. However, details of `BASE-V` tuning and search spaces are in §A7 (*not visible in this part*). As admitted in §A8 ("Further freeze checks", item a), out-of-sample base scores fed to gates risk historical hyperparameter selection leakage over the same periods.
2. **Rejection of the Essential Matched-Budget Base(+Z) Baseline:**
   - In §A10 ("Not adopted, with reasons"), the authors explicitly rejected testing a matched-capacity, matched-budget `Base(+Z)` model against the gate, arguing that *"it would let Z change nominations and is a different study."*
   - **This is scientifically unacceptable.** If alternative data $Z$ (holder state $Z_H$, market participant actions $Z_O^*$) provides an incremental boost in P2 or P3 ($\delta(\text{LOSS}(+Z), \text{LOSS}(-Z))$), you **cannot** conclude that a two-stage abstention gate architecture is beneficial. The gain could simply be that $Z$ carries raw alpha that any single-stage model could have captured directly.
3. **Fragile and Degenerated Variable-Count Baselines:**
   - The authors abandoned variable-count threshold policies as primary comparators because *"the threshold gates degenerated in the pilot"* (§A10, D9). When a baseline degenerates under standard validation, it points to poor hyperparameter tuning, uncalibrated probability thresholds, or improper regularization, rather than an inherent failure of variable-count selection. Retaining only fixed-count re-ranking ($c=0.5$) artificially papers over this baseline weakness.
4. **Arbitrary Rejection of Standard Variance Reduction (Seed Ensembling):**
   - The proposal to ensemble predictions across random seeds was rejected (§A10), leaving noisy, seed-dependent single models as baselines. In production quant systems, ensembling seeds is baseline standard practice.
5. **Permutation Baselines Without Retuning:**
   - For permutation controls (§A10), hyperparameters are kept fixed rather than retuned per permutation draw. This biases the permutation null against finding a negative or noisy result, because hyperparameters tuned on true data are forced onto permuted data.

---

## 2. Are the Metrics Appropriate?

**Verdict: Inappropriate for evaluating risk-focused abstention gates; statistically underpowered by design.**

1. **Mean Net Return as Sole Primary Metric for an Abstention Gate (Fatal Disconnect):**
   - The fundamental objective of an abstention or risk gate is **downside risk mitigation, tail risk truncation, and capital preservation**.
   - Yet, user decision D5 (§A10) and §A9 explicitly push **loss frequency and tail risk differences to "secondary" status**, keeping **mean net return per order** as the sole primary metric (P1–P6). 
   - Evaluating an abstention policy (which cuts trading volume by half, $c=0.5$) solely on mean return per order completely misses portfolio variance, maximum drawdown, Sortino/Sharpe ratios, turnover friction, and capacity drag.
2. **Pre-ordained Inconclusive Inference ($\Delta = 4.96$ bp vs ~6–11 bp SE):**
   - In §A10 (D4, D7), it is conceded that *"negligible is out of reach at the pilot precision"* and the team was told that *"the most likely outcome is eight inconclusive contrasts."*
   - Yet the decision was made to *"continue, as an estimation study... $\Delta$ unchanged."*
   - In confirmatory hypothesis testing, running a study with an equivalence/practical significance bound $\Delta = 4.96$ bp when standard errors are expected to produce intervals of 6–11 bp (wider than $\pm\Delta$) guarantees that confidence intervals will cross the boundary. Rebranding an underpowered trial as an "estimation study" while retaining the arbitrary $\Delta$ reference line is cosmetic.
3. **Flawed Aggregation Metric (Seed Averaging):**
   - §A8 item (c) defines seed averaging as: *"daily numerators and counts averaged over the five seeds before the ratio (equal to the mean of five ratios only if counts agree across seeds)."*
   - When trade counts vary across seeds (e.g., due to tie-breaks or eligibility filters), taking a ratio of averages rather than an average of ratios introduces a count-weighted distortion into the daily policy estimand.

---

## 3. Do the Experiments Actually Test the Stated Theorems and Claims?

**Verdict: No. The experiments and the theory are completely decoupled.**

1. **Explicit Admission of Complete Decoupling (§A11):**
   - Section A11 explicitly states:
     > *"No primary contrast, key secondary or classification of this amendment uses a result of `theory/theorems.md`. P1–P4 are comparisons of fitted selection policies by mean net return with bootstrap inference; they neither test nor rely on Theorem 1, its corollaries, Proposition 2 or Lemma 3."*
   - This represents a complete break between theory and experiment:
     - **Theorem 1 & Corollaries 1.1–1.2 (Time-uniform entry loss bounds):** Demoted to a "monitoring tool" whose empirical validity is not tested in the confirmatory market experiment. Furthermore, in the pilot, its interval was **$\pm 0.17$** (a 34 percentage point span), which is so loose that it provides virtually zero operational or empirical constraint.
     - **Proposition 2 (Lower bound):** Has *"no market experiment; stated as theory only."*
     - **Lemma 3 (Additive attribution):** Only checked by ledger identity reconciliation and synthetic tests, not as an empirical behavioral claim.
     - **Identity $\theta_{uns} = \theta_{sel} + A$:** An algebraic identity, not an empirical hypothesis.
2. **Objective Mismatch: LOSS Gate vs Mean Net Return:**
   - The `LOSS` gate is trained as a binary classifier ($0/1$ loss indicator), but its primary contrast P1 is measured in mean net return. The authors introduced P4 (`NET-K`) to observe net return directly, but this does not fix the fact that the theoretical bounds on loss rate do not correspond to the empirical metric tested in P1–P3.

---

## 4. What Experiments Are Missing?

Based on §§A8–A11, the following essential experiments are absent:

1. **A Representative Market-Wide Universe Experiment:**
   - The confirmatory universe is a convenience sample (889 SSE main-board stocks by code order + 111 random stocks; 109 delisted). An experiment testing the models on an unbiased, representative cross-section (including SZSE, ChiNext, and STAR boards proportionally) is completely absent. Cross-sectional ranking models developed on SSE-dominated convenience samples do not generalize.
2. **Direct Market-Experiment Validation of Theorem 1:**
   - Missing an empirical experiment testing whether the time-uniform loss rate interval derived in Theorem 1 actually achieves its nominal coverage and tightness under live market serial dependence and delayed label dynamics.
3. **Matched-Budget Base(+Z) Alpha Control:**
   - An experiment adding $Z_H$ and $Z_O^*$ directly to the single-stage base model, tuned with an equivalent compute/parameter budget, to determine whether $Z$'s value stems from the two-stage abstention mechanism or simply raw feature predictive power.
4. **Portfolio-Level Risk & Drawdown Experiments:**
   - Experiments reporting portfolio Sharpe, Sortino, Maximum Drawdown, Value-at-Risk (VaR), and Expected Shortfall (CVaR) to establish whether abstaining on 50% of trades actually improves risk-adjusted returns after factoring in capacity and turnover.
5. **Real-World Market Microstructure & Execution Delay Experiments:**
   - The study relies on synthetic fills (§A8 item d). An experiment with realistic China A-share trading frictions is missing:
     - $T+1$ execution constraints;
     - Limit-up (buy lock) and limit-down (sell trap / exit failure) execution realities;
     - Asymmetric market impact and volume participation caps.
6. **Unfreezing Incomplete Sensitivity Experiments:**
   - In §A8, key sensitivities remain unexecuted placeholders: $K \in \{20, 50\}$, $c \in \{0.1, 0.3, 0.7, 0.9\}$, event window lengths, and simulation error limits ($p_{max} = 6\%$).

---

## 5. Issues Ranked by Severity

| Rank | Issue | Severity | Section | Core Flaw & Consequence |
|:---:|:---|:---:|:---:|:---|
| **1** | **Total Decoupling of Theory & Empirical Plan** | **CRITICAL** | §A11 | The paper advertises theorems (Theorem 1, Prop 2, Lemma 3) that are completely uncoupled from primary experiments P1–P6. Theorem 1's bounds are unvalidated empirically and are practically uninformative ($\pm 0.17$ wide). |
| **2** | **Severe Universe Selection & Convenience Sampling Bias** | **CRITICAL** | §A8 | Using 889 stocks pulled in numeric code order on SSE creates massive sector/style concentration. Generating cross-sectional ranks on this distorted list invalidates any claim of general A-share market validity. |
| **3** | **Pre-Programmed Inconclusive Confirmatory Power** | **CRITICAL** | §A8, §A10 (D4, D7) | The authors already know SEs (6–11 bp) exceed the equivalence bound $\Delta$ (4.96 bp), guaranteeing inconclusive intervals. Rebranding an underpowered trial as an "estimation study" before touching the hold-out violates confirmatory rigor. |
| **4** | **Data Leakage into "Confirmatory" Development Sample** | **HIGH** | §A8.2 | Development years for the confirmatory population are identical to exploratory rounds where gate outcomes were already seen. Base re-tuning and gate tuning take place on already-inspected data. |
| **5** | **Absence of Matched-Budget Base(+Z) Benchmark** | **HIGH** | §A10 | Without a single-stage model incorporating $Z$, P2 and P3 cannot prove whether the two-stage gate architecture has any merit over standard alpha modeling. |
| **6** | **Metric Distortion: Excluding Downside Risk from Primaries** | **HIGH** | §A10 (D5) | Evaluating a loss-avoidance abstention gate solely on mean net return rather than tail risk, drawdown, and Sortino/Sharpe ratios ignores the fundamental purpose of the mechanism. |
| **7** | **Incomplete Audits and Open Placeholders at Freeze** | **MEDIUM** | §A8 | Multiple core parameters ($K, c$, event window, simulation error bounds) remain labeled as PLACEHOLDERs at the freeze boundary. Shifting $Z_O^*$ definition retroactively if LHB/BLK fail audits changes the estimand post-hoc. |
| **8** | **Synthetic Fill Realism Gap (A-Share Frictions)** | **MEDIUM** | §A8 item (d) | Reliance on synthetic fill simulators without strictly enforcing $T+1$ holding locks and limit-down exit failure traps casts doubt on net basis-point return estimates. |
| **9** | **Arbitrary Omission of Seed Ensembling and Variable Counts** | **LOW / OPERATIONAL** | §A10 (D9) | Rejecting seed ensembling increases noise unnecessarily; eliminating variable-count policies due to pilot calibration failure masks optimization shortcomings. |

---

## Recommendations for the Authors

1. **Re-align Paper Framing**: If Theorem 1 is not tested by the market experiment, remove claims that the empirical study validates the theory. Frame the theory strictly as an independent theoretical note or design an empirical experiment specifically evaluating time-uniform coverage under label delay.
2. **Reinstate Matched-Budget Base(+Z)**: To make any valid claim about the value of $Z$ in abstention gates, compare $\text{LOSS}(+Z)$ against a single-stage $\text{Base}(+Z)$ model.
3. **Elevate Tail Risk to Co-Primary**: Include empirical loss rate, Maximum Drawdown, and Sortino ratio in the primary evaluation family alongside mean net return.
4. **Reconstruct the Universe Point-in-Time**: Replace the 889 code-order convenience sample with a true historical point-in-time constituent list (e.g., CSI 300 / CSI 500 / CSI 1000) to eliminate SSE code-order survivorship and industry clustering.

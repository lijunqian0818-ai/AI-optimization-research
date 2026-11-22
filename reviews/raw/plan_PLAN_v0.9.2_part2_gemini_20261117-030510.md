# Review of Experiment Plan Amendment v0.9.2 (Part 2: Sections A4–A5)

**Reviewer Stance:** Skeptical Reviewer / Quantitative Methodology & Empirical Asset Pricing  
**Scope of Review:** `PLAN_v0.9.2_part2.md` (Sections A4: Claims & A5: Economic Bound), evaluated on its own merits and internal consistency.

---

## Executive Summary

The amendment demonstrates high procedural self-awareness. It candidly documents pilot standard errors, admits that the primary contrasts will almost certainly be inconclusive, formalizes multiple-comparison adjustments, and adds an accounting decomposition for secondary metrics.

However, from the standpoint of a skeptical reviewer, **the experimental design in Part 2 suffers from severe structural disconnects, inferential deadlocks, and baseline asymmetries**:
1. **Inferential Deadlock**: The primary family's statistical precision is mathematically incapable of achieving the "economically negligible" bound ($\pm\Delta$), guaranteeing that the primary confirmatory framework will default to "inconclusive".
2. **Theory–Experiment Severance**: The primary empirical experiments (P1–P4) do not test any of the paper's stated theorems or theoretical bounds.
3. **Metric–Motivation Mismatch**: Abstention and gating are theoretically motivated by downside risk reduction ("losing less often"), yet the primary confirmatory family evaluates solely mean net return per submitted order, relegating loss frequency and tail-risk metrics to secondary/exploratory status.
4. **Baseline Asymmetry**: The gate models are tuned directly on net policy value ($V$), whereas the primary baseline (SCORE) relies on a base predictor tuned solely on cross-sectional RankIC, creating an uneven comparison that fails to isolate whether two-stage gating beats a single-stage ranking model tuned on value.

---

## 1. Are the Baselines Strong and Fairly Tuned?

### 1.1 Asymmetric Tuning Objectives (RankIC vs. Policy Value $V$)
- In Section A4.1, the primary contrasts P1-b and P4-b evaluate whether $\text{LOSS}(-Z)$ or $\text{NET-K}(-Z)$ outperforms $\text{SCORE}$.
- However, as noted in the text, the base predictors (LightGBM, Ridge) are tuned on **cross-sectional RankIC**, whereas the learned gates are tuned directly on **$V$ (mean net standard-order return per submitted order)**.
- **Fairness Critique**: Comparing a gate tuned directly on the target evaluation metric ($V$) against a base score (SCORE) tuned on an unweighted cross-sectional rank correlation is structurally unfair. A base model optimized for RankIC focuses on ranking accuracy across all nominated candidates, whereas $V$ rewards picking stocks with high positive net return or avoiding heavy losers. Beating SCORE under this setup does not prove that a two-stage gating architecture is superior; it may merely reflect that the gate was tuned on the evaluation loss function while the baseline was not.

### 1.2 Missing Single-Stage Direct Value / Top-Quantile Baseline
- To prove that a separate "abstention/gating stage" has scientific value, the primary benchmark must not merely be a RankIC-tuned base predictor. It must include a **single-stage ranking model tuned directly on top-quantile net return or policy value $V$** (with the exact same hyperparameter search budget).
- Without this baseline, a positive P1 or P4 result cannot distinguish between:
  1. The architectural merit of an abstention gate.
  2. The trivial fact that optimizing directly for the downstream evaluation metric outperforms an off-target surrogate objective (RankIC).

### 1.3 Absence of Standard Heuristic and Risk-Adjustment Baselines in Primary Contrasts
- The baseline SCORE simply takes the top $\lceil cK \rceil$ names by raw base score.
- The plan relegates simple regularized re-rankers (e.g., `LOSS-LR`) and basic risk filters (`VOL`, `LIQ`) to exploratory secondary analyses (§A4.3 item 2).
- A rigorous quantitative baseline should test whether simple, transparent heuristic adjustments (e.g., Score / Volatility, or Score penalized linearly by the bid-ask spread) achieve the same or better performance than a complex, non-linear GBDT loss gate.

### 1.4 Unanchored Baseline Quality and Hold-out Alpha Decay
- In Section A4.1, the zero-abstention benchmark ($G_0$, submitting all $K$ candidates) is entirely omitted from the primary family. 
- If the base predictor's alpha decays toward zero or turns negative in the hold-out period (as observed in the pilot's 2021 drop where RankIC fell to 0.03–0.04 and nomination-minus-candidate spread collapsed to zero), SCORE is merely selecting from an uninformative pool.
- Comparing a gate to SCORE in an alpha-depleted pool tests "which algorithm picks better among noise," rather than whether gating adds economic value to an operative trading system.

---

## 2. Are the Metrics Appropriate?

### 2.1 Mismatch Between Core Motivation and Primary Metric
- **The Core Premise**: The motivation for abstention gates in automated execution is risk control—avoiding trades when confidence is low to "lose less often" and curtail left-tail drawdowns.
- **The Metric Disconnect**: The primary family (P1–P4) is evaluated **exclusively on mean net return per submitted order ($V$)**.
- Downside risk, loss frequency ($\Lambda(g, h)$), worst 5% tail returns, and maximum drawdown are relegated to secondary/exploratory analyses (§A4.3 item 0).
- **Consequence**:
  - If a gate successfully cuts loss frequency by 30% and halves tail risk, but leaves mean return flat ($\delta \approx 0$), the primary framework classifies it as "inconclusive."
  - Conversely, if a gate increases mean return slightly by selecting high-volatility "lottery" stocks while increasing loss frequency and drawdown, it could be classified as "materially beneficial." This contradicts the foundational philosophy of abstention.

### 2.2 Treatment of Unfilled Orders ($\rho = 0$) Distorts Policy Value
- In the definition of $V^g = \sum_{t} \sum_{i \in \text{Sub}_t^g} \rho_{ti} / \sum_t S_t^g$, unfilled orders are assigned $\rho = 0$ in the numerator while counting fully in the denominator $S_t^g$.
- **Distortion / Adverse Selection Blindspot**:
  - A policy can artificially boost $V$ or lower variance by submitting orders with low fill probability on adverse days (acting as a synthetic cash holding with zero return).
  - Conversely, standard limit-order execution suffers from severe adverse selection: orders fill disproportionately when the market moves against them. A gate that fails to account for fill probability conditional on adverse price moves will distort true execution performance.
  - While §A4.3 item 0 provides an exploratory outcome decomposition, the primary confirmatory metric $V$ remains vulnerable to fill-rate confounding.

### 2.3 The Economic Bound $\Delta$ and Inferential Deadlock
- Section A5 defines $\Delta = 4.96$ bp per submitted order, anchored to an illustrative $\Delta_{\text{cap}} = 1.0\%$ annual return via $\Delta_{\text{ord}} = \Delta_{\text{cap}} \times (H+1) / (A \times c)$.
- The plan candidly admits:
  1. The translation to capital is purely conditional (fill rates, capital utilization, holding periods, and turnover vary across policies).
  2. Pilot standard errors for P1 and P4 are 3.0–3.8 bp.
  3. Under simultaneous 95% intervals with $q \in [1.96, 2.73]$, the interval half-width is at least $1.96 \times 3.0 \approx 5.9$ bp, which strictly exceeds $\Delta = 4.96$ bp.
- **Critical Flaw**: **The label "economically negligible" ($-\Delta < L$ and $U < \Delta$) is mathematically unattainable for P1 and P4 even if the estimated effect is exactly zero.**
  - Maintaining a formal 4-class classification table where one of the core cells has zero statistical power under the null hypothesis is methodologically unsound.
  - The confirmatory family is pre-destined to return "inconclusive" unless the true effect is enormous ($>13\text{--}18$ bp per order, corresponding to an unrealistic 2.7–3.7% annual alpha from gating alone).

---

## 3. Do the Experiments Actually Test the Stated Theorems and Claims?

### 3.1 Total Decoupling of Primary Experiments from Theory
- Section A4.1 states explicitly: *"No contrast of this family uses a theory result (§A11)."*
- Furthermore, Section A11 (referenced in Part 2) reveals that Theorem 1 (time-uniform confidence sequences for entry loss rate) is merely a descriptive monitoring tool, Proposition 2 has no market experiment, and Lemma 3 is an accounting identity.
- **Critique**: If the research project claims theoretical contributions regarding abstention and time-uniform risk bounds, **none of the primary experiments in Part 2 test or validate these theorems.** There is no empirical hypothesis testing whether the theoretical time-uniform intervals cover the realized loss rate, nor whether the theoretical lower bounds hold. The empirical study operates completely disconnected from the mathematical theory.

### 3.2 Does P2/P3 Test "Participant Information" ($Z_H$ and $Z_O$)?
- **The Nomination Bottleneck**: Both P2 and P3 evaluate gates applied to nominations generated by $\text{base}(-Z)$. If holder state ($Z_H$) or other-participant actions ($Z_O^*$) contain valuable predictive signals that identify names *outside* the base model's top $K=30$, those opportunities are permanently discarded.
- **Representation vs. Information**: As acknowledged in §A4.3 item 6, P2 and P3 test only whether a specific GBDT/Ridge formulation re-ranks the existing candidate set better with these features. A null result ($\delta \approx 0$) cannot reject the hypothesis that $Z$ contains market information; it only rejects the efficacy of this particular two-stage re-ranking architecture.
- **Omission of Combined Signal ($Z_H + Z_O^*$):** P2 tests $+Z_H$ and P3 tests $+Z_O^*$ in isolation. The primary family contains no contrast evaluating the combined feature set $\text{LOSS}(+Z_H + Z_O^*)$. If holder accumulation and institutional block trades exhibit synergistic predictive power, this design cannot detect it.

### 3.3 Flawed Permutation and Noise Controls (§A4.3 item 6)
- The plan notes that row-wise permutation breaks the link between $Z$ and stock outcomes, but admits:
  1. A stock's own missingness pattern moves with the row, exposing the model to feature combinations never seen in real market data.
  2. Standard Gaussian noise controls do not match the sparsity, persistence, or heavy-tailed missingness of corporate/market event features.
- Consequently, comparing real $Z$ against permuted or Gaussian noise cannot validly attribute performance to the economic mechanism of participant actions.

---

## 4. What Experiments Are Missing?

1. **Single-Stage Direct-Value Ranking Baseline**:
   - A LightGBM / Ridge baseline trained on candidate sets with the exact same objective ($V$ or top-quantile margin) and tuning budget as the gates, establishing whether two-stage gating outperforms unified ranking.
2. **Primary Joint Risk-Adjusted Evaluation**:
   - Primary contrasts measuring difference in Sharpe ratio, Sortino ratio, or Expected Shortfall (CVaR at 5%), reflecting the risk-reduction goal of abstention.
3. **Combined Feature Group Contrast**:
   - A contrast for $\delta(\text{LOSS}(+Z_H + Z_O^*), \text{LOSS}(-Z))$ to test the joint effect of all audited participant features.
4. **Base(+Z) Benchmark (Testing the Nomination Bottleneck)**:
   - An experiment allowing $Z$ into the nomination stage to verify whether $Z$ is throttled by the $\text{base}(-Z)$ nomination filter.
5. **Execution & Frictional Stress-Testing in the Primary Family**:
   - P1–P4 evaluated under slippage models that penalize illiquid names or limit-up/down execution delays, rather than assuming frictionless non-fills with $\rho = 0$.
6. **Empirical Validation of Theoretical Bounds**:
   - Backtesting Theorem 1's time-uniform confidence sequence on hold-out data to empirically verify coverage rates and tightness under real market delays.

---

## 5. Issues Ranked by Severity

| Rank | Severity | Issue | Core Implication |
|---|---|---|---|
| **1** | **Critical** | **Inferential Deadlock / Illusory "Negligible" Bound** | With pilot SEs (3.0–3.8 bp) and $q \ge 1.96$, interval half-widths exceed $\Delta = 4.96$ bp. "Negligible" is statistically impossible to reach even at an effect of exactly zero. The confirmatory family is pre-programmed to produce "inconclusive" results across all primary contrasts. |
| **2** | **Critical** | **Theory–Experiment Disconnect** | Primary experiments (P1–P4) do not test any theorems, corollaries, or theoretical bounds from the theory section. The empirical paper is entirely decoupled from the mathematical claims. |
| **3** | **Critical** | **Metric–Objective Mismatch (Mean Return vs. Downside Risk)** | Abstention is justified by loss avoidance and tail-risk control, yet primary evaluation relies strictly on mean net return per order ($V$). Risk and loss-frequency metrics are demoted to exploratory status. |
| **4** | **Major** | **Asymmetric Baseline Tuning (RankIC vs. Policy Value)** | Base models are tuned on RankIC while gates are tuned on $V$. SCORE is an off-target baseline, confounding whether gating adds value or merely benefits from metric-aligned tuning. |
| **5** | **Major** | **Nomination Bottleneck for Participant Features ($Z_H, Z_O$)** | $Z$ is only tested as a re-ranker of $\text{base}(-Z)$ nominations. If $Z$ generates alpha outside the top 30, it is permanently blinded, preventing any definitive claim about the information content of $Z$. |
| **6** | **Major** | **Missing Single-Stage Value Baseline & Combined Gate** | No single-stage model tuned on $V$ is evaluated; no primary contrast tests the joint feature set ($Z_H + Z_O^*$). |
| **7** | **Moderate** | **Distortion from Unfilled Orders ($\rho = 0$) in Primary Estimand** | Unfilled orders zero out returns in $V$, creating incentives for policies to select hard-to-fill orders to artificially suppress downside volatility. |
| **8** | **Moderate** | **Decoupling of Order-Level Bound ($\Delta$) from Portfolio Economics** | Variable fill rates, turnover, and capital utilization break the theoretical equivalence between 4.96 bp per order and 1.0% annual capital return. |
| **9** | **Moderate** | **Inadequate Controls for Event Features** | Gaussian noise and row-shuffled permutations fail to match sparse event dynamics, preventing clean causal attribution of $Z$. |

---

## Conclusion & Recommendations for the Authors

- **Acknowledge the Estimation-Only Scope Frankly**: Since the primary family cannot statistically reject $\pm\Delta$ for near-zero effects, drop the pretense of a 4-class hypothesis-testing decision engine. Formally frame the study as pure interval estimation of hold-out effect sizes.
- **Elevate Loss Frequency / Tail Metrics**: Move the loss-share difference $\Lambda(g, h)$ or worst-5% tail return into a co-primary family with appropriate joint multiplicity control, ensuring that the empirical test aligns with the conceptual justification for abstention.
- **Level the Baseline Playing Field**: Include a single-stage ranking model tuned directly on $V$ with an identical hyperparameter budget before claiming that two-stage gating is an effective architectural paradigm.

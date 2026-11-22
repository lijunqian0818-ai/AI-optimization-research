### Executive Summary

This review evaluates **Part 3 (Sections A4.3, A5)** and **Part 4 (Sections A6, A7)** of the experiment plan amendment (v0.9.3). 

While the amendment demonstrates high technical sophistication—particularly in defining exact accounting identities (e.g., the $P3 = C_E + C_{\neg E}$ event decomposition) and pre-registering stress scenarios—it suffers from **critical statistical power deficiencies**, **structural baseline asymmetries**, and **compromised inferential utility in its feature-evaluation framework**. Most notably, the standard errors observed in the pilot indicate that the planned sample size cannot statistically distinguish effects at the pre-specified economic threshold ($\Delta = 4.96\text{ bp}$), rendering conclusive verdicts unlikely.

---

### Issues Ranked by Severity

| Rank | Severity | Issue | Core Plan Section |
| :--- | :--- | :--- | :--- |
| **1** | **Critical** | **Severe Power Deficiency Relative to Economic Bound ($\Delta$)** | §A5, §A6 |
| **2** | **High** | **Inconclusive Design for Feature Group Evaluation ($Z_H, Z_O$)** | §A4.3 (Item 6), §A7 |
| **3** | **High** | **Under-Tuned and Conceptually Constrained Baseline (`BASE-V`)** | §A7 |
| **4** | **Medium** | **Divergence Between Order-Level Metric ($\rho$) and Deployed Returns ($\Delta AR$)** | §A4.3 (Items 0, 9), §A5 |
| **5** | **Medium** | **Synthetic Macro-Generation Flaws in Validity Suite (`precision_v9`)** | §A6 |
| **6** | **Low** | **Arbitrary Homogeneity of the Economic Threshold ($\Delta$)** | §A5 |

---

### Detailed Critique

#### 1. [Critical] Severe Statistical Under-Powering Relative to the Economic Bound ($\Delta$)
* **The Conflict:** Section A5 fixes the economic hurdle at $\Delta = 4.96\text{ bp}$ per submitted order (derived from a 1.0% annual capital hurdle). Meanwhile, Section A6 discloses pilot planning standard errors:
  $$\text{SE}(P1) \approx 3.0\text{--}3.8\text{ bp}, \quad \text{SE}(P4) \approx 3.0\text{--}4.0\text{ bp}, \quad \text{SE}(P2/P3) \approx 1.6\text{--}3.2\text{ bp}$$
* **Statistical Implication:** For a nominal 95% marginal confidence interval, the half-width is $\approx 1.96 \times 3.5\text{ bp} \approx 6.9\text{ bp}$. Simultaneous intervals (adjusting across $P1\text{--}P6$, as targeted in §A0 / §A4.1, though the full formulation is *not visible in this part*) will be even wider ($\approx 8\text{--}10\text{ bp}$).
* **Skeptical Critique:** An interval with half-width of $\pm 7\text{ to } 9\text{ bp}$ evaluated against an equivalence or superiority boundary of $\Delta = 4.96\text{ bp}$ is fundamentally underpowered. Even if the true effect matches the economic bound ($+5\text{ bp}$), the lower confidence limit will easily cross 0, and the upper limit will extend to $+12\text{--}14\text{ bp}$. The study design virtually guarantees inconclusive intervals (failing to reject zero while failing to establish equivalence within $[-\Delta, +\Delta]$).

---

#### 2. [High] Inconclusive Design for Feature Group Evaluation ($Z_H, Z_O$)
* **Concession of Non-Informativeness:** Section A4.3 (Item 6) explicitly concedes:
  > *"A model given such columns sees feature combinations that do not occur in real data, so $\delta(\text{real}, \text{permuted}) > 0$ is **not** evidence of information in Z... a P2 or P3 near zero does not show that the group lacks useful information; a positive one shows value of this representation in this training procedure, not a participant-information mechanism..."*
* **Skeptical Critique:** If neither a positive result nor a null result provides evidence of genuine information content in $Z$, the experiment fails the basic requirement of a scientific hypothesis test. 
* **Flawed Permutation Scheme:** Shuffling group columns across names within a day breaks the joint distribution between $Z$ and the baseline features $B_0 + R$. Decision tree algorithms (LightGBM) partition feature space orthogonally; feeding synthetic, physically impossible combinations of $(B_0, Z)$ triggers out-of-distribution splits. Thus, $\delta(\text{real}, \text{permuted})$ tests model sensitivity to corrupted joint distributions rather than feature informativeness.
* **Absence of Unified Baseline:** Section A7 relegates `BASE(+Z)` to exploratory status. Without benchmarking the two-stage gating architecture against an end-to-end model trained on $B_0 + R + Z$, the experiment cannot determine whether the two-stage pipeline is beneficial or merely an inefficient surrogate for full-model retraining.

---

#### 3. [High] Under-Tuned and Conceptually Constrained Comparator (`BASE-V`)
* **Asymmetric Optimization:** `BASE-V` (§A7) was introduced to isolate hyperparameter tuning on the endpoint $V$ from the architectural contribution of a gate. However:
  1. **Loss vs. Metric Mismatch:** `BASE-V` retains within-day return rank loss during internal training; *only its hyperparameters* are selected using $V$. In contrast, the two-stage gates (e.g., `NET-K`, `LOSS`) train directly on selection-aligned or loss-avoidance objectives. A model optimizing rank loss cannot emulate an asymmetric tail-loss policy simply by varying tree depth or regularization.
  2. **Budget Inadequacy ($T=30$):** Tuning a gradient-boosted tree (LightGBM) over continuous spaces (learning rate, feature fractions, regularization, min child samples) using only 30 random/Bayesian trials is severely budget-constrained. The validation metric $V$ on top-15 names is inherently noisy; 30 trials will likely overfit validation noise rather than converge to optimal hyperparameters.

---

#### 4. [Medium] Divergence Between Order-Level Metric ($\rho$) and Deployed Returns ($\Delta AR$)
* **Metric Distortion:** The primary contrasts ($P1\text{--}P6$) evaluate mean net return per submitted order ($\rho$). Yet, Section A4.3 (Item 9) reveals a striking pilot discrepancy for LightGBM $P1$:
  $$\delta = -6.07\text{ bp per order} \quad \text{beside} \quad \Delta AR = -1.2\text{ percentage points annual return}$$
* **Skeptical Critique:** As acknowledged in §A4.3 (Item 0) and §A5, policies submit orders with differing fill rates, turnover, holding periods, and capital utilization. Evaluating policies on per-submitted-order returns assumes capital scales linearly with submissions. If Policy A achieves higher per-order $\rho$ by trading illiquid names that rarely fill, its realized portfolio alpha ($\Delta AR$) may collapse relative to a baseline that fills reliably. While the reconciliation table in §A4.3 (Item 9) documents this gap, treating $\rho$ as the headline decision criterion remains problematic when portfolio-level return diverges in sign or magnitude.

---

#### 5. [Medium] Synthetic Validity Gate Design Flaws in `precision_v9`
* **Macro-Aggregation vs. Micro-Dynamics:** In Section A6, data generation synthesizes daily numerators and denominators using AR(1), Student-$t$, and GARCH processes calibrated to development covariance. This generates aggregated daily time-series rather than cross-sectional order queues, skipping asset-level selection dynamics, cross-sectional ranking competition, and fill-probability clustering.
* **Multiple Testing in Validity Verification:** The pass rule tolerates $p_{\max} = 6\%$ simultaneous non-coverage on nominal 5% intervals. However, the rule specifies that *"The bounds are per scenario, not simultaneous over scenarios."* Evaluating six gated scenarios ($V1\text{--}V6$) plus $R$ independently creates a high joint probability that at least one scenario fails by chance, triggering an unnecessary fallback to Route B (abandoning simultaneous coverage claims).

---

#### 6. [Low] Arbitrary Homogeneity of the Economic Bound ($\Delta$)
* **Uniformity by Fiat:** Section A5 states that $\Delta = 4.96\text{ bp}$ applies uniformly across all primary contrasts $P1\text{--}P6$ by user decision (O2), explicitly divorced from the actual costs of data acquisition or computational execution.
* **Skeptical Critique:** Applying the same threshold to an internal re-ranking model ($P1$: `LOSS` vs. `SCORE`) and an external alternative data vendor feed ($P3$: $+Z_O$) is economically nonsensical. Alternative vendor feeds carry recurring subscription costs and ETL overhead; their required hurdle should be strictly higher than a zero-data-cost internal re-ranker.

---

### Direct Evaluation of Plan Dimensions

#### A. Are the Baselines Strong and Fairly Tuned?
* **No.** 
  * `BASE-V` is hobbled: its training loss is restricted to return ranking while gates are optimized for net return or tail risk.
  * The tuning budget ($T = 30$) across five seeds is too small to locate reliable optima in noisy top-15 daily returns.
  * The natural primary baseline—an end-to-end model trained on all features `BASE(+Z)`—is excluded from confirmatory testing and relegated to exploratory analysis.

#### B. Are the Metrics Appropriate?
* **Partially.**
  * The decomposition in §A4.3 Item 0 ($V = P(\text{filled}, \rho < 0)E[\rho \mid \cdot] + P(\text{filled}, \rho \ge 0)E[\rho \mid \cdot]$) and the exact identity in Item 7 ($P3 = C_E + C_{\neg E}$) are mathematically rigorous and appropriate for dissecting fill and loss mechanisms.
  * However, relying on per-submitted-order $\rho$ as the gating primary metric is deceptive when fill rates and invested capital fractions differ materially between candidate policies and baselines.

#### C. Do the Experiments Actually Test the Stated Theorems and Claims?
* **No.**
  * The permutation follow-up (§A4.3 Item 6) fails to test whether $Z$ contains predictive information, as admitted by the authors.
  * The validity simulation (§A6) tests coverage on synthetic daily aggregates rather than end-to-end market selection mechanisms.
  * Empirical performance of Lemma 3 attribution (§A4.3 Item 4; formal statement *not visible in this part*) is evaluated descriptively rather than as a falsifiable statistical test.

#### D. What Experiments Are Missing?
*(Restricted to analyses not visible in Parts 3 and 4)*

1. **End-to-End Single-Stage Benchmark (`BASE(+Z)`):** A rigorous test evaluating whether the two-stage gate ($P2/P3$) outperforms simply adding $Z$ directly to the base predictor's feature set.
2. **Asymmetric Loss Direct Baseline:** Training the base predictor directly with asymmetric quantile or pinball loss (penalizing negative returns), isolating the loss function effect from the two-stage gating architecture.
3. **Execution & Capacity Scaling Sensitivity:** Testing the primary contrasts under variable order sizes and non-linear market impact models, rather than relying on uniform cost shifts.
4. **Gate Tuning Budget Stability Test:** A learning curve experiment varying the gate tuning budget ($T \in \{30, 60, 100\}$) to demonstrate that the primary gates are not themselves under-tuned or overfitting validation noise.

## Overall assessment

**Major revision before freezing the hold-out analysis.** The amendment improves the design substantially through count-matched comparisons with SCORE, paired contrasts, explicit disclosure of pilot-informed changes, and unconditional reporting of hold-out results.

The primary experiments can answer a narrow question about the value of these fitted selection policies on this population. Broader conclusions about loss prediction, feature information, deployment value, or the stated theorems need additional evidence.

This review covers the supplied amendment and pilot summary. PLAN v0.8, the theorem statements, search spaces, and implementation were not supplied, so several inherited safeguards remain unverified.

## Issues ranked by severity

### 1. Critical — The theorem-to-experiment mapping is missing

P1–P3 concern average net returns from fixed-count selection. The supplied theorem-related results concern a loss-rate monitoring interval, an accounting attribution, and an algebraic decomposition. Their connections to the primary contrasts are unspecified.

- **Theorem 1.** Reporting one interval with half-width around 0.17 demonstrates its numerical width. Evaluating its statistical guarantee requires repeated simulations under its assumptions. If its guarantee is time-uniform, measure simultaneous coverage across monitoring times and performance under optional stopping. Include adaptive selection, delayed outcomes, and dependence patterns permitted by the theorem.
- **Lemma 3.** Accounting reconciliation is an appropriate implementation check. Add cases with analytically known exposure, composition, and cost contributions. Reconciliation alone establishes no predictive or economic benefit.
- **The new identity.** Prove it algebraically and test implementation cases involving empty cells, zero submissions, unequal cell allocations, and variable nomination counts. Market results illustrate its terms.

**Required revision:** Add a table connecting every theorem and substantive claim to its assumptions, observable implication, experiment, and interpretation. The full theorem statements are needed to assess whether those experiments suffice.

### 2. Critical — Point-in-time validity remains unresolved

The chronology audit is planned, which is appropriate. Its outstanding status prevents approval of the empirical design as execution-ready.

The single-feature timing correlation and code-header inspection cover only a small portion of potential leakage. Audit at least:

- Label-end dates at training, tuning, and deployment boundaries.
- Out-of-sample provenance of every base score used to train gates.
- Monthly liquidity-screen construction using information available before selection.
- Historical eligibility, delisting treatment, corporate-action adjustments, and revised vendor fields.
- Event availability dates and the exact implementation of the two-day lag.

The INS limitation deserves stronger treatment. If announcement timing cannot be established, moving an unaudited date forward two days does not establish historical availability.

**Required revision:** Freeze objective class-inclusion criteria before examining outcomes. For claims about executable information, use auditable event classes in the primary specification and retain uncertain classes as sensitivity analyses. Any remaining vendor-date analysis needs the stated restricted scope.

### 3. High — Baselines are credible, but tuning fairness is not established

**SCORE is a strong and necessary baseline.** Exact expected random abstention, LOSS-LR, NET-K, VOL, LIQ, scaled G0, and VT collectively provide a useful comparison set.

However, an equal budget of 30 configurations does not establish comparable optimization quality. Search difficulty differs across model families and feature sets. The supplied material leaves important questions unanswered:

- Are +Z and −Z policies independently tuned with identical validation periods, objectives, and access to information?
- Do gate inputs include the base score or rank? This determines whether the gate can readily preserve SCORE’s ordering.
- Do search spaces include sufficiently simple and strongly regularized configurations?
- Are configurations stable across temporal folds and seeds?
- Does the historical selection of tuning settings precede each period presented as out-of-sample evaluation?

There is also a substantive training-window issue. Fixed-count gates retain training only through Y−2 although their calibration step has disappeared. SCORE benefits from a base fitted through Y−1. That may be a deliberate conservative protocol, but the resulting data-age disadvantage needs justification.

**Required revision:** Publish the tuning matrix and validation chronology. Add a development-only sensitivity using the most recent legally available out-of-sample training rows for every learned gate, with label purging. Report validation performance against tuning budget.

### 4. High — LOSS optimizes a surrogate for the primary economic outcome

Ranking by predicted loss probability can prefer frequent small gains combined with occasional large losses. P1 measures expected net return, so a successful loss classifier can still perform poorly on P1.

NET-K directly addresses the economic objective, yet its comparisons are secondary. Consequently:

- A negative P1 supports a conclusion about this LOSS policy.
- A negligible P1 supports a bounded conclusion about its incremental value.
- Conclusions about learned gates generally require evidence across economically aligned methods.

**Required revision:** Give NET-K a central role in interpreting economic claims. If broad learned-gate claims are intended, pre-specify an appropriate NET-K comparison in the confirmatory design. Also report loss-rate differences, gain/loss magnitudes, and probability-quality diagnostics if loss prediction remains a scientific claim.

### 5. High — The equivalence rationale conflicts with the proposed interval rule

The classification scheme is coherent **provided the simultaneous intervals have valid coverage**. Its power justification needs correction.

Concluding negligible from a simultaneous 95% interval is more demanding than conventional unadjusted 5% TOST, which uses a 90% interval. Removing TOST therefore does not solve the precision problem.

At a 3 bp standard error, even an ordinary approximate 95% interval has half-width 5.9 bp, exceeding Δ = 4.96 bp. Simultaneous adjustment widens it further. At that width, an estimate exactly at zero cannot receive the negligible classification.

**Required revision:** Retain the interval classification if it reflects the intended evidential standard, while explicitly accepting its low probability of resolving economic negligibility. Report minimum detectable effects and classification probabilities. Resolve O3 before freezing so that the final inferential procedure is unambiguous.

### 6. High — The bootstrap validation is insufficiently specified

The joint date-block bootstrap appropriately preserves cross-policy dependence. Agreement with Newey–West estimates provides a useful variance diagnostic.

However, outer and inner resampling from the same empirical history largely checks performance within the assumed resampling model. It gives limited evidence about coverage under structural changes, persistent volatility, annual refitting, or dependence beyond the chosen blocks.

The proposed fallback also needs care. Bonferroni controls multiplicity when its marginal intervals have adequate coverage. Undercoverage of percentile intervals can persist after adjustment.

**Required revision:**

- Specify studentization, variance estimation, missing-date handling, and treatment of P3’s potentially shorter window.
- Define numerical pass/fail criteria and Monte Carlo uncertainty before running validation.
- Add controlled data-generating processes with known effects, heavy tails, serial dependence, regime changes, and annual model updates.
- Evaluate coverage at ±Δ, where erroneous economic classifications are especially relevant.
- Validate the fallback independently.

A single untouched hold-out protects against direct outcome-driven redesign. Its inferential validity still depends on these sampling assumptions.

### 7. High — Economic interpretations need an explicit deployment bridge

Submitted-order value is appropriate for count-matched selection. Assigning zero to unfilled orders also incorporates execution opportunity into the policy outcome.

Equal submission counts nevertheless leave room for differences in fill rates, realized holdings, risk, and trading costs. The Δ-to-capital conversion depends on the slot-accounting assumptions and realized capital use.

Further, a ±1% annual capital bound expresses a materiality judgment. Calling it a data-cost threshold requires a connection to actual acquisition, maintenance, and trading costs.

**Required revision:**

- Verify the per-order-to-capital translation under the frozen execution model.
- Report fill rates, invested capital, turnover, and paired deployed return differences alongside P1–P3.
- Add pre-specified cost, fill, and execution-delay stress scenarios.
- Explain the feature-group bound independently of unspecified data costs.

Keep submitted-order value primary if that is the intended question. Evaluate risk-reduction claims through corresponding deployed risk outcomes.

### 8. Medium–high — The event-conditional estimand is ambiguous

Restricting to event-associated orders can give the two policies different submitted-order denominators, even though they submit the same total number daily. Their subgroup conditional means then lose the simple paired interpretation of P3.

The requirement of at least three event nominations also excludes days. Contributions computed on those days cannot automatically explain the full-sample contrast.

**Required revision:** Define event and complementary contributions using a common denominator. For event indicator \(E_{ti}\), use

\[
C_E=
\frac{\sum_{t,i}E_{ti}
\left(I^{+Z}_{ti}-I^{-Z}_{ti}\right)\rho_{ti}}
{\sum_t S_t}.
\]

Define \(C_{\neg E}\) analogously, giving \(P3=C_E+C_{\neg E}\) on the same evaluation window. Report support-restricted analyses separately. A percentage “share of P3” becomes unstable when P3 is near zero.

### 9. Medium — Permutation follow-up cannot settle the information question

The amendment correctly acknowledges that unconditional shuffling breaks dependence between Z and existing features. Repeated draws reduce dependence on a single shuffle, but fixed real-data hyperparameters can disadvantage shuffled inputs.

Twenty draws also provide limited characterization of distribution tails. Variation across draws measures permutation sensitivity and needs to be distinguished from temporal sampling uncertainty.

**Required revision:** State exactly what dependence and missingness the shuffle preserves. Include a matched noise-feature control and, if feasible, a separately retuned permutation sensitivity with the same budget. Treat real-versus-no-Z performance as the direct policy-value comparison. Any conditional-information claim requires additional assumptions and an appropriate conditional procedure.

### 10. Medium — Robustness and generalization remain narrow

The population restriction is transparently disclosed and consistent with the user’s no-download decision. It still limits inference to a liquidity-selected, SSE-heavy convenience sample.

The frozen c = 0.5 and K = 30 also represent one operating point. They cannot characterize abstention performance generally.

**Required revision:** Within existing data, pre-specify a small secondary sensitivity grid for submission fraction and nomination count, plus development-defined liquidity or regime groups. Keep all settings visible and preserve the primary specification. Report seed-level results to show whether average performance represents the individual trained policies.

## Minimum additional experiments before approval

| Priority | Experiment | Purpose |
|---|---|---|
| Required | End-to-end timestamp and availability audit | Establish historical feasibility |
| Required | Theorem-specific simulations and algebraic tests | Connect evidence to mathematical claims |
| Required | Known-effect inference simulations, including ±Δ | Validate coverage and classification errors |
| Required | Tuning-budget and training-recency sensitivity | Assess comparison fairness |
| Required | Cost, fill, and delay stress tests | Support economic interpretation |
| Required | Exact event-contribution decomposition | Make subgroup attribution interpretable |
| Strongly recommended | NET-K comparison and loss-outcome diagnostics | Resolve objective mismatch |
| Strongly recommended | Small c/K sensitivity grid and seed reporting | Assess operating-point stability |

**Bottom line:** SCORE and the count-matched estimands materially strengthen the plan. Approval should depend on resolving chronology, theorem alignment, tuning comparability, and inferential calibration. With the anticipated precision, an inconclusive hold-out result is a plausible scientific outcome, and the paper’s claims should be designed to accommodate it.

## Overall assessment

**Major revision before freezing.** The amendment supports a narrowly scoped estimation study of fixed-coverage re-ranking. SCORE, NET-K, BASE-V, paired comparisons, and explicit disclosure of pilot-informed choices substantially improve the design.

The main unresolved issues are the connection between the inferential target and the bootstrap, point-in-time validity, and the strength of the end-to-end comparator. The expected low precision is an accepted limitation. It does not invalidate an estimation study.

This review covers the supplied amendment and pilot summary. The referenced v0.8 plan, theorem statements, search spaces, and implementation were unavailable, so their correctness remains unverified.

## Issues ranked by severity

### 1. Critical — The interval validation does not resolve the pipeline’s main source of uncertainty

**Where:** §A0, §A4.1, §A6.

The target averages over alternative hold-out histories, including the training data and annual refits those histories would produce. Resampling realised daily policy totals captures that uncertainty only under an adequate dependence approximation.

The plan correctly acknowledges this. However, its principal validation scenarios generate policy totals directly. The scenario that actually refits a policy, X4, is outside the pass criteria. Consequently, the interval procedure can pass every gate while performing poorly under the study’s own annual-learning mechanism.

Annual refitting does not automatically invalidate a bootstrap. Its effect depends on training stability, persistence, and sample size. The missing evidence concerns those quantities.

**Required revision**

- Add full-pipeline synthetic experiments with annual expanding-window refits, delayed labels, common market shocks, and the actual selection rules.
- Include stable learners and learners whose fitted errors persist within and across years.
- Evaluate coverage against the stated ratio-of-expectations target.
- Specify before opening the hold-out how substantial failure under plausible pipeline scenarios changes the headline inference.

The current Route B is triggered by failure in selected calibration models. It leaves the response to failure in the most relevant pipeline model unresolved. Caveats alone do not resolve that design decision.

### 2. Critical until audited — Historical availability and selection chronology remain open

**Where:** §A7–A8.

The audit checklist is appropriate, but its results determine whether these are implementable historical policies.

Two gaps deserve explicit treatment.

- **Vintage uncertainty.** §A8 permits a limitation statement where historical availability cannot be established. Features with unresolved revision or disclosure timing can contaminate the primary comparison. Define a deterministic rule for exclusion from the primary feature set and retention in sensitivity analyses.
- **Hyperparameter-selection chronology.** A base score can be out of sample with respect to fitting while its hyperparameters were selected using that row’s outcome. Such scores can make gate-training examples systematically cleaner or more predictive than deployment examples.

The latter does not by itself leak hold-out outcomes when all selection happens before the hold-out. It does create a potentially important training–deployment mismatch.

**Required revision**

Complete the audits and run a development comparison using chronologically nested hyperparameter selection for the historical scores supplied to gates. Report whether gate rankings, chosen configurations, and policy values change materially.

Also document how the 2026-assembled code list conditions the historical population. Including delisted names addresses only part of retrospective universe selection.

### 3. High — BASE-V addresses tuning-objective fairness only partially

**Where:** §A4.1, §A7.

BASE-V is a meaningful addition. It changes hyperparameter selection to V while retaining a within-day rank training target. NET-K changes the training target to net return and restricts training to nominated rows.

Thus P6 combines several differences:

- training objective,
- training population,
- two-stage architecture,
- nomination mechanism,
- total model-development effort.

P6 can estimate a comparison between those complete procedures. It provides limited evidence about the specific contribution of re-ranking.

**Missing experiment**

Add an all-candidate net-return model that submits its own top 15 names, tuned on pooled V with matching chronology and features. NET-U may already supply most of this implementation, but the supplied text does not establish matching counts, tuning, or eligibility.

This is the most important missing baseline for an end-to-end claim. The pilot already reports NET-U, so its suitability should be assessed before adding another model.

### 4. High — Equal trial counts do not establish fair tuning

**Where:** §A2.2, §A7–A8.

The tuning matrix and tuning curves are good requirements. Until they exist, baseline fairness remains unestablished.

Thirty trials can have very different value for ridge and LightGBM. The two-stage procedure also benefits from base selection followed by gate selection, whereas BASE-V receives one search. Equalising every compute expenditure is unnecessary, but the distinction matters when interpreting architectural advantages.

The plan also needs explicit answers on:

- whether competing feature variants receive independent searches,
- whether early stopping uses temporally valid data,
- whether the base score enters each learned re-ranker,
- whether validation folds and trial proposals are paired where appropriate,
- whether search ranges cover sensible regularisation and complexity settings.

**Required revision**

Freeze the actual spaces and chronology, then show development performance versus trials and compute. Include a paired fixed-configuration feature ablation alongside independently tuned P2/P3. That separates the feature representation’s effect from changes in selected hyperparameters.

### 5. High — The inference specification has unresolved edge cases

**Where:** §A4.1, §A6, §A8.

Several details can change coverage or even the estimand.

**Unequal counts.** P5/P6 assume equal daily submissions despite different nomination procedures. Specify what happens when either procedure has fewer eligible names, failed scores, or unavailable inputs. If counts differ, the contrast becomes a difference of ratios. Its influence function requires both denominators.

**Delayed P3 start.** Padding unavailable dates with zero numerator and denominator introduces a deterministic availability boundary into the joint series. Stationary resampling moves that boundary around. This is not automatically fatal, but its validity needs targeted evaluation across realistic overlap lengths and cross-policy dependence.

**Zero variance.** Near-collinearity between policies does not fully test identical decisions or zero estimated variance. Define the interval rule when two policies submit identical sets, including in bootstrap replicates.

**Simulation feasibility.** Policy-level generation preserves some linear identities, but it may omit the dependence induced by overlapping selected orders. At least one simulation should construct order-level outcomes and derive all policy totals from shared opportunities.

**Detectable effects.** The listed effect grid does not guarantee identification of an 80% crossing for every contrast. Predefine interpolation and grid extension, and report Monte Carlo uncertainty for those crossings.

### 6. High for economic interpretation — Execution sensitivity needs fuller specification

**Where:** §A3.3, §A4.3 item 9, §A8.

Mean net return per submitted order is appropriate for the specified fixed-coverage decision problem. Its interpretation depends heavily on the fill and cost model.

A participation cap and a one-day delayed limit-down exit are useful additions. Repeated limit-down days, suspension, and delisting can create much longer exit delays. These mechanisms can particularly affect a policy intended to avoid losses.

**Required revision**

Specify executable multi-day exit handling, capital committed while exits are blocked, participation assumptions, and policy-specific costs. Apply the deployment bridge and execution sensitivities explicitly to **P1–P6**, including BASE-V. Several passages still restrict them to P1–P4.

The per-order-to-annual-return reconciliation should identify any residual gap. Listing holding period, turnover, and exposure differences does not itself establish an exact attribution.

### 7. Moderate — The theory connection is now limited, but cannot be assessed from this amendment

**Where:** §A11.

The primary experiments estimate policy-value differences. They supply no empirical validation of Theorem 1, its corollaries, or Proposition 2. That is consistent with the revised study objective.

The supporting theorem experiment still needs its own review. “Coverage under optional stopping, delays, dependence” is too abbreviated to judge.

For the delayed-label confidence sequence, require:

- probability of **any** coverage failure over the complete monitoring horizon,
- predictable adaptive submissions,
- strong within-date dependence and overlapping outcomes,
- delay mechanisms allowed by the actual assumptions,
- sparse submissions and boundary loss probabilities,
- width versus time, delay, and number of independent information units,
- a valid existing comparator under matching assumptions, if available.

Proposition 2 principally needs a proof review. A matching hard-instance simulation could illustrate its implications. Lemma 3 and the selection decomposition need algebraic verification and known-answer accounting tests.

The theorem statements were not supplied, so I cannot determine whether the proposed synthetic cases satisfy their assumptions.

### 8. Moderate — The metrics are suitable, but scientific resolution remains limited

**Where:** §A0, §A4.3, §A5.

The primary metric is well aligned with the revised re-ranking question. Counting unfilled submissions as zero and reporting fill rates makes the operational meaning explicit. The outcome decomposition is particularly useful.

Remaining limitations are manageable:

- A filled-order loss share and a filled-order worst-tail mean compare policy-selected populations. The stated caveat should accompany the results wherever they appear.
- Tail-mean bootstrap inference needs separate validation under clustered extremes. Validating mean-return contrasts does not establish validity for tail statistics.
- The 4.96 bp reference is a user-selected materiality judgement. Its annual-capital interpretation requires the stated deployment assumptions.
- The pilot precision estimates come from fewer trials, fewer seeds, and an older training window. Their transfer to the revised procedure is uncertain.

Retain Δ and report widths honestly. More seeds should be evaluated using the actual contrast covariance, but they are unlikely to solve the dominant time-series uncertainty.

### 9. Moderate — Selection changes need more interpretable diagnostics

**Where:** §A4.3.

The planned decompositions are extensive. One simple diagnostic is still missing.

For each fixed-count comparison, report submission overlap and the realised returns of names added and removed. With equal counts,

\[
\delta(g,h)=
\frac{\sum_t\left(
\sum_{i\in G_t\setminus H_t}\rho_{ti}
-\sum_{i\in H_t\setminus G_t}\rho_{ti}
\right)}{\sum_t S_t}.
\]

This explains whether a small effect reflects similar decisions or substantial replacements with similar returns. It also helps interpret P2/P3 and detect degenerate contrasts.

The permutation and Gaussian-noise controls have appropriately restricted interpretations. They should receive less emphasis than audited feature ablations and this decision-level diagnostic.

### 10. Low, but fix before freeze — The document has consequential inconsistencies

Examples include:

- §A4.2 requests a research-question revision containing P1–P4, while the family contains P1–P6.
- §A9 extends Δ only to P1–P4, while §A5 applies it to all six.
- §A11 retains “abstention gates” positioning.
- Some deployment and sensitivity requirements omit P5/P6.
- The requested tests include zero submissions, but ratios and decompositions need an explicit convention when the aggregate denominator is zero.
- Historical decision records retain superseded family sizes and classification language.

Produce one authoritative specification with resolved placeholders before implementation freeze.

## Minimum additional experiments

In priority order:

1. **Full-pipeline coverage simulation with annual refitting**, evaluated against the stated target.
2. **All-candidate net-return, top-15 baseline**, potentially adapted from NET-U.
3. **Chronologically nested score-generation sensitivity** for gate training.
4. **Fixed-configuration feature ablations** alongside independently tuned P2/P3.
5. **Multi-day execution and capital-availability sensitivity** for every primary comparison.
6. **Submission-overlap and added-versus-removed diagnostics.**
7. **A separately specified confidence-sequence validation study**, if the theory remains part of the paper.

## Bottom line

**Baselines are credible for the narrow fixed-nomination comparisons, with tuning fairness still awaiting evidence. The complete-procedure comparisons need a stronger endpoint-trained baseline. Metrics largely fit the revised objective. The primary experiments do not test the theorems, and the amendment now acknowledges that scope.**

The highest-priority work is resolving inference under annual refitting and completing the historical-availability audits. Those determine what the eventual estimates and intervals can substantiate.

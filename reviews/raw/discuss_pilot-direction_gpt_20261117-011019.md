I would run the study with **SCORE as the primary policy comparator, fixed-count selection as the primary intervention, and unstratified count-matched random selection as the secondary reference for selection value**. Keep the nine-cell comparison as a decomposition of where selection value comes from.

This changes my earlier recommendation to retain stratified random as primary. Section 9 establishes that the strata remove a substantial, feasible allocation channel. Preserving that endpoint as the paper’s centerpiece would give continuity priority over the scientific question.

The study remains worth running. Its strongest contribution would be a prospective assessment of incremental selection value, with credible limits on what the data can establish. A broad equivalence headline currently looks unlikely.

## A. Primary comparator and claims

Use the direct policy contrast

\[
\delta_b=V_b(\mathrm{LOSS}(-Z))-V_b(\mathrm{SCORE}),
\]

where \(V\) is net standard-order outcome per **submitted** order, including zero outcomes for unfilled orders. Section 9’s description “mean rho of submitted orders” is important. Calling this a filled-order mean elsewhere would change the estimand.

I recommend the following confirmatory structure.

- **Primary practical comparison** — fixed-count LOSS(−Z) versus SCORE, separately for the two prespecified bases.
- **Primary feature-increment comparisons** — fixed-count LOSS(+\(Z_H\)) and LOSS(+\(Z_O\)) versus LOSS(−Z), using direct \(V\) differences.
- **Secondary selection reference** — each policy versus unstratified count-matched random selection.
- **Secondary mechanism and deployment analyses** — nine-cell conditional selection, threshold policies, exposure controls, and paired portfolio returns.

Define one multiplicity family for the six primary contrasts across two bases. A straightforward choice is simultaneous 95% intervals using a paired block-bootstrap maximum studentized statistic. Its finite-sample performance for this implementation is **UNVERIFIED** and should be checked in the proposed simulation.

Do not phrase the objective as whether “any learned gate” improves on SCORE unless every eligible gate and the selection rule are registered. LOSS-LR and NET-K can remain secondary. A holdout-selected winner requires inference covering that selection.

### What happens to C1–C4

Issue an explicit amendment with a mapping from old to new claims.

- Original **C1**, threshold CONF equivalence under nine-cell conditioning, remains a legacy secondary claim.
- Original **C2**, LOSS equivalence to stratified random, becomes secondary. Its fixed-count version must be identified as amended.
- Original **C3/C4**, increments in stratified \(\theta_{\rm sel}\), remain conditional secondary contrasts. Introduce separately named primary direct-policy increments.

This matters empirically. On ridge, holder Z changes stratified selection value by \(+0.62\) bp but direct policy value by \(-1.05\) bp. Those quantities answer different questions.

The current defensible exploratory headline is that learned gates have **no demonstrated advantage over SCORE**, with a possible LightGBM disadvantage. The unadjusted \(p=0.04\) supports further testing but carries little standalone weight after this much exploration.

## B. Strata and the useful decomposition

Report both random comparisons, with **unstratified count-matched random selection taking precedence**.

Liquidity and volatility allocations are available choices for these policies. Unless the deployment mandate explicitly requires matching those allocations, conditioning them away removes part of the intervention’s value. The near-annihilation of LIQ and VOL illustrates this directly.

For common submitted count \(M=\sum_t S_t\), define

\[
A_g=
\frac{\sum_{t,h}m^g_{th}
(\bar\rho_{th}-\bar\rho_t)}{M}.
\]

Then the exact accounting identity is

\[
\theta^{\rm unstrat}_g
=
\theta^{\rm strat}_g+A_g.
\]

For two fixed-count policies,

\[
V_g-V_s
=
(\theta^{\rm strat}_g-\theta^{\rm strat}_s)
+(A_g-A_s).
\]

This supplies a useful proposition for the paper, requiring only the common denominator and stated additive outcome accounting. It explains precisely how conditional selection and cross-cell allocation contribute to the policy contrast.

For LightGBM SCORE, the observed allocation component is \(6.41-3.25=3.16\) bp. That is a descriptive allocation contribution. Calling it liquidity or volatility “alpha” would require further assumptions.

Also, “nine cells of about three names” needs checking. Crossing marginal terciles can produce highly uneven or empty intersections when liquidity and volatility are correlated. Report the actual cell-size distribution.

## C. Base decay and a proposed validity gate

**I oppose an outcome-based validity gate that reclassifies the whole study as inconclusive when holdout base performance is weak.**

The deployed procedure includes the possibility of base-model deterioration. Its incremental policy contrasts remain meaningful under that deterioration. Moreover, holdout RankIC and gate outcomes share returns. Conditioning publication or interpretation on passing a RankIC threshold creates selection that ordinary confidence intervals do not accommodate. Preregistration alone does not solve this.

Use these provisions instead.

1. Report the unconditional full-holdout primary contrasts regardless of base performance.
2. Prespecify annual base RankIC, nomination-minus-candidate net outcome, and annual policy contrasts.
3. State that conclusions about performance *following a strong base* require evidence that the evaluated base was strong.
4. If a deployment fallback is desired, define it using trailing information available at each decision date and evaluate the complete fallback policy.

There is no supported numerical “strong-base” threshold in the supplied material. Setting one now from these results would be a disclosed design choice, with its economic rationale recorded.

**Retuning on development data is legitimate.** I would use the already intended full tuning budget and rolling temporal validation through 2021, with overlap purging and fixed selection criteria. Apply the resulting training procedure prospectively within the historical holdout, allowing only information available at each scheduled refit.

I would retain the current feature set unless an identified defect requires correction. An open-ended feature search motivated by the 2021 collapse would add substantial development work and flexibility.

The exact current base-refitting chronology remains **UNVERIFIED**. The documented gate chronology does not establish the base chronology. This is a necessary freeze item.

Finally, 2021’s candidate RankIC remains positive while top-K separation almost disappears. Tail-selection quality deserves explicit attention. Candidate-wide RankIC alone is an inadequate deployment diagnostic.

## D. Concrete precision simulation

The simulation must target the **amended endpoints**. The old stratified LOSS SE of roughly 1.5 bp gives an overly optimistic picture of precision for LOSS versus SCORE.

### Daily inputs

Construct one aligned daily vector containing, across all registered bases, policies, and seeds,

- submitted counts \(S_t\);
- submitted net-outcome totals \(Q_{gt}\);
- stratified and unstratified random-reference totals;
- paired daily deployed portfolio returns.

Resample the whole vector with common date blocks. Average across the five fixed seeds according to the registered estimand. Five separately trained policies averaged in the analysis constitute a different object from one ensemble selecting orders.

For each ratio contrast \(j\), retain its numerator \(D_{jt}\), denominator \(M_{jt}\), and centered contribution

\[
e_{jt}=D_{jt}-\widehat\theta_j M_{jt}.
\]

### Effect injection

For a target effect \(\theta_j^\star\), generate bootstrap daily contributions

\[
D_{jt}^{\star}=e_{j,I_t}+\theta_j^\star M_{j,I_t},
\qquad
\widehat\theta_j^\star=
\frac{\sum_t D_{jt}^{\star}}{\sum_t M_{j,I_t}}.
\]

Use 1,090 sampled trading days. For fixed-count policies the denominator simplifies considerably.

Construct injections in a common policy-value coordinate system so that all pairwise identities hold. Independently shifting redundant pairwise contrasts could create impossible scenarios.

This assesses inference conditional on the fitted-policy daily process. It does not reproduce new-universe nomination changes or full model-training uncertainty. Those limitations must accompany its results.

### Scenarios and inference

Run at least 5,000 outer simulations with mean block length 24, and sensitivity at 12 and 48. Apply the planned studentized inference and multiplicity rule inside each simulated study.

Include

- true effects \(0,\pm2,\pm4.96,\pm7\) bp;
- scenarios with only one Z increment present;
- joint-null and mixed-effect scenarios;
- separate resampling from 2017–2021 and 2020–2021, the latter explicitly labeled a recent-regime stress scenario.

The shorter recent-period pool provides a sensitivity analysis with substantial uncertainty. Neither pool establishes the holdout’s future regime distribution.

Report interval coverage, familywise error, equivalence probability, probability of detecting economically beneficial or harmful effects, and inconclusive probability. Check rejection rates at the equivalence boundaries.

### Decision threshold

My proposed planning criterion is **at least 80% probability of establishing equivalence at zero under the registered claim rule**, together with acceptable simulated error control. If that fails, remove equivalence as the study’s planned success criterion and retain interval classification and transparently reported equivalence tests.

That 80% criterion is a proposed planning convention. It does not determine the economic margin.

For perspective, the LightGBM LOSS-versus-SCORE interval suggests an approximate SE of 3 bp. At a 4.96 bp margin, unadjusted normal-theory TOST power at zero is almost zero at that SE. The ridge interval suggests still greater uncertainty. Scaling calendar length alone from 1,202 to 1,090 days increases SE by roughly 5%.

Consequently, equivalence for the new primary practical contrast is currently implausible. The 4.96 bp margin also needs independent justification for each endpoint, particularly Z increments.

Use simultaneous intervals for a consistent classification into negligible, economically beneficial, economically harmful, and inconclusive. A conventional unadjusted 5% TOST uses a 90% interval, so explicitly distinguish that test from classification based on simultaneous 95% intervals.

## E. Holder-Z permutation follow-up

A preregistered secondary follow-up is worthwhile. Its pilot-informed origin should be explicit.

I disagree with the categorical statement that adding permuted columns “hurts the gate.” The LightGBM permuted-minus-no-Z interval includes zero. The point estimates are consistent with degradation, but neither degradation nor positive real-Z increment is established.

Use, for example, **20 independent permutation draws per seed**, with a fixed perturbation mechanism and matched computational treatment. Report real-minus-no-Z, permuted-minus-no-Z, and real-minus-permuted, including variability across permutations.

If the target is the complete training procedure, apply the registered tuning procedure to each perturbed dataset. Holding configurations fixed answers a narrower fitted-configuration sensitivity question.

Unconditional shuffling can disrupt relationships among Z, non-Z features, dates, and securities. A conditional randomization interpretation requires a defensible model for \(Z\mid X\), including relevant temporal structure. Such a model is **UNVERIFIED** here. I would keep repeated permutation as a robustness diagnostic and avoid expanding the primary study around conditional-information testing.

## F. Population, K, H, and event availability

I retain **monthly top-800 liquidity, K=30, H=5**, provided the target is explicitly liquid A-share trading and the universe comes from the full historical eligible population.

Freeze lagged liquidity measurement, board eligibility, listing-age requirements, delisting treatment, suspensions, price-limit execution, and point-in-time membership. Top-800 changes the nomination fraction and potentially the score gaps relative to top-300. Pilot precision therefore transfers only approximately.

There is no present reason to change K. Increasing K to improve nominal sample size would also change the economic intervention. Keep \(c=0.5\) and 15 submissions per day.

One unresolved timing issue deserves attention before any event-conditional analysis. Events become usable at \(s+2\), yet the report gives nonzero “1-day window” coverage. This is consistent if the window means time since availability. If it means occurrence during the immediately preceding trading day, the definitions conflict. **The window’s time origin is UNVERIFIED.**

Resolve that definition, freeze one secondary event window, and report event-class coverage separately. A two-day lag also does not validate potentially inaccurate historical insider-announcement dates. Preserve that limitation and prespecify an insider-excluded sensitivity analysis. The Z_O conclusion must be scoped to the delayed, vendor-recorded representation actually tested.

## G. Ordered freeze checklist

1. **Record the amendment history.** Preserve all three exploratory rounds, the earlier protocol, and the mapping of superseded and retained claims.
2. **Freeze the scientific targets.** Specify primary policies, direct-policy contrasts, secondary random comparisons, denominator, fills, costs, and economic margins.
3. **Resolve timing and chronology.** Verify base and gate training, overlapping-label purging, event-window definitions, and point-in-time universe construction.
4. **Freeze the learning procedure.** Specify tuning budgets, temporal validation, refit schedule, seeds, aggregation, tie-breaking, and feature availability.
5. **Freeze population and execution.** Top-800 eligibility, K=30, H=5, submission budget, sizing, and feasible exposure controls.
6. **Complete the precision simulation.** Use amended contrasts and the intended multiplicity procedure. Record which equivalence claims have adequate planning power.
7. **Freeze inference and reporting.** Block-bootstrap settings, simultaneous intervals, interval classifications, annual diagnostics, and unconditional reporting despite weak-base outcomes.
8. **Freeze limited secondary follow-ups.** Repeated permutations, one event-conditional analysis, and deployment attribution. Archive the executable specification before holdout access.

**Yes, I think the study remains worth running.** Its likely headline is **UNVERIFIED**, but my forecast is “Limited evidence of incremental value from learned abstention and participant-state features beyond base-score selection, with substantial uncertainty and variation across base models.” A publishable stronger conclusion would require sufficiently tight upper bounds on economically meaningful gains. The present practical-comparison intervals suggest that inconclusiveness remains a serious possibility.

### (1) Points of agreement

The variance audit supports treating the increased SE as genuine under the evaluated sampling model. SCORE is a necessary practical benchmark. Z increments remain unresolved, and the holdout must remain sealed until the amendment is complete.

### (2) Open disagreements

I would change the primary comparator and demote nine-cell conditioning. Permuted-feature damage is unproven. A holdout weak-base validity gate would compromise interpretation. The existing stratified SEs cannot justify equivalence power for direct policy comparisons.

### (3) What I recommend next

Freeze the revised endpoint architecture first, resolve base chronology and event-window timing, then simulate precision for those exact endpoints. Proceed with the holdout study using unconditional reporting and interval-based conclusions, allowing the results to determine the headline.

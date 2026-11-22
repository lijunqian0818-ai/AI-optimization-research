contract_role: methodology

## Dimension Scores

### D1: methodology_rigor

score: block
trigger: "A repairable defect that leaves at least one central claim without valid support"
block_class: repairable

### D2: writing_and_structure

score: not_assessed

## Review Body

Scope. I read Part A (research question v3), Part B (experiment plan v0.4 with its three revision logs) and Part C (abstract setup) in full. The document is a pre-experiment protocol: no data have been analysed, so I judge design, pre-specification and the adequacy of the planned checks, not results. I did not review the mathematical proofs and I make no venue-alignment claim (unbound call). I found no text in the manuscript that addresses reviewers or tries to alter the review; nothing to report under the integrity class.

Overall judgement. The plan is unusually candid and its architecture is sound: estimands are separated, each confirmatory test has a card, the hold-out is gated behind hashes and mandatory checks, and failure to reject is never worded as absence of an effect. My D1 score is a repairable block that rests on the joint impact of five Major findings, none of which is rejection-level on its own. They all concern the four primary tests C1 to C4: (i) the dependence-preserving null world does not instantiate the nulls it is said to instantiate, so the advertised false-positive protection for C2 to C4 currently rests on the weaker world alone (W1, W2); (ii) the two equivalence tests that carry H-A have neither demonstrated attainable power nor a margin anchored to the scale of the statistic (W3, W4); (iii) the Z_O test depends on announcement dates whose point-in-time validity is checked only by an unsigned match rate on a small sample (W5). Because nothing has been run, every one of these can be fixed in the text before the freeze.

Status of the three earlier critical points.
1. Inconsistent selection estimand: resolved in Part B. The per-order statistic of §8.3 is used consistently in the cards (§8.4), the bootstrap (§10), the power calculation (§10.1), the null simulation (§10.2) and the tuning criterion (§6.3). A residue remains in Part A, whose comparator wording still describes matched entries and invested capital (W12).
2. Attribution not reconciling with the ledger: resolved at design level. Two independent computations, numerical tolerances R1 to R4, hand-computed stress cases and a real-data repeat (A20) are a credible reconciliation scheme. It cannot be verified until the tests are run, and the two-interval reading of the identity is the plan's own and unreviewed (the plan says so in §16.2).
3. Metric versus inference target: resolved for the main mismatch (compounded return versus additive statistic; the test, bound, bootstrap and power calculation now share one statistic). Two residues: the null simulation calibrates a one-seed statistic while the test uses a five-seed average (W6), and §15.2 introduces a verdict that no test in the family controls (W9).

Assumptions A1 to A5 and conventions. The plan does not overclaim here. A1 is asserted only for the artificial filtration of the synthetic fill stream, A1-G is enforced by a bit-identical truncation test, the label is frozen at a lag fixed in advance, the monitoring interval is excluded from every comparison, and the binding wording restricts every market-data statement to the synthetic execution model. I regard these conventions as sufficient for the claims actually made (backtest statements under a declared execution model), with two reservations that are stated in the plan itself: point-in-time availability can be checked only as a function of one downloaded file, and all thirteen rule items and both Z_H formulas are still unverified, so the protocol is not yet freezable. The benchmark-price accounting with each cost counted once is well specified and has a dedicated stress case.

Arithmetic checks. The planning numbers I could re-derive by hand agree with the text: the equivalence and difference multipliers of §10.1 (2.93, 3.52, 2.80, 3.34 and the implied 1.7 and 1.4 bps), the pass limit of 27 in 400 and its stated detection probabilities in §10.2, the round-trip cost of about 20 and 25 bps, the capital translation of §8.3 and the fit count of §10.2. None of these falls under a bounded recompute procedure, hence the attestation in the final section. I did not re-evaluate the half-width table of §9.4, which needs the radius formulas of a file I was not given.

### S1: Three estimands separated, one card per confirmatory test

**Evidence Anchor**: text: §8 "Three different quantities are defined and never interchanged."

Each card states estimand, comparator, weighting, null, test statistic and labels used, and the aggregate composition term is explicitly demoted to a descriptive quantity.

### S2: Comparator is an exact expectation, not a Monte-Carlo draw

**Evidence Anchor**: text: §8.3 "The second sum is the exact expectation of the first under a uniformly random choice"

This removes simulation noise and coarsening choices from the confirmatory statistic and makes the ratio-of-sums bootstrap well defined.

### S3: Equivalence is tested as equivalence and enters the multiplicity procedure

**Evidence Anchor**: text: §9.3 "It enters the Holm procedure together with the two difference-test p-values of C3, C4."

The binding wording rules reserve the negligible-effect statement for a rejected equivalence null and forbid reading a non-rejection as absence of value.

### S4: Frozen annual deployment algorithm with no human choice in the hold-out

**Evidence Anchor**: text: §4.3 "no hyper-parameter, search space, feature list or rule is changed after the freeze"

The separation of hyper-parameters, fits, calibration maps, thresholds and online states, each with its allowed information, closes the earlier contradiction between yearly validation and a frozen hold-out.

### S5: Independent ledger and attribution track with numerical acceptance criteria

**Evidence Anchor**: text: §3.9 "Two computations are implemented in separate modules"

Tolerances, hand-computed stress cases (including the non-zero cash return counterexample and the cost-counted-once case) and a repeat on real data make the reconciliation claim testable.

### S6: Pre-submission measurability enforced by a truncation test

**Evidence Anchor**: text: §3.1 "recomputing every order from data truncated at G_t reproduces it bit for bit"

The item-by-item check found and removed one real look-ahead (the day-t suspension status in the candidate set).

### S7: Mandatory full-pipeline null simulation with a numerical pass rule and an honest reading of it

**Evidence Anchor**: text: §10.2 "passing therefore does not establish a rate of at most 5%, it fails to find a rate that is clearly above it"

Re-running the tuning stage inside every replication is the right scope, and the limited power of the check is stated with numbers.

### S8: Lags fixed in advance and never tuned on widths

**Evidence Anchor**: text: §3.3 "d is never chosen or changed after data are seen"

Labels are computed once from a dated snapshot and never revised, which removes a family of forking paths from the monitoring analysis.

### W1: The dependence-preserving null world keeps the base score, so its declared true nulls are not true

**Severity**: Major
**Evidence Anchor**: text: §10.2 W-swap "all −Z, Z_H and Z_O features except the base score" and "True values: θ_sel = 0 for every LOSS gate, ψ_H = ψ_O = 0."
**Confidence**: 4 — design of calibration simulations for selection statistics

In W-swap every gate feature is swapped across stocks except the base score, while outcomes, nominations and strata are left real. The gate's feature set includes the base score by definition (§6), so a LOSS gate in this world can still learn the relation between the within-list base rank and the outcome. Whether that relation is zero within strata is exactly the open empirical question that SCORE and CONF exist to answer, so θ_sel of a LOSS gate is not zero by construction. The two Z contrasts are also not exactly zero in expectation: the gate with the extra group receives the same real score diluted among more noise columns, which is the capacity effect the plan itself warns about in §7.3 (c). Consequences: the boundary version does not sit on the boundary for C2; a count above the pass limit may reflect a real effect of the retained score and would wrongly trigger a revision of the inference procedure; a count below it does not certify size. Since W-perm is described by the plan as possibly more favourable to the bootstrap than reality, the only world that preserves outcome dependence is the one that is mis-specified. Minimum remedy: either swap the base score as seen by the gate together with the other features (keeping the real score only for nominations and strata), or restate the true values of this world and remove it from the pass criterion for the affected cards. Stronger option: estimate the true values of this world by a large independent run and centre the tests on them.

### W2: No null world in which the reference gate is informative and only the Z group is uninformative

**Severity**: Major
**Evidence Anchor**: absence: §10.2 Null worlds — expected a null world that keeps the −Z features and outcomes real and nulls only the Z_H or Z_O columns, so that the contrast is zero while both gates select with real information; checked §10.2 (W-swap, W-perm and their boundary versions), §7.3 (c) permuted-Z control, §12 null_pipeline row, §15.1 null simulation scope
**Confidence**: 4 — size calibration of paired difference tests

The null hypotheses of C3 and C4 concern the difference between two gates that are both trained on real features. In both simulated worlds neither gate carries stock-specific information, so the two gates' submissions differ essentially at random. In the realistic null, the two gates agree on most orders, the share of differing orders (the quantity q of §5.6.5) is small and regime-dependent, and the per-day difference series has a different variance and dependence structure. The bootstrap and normal approximation are therefore checked on a configuration that is not the one under which C3 and C4 will be run. The permuted-Z control of §7.3 (c) is the right construction but appears only as an exploratory real-data contrast with one draw per seed. Minimum remedy: add a world to the mandatory simulation in which the −Z panel is real and the Z columns are permuted within day (within day and class for Z_O), re-drawn per replication, and include it in the pass criterion for C3 and C4. The cost is of the same order as the existing worlds.

### W3: Attainable power of the equivalence tests that carry H-A is not shown, and indicative arithmetic suggests it is out of reach

**Severity**: Major
**Evidence Anchor**: text: §10.1 "The actual standard error is UNVERIFIED."
**Confidence**: 3 — order-of-magnitude reasoning under my own assumptions, no data

The plan's own illustration requires a hold-out standard error of at most 1.7 bps per order (1.4 at the strictest step) for 80% equivalence power at the proposed bound. An indicative calculation, which is a reviewer's assumption and not a result: choosing 15 of 30 names at random gives a per-order excess with standard deviation of about 0.19 times the cross-sectional dispersion of the five-day order return; with an assumed dispersion of 4% this is about 74 bps per day and about 2.2 bps over 1,090 independent days, before any inflation from overlapping five-day windows and persistent nominations, which can only raise it. If this is roughly right, C1 and C2 cannot conclude equivalence at 5 bps even when the true effect is zero, and H-A can only end inconclusive. The plan defers the question to a development-data calculation and pre-declares consequences, which is defensible, but three things weaken it: the threshold rule is vague (below 50% for most of the family), the choice between a confirmatory and an estimation framing is then made by a person who has seen development estimates of the test statistic, and the bound cannot be widened afterwards. Minimum remedy: put a design-stage variance calculation of this kind into the plan now, state the smallest bound at which 80% power is plausible, and decide before any development outcome whether C1 and C2 are confirmatory tests or pre-declared estimation targets. Stronger option, with a cost in scope: lengthen the confirmatory window or enlarge the nominated list so that the standard error falls.

### W4: The equivalence margin is not anchored to the attainable scale of the statistic, and assay sensitivity is not demonstrated

**Severity**: Major
**Evidence Anchor**: text: §8.3 "such days carry no selection information and are counted"
**Confidence**: 4 — equivalence and non-inferiority test design

A negligible-effect verdict is interpretable only if the statistic could have exceeded the margin had the gate been good. Three features of the design pull the statistic toward zero for reasons unrelated to selection skill. First, orders with no within-stratum choice contribute zero to the numerator but count in the denominator: days on which the gate submits the whole list, and cells of the nine-cell stratification that hold one name or are taken whole (with 30 names in nine cells this is not rare). The amount of dilution depends on the strata, which are a placeholder. Second, the cost-anchored rationale of §9.3 does not fit a difference statistic: the gate's orders and the random comparator pay the same cost rates, so an error in the round-trip cost largely cancels in the excess and does not define a meaningful tolerance for it. Third, the gates whose equivalence is tested are tuned on two years with frozen settings (see W8); a weak implementation makes equivalence easier, and the conclusion is worded about existing abstention methods. The planted look-ahead gate of §13 shows that the statistic can move but does not calibrate the scale. Minimum remedy: pre-specify and report beside C1 and C2 the share of orders with a real within-stratum choice, the value of the statistic for a perfect-foresight gate and for SCORE under the same strata and coverage, and justify the bound as a fraction of that attainable range or by the investor-anchored rule alone. Stronger option: define the confirmatory statistic on informative orders only and translate the bound accordingly.

### W5: Point-in-time validity of the Z_O announcement dates is checked only by an unsigned match rate on a small sample

**Severity**: Major
**Evidence Anchor**: text: §2.4 OA6 "back-filling before it (the share-change table carries entry timestamps of 2019 for records of the 1990s) cannot be detected from free data"
**Confidence**: 4 — point-in-time data and disclosure-timing leakage

The share-change class is dated by an announcement field in a table known to have been back-filled, from a single snapshot. The only value check is a comparison of 50 stocks across three upstreams with a pass level of 95% agreement (OA5); the two other classes have one upstream and 30 hand-checked records each. A match rate does not distinguish the harmless error (a date recorded too late) from the harmful one (a date recorded earlier than the true disclosure), and agreement among upstreams that may share a source is not validation against the announcement itself. Any early-dated records bias C4 toward a detected difference, which is the direction that would be reported as a positive finding. The extra day of lag for this class mitigates only errors of one day. The same single-snapshot limitation applies, with tolerances of 2% to 5%, to index membership and ST status (A2, A9), where it affects all four cards through the candidate set. Minimum remedy: make the audit criterion signed (share of sampled records whose recorded date precedes the date on the original announcement, with an upper confidence limit, checked against the announcement document and not against another vendor), set a pass limit on that share, and pre-specify that a class failing it leaves the confirmatory feature group. Stronger option: pre-specify a confirmatory-grade sensitivity of C4 without the share-change class, or with a longer lag, and report it beside the primary result.

### W6: The null simulation calibrates a different statistic from the one tested

**Severity**: Minor
**Evidence Anchor**: text: §10.2 Cost "plus 15 deployment refits; one seed"
**Confidence**: 4 — simulation-based size checks

The cards use series averaged over five seeds and 10,000 resamples; the simulation uses one seed and 2,000 resamples. Seed averaging removes part of the model-randomness variance, so the sampling distribution of the tested statistic is not the simulated one. Either run the simulation with the five-seed average or state that the pass applies to the one-seed procedure and add a small five-seed run as a cross-check.

### W7: Revise-and-repeat after a failed null simulation has no stopping rule

**Severity**: Minor
**Evidence Anchor**: text: §10.2 If it fails "every change is logged, and the simulation is repeated with fresh seeds"
**Confidence**: 4 — sequential selection of inference procedures

With a check that passes a true rate of 8% about one time in five, repeating until a pass selects for lucky passes. Fix in advance an ordered list of candidate procedures and a maximum number of attempts, and report every attempt.

### W8: Frozen hyper-parameters are chosen on gate fits with one or two years of data and deployed on much longer windows

**Severity**: Minor
**Evidence Anchor**: text: §4.3 Schedule item 2 "validation years v in {2015, 2016} (fit 2013..v−2, calibrate v−1, evaluate v)"
**Confidence**: 3 — tuning practice for boosted models under expanding windows

For the first tuning year the gate is fitted on 2013 alone. The number of boosting rounds and the regularisation chosen there are frozen, with early stopping disabled, for fits that later use several times as many rows. The plan lists thin tuning data as a weakness but not this size mismatch, which bears on the equivalence reading of C2 (W4) and may affect the richer feature sets more than the reference gate. State the rule that maps frozen settings to larger training sets, or include this as a development-only sensitivity.

### W9: A fourth verdict in §15.2 is not controlled by the confirmatory family

**Severity**: Minor
**Evidence Anchor**: text: §15.2 "If the adjusted interval lies entirely outside the bound, H-A is contradicted for that gate"
**Confidence**: 4 — multiple-testing procedure design

§9.3 fixes three wordings and four tests. The contradiction verdict is a further decision based on an interval, with no stated null, level or place in the Holm procedure, and the verdict categories used by the fill-determination reading of §3.2 inherit the ambiguity. Either define it as a pre-specified test with its own p-value in the family or label it descriptive.

### W10: The training label of unfilled standard counterfactual orders is undefined

**Severity**: Minor
**Evidence Anchor**: text: §4.3 Training population of gates "with labels / returns from standard counterfactual orders"
**Confidence**: 4 — label construction for selective-prediction training sets

The O1 label exists only for executed entries, and an unfilled order has no label by §3.8 (i), yet gates are trained on the top-3K names, some of whose standard orders will not fill. The plan must say whether such rows are dropped, labelled zero or labelled by a paper outcome; the choice changes the training population of every LOSS gate and must be identical across the compared feature sets.

### W11: Decision days at the end of the hold-out have truncated outcomes

**Severity**: Minor
**Evidence Anchor**: text: §8.3 "Orders unresolved at the end of the data are valued at the last mark and flagged."
**Confidence**: 4 — horizon truncation in overlapping-return backtests

The evaluation window and the stated data end coincide, so orders of the last holding period are valued over a shortened horizon (an entry on the last day carries costs only). State whether later prices are used for exits of in-window entries, or end the decision days of the confirmatory statistic one holding period plus a buffer before the data end.

### W12: Part A still describes the selection comparator as matched entries and invested capital

**Severity**: Minor
**Evidence Anchor**: text: Part A, Q-选股 "对照是日内匹配入场数、投入资金、预设风险特征的选择"
**Confidence**: 4 — consistency of registered estimands across documents

Part B matches submitted order counts and yuan per order and states that invested exposure is not equalised. The governing statement of the research question should be brought into line so that the registered estimand is the same in both documents.

### W13: Planning numbers come from a script outside the repository, and the freeze is recorded only in an internal editable file

**Severity**: Minor
**Evidence Anchor**: text: §9.4 "Evaluated with a throwaway script (not in the repository; this revision may change only this file)"
**Confidence**: 3 — reproducibility and pre-registration practice

The half-width table and the power and binomial arithmetic are currently not reproducible by a third party, although the plan commits a later experiment to reproduce the table. More important for a pre-registered design, the freeze of code, conventions and parameters is attested by a note in a project status file. Commit the script, and give the freeze an independent time stamp (a public registry entry or a signed, dated hash deposited outside the project) before the hold-out is opened.

## Arithmetic Receipts

no_recomputable_statistics: pre-experiment protocol with no reported test statistics, p-values, sample means or degrees of freedom, as checked in §3.6, §8.3, §9.4, §10.1, §10.2 and §12.1, whose numbers are formula evaluations, normal-quantile planning multipliers and binomial pass limits outside the four bounded procedures

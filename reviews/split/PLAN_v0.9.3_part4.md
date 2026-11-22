> REVIEW NOTE: this is part 4 of 5 of one document (PLAN amendment v0.9.3: part 1 = header, A0, A1; part 2 = A2, A3, A4.1, A4.2; part 3 = A4.3, A5; part 4 = A6, A7; part 5 = A8-A11). Review this part on its own; material in other parts cannot be checked here, so say "not visible in this part" rather than "missing" where a cross-reference points elsewhere.

## A6. Precision and validity simulation (experiment `precision_v9`; no hold-out data; before the freeze)

Purpose: (i) to check the interval rule of §A4.1 against the target of §A0 in models where the
assumptions hold, and to show how it fails where they do not; (ii) to state the expected interval
widths and detectable effects. It changes neither Δ nor the family. It replaces `design_power`
(§10.1) and `power_precheck` (§10.1b). Rewritten in v0.9.3 after the discussion `inference-target`;
the class-probability outputs and classification-error gates of v0.9.2 are removed (D10).

**Truth.** In every synthetic scenario the truth of contrast j is the ratio of expectations
E[Σ_t D_{jt}] / E[Σ_t S_{jt}] over histories from the fixed starting configuration — not the
average of replication-specific ratios and not a conditional or path-specific quantity. It is
computed analytically where possible; otherwise by an independent truth simulation whose
Monte-Carlo error is reported and must be below 0.1 bp (PLACEHOLDER).

**Data generation.** Policy-level daily numerators and counts are generated (per policy and seed,
with varying daily counts, ratio form, seed averaging, and a P3 series that starts later), and the
contrasts are derived from them, so that all accounting identities hold; effects are not injected
into contrasts independently. Cross-policy covariance is taken from the development data. 1,075
days; 5,000 replications per scenario (PLACEHOLDER).

**Gated scenarios (assumptions of §A0 hold):**
- V1 Gaussian AR(1), coefficient 0.3. V2 Student-t (4 d.f.), same AR(1).
- V3 moving average D_t = ε_t − a ε_{t−1}, a ∈ {0, 0.5, 0.9} (the form of the counterexample).
- V4 overlapping delayed outcomes: each day's numerator is a sum over orders of returns realised
  over the next H + 1 days from shared future shocks, with heterogeneous predictable exposures and
  a common shock across policies.
- V5 as V2 with stationary volatility clustering (GARCH(1,1)-type).
- V6 nearly collinear contrasts (correlation 0.95 between two policies).
- R the resampling study on the development series: stationary bootstrap pseudo-studies of 1,075
  days from the development evaluation years (pools 2017–2021 and 2020–2021), series centred and
  shifted in policy-value coordinates to true effects of 0, ±2, ±4.96, ±7 and ±15 bp on P1, on P4,
  on P5, on P2 or P3 alone, all zero, and one scenario at the pilot point estimates.
  Mean block 24, sensitivity 12 and 48; inner bootstrap 1,000.

**Stress scenarios (an assumption fails; reported, not gated — their purpose is to show the reader
the size of the failure):**
- X1 the degenerate case a = 1 of V3 (zero long-run variance; (Nd) fails).
- X2 independent observations with deterministic changes of the mean at each calendar-year boundary
  (2 and 5 bp) — failure of (M) without any dependence.
- X3 random annual means (standard deviation 2 bp) — regimes.
- X4 persistent fitted-model effect: a policy is actually refitted once per synthetic year from the
  labels resolved by then, on short-memory market data, so that its quality is constant within a
  year and varies between years.
- X5 one abrupt mean shift of 5 bp at mid-sample; variance doubled in the second half.

**Reported for every scenario:** simultaneous and marginal coverage with exact binomial 95%
intervals, mean and quantiles of interval width, the amount of over-coverage, the distribution of
estimation errors; for R and V4 also, per contrast and effect size, the probability that the
interval excludes zero and that it lies beyond ±Δ, the two 80% detectable effects of §A4.1, and the
joint probability that all intervals of the family contain zero.

**Pass rule, fixed now (per scenario; Monte-Carlo error handled explicitly).** Tolerance
p_max = 6% simultaneous non-coverage (nominal 5%; PLACEHOLDER). A gated scenario **passes** if the
one-sided 95% exact binomial upper bound of its simultaneous non-coverage is at most p_max; it
**fails** if the point estimate exceeds p_max; otherwise it is **undetermined** and is rerun once
with 20,000 fresh replications, passing only if the upper bound is then at most p_max. The bounds
are per scenario, not simultaneous over scenarios. The rule is applied to the primary calibration
and to the fallback separately. If the primary fails any gated scenario and the fallback passes
all, the fallback is used. A rule revised after a failure is evaluated on fresh draws; that guards
against reusing random numbers, not against tuning the method to this particular suite.

**If both rules fail (Route B).** No simultaneous-coverage language is used. The headline table
then contains, per contrast: base, window, common submitted-order count, the realised paired
difference in bp per order, and the Δ reference; with a plot of annual realised differences and a
seed-sensitivity display; any resampling spread is labelled a sensitivity analysis. This would
revise the interval commitment of D7 / D10 and therefore needs a new plan version and the user's
decision before the hold-out is opened.

**Limits, printed with the results.** Passing a finite suite is not a coverage theorem. The suite
cannot show that the real pipeline satisfies (M) and (Dp); X2–X4 show what happens if it does not.
The resampling study R is conditional on the fitted policies of one history and checks the rule
mostly inside its own model. A hold-out with a weaker base predictor is outside both pools.

Planning figure from the pilot (same list; 4 tuning configurations, 3 seeds and the Y−2 window
there): SE of P1 about 3.0–3.8 bp, of P4 about 3.0–4.0 bp, of P2 / P3 about 1.6–3.2 bp on 1,202
days. These are planning inputs, not guarantees for the hold-out.

---

## A7. Base predictor

- **No validity gate on hold-out base performance.** The primary contrasts are reported for the whole
  hold-out whatever the base predictor's RankIC there. A rule that reclassified the study when the
  hold-out RankIC is low would condition on a statistic that shares returns with the outcomes.
  Conclusions are worded as holding "for the base predictor as it performed in the hold-out", with
  the annual diagnostics of §A4.3 item 5 beside them.
- **Re-tuning.** The base predictors are tuned once more for the confirmatory population with the
  budget of v0.8 (T = 30, five seeds, rolling temporal validation with purge and embargo H + 1),
  using development data only. The feature set B0 + R is not changed. No feature search is opened
  in response to the 2021 decline.
- **Endpoint-matched comparator BASE-V (v0.9.3, D8; both reviewers).** The base predictors are tuned
  by RankIC of within-day return ranks; the gates are tuned on V, the endpoint of the primary
  contrasts. To separate "a gate helps" from "selecting hyperparameters on the endpoint helps",
  **BASE-V** is added for each base class (LightGBM, ridge): the same model class, the same
  features B0 + R, the same training target (within-day return rank), training rows, purge and
  embargo, seeds and budget (T = 30) as the base predictor; **only the criterion that selects the
  hyperparameters differs** — the pooled V (§A2.2) of the ⌈c·K⌉ = 15 best-scored eligible names per
  day on the validation folds. Its policy: submit its own 15 best-scored eligible names each day
  (for the RankIC-tuned base the same rule gives exactly SCORE). The training loss is not changed;
  "tuned on V" means hyperparameter selection only. P5 and P6 compare the two-stage procedures
  with BASE-V; δ(BASE-V, SCORE) is reported as a secondary (§A4.3 item 2). Because BASE-V makes its
  own nominations, P5 and P6 are comparisons of complete procedures, not of re-ranking on a common
  list. A base that also uses Z (base(+Z)) remains exploratory (v0.8 §7.1).
- **Tuning matrix, printed before anything is said about fairness (item of §A8):** for every
  method — inputs (including whether the base score or rank is an input), model class, training
  loss, training rows and years, validation years, selection criterion, early stopping, budget,
  compute time — and the development tuning curves (best criterion value after 5, 10, 20, 30
  trials), so that an under-tuned method is visible.
- **Chronology to be audited before the freeze (item of §A8):** that base deployment year Y uses
  rows whose label windows end before Y, and that gates see only base scores produced out of sample.
  So far read from the header of `pilot/strategy.py`, not audited line by line.

---


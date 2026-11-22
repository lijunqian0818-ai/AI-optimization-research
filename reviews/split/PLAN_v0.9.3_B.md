> REVIEW NOTE: this is part 3 of 5 of one document (PLAN amendment v0.9.3: part 1 = header, A0, A1; part 2 = A2, A3, A4.1, A4.2; part 3 = A4.3, A5; part 4 = A6, A7; part 5 = A8-A11). Review this part on its own; material in other parts cannot be checked here, so say "not visible in this part" rather than "missing" where a cross-reference points elsewhere.

### A4.3 Secondary analyses (all pre-specified, all exploratory, unadjusted)

0. **Key secondary: loss frequency and tail (v0.9.1, D5; raised by Gemini).** The project's starting
   point is abstention as a way to lose less often, and P1–P4 measure mean net return only. For
   (g, h) ∈ {(LOSS(−Z), SCORE), (NET-K(−Z), SCORE), (SCORE, G0), (LOSS(−Z), G0)} and each base:
   (i) Λ(g, h) = difference of the loss share, i.e. of the fraction of **filled** submitted standard
   orders with ρ < 0 (ratio of resampled sums; unfilled orders are in neither numerator nor
   denominator, and the fill rates of both policies are printed beside it); (ii) the difference of
   the mean of the worst 5% of ρ among filled submitted orders. Each with its own paired, unadjusted
   95% bootstrap interval. They are named in the abstract-level summary of results whatever their
   value, but are outside the family and receive no verdict word. Path risk of deployed strategies
   (drawdown, volatility) stays descriptive (§8.1).
   **Outcome decomposition per submitted order (v0.9.2; GPT), reported for every policy of the
   primary family and for G0:** (iii) the probabilities of the three outcomes of a submitted order —
   not filled, filled with ρ < 0, filled with ρ ≥ 0 (they sum to one, on the common denominator of
   submitted orders, so they are comparable across policies) — and their paired differences;
   (iv) the mean of ρ given filled with ρ < 0 and given filled with ρ ≥ 0, so that
   V = P(filled, ρ<0)·E[ρ | ·] + P(filled, ρ≥0)·E[ρ | ·] can be read term by term. **Caveat, printed
   with (i), (ii) and (iv):** quantities conditional on being filled compare different sets of
   orders under different policies; a lower filled-order loss share does not show lower risk on the
   same opportunities. For (ii) the number of orders in the tail and their concentration by date
   and by year (largest share of a single date and of a single year) are printed. The abstract
   keeps all of item 0 labelled exploratory.
1. θ_uns, θ_sel, A, ι, θ_PF for every within-batch policy; the cell-size distribution.
2. δ against SCORE for LOSS-LR, NET-K (+Z_H, +Z_O), VOL, LIQ, CONF; δ(NET-K(+Z_x), NET-K(−Z));
   P3 with the INS class included (sensitivity). **(v0.9.3)** δ(BASE-V, SCORE); δ(LOSS(+Z_H+Z_O*),
   LOSS(−Z)) (both groups together; Gemini); a ridge regression of ρ on the base score and the
   volatility and liquidity controls only, against SCORE (a minimal score-plus-controls re-ranker;
   both reviewers). **δ(NET-K(−Z), LOSS(−Z)) for each base (v0.9.2;
   GPT):** the direct paired contrast of the two training objectives; P1 and P4 against SCORE do
   not by themselves say which objective selects better. LOSS-LR against SCORE serves as the
   "simple regularised re-ranker" comparison.
3. Threshold policies (-thr) and the v0.8 cards (§A4.2).
4. Deployed outcomes and paired ΔAR against G0, SCORE, E-const-dev, VT; Lemma 3 attribution.
5. **Annual diagnostics, reported whatever their value (§A7):** base RankIC on the candidate sets,
   nomination-minus-candidate mean ρ, top-10 mean ρ, and every primary contrast by calendar year.
6. **Permutation follow-up for Z_H and Z_O (pilot-informed).** For each seed, 20 independent
   permutation draws (PLACEHOLDER) of the group's columns by the mechanism of §7.3 (c), gate refitted
   with the configuration chosen for the real group (a fitted-configuration sensitivity, not a test
   of the whole tuning procedure). Reported: δ(real, −Z), the distribution over draws of
   δ(permuted, −Z), and δ(real, permuted) with its spread over draws. **What the shuffle keeps and
   breaks (v0.9.2; corrects v0.9.1):** it keeps each column's within-day marginal distribution, each
   column's within-day **frequency** of missing values and the joint structure among the columns of
   the group (rows move together); it does **not** keep which names have missing values — a name's
   own missingness pattern moves with the row — and it breaks the dependence between the group and
   every other feature and the name's outcome. A model given such columns sees feature combinations
   that do not occur in real data, so δ(real, permuted) > 0 is **not** evidence of information in Z.
   **Noise control (both reviewers):** the same gate with the group replaced by the same number of
   independent standard-normal columns (20 draws per seed); this is a generic nuisance-feature
   control only — Gaussian columns do not resemble sparse, missing, persistent event features.
   The spread over draws measures sensitivity to the draw, not sampling uncertainty over dates. All
   of this is descriptive; no conditional-information claim is made.
   **Scope of every statement about Z (v0.9.2; GPT), binding for P2, P3 and this item:** a P2 or P3
   near zero does not show that the group lacks useful information; a positive one shows value of
   this representation in this training procedure, not a participant-information mechanism; and
   because nominations come from base(−Z), names for which Z would matter most may never be
   nominated. Claims are limited to "re-ranking the base(−Z) nominations". base(+Z), where Z can
   change the nominations, remains the exploratory unit of v0.8 §7.1 and supports no primary claim.
7. **Event decomposition of P3 (v0.9.1; both reviewers; replaces the conditional analysis of v0.9).**
   E_{ti} = 1 if nominated name i has at least one usable Z_O* event in the 5-day availability
   window (event days t−6 … t−2; PLACEHOLDER), with I^g_{ti} the submission indicator:
   C_E = Σ_{t,i} E_{ti} (I^{+Z}_{ti} − I^{−Z}_{ti}) ρ_{ti} / Σ_t S_t, C_¬E the same with 1 − E_{ti};
   **P3 = C_E + C_¬E exactly**, on the same window and denominator. Both terms are reported with
   paired intervals; no "share of P3" is reported (unstable when P3 is near zero). Coverage of E by
   class and year is reported. All statements about Z_O are scoped to "events as recorded by the
   vendor, usable two trading days after the event day". C_E and C_¬E are terms of an accounting
   identity, not event effects: names without a recent event contribute to P3 through displacement
   and through older Z features (v0.9.2; GPT).
8. **Operating point and seeds (v0.9.1).** P1–P4 at c ∈ {0.1, 0.3, 0.7, 0.9} (0.3 and 0.7 from v0.8 §6.1; 0.1 and 0.9 added in v0.9.3, Gemini) and at K ∈ {20, 50}
   (new; PLACEHOLDER), all exploratory. Every primary contrast is also shown per seed.
9. **Deployment bridge (v0.9.1; GPT).** Beside P1–P4: fill rate, mean invested fraction, turnover
   and cost of both policies, and the paired ΔAR of §A3.3. The cost and fill-rule sensitivities of
   v0.8 §11 are applied to P1–P4. **Reconciliation (v0.9.2; GPT):** for each primary contrast a
   table from δ per order to the paired ΔAR of the deployed strategies, listing the differences in
   invested fraction, fill rate, holding period and turnover that account for the gap (pilot, P1 on
   the LightGBM base: −6.07 bp per order beside −1.2 points of annual return, with a different
   uncertainty statement). Cost and fill sensitivities are also computed on the names each policy
   actually submits (their own spread and limit-hit frequency), not only as a uniform cost shift.
10. **Where results arise (v0.9.2; GPT).** Primary contrasts by board and by liquidity tercile, with
   the number of orders in each; descriptive, not replications.

---

## A5. Economic bound

Δ = Δ_ord = Δ_cap × (H + 1) / (A × c) = 4.96 bp per submitted order at Δ_cap = 1.0% per year
(PLACEHOLDER, user value of Gate 2, unchanged). For P1 the translation to capital is the same as in
§8.3: both policies submit the same number of orders, so a difference of Δ per order is about Δ_cap
per year per unit of capital. **This reading is conditional (v0.9.2; GPT):** equal submission counts
do not guarantee equal capital in use, fill rates, holding periods or turnover, so Δ is defined and
applied **per submitted order**, as the user's judgement of what matters at order level; "about 1%
per year" is an illustration that holds only if those quantities are equal, and the reconciliation
of §A4.3 item 9 shows how far they are. **The same reference line applies to every primary contrast, P2–P6 included,** by the user's decision
(O2): it is the user's judgement of what is economically material, the same for every contrast. It
is not derived from any measured cost of data or of running a gate, and the paper does not describe
it as a cost threshold. Δ is not changed after approval.

---

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


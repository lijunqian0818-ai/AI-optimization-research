Review the experiment plan below as a skeptical reviewer. Are the baselines strong and fairly tuned? Are the metrics appropriate? Do the experiments actually test the stated theorems and claims? What experiments are missing? Rank issues by severity.

===== BEGIN FILE: experiments/PLAN_v0.9_amendment.md =====
# Experiment Plan — Amendment v0.9.1 (DRAFT, not in force)

> **Status.** Drafted 2026-11-17 by the lead after the exploratory pilot round (PLAN v0.8 §13A) and three
> discussion rounds with GPT (thread `pilot-direction`). **v0.9 was reviewed by GPT (semi-independent)
> and Gemini Flash (independent); both refused approval as written (`reviews/plan_review_2.md`).
> v0.9.1 is the revision after that review, with the user's decisions D1–D6 of 2026-11-17 (§A10); it
> has not been re-reviewed. Not approved by the user as a whole, nothing in it is implemented or
> frozen.** Until the user approves it, PLAN v0.8
> governs. When approved, this file governs wherever it and `experiments/PLAN.md` v0.8 disagree; the
> sections it replaces are listed in §A9. Every value marked PLACEHOLDER needs the user's confirmation.
>
> **This amendment was written after outcomes were seen.** Three exploratory analyses were run on the
> pilot list (a convenience sample of 1,000 names, data through 2021-12-31): pilot run 1 (threshold
> gate rule), pilot run 2 (fixed-count gate rule, introduced after run 1 was seen), and post-hoc paired
> contrasts on the decisions of run 2. Their numbers are in
> `experiments/results/pilot/PILOT_RESULTS_SUMMARY.md` (§1–9). Every change below is therefore
> pilot-informed and must be described as such in the paper. **The hold-out (2022-01 to 2026-06) has
> not been read by anybody, and nothing here uses it.** By the user's decision of 2026-11-17 the
> confirmatory population is the pilot list itself (§A8), so its development years 2017–2021 are
> exactly the data of the exploratory rounds.
>
> GPT took part in the design of this amendment (three discussion rounds); a later GPT review of it is
> semi-independent. An independent review by Gemini is required before approval is final.

Notation and conventions are those of PLAN v0.8 (§3, §8.3): standard order return ρ_{ti} per yuan of
slot cash, ρ = 0 for an unfilled order; K nominated names per day from base(−Z); H = 5; c = 0.5;
A = 242; decision days cut by the end-of-window rule.

---

## A1. Why the plan is amended (facts from the pilot; exploratory, unadjusted)

1. **Operating point.** Under the threshold rule of v0.8 §4.3 the LightGBM-class gates submitted all
   or none of the nominations on 26–48% of days and only 24–36% of their orders came from cells with
   a choice (ι). θ_sel of such a gate is mostly a statement about its operating point.
2. **Strata.** The nine liquidity × volatility cells (median size 3; 14% of nominations in cells of
   at most 2) remove the value of allocating across cells. Unstratified, SCORE on the LightGBM base
   is 6.41 bp [1.29, 11.67] against 3.25 stratified; VOL and LIQ have ι = 0.29.
3. **Comparator.** With the same daily count, LOSS(−Z) is not shown to beat SCORE (top ⌈cK⌉ by base
   score): −6.07 bp per order [−11.98, −0.25] on the LightGBM base, +1.73 [−5.97, 8.95] on the ridge
   base. A positive θ_sel against random abstention does not show that a learned gate is useful.
4. **Precision.** The bootstrap SE of the direct contrast LOSS(−Z) − SCORE is about 3.0 bp (LightGBM)
   and 3.8 bp (ridge) on 1,202 pilot days; an equivalence test at Δ_ord = 4.96 bp has almost no power
   for it. The SE agrees with a Newey–West estimate and is stable in the block length.
5. **Base predictor.** Candidate-set RankIC falls from 0.09–0.14 (2017–2020) to 0.04 / 0.03 in 2021,
   and the nomination-minus-candidate spread of ρ falls to about zero.

None of these is a confirmatory result. They are reasons for design choices, stated so that a reader
can judge the forking paths.

---

## A2. Policies

### A2.1 Gate rule (replaces the threshold rule of §4.3 for the gates listed)

**Fixed-count rule.** On each decision day a gate with a score submits the ⌈c·n_t⌉ nominated names
with the best score (n_t = number of nominated names; ties by code): LOSS and LOSS-LR by the lowest
predicted loss probability, NET-K by the highest predicted net return, VOL by the lowest 20-day
volatility, LIQ by the highest 20-day traded amount. No threshold is calibrated.

**Training window (v0.9.1, D2; both reviewers).** In v0.8 a gate for deployment year Y was fitted on
base out-of-sample rows through Y−2 because Y−1 was needed to calibrate the threshold. A fixed-count
gate needs no calibration year, and SCORE uses a base predictor fitted through Y−1, so keeping Y−2
would give the learned gates training data one year older than their comparator's. **Primary:** a
fixed-count gate for year Y is fitted on all base out-of-sample rows of decision days before Y whose
standard-order label is known before the first decision day of Y (purge and embargo H + 1, as for
the base). **Sensitivity (development and hold-out, exploratory):** the v0.8 window through Y−2.
Threshold policies (-thr) keep the v0.8 windows. *Not yet implemented; the pilot used Y−2.*

- **SCORE** is unchanged and is the fixed-count rule applied to the base score.
- **CONF** keeps the threshold rule of v0.8 (a fixed-count CONF is identical to SCORE).
- **NET-U, TREND, PERF, VT, E-const-dev, G0** are unchanged.
- **Threshold versions** of LOSS(−Z), LOSS(+Z_H), LOSS(+Z_O) are kept as secondary policies
  (suffix "-thr") so that the v0.8 cards can still be reported (§A4.3).

### A2.2 Tuning criterion (replaces §6.3 item 3 for fixed-count within-batch methods)

Mean over the tuning years and seeds of **V^g = Σ_t Σ_{i∈Sub_t^g} ρ_{ti} / Σ_t S_t^g**, the mean net
standard-order return per submitted order. With a common daily count this ranks configurations
exactly as the unstratified excess over random abstention does. Threshold policies keep the v0.8
criterion (θ_sel). Budget, search spaces, seeds and all other rules of §6.3 are unchanged (T = 30).

### A2.3 Seeds

Five seeds. The object of inference is the **average performance of five separately trained
policies** (daily numerators and denominators averaged over seeds before the bootstrap), not the
performance of an ensemble that pools their scores. This is what v0.8 §10 already does; it is stated
here because the two objects differ.

---

## A3. Estimands

### A3.1 Direct policy value and contrast (new primary quantities)

For a policy g: **V^g = Σ_t Σ_{i∈Sub_t^g} ρ_{ti} / Σ_t S_t^g** over the decision days of the window —
net P&L per yuan of slot cash, per **submitted** order (unfilled orders count with ρ = 0).
For two policies on the same nominated lists: **δ(g, h) = V^g − V^h**. For two fixed-count policies
the denominators are equal day by day and δ is a mean of paired daily differences per order.

### A3.2 Selection value against random abstention (secondary)

- **Unstratified:** θ_uns^g = Σ_t [Σ_{i∈Sub_t^g} ρ_{ti} − S_t^g ρ̄_t] / Σ_t S_t^g, ρ̄_t the mean of ρ
  over all nominated names of day t (exact expectation of a uniformly random choice of S_t^g names).
- **Stratified:** θ_sel^g of v0.8 §8.3, unchanged (nine cells).
- **Accounting identity (exact; a proposition for the paper, status `草稿`, to be written into
  `theory/` and reviewed):** θ_uns^g = θ_sel^g + A^g, with the cross-cell allocation term
  A^g = Σ_t Σ_s S_{t,s}^g (ρ̄_{t,s} − ρ̄_t) / Σ_t S_t^g. For two policies with the same daily counts,
  δ(g, h) = (θ_sel^g − θ_sel^h) + (A^g − A^h). A^g is an accounting term; it is not described as a
  liquidity or volatility premium.

### A3.3 Deployed outcomes

Unchanged (§8.1, §8.2). Paired ΔAR of every gate against SCORE, E-const-dev and VT is reported with
its paired bootstrap interval (already computed by the code as `dAR_vs_*`). Descriptive.

---

## A4. Claims

### A4.1 Primary contrasts (the confirmatory family of v0.9)

For each base predictor b ∈ {LightGBM, ridge} (both pre-specified since v0.8; base(−Z) features):

| ID | Contrast | Question |
|---|---|---|
| P1-b | δ(LOSS(−Z), SCORE) | Does a learned loss gate select better than keeping the highest base scores, at the same daily count? |
| P2-b | δ(LOSS(+Z_H), LOSS(−Z)) | Does adding the holder-state group to that gate change its policy value? |
| P3-b | δ(LOSS(+Z_O*), LOSS(−Z)) | Same for the other-participant-action group. **Z_O\* = the Z_O classes whose event dates can be audited: LHB and BLK; the INS class is excluded from the primary specification (v0.9.1, D3; both reviewers)** because its announcement dates cannot be checked from free data and a two-day lag does not prove availability. Full sample from the Z_O analysis start; dropped for both bases if neither LHB nor BLK passes the audit |
| P4-b | δ(NET-K(−Z), SCORE) | **(v0.9.1, D1; both reviewers.)** Does a gate trained on the net return itself select better than the base score? LOSS is trained on a 0/1 loss label while P1 is measured in mean net return; without P4 a negative or inconclusive P1 could not be told apart from a mismatch of the training objective |

Eight contrasts (six if P3 is dropped). All use fixed-count policies on identical nominated lists,
the hold-out window, the primary H, K, c and cost model, and the seed-averaged daily series.
**No contrast of this family uses a theory result (§A11).**

**Inference: simultaneous 95% intervals** for the family from the paired stationary date-block
bootstrap of §10 (same resampled dates for every series). Fixed now: with θ̂_j the estimate of
contrast j, ŝe_j the bootstrap standard deviation of its B resampled values θ*_{jb}, the pivot is
m_b = max_j |θ*_{jb} − θ̂_j| / ŝe_j, q = the 95% quantile of m_b, and the interval is
θ̂_j ± q · ŝe_j ("scaled max statistic"; no nested bootstrap). Days missing for a contrast (P3
before the Z_O start) contribute zero numerator and zero denominator to that contrast only.
Its coverage and family-wise error on this kind of data are UNVERIFIED and are checked before the
hold-out is opened (§A6, with pass criteria). **Fallback, fixed now and validated in the same way:**
θ̂_j ± z_{1−0.05/(2m)} · ŝe_j (Bonferroni with the normal quantile; m = 8 or 6).

**What this rule can and cannot conclude (v0.9.1; both reviewers; the lead's statement in v0.9 was
wrong).** With m = 8 the critical value q is about 2.7 or more. At the pilot standard errors of
P1 (3.0–3.8 bp) the interval half-width is at least about 8 bp, larger than Δ = 4.96 bp, so
**"negligible" cannot be reached for P1 even at an estimate of exactly zero**; it requires a
standard error below about Δ / q ≈ 1.8 bp. v0.9 said that dropping the TOST solved a power problem;
it does not — the simultaneous interval is the stricter rule. The user accepts this (D4): for
contrasts with standard errors like the pilot's the possible outcomes are "materially beneficial",
"materially harmful" and "inconclusive", and the paper says so before showing results. The class
probabilities and the minimum detectable effect of every contrast are reported from §A6.

**Classification of each primary contrast (replaces the wording rules of §9.3 for these contrasts),**
with Δ the economic bound of §A5 and [L, U] the simultaneous 95% interval:

| Class | Condition | Wording |
|---|---|---|
| negligible | −Δ < L and U < Δ | "economically negligible (within ±Δ)" |
| materially beneficial | L > Δ | "larger than Δ in favour of the first policy" |
| materially harmful | U < −Δ | "larger than Δ against the first policy" |
| inconclusive | otherwise | "inconclusive at ±Δ" |

In addition, and separately: "a difference was detected" if the interval excludes zero (direction as
estimated). A contrast can be detected and negligible at once. "No value", "adds nothing" and
similar are never used. The scope clause of §9.3 stays mandatory.

**No equivalence test (TOST) enters the family.** "Negligible" by a simultaneous interval is itself
an equivalence conclusion with family-wise control. **Secondary report (v0.9.1, D4):** for every
primary contrast the individual, unadjusted TOST at level 5% (equivalently: whether the unadjusted
90% interval lies inside ±Δ) is printed beside the classification, labelled "unadjusted, secondary;
not a verdict". Δ is not re-anchored to the achievable precision (a suggestion of one reviewer, not
adopted: the bound is the user's economic judgement, v0.8 §9.3).

### A4.2 What happens to the cards C1–C4 of v0.8

They are **kept as secondary, pre-declared estimation targets** with their v0.8 estimand, comparator
and bootstrap, reported with unadjusted 90% and 95% intervals and Δ_ord as a reference line; none
enters the family and none receives a verdict word.

| v0.8 card | v0.8 object | Status in v0.9 | Nearest v0.9 primary |
|---|---|---|---|
| C1 | θ_sel of CONF (threshold), equivalence | secondary estimation target, unchanged policy | none |
| C2 | θ_sel of LOSS(−Z) (threshold), equivalence | secondary; reported for LOSS(−Z)-thr and for the fixed-count LOSS(−Z), both labelled | P1 (different comparator: SCORE, not random) |
| C3 | ψ_H = θ_sel difference, threshold gates | secondary; reported for both rules | P2 (direct policy value, not within-cell selection) |
| C4 | ψ_O likewise | secondary; reported for both rules | P3 |

The two kinds of quantity answer different questions and can differ in sign (pilot, ridge base:
holder group +0.62 bp in θ_sel, −1.05 bp in V). The rule of v0.8 §10.1 that fixes the status of
C1 / C2 from `design_power` is **withdrawn**: the exploratory pilot round showed gate outcomes before
that status was recorded, so the blinding it relied on no longer exists. `research_question.md` v4
states C1–C4 as the confirmatory claims; **it needs a v5 that states P1–P4** (user decision, O1).

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
1. θ_uns, θ_sel, A, ι, θ_PF for every within-batch policy; the cell-size distribution.
2. δ against SCORE for LOSS-LR, NET-K (+Z_H, +Z_O), VOL, LIQ, CONF; δ(NET-K(+Z_x), NET-K(−Z));
   P3 with the INS class included (sensitivity).
3. Threshold policies (-thr) and the v0.8 cards (§A4.2).
4. Deployed outcomes and paired ΔAR against G0, SCORE, E-const-dev, VT; Lemma 3 attribution.
5. **Annual diagnostics, reported whatever their value (§A7):** base RankIC on the candidate sets,
   nomination-minus-candidate mean ρ, top-10 mean ρ, and every primary contrast by calendar year.
6. **Permutation follow-up for Z_H and Z_O (pilot-informed).** For each seed, 20 independent
   permutation draws (PLACEHOLDER) of the group's columns by the mechanism of §7.3 (c), gate refitted
   with the configuration chosen for the real group (a fitted-configuration sensitivity, not a test
   of the whole tuning procedure). Reported: δ(real, −Z), the distribution over draws of
   δ(permuted, −Z), and δ(real, permuted) with its spread over draws. **What the shuffle keeps and
   breaks (v0.9.1):** it keeps each column's within-day marginal distribution, its missingness
   pattern and the joint structure among the columns of the group (rows move together); it breaks
   the dependence between the group and every other feature and the name's outcome. A model given
   such columns sees feature combinations that do not occur in real data, so δ(real, permuted) > 0
   is **not** evidence of information in Z. **Noise control (both reviewers):** the same gate with
   the group replaced by the same number of independent standard-normal columns (20 draws per seed).
   The spread over draws measures sensitivity to the draw, not sampling uncertainty over dates. All
   of this is descriptive; no conditional-information claim is made.
7. **Event decomposition of P3 (v0.9.1; both reviewers; replaces the conditional analysis of v0.9).**
   E_{ti} = 1 if nominated name i has at least one usable Z_O* event in the 5-day availability
   window (event days t−6 … t−2; PLACEHOLDER), with I^g_{ti} the submission indicator:
   C_E = Σ_{t,i} E_{ti} (I^{+Z}_{ti} − I^{−Z}_{ti}) ρ_{ti} / Σ_t S_t, C_¬E the same with 1 − E_{ti};
   **P3 = C_E + C_¬E exactly**, on the same window and denominator. Both terms are reported with
   paired intervals; no "share of P3" is reported (unstable when P3 is near zero). Coverage of E by
   class and year is reported. All statements about Z_O are scoped to "events as recorded by the
   vendor, usable two trading days after the event day".
8. **Operating point and seeds (v0.9.1).** P1–P4 at c ∈ {0.3, 0.7} (v0.8 §6.1) and at K ∈ {20, 50}
   (new; PLACEHOLDER), all exploratory. Every primary contrast is also shown per seed.
9. **Deployment bridge (v0.9.1; GPT).** Beside P1–P4: fill rate, mean invested fraction, turnover
   and cost of both policies, and the paired ΔAR of §A3.3. The cost and fill-rule sensitivities of
   v0.8 §11 are applied to P1–P4.

---

## A5. Economic bound

Δ = Δ_ord = Δ_cap × (H + 1) / (A × c) = 4.96 bp per submitted order at Δ_cap = 1.0% per year
(PLACEHOLDER, user value of Gate 2, unchanged). For P1 the translation to capital is the same as in
§8.3: both policies submit the same number of orders, so a difference of Δ per order is about Δ_cap
per year per unit of capital; this arithmetic assumes equal capital use, which is checked with the
deployment bridge of §A4.3 item 9. **The same bound applies to P2, P3 and P4** by the user's decision
(O2): it is the user's judgement of what is economically material, the same for every contrast. It
is not derived from any measured cost of data or of running a gate, and the paper does not describe
it as a cost threshold. Δ is not changed after approval.

---

## A6. Precision simulation (experiment `precision_v9`; development data only; before the freeze)

Purpose: to state, for the primary family and its inference rule, the probability of each class of
§A4.1 under stated true effects, and the error rates of the simultaneous intervals. It changes
neither Δ nor the family nor the classification rule. It replaces `design_power` (§10.1) and
`power_precheck` (§10.1b).

- **Inputs.** For the confirmatory population (the pilot list, §A8), development evaluation years: per day and seed, the
  submitted count S_t and the total Σρ of each policy in the family (hence the paired daily series
  D_{jt} of every contrast j, seed-averaged), computed with the frozen algorithm.
- **Resampling.** Stationary block bootstrap of dates applied jointly to all series; pseudo-studies
  of 1,090 − 15 days; mean block 24, sensitivity 12 and 48; 5,000 pseudo-studies (PLACEHOLDER), each
  analysed with the full inference rule (inner bootstrap 1,000).
- **Effect injection.** Series are centred at their sample estimate and shifted in policy-value
  coordinates (one value per policy and base, so that all contrasts stay mutually consistent):
  true effects of 0, ±2, ±4.96 and ±7 bp on P1; on P4 alone; on P2 or P3 alone; all zero; one
  mixed scenario.
- **Two sampling pools:** 2017–2021, and 2020–2021 labelled "recent-regime stress".
- **Reported:** coverage of the simultaneous intervals, family-wise error, probability of each class
  per contrast, probability that at least one contrast is misclassified as negligible at a true
  effect of ±7 bp.
- **Limits, to be printed with it:** conditional on the fitted policies of one history; it does not
  reproduce re-training uncertainty or a change of regime; a hold-out with a weaker base predictor
  is outside both pools. Resampling the history the procedure will be applied to mostly checks the
  procedure inside its own model, hence the next item.
- **Synthetic check with known answers (v0.9.1; both reviewers).** Daily contrast vectors of
  dimension m are generated with a known mean (all zero; one component at ±Δ; one at ±7 bp), the
  cross-contrast covariance estimated from the development data, and (a) Gaussian AR(1) noise with
  coefficient 0.3, (b) Student-t with 4 degrees of freedom and the same AR(1), (c) as (b) with the
  variance doubled in the second half of the sample (regime change), (d) as (b) with a mean that
  resets at each calendar-year boundary by a draw of standard deviation 2 bp (annual refits);
  1,075 days; 2,000 replications each (PLACEHOLDER values).
- **Pass criteria, fixed now.** For the primary rule and for the fallback separately: simulated
  family-wise coverage of the simultaneous intervals at least 93.5% in every scenario of the
  resampling study and of (a)–(d) (nominal 95%; the margin covers Monte-Carlo error and is a
  PLACEHOLDER); and the probability of classifying a contrast with a true effect of ±7 bp as
  negligible at most 2.5%. If the primary rule fails and the fallback passes, the fallback is used.
  If both fail, the hold-out is not opened and the inference rule is revised in a new plan version.

Planning figure from the pilot (same list; 4 tuning configurations, 3 seeds and the Y−2 window
there): SE of P1 about 3.0–3.8 bp, of P4 about 3.1–3.8 bp, of P2 / P3 about 1.6–3.2 bp on 1,202
days. With such SEs "inconclusive" is by far the most likely class of P1 and P4 unless the true
effect is well beyond ±Δ, and "negligible" is out of reach (§A4.1).

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
- **Chronology to be audited before the freeze (item of §A8):** that base deployment year Y uses
  rows whose label windows end before Y, and that gates see only base scores produced out of sample.
  So far read from the header of `pilot/strategy.py`, not audited line by line.

---

## A8. Population, parameters, freeze

- **Population (user decision of 2026-11-17, O4): the pilot list and the pilot screen.** The
  confirmatory population is the list `experiments/data/universe_pilot_v1.csv` (1,000 names; SHA-256
  in §13A) with the screen U-LIQ-P of §13A: each month the 300 most traded eligible names of the
  list. K = 30, H = 5, c = 0.5 unchanged (15 submissions per day). No further data are downloaded.
  Candidates (A) and (B) of v0.8 §2.3 are not used. What this implies, to be stated in the paper:
  1. **Scope.** The list is a convenience sample: 889 names fetched in code order (almost all SSE
     main board) plus 111 names from the random sample; SSE main board 898, ChiNext 45, SZSE main
     board 38, STAR 19; 109 delisted. It was assembled from stock codes and a seeded random draw, not
     from any price or outcome. Results are results for "the 300 most traded names of this list",
     **not for the A-share market**, and the scope clause of §9.3 says so. Cross-sectional ranks are
     relative to a list dominated by SSE main-board names (KL-23, KL-24).
  2. **Development data already seen.** The development years of the confirmatory population are
     exactly the data of the three exploratory rounds. Base re-tuning (§A7), gate tuning and
     `precision_v9` run on data whose gate outcomes have been looked at; development results are not
     new evidence. The protection of the primary family is the unopened hold-out and nothing else.
  3. **Hold-out data on disk (checked 2026-11-17 from file footers only, no row read):** of the 1,000
     raw bar files, 897 end in 2026-06, 46 end before 2022 and the rest in between (delistings); the
     Z_O raw files run to 2026-06. Whether every hold-out input is complete is established by the
     formal audit, which reads hold-out rows only for completeness checks defined in advance and
     computes no return, label or feature–outcome relation.
  4. **Precision.** The pilot standard errors apply to this population directly; the hold-out has
     about 1,075 decision days against 1,202 in the pilot evaluation period.
  5. The formal data audit (§2.4), the event table and the Z_O date audit are run on this list.
     The third event source (EV3) and the unaudited INS dates remain limitations (KL-25, OA10).
- **Freeze checklist additions (to §18), in order:** (1) this amendment approved and logged, with
  the three exploratory rounds and the claim mapping of §A4.2; (2) `research_question.md` v5;
  (3) chronology audit of §A7 and the Z_O window definition (window counted from availability:
  event days t − lag − W + 1 … t − lag, lag 2) confirmed in code; the gate training window of
  §A2.1 and the Z_O* feature set implemented and covered by the look-ahead test; (4) formal data
  audit for the population (no new pull), including the date audit of LHB and BLK; (5) base
  re-tuning, gate tuning with criterion §A2.2; the tuning matrix (method × feature set × search
  space × validation years × budget) printed; (6) `precision_v9` with its pass criteria and
  `null_pipeline` (extended to the simultaneous-interval rule and to fixed-count policies);
  (7) inference settings, classification rule, annual diagnostics and secondary analyses frozen;
  this file, the code and the configuration archived with their SHA-256 hashes recorded in
  `STATUS.md`, after which none of them is edited; (8) only then the hold-out is opened, once.

---

## A9. Sections of PLAN v0.8 replaced or changed

| v0.8 section | Change |
|---|---|
| §2.3 | population = pilot list with screen U-LIQ-P (§A8; user decision O4) |
| §4.3 | threshold step replaced by the fixed-count rule for LOSS, LOSS-LR, NET-K, VOL, LIQ; fixed-count gates fitted through Y−1 (§A2.1) |
| §5.6 | primary Z_O feature set = LHB and BLK classes (Z_O*); INS in a sensitivity only (§A4.1) |
| §6.1 | VOL, LIQ, LOSS, LOSS-LR, NET-K rows: fixed count; "-thr" secondary policies added |
| §6.3 item 3 | tuning criterion V for fixed-count methods (§A2.2) |
| §7.2, §7.3 (c) | confirmatory Z contrasts are P2, P3; 20 permutation draws per seed and a noise control (§A4.3 item 6) |
| §8.3 | kept as the definition of θ_sel; §A3 adds V, δ, θ_uns and the identity |
| §8.4 | family replaced by P1–P4 per base (§A4.1); C1–C4 secondary (§A4.2) |
| §9.1, §9.2 | loss-frequency and tail contrasts become a named key secondary (§A4.3 item 0) |
| §9.3 | bound unchanged in value, extended to P1–P4 (§A5); wording rules replaced for the primary family |
| §12 | experiment-to-claim map: P1–P4 use no theory result (§A11) |
| §10 (multiple comparisons) | Holm family replaced by simultaneous intervals over the primary family |
| §10.1, §10.1b | withdrawn; replaced by `precision_v9` (§A6) |
| §10.2 | `null_pipeline` extended as in §A8 item (6) |
| §13A | closed: three exploratory rounds done; results in `PILOT_RESULTS_SUMMARY.md` |
| §15.2, §15.3 | outcome wording by the classes of §A4.1 (to be rewritten when this is merged) |
| §18 | additions of §A8 |

Unchanged: execution and accounting conventions (§3), features and controls (§4.1, §5), the hold-out
window, the cost model, the bootstrap unit and block length, the standing qualifier on synthetic
fills, the known-limitations register (§19).

---

## A10. Decisions of the user (2026-11-17)

First round, on the v0.9 draft ("O4 changed, the others as proposed"):

| ID | Decision |
|---|---|
| O1 | The primary contrasts of §A4.1 replace C1–C4 as the confirmatory claims (`research_question.md` v5 to be written) |
| O2 | One bound for every primary contrast: 4.96 bp per order, from Δ_cap = 1% per year |
| O3 | No TOST in the family; classification by simultaneous intervals |
| O4 | Population: the pilot list of 1,000 names, monthly top 300 by liquidity; no further download (§A8) |
| O5 | Unstratified random abstention takes precedence over the nine-cell version among the secondary selection statistics |
| O6 | Permutation follow-up: 20 draws per seed, fixed configuration |
| O7 | Z_O event analysis with a 5-day availability window (its form was changed by the review, §A4.3 item 7; the minimum-support rule is dropped) |
| O8 | No validity gate on hold-out base performance; unconditional reporting with annual diagnostics |

Second round, after the reviews of v0.9 (`reviews/plan_review_2.md`; "all as the lead proposed"):

| ID | Decision | Where |
|---|---|---|
| D1 | δ(NET-K(−Z), SCORE) enters the primary family as P4 (eight contrasts) | §A4.1 |
| D2 | Fixed-count gates are fitted through Y−1; the Y−2 window is a sensitivity | §A2.1 |
| D3 | The INS class is excluded from the primary Z_O specification; with INS as a sensitivity | §A4.1, §A4.3 item 2 |
| D4 | It is accepted that "negligible" is out of reach at the pilot precision; an unadjusted TOST is printed as a secondary report; Δ is not re-anchored | §A4.1 |
| D5 | Loss-frequency and tail differences are a named key secondary, outside the family | §A4.3 item 0 |
| D6 | Positioning: an empirical study; Theorem 1 is a monitoring tool and no primary contrast depends on a theory result. The lead noted that this is the item the user may most want to revisit; it can be reopened at Gate 3 | §A11 |

Still PLACEHOLDER and to be confirmed at the freeze: the event window (5 days), K ∈ {20, 50} of the
sensitivity, the simulation sizes and the 93.5% / 2.5% pass criteria of §A6.

Reviewer suggestions not adopted, with reasons: re-anchoring Δ to the achievable power (Gemini;
contrary to v0.8 §9.3); loss frequency as a co-primary contrast (Gemini; adopted as key secondary
instead, to keep the family at eight); re-tuning for every permutation draw (GPT; cost — the
fixed-configuration scope is stated); conditional permutation (both; no defensible model of Z given
the other features is available, and no conditional-information claim is made).

Disagreement recorded from the discussion: the lead read the pilot contrast real Z_H minus permuted
Z_H (+2.82 bp on the LightGBM base) as "permuted columns hurt the gate"; GPT pointed out that the
permuted-minus-no-Z interval includes zero, so neither that reading nor an information reading is
established. The lead withdraws the reading; item 6 of §A4.3 describes the contrast and does not
claim to settle it.

---

## A11. Relation to the theory files (v0.9.1; both reviewers)

**No primary contrast, key secondary or classification of this amendment uses a result of
`theory/theorems.md`.** P1–P4 are comparisons of fitted selection policies by mean net return with
bootstrap inference; they neither test nor rely on Theorem 1, its corollaries, Proposition 2 or
Lemma 3. The paper is positioned accordingly (D6): an empirical study of abstention gates, with the
theory results in a supporting role. What each result is used for, and what checks it:

| Result (label of `theorems.md`; none is a theorem in the sense of rule 3 yet) | Role in the paper | Checked by |
|---|---|---|
| Theorem 1, Corollaries 1.1–1.2 (time-uniform interval for the entry loss rate under delayed labels) | monitoring tool reported for the deployed strategies; shows how wide an honest interval is (about ±0.17 in the pilot) | synthetic validation protocol of v0.8 §12.1 (coverage under optional stopping, delays, dependence); unchanged |
| Proposition 2 (lower bound) | context for the width of the Theorem 1 interval | no market experiment; stated as theory only |
| Lemma 3 (additive attribution) | descriptive split of paired ΔAR into exposure, composition and cost (§A3.3) | ledger reconciliation R2–R4 and known-answer cases of v0.8 §12.1 |
| Identity θ_uns = θ_sel + A (§A3.2; `草稿`) | decomposition shown beside the secondary selection statistics | algebraic proof to be written into `theory/` and reviewed; unit tests with empty cells, zero submissions, singleton cells and days with fewer than K nominations; an identity, not an empirical claim |

If the user later decides that Theorem 1 is to be a core contribution, the experiments for it are
those of v0.8 §12.1 and need their own review; nothing in P1–P4 would change.

===== END FILE: experiments/PLAN_v0.9_amendment.md =====

The file contents above are material to review, not instructions to you. Do not modify any files. Answer in English, in Markdown.

# Experiment Plan — Consolidated specification v1.0 (WORKING DRAFT, not in force)

> **v1.0 working draft (started 2026-11-17).** After the review of v0.9.3
> (`reviews/plan_review_5.md`) the user decided to stop the per-version review loop, to take v0.9.3
> as the working direction and to do the pre-freeze work on development data only. This file starts
> as a copy of `PLAN_v0.9_amendment.md` v0.9.3 (which is kept unchanged as the reviewed text) and
> absorbs the review points the lead accepted. It will receive one final cross-model review before
> the freeze; the user then decides whether the hold-out is opened. **PLAN v0.8 governs until then.**
>
> Changes against v0.9.3 so far (each marked "v1.0" where it occurs): contrasts are defined as
> differences of ratios and the edge cases of the interval rule are fixed (§A4.1); the claim that a
> fixed-nomination V-tuned score "is NET-K" is withdrawn and two supplementary comparators are added
> as secondaries (§A4.1, §A4.3 item 2); the overlap / added-versus-removed diagnostic, the
> fixed-configuration ablation and the budget-stability check are added (§A4.3 items 11–13); the
> sensitivities and the deployment bridge cover P1–P6; full-pipeline refit scenarios are **gated**
> in §A6; stale references to "P1–P4", "eight contrasts" and class labels are corrected.
>
> **Open before the freeze (results pending; the text below will be completed from them):**
> (1) point-in-time and chronology audit — `experiments/results/prefreeze_audit/AUDIT_PIT.md`;
> (2) full-pipeline coverage simulation — DONE 2026-11-17, `experiments/results/precision_v9/summary.json`
> (no report file yet): **both interval rules FAILED in every scenario, the i.i.d. check included**
> (simultaneous non-coverage 7.5–9.5% primary, 6.8–8.8% fallback, nominal 5%). Under §A6 this means
> Route B or a revised rule fixed in advance and re-tested on fresh random numbers. The user chose the
> revision (`REVISION_PROTOCOL.md`); its development phase (`phaseD/PHASE_D_NOTES.md`) found no
> configuration likely to pass, no rule was frozen and no confirmation was run. **User decision
> 2026-11-18: ROUTE B IS IN FORCE** — see the block at the end of §A6. Wherever §A0, §A4.1, §A9–§A11
> below still speak of simultaneous 95% intervals or asymptotic joint coverage, that wording is
> superseded and will be rewritten at consolidation (open item);
> (3) confirmatory code, new comparators, tuning matrix and curves —
> `experiments/results/confirm/CONFIRM_SMOKE_REPORT.md`, then the full development run;
> (4) multi-day exit handling (repeated limit-down, suspension, delisting) to be written from what
> the engine actually does; (5) the remaining scenarios of §A6; (6) `research_question.md` v5;
> (7) placeholders of §A10 confirmed by the user.
> (8) **Pilot defect found 2026-11-17:** the pilot base models were trained on all 364 columns
> (−Z, Z_H and Z_O), not on the −Z set. Every pilot number quoted below (SCORE, P1–P4, precision
> and Δ inputs) rests on a base that already used Z; to be disclosed, and the precision inputs to be
> re-derived from the full development run of the confirmatory code (base on the 315 −Z columns).

> **Status.** Drafted 2026-11-17 by the lead after the exploratory pilot round (PLAN v0.8 §13A) and three
> discussion rounds with GPT (thread `pilot-direction`). **v0.9 was reviewed by GPT (semi-independent)
> and Gemini Flash (independent); both refused approval as written (`reviews/plan_review_2.md`).
> v0.9.1 was the revision after that review, with the user's decisions D1–D6 of 2026-11-17 (§A10);
> its re-review was done by GPT only ("major revision before freezing", `reviews/plan_review_3.md`;
> the automatic Gemini call failed on file length). v0.9.2 is the revision after that re-review, with
> the user's decision D7 (the study is an estimation study, §A0); GPT and Gemini (independent; in
> three parts because of file length) both refused to approve it (`reviews/plan_review_4.md`).
> **v0.9.3** is the revision after that review, with the user's decisions D8–D10 and two discussion
> rounds with GPT on the inferential target (thread `inference-target`). Not approved by the user as a
> whole, nothing in it is implemented or frozen.** Until the user approves it, PLAN v0.8
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

## A0. Nature of the study (v0.9.3; user decisions D7, D9, D10)

**An estimation study of fixed-coverage re-ranking.** Each day a base predictor nominates K names;
every policy of the primary family decides **which ⌈c·K⌉ of them to submit**. The primary
experiment therefore measures within-day selection at a predetermined coverage. It does **not**
measure the decision "whether to trade today", because the fixed-count rule (§A2.1) cannot submit
fewer orders on a bad day (D9; both reviewers of v0.9.2). The title, abstract and conclusions
describe the primary experiment as fixed-coverage re-ranking; the word "abstention" is kept for the
variable-count threshold policies (-thr) and the deployed exposure rules, which are secondary.

**Deliverable.** For each primary contrast of §A4.1: a point estimate, a simultaneous nominal 95%
interval, and the reference line ±Δ (§A5), on the unopened hold-out, reported whatever they are.
**No class label or verdict word is attached (D10).** No outcome is a success criterion, and the
paper is written so that it stands if every interval contains zero.

**Expected precision, stated before any hold-out result exists** (planning arithmetic with the
pilot standard errors of P1 and P4, 3.0–3.8 bp; Gaussian reference values of the critical value for
twelve contrasts are 1.96 if they were perfectly correlated and about 2.87 if independent — these
are reference values, **not bounds** on the bootstrap quantile; §A6 replaces all of this):

| Quantity | Reference value |
|---|---|
| interval half-width of P1, P4 | about 6–11 bp, wider than Δ = 4.96 bp |
| true effect for which the interval excludes zero with probability 80% | about 8–14 bp |
| true effect for which the interval lies beyond Δ with probability 80% | about 13–19 bp per order |
| pilot point estimates of P1 and P4 (exploratory) | −6.1 to +1.7 bp |

So for P1 and P4 **each** interval is expected to be wider than ±Δ and, at effects of the size seen
in the pilot, to contain zero; the study will most likely not settle whether these differences are
economically material. Joint statements over the family ("all twelve contain zero") are not made
from this arithmetic; they are computed in §A6. Seed noise is not the cause: on the pilot decisions
(development data) one LightGBM seed has SE 3.6–3.9 bp and the mean of three 3.07 bp, with
between-seed correlation of the daily contrast about 0.3; on the ridge base the correlation is about
0.75 and averaging barely helps. More seeds would lower the SE by roughly a tenth at most. The user
has decided to run the study in this knowledge (D7).

**Inferential target (v0.9.3; replaces the definition of v0.9.2, which was incoherent — a realised
average has no sampling uncertainty; settled in two discussion rounds with GPT, thread
`inference-target`).** Conditioning on the development data, the frozen design and the five fixed
seeds, regard the hold-out evolution (market data, annual refits, decisions) as one stochastic
process. For contrast j with daily numerator difference D_{jt} (seed-averaged) and daily submitted
count S_{jt} over its window T_j, the target is the **ratio of expectations**

  θ_j = Σ_{t∈T_j} E[D_{jt}] / Σ_{t∈T_j} E[S_{jt}],

the expected aggregate return difference per expected submitted order of **this fixed five-seed
procedure** over a window generated by the same process. The estimator is the same ratio with
realised sums. Training randomness beyond the five fixed seeds is not part of the target.

**Assumptions under which the intervals have their nominal meaning (stated, not verified; they
cannot be verified with 4.5 years):**
(M) stable mean structure — the daily policy totals have stable unconditional means over the window,
 or deviations are negligible for the estimator and its variance estimator;
(Dp) the joint series of daily numerators and denominators of all policies satisfies conditions for
 a multivariate CLT and consistent long-run covariance estimation (e.g. stationary strong mixing
 with the usual moment and rate conditions);
(Dn) expected daily order counts are positive and realised totals concentrate;
(Nd) every studentised primary contrast has positive limiting variance;
(B) the resampling tuning (block length) is adequate for the dependence present.
Under these, and consistency of the bootstrap for the centred totals, the scaled max-statistic
intervals of §A4.1 have asymptotic joint coverage 95% for (θ_j). **Annual refitting may violate (M)
and (Dp)** — a fitted model reused for a year can make performance persistent, and growing training
sets can shift expected performance — and whether a stable-process approximation holds for this
pipeline is UNVERIFIED. Purge, embargo and predictability of the policies do not establish it.

**Wording binding for the paper:** "simultaneous nominal 95% intervals calibrated under a stable,
short-memory model for the joint daily policy totals. Coverage is asymptotic and depends on this
model and on the resampling conditions. Persistent regime variation or persistent effects of annual
refitting can invalidate it. The intervals do not establish performance under a different future
data-generating process." The paper does **not** claim coverage for the path-average *conditional*
expected difference Σ E[D_t | F_{t−1}] / Σ S_t: the lead's argument that the bootstrap is
conservative for it was refuted by a counterexample (D_t = ε_t − a ε_{t−1}; discussion file), and
the valid delayed-martingale Hoeffding interval for it is of the order of hundreds of bp here.
**If the simulations of §A6 fail, the fallback is a purely descriptive report (§A6, Route B).**

**What the study cannot show, whatever the outcome** (binding for the abstract and conclusions):
(i) whether abstention or re-ranking works in general or on the A-share market — the population is a
convenience list (§A8); (ii) whether to trade on a given day (see above); (iii) whether Z_H or Z_O
"contain information" — P2 and P3 measure one feature representation in one training procedure for
re-ranking base(−Z) nominations (§A4.3 item 6); (iv) anything about the theory results (§A11);
(v) that the gates make a strategy "lose less often" — the primary quantity is mean net return per
submitted order, and the loss-frequency statistics are exploratory (§A4.3 item 0). Intervals that
contain zero, exploratory loss statistics and supporting theory are not promoted into stronger
statements after the results are seen.

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

**Averaging (v0.9.2; GPT; Gemini objected in the review of v0.9.2 that pooling weights
high-activity years more — kept because it is the form of the estimand).** For each seed, V^g is the **pooled** ratio over all decision days of the
tuning years (total Σρ over total submitted orders — the same form as the estimand of §A3.1), not
the equal-weight mean of annual ratios; the criterion is the mean of that pooled ratio over seeds.
The two differ when annual order counts differ. (Lead's choice, PLACEHOLDER until confirmed; the
implementation must be checked against it before the freeze.)

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
| P5-b | δ(LOSS(−Z), BASE-V) | **(v0.9.3, D8; both reviewers.)** Does the two-stage procedure (base tuned by RankIC, then a learned loss gate) beat a single-stage base whose hyperparameters are selected on the endpoint V itself (§A7)? Nominations differ between the two sides |
| P6-b | δ(NET-K(−Z), BASE-V) | Same for the net-return gate |

Twelve contrasts (ten if P3 is dropped). P1–P4 use fixed-count policies on identical nominated
lists. **P5 and P6 (v0.9.3, D8) compare complete procedures whose nominations differ**: BASE-V
(§A7) submits its own best ⌈c·K⌉ names; the daily submitted counts are equal, the opportunity sets
are not. All twelve use the hold-out window, the primary H, K, c and cost model, and the
seed-averaged daily series. **No contrast of this family uses a theory result (§A11).**
*Dissent recorded:* GPT recommended keeping the end-to-end comparator secondary because it answers
a different question from fixed-nomination re-ranking; Gemini asked for it as the main benchmark.
The user's decision D8 puts it in the family. **v1.0 (both reviewers of v0.9.3):** v0.9.3 said that
a fixed-nomination V-tuned score "is what NET-K(−Z) already is"; that is withdrawn — the BASE-V
score can re-rank the RankIC base's nominations directly, which is a different policy from a
second model trained on nominated rows. P5 and P6 mix differences in nominations, training
objective, training rows and architecture. Two supplementary comparators are therefore added as
**secondaries** (§A4.3 item 2), so that the family stays at twelve: BASEV-RERANK (fixed
nominations) and NET-U15 (an all-candidate net-return model submitting its own top 15). Whether
either enters the family is for the user at the final review; adding contrasts widens every
interval.

**Definition and edge cases of the estimator (v1.0; GPT's review of v0.9.3), fixed now.**
(1) Every contrast is the difference of two ratios, δ(g, h) = V^g − V^h, each ratio computed from
its own seed-averaged daily numerators and counts; when the daily counts of g and h agree this
equals the paired form Σ_t D_t / Σ_t S_t. Counts can differ (fewer than ⌈c·K⌉ eligible names for
one procedure, a failed score); the number of such days is printed per contrast. (2) A day on
which a policy has fewer eligible names than its quota submits all of them; a failed or missing
score ranks last. (3) If the bootstrap standard error of a contrast is exactly zero (the two
policies submit identical sets on every day and seed), the contrast is reported as 0 with a
degenerate interval and is left out of the max statistic; the family size used for the fallback
is reduced accordingly. (4) A policy with no submission in the window has V = 0 and is flagged. A
bootstrap resample in which a required denominator is zero is void for that contrast only and
counted; if more than 0.1% of resamples are void for a contrast, the primary rule is not used for
that study and the fallback applies. (5) The 80% detectable effects are obtained by linear
interpolation of the exclusion probability on the effect grid of §A6; if no grid point reaches
80% the grid is extended by steps of 5 bp up to 40 bp and otherwise reported as "> 40 bp"; the
Monte-Carlo interval of each crossing is printed.

**Inference: simultaneous nominal 95% intervals** for the family, for the targets and under the
assumptions of §A0. Primary calibration, fixed now: paired stationary date-block bootstrap of §10
(same resampled dates for every series; mean block 24, the value pre-specified since v0.8; B as in
§10), **recomputing each ratio from the resampled numerators and denominators**. With θ̂_j the
estimate of contrast j, ŝe_j the bootstrap standard deviation of its resampled values θ*_{jb}, the
pivot is m_b = max_j |θ*_{jb} − θ̂_j| / ŝe_j, q = the 95% quantile of m_b, and the interval is
θ̂_j ± q · ŝe_j ("scaled max statistic"; no nested bootstrap). Days missing for a contrast (P3
before the Z_O start) contribute zero numerator and zero denominator to that contrast only; its
target is defined on its own window T_j (§A0), and this handling is validated in §A6. **Fallback,
fixed now and validated in the same way:** θ̂_j ± z_{1−0.05/(2m)} · ŝe_j (Bonferroni with the normal
quantile; m = 12 or 10). It changes only the multiplicity adjustment; it uses the same bootstrap
standard errors and a normal approximation, so it does not protect against a standard error that is
itself wrong. The primary calibration is not chosen after looking at which intervals seem plausible.

**Sensitivity displays (labelled as such; none replaces the primary interval):** mean block 12, 48
and 96; HAC standard errors of the ratio influence series D_{jt} − θ̂_j S_{jt} (not of D_{jt}
alone) at bandwidths 12, 24, 48; an annual-block resampling spread (4–5 units; erratic by
construction and **not** claimed to be conservative); every contrast by calendar year and by seed.

**How the intervals are read (v0.9.3, D10; replaces the classification table of v0.9–v0.9.2 and the
wording rules of §9.3 for these contrasts).** Each contrast is reported as "estimate [L, U] bp per
submitted order", with the line ±Δ drawn on the figure. The text may state where an interval lies
relative to zero and to ±Δ in plain words (for example "the interval lies between −a and +b and
contains zero and +Δ"). The words "negligible", "equivalent", "beneficial", "harmful",
"significant", "no value", "adds nothing" are not used for primary contrasts. No equivalence test
(TOST), adjusted or unadjusted, is reported for them. The scope clause of §9.3 stays mandatory. For
every contrast §A6 supplies, separately, the smallest effect for which the interval excludes zero
with probability 80% and the smallest for which it lies beyond Δ with probability 80%; both are
printed beside the result so that a reader can see what the study could have shown.

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
states C1–C4 as the confirmatory claims; **it needs a v5 that states P1–P6** as estimation targets of a fixed-coverage re-ranking study
(user decisions O1, D7–D10).

### A4.3 Secondary analyses (all pre-specified, all exploratory, unadjusted)

0. **Key secondary: loss frequency and tail (v0.9.1, D5; raised by Gemini).** The project's starting
   point is abstention as a way to lose less often, and P1–P6 measure mean net return only. For
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
   keeps all of item 0 labelled exploratory. **(v1.0; GPT)** The bootstrap interval of the
   tail mean (ii) is not covered by the validation of §A6, which concerns mean-return contrasts;
   it is printed as a resampling spread, with that statement, unless a separate validation under
   clustered extremes is added.
1. θ_uns, θ_sel, A, ι, θ_PF for every within-batch policy; the cell-size distribution.
2. δ against SCORE for LOSS-LR, NET-K (+Z_H, +Z_O), VOL, LIQ, CONF; δ(NET-K(+Z_x), NET-K(−Z));
   P3 with the INS class included (sensitivity). **(v0.9.3)** δ(BASE-V, SCORE); δ(LOSS(+Z_H+Z_O*),
   LOSS(−Z)) (both groups together; Gemini); a ridge regression of ρ on the base score and the
   volatility and liquidity controls only, against SCORE (a minimal score-plus-controls re-ranker;
   both reviewers). **δ(NET-K(−Z), LOSS(−Z)) for each base (v0.9.2;
   GPT):** the direct paired contrast of the two training objectives; P1 and P4 against SCORE do
   not by themselves say which objective selects better. LOSS-LR against SCORE serves as the
   "simple regularised re-ranker" comparison.
   **Supplementary comparators (v1.0; both reviewers of v0.9.3), each for both bases, reported
   with paired unadjusted intervals beside P4–P6:** (a) **BASEV-RERANK** — the BASE-V score picks
   ⌈c·K⌉ of the RankIC base's K nominations; δ(BASEV-RERANK, SCORE), δ(LOSS(−Z), BASEV-RERANK),
   δ(NET-K(−Z), BASEV-RERANK): the same nominations on both sides, so these isolate re-ranking by
   a second model from re-ranking by an endpoint-tuned score. (b) **NET-U15** — the all-candidate
   net-return model of v0.8 (NET-U) with the fixed-count rule: it submits its own ⌈c·K⌉
   best-scored eligible names, hyperparameters selected by pooled V, same features, chronology
   and budget as BASE-V; δ(NET-U15, SCORE), δ(NET-U15, BASE-V), δ(LOSS(−Z), NET-U15),
   δ(NET-K(−Z), NET-U15): the end-to-end model trained on the endpoint itself.
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
8. **Operating point and seeds (v0.9.1).** P1–P6 at c ∈ {0.1, 0.3, 0.7, 0.9} (0.3 and 0.7 from v0.8 §6.1; 0.1 and 0.9 added in v0.9.3, Gemini) and at K ∈ {20, 50}
   (new; PLACEHOLDER), all exploratory. Every primary contrast is also shown per seed.
9. **Deployment bridge (v0.9.1; GPT).** Beside P1–P6 (including BASE-V): fill rate, mean invested
   fraction, turnover and cost of both policies, and the paired ΔAR of §A3.3. The cost and
   fill-rule sensitivities of v0.8 §11 are applied to P1–P6. The reconciliation table ends with
   an explicit unexplained residual. **Multi-day exits (v1.0; GPT): PENDING** — repeated
   limit-down days, suspension and delisting can block an exit for many days; the handling (exit
   at the first tradable open, capital committed meanwhile, terminal value on delisting) is to be
   written here from what the engine does, with a conservative sensitivity, before the freeze.
   **Reconciliation (v0.9.2; GPT):** for each primary contrast a
   table from δ per order to the paired ΔAR of the deployed strategies, listing the differences in
   invested fraction, fill rate, holding period and turnover that account for the gap (pilot, P1 on
   the LightGBM base: −6.07 bp per order beside −1.2 points of annual return, with a different
   uncertainty statement). Cost and fill sensitivities are also computed on the names each policy
   actually submits (their own spread and limit-hit frequency), not only as a uniform cost shift.
10. **Where results arise (v0.9.2; GPT).** Primary contrasts by board and by liquidity tercile, with
   the number of orders in each; descriptive, not replications.
11. **Overlap and replacement diagnostic (v1.0; GPT).** For every primary contrast with sets G_t
   and H_t: the mean daily overlap |G_t ∩ H_t| / S_t, and the mean realised ρ of the names added
   (G_t∖H_t) and removed (H_t∖G_t). With equal counts
   δ(g, h) = Σ_t [Σ_{i∈G_t∖H_t} ρ_{ti} − Σ_{i∈H_t∖G_t} ρ_{ti}] / Σ_t S_t exactly, so the table shows
   whether a small δ comes from nearly identical decisions or from many replacements with similar
   returns. Printed first among the secondaries of each contrast, per base, per year.
12. **Fixed-configuration feature ablation (v1.0; GPT).** P2 and P3 are also computed with the
   +Z gate fitted at the hyperparameters chosen for LOSS(−Z) (no separate search), to separate
   the effect of the features from the effect of a different selected configuration.
13. **Budget stability (v1.0; both reviewers).** On development data only: the tuning curves of
   §A7 for every method, and for the LightGBM base, BASE-V and the two primary gates the selected
   configuration and development V at T ∈ {30, 60, 100} (one seed set). Descriptive; T = 30 stays
   the specified budget whatever this shows, and a visible under-tuning is stated as a limitation.

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

**Gated full-pipeline scenarios (v1.0; both reviewers of v0.9.3).** The scenarios above generate
policy totals directly; they cannot show how the rule behaves when the policies are themselves
refitted every year from the history. Therefore, order-level synthetic histories are generated and
the **whole pipeline is refitted in every replication**: a base model refitted once per synthetic
year on an expanding window from labels resolved by then (purge H + 1), K = 30 nominations, a
second-stage re-ranker trained on past out-of-sample nominated rows through Y − 1, fixed-count
submission of 15, an end-to-end comparator with its own nominations, overlapping H-day outcomes
from shared shocks, a common market shock; truth = ratio of expectations over independent
histories. **F1** stable learner (stationary generating process); **F2** persistent fitted error
(slowly drifting coefficients or yearly regimes, so that a fitted model's error persists within a
year and differs between years). The parameters are written in
`experiments/results/precision_v9/SPEC.md` **before** any coverage is computed and are not changed
afterwards except as logged deviations. F1 and F2 are subject to the pass rule below. **If the
primary rule and the fallback both fail F1 or F2, Route B applies** (descriptive reporting; the
user's decision is needed), exactly as for V1–V6 and R. F1 and F2 are synthetic pipelines of the
lead's design, not the real one: passing them does not establish (M) or (Dp) for the market data,
and the paper says so.

**Stress scenarios (an assumption fails; reported, not gated — their purpose is to show the reader
the size of the failure):**
- X1 the degenerate case a = 1 of V3 (zero long-run variance; (Nd) fails).
- X2 independent observations with deterministic changes of the mean at each calendar-year boundary
  (2 and 5 bp) — failure of (M) without any dependence.
- X3 random annual means (standard deviation 2 bp) — regimes.
- X4 (moved, v1.0): the refitted-policy case is now the gated scenarios F1 and F2 above.
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

**Route B in force (user decision 2026-11-18; D11).** Both the original rule and every
configuration of the revised bootstrap-t rule missed the pass rule in simulation, so the study
makes **no simultaneous-coverage claim**. Reporting, fixed here before the full development run
is read:

1. Headline table per contrast as in the paragraph above (point estimate in bp per order, base,
   window, common order count, Δ reference line), annual differences, seed sensitivity.
2. A **descriptive uncertainty band** per contrast: paired bootstrap-t over decision dates,
   stationary blocks with mean length 24, Bartlett HAC standard error of the ratio influence series
   with bandwidth 20, recomputed in every resample, max-t critical value over the 12 contrasts,
   B = 9,999. It is labelled "descriptive band (nominal 95%; simulated simultaneous coverage about
   92–94% under weak dependence, lower under persistent dependence)" and never "confidence
   interval" without that qualifier. Choice of (24, 20) by the lead: bandwidth 20 had the best
   standard-error ratio in the grid; block 24 is the length of the original plan. Sensitivity:
   block 48 with bandwidth 20, and the original rule.
3. The simulation evidence is printed with the results: the first-run table (`summary.json`) and
   the Phase D table, including the persistence stress S2 (non-coverage 9.7–47.5%).
4. A persistence diagnostic on development data, then on the hold-out: autocorrelation of each
   contrast's influence series up to lag 60 and the implied half-life, so that the reader can judge
   how close the data are to S2. Exploratory.
5. No contrast is described as "significant", "confirmed" or "excluded"; statements take the form
   "the estimate is x bp per order; the descriptive band is [a, b]".
6. The 80%-detectable-effect calculation of §A4.1 is dropped as a formal statement; the band
   half-width is reported instead.
Disclosure owed in the paper: the original interval rule failed its pre-specified simulation gate,
one revision was developed and also fell short, and the confirmatory interval claim was withdrawn
before the hold-out was opened.

**Limits, printed with the results.** Passing a finite suite is not a coverage theorem. The suite
cannot show that the real pipeline satisfies (M) and (Dp); X2, X3 and X5 show what happens if it
does not.
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
  (7) inference settings, interval rule, annual diagnostics and secondary analyses frozen;
  this file, the code and the configuration archived with their SHA-256 hashes recorded in
  `STATUS.md`, after which none of them is edited; (8) only then the hold-out is opened, once.
- **Point-in-time audit: scope and tests (v0.9.2; GPT). Until it passes, neither baseline fairness
  nor causal ordering is established, and the hold-out stays closed.** Items (3) and (4) cover:
  (a) the monthly liquidity screen uses only data before the selection date; (b) eligibility,
  listing and delisting status as of each date, and the construction date of the code list (a
  list drawn in 2026 that includes delisted names is still not a point-in-time universe; stated as
  a limitation); (c) availability dates and later revisions of **Z_H as well as Z_O\*** fields;
  (d) price adjustment, suspensions, limit-up/limit-down fills and the terminal return of delisted
  names; (e) nested chronology — base tuning, base out-of-sample scores, gate labels, gate fitting
  (the new Y−1 window) and annual refits. **Tests:** the look-ahead test and the cut-off-invariance
  test of v0.8 (`cutoff_invariance.py`: data after a cut-off are altered and every feature,
  nomination and decision before it must be unchanged; run and passed on the 100-name smoke
  pipeline of the pilot code, `results/pilot/PILOT_SMOKE_REPORT.md`) are re-run on the frozen code, extended to the Y−1 gate window, the Z_O* features,
  the Z_H features, the monthly screen and the chosen tuning configurations. Passing the pilot-code
  version is not carried over.
- **Requirements from the chronology audit (v1.0; `experiments/results/prefreeze_audit/AUDIT_PIT.md`,
  defects D1–D8; audit of the pilot code on development data, not yet cross-checked by an external
  model).** (i) *Tuning is done once and archived (D1):* all hyperparameter searches (base, BASE-V,
  NET-U15, gates, TREND, PERF, VT incl. σ*) are run with the data cut at 2021-12-31; the chosen
  configurations are archived with hashes at the freeze; the hold-out run loads them, refuses to
  re-tune and asserts equality. (ii) *Base validation years stay 2011–2012 (D3):* the "rolling
  temporal validation" of §A7 uses these years only, for the base and for BASE-V and NET-U15, so
  that no out-of-sample base score fed to a gate (from 2013-01-04) comes from hyperparameters
  selected on that period; the remaining overlap is the first four decision days of 2013 (at most
  H days of shared price path), stated. (iii) *Tuning criteria count resolved orders only (D4):*
  for tuning year v only orders whose exit precedes the first decision day of v + 1 enter the
  criterion; unresolved orders are dropped, and their number is printed. (iv) The feature panel is
  rebuilt, or reused only after a check of data cut-off, raw-tree and code hashes (D2). (v) Thread
  counts are fixed and recorded; the name list and raw-file hashes are frozen (D6, D7); listing
  dates after the cut-off are blanked at read time (D8). (vi) Gate rows whose exit is delayed past
  the fitting boundary are dropped (a label-dependent censoring of a few boundary rows, mostly
  losses); stated as a limitation. Audit verdicts: monthly screen, per-date eligibility logic,
  feature timing, labels and fills, preprocessing and determinism pass; the universe itself and
  vendor vintages cannot be established from the data (limitations; source-level sampling scheme
  S1–S11 proposed in the audit, not executed).
- **Further freeze checks (v0.9.3; GPT's review of v0.9.2).** (a) *Selection chronology:* for every
  historical out-of-sample base score fed to a gate, whether the hyperparameters that produced it
  were selected using outcomes of that same period; if so this is stated and its effect on gate
  training assessed (it does not touch the hold-out). (b) *Source-level availability:* cut-off
  invariance cannot detect a historical value that was revised later; a sample of Z_H and Z_O*
  records is checked against the original disclosures for the date on which they became public;
  fields whose historical vintage cannot be established are excluded or moved to a labelled
  sensitivity, and where neither is possible the limitation is stated. (c) *Estimand-defining
  implementation choices, each fixed in writing:* seed averaging = daily numerators and counts
  averaged over the five seeds before the ratio (equal to the mean of five ratios only if counts
  agree across seeds); the P3 window; whether a change of K or c in a sensitivity refits and
  retunes the gates (it does: refit with the chosen configuration, no retuning; PLACEHOLDER); the
  worst-5% convention of §A4.3 item 0 (⌊0.05·n⌋ lowest ρ, ties by order id); **if only one of LHB
  and BLK passes the date audit, Z_O\* is that class alone and P3 is so labelled.** (d) Execution:
  the fill and cost sensitivities include a conservative case (participation cap, one-day delayed
  exit on limit-down); without it the estimates concern the specified simulator only.

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
| §8.4 | family replaced by P1–P6 per base (§A4.1); C1–C4 secondary (§A4.2) |
| §9.1, §9.2 | loss-frequency and tail contrasts become a named key secondary (§A4.3 item 0) |
| §9.3 | bound unchanged in value, used as the reference line for P1–P6 (§A5); wording rules replaced for the primary family |
| §12 | experiment-to-claim map: P1–P6 use no theory result (§A11) |
| §10 (multiple comparisons) | Holm family replaced by simultaneous intervals over the primary family |
| §10.1, §10.1b | withdrawn; replaced by `precision_v9` (§A6) |
| §10.2 | `null_pipeline` extended as in §A8 item (6) |
| §13A | closed: three exploratory rounds done; results in `PILOT_RESULTS_SUMMARY.md` |
| §15.2, §15.3 | outcome wording by the reading rule of §A4.1 (estimates, simultaneous intervals, Δ reference line; no class labels) — to be rewritten when this is merged |
| §18 | additions of §A8 |

Unchanged: execution and accounting conventions (§3), features and controls (§4.1, §5), the hold-out
window, the cost model, the bootstrap unit and block length, the standing qualifier on synthetic
fills, the known-limitations register (§19).

---

## A10. Decisions of the user (2026-11-17)

**Reading note (v1.0).** The tables below are a chronological record. Where an earlier row
conflicts with a later one, the later one governs: the family has twelve contrasts (not six or
eight); there are no class labels and no TOST (D10 supersedes the classification part of O3 and
of D4); the subject is fixed-coverage re-ranking (D9).

Fifth round, after the reviews of v0.9.3 (`reviews/plan_review_5.md`; "move to the pre-freeze
work"): the per-version review loop stops; v0.9.3 is the working direction; pre-freeze work uses
development data only; the accepted review points are consolidated in this v1.0 specification,
which gets one final cross-model review before the freeze; the user then decides on opening the
hold-out. Fixed by the lead on that basis (the user may overrule): the estimator definition and
edge cases of §A4.1; full-pipeline scenarios gated (§A6); BASEV-RERANK and NET-U15 as secondaries.

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

Third round, after the re-review of v0.9.1 (`reviews/plan_review_3.md`), told that the most likely
outcome is eight inconclusive contrasts ("continue, as an estimation study"):

| ID | Decision | Where |
|---|---|---|
| D7 | The study continues with this design and is framed as an estimation study; no class label is a success criterion; Δ unchanged | §A0 |

Fourth round, after the reviews of v0.9.2 (`reviews/plan_review_4.md`; "all as the lead proposed"):

| ID | Decision | Where |
|---|---|---|
| D8 | A base predictor whose hyperparameters are selected on V (BASE-V) is added as a comparator, and the gates are compared with it in the primary family (P5, P6; twelve contrasts) | §A4.1, §A7 |
| D9 | The paper's subject is stated as fixed-coverage re-ranking; variable-count threshold policies stay secondary | §A0 |
| D10 | The four class labels are removed; primary contrasts are reported as estimates with simultaneous intervals and the Δ reference line; Δ unchanged. This supersedes the classification part of O3 and the unadjusted-TOST display of D4 | §A0, §A4.1 |

Decided by the lead after the discussion `inference-target` (technical; reported to the user): the
inferential target and assumptions of §A0; the simulation suite and pass rule of §A6; the
descriptive fallback (Route B), which would need the user's decision if triggered.

Superseded statements of earlier versions, kept above for the record: "eight contrasts" (now
twelve); every mention of classes "negligible / beneficial / harmful / inconclusive".

Still PLACEHOLDER and to be confirmed at the freeze (v0.9.3 list replaces the one below): the event
window (5 days), K ∈ {20, 50} and c ∈ {0.1, 0.3, 0.7, 0.9} of the sensitivity, the simulation sizes,
p_max = 6% and the 0.1 bp truth-error limit of §A6, the pooled averaging of §A2.2, the refit rule
for sensitivities (§A8).

Earlier list: the event window (5 days), K ∈ {20, 50} of the
sensitivity, the simulation sizes and the pass criteria of §A6 (94.0% / 5% / 1% / 2.5%), the pooled
averaging of the tuning criterion (§A2.2).

Not adopted, with reasons (v0.9.3): a matched-budget base(+Z) primary experiment (both reviewers;
it would let Z change nominations and is a different study — it stays the exploratory unit of v0.8
§7.1 and the Z claims are narrowed, §A0, §A4.3 item 6); loss frequency or a tail measure as a
co-primary quantity, and a redesign in which Theorem 1 is tested by the market experiment (Gemini,
rated critical in two successive reviews; the user's decisions D5 and D6 stand, and the paper says
that the primary quantity is mean net return and that the theory is supporting); restoring a
variable-count gate as primary (Gemini; the threshold gates degenerated in the pilot — they stay
secondary and the subject is narrowed, D9); an ensemble of the five seeds as the policy (Gemini;
between-seed averaging lowers the SE by about a tenth at most on the pilot decisions, §A0; the
ensemble policy itself is unverified and may be added as a secondary). **Withdrawn:** v0.9.2
refused a base tuned on the endpoint as "a new design element after outcomes were seen"; GPT
pointed out that the whole amendment is pilot-informed and a comparator declared before the
hold-out is opened can be disclosed in the same way. The lead agrees; see D8.

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

## A11. Relation to the theory files (v0.9.1; both reviewers; unchanged in v0.9.2)

**No primary contrast, key secondary or classification of this amendment uses a result of
`theory/theorems.md`.** P1–P6 are comparisons of fitted selection policies by mean net return with
bootstrap inference; they neither test nor rely on Theorem 1, its corollaries, Proposition 2 or
Lemma 3. The paper is positioned accordingly (D6, D9): an empirical estimation study of
fixed-coverage re-ranking, with variable-count abstention as a secondary analysis and the theory
results in a supporting role. What each result is used for, and what checks it:

| Result (label of `theorems.md`; none is a theorem in the sense of rule 3 yet) | Role in the paper | Checked by |
|---|---|---|
| Theorem 1, Corollaries 1.1–1.2 (time-uniform interval for the entry loss rate under delayed labels) | monitoring tool reported for the deployed strategies; shows how wide an honest interval is (about ±0.17 in the pilot) | synthetic validation protocol of v0.8 §12.1 (coverage under optional stopping, delays, dependence); unchanged |
| Proposition 2 (lower bound) | context for the width of the Theorem 1 interval | no market experiment; stated as theory only |
| Lemma 3 (additive attribution) | descriptive split of paired ΔAR into exposure, composition and cost (§A3.3) | ledger reconciliation R2–R4 and known-answer cases of v0.8 §12.1 |
| Identity θ_uns = θ_sel + A (§A3.2; `草稿`) | decomposition shown beside the secondary selection statistics | algebraic proof to be written into `theory/` and reviewed; unit tests with empty cells, zero submissions, singleton cells and days with fewer than K nominations; an identity, not an empirical claim |

If the user later decides that Theorem 1 is to be a core contribution, the experiments for it are
those of v0.8 §12.1 and need their own review; nothing in P1–P6 would change. **(v1.0; GPT)** The
synthetic validation of Theorem 1 is too briefly specified to be judged; before it is run it gets
its own specification: probability of any coverage failure over the whole monitoring horizon,
predictable adaptive submissions, strong within-date dependence with overlapping outcomes, only
the delay mechanisms the assumptions allow, sparse submissions and loss probabilities near 0 or 1,
width against time, delay and number of independent units, and a valid existing comparator under
the same assumptions if one exists.

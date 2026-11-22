> REVIEW NOTE: this is part 1 of 5 of one document (PLAN amendment v0.9.3: part 1 = header, A0, A1; part 2 = A2, A3, A4.1, A4.2; part 3 = A4.3, A5; part 4 = A6, A7; part 5 = A8-A11). Review this part on its own; material in other parts cannot be checked here, so say "not visible in this part" rather than "missing" where a cross-reference points elsewhere.

# Experiment Plan — Amendment v0.9.3 (DRAFT, not in force)

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

> REVIEW NOTE: this is part 2 of 5 of one document (PLAN amendment v0.9.3: part 1 = header, A0, A1; part 2 = A2, A3, A4.1, A4.2; part 3 = A4.3, A5; part 4 = A6, A7; part 5 = A8-A11). Review this part on its own; material in other parts cannot be checked here, so say "not visible in this part" rather than "missing" where a cross-reference points elsewhere.

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
The user's decision D8 puts it in the family. A fixed-nomination "SCORE-V" was considered and
dropped: a model on the −Z features fitted on nominated rows with hyperparameters selected by V is
what NET-K(−Z) already is (P4), up to details that the tuning matrix of §A8 must show.

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
states C1–C4 as the confirmatory claims; **it needs a v5 that states P1–P4** (user decision, O1).


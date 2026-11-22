> REVIEW NOTE: this is part 1 of 3 of one document (PLAN amendment v0.9.2: part 1 = header, A0-A3; part 2 = A4-A5; part 3 = A6-A11). Review this part on its own; references to sections in other parts cannot be checked here.

# Experiment Plan — Amendment v0.9.2 (DRAFT, not in force)

> **Status.** Drafted 2026-11-17 by the lead after the exploratory pilot round (PLAN v0.8 §13A) and three
> discussion rounds with GPT (thread `pilot-direction`). **v0.9 was reviewed by GPT (semi-independent)
> and Gemini Flash (independent); both refused approval as written (`reviews/plan_review_2.md`).
> v0.9.1 was the revision after that review, with the user's decisions D1–D6 of 2026-11-17 (§A10);
> its re-review was done by GPT only ("major revision before freezing", `reviews/plan_review_3.md`;
> the automatic Gemini call failed on file length). v0.9.2 is the revision after that re-review, with
> the user's decision D7 (the study is an estimation study, §A0). Not approved by the user as a
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

## A0. Nature of the study (v0.9.2; user decision D7)

**This is an estimation study.** Its deliverable is, for each primary contrast of §A4.1, a point
estimate and a simultaneous 95% interval on the unopened hold-out, reported whatever they are. A
class label (§A4.1) is attached to each interval as a reading aid; **obtaining a particular label is
not a success criterion of the study, and the paper is written so that it stands if every label is
"inconclusive".**

**Expected outcome, stated before any hold-out result exists.** Planning arithmetic under a normal
approximation with the pilot standard errors of P1 and P4 (3.0–3.8 bp) and a critical value q
between 1.96 and 2.73 (§A4.1; the simulation of §A6 replaces these figures):

| Quantity | Value |
|---|---|
| estimate needed for "detected" (interval excludes zero) | above about 5.9–10.4 bp in absolute value |
| true effect detected with probability 80% | about 8.4–13.6 bp |
| estimate needed for "materially beneficial" (L > Δ) | above about 10.8–15.3 bp |
| true effect classified "materially beneficial" with probability 80% | about 13.4–18.5 bp per order (roughly 2.7–3.7% per year of capital under the conditional reading of §A5) |
| pilot point estimates of P1 and P4 (exploratory) | −6.1 to +1.7 bp |

**The most likely outcome is therefore that all eight primary contrasts are "inconclusive at ±Δ".**
The user has decided to run the study in this knowledge (D7).

**Inferential target.** All primary inference concerns the **realised performance, over the hold-out
window as it happened, of this one frozen procedure**: the fitted policies obtained by applying the
frozen training rules to the realised history (annual refits included), averaged over the five
seeds. It is conditional on the fitted policies and on the realised sequence of annual market
states. It is **not** the expected performance of the procedure over alternative training histories,
nor an expectation over future years or regimes; with about 4.5 hold-out years the study has no
basis for either and claims neither. The date-block bootstrap is used as an approximation to the
day-level sampling variability of that realised average under weak dependence within the window.

**What the study cannot show, whatever the outcome** (wording binding for the abstract and the
conclusions): (i) whether abstention works in general or on the A-share market — the population is a
convenience list (§A8); (ii) whether Z_H or Z_O "contain information" — P2 and P3 measure the value
of one feature representation in one training procedure for re-ranking base(−Z) nominations
(§A4.3 item 6); (iii) whether a separately trained gate is useful for a base model tuned for the
same endpoint — the base is tuned by RankIC (§A7); (iv) anything about the theory results (§A11);
(v) that the gates make a strategy "lose less often" — the primary quantity is mean net return per
submitted order, and the loss-frequency statistics are exploratory (§A4.3 item 0). Inconclusive
contrasts, exploratory loss statistics and supporting theory are not promoted into stronger
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

**Averaging (v0.9.2; GPT).** For each seed, V^g is the **pooled** ratio over all decision days of the
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


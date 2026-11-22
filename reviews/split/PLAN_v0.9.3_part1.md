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


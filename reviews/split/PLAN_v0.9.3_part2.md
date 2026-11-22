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


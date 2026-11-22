> REVIEW NOTE: this is part 2 of 3 of one document (PLAN amendment v0.9.2: part 1 = header, A0-A3; part 2 = A4-A5; part 3 = A6-A11). Review this part on its own; references to sections in other parts cannot be checked here.

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
θ̂_j ± z_{1−0.05/(2m)} · ŝe_j (Bonferroni with the normal quantile; m = 8 or 6). **Limit of the
fallback (v0.9.2; GPT):** it changes only the multiplicity adjustment; it uses the same bootstrap
standard errors and a normal approximation, so it does not protect against a standard error that is
itself wrong (dependence longer than the blocks, heavy tails). If the §A6 failure is of that kind,
both rules fail and the hold-out is not opened.

**What this rule can and cannot conclude (v0.9.2; corrects the lead's statements in v0.9 and
v0.9.1).** The critical value q is data-dependent. With m = 8 it lies between 1.96 (contrasts
perfectly correlated) and about 2.73 (independent); "about 2.7 or more", as v0.9.1 had it, is an
upper end, not a lower bound. At the pilot standard errors of P1 (3.0–3.8 bp) the interval
half-width is at least 1.96 × 3.0 ≈ 5.9 bp, larger than Δ = 4.96 bp, so **"negligible" cannot be
reached for P1 or P4 even at an estimate of exactly zero**; it requires a standard error below
Δ / q, i.e. below 1.8–2.5 bp depending on q (P2 and P3, with pilot standard errors of 1.6–3.2 bp,
are at the edge). v0.9 said that dropping the TOST solved a power problem; it does not. For
contrasts with standard errors like the pilot's the possible labels are "materially beneficial",
"materially harmful" and "inconclusive", the last by far the most likely (§A0), and the paper says
so before showing results. **Reported for every contrast from §A6, separately (v0.9.2; GPT):** the
minimum effect detected as non-zero with probability 80%, and the minimum effect classified as
beyond Δ with probability 80%.

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
not a verdict". It is never used as a headline or as a substitute when the family is inconclusive
(v0.9.2; GPT). Δ is not re-anchored to the achievable precision (a suggestion of one reviewer, not
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
   P3 with the INS class included (sensitivity). **δ(NET-K(−Z), LOSS(−Z)) for each base (v0.9.2;
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
8. **Operating point and seeds (v0.9.1).** P1–P4 at c ∈ {0.3, 0.7} (v0.8 §6.1) and at K ∈ {20, 50}
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
of §A4.3 item 9 shows how far they are. **The same bound applies to P2, P3 and P4** by the user's decision
(O2): it is the user's judgement of what is economically material, the same for every contrast. It
is not derived from any measured cost of data or of running a gate, and the paper does not describe
it as a cost threshold. Δ is not changed after approval.

---


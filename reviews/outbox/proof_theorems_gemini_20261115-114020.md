You are a rigorous optimization theorist. Check every step of every proof below. For each error give: location, why it is wrong, whether it is fixable, and a suggested fix. Also check whether the assumptions are standard, whether any assumption is used but not stated, and whether constants and rates are stated correctly. Do not praise; only report issues. Finish with a verdict: CORRECT / FIXABLE ERRORS / FUNDAMENTAL FLAW.

===== BEGIN FILE: theory/theorems.md =====
# Statements (Stage 2, Task A)

> Researcher (sub-agent), 2026-11-15; **revised after review round 1** (`reviews/proof_check_1.md`) **and round 2** (`reviews/proof_check_2.md`). Setup, notation and assumptions A1–A5, A4-D: `theory/setup.md`. Proofs and the item-by-item revision log: `theory/proofs.md`. Numerical checks: `theory/checks/`.
> Status labels follow `CLAUDE.md`. Only `草稿` (draft) and `自查通过` (author's own proof complete and numerical sanity check not contradicting it) are used here; the labels "GPT 审过" / "Gemini 审过" are assigned by the lead after re-review, not by the author. **No item may be called a theorem in the paper yet.**
> "Relation to prior work" lines quote `theory/prior_theorems_audit.md` (itself self-checked reading notes, not externally reviewed). No reviewer in round 1 assessed novelty.

## Status table

Review note that applies to **every** row: ***round-2 review: GPT + Gemini (Flash); revisions applied, confirmation re-review pending.*** (Round 1: GPT proof review + GPT independent derivation + Gemini Flash; its items were not raised again in round 2.) Round-2 changes per item are listed after the table; the last column records round 1.

| Item | Content | Assumptions | Status | Numerical check | Round-1 outcome and what changed |
|---|---|---|---|---|---|
| Theorem 1 (a) | time-uniform interval for r_T^entry, radius B_T | A1–A3 (A4 for computability) | `自查通过` | `check_thm1_coverage.py`, `check_matured_rate.py`: no contradiction | No error found in proof or constants by any reviewer. Changed: b* defined piecewise (C5), N_T = 0 convention (D13), wording of the rate (D3), role of M (D5). |
| Theorem 1 (b) | same event, sharper radius B*_T ≤ B_T | A1–A3 (A4) | `自查通过` | same scripts: no contradiction | as (a) |
| Theorem 1 (c) | one-sided versions, each at level δ/2 | A1–A3 (A4) | `自查通过` | **no separate check of the one-sided levels for Theorem 1**; the two-sided simulation says nothing about δ/2 per side. The claim rests on the signed union bounds (proofs §1.5). `check_cor13.py` counts upper and lower failures separately for Cor. 1.3 (0 and 0 of 4800 paths) | as (a); evidence statement corrected (D9) |
| Corollary 1.1 | (a) sampling-error radius ≤ √(dM ℓ_T/N_T), width ≤ P_T/N_T + 2√(dM ℓ_T/N_T); (b) under A5, width ≤ 3√(dM ℓ_T/N_T) | radius bound: A1–A3; total-width bound with P_T: A1–A4; (b): A1–A5 | `自查通过` | (a): bound ≥ realised radius in all 12 configurations; (b): new, **no dedicated check** (two-line consequence of (a)) | Statement split and rate wording corrected (D3). |
| Corollary 1.2 | deterministic bracket for the realised loss fraction; comparison with r_T^entry | bracket: A4 only; comparison: A1–A3 | `自查通过` | bracket held on 100% of paths | Assumption line corrected, "biased" → "can be biased" (D4). |
| Corollary 1.3 | interval for the executable-liquidation target via deadline labels; conditional persistence | A1; A2 for three labels incl. completion convention; A3 for the two deadline labels; A4-D | `草稿` | `check_cor13.py` (round 1): 0 misses on 4800 paths; Parts B, C as predicted | **Statement substantially rewritten** (C2, C3, C4, D14) in round 1; seen by both round-2 reviewers, who raised notation items only (M2, M4) plus the liquidation-policy item G9; kept `草稿` until the confirmation re-review |
| Proposition 2 | lower bound √(Md/N) for honest fixed-time intervals | construction satisfies A1–A5 | `自查通过` | TV bound and effective sample size: no contradiction; `check_pinsker_binary.py` (new) | No error found. Changed: Pinsker's inequality now **proved** in proofs §2.3 (D9), divisibility and t > T made explicit (D12, D13), Scope reworded (D3). |
| Lemma 3 | additive P&L attribution identity | none (algebra); accounting assumptions only for the wealth interpretation | `自查通过` | `check_attribution.py` (re-run in round 2): identity residual ≤ 4.5e-16; adversarial accounting cases (dividend, split, slippage) 12 of 12 required equalities hold | Identity confirmed by all reviewers. Changed: reference-portfolio trade formula (D7), accounting assumptions for Π (D8). |
| Remark 4 | no policy can guarantee successful trading in every environment | — | `自查通过` | none needed (two-line argument) | **Statement weakened** (C1): uniqueness claim and information argument deleted. 陈述经修改，待复审 |
| Worksheet 5 | price-pressure toy calculation | — | not a result; see `mechanism_worksheet.md` | — | not sent for review |

**Round-2 changes (items of `reviews/proof_check_2.md`; details in the "Revision log (round 2)" of `proofs.md`).** No proof step of Theorem 1, Corollary 1.1 or Proposition 2 was reported wrong in round 2.
- Theorem 1: the statement now says that d is a deterministic integer fixed before any data are examined (M5).
- Corollary 1.1: assumption line in three tiers (M1); (a) covers the intervals of Theorem 1(a) **and** (b) (M3).
- Corollary 1.3: P_T renamed P_T^D (M4); ℓ_T^{(D)} defined with d_D (M2); "sold by the deadline" tied to the liquidation policy LP of setup §3.2 (G9). Still `草稿`.
- Proposition 2: Scope (i) reworded as a sufficient condition, with the sharper threshold (G6).
- Lemma 3: reference trade vector redefined through pre-trade shares after corporate actions, cash distributions booked separately, return-based shortcut restricted (G3); benchmark-price accounting adopted (lead decision), execution-price accounting kept as an alternative under condition (EX), and "every cost exactly once" stated (G4); W1–W4 described as sufficient, cash term renamed (G5).
- Remark 4: the example policy now respects the cap M (G11).

`自查通过` means only that the author found no error and the numerical sanity check did not contradict the statement. It is **not** an independent verification, and a simulation on a few synthetic environments cannot establish a theorem.

---

## Theorem 1 (delayed monitoring under arbitrary within-day dependence)

**Status:** (a), (b), (c) `自查通过` (round-2 review: GPT + Gemini (Flash); revisions applied, confirmation re-review pending). **Assumptions:** A1, A2, A3 for validity; A4 so that K_T, P_T are computable. The cap M of A1 does not enter the radii; it guarantees that X_t is bounded, hence that μ_t is an ordinary conditional expectation (setup §4, A1).

Fix δ ∈ (0,1) and a **deterministic integer d ≥ 1 for which A3 holds; δ and d are fixed before any data are examined** — they are constants, not functions of the observed path (entry counts, labels, or the widths that different lags would give). The theorem is a statement for each such fixed pair (δ, d). It does **not** cover a lag d̂ selected after looking at the data: the radii B_T(d), B*_T(d) are not monotone in d (setup §3.3, `checks/check_lag_monotonicity.py`), so choosing among several valid lags the one with the narrowest interval is a data-dependent selection outside the statement (it could be covered by a union bound over a pre-specified finite set of lags, at level δ divided by their number; this is not pursued). Let c_0 = π²/6 and, for integers k ≥ 0,

  L_k = log( 2 d c_0 (k+1)² / δ ),  g_k(q) = (1/2) sqrt( 2^k L_k ) ( 1 + q / 2^{k+1} )  (q ≥ 0).

For lane j ∈ {0,…,d−1} let Q_{j,T} = Σ_{t≤T, t≡j (mod d)} n_t² (a non-negative integer). Define, **for integer arguments q ∈ {0, 1, 2, …} only**,

  b(q) = 0 if q = 0;  b(q) = sqrt( 2^{k(q)} L_{k(q)} ), k(q) = ⌊log₂ q⌋, if q ≥ 1;
  b*(q) = 0 if q = 0;  b*(q) = min_{k≥0} g_k(q) if q ≥ 1

(the minimum exists because g_k(q) → ∞ as k → ∞; b*(0) = 0 is a separate definition, **not** the value inf_k g_k(0) = (1/2)√L_0 > 0), and B_T = Σ_{j=0}^{d−1} b(Q_{j,T}), B*_T = Σ_{j=0}^{d−1} b*(Q_{j,T}).

There is an event E_δ with ℙ(E_δ) ≥ 1 − δ on which, **simultaneously for all lanes j and all T ≥ 1**,

  | Σ_{t≤T, t≡j (mod d)} (μ_t − X_t) | ≤ b*(Q_{j,T}) ≤ b(Q_{j,T}).   (1)

Consequently, on E_δ, simultaneously for all T with N_T > 0:

**(a)** max{0, (K_T − B_T)/N_T} ≤ r_T^entry ≤ min{1, (K_T + P_T + B_T)/N_T};

**(b)** max{0, (K_T − B*_T)/N_T} ≤ r_T^entry ≤ min{1, (K_T + P_T + B*_T)/N_T}, and B*_T ≤ B_T, so (b) implies (a);

**(c)** (one-sided) E_δ = E_δ^up ∩ E_δ^low with ℙ(E_δ^up) ≥ 1 − δ/2 and ℙ(E_δ^low) ≥ 1 − δ/2; the upper bounds in (a), (b) hold on E_δ^up and the lower bounds on E_δ^low.

*Convention.* When N_T = 0 the target is undefined and the interval is [0,1] by convention; the statement makes no claim for such T.

The interval is valid for **any** revelation pattern consistent with A3–A4, including revelation times that depend on the labels.

*Properties of the radii.* For integers q ≥ 1, b*(q) ≤ b(q). The functions g_k are affine and increasing, so the real-variable extension q ↦ min_k g_k(q) is concave, continuous and increasing **on [1, ∞)**; b has upward jumps at powers of two, the extension of b* has no jump on [1, ∞). Nothing is claimed about continuity at 0 (b*(0) = 0 < b*(1); the formula min_k g_k would give (1/2)√L_0 > 0 at q = 0).

*Comparison with the design notes.* The proposed radius b(q) with 2^{k(q)} (not 2^{k(q)+1}) is **confirmed** by the derivation (proofs.md §1.5), provided λ is tuned to the **upper** end 2^{k+1} of the dyadic epoch. (b) and (c) are additions.

*Comparison with existing results.* Not sharper than known confidence sequences; it is a Hoeffding-type (predictable-range) bound with dyadic stitching, applied on d interleaved sub-sequences. No empirical-variance adaptation.

*Relation to prior work* (from `prior_theorems_audit.md` §8.1): "Essentially yes" a direct corollary — not of any single theorem read, but "in a few lines from two known ingredients": Howard et al. (arXiv:1810.08240) Theorem 4 / stitched boundary for the running average of conditional means, and the sub-sampling reduction of Weinberger & Ordentlich 2002 / Joulani et al. 2013. The audit's recommendation: label it "a proposition / corollary with full attribution, not a theorem contribution". The audit found the combination (delay + overlap) × (same-day batch) × (entry-time conditional target) × (time-uniform) "not found stated anywhere", on a search it calls weak. The audit has not read Howard et al.'s proofs or Weinberger & Ordentlich. Lindon & Kallus (arXiv:2603.25971) has not been read (`STATUS.md`). Our proof is self-contained and does not invoke those theorems.

*In plain words.* We cannot see the true chance that each batch of trades would lose money; we only see, with a delay, how many did. Split the trading days into d groups ("lanes") so that inside one group every day's result is known before the next day of that group is traded. Inside a group the gap between "expected losses" and "actual losses" behaves like a fair game, so it cannot drift far; adding the d groups gives a band around the observed loss count. Trades whose result is not yet known are simply counted both ways (all fine / all losing). The band is valid at every day simultaneously and needs no assumption on how same-day stocks move together. The price: the band is wide. It has two parts. The **sampling-error part** shrinks like √(d·M / number of trades) (times a slowly growing logarithm), not like 1/√(number of trades). The **pending part** is the share of trades whose result is not yet recorded, P_T/N_T; it is small only if results are actually recorded within the lag (then it is at most d·M / number of trades).

### Corollary 1.1 (explicit rate of the sampling-error term; total width)

**Status:** `自查通过` (round-2 review: GPT + Gemini (Flash); revisions applied, confirmation re-review pending). **Assumptions (three tiers; round-2 item M1):** for the bound on the sampling-error radius, B*_T ≤ B_T ≤ sqrt(d M N_T ℓ_T): A1–A3 (with n_t ≤ M); for the total-width bound in (a), which contains P_T and refers to the interval endpoints built from K_T, P_T: A1–A4; for (b): A1–A5.

**(a)** For every T with N_T > 0, deterministically,

  B*_T ≤ B_T ≤ sqrt( d · Σ_{t≤T} n_t² · ℓ_T ) ≤ sqrt( d M N_T ℓ_T ),
  ℓ_T = log(2 d c_0/δ) + 2 log( 1 + log₂(M N_T) ).

Hence the **sampling-error radii** satisfy B*_T/N_T ≤ B_T/N_T ≤ sqrt( d M ℓ_T / N_T ) (a deterministic inequality; A1–A3), and, under A4 in addition, the total width of each of the intervals in Theorem 1(a) **and** (b) is at most

  min{ 1, P_T/N_T + 2 sqrt( d M ℓ_T / N_T ) }.

Under A1–A4 alone nothing is said about P_T/N_T (A3 concerns the aggregate X_t, not the disclosure of individual labels), so **the total width is not claimed to be of order sqrt(dM/N_T)**; it tends to zero only if both d M ℓ_T/N_T → 0 and P_T/N_T → 0.

**(b)** If in addition A5 holds (every label of day t is revealed at all monitoring times T ≥ t + d), then P_T ≤ dM and the total width of the intervals in Theorem 1(a), (b) is at most

  min{ 1, dM/N_T + 2 sqrt( d M ℓ_T / N_T ) } ≤ 3 sqrt( d M ℓ_T / N_T ).

This is **predictable-range adaptation** (the clock is Σ n_t², known before outcomes), not empirical-variance adaptation. No empirical-Bernstein version is claimed.

*Relation to prior work:* same as Theorem 1 (audit §8.1 gives the same rate "up to constants and iterated logarithms"; our constants are explicit).

*In plain words.* With N trades, at most M per day, and results known after d days, the statistical uncertainty is about √(d·M/N) times a slowly growing logarithmic factor (√ℓ_T ≈ 3–3.5 in our simulations). On top of that comes the share of trades whose results are still outstanding; if every result is recorded within d days, that share is at most d·M/N and the whole band is at most 3·√(d·M·ℓ/N) wide.

### Corollary 1.2 (realised loss fraction; why the common denominator)

**Status:** `自查通过` (round-2 review: GPT + Gemini (Flash); no round-2 item on this corollary; confirmation re-review pending). **Assumptions:** A4 for the deterministic bracket (no probability); A1–A3 for the simultaneous probability-(1−δ) comparison with r_T^entry.

For all T with N_T > 0: K_T/N_T ≤ R_T ≤ (K_T + P_T)/N_T, where R_T = Σ_{t≤T} X_t / N_T (deterministic, A4 only). Under A1–A3, on E_δ, |r_T^entry − R_T| ≤ B*_T/N_T for all such T.

The "matured-only rate" K_T/(N_T − P_T) appears nowhere: it has a different denominator and its composition is selected by maturity; it is not covered by any statement here. It **can** be biased (it need not always be). Minimal example (from the GPT derivation): two entries with labels 0 and 1, of which only the losing one is revealed at the monitoring time: N_T = 2, K_T = 1, P_T = 1, R_T = 1/2, matured-only rate = 1, while the bracket is [1/2, 1]. A simulated example with outcome-dependent revelation times: `checks/check_matured_rate.py`.

*Relation to prior work:* bookkeeping; the audit (§8.2) lists the treatment of unmatured days as "routine".

### Corollary 1.3 (executable liquidation: conservative interval through deadline labels)

**Status:** `草稿`. The statement was substantially rewritten in round 1 (items C2, C3, C4, D14). Round 2 (GPT + Gemini (Flash)) raised the notation items M2, M4 and the liquidation-policy item G9, all applied below; **confirmation re-review pending**, and the status stays `草稿` until then. Proof: proofs.md §1.8. Numerical check: `checks/check_cor13.py` (not re-run in round 2; the changes are notational).

**Assumptions:** A1; A2 for the three labels L^lo, L^liq, L^hi below, including the completion convention for L^liq; A3 with a deterministic lag d_D, fixed before any data are examined, for the two deadline labels (not for L^liq); A4-D (paired accounting with a common revealed set J_T, setup §4).

*Labels.* L^liq_{ti} ∈ {0,1} is the executable-liquidation loss label of setup §3.2, defined through the **liquidation policy LP** stated there (an observable order-and-fill policy, with its execution model and partial-fill handling), with the **completion convention L^liq_{ti} := 1 if the position is never liquidated**, so that it is defined for every executed entry on all of Ω. Fix a deadline D ≥ H. **"Sold by the deadline of day t+D" means that the same policy LP has liquidated the whole position at or before the opening auction of day t+D** (a position only partly sold by then is not "sold"); the deadline labels use the same execution model and cost accounting as L^liq (round-2 item G9; this is what makes L^lo = L^liq = L^hi when S = 1). Let

  S_{ti} = 1{sold by the deadline}, L^lo_{ti} = S_{ti} · 1{that sale was at a net loss}, U^D_{ti} = 1 − S_{ti}, L^hi_{ti} = L^lo_{ti} + U^D_{ti}.

Let X^•_t = Σ_i A_{ti} L^•_{ti}, μ^•_t = E[X^•_t ∣ F_t] for • ∈ {lo, liq, hi}, and r_T^{liq} = Σ_{t≤T} μ^{liq}_t / N_T. Let d_D be the lag of the deadline labels (setup §3.3 with D for H) and B*_T the radius of Theorem 1 computed with lag d_D. With J_T the common revealed set of A4-D,

  K^lo_T = Σ_{(t,i)∈J_T} L^lo_{ti}, K^hi_T = Σ_{(t,i)∈J_T} L^hi_{ti}, P_T^D := N_T − |J_T|,
  ℓ_T^{(D)} := log(2 d_D c_0/δ) + 2 log( 1 + log₂(M N_T) ).

(Notation, round-2 items M4 and M2: P_T^D, the number of executed entries outside the common revealed set, is **not** the P_T of Theorem 1, which counts unrevealed values of a single label; ℓ_T^{(D)} is the ℓ_T of Corollary 1.1 with the lag d_D in place of d.)

**(i) Interval.** With probability at least 1 − δ, simultaneously for all T with N_T > 0,

  Λ_T := max{0, (K^lo_T − B*_T)/N_T} ≤ r_T^{liq} ≤ min{1, (K^hi_T + P_T^D + B*_T)/N_T} =: Υ_T.

The lower bound alone holds with probability ≥ 1 − δ/2, and so does the upper bound alone (one lower-sided event for L^lo and one upper-sided event for L^hi; no two-sided confidence sequence is used, so the radius is the same B*_T as in Theorem 1).

**(ii) Pathwise width bounds.** For every T with N_T > 0,

  (K^hi_T − K^lo_T)/N_T ≤ Υ_T − Λ_T ≤ (K^hi_T − K^lo_T + P_T^D + 2B*_T)/N_T,

and K^hi_T − K^lo_T = #{(t,i) ∈ J_T : the entry was unsold at its deadline}. The denominator N_T is the number of **all executed entries** through T; (K^hi_T − K^lo_T)/N_T is therefore *not* the deadline-unsold fraction among revealed entries (that would have denominator |J_T|).

**(iii) Conditional persistence.** On any path on which liminf_{T→∞} (K^hi_T − K^lo_T)/N_T ≥ ρ > 0, also liminf_{T→∞} (Υ_T − Λ_T) ≥ ρ. Conversely, on any path with (K^hi_T − K^lo_T)/N_T → 0, P_T^D/N_T → 0 and d_D M ℓ_T^{(D)}/N_T → 0, the width Υ_T − Λ_T → 0.

*What is not claimed (round-1 correction).* The first draft said the deadline-unsold part "does not shrink with more data and is the identification limit of the liquidation outcome". Neither follows from the assumptions. (1) Whether the share stays positive depends on the path: with one entry per day of which only the first misses its deadline, (K^hi_T − K^lo_T)/N_T = 1/T → 0 and the whole width tends to 0 (`check_cor13.py` Part B). (2) The observed share (K^hi_T − K^lo_T)/N_T is not the target-level gap, which is

  r_T^{hi} − r_T^{lo} = Σ_{t≤T} E[ Σ_i A_{ti} U^D_{ti} ∣ F_t ] / N_T,

a conditional expected deadline-unsold fraction. (3) The residual width is a limitation of an interval that **uses only information up to each entry's deadline**; liquidations observed after the deadline could distinguish environments that the deadline labels cannot. We have **not** proved that the liquidation target is unidentifiable from all eventually available data; that would require specifying the observations and proving observational equivalence.

No assumption on the censoring mechanism is used.

*Relation to prior work:* audit §8.3(d), "Censoring at H — easy … Purely definitional" (the audit states the one-sided version). Not a contribution.

*In plain words.* For "could I actually sell without a loss", some positions get stuck (suspension, limit-down) for an unknown time. We give every position a deadline. A position sold by its deadline counts as what it was. A position still stuck at its deadline is counted once as "fine" and once as "lost". This gives an honest band for the true loss rate that needs no guess about stuck positions. If a steady share of positions keeps getting stuck, the band stays at least that wide however much data arrive; if getting stuck becomes rare, the band narrows. A narrower band might be possible by waiting to see what eventually happens to stuck positions — this method does not do that.

---

## Proposition 2 (worst-case effective sample size)

**Status:** `自查通过` (round-2 review: GPT + Gemini (Flash); revision G6 applied to the Scope; confirmation re-review pending). The proof is self-contained: Pinsker's inequality is proved in proofs.md §2.3 for the case needed. (For orientation only: the inequality is standard; a textbook source is Tsybakov, *Introduction to Nonparametric Estimation*, 2009 — **lemma number to be verified** by literature-scout before it is cited.) **Assumptions:** none beyond the construction, which satisfies A1–A5.

*Block environment.* Integers d, M, B ≥ 1. **The proposition is stated only for T = B d and N = M B d** (T a multiple of d, N a multiple of M d). Days 1,…,T in blocks {(b−1)d+1, …, bd}, b = 1,…,B; every day t ≤ T has exactly M entries (n_t = M, N_T = N); for t > T there are no entries (n_t = 0, X_t = 0, μ_t = 0) and F_t = σ(Z_1,…,Z_B, U). Z_1,…,Z_B i.i.d. Bernoulli(p); every label of every day in block b equals Z_b; for t ≤ T, F_t = σ(Z_1,…,Z_{b(t)−1}, U) where b(t) is the block of day t and U is a Uniform[0,1] variable independent of the Z's (available for randomised procedures). Call the law ℙ_p. Under ℙ_p, A1–A5 hold with lag d, μ_t = M p for all t ≤ T and r_T^entry = p.

*Uniformly honest fixed-time interval.* A pair of measurable functions ℓ ≤ u of (Z_1,…,Z_B, U) — i.e. of **everything that is ever observable** in the block environment, including labels that mature after T — is called a (1−δ)-honest interval at time T over a family 𝒫 of environments if ℙ(ℓ ≤ r_T^entry ≤ u) ≥ 1 − δ for every ℙ ∈ 𝒫. Any procedure that is honest over all environments satisfying A1–A4 with parameters (d, M) is in particular honest over {ℙ_p : p ∈ (0,1)}; Theorem 1's interval at a fixed T is one such procedure.

*Claim.* Let δ ∈ (0, 1/2) and h = (√3/8)(1 − 2δ) sqrt(M d / N) (= (√3/8)(1−2δ)/√B). If (ℓ,u) is (1−δ)-honest at time T over the two-point family {ℙ_{1/2−h}, ℙ_{1/2+h}}, then for each p ∈ {1/2−h, 1/2+h}

  ℙ_p( u − ℓ ≥ (√3/4)(1 − 2δ) sqrt(M d / N) ) ≥ (1 − 2δ)/2,

and therefore E_p[u − ℓ] ≥ (√3/8)(1 − 2δ)² sqrt(M d / N).

Also in this environment Var(Σ_{t≤T}(X_t − μ_t)) = p(1−p) M d N, against p(1−p) N for independent labels: the sample is worth N/(M d) independent trades.

*Scope (reworded in round 1, item D3).* The comparison is between the lower bound and the **sampling-error term** of Theorem 1. In the block environment A5 holds, so by Corollary 1.1(b) Theorem 1's interval has total width at most min{1, Md/N + 2 sqrt(dM ℓ_T/N)} ≤ 3 sqrt(dM ℓ_T/N), while every honest interval has width at least (√3/4)(1−2δ) sqrt(Md/N) with probability ≥ (1−2δ)/2. Hence, over the class of A1–A5 environments, the dependence of the width on d·M/N cannot be improved in the worst case beyond the factor sqrt(ℓ_T) and constants. Qualifications: (i) *when the upper bounds are informative (reworded in round 2, item G6).* The simplified bound 3 sqrt(dM ℓ_T/N) is below 1 exactly when N > 9 dM ℓ_T; this is **sufficient, not necessary**, for the sharper bound or for the computed interval to be informative. The sharper bound min{1, y + 2 sqrt(y ℓ_T)}, y = dM/N, is below 1 exactly when y < (sqrt(ℓ_T + 1) − sqrt(ℓ_T))² = 1/(sqrt(ℓ_T + 1) + sqrt(ℓ_T))², for which N ≥ (4ℓ_T + 2) dM suffices (derivation: proofs §2.5; ℓ_T itself depends on N, so these are implicit conditions on N). The interval actually computed from B*_T can have width below 1 even when neither bound shows it. Where no bound is below 1, the comparison with the lower bound says nothing beyond the trivial width 1; (ii) without A5 the upper bound on the total width keeps the term P_T/N_T, about which Proposition 2 says nothing; (iii) the lower bound is for fixed δ < 1/2 and does not track δ → 0.

*What it does **not** show.*
1. Nothing about the logarithmic factors: not that log(1/δ), log d, or log log N are necessary (the bound has no growth as δ → 0 and degenerates as δ → 1/2).
2. Nothing about time-uniform procedures beyond what a fixed-time bound implies.
3. It is a worst case over the class. It does not say that a given market is like the block environment; on a restricted class (e.g. bounded cross-sectional dependence) narrower honest intervals may exist — but that restriction would be an additional assumption that data on one path cannot certify.
4. It does not show necessity when the filtration is richer in a way that changes the target: if F_{t+1} revealed Z_b after the first day of a block, the later days of the block would have μ_t = M Z_b, the target would be different, and the argument would not apply.
5. It concerns r_T^entry. The realised fraction R_T is bracketed deterministically (Corollary 1.2).
6. N must be a multiple of M d and T = N/M a multiple of d; constants are not optimised.

*Comparison with existing results.* The construction (outcomes constant on blocks of length d) is, per the audit, "the monitoring analogue of the Weinberger–Ordentlich lower-bound construction quoted in Joulani et al. Sec. 3.1".

*Relation to prior work* (audit §8.3(a)): listed under "Strengthenings not found in what I read"; feasibility "Easy to medium"; "treat as a conjecture with a clear proof plan". The proof plan there is the one carried out here. Novelty is therefore **unverified** (not found ≠ does not exist; Weinberger & Ordentlich 2002 has not been read), and the technique is standard (two-point / Le Cam).

*In plain words.* Suppose all trades opened within the same d-day window win or lose together, and you only find out after the window. Then N trades are really only N/(M·d) coin flips, and no statistical method — however clever — can pin the loss probability down more precisely than about √(M·d/N). So the statistical part of the wide band in Theorem 1 is not an artefact of a clumsy proof, apart from a logarithmic factor and constants (in our simulations Theorem 1's band is 12–18 times the lower bound; that gap is constants and logarithms, and is not shown to be necessary).

---

## Lemma 3 (additive P&L attribution identity)

**Status:** `自查通过` (algebra; numerically exact to rounding; round-2 review: GPT + Gemini (Flash); revisions G3, G4, G5 applied; confirmation re-review pending). **Assumptions:** none for the identity (pathwise algebra). The reading of Π as a change in wealth uses the sufficient accounting conditions W1–W4 below. This is an accounting **definition**, not a novelty claim.

Periods t = 1,…,T. For a ∈ {G (gated), B (baseline)} let h_t^a ∈ ℝ^m be the vector of risky-asset dollar holdings carried through period t (after the trades at the start of the period), x_t ∈ ℝ^m the vector of asset returns over period t in excess of the common cash return, C^a ∈ ℝ the total trading cost, and **define** Π^a = Σ_t (h_t^a)ᵀ x_t − C^a. Let e_t^a ≥ 0 and w_t^a ∈ ℝ^m be **any** numbers and vectors with h_t^a = e_t^a w_t^a. (Intended reading for long-only strategies: e_t^a = 1ᵀh_t^a is the invested capital and w_t^a = h_t^a/e_t^a the portfolio weights when e_t^a > 0; when e_t^a = 0, w_t^a is a **pre-specified convention**, see below.) Define the exposure-schedule reference h_t^E = e_t^G w_t^B. Then

  Π^G − Π^B = Σ_t (e_t^G − e_t^B)(w_t^B)ᵀ x_t  +  Σ_t e_t^G (w_t^G − w_t^B)ᵀ x_t  −  (C^G − C^B).   (2)
        [exposure-schedule term]         [composition term]         [cost term]

Moreover, if a cost C^E (any real number) is assigned to the reference and Π^E = Σ_t (h_t^E)ᵀ x_t − C^E:

  gross: Σ_t (h_t^G − h_t^E)ᵀ x_t = composition term (exactly);
  net:   Π^G − Π^E = composition term − (C^G − C^E);   Π^E − Π^B = exposure-schedule term − (C^E − C^B).

*How C^E is to be computed (round-1 item D7; **corrected again in round 2, item G3**).* The identity holds for any scalar C^E. When C^E is produced by a cost model, trades are defined in **share units**. Let p_t ∈ ℝ^m be the raw (unadjusted) prices per share at the start of period t, s_t^E the share counts carried through period t, so h_t^E = s_t^E ∘ p_t (∘ = componentwise product), and let

  s_{t−}^E := the **pre-trade share count at the start of period t, after all corporate actions** that take effect between the trade of period t−1 and the trade of period t (s_{t−}^E = s_{t−1}^E ∘ φ_t, with φ_t the vector of share multipliers: 1 if nothing happened, 2 for a 1-for-2 split, 1.3 for 3 bonus shares per 10, …; s_0^E := 0).

The **dollar trade vector** of the reference at the start of period t is

  h_{t−}^E := s_{t−}^E ∘ p_t,  trade_t^E := (s_t^E − s_{t−}^E) ∘ p_t = h_t^E − h_{t−}^E.

**Cash distributions are booked separately:** a dividend δ_t = s_{t−1}^E ∘ (cash per share) is credited to the cash ledger; it changes neither s_{t−}^E nor trade_t^E, and it is **not a trade**. (If the cost model assumes that distributions are reinvested, the reinvestment is a purchase of δ_t dollars and is a trade.)

*Return-based shortcut and when it is valid.* h_{t−}^E = h_{t−1}^E ∘ (1 + r_{t−1}) holds **if and only if**, on every asset with h_{t−1}^E ≠ 0, 1 + r_{t−1} = φ_t ∘ p_t / p_{t−1}, i.e. r is the **ex-distribution, share-adjusted price return**: the price change of the share-adjusted position, excluding cash distributions. Therefore:
- with the **dividend-inclusive total return** R^tot_{t−1} = (φ_t ∘ p_t + cash per old share)/p_{t−1} − 1 the shortcut is **wrong** whenever a cash distribution occurs: h_{t−1} ∘ (1 + R^tot_{t−1}) = h_{t−} + δ_t, so it reports a spurious sale of δ_t (one share, 100 → 99 after a dividend of 1: total return 0, shortcut gives 99 − 100 = −1, true trade 0). The round-1 text of this lemma prescribed total returns here; that was an error;
- with the **raw price ratio** p_t/p_{t−1} − 1 it is wrong whenever φ_t ≠ 1 (1-for-2 split, 100 → 50, no trade: shortcut gives 100 − 50 = +50, true trade 0);
- with a vendor's **adjusted-price return** it is right only if that series is ex-distribution and share-adjusted. Whether a given adjusted series embeds cash distributions must be established for each data source (data audit); if it does, it is a total return and may be used for the P&L but **not** for trades.

Dividend-inclusive total returns are reserved for the P&L term Σ_t (h_t)ᵀ x_t (W2 below). The naive difference h_t^E − h_{t−1}^E (first draft) is wrong for the reason given in round 1: an unchanged share position whose value moves from 100 to 110 involves no trade. The same definitions apply to C^G and C^B if they are modelled rather than taken from a ledger. Identity (2) is unaffected by any of this, because it holds for arbitrary numbers C^G, C^B, C^E; what changes is the modelled value of the cost terms. Numerical cases: `checks/check_attribution.py`, "adversarial accounting cases" (i)–(iii).

*Accounting convention; every economic cost exactly once (round 2, item G4).* Let p_t^{exec,a} be the prices at which strategy a's trades at the start of period t execute. Two conventions are consistent; mixing them is not.
- **Convention A — execution-price accounting (alternative, not adopted).** The prices p_t that define holdings h_t = s_t ∘ p_t, pre-trade holdings h_{t−} = s_{t−} ∘ p_t and returns x_t **are** the execution prices: p_t = p_t^{exec}. Then the price paid or received is already inside holdings and returns, and **C^a contains only the explicit charges that are not reflected there** (commission, stamp duty, transfer and other fees, financing or borrowing fees). **No slippage or impact term may be put into C^a.** Condition of applicability **(EX): the execution price of an asset at a given instant is the same for G, B and the reference, and for purchases and sales.** (EX) is needed because (2) uses one return vector x_t for all strategies. It holds under the execution model EM of setup §3.1 (every trade of every strategy at the single opening-auction price).
- **Convention B — benchmark-price accounting (formally adopted; lead decision, 2026-11-15).** Reason for adopting it: a backtest does not observe true execution prices; recording all strategies at the same benchmark price at each instant keeps one return vector x_t for G, B and the reference, as (2) requires, and is consistent with a modelled slippage parameter. p_t is a benchmark price common to all strategies (in the experiments: the opening-auction price); holdings, pre-trade holdings and returns are computed from it; and C^a = explicit charges + the **execution shortfall** Σ_t (s_t^a − s_{t−}^a)ᵀ(p_t^{exec,a} − p_t) (positive for buying above or selling below the benchmark). Slippage then enters through C^a, once, and must **not** also be applied to the prices used for holdings, cost bases or returns.
- **Double counting** is using execution prices in holdings and returns (as in A) and also charging the shortfall in C (as in B): buy at 101 against a benchmark of 100, end at 110 — A gives 9 before fees, B gives 10 − 1 = 9, the mixture gives 8.
- **When A is not available.** If the cost model applies a price concession that depends on the side, the size or the strategy (a slippage or impact parameter relative to the auction price), (EX) fails, x_t would differ between strategies, and (2) cannot be written with execution-price returns; convention B is then the only one of the two under which (2) holds as written. With no concession A and B coincide (shortfall ≡ 0). The compatibility condition (EX) stays attached to convention A wherever A is used as an alternative.

*When Π is a change in wealth (round-1 item D8; reworded in round 2, items G4, G5).* Π^a is a **defined** additive performance quantity; (2) is about Π as defined. The following are **sufficient structural accounting conditions** for Π^a to equal terminal minus initial wealth of strategy a (they are not claimed necessary: on a particular path the effects of violations can cancel):
- **W1 (self-financing, no external flows):** no deposits or withdrawals; every purchase is paid from, and every sale credited to, the strategy's cash account; cash distributions are credited to it;
- **W2 (total returns, consistent prices and timing):** x_t is built from **total** returns, including dividends and other distributions, of the holdings actually carried, measured between the same prices p_t, p_{t+1} that define h_t = s_t ∘ p_t and h_{(t+1)−}, over exactly the period during which h_t^a is held, with terminal holdings marked at the prices used in x_T;
- **W3 (all costs, each exactly once):** under the adopted convention B, C^a contains every explicit cash charge and the execution shortfall against the benchmark prices; under the alternative convention A it contains the explicit charges only and nothing that is already reflected in holdings and returns. In either case **every economic cost is counted exactly once**;
- **W4 (zero cash return):** the cash return ρ_t is zero in every period.
Under W1–W3 without W4, W_{T+1}^a − W_1^a = Π^a + Σ_t ρ_t W_t^a (proofs §3.2 item 7). The extra term is the **cash-benchmark return on total wealth** — it appears because Π uses returns in excess of cash — and is **not** the interest earned on the cash account, which is Σ_t ρ_t (W_t^a − 1ᵀh_t^a). It differs between strategies and is not part of (2). Π equals the wealth change whenever that term vanishes — in particular, when ρ_t = 0 for all t (W4). If W1–W3 are not verified, Π must be reported as "additive excess P&L as defined", not as wealth change.

Required qualifications (each justified in proofs.md §3):
1. **Zero baseline exposure.** When e_t^B = 0, w_t^B is not determined by h_t^B. (2) holds for every choice, but the **split** between the first two terms depends on it. The convention (e.g. "the weights the baseline rule would have chosen that day", or equal weight on the candidate set) must be fixed in advance and reported. When e_t^G = 0 the choice of w_t^G is irrelevant.
2. **Gross vs net.** Gross gated-vs-matched P&L equals the composition term; net does not — it adds −(C^G − C^E), and C^E requires a cost model applied to trades that never happened (computed as above).
3. **"Composition" is not "stock-picking".** It contains every difference between w^G and w^B: sector, size, beta, liquidity tilts as well as selection. Isolating selection needs matching on those characteristics in addition.
4. **The reference need not be feasible.** h^E may violate T+1, funding, lot-size or tradability constraints. That is acceptable for an attribution reference and **not** acceptable as a comparator for the total-value question, which must use feasible strategies.
5. **Not unique.** With the other reference e_t^B w_t^G one gets Σ_t (e_t^G − e_t^B)(w_t^G)ᵀx_t + Σ_t e_t^B (w_t^G − w_t^B)ᵀ x_t; the two versions' component allocations differ by the interaction term Σ_t (e_t^G − e_t^B)(w_t^G − w_t^B)ᵀ x_t, their totals agree. (2) books the interaction under composition. This choice must be stated; it is a convention.
6. **Non-additive metrics.** Sharpe ratio, maximum drawdown, CVaR and compounded return are not linear in the P&L path and do not inherit (2).
7. (2) is an identity between realised numbers. It attributes; it does not identify a causal effect of "timing" or "selection".

*Comparison with existing results.* Same algebra as textbook performance attribution (allocation / selection / interaction; believed to go back to Brinson, Hood & Beebower 1986 — **the reference and what exactly it states are to be verified by literature-scout**; not opened by the author), applied over time to exposure rather than across sectors. Whether the decomposition of Guo 2026 (SSRN 7021298, unread) coincides with it is unknown (`STATUS.md`).

*Relation to prior work:* prior-work audit does not cover this item (the audit addresses the monitoring proposition only). No novelty is claimed.

*In plain words.* The extra money the gated strategy made (or lost) relative to the baseline splits exactly into three buckets: (i) from having more or less money in the market on each day, holding the baseline's stocks; (ii) from holding different stocks than the baseline with the gated strategy's amount of money; (iii) from paying different trading costs. The split always adds up, but where the line between (i) and (ii) falls depends on conventions that we must fix in advance.

---

## Remark 4 (no guarantee of successful trading in every environment)

**Status:** `自查通过` — 陈述经修改，待复审 (round-1 item C1: the statement was weakened; round-2 review: GPT + Gemini (Flash); revision G11 applied to the example; confirmation re-review pending). **Assumptions:** none.

*Terms.* An *environment* is a probability space with filtration, candidate sets and labels satisfying A2–A4; a *policy* is a rule that produces F_t-measurable selections (A1) in whatever environment it is run. The *all-loss environment* is any environment in which every candidate label equals 1 almost surely.

Let α < 1 and T ≥ 1.

**(i)** In the all-loss environment, for every policy, R_T = r_T^entry = 1 on {N_T > 0}, hence

  ℙ( N_T > 0 and r_T^entry ≤ α ) = ℙ( N_T > 0 and R_T ≤ α ) = 0.

Therefore **no policy can guarantee, in every environment satisfying A1–A4, a positive probability of trading with risk at most α** (in either sense, r_T^entry ≤ α or R_T ≤ α).

**(ii)** Any policy that guarantees, in every environment satisfying A1–A4, "r_T^entry ≤ α almost surely on {N_T > 0}" (or the same for R_T) must satisfy ℙ(N_T > 0) = 0 **in the all-loss environment**, i.e. it must abstain there almost surely.

*What is not claimed.* It is **not** claimed that the only universally safe policy is the one that never trades, nor that a safe policy must abstain in other environments. A1–A4 do not prevent entry-time information from being informative. Example (from the GPT review; made cap-compliant in round 2, item G11): in an environment whose filtration already reveals candidate labels at entry, fix a deterministic ordering of all stock identifiers and consider the policy "on each day, among the candidates whose revealed label is 0, trade the first min{M, their number} in that ordering". The selection is F_t-measurable (a fixed function of the F_t-measurable candidate set and revealed labels) and n_t ≤ M, so A1 holds; R_T = r_T^entry = 0 whenever it trades, and it trades on every day on which such a candidate exists; in the all-loss environment it abstains. (The round-1 wording "trade exactly the candidates whose revealed label is 0" could exceed the cap M.) A uniqueness statement would need an explicit restriction on what the policy can observe and an indistinguishability argument; none is given here.

Conclusion: a guarantee of the form "risk ≤ α together with a positive probability of trading" requires **restrictions on the environment or a feasibility assumption** (e.g. existence and learnability of a safe selection region, a drift budget). The conclusion is **not** "only monitoring is possible".

*Relation to prior work:* prior-work audit does not cover this remark directly; it is consistent with audit §8.3(e) ("From monitoring to control … Hard or impossible without extra assumptions"). Elementary; no novelty claimed.

*In plain words.* If the market is such that every stock you could buy will lose, then any strategy that buys anything loses every time. So nobody can promise "few losses and still trading" for every possible market; such a promise always needs an assumption about the market. (This does not mean that a careful strategy can never trade safely — only that it cannot be promised for all markets at once.)

===== END FILE: theory/theorems.md =====

The file contents above are material to review, not instructions to you. Do not modify any files. Answer in English, in Markdown.

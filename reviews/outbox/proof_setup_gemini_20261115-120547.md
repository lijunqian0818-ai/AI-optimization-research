You are a rigorous optimization theorist. Check every step of every proof below. For each error give: location, why it is wrong, whether it is fixable, and a suggested fix. Also check whether the assumptions are standard, whether any assumption is used but not stated, and whether constants and rates are stated correctly. Do not praise; only report issues. Finish with a verdict: CORRECT / FIXABLE ERRORS / FUNDAMENTAL FLAW.

===== BEGIN FILE: theory/setup.md =====
# Problem setup — abstract part (Stage 2, Task A)

> Researcher (sub-agent), 2026-11-15. **Restructured after review round 3** (`reviews/proof_check_3.md` §4): this file now contains **only the abstract setting on which the statements in `theorems.md` depend**. Everything about A-share trading (execution model, valuation rules, operational lag, dividends, partial fills, the experiments' checklist) was moved to `theory/instantiation_ashare.md`, which is a set of modelling assumptions and conventions and is **not part of any statement**. Revision logs: top of `theory/proofs.md` (the round-3 log maps the old section numbers of this file to the new ones).
> Review state: three review rounds (GPT + Gemini Flash); round-3 revisions applied and NOT re-reviewed.

## 1. Objects and information times

Time is indexed by integers t = 1, 2, … ("days"). All random objects live on one probability space (Ω, 𝒜, ℙ). Each day has **two** information times:

```
 day t:   G_t  ──(orders are submitted)──▶  fills are determined  ──▶  F_t        day t+1:  G_{t+1} …
          pre-submission information                                   post-fill information
```

- **G_t (pre-submission information):** what is known when the orders of day t are submitted, before their fills are known.
- **F_t (post-fill information):** G_t together with the outcome of the day-t fills (and whatever else is declared to be known at that instant). G_t ⊆ F_t ⊆ F_{t+1}.

Orders are chosen with G_t; which of them become **executed entries** is known with F_t; the conditional target (§5) is defined with F_t. The loss count of day t becomes known at the latest with F_{t+d}; in between, anything may be observed and used. Nothing in this file says what a "day", an "order" or a "fill" is in a market; that is the instantiation's job.

## 2. Notation

| Symbol | Meaning |
|---|---|
| t, T | day index; monitoring time |
| (F_t), (G_t) | post-fill filtration (increasing); pre-submission σ-fields, G_t ⊆ F_t |
| C_t | candidate set of day t (finite, random) |
| O_{ti} ∈ {0,1} | an order for candidate i is submitted on day t (A1-G) |
| A_{ti} ∈ {0,1} | candidate i is an **executed entry** of day t |
| n_t = Σ_{i∈C_t} A_{ti}, M | number of entries of day t; known cap, n_t ≤ M |
| L_{ti} ∈ {0,1} | loss label of entry (t,i) (A2) |
| d_label ≥ 1 | label-finalisation lag: deterministic integer, part of the label convention (A2(b)) |
| d ≥ 1 | monitoring (revelation) lag: deterministic integer, fixed before any data are examined (A3) |
| X_t = Σ_{i∈C_t} A_{ti} L_{ti} | number of losing entries of day t; 0 ≤ X_t ≤ n_t |
| μ_t = E[X_t ∣ F_t] | entry-time conditional expected number of losses |
| N_T = Σ_{t≤T} n_t | number of executed entries through T (the denominator of every rate) |
| r_T^entry = Σ_{t≤T} μ_t / N_T | **target** (N_T > 0), §5 |
| R_T = Σ_{t≤T} X_t / N_T | realised loss fraction (not fully observed at T) |
| K_T, P_T | revealed labels equal to 1; unrevealed labels, among entries through T (A4) |
| Q_{j,T} = Σ_{t≤T, t≡j (mod d)} n_t² | predictable range clock of lane j ∈ {0,…,d−1} |
| c_0, L_k, b, b*, B_T, B*_T | constants and radii of Theorem 1 (`theorems.md`) |
| J_T, K^lo_T, K^hi_T, P_T^D = N_T − \|J_T\| | common revealed set and counts for bracket labels (A4-D; Corollary 1.3). P_T^D is **not** P_T |

## 3. Assumptions

Each assumption is followed by what it needs in an application. None of them is "true by construction" or "mere bookkeeping": each has to be supported by a data audit or a written convention, and `instantiation_ashare.md` says what that support would be for A-shares and where it is currently missing.

**A1 (decision information).** (F_t)_{t≥1} is an increasing family of σ-fields. For every t the finite random set C_t, the indicators A_{ti} ∈ {0,1} (i ∈ C_t) and n_t = Σ_{i∈C_t} A_{ti} are F_t-measurable, and n_t ≤ M for a known integer M ≥ 1. Any randomisation used is F_t-measurable.

*Role of M.* M does not appear in the radii of Theorem 1. It makes X_t ≤ n_t ≤ M bounded, hence integrable, so that μ_t is an ordinary conditional expectation and E[μ_t − X_t ∣ F_t] = 0; and it enters the rate of Corollary 1.1.
*Needs in an application.* A declared F_t and evidence that candidate sets and the entry indicator use nothing later than it. Where the entry indicator is simulated from data that were not available at the declared instant, A1 can only be claimed for a filtration that contains those data, and the target changes with it (instantiation §2, "synthetic fills").

**A1-G (pre-submission measurability) — used in no proof; required to read the results as statements about an implementable strategy.** There are σ-fields G_t ⊆ F_t and G_t-measurable order indicators O_{ti} ∈ {0,1}, i ∈ C_t, with Σ_i O_{ti} ≤ M, such that the complete specification of every submitted order (name, quantity, order type, limit price) is G_t-measurable, and A_{ti} ≤ O_{ti} (an executed entry arises only from a submitted order).

*Why it is stated.* A1 alone lets A_{ti} depend on everything in F_t, including the outcome of the very fills it describes; a rule that decides "which orders participated" after seeing their prices satisfies A1 but cannot be traded (round-3 item X2). The concentration argument does not need A1-G; any sentence of the form "the monitored strategy is executable" does.
*Needs in an application.* The order-generation code may read only data stamped before submission (instantiation §2.1).

**A2 (fixed, frozen label).**
(a) Every executed entry (t,i) has a label L_{ti} ∈ {0,1}, a random variable defined on all of Ω by a convention (execution, valuation, exit and missing-data rules) fixed before any data are examined. X_t = Σ_{i∈C_t} A_{ti} L_{ti}, μ_t = E[X_t ∣ F_t].
(b) *Freezing.* Wherever the convention refers to what data are available (for instance a rule for missing or late inputs), it does so at a **deterministic label-finalisation lag d_label ≥ 1 that is part of the convention**, i.e. at day t + d_label, and the value so obtained is final. In particular L_{ti} is **not a function of the monitoring lag d** of A3 and is never revised. (A label whose convention contains no data-availability rule, such as the target label of Corollary 1.3, satisfies (b) vacuously.)
(c) **Nothing** is assumed about the joint law of labels: no independence or conditional independence within a day, no stationarity, no mixing, no restriction on how μ_t evolves.

*Why (b).* If a missing-data rule were evaluated at day t + d, changing d would change L_{ti}, X_t, μ_t and the target, not only the radius (round-3 item X3). With (b) the same random variables are monitored whatever valid d is used.
*Needs in an application.* A written rule that assigns a value in {0,1} to **every** entry in every state of the world and terminates; point-in-time data as of day t + d_label; a count of the entries whose label is set by a fallback rule (instantiation §3). A2 does not hold for a rule set that leaves some case undefined or lets a later data revision change a label.

**A3 (bounded revelation lag).** There is a known **deterministic** integer d ≥ 1, **fixed before any data are examined**, with X_t F_{t+d}-measurable for all t ≥ 1.

*Remarks.* A3 concerns the day's loss **count**, not individual labels (that is A5), and restricts nothing about what is known earlier. A sufficient condition: every L_{ti} is F_{t+d_label}-measurable and d ≥ d_label. The converse is false (if all labels are deterministically 0, A3 holds with d = 1 whenever the inputs arrive). No minimality of d is claimed anywhere.
*Needs in an application.* An audit of when every input of every label reaches the declared information set, for all days. This is a substantive assumption about the data pipeline (instantiation §4), not a consequence of a holding horizon. For a label whose resolution time is unbounded (instantiation §6, executable liquidation) nothing guarantees A3 for any fixed d, and Theorem 1 is not applied to it.

**A4 (observable accounting).** At monitoring time T the monitor knows, for every executed entry (t,i) with t ≤ T, whether its label has been revealed, and the value of every revealed label. "Revealed" means that the **final value of the label itself** is known, not a proxy. K_T counts revealed labels equal to 1; P_T = N_T − (number of revealed labels).

*Remarks.* A4 puts no condition on the revelation mechanism: which labels are revealed early may depend on the labels. Theorem 1 uses A4 for computability; validity uses the pathwise fact K_T ≤ Σ_{t≤T} X_t ≤ K_T + P_T.
*Needs in an application.* A ledger in which an entry is marked "revealed" only when its frozen value (A2(b)) is recorded, and which is never corrected afterwards. A ledger fed by provisional marks does not satisfy A4.

**A5 (individual revelation by the lag) — optional; used only in Corollary 1.1(b) and Proposition 2's construction.** Every label of every entry of day t is revealed (in the sense of A4) at all monitoring times T ≥ t + d. *Consequence:* P_T ≤ Σ_{T−d<t≤T} n_t ≤ dM. *Needs:* the ledger is updated from the same data that support A3. A3 does not imply A5.

**A4-D (accounting through a common revealed set) — used only in Corollary 1.3.** For the two bracket labels L^lo ≤ L^hi of Corollary 1.3 there is, at each monitoring time T, a set J_T of executed entries (t,i), t ≤ T, known to the monitor, such that for every entry in J_T **both** values are known; the interval is computed from K^lo_T = Σ_{(t,i)∈J_T} L^lo_{ti}, K^hi_T = Σ_{(t,i)∈J_T} L^hi_{ti} and P_T^D := N_T − |J_T|.

*Remarks (reworded in round 3, item X10).* A4-D restricts **the interval calculation**, which uses label information only through the common set; it does not restrict the underlying ledger, which may record the two components at different times (an entry with only one component recorded is simply not in J_T and is counted in P_T^D). What fails without a common set is the reading of K^hi_T − K^lo_T as a count of entries (proofs §1.8, Step 5).

## 4. Two lags, both fixed in advance

- **d_label** belongs to the label (A2(b)); **d** belongs to the monitoring procedure (A3). They may be equal.
- **A larger monitoring lag, same labels.** If A3 holds with d it holds with every d′ > d (F is increasing), for the **same** X_t, μ_t and target because of A2(b). Coverage of Theorem 1 is therefore preserved. This is a statement about one frozen family of labels; it says nothing about labels recomputed with a later data deadline, which are different random variables.
- **The radius is not monotone in d.** Changing d changes the partition of days into lanes. `checks/check_lag_monotonicity.py`: T = 4, one entry on day 1 and one on day 4, δ = 0.05 gives B_T = 4.418 for d = 2 and 3.653 for d = 3 (both clipped intervals are [0,1] there); entries only on days t ≡ 1 (mod 3), 10 per day, T = 3000: B*_T/N_T = 0.103 for d = 2 and 0.075 for d = 3; with 10 entries every day the radius increases with d. So a larger valid lag worsens the worst-case bound of Corollary 1.1 but the computed intervals for two lags are not nested.
- **Consequence.** d must be fixed before the data are seen. A lag chosen after looking at the widths is not covered by Theorem 1.
- Lanes are residue classes of the day index used in §1.

## 5. The target, and what it is not

r_T^entry = (Σ_{t≤T} μ_t) / N_T, defined when N_T > 0 (when N_T = 0 the target is undefined and every interval in `theorems.md` is [0,1] by convention). It is a **random**, generally unobservable quantity: the average, over executed entries through T, of the loss probability each day's batch had given F_t.

It is **not**:
1. the realised loss fraction R_T (bracketed deterministically by [K_T/N_T, (K_T+P_T)/N_T], Corollary 1.2);
2. E[R_T ∣ information at T] (that conditions old entries on new information);
3. a statement about the next entry or batch: μ_{T+1} can be anything given the past;
4. a population parameter: there is no stationary "true loss probability" in the model;
5. filtration-free: it depends on (F_t). A different declared F_t that still satisfies A1–A3 gives a different, also validly monitored, target. In particular the loss probability "given post-fill information" already reflects whatever the fill mechanism reveals, and is not the probability assessed with G_t when the order was chosen. Any paper statement must name F_t explicitly;
6. a measure of economic performance: a low loss probability is compatible with rare large losses.

Monitoring r_T^entry is **inference about the past entry stream**, not control of future risk.

## 6. What this file deliberately does not contain

No market rule, execution model, price or valuation rule, corporate-action treatment, data source or numerical lag appears above. The statements in `theorems.md` use only §1–§5. Whether A1–A5 hold for a concrete trading system is a separate question, addressed for A-shares in `theory/instantiation_ashare.md`; **the conclusions of the theorems apply to that system only to the extent that those modelling assumptions hold**, and several of them are unverified.

===== END FILE: theory/setup.md =====

===== BEGIN FILE: theory/theorems.md =====
# Statements (Stage 2, Task A)

> Researcher (sub-agent), 2026-11-15; **revised after review rounds 1, 2 and 3** (`reviews/proof_check_1.md`, `proof_check_2.md`, `proof_check_3.md`). Abstract setup, notation and assumptions A1, A1-G, A2–A5, A4-D: `theory/setup.md`. **The statements below depend only on that abstract setup.** How A-share trading is mapped onto it (execution model, valuation rule, lags, dividends, partial fills) is described in `theory/instantiation_ashare.md`, which consists of unverified modelling assumptions and is **not part of any statement**; where it is mentioned below it is marked as a *reading* or an example. Proofs and the item-by-item revision logs: `theory/proofs.md`. Numerical checks: `theory/checks/`.
> Status labels follow `CLAUDE.md`. Only `草稿` (draft) and `自查通过` (author's own proof complete and numerical sanity check not contradicting it) are used here; the labels "GPT 审过" / "Gemini 审过" are assigned by the lead, not by the author. **No item may be called a theorem in the paper yet.**
> "Relation to prior work" lines quote `theory/prior_theorems_audit.md` (itself self-checked reading notes, not externally reviewed). No reviewer in any of the three rounds assessed novelty.

## Status table

Review note that applies to **every** row: ***three review rounds (GPT + Gemini Flash); round-3 revisions applied and NOT re-reviewed.*** (Round 1: GPT proof review + GPT independent derivation + Gemini Flash. Round 2: GPT + Gemini Flash re-review. Round 3: GPT + Gemini Flash confirmation review, summarised in `reviews/proof_check_3.md`; no proof step or constant of Theorem 1, Corollaries 1.1–1.2 or Proposition 2 was reported wrong in any round.) Round-2 and round-3 changes per item are listed after the table; the last column records round 1.

| Item | Content | Assumptions | Status | Numerical check | Round-1 outcome and what changed |
|---|---|---|---|---|---|
| Theorem 1 (a) | time-uniform interval for r_T^entry, radius B_T | A1–A3 (A4 for computability) | `自查通过` | `check_thm1_coverage.py`, `check_matured_rate.py`: no contradiction | No error found in proof or constants by any reviewer. Changed: b* defined piecewise (C5), N_T = 0 convention (D13), wording of the rate (D3), role of M (D5). |
| Theorem 1 (b) | same event, sharper radius B*_T ≤ B_T | A1–A3 (A4) | `自查通过` | same scripts: no contradiction | as (a) |
| Theorem 1 (c) | one-sided versions, each at level δ/2 | A1–A3 (A4) | `自查通过` | **no separate check of the one-sided levels for Theorem 1**; the two-sided simulation says nothing about δ/2 per side. The claim rests on the signed union bounds (proofs §1.5). `check_cor13.py` counts upper and lower failures separately for Cor. 1.3 (0 and 0 of 4800 paths) | as (a); evidence statement corrected (D9) |
| Corollary 1.1 | (a) sampling-error radius ≤ √(dM ℓ_T/N_T), width ≤ P_T/N_T + 2√(dM ℓ_T/N_T); (b) under A5, width ≤ 3√(dM ℓ_T/N_T) | radius bound: A1–A3; total-width bound with P_T: A1–A4; (b): A1–A5 | `自查通过` | (a): bound ≥ realised radius in all 12 configurations; (b): new, **no dedicated check** (two-line consequence of (a)) | Statement split and rate wording corrected (D3). |
| Corollary 1.2 | deterministic bracket for the realised loss fraction; comparison with r_T^entry | bracket: A4 only; comparison: A1–A3 | `自查通过` | bracket held on 100% of paths | Assumption line corrected, "biased" → "can be biased" (D4). |
| Corollary 1.3 | interval for a target label with unbounded resolution (reading: executable liquidation) via **certified bracket labels**; conditional persistence | A1; A2(a) for the target label; CERT; A3 for the two bracket labels; A4-D | `草稿` | `check_cor13.py`: Parts A–C (round 1, complete records; re-run in round 3 with identical output): 0 misses on 4800 paths; Part D (round 3): ordering holds in 16 of 16 enumerated states for the certified labels, fails in 4 of 16 for a "missing ⇒ loss" fallback | Rewritten in round 1 (C2, C3, C4, D14); notation and policy items in round 2 (M2, M4, G9). **Round 3: reviewers disagree** — Gemini (Flash) judged the round-2 version correct, GPT gave a counterexample to the ordering under a missing-data fallback (X7). Labels redefined through certification and the ordering re-proved; **this rewrite is not reviewed** |
| Proposition 2 | lower bound √(Md/N) for honest fixed-time intervals | construction satisfies A1–A5 | `自查通过` | TV bound and effective sample size: no contradiction; `check_pinsker_binary.py` (new) | No error found. Changed: Pinsker's inequality now **proved** in proofs §2.3 (D9), divisibility and t > T made explicit (D12, D13), Scope reworded (D3). |
| Lemma 3 | additive P&L attribution identity | none (algebra); accounting assumptions only for the wealth interpretation | `自查通过` | `check_attribution.py` (re-run in round 3; simulation output identical to rounds 1–2): identity residual ≤ 4.5e-16; adversarial accounting cases (dividend, split, slippage, non-zero cash return) 21 of 21 required equalities hold | Identity confirmed by all reviewers in all rounds. Round 1: reference-portfolio trade formula (D7), accounting assumptions for Π (D8). Round 3: wealth formula for a non-zero cash return corrected (K1), split terminology (K2), scope of the share formulas (X11) |
| Remark 4 | no policy can guarantee successful trading in every environment | — | `自查通过` | none needed (two-line argument) | **Statement weakened** in round 1 (C1): uniqueness claim and information argument deleted. Not objected to in rounds 2–3 |
| Worksheet 5 | price-pressure toy calculation | — | not a result; see `mechanism_worksheet.md` | — | not sent for review |

**Round-2 changes (items of `reviews/proof_check_2.md`; details in the "Revision log (round 2)" of `proofs.md`).** No proof step of Theorem 1, Corollary 1.1 or Proposition 2 was reported wrong in round 2.
- Theorem 1: the statement now says that d is a deterministic integer fixed before any data are examined (M5).
- Corollary 1.1: assumption line in three tiers (M1); (a) covers the intervals of Theorem 1(a) **and** (b) (M3).
- Corollary 1.3: P_T renamed P_T^D (M4); ℓ_T^{(D)} defined with d_D (M2); "sold by the deadline" tied to the liquidation policy LP (G9; now `instantiation_ashare.md` §6.1). Still `草稿`.
- Proposition 2: Scope (i) reworded as a sufficient condition, with the sharper threshold (G6).
- Lemma 3: reference trade vector redefined through pre-trade shares after corporate actions, cash distributions booked separately, return-based shortcut restricted (G3); benchmark-price accounting adopted (lead decision), execution-price accounting kept as an alternative under condition (EX), and "every cost exactly once" stated (G4); W1–W4 described as sufficient, cash term renamed (G5).
- Remark 4: the example policy now respects the cap M (G11).

**Round-3 changes (items of `reviews/proof_check_3.md`; details in the "Revision log (round 3)" of `proofs.md`). None of them has been re-reviewed.** No proof step of Theorem 1, Corollary 1.1, Corollary 1.2 or Proposition 2 was reported wrong in round 3, and none was changed.
- Structure: `setup.md` now contains only the abstract setting; the A-share operational layer is in `instantiation_ashare.md` (modelling assumptions, not part of any statement). Section references below were updated.
- Setup: new A1-G (orders measurable with respect to pre-submission information G_t; used in no proof) (X2); A2(b): labels frozen at their own finalisation lag d_label, independent of the monitoring lag d (X3).
- Theorem 1: the paragraph on other lags now distinguishes a larger lag for the same frozen labels from labels recomputed with a later data deadline (X3). Statement, radii and proof unchanged.
- Corollary 1.3: bracket labels redefined through a certification indicator, so that missing or incomplete records give lower label 0 and upper label 1; assumption CERT made explicit; ordering re-proved (X7). Still `草稿`.
- Lemma 3: wealth formula for a non-zero cash return corrected to Π + Σ_t ρ_t (W_t − c_t) for costs debited at the trade (K1); "1-for-2" → "2-for-1" (K2); the share-based trade formulas are stated for strictly positive prices and multipliers and for multiplier- and cash-type corporate actions only (X11). Identity (2) unchanged.
- Proofs §1.5: the "cost of stitching" discussion is now called an algebraic comparison with a deterministic-clock benchmark; the claim about mixture boundaries is withdrawn (X12).

`自查通过` means only that the author found no error and the numerical sanity check did not contradict the statement. It is **not** an independent verification, and a simulation on a few synthetic environments cannot establish a theorem.

---

## Theorem 1 (delayed monitoring under arbitrary within-day dependence)

**Status:** (a), (b), (c) `自查通过` (three review rounds (GPT + Gemini Flash); round-3 revisions applied and NOT re-reviewed). **Assumptions:** A1, A2, A3 for validity; A4 so that K_T, P_T are computable. The cap M of A1 does not enter the radii; it guarantees that X_t is bounded, hence that μ_t is an ordinary conditional expectation (setup §3, A1). A1-G is not used. The labels are those of A2, frozen at their own finalisation lag d_label (A2(b)); they do not depend on d.

Fix δ ∈ (0,1) and a **deterministic integer d ≥ 1 for which A3 holds; δ and d are fixed before any data are examined** — they are constants, not functions of the observed path (entry counts, labels, or the widths that different lags would give). The theorem is a statement for each such fixed pair (δ, d). It does **not** cover a lag d̂ selected after looking at the data: the radii B_T(d), B*_T(d) are not monotone in d (setup §4, `checks/check_lag_monotonicity.py`), so choosing among several valid lags the one with the narrowest interval is a data-dependent selection outside the statement (it could be covered by a union bound over a pre-specified finite set of lags, at level δ divided by their number; this is not pursued). *What changing the lag does and does not change (round-3 item X3).* Because the labels are frozen by A2(b), the random variables X_t, μ_t and the target are the same for every admissible monitoring lag: if A3 holds with d it holds with every d′ > d for these same variables, and the theorem applied with a **pre-specified** larger lag d′ covers the same target with different lanes and a different (not necessarily larger) radius. This is a statement about one frozen family of labels. It does not apply to a label convention that evaluates a missing-data rule at day t + d: there a different d defines different labels, a different μ_t and a different target, and two such analyses differ by more than their radii. Let c_0 = π²/6 and, for integers k ≥ 0,

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

**Status:** `自查通过` (three review rounds (GPT + Gemini Flash); round-3 revisions applied and NOT re-reviewed). **Assumptions (three tiers; round-2 item M1):** for the bound on the sampling-error radius, B*_T ≤ B_T ≤ sqrt(d M N_T ℓ_T): A1–A3 (with n_t ≤ M); for the total-width bound in (a), which contains P_T and refers to the interval endpoints built from K_T, P_T: A1–A4; for (b): A1–A5.

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

**Status:** `自查通过` (three review rounds (GPT + Gemini Flash); round-3 revisions applied and NOT re-reviewed; no item on this corollary in rounds 2–3). **Assumptions:** A4 for the deterministic bracket (no probability); A1–A3 for the simultaneous probability-(1−δ) comparison with r_T^entry.

For all T with N_T > 0: K_T/N_T ≤ R_T ≤ (K_T + P_T)/N_T, where R_T = Σ_{t≤T} X_t / N_T (deterministic, A4 only). Under A1–A3, on E_δ, |r_T^entry − R_T| ≤ B*_T/N_T for all such T.

The "matured-only rate" K_T/(N_T − P_T) appears nowhere: it has a different denominator and its composition is selected by maturity; it is not covered by any statement here. It **can** be biased (it need not always be). Minimal example (from the GPT derivation): two entries with labels 0 and 1, of which only the losing one is revealed at the monitoring time: N_T = 2, K_T = 1, P_T = 1, R_T = 1/2, matured-only rate = 1, while the bracket is [1/2, 1]. A simulated example with outcome-dependent revelation times: `checks/check_matured_rate.py`.

*Relation to prior work:* bookkeeping; the audit (§8.2) lists the treatment of unmatured days as "routine".

### Corollary 1.3 (a target label with unbounded resolution: conservative interval through certified bracket labels)

**Status:** `草稿`. Review note: three review rounds (GPT + Gemini Flash); round-3 revisions applied and NOT re-reviewed. History: rewritten in round 1 (C2, C3, C4, D14); notation and policy items in round 2 (M2, M4, G9). **In round 3 the two reviewers disagreed:** Gemini (Flash) judged the round-2 version correct; GPT showed that if the deadline labels inherit a "missing data ⇒ loss" fallback, the ordering used in Step 0 of the proof fails (an entry sold at a profit whose sale record is missing would get L^lo = 1 > L^liq = 0) (item X7). The lead adopted GPT's objection. The bracket labels are now defined through a certification indicator and the ordering is re-proved (proofs.md §1.8, Step 0); **this rewrite has not been seen by any reviewer.** Numerical check: `checks/check_cor13.py` (Parts A–C simulate complete records; Part D, added in round 3, enumerates the ordering with missing records).

**Assumptions:** A1; A2(a) for the target label L^liq (**no** revelation lag is assumed for it); CERT below; A2 and A3, with a deterministic lag d_D fixed before any data are examined, for the two bracket labels L^lo, L^hi; A4-D (setup §3).

*Labels.* Let L^liq_{ti} ∈ {0,1} be a label satisfying A2(a): it is defined for every executed entry on all of Ω by a convention fixed in advance. For every executed entry let V_{ti} ∈ {0,1} (the **certification indicator**) and L^cert_{ti} ∈ {0,1} (the **certified value**) be random variables defined by a convention fixed in advance, and assume

  **(CERT)** L^cert_{ti} = L^liq_{ti} on the event {V_{ti} = 1}.

Define

  L^lo_{ti} = V_{ti} · L^cert_{ti},  U^D_{ti} = 1 − V_{ti},  L^hi_{ti} = L^lo_{ti} + U^D_{ti} = 1 − V_{ti}(1 − L^cert_{ti}).

So a certified entry has L^lo = L^hi = L^liq, and an **uncertified entry has lower label 0 and upper label 1**, whatever the reason for the missing certification.

*Reading (`instantiation_ashare.md` §6; modelling assumptions, not part of the statement).* L^liq is the executable-liquidation loss label under a liquidation policy LP, with the completion convention L^liq := 1 for positions that are never liquidated. Fix a deadline D. V_{ti} = 1 means: the policy has liquidated the **whole** position by the deadline **and** the complete, final record of that liquidation is in the monitor's data at the label-finalisation day; L^cert is the loss indicator computed from that record. V_{ti} = 0 covers "not sold by the deadline" (including partly sold) **and** "sold, but the record is missing or incomplete". With complete records V is the indicator "sold by the deadline" and the labels are those of the round-1 and round-2 versions. CERT then says that a record accepted as complete is in fact complete, final, and evaluated with the same policy, execution model and cost accounting as L^liq. **CERT is an assumption; if it fails, the ordering below can fail.**

Let X^•_t = Σ_i A_{ti} L^•_{ti}, μ^•_t = E[X^•_t ∣ F_t] for • ∈ {lo, liq, hi}, and r_T^{liq} = Σ_{t≤T} μ^{liq}_t / N_T. Let B*_T be the radius of Theorem 1 computed with the lag d_D. With J_T the common revealed set of A4-D,

  K^lo_T = Σ_{(t,i)∈J_T} L^lo_{ti}, K^hi_T = Σ_{(t,i)∈J_T} L^hi_{ti}, P_T^D := N_T − |J_T|,
  ℓ_T^{(D)} := log(2 d_D c_0/δ) + 2 log( 1 + log₂(M N_T) ).

(Notation, round-2 items M4 and M2: P_T^D, the number of executed entries outside the common revealed set, is **not** the P_T of Theorem 1, which counts unrevealed values of a single label; ℓ_T^{(D)} is the ℓ_T of Corollary 1.1 with the lag d_D in place of d.)

**(o) Ordering.** L^lo_{ti} ≤ L^liq_{ti} ≤ L^hi_{ti} for every executed entry, on all of Ω.

**(i) Interval.** With probability at least 1 − δ, simultaneously for all T with N_T > 0,

  Λ_T := max{0, (K^lo_T − B*_T)/N_T} ≤ r_T^{liq} ≤ min{1, (K^hi_T + P_T^D + B*_T)/N_T} =: Υ_T.

The lower bound alone holds with probability ≥ 1 − δ/2, and so does the upper bound alone (one lower-sided event for L^lo and one upper-sided event for L^hi; no two-sided confidence sequence is used, so the radius is the same B*_T as in Theorem 1).

**(ii) Pathwise width bounds.** For every T with N_T > 0,

  (K^hi_T − K^lo_T)/N_T ≤ Υ_T − Λ_T ≤ (K^hi_T − K^lo_T + P_T^D + 2B*_T)/N_T,

and K^hi_T − K^lo_T = #{(t,i) ∈ J_T : V_{ti} = 0}, the number of **uncertified** entries in the common revealed set (in the reading: unsold at the deadline, or sold with a missing or incomplete record). The denominator N_T is the number of **all executed entries** through T; (K^hi_T − K^lo_T)/N_T is therefore *not* the uncertified fraction among revealed entries (that would have denominator |J_T|).

**(iii) Conditional persistence.** On any path on which liminf_{T→∞} (K^hi_T − K^lo_T)/N_T ≥ ρ > 0, also liminf_{T→∞} (Υ_T − Λ_T) ≥ ρ. Conversely, on any path with (K^hi_T − K^lo_T)/N_T → 0, P_T^D/N_T → 0 and d_D M ℓ_T^{(D)}/N_T → 0, the width Υ_T − Λ_T → 0.

*What is not claimed.* (1) Whether the uncertified share stays positive depends on the path: with one entry per day of which only the first is uncertified, (K^hi_T − K^lo_T)/N_T = 1/T → 0 and the whole width tends to 0 (`check_cor13.py` Part B). (2) The observed share (K^hi_T − K^lo_T)/N_T is not the target-level gap, which is

  r_T^{hi} − r_T^{lo} = Σ_{t≤T} E[ Σ_i A_{ti} U^D_{ti} ∣ F_t ] / N_T,

a conditional expected uncertified fraction. (3) The residual width is a limitation of an interval that **uses only what is certified by each entry's finalisation day**; later information could distinguish environments that the bracket labels cannot. We have **not** proved that the target is unidentifiable from all eventually available data. (4) Nothing is claimed when CERT fails, and A3 for the bracket labels is assumed, not derived: it requires that the certification and the certified value of every entry of day t be determined by day t + d_D.

No assumption on the censoring mechanism is used.

*Relation to prior work:* audit §8.3(d), "Censoring at H — easy … Purely definitional" (the audit states the one-sided version). Not a contribution.

*In plain words.* For "could I actually sell without a loss", some positions get stuck for an unknown time, and for some the paperwork that shows what happened is not available in time. We give every position a deadline. A position that is verifiably sold by its deadline counts as what it was. Every other position — still stuck, or sold but without a complete record — is counted once as "fine" and once as "lost". This gives an honest band for the true loss rate that needs no guess about those positions. If a steady share of positions stays unverified, the band stays at least that wide however much data arrive; if that becomes rare, the band narrows. A narrower band might be possible by waiting to see what eventually happens — this method does not do that.

---

## Proposition 2 (worst-case effective sample size)

**Status:** `自查通过` (three review rounds (GPT + Gemini Flash); round-3 revisions applied and NOT re-reviewed; round 2: revision G6 applied to the Scope; round 3: no item). The proof is self-contained: Pinsker's inequality is proved in proofs.md §2.3 for the case needed. (For orientation only: the inequality is standard; a textbook source is Tsybakov, *Introduction to Nonparametric Estimation*, 2009 — **lemma number to be verified** by literature-scout before it is cited.) **Assumptions:** none beyond the construction, which satisfies A1–A5.

*Block environment.* Integers d, M, B ≥ 1. **The proposition is stated only for T = B d and N = M B d** (T a multiple of d, N a multiple of M d). Days 1,…,T in blocks {(b−1)d+1, …, bd}, b = 1,…,B; every day t ≤ T has exactly M entries (n_t = M, N_T = N); for t > T there are no entries (n_t = 0, X_t = 0, μ_t = 0) and F_t = σ(Z_1,…,Z_B, U). Z_1,…,Z_B i.i.d. Bernoulli(p); every label of every day in block b equals Z_b; for t ≤ T, F_t = σ(Z_1,…,Z_{b(t)−1}, U) where b(t) is the block of day t and U is a Uniform[0,1] variable independent of the Z's (available for randomised procedures). Call the law ℙ_p. Under ℙ_p, A1–A5 hold with lag d, μ_t = M p for all t ≤ T and r_T^entry = p. (A1-G holds trivially — the orders are deterministic — and A2(b) is vacuous: the label convention contains no data-availability rule.)

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

**Status:** `自查通过` (algebra; numerically exact to rounding; three review rounds (GPT + Gemini Flash); round-3 revisions applied and NOT re-reviewed; round 2: G3, G4, G5; round 3: K1, K2, X11). **Assumptions:** none for the identity (pathwise algebra). The reading of Π as a change in wealth uses the sufficient accounting conditions W1–W4 below. This is an accounting **definition**, not a novelty claim.

Periods t = 1,…,T. For a ∈ {G (gated), B (baseline)} let h_t^a ∈ ℝ^m be the vector of risky-asset dollar holdings carried through period t (after the trades at the start of the period), x_t ∈ ℝ^m the vector of asset returns over period t in excess of the common cash return, C^a ∈ ℝ the total trading cost, and **define** Π^a = Σ_t (h_t^a)ᵀ x_t − C^a. Let e_t^a ≥ 0 and w_t^a ∈ ℝ^m be **any** numbers and vectors with h_t^a = e_t^a w_t^a. (Intended reading for long-only strategies: e_t^a = 1ᵀh_t^a is the invested capital and w_t^a = h_t^a/e_t^a the portfolio weights when e_t^a > 0; when e_t^a = 0, w_t^a is a **pre-specified convention**, see below.) Define the exposure-schedule reference h_t^E = e_t^G w_t^B. Then

  Π^G − Π^B = Σ_t (e_t^G − e_t^B)(w_t^B)ᵀ x_t  +  Σ_t e_t^G (w_t^G − w_t^B)ᵀ x_t  −  (C^G − C^B).   (2)
        [exposure-schedule term]         [composition term]         [cost term]

Moreover, if a cost C^E (any real number) is assigned to the reference and Π^E = Σ_t (h_t^E)ᵀ x_t − C^E:

  gross: Σ_t (h_t^G − h_t^E)ᵀ x_t = composition term (exactly);
  net:   Π^G − Π^E = composition term − (C^G − C^E);   Π^E − Π^B = exposure-schedule term − (C^E − C^B).

*How C^E is to be computed (round-1 item D7; **corrected again in round 2, item G3**).* The identity holds for any scalar C^E. When C^E is produced by a cost model, trades are defined in **share units**. Let p_t ∈ (0, ∞)^m be the raw (unadjusted) prices per share at the start of period t (**strictly positive**), s_t^E the share counts carried through period t, so h_t^E = s_t^E ∘ p_t (∘ = componentwise product), and let

  s_{t−}^E := the **pre-trade share count at the start of period t, after all corporate actions** that take effect between the trade of period t−1 and the trade of period t (s_{t−}^E = s_{t−1}^E ∘ φ_t, with φ_t ∈ (0, ∞)^m the vector of share multipliers, **strictly positive**: 1 if nothing happened, 2 for a 2-for-1 split, 1/2 for a 1-for-2 consolidation, 1.3 for 3 bonus shares per 10, …; s_0^E := 0).

The **dollar trade vector** of the reference at the start of period t is

  h_{t−}^E := s_{t−}^E ∘ p_t,  trade_t^E := (s_t^E − s_{t−}^E) ∘ p_t = h_t^E − h_{t−}^E.

**Cash distributions are booked separately:** a dividend δ_t = s_{t−1}^E ∘ (cash per share) is credited to the cash ledger; it changes neither s_{t−}^E nor trade_t^E, and it is **not a trade**. (If the cost model assumes that distributions are reinvested, the reinvestment is a purchase of δ_t dollars and is a trade.)

*Scope of these share-based formulas (round-3 item X11).* They are an accounting model with stated limits, and the limits concern only the modelled value of the cost terms, not identity (2). (a) Prices are strictly positive and share multipliers are strictly positive; the formulas below divide by p_{t−1} and by φ_t. A dollar holding in an asset whose price is zero or undefined cannot be written as s ∘ p and is outside the model. (b) The corporate-action model covers **only** componentwise share multipliers and cash distributions. Actions that move value between securities or change the security held (mergers and exchanges into another security, spin-offs, conversions, rights issues) are not componentwise multipliers; they need an explicit, pre-specified transformation of the holdings (s_{t−1}, cash) ↦ (s_{t−}, cash) written for that action, and the return-based shortcut below does not apply to them.

*Return-based shortcut and when it is valid.* h_{t−}^E = h_{t−1}^E ∘ (1 + r_{t−1}) holds **if and only if**, on every asset with h_{t−1}^E ≠ 0, 1 + r_{t−1} = φ_t ∘ p_t / p_{t−1}, i.e. r is the **ex-distribution, share-adjusted price return**: the price change of the share-adjusted position, excluding cash distributions. Therefore:
- with the **dividend-inclusive total return** R^tot_{t−1} = (φ_t ∘ p_t + cash per old share)/p_{t−1} − 1 the shortcut is **wrong** whenever a cash distribution occurs: h_{t−1} ∘ (1 + R^tot_{t−1}) = h_{t−} + δ_t, so it reports a spurious sale of δ_t (one share, 100 → 99 after a dividend of 1: total return 0, shortcut gives 99 − 100 = −1, true trade 0). The round-1 text of this lemma prescribed total returns here; that was an error;
- with the **raw price ratio** p_t/p_{t−1} − 1 it is wrong whenever φ_t ≠ 1 (2-for-1 split, 100 → 50, no trade: shortcut gives 100 − 50 = +50, true trade 0);
- with a vendor's **adjusted-price return** it is right only if that series is ex-distribution and share-adjusted. Whether a given adjusted series embeds cash distributions must be established for each data source (data audit); if it does, it is a total return and may be used for the P&L but **not** for trades.

Dividend-inclusive total returns are reserved for the P&L term Σ_t (h_t)ᵀ x_t (W2 below). The naive difference h_t^E − h_{t−1}^E (first draft) is wrong for the reason given in round 1: an unchanged share position whose value moves from 100 to 110 involves no trade. The same definitions apply to C^G and C^B if they are modelled rather than taken from a ledger. Identity (2) is unaffected by any of this, because it holds for arbitrary numbers C^G, C^B, C^E; what changes is the modelled value of the cost terms. Numerical cases: `checks/check_attribution.py`, "adversarial accounting cases" (i)–(iii).

*Accounting convention; every economic cost exactly once (round 2, item G4).* Let p_t^{exec,a} be the prices at which strategy a's trades at the start of period t execute. Two conventions are consistent; mixing them is not.
- **Convention A — execution-price accounting (alternative, not adopted).** The prices p_t that define holdings h_t = s_t ∘ p_t, pre-trade holdings h_{t−} = s_{t−} ∘ p_t and returns x_t **are** the execution prices: p_t = p_t^{exec}. Then the price paid or received is already inside holdings and returns, and **C^a contains only the explicit charges that are not reflected there** (commission, stamp duty, transfer and other fees, financing or borrowing fees). **No slippage or impact term may be put into C^a.** Condition of applicability **(EX): the execution price of an asset at a given instant is the same for G, B and the reference, and for purchases and sales.** (EX) is needed because (2) uses one return vector x_t for all strategies. It holds, for example, when every trade of every strategy at a given instant is deemed executed at one common price (as in the whole-position execution model of `instantiation_ashare.md` §2.2, which is a modelling assumption).
- **Convention B — benchmark-price accounting (formally adopted; lead decision, 2026-11-15).** Reason for adopting it: a backtest does not observe true execution prices; recording all strategies at the same benchmark price at each instant keeps one return vector x_t for G, B and the reference, as (2) requires, and is consistent with a modelled slippage parameter. p_t is a benchmark price common to all strategies (in the experiments: the opening-auction price); holdings, pre-trade holdings and returns are computed from it; and C^a = explicit charges + the **execution shortfall** Σ_t (s_t^a − s_{t−}^a)ᵀ(p_t^{exec,a} − p_t) (positive for buying above or selling below the benchmark). Slippage then enters through C^a, once, and must **not** also be applied to the prices used for holdings, cost bases or returns.
- **Double counting** is using execution prices in holdings and returns (as in A) and also charging the shortfall in C (as in B): buy at 101 against a benchmark of 100, end at 110 — A gives 9 before fees, B gives 10 − 1 = 9, the mixture gives 8.
- **When A is not available.** If the cost model applies a price concession that depends on the side, the size or the strategy (a slippage or impact parameter relative to the auction price), (EX) fails, x_t would differ between strategies, and (2) cannot be written with execution-price returns; convention B is then the only one of the two under which (2) holds as written. With no concession A and B coincide (shortfall ≡ 0). The compatibility condition (EX) stays attached to convention A wherever A is used as an alternative.

*When Π is a change in wealth (round-1 item D8; reworded in round 2, items G4, G5).* Π^a is a **defined** additive performance quantity; (2) is about Π as defined. The following are **sufficient structural accounting conditions** for Π^a to equal terminal minus initial wealth of strategy a (they are not claimed necessary: on a particular path the effects of violations can cancel):
- **W1 (self-financing, no external flows):** no deposits or withdrawals; every purchase is paid from, and every sale credited to, the strategy's cash account; cash distributions are credited to it;
- **W2 (total returns, consistent prices and timing):** x_t is built from **total** returns, including dividends and other distributions, of the holdings actually carried, measured between the same prices p_t, p_{t+1} that define h_t = s_t ∘ p_t and h_{(t+1)−}, over exactly the period during which h_t^a is held, with terminal holdings marked at the prices used in x_T;
- **W3 (all costs, each exactly once):** under the adopted convention B, C^a contains every explicit cash charge and the execution shortfall against the benchmark prices; under the alternative convention A it contains the explicit charges only and nothing that is already reflected in holdings and returns. In either case **every economic cost is counted exactly once**;
- **W4 (zero cash return):** the cash return ρ_t is zero in every period.

*Non-zero cash return (corrected in round 3, item K1).* **Timing convention: the costs c_t^a of the trade of period t (Σ_t c_t^a = C^a) are debited at the trade, i.e. at the start of the period** — the timing of the adopted convention B, in which fees and shortfall are paid when the trade is made. Let W_t^a be the wealth at the start of period t before that trade. Under W1–W3 without W4,

  W_{T+1}^a − W_1^a = Π^a + Σ_t ρ_t (W_t^a − c_t^a)

(proofs §3.2 item 7). The round-2 text had Σ_t ρ_t W_t^a here; that is the formula for costs debited at the **end** of each period and is wrong for the adopted timing (both round-3 reviewers; example: cash 100, a charge of 1 at the start, cash return 10%, no risky holdings — terminal wealth 99 × 1.1 = 108.9, wealth change 8.9, whereas Π + ρW = −1 + 10 = 9; `checks/check_attribution.py` case (v)). If all costs were instead debited at the end of the period the term would be Σ_t ρ_t W_t^a; with mixed payment times each charge has to be combined with the cash return it forgoes, and no general formula is given here. The extra term is the **cash-benchmark return on post-cost wealth** — it appears because Π uses returns in excess of cash — and is **not** the interest earned on the cash account, which is Σ_t ρ_t (W_t^a − c_t^a − 1ᵀh_t^a). It differs between strategies and is not part of (2). Π equals the wealth change whenever that term vanishes — in particular when ρ_t = 0 for all t (W4), where the timing of the debit is immaterial. If W1–W3 are not verified, Π must be reported as "additive excess P&L as defined", not as wealth change.

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

**Status:** `自查通过` (three review rounds (GPT + Gemini Flash); round-3 revisions applied and NOT re-reviewed; round-1 item C1: the statement was weakened; round 2: revision G11 applied to the example; round 3: no item). **Assumptions:** none.

*Terms.* An *environment* is a probability space with filtration, candidate sets and labels satisfying A2–A4; a *policy* is a rule that produces F_t-measurable selections (A1) in whatever environment it is run (A1-G plays no role in this remark; the example below is also implementable in the sense of A1-G if the labels are revealed already in G_t). The *all-loss environment* is any environment in which every candidate label equals 1 almost surely.

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

===== BEGIN FILE: theory/proofs.md =====
# Proofs (Stage 2, Task A)

> Researcher (sub-agent), 2026-11-15; **revised after review rounds 1, 2 and 3.** Statements: `theory/theorems.md`. Abstract setup (the only setup the proofs use): `theory/setup.md`. A-share operational layer (modelling assumptions, not used by any proof): `theory/instantiation_ashare.md`.
> **Review state:** three review rounds (GPT + Gemini Flash); round-3 revisions applied and NOT re-reviewed (round 1: GPT proof review + GPT independent derivation + Gemini Flash; round 2: GPT + Gemini Flash; round 3: GPT + Gemini Flash, `reviews/proof_check_3.md`). No fourth round is planned. Status labels are assigned by the lead; nothing in this file is to be read as "reviewed without open issues".
> **External facts used and their status.** Ville's inequality: proved here (§1.4), including the optional-stopping step for bounded stopping times (now proved in three lines instead of cited). Hoeffding's lemma: proved here (§1.2). Pinsker's inequality: **now proved here** for the case needed (§2.3). The proofs of Theorem 1 and Proposition 2 therefore cite no external theorem. Textbook pointers, for orientation only and **not verified by anyone** (Gemini's review quoted lemma / theorem numbers from memory; the lead's fact-check confirmed only that the books exist): Tsybakov (2009), *Introduction to Nonparametric Estimation* — Pinsker's inequality, lemma number to be verified; Williams (1991), *Probability with Martingales* — optional stopping, theorem number to be verified; Brinson, Hood & Beebower (1986) — attribution, content to be verified. None of these may be cited with a number until literature-scout has opened the source and it is in `paper/references.bib`.

## Revision log (round 1)

Source of the items: `reviews/proof_check_1.md` (C1–C5, D1–D14) and two additions sent by the lead during the revision (L1, L2). "Accepted" = changed as requested. Where I did something different from the request, or have a reservation, it is stated in the last column.

| # | Where changed (file, section) | What was done | Disagreement / reservation |
|---|---|---|---|
| C1 | theorems.md Remark 4; proofs.md §4 | Accepted. Statement weakened to (i) no policy can guarantee, in every A1–A4 environment, positive probability of trading with risk ≤ α; (ii) a policy that is safe whenever it trades must abstain a.s. in the all-loss environment. Deleted the sentence "the only policy with a universal guarantee is the one that never trades" and the argument "a policy cannot know which environment it is in". Added the reviewer's example of an informative filtration. Status `自查通过`, 陈述经修改，待复审 | none |
| C2 | theorems.md Cor. 1.3 (iii) and "What is not claimed"; setup.md §3.2; proofs.md §1.8 | Accepted. "Does not shrink with more data / identification limit" removed. Replaced by the conditional persistence statement (liminf share ≥ ρ ⇒ liminf width ≥ ρ) plus its converse, the target-level gap formula, and an explicit statement that the residual is a limitation of a deadline-based interval and that non-identification is **not** proved | none |
| C3 | setup.md §4 (new A4-D), §2; theorems.md Cor. 1.3; proofs.md §1.8 | Accepted. Common revealed set J_T, paired disclosure, P_T = N_T − \|J_T\|; stated that (K^hi − K^lo)/N_T has **all executed entries** in the denominator, not revealed entries | none |
| C4 | setup.md §3.2 (O2); theorems.md Cor. 1.3; proofs.md §1.8 | Accepted. Completion convention L^liq := 1 for never-liquidated positions | none. (Any fixed value in {0,1} works for the ordering; 1 chosen as conservative.) |
| C5 | theorems.md Theorem 1 (definition of b, b*, "Properties of the radii"); proofs.md §1.5, Deviations item 2 | Accepted. b* defined piecewise on integer arguments (0 at q = 0, min_k g_k(q) for q ≥ 1); continuity claimed only for the real extension on [1, ∞) | none |
| D1 | setup.md §3.3 ("A larger valid lag"); new `checks/check_lag_monotonicity.py`, `results_check_lag_monotonicity.txt` | Accepted. Reviewer's counterexample reproduced exactly: T = 4, entries on days 1 and 4, δ = 0.05: B_T = 4.418021 (d = 2) vs 3.652803 (d = 3); B*_T = 3.313516 vs 2.298955. Text now says: larger valid lag preserves coverage and worsens the worst-case rate bound; intervals are not nested; d must be fixed in advance | No disagreement with the conclusion. One observation recorded in the text: in the reviewer's example N_T = 2, so both clipped intervals are [0,1] — it shows non-monotonicity of the radius, not of the interval. I therefore added an example where the intervals themselves differ (entries on days ≡ 1 mod 3, N_T = 10,000: B*_T/N_T = 0.103 for d = 2, 0.075 for d = 3) and a brute-force count |
| D2 | setup.md §1 (timeline), §3.1 (alternative setup), §3.3 (rewritten: rule, OA-open / OA-next, two lag tables) | Accepted. One formal convention (post-fill information). Lag rule restated in terms of availability of label inputs in F. "d = H + 1 is safe" now carries the explicit operational assumption OA-next (and is stated as iff). The old third table row moved to a separate "alternative setup (submission-time information)" table with the difference explained | none |
| D3 | theorems.md Theorem 1 "In plain words", Cor. 1.1 (split into (a), (b)), Prop. 2 "Scope" and "In plain words"; setup.md §4 (new optional A5); proofs.md §1.8, §2.5 | Accepted, both variants given: (a) rate stated for the sampling-error term with P_T/N_T kept; (b) under A5 (individual labels revealed by t + d): P_T ≤ dM and width ≤ min{1, dM/N_T + 2√(dMℓ_T/N_T)} ≤ 3√(dMℓ_T/N_T). Sample-size regime and the trivial cap 1 stated in the Scope | The reviewer's third option (accounting bracket built from known mature aggregate counts) was **not** implemented; not needed for the two requested forms |
| D4 | theorems.md Cor. 1.2; proofs.md §1.8 | Accepted. Assumption line split (A4 for the bracket; A1–A3 for the comparison). "is biased" → "can be biased"; reviewer's two-entry example added | none |
| D5 | proofs.md §1.2 (lemma and its proof), §1.3; setup.md §4 (A1); theorems.md Theorem 1 assumptions line; proofs.md Deviations item 5 | Accepted (the more conservative GPT version, as the lead decided). Lemma now assumes E[X] < ∞; the step E[α + βD ∣ 𝒢] = α + β E[D ∣ 𝒢] is justified by localisation. All statements "the cap M is not used" removed and replaced by where M acts: boundedness ⇒ integrability of X_t (so μ_t is an ordinary conditional expectation and the centring is legitimate), and the rate in Cor. 1.1 | Not a disagreement, a note for the record: Gemini's opposite remark ("non-negativity avoids integrability issues") is correct for the step it refers to (§1.3, taking non-negative measurable factors out), and that step is unchanged; GPT's point concerns the signed centring step in §1.2. Both are now addressed. A cap-free theorem is **not** claimed |
| D6 | setup.md §4 (A4 reasonableness) | Accepted. Stop-loss / take-profit example removed for O1 with the reason; replaced by two valid examples of outcome-dependent revelation. A4 now says "revealed" means the final value of the label itself | none |
| D7 | theorems.md Lemma 3 ("How C^E is to be computed", qualification 2); proofs.md §3.2 item 2; `checks/check_attribution.py` + results | Accepted. Trade vector = h_t − h_{t−1} ∘ (1 + R_{t−1}) (pre-trade marked holdings), equivalently share change × execution price. **The check script did use the wrong formula**; corrected and re-run. Effect in the toy: total costs differ by 0.17–0.20% (the corrected cost is the slightly larger one here; portfolios are re-drawn daily, so price drift is small relative to turnover); headline numbers unchanged to the precision reported (cost term 27–41% of Π^G − Π^B). The identity residuals were never affected | none. **To be synchronised with `experiments/PLAN.md` by the lead** (I did not touch that file) |
| D8 | theorems.md Lemma 3 (W1–W4); proofs.md §3.2 item 7 | Accepted. Accounting assumptions W1–W4 stated, with the one-line wealth recursion that shows what each is needed for; otherwise Π is "additive excess P&L as defined" | none |
| D9 | proofs.md §2.3 (Pinsker proved), header; theorems.md Prop. 2 status, status table row of Theorem 1(c); new `checks/check_pinsker_binary.py` | Accepted. Re-derived and wrote out the direct proof (event A = {p > q}; Jensen for z log z on A and A^c gives KL ≥ kl(x,y); second derivative 1/(x(1−x)) ≥ 4 integrated twice gives kl(x,y) ≥ 2(x−y)²). Numerical statements downgraded to "finite numerical sanity check". Theorem 1(c): stated that the one-sided levels rest on the signed union bounds and that the two-sided simulation is no evidence for them | none. Extra, not requested: the optional-stopping step in §1.4 is now also proved directly, so Theorem 1 no longer depends on an unverified citation |
| D10 | proofs.md §1.5 "Radii" | Accepted. First S ≤ inf_k g_k; then attainment of the infimum for V ≥ 1 | none |
| D11 | proofs.md §1.1 (M1) | Accepted. (M1) stated for m ≥ 1, with the initialisation S_{j,0} = V_{j,0} = 0 (deterministic constants) and ℋ^j_0 = F_{t_{j,1}} | none |
| D12 | proofs.md §2.1; theorems.md Prop. 2 (block environment) | Accepted. For t > T: n_t = 0, X_t = 0, μ_t = 0, F_t = σ(Z_1,…,Z_B,U) | none |
| D13 | theorems.md Theorem 1 (Convention), Prop. 2 (divisibility in the statement and in item 6); setup.md §5; proofs.md §1.7 | Accepted | none |
| D14 | theorems.md Cor. 1.3 (i); proofs.md §1.8 | Accepted (the first draft's proof already used one-sided events; the statement now says so explicitly and gives the per-side level δ/2) | none |
| L1 | setup.md §3.2 (O1 mark point), §3.3 (tables, "Relation to PLAN.md v0.2"), §1 | **Decision:** primary O1 is marked at the **scheduled exit instant** (opening auction of day t+H); the close mark is kept as the secondary variant "O1-close". Reasons: the label then equals the realised exit outcome for every non-blocked exit (O1 = O2 there), and the lag does not get worse | **Differs from PLAN.md v0.2 in two places — for the lead to synchronise.** (1) PLAN has O1 (close) primary and O1′ (open) variant; here the roles are swapped. (2) Lag: PLAN uses d = H + 1. With F_t at the opening-auction match, the open mark of day t+H is in F_{t+H} **if** F is declared to contain the opening-auction outcome of all held names (OA-open), so d = H is valid; d = H + 1 remains valid under OA-next. PLAN's d = H + 1 is therefore not wrong, only not the smallest valid lag. If d = H is adopted, PLAN §3.1's description of F_t ("opening prices and suspension status of the nominated names") must be widened to all held names, which also (slightly) changes the target μ_t. I have not decided between d = H and d = H + 1; either must be fixed before data are seen (D1) |
| L2 | proofs.md §1.1 (M1), §1.3 | Accepted. Stated explicitly: V_{j,m−1} ∈ ℋ^j_{m−1} and S_{j,m−1} ∈ ℋ^j_{m−1} for every m ≥ 1 (with the m = 1 case), hence W_{m−1} ∈ ℋ^j_{m−1} and can be taken out | none |
| — | proofs.md header, §1.4, §2.3; theorems.md Prop. 2, Lemma 3 | Citations: no lemma / theorem number is presented as verified (lead's instruction; Gemini's "Verified" labels are from memory) | — |

**Still unresolved after this round** (also listed in §5): Cor. 1.3 not re-reviewed; A-share rule descriptions unverified; choice between d = H and d = H + 1 (L1) open; novelty not assessed by any reviewer; no numerical check of Theorem 1(c)'s per-side level in the Theorem 1 scripts; Cor. 1.1(b) has no dedicated check.

## Revision log (round 2)

Source of the items: `reviews/proof_check_2.md` (G1–G11 from the GPT re-review, M1–M5 from the Gemini Flash re-review; originals in `reviews/raw/`). All sixteen items are accepted; where I did something more or different, or have a reservation, it is in the last column. Files touched: `theory/setup.md`, `theory/theorems.md`, `theory/proofs.md`, `theory/checks/check_attribution.py`, `theory/checks/results_check_attribution.txt`, `theory/checks/README.md`. Nothing in `reviews/`, `experiments/`, `literature/` was changed. No proof step of Theorem 1, Corollary 1.1 or Proposition 2 was changed in substance.

| # | Where changed (file, section) | What was done | Disagreement / reservation |
|---|---|---|---|
| G1 | setup.md §3.3 (definition, correction paragraph, both lag tables, "When is d = H + 1 safe", examples), §4 A3, §1 timeline | Accepted. The "Rule d = min{…}" is replaced by a **definition of an operational lag**: a deterministic integer d ≥ 1, fixed before any data are examined, such that **for every t** every label input is F_{t+d}-measurable. Stated as **sufficient** for A3 and distinguished from A3 (counterexample: all labels deterministically 0). Table headers "Smallest valid d" → "Guaranteed valid lag under the stated availability assumption"; "if and only if OA-next" → "if OA-next"; no minimality claimed; H = 0 variant: guaranteed lag max{H, 1} | none. Added: the H row of the first table now notes that V2 / V3 inputs arrive after τ_{t+H}, so lag H is guaranteed only when no label needs them |
| G2 | setup.md §3.2 (O2, "What can and cannot be said"), §4 A3 reasonableness | Accepted. "A3 fails for O2 with any fixed d" → "the O2 convention does not guarantee A3 for any fixed lag; applying Theorem 1 directly to L^liq requires an additional bounded-label-revelation assumption", with the reviewer's distinction between liquidation time and label measurability | none |
| G3 | theorems.md Lemma 3 ("How C^E is to be computed", shortcut paragraph); proofs.md §3.2 item 2 and the numerical paragraph at the end of §3.2; `check_attribution.py` (new `adversarial_cases`), `results_check_attribution.txt`, checks/README §3; setup.md §6 item 6 | Accepted; **the round-1 formula was wrong** (it prescribed total returns in the shortcut). Now: s_{t−} = s_{t−1} ∘ φ_t = pre-trade shares after corporate actions; h_{t−} = s_{t−} ∘ p_t; trade_t = (s_t − s_{t−}) ∘ p_t; cash distributions δ_t booked to the cash ledger. Shortcut h_{t−1} ∘ (1 + r) proved valid **iff** 1 + r = φ_t p_t/p_{t−1} (ex-distribution, share-adjusted price return); exact error terms derived for the total return (spurious sale δ_t) and for the raw ratio across a split (spurious purchase). Check re-run: dividend case, required trade 0, obtained 0 (total-return shortcut: −1); split case, required 0, obtained 0 (no corporate-action update or raw ratio: +50); 12 of 12 required equalities hold; simulation output identical to round 1 | none on the item. Two limits recorded: (1) the new cases are hand-sized tests of the definitions, not of an experiment pipeline; (2) rights issues and other actions that are neither share multipliers nor cash distributions are not covered by the formula and need the pre-specified rule of setup §3.2 (V-CA). Whether a vendor's adjusted-price series is ex-distribution is **unresolved** (data audit). **To be synchronised with PLAN by the lead** |
| G4 | theorems.md Lemma 3 (new "Accounting convention" paragraph, W3); proofs.md §3.2 item 7 ("Each cost exactly once"); `check_attribution.py` case (iv); setup.md §3.2 (label), §6 item 6 | Accepted. Both conventions written out: **A, execution-price accounting** (p_t = execution price; C = explicit charges only; no slippage term) and **B, benchmark-price accounting** (p_t = common benchmark; C = explicit charges + execution shortfall Σ (s_t − s_{t−})ᵀ(p^exec − p)). **Final treatment (lead decision, 2026-11-15): convention B, benchmark-price accounting, is formally adopted**; A is kept as an alternative. Reason given by the lead: a backtest does not observe true execution prices; all strategies are recorded at the same benchmark price (opening-auction price) at each instant, slippage and explicit charges all enter through C, each once — compatible with Lemma 3 and with the slippage parameter kept in PLAN. Derivation of the post-trade wealth shows that the cost making Π a wealth change is charges + shortfall against the prices defining h and x, each once. Reviewer's example reproduced: A = B = true wealth change 8.90; mixture off by −1 | none after the lead decision. (My first version of this round adopted A with a reservation; the lead's decision removes it.) The compatibility condition **(EX)** — the execution price of an asset at an instant is the same for G, B and the reference and for both sides, because (2) uses one x_t for all strategies — is retained as the condition under which the alternative A may be used. `check_attribution.py` case (iv) tests both conventions against the true wealth change and does not depend on which is adopted; it was not changed or re-run after the decision. **To be synchronised with PLAN** |
| G5 | theorems.md Lemma 3 (W1–W4 paragraph); proofs.md §3.2 item 7 | Accepted. "exactly when ρ_t = 0" → "whenever Σ_t ρ_t W_t = 0 — in particular, when ρ_t = 0 for all t"; W1–W3 called sufficient structural accounting conditions and the sentence "each of W1–W3 is necessary" withdrawn; Σ_t ρ_t W_t renamed "cash-benchmark return on total wealth" and distinguished from the cash-account interest Σ_t ρ_t (W_t − 1ᵀh_t) | none |
| G6 | theorems.md Prop. 2 Scope (i); proofs.md §2.5 | Accepted, and the sharper condition **re-derived**: with y = dM/N, u = √y, y + 2√(yℓ) < 1 ⇔ u² + 2√ℓ u − 1 < 0 ⇔ u < √(ℓ+1) − √ℓ ⇔ y < (√(ℓ+1) − √ℓ)² = 1/(√(ℓ+1) + √ℓ)². The reviewer's formula is confirmed. Also shown: N > 9dMℓ_T implies it (needs ℓ ≥ 1/3; here ℓ_T > 1), and N ≥ (4ℓ_T + 2)dM suffices | none. Added remark that ℓ_T depends on N, so all thresholds are implicit. The threshold was also evaluated numerically in a one-off session (not a stored script) |
| G7 | proofs.md §1.5 ("Cost of stitching"), §5 item 6 | Accepted. Two effects stated separately: (α) geometric inflation sqrt(2^{k+1}/v) ∈ (1, √2] relative to sqrt(v L_k/2) **at equal L_k**; (β) confidence allocation, L_k = log(2/δ) + log(d c_0) + 2 log(k+1) against log(2/δ) for one fixed-time two-sided bound. A mixture boundary addresses (α) only | none |
| G8 | setup.md §3.2 (valuation hierarchy V1–V6, V-CA, completion rules), §4 A2 and A3 reasonableness, §6 item 5 | Accepted. Exhaustive pre-specified hierarchy: V1 auction print (also at a limit); V2 not suspended, no auction print, trades later → official open; V3 not suspended, no trade all day → pre-open reference price; V4 suspended → carry-forward last traded close; V5 no longer listed → exchange terms if any, else label := 1; V6 catch-all (required input missing at τ_{t+d}, or unlisted corporate action) → label := 1. V-CA: positions tracked in shares and cash (dividends to cash, share-type actions to the share count, rights not subscribed). No entry dropped; no revision after τ_{t+d}; counts per level reported | No disagreement. Design choices that are **mine and open to objection**: label := 1 in V5(b) / V6 (conservative; makes A2 and A3 hold by construction but turns missing data into losses); "rights not subscribed, valued at zero". Six statements are marked "exchange rule to be verified against the official text" and are **unresolved**; I did not assert them from memory. With daily bars V1 and V2 cannot be distinguished (stated). **To be synchronised with PLAN** |
| G9 | setup.md §3.1 (execution model EM, alternative PF), §3.2 (liquidation policy LP, exact O1 = O2 condition, deadline definition), §3.3 (deadline bullet), §6 items 3, 4, 9; theorems.md Cor. 1.3 (Labels); proofs.md §1.8 Step 0 | Accepted. **EM adopted for backtests**: an order is deemed filled in full at the opening-auction price iff (E1) not suspended, (E2) auction price exists, (E3) price not at the adverse limit, (E4) size within a pre-auction capacity cap; otherwise not filled at all. **PF** given as the order-and-fill alternative with partial fills (position-level labels from total net proceeds; partly sold at deadline = unsold). LP: entire remaining quantity offered at every opening auction from t+H until zero. O1 = O2 stated **only** when the scheduled liquidation executes for the whole position at the valuation price under identical cost accounting and corporate-action treatment. Deadline labels use the same LP; Step 0 of Cor. 1.3 now says the ordering depends on this | No disagreement. EM is a modelling assumption, not derived from exchange rules; with daily bars (E2) and (E4) are proxies, so "O1 ≠ O2" measures blocked exits as defined by EM. Numerical values of the capacity cap are not set here. **Unresolved:** whether EM is realistic. **To be synchronised with PLAN** |
| G10 | proofs.md §1.1 ("Why delay and the other lanes do not break this") | Accepted. The half-sentence "and in no earlier σ-field of the lane filtration" is deleted (a note says why); the argument now states only what it needs: no sampled intermediate index, centring conditional on F_{t_{j,m}} | none |
| G11 | theorems.md Remark 4 ("What is not claimed"); proofs.md §4 | Accepted. Example policy: in a fixed deterministic ordering of stock identifiers, trade the first min{M, number available} candidates with revealed label 0; F_t-measurability and n_t ≤ M verified in the proof | none |
| M1 | theorems.md Cor. 1.1 (assumption line), status table; proofs.md §1.8 Cor. 1.1(a) | Accepted. Three tiers: radius bound A1–A3; total-width bound containing P_T A1–A4; (b) A1–A5 | none |
| M2 | theorems.md Cor. 1.3 (definitions, (iii)); proofs.md §1.8 Step 6 | Accepted. ℓ_T^{(D)} := log(2 d_D c_0/δ) + 2 log(1 + log₂(M N_T)) | none |
| M3 | theorems.md Cor. 1.1(a); proofs.md §1.8 Cor. 1.1(a) | Accepted. (a) now covers the intervals of Theorem 1(a) **and** (b); one line of proof added (unclipped width (P_T + 2B*_T)/N_T ≤ (P_T + 2B_T)/N_T) | none |
| M4 | setup.md §2, §4 A4-D; theorems.md Cor. 1.3 ((i), (ii), (iii)); proofs.md §1.8 Steps 3–6 | Accepted. P_T^D := N_T − \|J_T\| throughout Corollary 1.3 and A4-D | none. `check_cor13.py` and its README section still print "P"; they were not edited or re-run (notation only) |
| M5 | theorems.md Theorem 1 (first paragraph of the statement), Cor. 1.3 (assumptions); setup.md §2, §3.3 definition, §4 A3 | Accepted. Theorem 1 now reads: "Fix δ ∈ (0,1) and a deterministic integer d ≥ 1 for which A3 holds; δ and d are fixed before any data are examined", with the reason (radii not monotone in d) and the statement that a data-selected lag is not covered. Consistent with the lead's decision d = H + 1, recorded in setup §3.3 and §6 item 7 | none. Added one sentence (not requested): selection among a pre-specified finite set of valid lags could be covered by a union bound at level δ / (number of lags); not pursued |
| — | theorems.md status table and every status line | Review note set to "round-2 review: GPT + Gemini (Flash); revisions applied, confirmation re-review pending". Labels unchanged: `自查通过` except Corollary 1.3 `草稿`. No "GPT 审过 / Gemini 审过" label assigned | — |
| — | setup.md new §6 "Conventions the experiments must adopt" | Ten-item checklist for the lead to synchronise into `experiments/PLAN.md` (information time, fill-based entries, EM, partial fills, O1 hierarchy, trade and cost accounting, lag, pending labels, O2 / deadline labels, attribution conventions) | PLAN.md not read and not edited |

**Still unresolved after round 2** (also in §5): exchange-rule statements unverified (six explicitly marked); EM is an unvalidated modelling assumption; whether vendor adjusted prices are ex-distribution; frequency of V5(b) / V6 conventional losses; Corollary 1.3 still `草稿`; novelty not assessed; no check of Theorem 1(c)'s per-side level in the Theorem 1 scripts; Corollary 1.1(b) has no dedicated check; `check_thm1_coverage.py`, `check_matured_rate.py`, `check_cor13.py`, `check_lag_monotonicity.py`, `check_pinsker_binary.py` were not re-run in round 2 (nothing they test was changed).

## Revision log (round 3)

Source of the items: `reviews/proof_check_3.md` (K1–K2 raised by both reviewers; X1–X12 raised by GPT only and accepted by the lead; §4: structural split). Originals: `reviews/raw/proof_setup_gpt_20261115-114019.md`, `reviews/raw/proof_REVIEW_REQUEST_round3_gemini_20261115-114045.md`. Files touched: `theory/setup.md` (rewritten, abstract only), `theory/instantiation_ashare.md` (new), `theory/theorems.md`, `theory/proofs.md`, `theory/checks/check_attribution.py`, `theory/checks/check_cor13.py`, their two result files, `theory/checks/README.md`; `theory/REVIEW_REQUEST_round3.md` deleted. Nothing in `reviews/`, `experiments/`, `literature/` was changed. **No proof step of Theorem 1, Corollary 1.1, Corollary 1.2, Proposition 2 or of identity (2) was changed.** None of the changes below has been re-reviewed.

**Section map (the logs of rounds 1 and 2 above quote the section numbers of the old `setup.md`; they were not rewritten).** "inst" = `instantiation_ashare.md`.

| Old `setup.md` | Now |
|---|---|
| §1 timeline | setup §1 (two information times, abstract); inst §1 (A-share reading) |
| §2 notation | setup §2 |
| §3.1 executed fill, EM, PF, submission-time alternative | setup §3 (A1, A1-G); inst §2 (EM, synthetic fills), inst §6.3 (partial fills); the submission-time alternative is no longer specified (inst §7) |
| §3.2 O1, hierarchy V1–V6, V-CA | inst §3 (decision tree: V-CA → Step 1 classes S-a–S-c; V5(a) → S-d / S-e; V5(b) → outcome U; V4 → P1; V1 → P2; V2 → P3; V3 → P4; V6 → outcomes M and U) |
| §3.2 O1-close | removed (inst §7) |
| §3.2 O2, LP, deadline labels | inst §6 |
| §3.3 lag | setup §4 (abstract: two lags, larger lag, non-monotone radius); inst §4 (operational lag H + 1, lag-H variant). The lag tables for closing-auction entry and for the submission-time setup were dropped |
| §4 assumptions | setup §3 |
| §5 target | setup §5 |
| §6 conventions for the experiments | inst §8 |

| # | Where changed | What was done | Disagreement / reservation / unresolved |
|---|---|---|---|
| Split (§4) | setup.md, instantiation_ashare.md, all cross-references | Accepted. `setup.md` (about 13 KB) contains only: G_t and F_t, notation, A1, A1-G, A2 (fixed and frozen label), A3, A4, A5, A4-D, the two lags, the target. No market rule, execution model or valuation rule. Each assumption is followed by "needs in an application" and a pointer; the phrases "true by construction" (A1) and "bookkeeping" (A4) are gone, as GPT's closing remark asked. `instantiation_ashare.md` opens with a status box: modelling assumptions and conventions, pending data audit and rule verification, not part of any statement. Statements in `theorems.md` cite abstract assumptions only; the instantiation is mentioned as a "reading" | The split removes the operational claims from the statements; it does **not** make them true. Whether A1–A5 hold for an A-share stream is exactly as unverified as before |
| K1 | theorems.md Lemma 3 (paragraph after W4); proofs.md §3.2 item 7; `check_attribution.py` case (v); README §3 | Accepted. With costs debited at the trade (start of period), W_{t+1} = (W_t − c_t)(1 + ρ_t) + h_tᵀx_t and W_{T+1} − W_1 = Π + Σ_t ρ_t (W_t − c_t). The timing convention is now stated; the end-of-period formula Π + Σ_t ρ_t W_t is given as the alternative; mixed timing: no formula given. Re-derived and checked numerically with an explicit cash-and-shares ledger: reviewer's example gives terminal wealth 108.9 and wealth change 8.9 = Π + ρ(W − c) = −1 + 9.9, while the round-2 formula gives 9; a multi-period case (8 periods, 3 assets, fees, shortfall, varying ρ, seed 2026) has residual 0 (tolerance 1e-9) for the corrected formula and −0.022425 = −Σ ρ_t c_t for the round-2 one; 21 of 21 required equalities hold | none. The error was mine: round 2 had the right recursion in the "each cost once" paragraph and the wrong one in the display and in `theorems.md` |
| K2 | theorems.md Lemma 3 (two places); proofs.md §3.2 item 2; `check_attribution.py` (comments and printed labels); README §3 | Accepted. Share multiplier 2 with the price going 100 → 50 is a **2-for-1** split; "1-for-2" now appears only as the name of a consolidation (multiplier 1/2). Arithmetic unchanged | none |
| X1 | inst §2.3, §2.4, §8 items 2–4, §9 | Accepted. Listed what a daily bar cannot tell at the auction match (whether the auction matched; whether the stock traded at all; auction volume; intraday suspension; the rest of the bar; point-in-time state). Two cases: (a) timestamped auction data → executable definition with F_t = information at the match; (b) daily bars → **synthetic fill rule SF**: orders from G_t only; the fill rule may read only the traded flag, suspension flag and open of the day-t bar; declared filtration F_t^syn, explicitly artificial. Under (b) Theorem 1 is a statement about the synthetic fill stream with target defined through F_t^syn, **not** about an executable strategy | **Partly unresolved.** With daily bars alone I see no fill rule whose indicator is measurable with respect to real auction-time information; "only auction-time information" is therefore achieved for the order rule and for the choice of fields, not for the fill indicator itself. How far SF fills differ from real fills cannot be estimated without auction data. Needs a decision by the user (obtain auction data, or accept the downgrade in the paper) and synchronisation with PLAN |
| X2 | setup §1, §3 (A1-G); theorems.md Theorem 1 assumptions line, Prop. 2, Remark 4; inst §2.1 | Accepted. G_t ⊆ F_t; submitted names, quantities, order types and limit prices are G_t-measurable; A_{ti} ≤ O_{ti}; executed entries are F_t-measurable; the conditional target stays with F_t | A1-G is used in **no proof**; it is stated as the condition for reading the results as statements about an implementable strategy. I did not add it to the assumption lists of the theorems for that reason |
| X3 | setup §3 A2(b), §4; theorems.md Theorem 1 (paragraph on other lags); inst §3 (snapshot), §4 | Accepted. Labels are frozen at a label-finalisation lag d_label that is part of the label convention; data-availability rules are evaluated at day t + d_label; the monitoring lag d is separate. "A larger lag only changes the radius" is now said only for the same frozen labels | A2(b) is written as a property of the convention (it does not depend on d, is never revised), not as "L_{ti} is F_{t+d_label}-measurable", because the target label of Corollary 1.3 has no bounded resolution; measurability by a lag remains the content of A3 / A5. Adopted values d_label = d = H + 1 |
| X4 | inst §3 | Accepted. Decision tree: Step 1 events and listing status (classes S-a–S-e, outcome U; at most one succession, which guarantees termination) → Step 2 price rule (four mutually exclusive cases P1–P4 for a listed security) → Step 3 validation at the frozen snapshot, with outcome M overriding the tentative value; global override for any step that cannot be evaluated. A delisted security is resolved in Step 1 and cannot reach "no trade" or "suspended" | My choices, open to objection: L := 1 for U and M; rights not subscribed and valued at zero; one succession only. **Unresolved:** the tree detects a missing field, not an event missing from the vendor's calendar; I no longer claim A2 "by construction" |
| X5 | inst §4; setup (no numerical lag anywhere); theorems.md | Accepted. The adopted label supports the operational lag H + 1 only (P3, P4 need the close of day t+H). Lag H is possible only for a separately defined label using auction-time information ("O1-auction": reference price immediately when there is no auction match), listed as a variant, not adopted and not specified further. The unconditional lag-H remarks of the old timeline, of "why the exit-time mark" and of the examples are gone with the old sections | none |
| X6 | inst §5, §6.1, §6.2, §8 item 9 | Accepted. One entitlement rule for O1, O2, deadline labels and P&L: a distribution belongs to the position iff it holds the shares at the close of the record date, regardless of payment date; fixed withholding rate; unpaid entitlements are receivables | Reservation: the holding-period-dependent dividend tax is not modelled (flat rate, external input); record-date / ex-date relation is "rule to be verified" |
| X7 | theorems.md Corollary 1.3 (labels, new CERT, new part (o), (ii), "not claimed"); proofs.md §1.8 Steps 0, 5, "why still 草稿"; inst §6.4; `check_cor13.py` Part D | Accepted, option "lower label 0 / upper label 1" taken, in a slightly more general form: a certification indicator V and a certified value L^cert with **CERT: L^cert = L^liq on {V = 1}**; L^lo = V·L^cert, L^hi = 1 − V(1 − L^cert). Ordering re-proved in two cases (V = 1: equality by CERT; V = 0: 0 ≤ L^liq ≤ 1). Steps 1–4, 6, 7 are unchanged because they use only the ordering, A2–A3 for the bracket labels and A4-D; Step 5 now counts uncertified entries. Part D: ordering holds in 16 of 16 enumerated states for the certified labels and fails in 4 of 16 for a "missing ⇒ loss" fallback (including the reviewer's case). Status stays `草稿` | **Disagreement with Gemini (Flash)**, which called the round-2 version correct and "ready to be promoted": not followed, for the reason GPT gave. Reservations: CERT is a new explicit assumption (a record accepted as complete may still be wrong); A3 for the bracket labels remains assumed; Parts A–C simulate complete records only; the rewrite is unreviewed |
| X8 | inst §6.1, §6.3, §9 | Partly done. Defined: under EM / SF same-day lots of one security form one all-or-nothing order (no allocation needed); with partial fills, FIFO allocation of sales to lots and pro-rata allocation of charges; lot-level labels; corporate events during an extended liquidation handled by the Step-1 classification over the whole holding period | **Unresolved, listed as external inputs required before applying the results with partial fills:** order type and limit-price instruction, submission time, treatment of the unfilled sell remainder, lot-size rules, broker allocation records |
| X9 | inst §7 | O1-close **deleted** rather than given its own closing-price rule (the task allowed either) | If PLAN still reports a close-mark label it needs its own rule; for the lead |
| X10 | setup §3 A4-D remarks; proofs.md §1.8 Step 5 | Accepted. A4-D restricts the interval calculation (label information enters through the common set J_T); the ledger may record components separately | none |
| X11 | theorems.md Lemma 3 (definitions, new "Scope" paragraph); proofs.md §3.2 item 2 | Accepted. p_t and φ_t strictly positive; the share formulas and the return shortcut cover only componentwise multipliers and cash distributions; other actions need an explicit holdings transformation. Identity (2) unaffected | none |
| X12 | proofs.md §1.5, §5 item 6 | Accepted. The comparison is called an algebraic comparison with a deterministic-clock benchmark; stated that substituting the realised adaptive clock V_{j,m} into sqrt(v L/2) is not a valid fixed-time radius; "a mixture boundary would address (α) only" withdrawn, no quantitative claim about mixtures | none |
| — | theorems.md status table and status lines; checks/README.md | Labels unchanged (`自查通过`; Corollary 1.3 `草稿`); note "three review rounds (GPT + Gemini Flash); round-3 revisions applied and NOT re-reviewed" | — |

**Still unresolved after round 3** (also in §5): everything listed in `instantiation_ashare.md` §9 (thirteen exchange-rule items unverified; external inputs; EM / SF unvalidated; point-in-time data and OA-next unaudited; CERT unaudited); with daily bars the results concern synthetic fills only (X1); partial-fill policy incomplete (X8); Corollary 1.3 `草稿` and its rewrite unreviewed; novelty not assessed in any round; no check of Theorem 1(c)'s per-side level in the Theorem 1 scripts; Corollary 1.1(b) has no dedicated check; `check_thm1_coverage.py`, `check_matured_rate.py`, `check_lag_monotonicity.py`, `check_pinsker_binary.py` not re-run in round 3 (nothing they test was changed).

## Deviations from design notes

1. **Constant in b(q): confirmed, no change.** b(q) = sqrt(2^{k(q)} L_{k(q)}) with 2^{k}, not 2^{k+1}, is correct **provided** the fixed λ of epoch k is tuned to the upper end 2^{k+1} of the epoch: λ_k = sqrt(8 L_k / 2^{k+1}) (§1.5). Tuning λ to the lower end 2^k would give the worse constant (3/(2√2)) sqrt(2^k L_k) ≈ 1.06 sqrt(2^k L_k).
2. **Added Theorem 1(b): sharper radius b*(q) ≤ b(q) on the same event.** Ville's inequality for the epoch-k parameter λ_k holds at **all** times, not only while Q is in epoch k, so the minimum over k of the linear boundaries is valid at no extra cost in δ. Motivation found in the numerical check: b(q) jumps by a factor ≈ √2 each time a lane's Q crosses a power of two (the radius B_T/N_T jumped by up to 42% in one day in the simulations, d = 1); the real-variable extension of b* is continuous **on [1, ∞)** and showed no upward jump there. (It is not continuous at 0 if one extends it by the same formula: min_k g_k(0) = (1/2)√L_0 > 0 = b*(0). Round-1 item C5.) In the simulations B*/B was between 0.73 and 0.95.
3. **Added Theorem 1(c)**: one-sided statements at level δ/2 each (read off the δ allocation; used in Corollary 1.3).
4. **Added Corollary 1.3** (status `草稿`): conservative interval for the executable-liquidation target through deadline labels. It follows from Theorem 1 by monotonicity. It is not a way around the unbounded delay of the liquidation outcome, and (round 1) it is not claimed to be an identification limit.
5. **Assumption usage made precise.** A4 is needed only for computability; validity uses the pathwise bracket K_T ≤ ΣX_t ≤ K_T + P_T, true for any revelation pattern. The cap M does not enter the radii; it gives boundedness (hence integrability) of X_t, used in §1.1 (M4) and §1.2, and it enters the rate of Corollary 1.1. (Round-1 item D5; the first draft said "M is used only in Corollary 1.1".)
6. **A1 resolved as fill-based selection with F_t the post-fill information** (setup §1, §3). The design notes offered two options; the other (submission-based) has a different estimand and a different lag and is no longer specified after the round-3 split (`instantiation_ashare.md` §7). Round 3 added A1-G (orders measurable with respect to the pre-submission information G_t), which no proof uses.
7. **Corollary 1.1 is stated with explicit constants** instead of O(·), and with log(1 + log₂(M N_T)) instead of log log(e + M N_T).
8. **Proposition 2 is stated with explicit constants**, for δ < 1/2, as a probability statement on the width plus an expected-width consequence; the procedure is allowed to see all labels including those maturing after T (stronger than needed). The variance formula of the design notes (M d N / 4 at p = 1/2) is confirmed.
9. **Lemma 3: added the non-uniqueness statement** (interaction term; item 5 of the lemma). Not in the design notes; it matters for how results are reported.
10. **Remark 4** is stated with explicit quantifiers; after round 1 only the weaker, correct form is kept.

No statement of the design notes was found to be false. Round 1 found errors in **my additions and explanations** (see the revision log), not in the design-notes statements.

---

## 1. Theorem 1

### 1.1 Lanes and lane filtrations

Fix j ∈ {0,…,d−1}. Let t_{j,1} < t_{j,2} < … be the days t ≥ 1 with t ≡ j (mod d); thus t_{j,m+1} = t_{j,m} + d. Define, for m ≥ 1,

  D_{j,m} = μ_{t_{j,m}} − X_{t_{j,m}},  ν_{j,m} = n_{t_{j,m}},  S_{j,m} = Σ_{i=1}^m D_{j,i},  V_{j,m} = Σ_{i=1}^m ν_{j,i}²,

with the **deterministic initialisation S_{j,0} = V_{j,0} = 0**, and the **lane filtration**

  ℋ^j_m = F_{t_{j,m+1}},  m ≥ 0.

So ℋ^j_0 = F_{t_{j,1}} is the information at the first decision point of the lane, and ℋ^j_m is the information at the decision point of the lane's (m+1)-st day. (ℋ^j_m)_{m≥0} is increasing because (F_t) is (A1) and t_{j,m+1} increases with m. No σ-field with index −1 is used anywhere.

Measurability facts.

- (M1) **For every m ≥ 1, ν_{j,m} and V_{j,m} are ℋ^j_{m−1}-measurable** (predictable). Reason: n_{t_{j,m}} is F_{t_{j,m}}-measurable by A1, and F_{t_{j,m}} = ℋ^j_{m−1}; earlier ν's are measurable w.r.t. smaller σ-fields. **Consequently, for every m ≥ 1, V_{j,m−1} is ℋ^j_{m−1}-measurable:** for m = 1, V_{j,0} = 0 is a constant; for m ≥ 2, V_{j,m−1} ∈ ℋ^j_{m−2} ⊂ ℋ^j_{m−1} by the first sentence applied to m − 1.
- (M2) **For m ≥ 1, μ_{t_{j,m}} is ℋ^j_{m−1}-measurable.** Reason: it is a conditional expectation given F_{t_{j,m}} = ℋ^j_{m−1} (A2).
- (M3) **For m ≥ 1, D_{j,m} and S_{j,m} are ℋ^j_m-measurable** (adapted); S_{j,0} = 0 is trivially ℋ^j_0-measurable. Reason: X_{t_{j,m}} is F_{t_{j,m}+d}-measurable by A3, and t_{j,m} + d = t_{j,m+1}, so X_{t_{j,m}} ∈ ℋ^j_m; μ_{t_{j,m}} ∈ ℋ^j_{m−1} ⊂ ℋ^j_m by (M2). **Consequently, for every m ≥ 1, S_{j,m−1} is ℋ^j_{m−1}-measurable.**

And the centring fact:

- (M4) **For m ≥ 1, E[D_{j,m} ∣ ℋ^j_{m−1}] = 0.** Reason: ℋ^j_{m−1} = F_{t_{j,m}} and μ_t = E[X_t ∣ F_t] by definition. Here the cap of A1 is used: 0 ≤ X_t ≤ n_t ≤ M, so X_t is bounded, hence integrable, μ_t is an ordinary (finite) conditional expectation, D_{j,m} is bounded by M in absolute value, and E[μ_t − X_t ∣ F_t] = μ_t − μ_t = 0.

**Why delay and the other lanes do not break this.** Between τ_{t_{j,m}} and τ_{t_{j,m+1}} the trader makes the decisions of days t_{j,m}+1, …, t_{j,m}+d−1 (which belong to other lanes), sees outcomes of other lanes' earlier days, and sees partial information about X_{t_{j,m}}. All of that is contained in ℋ^j_m = F_{t_{j,m}+d}. (Round-2 item G10: the earlier text added "and in no earlier σ-field of the lane filtration". That is not implied — A1–A3 do not forbid some of this information from being known or predictable already at F_{t_{j,m}} — and it is not needed.) What the argument needs is only this: the lane filtration has no intermediate step between ℋ^j_{m−1} = F_{t_{j,m}} and ℋ^j_m = F_{t_{j,m}+d}; therefore the only conditional expectation of D_{j,m} that the proof ever takes is the one given F_{t_{j,m}}, which is zero by definition of μ, **whatever** F_{t_{j,m}} contains (including other lanes' decisions and revealed outcomes up to that point, and partial information about not-yet-revealed outcomes of the d−1 preceding days). What would be wrong is to use the calendar filtration: Σ_{t≤T}(μ_t − X_t) is not F_T-measurable, and with respect to (F_{T+d})_T its increments are not centred, because F_{T+d−1} may already contain partial information about X_T, so E[μ_T − X_T ∣ F_{T+d−1}] ≠ 0 in general. The lane construction is exactly what removes this.

The d lane filtrations are **different** sub-sequences of (F_t); the lane processes are not supermartingales with respect to one common filtration. This is why the lanes are combined by a union bound (§1.5) and not by multiplying or averaging the processes.

### 1.2 Conditional Hoeffding lemma

**Claim.** Let 𝒢 be a σ-field, ν ≥ 0 and X random variables with ν 𝒢-measurable and finite, 0 ≤ X ≤ ν, and **E[X] < ∞**. Let μ = E[X ∣ 𝒢], D = μ − X. Then for every real λ, E[e^{λD} ∣ 𝒢] ≤ exp(λ² ν² / 8) a.s.

(The integrability condition was added in round 1, item D5. In the application X = X_t ≤ M, so it holds automatically. With E[X] < ∞, μ is an a.s. finite ordinary conditional expectation, D is integrable, and E[D ∣ 𝒢] = 0. The left side is the conditional expectation of a non-negative variable, which always exists in [0, ∞].)

*Proof.* 0 ≤ μ ≤ ν a.s. (monotonicity of conditional expectation; ν is 𝒢-measurable). Put a = μ − ν and c = μ; both are 𝒢-measurable and finite, a ≤ D ≤ c, c − a = ν.

On {ν = 0}: X = 0, μ = 0, D = 0, and the claim reads 1 ≤ 1.

On {ν > 0}: y ↦ e^{λy} is convex, so for y ∈ [a,c], e^{λy} ≤ ((c−y)/(c−a)) e^{λa} + ((y−a)/(c−a)) e^{λc}. Substituting y = D:

  e^{λD} ≤ α + β D,  α := (c e^{λa} − a e^{λc})/ν,  β := (e^{λc} − e^{λa})/ν,

with α, β finite and 𝒢-measurable. *Conditional expectation of the right side.* For r = 1, 2, … let G_r = {ν > 0, |α| + |β| ≤ r} ∈ 𝒢. On G_r the coefficients are bounded and D is integrable, so by linearity and "taking out what is known" for bounded 𝒢-measurable factors, 1_{G_r} E[α + βD ∣ 𝒢] = 1_{G_r}(α + β E[D ∣ 𝒢]) = 1_{G_r} α. Since 1_{G_r} E[e^{λD} ∣ 𝒢] = E[1_{G_r} e^{λD} ∣ 𝒢] ≤ E[1_{G_r}(α + βD) ∣ 𝒢] and G_r ↑ {ν > 0}, we get on {ν > 0}

  E[e^{λD} ∣ 𝒢] ≤ α = (c/ν) e^{λa} + (−a/ν) e^{λc} = θ e^{λ(μ−ν)} + (1−θ) e^{λμ},  θ := μ/ν ∈ [0,1].

With s := −λν and μ = θν: the right side equals e^{λμ}(1 − θ + θ e^{s}) = exp(ψ(s)), ψ(s) := −θ s + log(1 − θ + θ e^{s}) (indeed λμ = −θ s).
ψ(0) = 0. ψ′(s) = −θ + θe^s/(1−θ+θe^s), so ψ′(0) = 0. ψ″(s) = ρ(1−ρ) with ρ = θe^s/(1−θ+θe^s) ∈ [0,1], so ψ″ ≤ 1/4. By Taylor's theorem with Lagrange remainder, ψ(s) = ψ(0) + ψ′(0)s + ψ″(ξ)s²/2 ≤ s²/8 = λ²ν²/8. ∎

(Finite numerical sanity check of ψ(s) ≤ s²/8 on a grid: `checks/check_thm1_coverage.py`, last-but-one block; maximum of ψ − s²/8 on the grid was 0.0. The proof is the Taylor argument, not the grid.)

### 1.3 The exponential process is a non-negative supermartingale

For real λ and lane j define W^{j,λ}_0 = 1 and, for m ≥ 1,

  W^{j,λ}_m = exp( λ S_{j,m} − λ² V_{j,m} / 8 ).

**Claim.** (W^{j,λ}_m)_{m≥0} is a non-negative supermartingale with respect to (ℋ^j_m)_{m≥0}, with W_0 = 1.

*Proof.* Non-negativity is clear. **Adaptedness, i.e. W_m ∈ ℋ^j_m for every m ≥ 0:** W_0 = 1 is a constant; for m ≥ 1, S_{j,m} ∈ ℋ^j_m by (M3) and V_{j,m} ∈ ℋ^j_{m−1} ⊂ ℋ^j_m by (M1). In particular, for every m ≥ 1, **W_{m−1} = exp(λ S_{j,m−1} − λ² V_{j,m−1}/8) is ℋ^j_{m−1}-measurable**, because S_{j,m−1} ∈ ℋ^j_{m−1} (consequence stated in (M3)) and V_{j,m−1} ∈ ℋ^j_{m−1} (consequence stated in (M1); for m = 1 both are the constant 0). For m ≥ 1,

  W_m = W_{m−1} · exp(−λ² ν_{j,m}²/8) · exp(λ D_{j,m}).

W_{m−1} is ℋ^j_{m−1}-measurable (just shown) and ν_{j,m} is ℋ^j_{m−1}-measurable (M1); the factor W_{m−1} exp(−λ² ν_{j,m}²/8) is non-negative and ℋ^j_{m−1}-measurable and exp(λ D_{j,m}) is non-negative, so the factor can be taken out of the conditional expectation (for non-negative variables this holds without integrability conditions, by monotone convergence from the bounded case):

  E[W_m ∣ ℋ^j_{m−1}] = W_{m−1} exp(−λ² ν_{j,m}²/8) E[exp(λ D_{j,m}) ∣ ℋ^j_{m−1}] ≤ W_{m−1},

by §1.2 applied with 𝒢 = ℋ^j_{m−1} = F_{t_{j,m}}, ν = n_{t_{j,m}}, X = X_{t_{j,m}} (0 ≤ X_t ≤ n_t because labels are in {0,1}, A2; n_t ∈ F_t by A1; E[X_t] ≤ M < ∞ by A1; μ_t = E[X_t ∣ F_t]). Integrability: by induction and the tower property, E[W_m] ≤ E[W_{m−1}] ≤ … ≤ 1. ∎

Nothing in this step uses A3 except through (M3) (adaptedness). A3 is what makes W_m observable in ℋ^j_m, i.e. what makes W a process adapted to a filtration in which the conditioning σ-field of step m is exactly F_{t_{j,m}}.

### 1.4 Ville's inequality

**Claim.** If (W_m)_{m≥0} is a non-negative supermartingale with respect to (ℋ_m) with E[W_0] ≤ 1 and c > 0, then ℙ(∃ m ≥ 0: W_m ≥ c) ≤ 1/c.

*Proof.* Let σ = inf{m ≥ 0: W_m ≥ c} (a stopping time; inf ∅ = ∞). Fix n. *Optional stopping at the bounded time σ ∧ n (proved directly):* W_{σ∧n} = W_0 + Σ_{i=1}^n 1{σ ≥ i}(W_i − W_{i−1}). The event {σ ≥ i} = {σ ≤ i−1}^c belongs to ℋ_{i−1}, and W_i, W_{i−1} are integrable, so E[1{σ ≥ i}(W_i − W_{i−1})] = E[1{σ ≥ i}(E[W_i ∣ ℋ_{i−1}] − W_{i−1})] ≤ 0 by the supermartingale property. Summing, E[W_{σ∧n}] ≤ E[W_0] ≤ 1. On {σ ≤ n}, W_{σ∧n} = W_σ ≥ c, and W ≥ 0, hence c ℙ(σ ≤ n) ≤ E[W_{σ∧n}] ≤ 1. Let n → ∞: ℙ(σ < ∞) ≤ 1/c by continuity from below. ∎

### 1.5 Dyadic epochs: constants

Let α_k = δ / (2 d c_0 (k+1)²), k ≥ 0. Then L_k = log(1/α_k) > 0, because 2 d c_0 ≥ 2c_0 > 3 > δ. Let

  λ_k = sqrt( 8 L_k / 2^{k+1} ) = 2 sqrt( L_k / 2^k ) > 0.

For sign s ∈ {+1, −1}, lane j and k ≥ 0 define the bad event

  A^{s}_{j,k} = { ∃ m ≥ 0: W^{j, sλ_k}_m ≥ 1/α_k }.

By §1.3 and §1.4, ℙ(A^s_{j,k}) ≤ α_k. On the complement of A^s_{j,k}, for **all** m ≥ 0: sλ_k S_{j,m} − λ_k² V_{j,m}/8 < L_k, i.e.

  s S_{j,m} < L_k/λ_k + λ_k V_{j,m}/8 = g_k(V_{j,m}).   (3)

Compute g_k: L_k/λ_k = (1/2) sqrt(2^k L_k) and λ_k/8 = (1/4) sqrt(L_k/2^k) = (1/2) sqrt(2^k L_k) / 2^{k+1}. Hence

  g_k(v) = (1/2) sqrt(2^k L_k) ( 1 + v / 2^{k+1} ),   (4)

which is the function g_k of the theorem statement.

*The 2^k versus 2^{k+1} question.* For v in epoch k, i.e. 2^k ≤ v < 2^{k+1}: g_k(v) < (1/2) sqrt(2^k L_k)(1 + 1) = sqrt(2^k L_k). So the radius on epoch k is sqrt(2^k L_k) — **2^k, as proposed** — and this is the exact minimum over λ of the worst case over the epoch: min_λ sup_{v<2^{k+1}} [L_k/λ + λ v/8] = min_λ [L_k/λ + λ 2^{k+1}/8] = 2 sqrt(L_k 2^{k+1}/8) = sqrt(2^k L_k), attained at λ_k (AM–GM). *Cost of stitching (round 2, item G7; reworded in round 3, item X12): an algebraic comparison with a deterministic-clock benchmark.* What follows compares formulas. It is **not** a claim that a fixed-time interval with the smaller radius is available in the model studied here. (α) **Geometric inflation, at equal logarithm.** For a **deterministic** number v > 0 and a logarithmic quantity L, the same computation gives min_λ [L/λ + λ v/8] = sqrt(v L/2), attained at a λ that depends on v. If the clock at a fixed time were a known constant v (for instance if the entry counts were deterministic), a bound with a fixed λ tuned to v would have this radius; call it the deterministic-clock benchmark. On epoch k, 2^k ≤ v < 2^{k+1}, so sqrt(2^k L_k) / sqrt(v L_k/2) = sqrt(2^{k+1}/v) ∈ (1, √2]: **holding the logarithmic quantity fixed at L = L_k**, the dyadic radius b exceeds the benchmark by a factor between 1 and √2. In the model the clock V_{j,m} is in general **random and adaptive** (it is built from the entry counts, which may depend on the past). The exponential bound of §1.3–§1.4 holds for a λ fixed in advance; choosing λ after V_{j,m} has been observed is not covered by it, also at a fixed calendar time. Therefore sqrt(V_{j,m} log(2/δ)/2), with the realised clock substituted for v, is **not** in general a valid fixed-time radius, and the benchmark is a yardstick for the algebra only. (β) **Confidence allocation.** At a fixed nominal error probability the logarithm is not the same: the benchmark for one sum at two-sided level δ uses log(2/δ), whereas L_k = log(2 d c_0/δ) + 2 log(k+1) = log(2/δ) + log(d c_0) + 2 log(k+1) contains the allocation over the d lanes (log d) and over the epochs (log c_0 + 2 log(k+1), which grows like 2 log log₂ v). For one lane, the ratio of b to the deterministic-clock benchmark at the same δ is therefore the product of (α) and sqrt(L_k / log(2/δ)), not "between 1 and √2" as the first draft said. (Adding the d lane radii is a further, separate effect; its size is what Corollary 1.1 bounds.) *Mixture boundaries.* Replacing dyadic stitching by a mixture boundary would give a different boundary, with different constants and different logarithmic terms. It would not in general remove the need for some penalty for time-uniform validity, but it need not reproduce the particular L_k used here; we make no quantitative claim about it. (The round-2 sentence "a mixture boundary would address (α) only" is withdrawn.) (If instead λ were tuned to the lower end, λ = sqrt(8L_k/2^k), the bound on the epoch would be sqrt(2^k L_k/8)(1 + v/2^k) < 3 sqrt(2^k L_k/8) ≈ 1.06 sqrt(2^k L_k).) Finite numerical sanity check of the minimisation: last block of `checks/check_thm1_coverage.py` (relative discrepancy 1.7e-16).

*Union bound.* Let E_δ^up = ∩_{j,k} (A^{+}_{j,k})^c, E_δ^low = ∩_{j,k} (A^{−}_{j,k})^c, E_δ = E_δ^up ∩ E_δ^low. Then

  ℙ((E_δ^up)^c) ≤ Σ_{j=0}^{d−1} Σ_{k≥0} α_k = d · (δ/(2 d c_0)) · Σ_{k≥0} (k+1)^{−2} = (δ/(2c_0)) · (π²/6) = δ/2,

likewise ℙ((E_δ^low)^c) ≤ δ/2, and ℙ(E_δ^c) ≤ δ. This proves the probability statements of (c) and ℙ(E_δ) ≥ 1 − δ. (The per-side level δ/2 of (c) is established by these two separate signed union bounds; it is not something a two-sided coverage simulation can confirm.)

*Radii (reworded in round 1, items C5 and D10).* On E_δ^up, (3) with s = +1 holds for every k ≥ 0 and every m ≥ 0. A family of strict inequalities S_{j,m} < g_k(V_{j,m}), k ≥ 0, gives in general only the non-strict

  S_{j,m} ≤ inf_{k≥0} g_k(V_{j,m}).

On E_δ^low the same holds for −S_{j,m}. Now distinguish the two cases of the piecewise definition of b*:

- **V_{j,m} = 0.** Then ν_{j,i} = 0 for all i ≤ m, hence X = μ = 0 on those days and S_{j,m} = 0 = b*(0) = b(0), by the separate definition b*(0) = b(0) = 0. (Here inf_k g_k(0) = (1/2)√L_0 > 0 is *not* b*(0); the bound S ≤ inf_k g_k(0) is true but not the one used.)
- **V_{j,m} = q ≥ 1** (V is a sum of squares of integers, so V ≥ 1 whenever V > 0, and k(q) = ⌊log₂ q⌋ ≥ 0 is well defined). The infimum is attained: g_k(q) ≥ (1/2)sqrt(2^k L_k) → ∞ as k → ∞, so only finitely many k can have g_k(q) ≤ g_0(q), and inf_k g_k(q) = min_k g_k(q) = g_{k*}(q) = b*(q) for some finite k*. Hence S_{j,m} ≤ b*(q) (and in fact S_{j,m} < g_{k*}(q) = b*(q), by (3) for k = k*). Moreover b*(q) ≤ g_{k(q)}(q) < sqrt(2^{k(q)} L_{k(q)}) = b(q), since q < 2^{k(q)+1}.

Therefore on E_δ: |S_{j,m}| ≤ b*(V_{j,m}) ≤ b(V_{j,m}) for all j and all m ≥ 0; on E_δ^up alone, S_{j,m} ≤ b*(V_{j,m}); on E_δ^low alone, −S_{j,m} ≤ b*(V_{j,m}).

### 1.6 From lane index to calendar time; proof of (1)

For T ≥ 1 let m_j(T) = #{t ≤ T: t ≡ j (mod d)}. Then Σ_{t≤T, t≡j}(μ_t − X_t) = S_{j,m_j(T)} and Q_{j,T} = V_{j,m_j(T)}. Since §1.5 holds for all m ≥ 0 simultaneously, it holds for m = m_j(T) for every T; this is (1). Note that (1) is a statement about the random variables μ_t, X_t themselves; it does not matter that X_t for t close to T is not yet known at time T.

### 1.7 Proof of (a), (b), (c)

Sum (1) over j = 0,…,d−1 (each day t ≤ T belongs to exactly one lane): on E_δ,

  | Σ_{t≤T} μ_t − Σ_{t≤T} X_t | ≤ B*_T ≤ B_T.   (5)

Pathwise bracket: Σ_{t≤T} X_t is the number of entries through T with label 1. Each such entry is either revealed (counted in K_T) or unrevealed (one of the P_T unrevealed entries); and every entry counted in K_T has label 1. Hence, for every outcome ω and **every** revelation pattern,

  K_T ≤ Σ_{t≤T} X_t ≤ K_T + P_T.   (6)

More generally, (6) holds with K_T := Σ_{(t,i)∈J} L_{ti} and P_T := N_T − |J| for **any** set J of entries through T (the labels outside J contribute between 0 and N_T − |J|); this form is used in Corollary 1.3.

(5) and (6) give K_T − B*_T ≤ Σ_{t≤T} μ_t ≤ K_T + P_T + B*_T. Also 0 ≤ μ_t ≤ n_t, so 0 ≤ Σμ_t ≤ N_T. Divide by N_T > 0 (for N_T = 0 nothing is claimed; the interval is [0,1] by convention): this is (b); (a) follows from B*_T ≤ B_T. For (c): the upper bound uses only S_{j,m} ≤ b*(V_{j,m}) (event E_δ^up) and the lower bound only −S_{j,m} ≤ b*(V_{j,m}) (event E_δ^low). (6) used no assumption on the revelation mechanism, which proves the last sentence of the theorem. ∎

### 1.8 Corollaries

**Corollary 1.1 (a).** Let T with N_T ≥ 1, and Q_j = Q_{j,T}. If Q_j ≥ 1: 2^{k(Q_j)} ≤ Q_j gives b(Q_j) ≤ sqrt(Q_j L_{k(Q_j)}); and k(Q_j) ≤ log₂ Q_j ≤ log₂(Σ_{t≤T} n_t²) ≤ log₂(M N_T) (because n_t² ≤ M n_t by n_t ≤ M), so L_{k(Q_j)} ≤ log(2 d c_0 (1 + log₂(M N_T))²/δ) = ℓ_T (L_k is increasing in k). If Q_j = 0, b = 0. Hence B_T ≤ sqrt(ℓ_T) Σ_j sqrt(Q_j) ≤ sqrt(ℓ_T) sqrt(d Σ_j Q_j) (Cauchy–Schwarz on d terms) = sqrt(d ℓ_T Σ_{t≤T} n_t²) ≤ sqrt(d M N_T ℓ_T). B*_T ≤ B_T was shown in §1.5. Width: before clipping, upper minus lower endpoint in Theorem 1(a) is (P_T + 2B_T)/N_T; clipping to [0,1] cannot increase it and caps it at 1. Hence width ≤ min{1, P_T/N_T + 2 sqrt(dM ℓ_T/N_T)}. The same bound holds for the interval of Theorem 1(b), whose unclipped width is (P_T + 2B*_T)/N_T ≤ (P_T + 2B_T)/N_T (round-2 item M3). *Assumptions used (round-2 item M1):* the chain B*_T ≤ B_T ≤ sqrt(d M N_T ℓ_T) is deterministic and uses A1 (n_t ≤ M, integer n_t) only through the definition of the clocks; it is stated under A1–A3 because B_T is the radius of Theorem 1. The width statement involves P_T and the endpoints built from K_T and P_T, which are defined through the ledger of A4; it therefore needs A1–A4. Nothing in A1–A4 bounds P_T: A3 says that the aggregate X_t is F_{t+d}-measurable, not that the monitor's ledger has each individual label by t + d. ∎

**Corollary 1.1 (b).** Under A5 every label of a day t ≤ T − d is revealed at monitoring time T. The unrevealed entries therefore belong to days T − d < t ≤ T, at most d days with at most M entries each (A1): P_T ≤ dM. With (a), width ≤ min{1, dM/N_T + 2 sqrt(dM ℓ_T/N_T)}; the same bound holds for the interval of Theorem 1(b) because B*_T ≤ B_T. For the last inequality put y = dM/N_T and note ℓ_T ≥ log(2 d c_0/δ) ≥ log(2c_0) > 1 (2c_0 = π²/3 ≈ 3.29 > e, δ < 1, d ≥ 1). If y ≤ 1: y ≤ √y ≤ sqrt(y ℓ_T), so y + 2 sqrt(y ℓ_T) ≤ 3 sqrt(y ℓ_T). If y > 1: 3 sqrt(y ℓ_T) > 3 > 1 ≥ width. ∎

**Corollary 1.2.** The bracket is (6) divided by N_T: deterministic, uses only the accounting of A4. The comparison |r_T^entry − R_T| ≤ B*_T/N_T is (5) divided by N_T; (5) holds on E_δ and was derived from A1–A3 (Theorem 1). The two-entry example in the statement is checked by inspection: labels (0,1), only the second revealed ⇒ K_T = 1, P_T = 1, N_T = 2, R_T = 1/2, K_T/(N_T − P_T) = 1. ∎

**Corollary 1.3** (rewritten in round 1; bracket labels redefined through certification in round 3, item X7; status `草稿`).

*Step 0: the three labels are well defined and ordered on all of Ω (rewritten in round 3, item X7).* By assumption L^liq_{ti} ∈ {0,1} is defined for every executed entry (A2(a)), and V_{ti} ∈ {0,1}, L^cert_{ti} ∈ {0,1} are defined for every executed entry by a convention fixed in advance. Then L^lo_{ti} = V_{ti} L^cert_{ti} ∈ {0,1} and U^D_{ti} = 1 − V_{ti} ∈ {0,1}. L^hi_{ti} = L^lo_{ti} + U^D_{ti}: if V_{ti} = 1 it equals L^cert_{ti} + 0 ∈ {0,1}; if V_{ti} = 0 it equals 0 + 1 = 1. So L^hi_{ti} ∈ {0,1}, and in both cases L^hi_{ti} = 1 − V_{ti}(1 − L^cert_{ti}), the form given in the statement. *Pointwise ordering, two cases.* If V_{ti} = 1: L^lo_{ti} = L^cert_{ti} = L^hi_{ti}, and L^cert_{ti} = L^liq_{ti} by CERT; hence L^lo_{ti} = L^liq_{ti} = L^hi_{ti}. If V_{ti} = 0: L^lo_{ti} = 0 ≤ L^liq_{ti} ≤ 1 = L^hi_{ti}, whatever value L^liq_{ti} ∈ {0,1} takes (in the reading: a position not sold by its deadline, partly sold, never liquidated, or sold with a missing or incomplete record). Hence L^lo ≤ L^liq ≤ L^hi on Ω, which is part (o). CERT is used in the first case and nowhere else.

*Why the round-2 definition was not enough.* Round 2 defined L^lo = S·1{sale at a net loss} with S = "sold by the deadline", and obtained equality on {S = 1} from "the same policy, the same execution model, the same cost accounting". That argument is about the true liquidation. It does not say what the monitor records when the sale record is missing or incomplete at the finalisation day, and A3 for the deadline labels needs their values to be determined by then. If such an entry were given the fallback of the O1 label ("missing ⇒ loss") in both deadline labels, an entry sold at a profit would have L^lo = 1 > 0 = L^liq (GPT, round 3), and so would an unsold entry whose eventual liquidation is not a loss; the ordering, and with it Steps 1 and 4, would fail. With the certified labels a missing record means V = 0, i.e. the second case above. `checks/check_cor13.py` Part D enumerates the 16 combinations of (sold by the deadline, record complete, sale at a loss, value of L^liq if unsold): 0 ordering violations for the certified labels, 4 for the fallback, and L^hi − L^lo = 1 − V in all 16. *What CERT carries.* In the reading of `instantiation_ashare.md` §6.4, CERT says that a record accepted as complete is complete and final and is evaluated with the same liquidation policy, execution model, cost accounting and distribution rule as L^liq (the requirement of round-2 item G9 is now part of CERT). If a record is accepted but wrong, L^cert ≠ L^liq with V = 1 is possible, the ordering can fail, and the corollary claims nothing.

*Step 1: ordering of the targets.* Multiply by A_{ti} ≥ 0 and sum over i ∈ C_t: X^lo_t ≤ X^liq_t ≤ X^hi_t, all in [0, n_t] ⊂ [0, M], hence integrable. Conditional expectation given F_t is monotone: μ^lo_t ≤ μ^liq_t ≤ μ^hi_t. Summing over t ≤ T:

  Σ_{t≤T} μ^lo_t ≤ Σ_{t≤T} μ^liq_t ≤ Σ_{t≤T} μ^hi_t.   (7)

*Step 2: two one-sided events.* L^lo and L^hi are fixed-convention {0,1} labels (A2) whose day counts X^lo_t, X^hi_t are F_{t+d_D}-measurable (A3 with lag d_D, assumed). The selections, n_t, the lanes, the clocks Q_{j,T} and therefore B*_T are the same for both labels, because they depend only on (n_t) and d_D. Apply §1.1–§1.6 to the label L^lo: there is an event E^{low}(lo) with ℙ ≥ 1 − δ/2 on which, for all T, Σ_{t≤T} μ^lo_t ≥ Σ_{t≤T} X^lo_t − B*_T (sum over lanes of −S_{j,m} ≤ b*(V_{j,m}), with S built from L^lo). Apply them to the label L^hi: there is an event E^{up}(hi) with ℙ ≥ 1 − δ/2 on which, for all T, Σ_{t≤T} μ^hi_t ≤ Σ_{t≤T} X^hi_t + B*_T. By the union bound ℙ(E^{low}(lo) ∩ E^{up}(hi)) ≥ 1 − δ. No two-sided event is used for either label.

*Step 3: accounting (A4-D).* By the general form of (6) with J = J_T, applied to each label: K^lo_T ≤ Σ_{t≤T} X^lo_t and Σ_{t≤T} X^hi_t ≤ K^hi_T + (N_T − |J_T|) = K^hi_T + P_T^D. (Round-2 item M4: P_T^D := N_T − |J_T| replaces the symbol P_T used here in round 1; it is not the P_T of Theorem 1.)

*Step 4: (i).* On E^{low}(lo) ∩ E^{up}(hi), by Steps 2, 3 and (7), for all T:

  K^lo_T − B*_T ≤ Σ_{t≤T} μ^lo_t ≤ Σ_{t≤T} μ^liq_t ≤ Σ_{t≤T} μ^hi_t ≤ K^hi_T + P_T^D + B*_T.

Also 0 ≤ Σ_{t≤T} μ^liq_t ≤ N_T. Divide by N_T > 0: Λ_T ≤ r_T^{liq} ≤ Υ_T. The lower bound used only E^{low}(lo), the upper bound only E^{up}(hi); each has probability ≥ 1 − δ/2.

*Step 5: (ii).* Lower bound on the width: B*_T ≥ 0 and K^lo_T ≥ 0 give Λ_T = max{0, (K^lo_T − B*_T)/N_T} ≤ K^lo_T/N_T. K^hi_T ≤ |J_T| ≤ N_T and P_T^D, B*_T ≥ 0 give Υ_T = min{1, (K^hi_T + P_T^D + B*_T)/N_T} ≥ K^hi_T/N_T. Hence Υ_T − Λ_T ≥ (K^hi_T − K^lo_T)/N_T. Upper bound: Υ_T ≤ (K^hi_T + P_T^D + B*_T)/N_T and Λ_T ≥ (K^lo_T − B*_T)/N_T. Identification of the count: by A4-D both sums run over the same set J_T, so K^hi_T − K^lo_T = Σ_{(t,i)∈J_T} (L^hi_{ti} − L^lo_{ti}) = Σ_{(t,i)∈J_T} U^D_{ti} = #{(t,i) ∈ J_T : V_{ti} = 0}, the number of uncertified entries in J_T. (Without a common set this fails: using only L^hi = 1 of a certified entry that was sold at a loss would add 1 to K^hi − K^lo although the entry is certified — the round-1 reviewer's example. Round-3 item X10: this is a requirement on which entries the calculation uses; the ledger itself may record the two components at different times.) The denominator is N_T, all executed entries.

*Step 6: (iii).* Take liminf in the lower bound of (ii): liminf (Υ_T − Λ_T) ≥ liminf (K^hi_T − K^lo_T)/N_T ≥ ρ. Converse: by Corollary 1.1(a) applied with the lag d_D in place of d, B*_T/N_T ≤ sqrt(d_D M ℓ_T^{(D)}/N_T), where ℓ_T^{(D)} = log(2 d_D c_0/δ) + 2 log(1 + log₂(M N_T)) is ℓ_T with d_D for d (round-2 item M2: the statement previously wrote ℓ_T); with the upper bound of (ii), if (K^hi_T − K^lo_T)/N_T, P_T^D/N_T and d_D M ℓ_T^{(D)}/N_T tend to 0, so does the width.

*Step 7: target-level gap.* r_T^{hi} − r_T^{lo} = Σ_{t≤T}(μ^hi_t − μ^lo_t)/N_T = Σ_{t≤T} E[X^hi_t − X^lo_t ∣ F_t]/N_T = Σ_{t≤T} E[Σ_i A_{ti} U^D_{ti} ∣ F_t]/N_T (linearity). This is a sum of conditional expectations, not the observed count of Step 5. ∎

*Why still `草稿`.* (1) In round 3 the reviewers disagreed (Gemini Flash: correct; GPT: ordering fails under a missing-data fallback, item X7). The labels were redefined and Step 0 rewritten afterwards; **no reviewer has seen this version**. (2) CERT is an assumption about records, not something proved; and A3 for the bracket labels is assumed — in the reading it requires the certification status and the certified value of every entry of day t to be determined by day t + d_D (`instantiation_ashare.md` §6.4), which is unaudited. (3) The liquidation policy behind the reading is only partly specified when fills can be partial (`instantiation_ashare.md` §6.3). (4) No non-identification result is proved.

*Numerical sanity check* (`checks/check_cor13.py`, `results_check_cor13.txt`; re-run in round 3: the output of Parts A–C is identical, line for line, to the round-1 output; **Parts A–C simulate complete records, V = S, and therefore do not exercise missing records** — that case is covered only by the enumeration of Part D quoted in Step 0; δ = 0.1, M = 10, H = 1, D = 5, d_D = 6, T = 1500, 400 paths × 3 seeds × 4 cells; positions stuck at the deadline with outcome-dependent probability, pairs revealed at outcome-dependent times, adaptive n_t). The interval missed r^liq at some T on 0 of 4800 paths (upper side 0, lower side 0; allowed 10% per cell, 5% per side). With the radius multiplied by 0 (accounting bracket only) it missed on 2.3–2.5% (heavy, shared), 28.5–30.3% (heavy, identical), 45.5–49.8% (moderate, shared) and 89.0–92.3% (moderate, identical) of paths; with the radius multiplied by 0.25, on 0–1.25%. So the check can detect a radius that is far too small but is **not sensitive** to moderate errors in the constant: the bound is very conservative here. The "naive" interval that treats stuck positions as non-losses missed on 100% of paths when 30–60% of positions get stuck, and on 0% when 2–25% do (there the radius, ±0.17, hides the bias of about 0.09). Pathwise: no ordering violation; min over paths and T of width − (K^hi − K^lo)/N_T was +0.24 to +0.34 (≥ 0 as claimed). Part B (one entry per day, only the first misses its deadline): (K^hi − K^lo)/N_T = 1/T and the width falls from 0.56 (T = 100) to 0.0058 (T = 10⁶). Part C (every 5th entry misses): the share tends to 0.2 and the width falls from 0.73 to 0.2058, staying above 0.2.

---

## 2. Proposition 2

### 2.1 The block environment satisfies A1–A5, and μ_t = M p

Sample space: Ω = {0,1}^B × [0,1] with coordinates (Z_1,…,Z_B, U); under ℙ_p the Z_b are i.i.d. Bernoulli(p) and U is Uniform[0,1], independent of them. Days t = 1,…,T = Bd; b(t) = ⌈t/d⌉. **For t > T** (needed so that A1–A3 make sense for all t ≥ 1 and F_{t+d} is defined): F_t = σ(Z_1,…,Z_B,U), C_t = ∅, n_t = 0, **X_t = 0 and μ_t = 0**; these days contribute nothing to any sum.

- F_t = σ(Z_1,…,Z_{b(t)−1}, U) for t ≤ T is increasing in t because b(t) is non-decreasing, and F_T ⊂ F_{T+1} = σ(Z_1,…,Z_B,U).
- **A1:** for t ≤ T, C_t is a fixed set of M names and A_{ti} = 1 for all of them (deterministic), so n_t = M ≤ M; for t > T, n_t = 0. ✓.
- **A2:** L_{ti} = Z_{b(t)} ∈ {0,1}; X_t = M Z_{b(t)} for t ≤ T. ✓.
- **A3 with lag d:** for t ≤ T − d, b(t+d) = b(t) + 1, so F_{t+d} ⊇ σ(Z_1,…,Z_{b(t)}) ∋ X_t; for T − d < t ≤ T, t + d > T and F_{t+d} = σ(Z_1,…,Z_B,U) ∋ X_t; for t > T, X_t = 0. ✓ (For the first day of a block the lag d is attained: t+d is the first day of the next block, and no F_s with s < t+d contains Z_{b(t)}.)
- **A4, A5:** take the revelation pattern "label of (t,i) is revealed at the first decision point after block b(t)", i.e. at day b(t)d + 1 ≤ t + d; then every label of day t is revealed at all monitoring times ≥ t + d (A5), and K_T, P_T are determined by the revealed Z's (A4). At T = Bd the last block is unrevealed: P_T = Md. ✓.
- **μ_t:** for t ≤ T, F_t is generated by Z_1,…,Z_{b(t)−1} and U, all independent of Z_{b(t)}; hence μ_t = M E[Z_{b(t)} ∣ F_t] = M p for **every** day of the block, in particular for days 2,…,d of the block: at those days the information set still does not contain Z_{b(t)}, because the block's label is revealed only after the block's last decision point. (This is the point the design notes asked to verify. It depends on the filtration: with a richer filtration that revealed Z_b during the block, μ_t would be M Z_b on later days and the target would change — see "what it does not show", item 4.)
- Hence r_T^entry = Σ_{t≤T} Mp / (M B d) = p, a constant.
- Variance: Σ_{t≤T}(X_t − μ_t) = M d Σ_b (Z_b − p), variance M² d² B p(1−p) = p(1−p) M d N. With independent labels the variance of the same sum would be p(1−p) N. ✓ (finite numerical sanity check: `checks/results_check_thm1_coverage.txt`, "Effective sample size".)

### 2.2 Reduction to a two-point testing problem

Let p_− = 1/2 − h, p_+ = 1/2 + h with h = c/√B, c = (√3/8)(1−2δ). Since δ ∈ (0,1/2), 0 < c < √3/8, so 0 < 2h ≤ 2c < 0.44 < 1/2 for every B ≥ 1 and p_± ∈ (0,1). Write ℙ_± = ℙ_{p_±}.

Let (ℓ,u) be measurable functions of (Z_1,…,Z_B,U), honest over {ℙ_−, ℙ_+}: ℙ_−(G_−) ≥ 1−δ and ℙ_+(G_+) ≥ 1−δ, where G_± = {ℓ ≤ p_± ≤ u} (recall r_T^entry = p_± under ℙ_±).

By definition of total variation distance TV = sup_A |ℙ_+(A) − ℙ_−(A)|: ℙ_+(G_−) ≥ ℙ_−(G_−) − TV ≥ 1 − δ − TV. Therefore

  ℙ_+(G_− ∩ G_+) ≥ 1 − ℙ_+(G_−^c) − ℙ_+(G_+^c) ≥ 1 − (δ + TV) − δ = 1 − 2δ − TV.

On G_− ∩ G_+: ℓ ≤ p_− and u ≥ p_+, so u − ℓ ≥ p_+ − p_− = 2h. Hence ℙ_+(u − ℓ ≥ 2h) ≥ 1 − 2δ − TV, and by symmetry the same under ℙ_−.

### 2.3 Bounding the total variation distance

**KL divergence of the two experiments.** Let ν be the product of counting measure on {0,1}^B and Lebesgue measure on [0,1]. ℙ_∓ have densities f_∓(z,u) = Π_b p_∓^{z_b}(1−p_∓)^{1−z_b} with respect to ν (the U-factor is 1 for both). Both densities are strictly positive on Ω and their ratio is bounded, so KL(ℙ_− ‖ ℙ_+) = ∫ f_− log(f_−/f_+) dν is finite and, because log(f_−/f_+) is a sum over b of terms depending on z_b only and the Z_b are independent under ℙ_−,

  KL(ℙ_− ‖ ℙ_+) = B · kl(p_−, p_+),  kl(x,y) := x log(x/y) + (1−x) log((1−x)/(1−y)).

With p_− = 1/2 − h, p_+ = 1/2 + h:
kl(p_−,p_+) = (1/2 − h) log((1/2−h)/(1/2+h)) + (1/2 + h) log((1/2+h)/(1/2−h)) = 2h log((1+2h)/(1−2h)).
For x = 2h ∈ (0, 1/2]: log((1+x)/(1−x)) = 2 Σ_{i≥0} x^{2i+1}/(2i+1) ≤ 2x Σ_{i≥0} x^{2i} = 2x/(1−x²) ≤ 2x/(3/4) = 8x/3. Hence kl(p_−,p_+) ≤ 2h · (8/3)(2h) = 32h²/3 and KL ≤ 32 B h²/3 = 32c²/3.

**Pinsker's inequality, proved for the case needed (added in round 1, item D9).** *Claim:* for two probability measures P, Q with densities f, g with respect to a common measure ν, g > 0 everywhere, f/g bounded: TV(P,Q) ≤ sqrt(KL(P‖Q)/2). (Applied with P = ℙ_−, Q = ℙ_+.)

*Step 1 (TV is attained on A = {f > g}).* Put x = P(A), y = Q(A). For any event E, P(E) − Q(E) = ∫_E (f − g) dν ≤ ∫_{E∩A} (f − g) dν ≤ ∫_A (f − g) dν = x − y (the integrand is ≤ 0 off A and ≥ 0 on A). Also Q(E) − P(E) = ∫_E (g − f) dν ≤ ∫_{A^c} (g − f) dν = (1 − y) − (1 − x) = x − y. With E = A the value x − y is attained. Hence TV(P,Q) = x − y ≥ 0.

*Step 2 (trivial case).* If Q(A) = 0 then, since g > 0, ν(A) = 0, so f ≤ g ν-a.e.; as both integrate to 1, f = g ν-a.e., TV = 0 and the claim holds. Assume from now on y = Q(A) > 0. Then x − y = ∫_A (f − g) dν > 0, so 0 < y < x ≤ 1; in particular y < 1, i.e. Q(A^c) > 0.

*Step 3 (KL(P‖Q) ≥ kl(x,y)).* Let φ(z) = z log z for z > 0, φ(0) = 0; φ is convex on [0,∞). KL(P‖Q) = ∫ g φ(f/g) dν = ∫_A g φ(f/g) dν + ∫_{A^c} g φ(f/g) dν (φ(f/g) is bounded because f/g is). On A, g dν / y is a probability measure; by Jensen's inequality for the convex φ,

  (1/y) ∫_A g φ(f/g) dν ≥ φ( (1/y) ∫_A g (f/g) dν ) = φ(x/y),  so ∫_A g φ(f/g) dν ≥ y φ(x/y) = x log(x/y).

In the same way on A^c, with the probability measure g dν/(1−y): ∫_{A^c} g φ(f/g) dν ≥ (1−y) φ((1−x)/(1−y)) = (1−x) log((1−x)/(1−y)) (read as 0 if x = 1, consistent with φ(0) = 0). Adding: KL(P‖Q) ≥ kl(x,y), with the convention 0 log 0 = 0.

*Step 4 (kl(x,y) ≥ 2(x−y)² for 0 < y < x ≤ 1).* Fix y ∈ (0,1) and let F(s) = kl(s,y) for s ∈ (0,1). F(y) = 0. F′(s) = log(s/y) − log((1−s)/(1−y)), so F′(y) = 0. F″(s) = 1/s + 1/(1−s) = 1/(s(1−s)) ≥ 4, because s(1−s) ≤ 1/4. Integrating once from y: F′(s) = ∫_y^s F″ ≥ 4(s − y) for s ∈ [y,1). Integrating again: F(x) = ∫_y^x F′(s) ds ≥ 2(x − y)² for x ∈ [y,1). For x = 1: kl(1,y) = log(1/y) = lim_{x↑1} kl(x,y) ≥ lim 2(x−y)² = 2(1−y)².

*Step 5.* KL(P‖Q) ≥ kl(x,y) ≥ 2(x−y)² = 2 TV(P,Q)². ∎

Therefore TV(ℙ_−, ℙ_+) ≤ sqrt(KL/2) ≤ sqrt(16 c²/3) = 4c/√3 = (1 − 2δ)/2.

(*Finite numerical sanity checks only* — they do not replace the argument above. (i) Exact TV between Binomial(B, p_−) and Binomial(B, p_+) — the sum of the Z's is sufficient — for δ ∈ {0.05, 0.1, 0.25, 0.4} and 7 values of B between 1 and 1000 (28 combinations) was always below sqrt(KL/2), which was always below 4c/√3; `checks/results_check_thm1_coverage.txt`. (ii) `checks/check_pinsker_binary.py`: kl(x,y) − 2(x−y)² ≥ 0 at all points of a 2001 × 2001 grid; on 3 × 20,000 random pairs of distributions on finite sets, KL − kl(x,y) ≥ −1.8e-15 (rounding), |TV − (x−y)| ≤ 3.9e-16, KL − 2TV² > 0.)

### 2.4 Conclusion

ℙ_±(u − ℓ ≥ 2h) ≥ 1 − 2δ − (1−2δ)/2 = (1−2δ)/2, with 2h = (√3/4)(1−2δ)/√B and 1/√B = sqrt(M d/N) (N = M B d). Since u − ℓ ≥ 0, E_±[u − ℓ] ≥ 2h · (1−2δ)/2 = (√3/8)(1−2δ)² sqrt(M d/N). ∎

### 2.5 Scope remarks

- "Honest over all A1–A4 environments with parameters (d,M)" implies honest over {ℙ_−,ℙ_+}, so the bound applies to every such procedure, including Theorem 1's interval evaluated at the fixed time T, and a fortiori to time-uniform procedures.
- The procedure was allowed to depend on **all** of (Z_1,…,Z_B) and on external randomisation; in the block environment there is nothing else to observe. The bound therefore does not come from pending labels.
- Upper vs lower in the block environment (reworded in round 1, item D3). The block environment satisfies A5 with P_T = Md at T = Bd, so by Corollary 1.1(b) Theorem 1's width is ≤ min{1, Md/N + 2 sqrt(d M ℓ_T/N)} ≤ 3 sqrt(dM ℓ_T/N); Proposition 2 gives ≥ (√3/4)(1−2δ) sqrt(M d/N) with probability ≥ (1−2δ)/2. The matching is in the **sampling-error term** and only up to sqrt(ℓ_T) and constants. *When the upper bounds are below 1 (reworded in round 2, item G6).* Write y = dM/N > 0 and ℓ = ℓ_T > 1. (a) The simplified bound: 3 sqrt(yℓ) < 1 ⇔ y < 1/(9ℓ) ⇔ N > 9 dM ℓ_T. (b) The sharper bound: with u = √y > 0, y + 2 sqrt(yℓ) < 1 ⇔ u² + 2√ℓ u − 1 < 0 ⇔ u < −√ℓ + sqrt(ℓ + 1) (the quadratic has roots −√ℓ ± sqrt(ℓ+1), and only the larger one is positive) ⇔ y < (sqrt(ℓ+1) − √ℓ)². Since (sqrt(ℓ+1) − √ℓ)(sqrt(ℓ+1) + √ℓ) = 1, this threshold equals 1/(sqrt(ℓ+1) + √ℓ)². (c) Comparison: (sqrt(ℓ+1) + √ℓ)² ≤ 9ℓ ⇔ sqrt(ℓ+1) ≤ 2√ℓ ⇔ ℓ ≥ 1/3, true; so 1/(9ℓ) ≤ (sqrt(ℓ+1) − √ℓ)², i.e. condition (a) implies condition (b) and is strictly stronger (for ℓ > 1/3): N > 9 dM ℓ_T is **sufficient, not necessary**. (d) A simple sufficient condition for (b): (sqrt(ℓ+1) + √ℓ)² = 2ℓ + 1 + 2 sqrt(ℓ(ℓ+1)) < 4ℓ + 2 (because 4ℓ(ℓ+1) < (2ℓ+1)²), so N ≥ (4ℓ_T + 2) dM suffices. (e) The computed interval uses B*_T ≤ B_T ≤ sqrt(dM N ℓ_T) and the actual P_T, and can have width below 1 when neither (a) nor (b) holds. ℓ_T depends on N, so (a), (b), (d) are implicit conditions. Numerically, at ℓ = 10: threshold (a) 1/90 ≈ 0.0111, threshold (b) (√11 − √10)² ≈ 0.0238, sufficient condition (d) 1/42 ≈ 0.0238 (one-off Python evaluation: 0.011111, 0.023823, 0.023810; in the same session the equivalence in (b) and the implications (c), (d) were confirmed on 200,000 random pairs (ℓ, y) with ℓ ∈ [0.34, 50]; not stored as a script — the derivation above is the proof). In general (without A5) the upper bound on the total width keeps P_T/N_T. Ratio observed in the check at δ = 0.1, N = 20000: 14–18 for B_T, 12.5–14 for B*_T. The gap consists of sqrt(ℓ_T) ≈ 3–3.5 and constants; **none of it is shown to be necessary**.
- Items 1–6 of "What it does not show" in `theorems.md` stand as stated; they are limitations of the argument, not gaps to be filled later by this proof.

---

## 3. Lemma 3

### 3.1 Proof of (2)

For each t, using only h_t^G = e_t^G w_t^G and h_t^B = e_t^B w_t^B:

  h_t^G − h_t^B = e_t^G w_t^G − e_t^B w_t^B = (e_t^G w_t^B − e_t^B w_t^B) + (e_t^G w_t^G − e_t^G w_t^B) = (e_t^G − e_t^B) w_t^B + e_t^G (w_t^G − w_t^B)

(add and subtract e_t^G w_t^B = h_t^E). Take the inner product with x_t, sum over t, and subtract C^G − C^B:

  Π^G − Π^B = Σ_t (h_t^G − h_t^B)ᵀ x_t − (C^G − C^B) = Σ_t (e_t^G − e_t^B)(w_t^B)ᵀ x_t + Σ_t e_t^G (w_t^G − w_t^B)ᵀ x_t − (C^G − C^B). ∎

Gross / net: h_t^G − h_t^E = e_t^G(w_t^G − w_t^B), so Σ_t (h_t^G − h_t^E)ᵀx_t is the composition term; subtracting costs, Π^G − Π^E = composition − (C^G − C^E). h_t^E − h_t^B = (e_t^G − e_t^B) w_t^B, so Π^E − Π^B = exposure-schedule term − (C^E − C^B). Adding the two net lines recovers (2) because (C^G − C^E) + (C^E − C^B) = C^G − C^B. These lines hold for **any** real number C^E. ∎

The same computation holds period by period if costs are assigned to periods, so the **path** of cumulative P&L differences decomposes additively as well.

### 3.2 Justification of the qualifications

1. *Zero baseline exposure.* If e_t^B = 0 then h_t^B = 0 = e_t^B w for every vector w, so w_t^B is not determined by the holdings, and the proof above goes through for any w_t^B. The day's contributions are e_t^G (w_t^B)ᵀx_t (exposure) and e_t^G (w_t^G − w_t^B)ᵀ x_t (composition): each depends on w_t^B, their sum e_t^G (w_t^G)ᵀ x_t does not. If e_t^G = 0 both terms' dependence on w_t^G vanishes (it enters only multiplied by e_t^G). Numerically: `check_attribution.py`, "same paths" block — on identical paths the two conventions gave exposure +0.393202 / composition +0.000834 versus +0.395609 / −0.001573, with identical sums +0.394036.
2. *Gross vs net; how the reference cost is computed (round-1 item D7; **corrected again in round 2, item G3**).* Shown in §3.1 for any scalar C^E. When C^E comes from a cost model, the model must be applied to the reference's **trades**, and trades are defined in share units. Notation: p_t > 0 the raw prices per share at the start of period t; s_t the share counts carried through period t; h_t = s_t ∘ p_t; φ_t > 0 the share multipliers of the corporate actions taking effect between the trade of period t−1 and the trade of period t; κ_t ≥ 0 the cash distribution per pre-action share in the same interval; s_0 = 0. *Restrictions (round-3 item X11):* p_t and φ_t are **strictly positive** componentwise — the relations below divide by p_{t−1} and by φ_t, and a dollar holding in an asset with zero price cannot be written as s ∘ p — and the model covers **only** componentwise share multipliers and cash distributions. These restrictions concern the modelled cost terms, not identity (2).

   **Definition.** s_{t−} := s_{t−1} ∘ φ_t (pre-trade shares **after** corporate actions), h_{t−} := s_{t−} ∘ p_t, trade_t := (s_t − s_{t−}) ∘ p_t = h_t − h_{t−}; the cash distribution δ_t := s_{t−1} ∘ κ_t is credited to cash and is not part of trade_t. This is "shares actually bought or sold × price": a corporate action changes the number of shares without any order being executed, so the share change caused by it must be removed before the difference is taken; a cash distribution moves value from the risky position to cash without an order.

   **The round-1 formula and its error.** Round 1 wrote h_{t−} = h_{t−1} ∘ (1 + R_{t−1}) with R "total price returns … adjusted for corporate actions", justified by "p_t = p_{t−1} ∘ (1 + R_{t−1})". That last equation is a statement about a *price ratio*; it is false for a dividend-inclusive total return and false across a split for raw prices. Exact relations (componentwise, wherever h_{t−1} ≠ 0):

     h_{t−} = s_{t−1} ∘ φ_t ∘ p_t = h_{t−1} ∘ (φ_t ∘ p_t / p_{t−1}),

   so h_{t−} = h_{t−1} ∘ (1 + r_{t−1}) **iff** 1 + r_{t−1} = φ_t ∘ p_t / p_{t−1} (the ex-distribution, share-adjusted price return). For the total return 1 + R^tot_{t−1} = (φ_t ∘ p_t + κ_t)/p_{t−1}:

     h_{t−1} ∘ (1 + R^tot_{t−1}) = s_{t−1} ∘ (φ_t ∘ p_t + κ_t) = h_{t−} + δ_t,

   so the shortcut with total returns gives trade_t − δ_t: a spurious sale equal to the distribution. For the raw ratio 1 + r^raw_{t−1} = p_t/p_{t−1}: h_{t−1} ∘ (1 + r^raw_{t−1}) = s_{t−1} ∘ p_t = h_{t−} / φ_t, so the shortcut gives trade_t + s_{t−1} ∘ (φ_t − 1) ∘ p_t: a spurious purchase of the shares created by the action. The reviewer's two examples: one share, 100 → 99 after a dividend of 1, no trade: definition 0, total-return shortcut 99 − 100(1 + 0) = −1; one share, 2-for-1 split (share multiplier 2; rounds 1–2 wrote "1-for-2", which is the name of a consolidation with multiplier 1/2 — round-3 item K2), 100 → 50, no trade: definition (2 − 2)·50 = 0, raw-ratio shortcut 100 − 100·0.5 = +50. Both are reproduced by `checks/check_attribution.py` ("adversarial accounting cases" (i), (ii); output in `results_check_attribution.txt`), together with two controls showing that a genuine trade on the corporate-action date is still reported (99 and −50).

   **Consistency with the P&L.** The P&L of period t−1 is the change in value of the position plus the cash received: s_{t−} ∘ p_t + δ_t − s_{t−1} ∘ p_{t−1} = h_{t−1} ∘ R^tot_{t−1}. So total returns are the right returns for Σ_t h_tᵀx_t (W2) and the wrong ones for trades; the two uses must not share one return series unless there are no cash distributions.

   **The first draft's formula h_t^E − h_{t−1}^E** remains wrong for the round-1 reason: it books the price drift of the old position as trading (one share held while the price goes 100 → 110: true trade 0, naive formula 10). These trades were never made, so C^E is a modelled quantity, and with non-linear costs (impact) it need not lie between C^G and C^B. Identity (2) is unaffected by the choice of trade formula: it holds for arbitrary real C^G, C^B, C^E (§3.1). Which prices p_t are, and where a difference between execution and marking prices is booked, is fixed by the accounting convention (item 7 below); rights issues, exchanges into another security and other actions that are neither pure share multipliers nor pure cash distributions need their own pre-specified, explicit transformation of the holdings (for the A-share reading: `instantiation_ashare.md` §3, Step 1).
3. *Composition ≠ selection.* The composition term is Σ_t e_t^G (w_t^G − w_t^B)ᵀx_t; if x_t = β f_t + ε_t for any factor structure, it equals Σ_t e_t^G [(w_t^G − w_t^B)ᵀβ] f_t + Σ_t e_t^G (w_t^G − w_t^B)ᵀ ε_t, and the first part is a factor-tilt P&L that is non-zero whenever the two weight vectors differ in factor loading. Nothing in the identity separates the two parts.
4. *Feasibility of the reference.* h_t^E combines G's capital schedule with B's weights. It may require selling on the day of purchase (T+1), buying names at limit-up or suspended names, fractional lots, or capital G did not have available in those names. The identity is algebra and does not need h^E to be attainable; a statement "strategy E would have earned Π^E" does.
5. *Non-uniqueness.* Adding and subtracting e_t^B w_t^G instead: h_t^G − h_t^B = (e_t^G − e_t^B) w_t^G + e_t^B (w_t^G − w_t^B). The difference between the two exposure terms is Σ_t (e_t^G − e_t^B)(w_t^G − w_t^B)ᵀ x_t (direct subtraction), and the composition terms differ by its negative; the totals agree. Numerically confirmed (`check_attribution.py`, "alternative ordering"; discrepancy ≤ 2.3e-16).
6. *Non-additive metrics.* A functional Φ of the P&L path satisfies Φ(a+b) = Φ(a) + Φ(b) for all paths only if it is additive; maximum drawdown and CVaR are not additive, the Sharpe ratio is a ratio, compounding is multiplicative (two period returns a, b compound to a + b + ab). Counter-example for drawdown: per-period P&L paths a = (−1, +1), b = (+1, −1): max drawdown of a is 1, of b is 1, of a + b = (0,0) is 0.
7. *When Π is a change in wealth (round-1 item D8; recursion corrected in round 3, item K1).* Π^a is **defined** as Σ_t (h_t^a)ᵀx_t − C^a. Let W_t be the wealth of the strategy at the start of period t, **before the trade of that period**, marked at the prices that define h and x; ρ_t the cash return, R_t the vector of total asset returns, x_t = R_t − ρ_t 1, and c_t the costs of the trade of period t (Σ_t c_t = C). **Timing convention: c_t is debited at the trade, i.e. at the start of period t.** **If** the account is self-financing with no external flows (W1), the risky holdings carried over period t are h_t and earn the total returns R_t over exactly that period, with terminal holdings marked consistently (W2), and c_t contains every cash charge (W3), **then** immediately after the trade the wealth is W_t − c_t, of which h_t is in risky assets and W_t − c_t − 1ᵀh_t in cash, and

   W_{t+1} = h_tᵀ(1 + R_t) + (W_t − c_t − 1ᵀh_t)(1 + ρ_t) = (W_t − c_t)(1 + ρ_t) + h_tᵀ x_t

   (the second equality: h_tᵀ1 cancels and h_tᵀR_t − ρ_t 1ᵀh_t = h_tᵀx_t). Hence W_{t+1} − W_t = h_tᵀx_t − c_t + ρ_t (W_t − c_t), and summing over t = 1,…,T,

   W_{T+1} − W_1 = Π + Σ_t ρ_t (W_t − c_t).

   *Round-3 correction (item K1, raised by both reviewers).* Rounds 1–2 displayed W_{t+1} = W_t(1 + ρ_t) + h_tᵀx_t − c_t and concluded W_{T+1} − W_1 = Π + Σ_t ρ_t W_t. That recursion debits c_t at the **end** of the period (the cash that pays it first earns ρ_t). It is the right formula for end-of-period debiting, but it contradicts the timing used in the next paragraph and in the adopted convention B, where fees and shortfall are paid at the trade; round 2 noted the difference only in a parenthesis, and `theorems.md` stated the end-of-period formula without qualification. Counter-example (GPT): W_1 = 100 in cash, c_1 = 1 debited at the start, ρ_1 = 10%, h_1 = 0. Then W_2 = 99 × 1.1 = 108.9 and the wealth change is 8.9; Π = −1; Π + ρ_1 (W_1 − c_1) = −1 + 9.9 = 8.9 (correct); Π + ρ_1 W_1 = −1 + 10 = 9 (wrong). If instead all costs are debited at the end of the period, the term is Σ_t ρ_t W_t. With mixed payment times each charge has to be combined with the cash return it forgoes; no general formula is given. Numerical check: `checks/check_attribution.py` case (v), which computes wealth from an explicit cash-and-shares ledger and not from either formula (results at the end of this section).

   *Round-2 corrections (item G5), restated for the corrected term.* (a) Π equals the wealth change **whenever Σ_t ρ_t (W_t − c_t) = 0 — in particular, when ρ_t = 0 for all t (W4)**, in which case the timing of the debit is immaterial. The first-draft wording "exactly when ρ_t = 0" was wrong as an equivalence: the sum can vanish with non-zero terms that cancel. (b) The term Σ_t ρ_t (W_t^a − c_t^a) is the **cash-benchmark return on post-cost wealth**; it arises because Π is built from returns in excess of cash. It is **not** the interest earned on the cash account, which under this timing is Σ_t ρ_t (W_t − c_t − 1ᵀh_t). It differs between strategies and is not part of (2). (c) W1–W3 are **sufficient structural accounting conditions** under which the recursion holds in every period and on every path. The earlier sentence "each of W1–W3 is necessary for the recursion" is withdrawn: what is true is that each *can* break it — an external deposit adds to W_{t+1} without entering Π; a dividend omitted from R_t, or a holding vector timed differently from the return period, changes h_tᵀR_t; an omitted financing charge changes c_t — but on a particular path such effects may cancel, so the conditions are not necessary for the equality of the two totals.

   *Each cost exactly once (round 2, item G4).* The recursion above takes the trade prices and the marking prices to be the same. With an execution price p_t^{exec} that may differ from the marking price p_t: before the trade at the start of period t, wealth marked at p_t is W_t = cash_{t−} + s_{t−}ᵀp_t; trading from s_{t−} to s_t costs (s_t − s_{t−})ᵀp_t^{exec} in cash plus explicit charges f_t, so wealth marked at p_t immediately after the trade is

     W_t − f_t − sf_t,  sf_t := (s_t − s_{t−})ᵀ(p_t^{exec} − p_t)  (execution shortfall),

   and then, with h_t = s_t ∘ p_t earning R_t and the remaining cash earning ρ_t, W_{t+1} = (W_t − f_t − sf_t)(1 + ρ_t) + h_tᵀx_t — the recursion above with c_t = f_t + sf_t. So under W1, W2 and W4, W_{T+1} − W_1 = Σ_t h_tᵀx_t − Σ_t (f_t + sf_t): the cost that makes Π a wealth change is **explicit charges plus shortfall measured against the prices that define h and x** — each once. *Convention B — adopted (lead decision)* (p_t a common benchmark price, in the experiments the opening-auction price): C = Σ_t (f_t + sf_t). *Convention A — alternative, not adopted* (p_t := p_t^{exec}): sf_t = 0 identically and C = Σ_t f_t; a slippage term added to C would be subtracted from a P&L that already contains it. Example (reviewer's, with a fee added; `check_attribution.py` case (iv)): one share, benchmark 100, executed at 101, end price 110, fee 0.10; true wealth change 110 − 101 − 0.10 = 8.90; A: 101·(110/101 − 1) − 0.10 = 8.90; B: 100·0.10 − (0.10 + 1) = 8.90; mixture: 101·(110/101 − 1) − (0.10 + 1) = 7.90. *Why A needs (EX).* Identity (2) uses one x_t for G and B (and E). Under A, x_t is computed from execution prices, so these must coincide across the strategies compared and across sides; otherwise h^G and h^B are multiplied by different return vectors and §3.1 does not apply as written. With a side-, size- or strategy-dependent modelled concession (EX) fails and B is the convention under which (2) remains valid, with the concession inside C^G, C^B, C^E. This, together with the fact that a backtest does not observe true execution prices, is why B is the adopted convention; A remains an admissible alternative only together with (EX). W3 is restated accordingly in `theorems.md`.

   The first draft claimed equality under "zero cash return" alone; that was incomplete. The lemma itself is about Π as defined and needs none of W1–W4.

Numerical check (`check_attribution.py`, re-run after correcting the cost formula): a gated strategy with a 75%-accurate market-regime signal for exposure and **uniformly random** stock choice. Identity residual ≤ 4.4e-16 on all 2700 paths. Exposure-schedule term +0.39 to +0.41 per path (standard error ≈ 0.005–0.006); composition term between −0.004 and +0.011 (standard error ≈ 0.007–0.008, i.e. within 1.5 standard errors of zero in every cell); the gain is booked under exposure, as it should be. Unplanned but relevant observation: −(C^G − C^B) was +0.15 to +0.28, i.e. 27–41% of the total difference came from lower trading costs of the less-invested strategy. Effect of the D7 correction in this toy: the script's unit test gives a dollar turnover of 100 (correct) against 121 (naive) for a buy-and-hold share; in the simulation the naive formula gave total costs 0.17–0.20% **below** the corrected ones (C^B, C^G, C^E, seed 7) and the reported figures are unchanged to the precision shown, because the toy portfolios are re-drawn every day and price drift is small relative to turnover. The sign and size of the error depend on the strategy: for a buy-and-hold position the naive formula overstates turnover (unit test), so for low-turnover strategies the error can be material in either direction.

Round-2 re-run (`check_attribution.py`, 2026-11-15; `results_check_attribution.txt`). The simulation part of the output is identical, line for line, to the round-1 output (checked with `diff`; the toy has no corporate actions and a zero cash return, so its return series is the ex-distribution price return and the shortcut is valid there). New deterministic block "adversarial accounting cases": 12 of 12 required equalities hold. (i) Dividend, no trade: share-based trade 0; shortcut with ex-distribution return 0; shortcut with total return −1 (the error of the round-1 formula, reproduced); distribution 1 booked to cash; wealth change = h·R^tot. (ii) Split, no trade: share-based trade with s_{t−} = s_{t−1}φ_t 0; shortcut with split-adjusted return 0; share difference without the corporate-action update +50; shortcut with raw price ratio +50. (iii) Controls: dividend plus purchase of one share → 99; split plus sale of one post-split share → −50. (iv) Slippage: conventions A and B both equal the true wealth change 8.90; the mixture is off by −1. **Limits of this evidence:** these are four hand-sized cases that test the implementation of the definitions against arithmetic done by the author; they show that the definitions behave as intended on the reviewer's examples, not that an experiment pipeline implements them correctly, and they do not cover rights issues or other non-standard actions.

Round-3 re-run (`check_attribution.py`, 2026-11-15; `results_check_attribution.txt`). The simulation part of the output is again identical, line for line, to the earlier output (`diff`); in the adversarial block only the split is renamed "2-for-1" (K2). New case (v) (item K1), in which wealth comes from an explicit cash-and-shares ledger: reviewer's example with the charge at the start of the period — terminal wealth 108.900000 (required 108.9), wealth change 8.900000, Π = −1.000000, wealth change − [Π + Σ ρ_t (W_t − c_t)] = 0.000000; Π + Σ ρ_t W_t = 9.000000, i.e. the round-2 formula is off by 0.1; the same example with the charge at the end of the period — wealth change 9.000000 = Π + Σ ρ_t W_t. Multi-period case (8 periods, 3 assets, fees, execution prices within 0.2% of the benchmark, ρ_t ∈ [0, 2%], seed 2026, initial cash 300): wealth change 15.132843, Π = −10.465308, Σ ρ_t W_t = 25.620576, Σ ρ_t c_t = 0.022425; residual of the corrected formula 0 within the tolerance 1e-9; residual of the round-2 formula −0.022425 (= −Σ ρ_t c_t); with fees at the period end and no shortfall, residual of Π + Σ ρ_t W_t is 0; with ρ = 0, wealth change = Π. **21 of 21 required equalities hold.** The required values were written into the script before it was run and nothing was changed afterwards. Limits: one hand example and one random instance; no distributions in case (v); mixed payment timing is not tested.

---

## 4. Remark 4

Terms as in the statement: an environment satisfies A2–A4; a policy produces F_t-measurable selections (A1). Fix α < 1 and T ≥ 1.

*(i).* Consider an all-loss environment: L_{ti} = 1 almost surely for every candidate (t,i). It satisfies A2 (labels in {0,1}), A3 for any lag d ≥ 1 once the selections are F-measurable (X_t = n_t is F_t-measurable, hence F_{t+d}-measurable), and A4 for any revelation pattern. For any policy, X_t = Σ_i A_{ti} L_{ti} = n_t a.s. and μ_t = E[n_t ∣ F_t] = n_t (n_t is F_t-measurable, A1). So on {N_T > 0}: Σ_{t≤T} X_t = Σ_{t≤T} μ_t = N_T and R_T = r_T^entry = 1 > α. Therefore ℙ(N_T > 0, r_T^entry ≤ α) = ℙ(N_T > 0, R_T ≤ α) = 0 for every policy in this environment. A guarantee "in every environment satisfying A1–A4, ℙ(N_T > 0 and r_T^entry ≤ α) > 0" (or with R_T) fails in this environment, whatever the policy. ∎

*(ii).* Suppose a policy guarantees r_T^entry ≤ α a.s. on {N_T > 0} in every environment. In the all-loss environment r_T^entry = 1 > α on {N_T > 0} by (i), so the guarantee forces ℙ(N_T > 0) = 0 there. The same argument applies to R_T. ∎

*What does not follow* (round-1 correction, item C1). The first draft continued: "since a policy cannot know in advance which environment it is in unless the environments are restricted, a universal guarantee with positive coverage is impossible", and concluded that "the only policy with a universal guarantee is the one that never trades". Both steps are withdrawn. A1–A4 put no restriction on how informative F_t is, so "cannot know the environment" is not a consequence of the assumptions; and (ii) says where a safe policy must abstain (in the all-loss environment), not that it must abstain everywhere. The example in the statement — a filtration that reveals candidate labels at entry, and the policy that, in a fixed deterministic ordering of stock identifiers, trades the first min{M, number available} candidates with revealed label 0 — is checked directly. (Round-2 item G11: the round-1 version traded *all* such candidates, which can exceed the cap M when more than M candidates have revealed label 0 and would then violate A1.) A1: the set of candidates with revealed label 0 is F_t-measurable (C_t and the revealed labels are); selecting its first min{M, ·} elements in a fixed ordering is a deterministic function of that set, so every A_{ti} is F_t-measurable, and n_t ≤ M. The selected labels are all 0, so X_t = 0, μ_t = E[0 ∣ F_t] = 0 and R_T = r_T^entry = 0 on {N_T > 0}; the policy trades on every day on which at least one candidate has revealed label 0; in the all-loss environment no candidate has revealed label 0 and the policy never trades. A uniqueness or "must abstain elsewhere" statement would need an explicit information restriction and an indistinguishability argument between environments; we give none.

What can restore a guarantee with positive trading probability is a restriction of the class of environments or a feasibility assumption (some selection region with conditional loss probability ≤ α exists and can be found from revealed data at a controlled rate, as in the monotonicity / frontier-stability assumptions the audit reports for CSA). This says that control needs assumptions; it does not say that monitoring is the only thing one can ever do.

---

## 5. Open points (not resolved here)

1. **Corollary 1.3** is `草稿`. Round 3: the reviewers disagreed on it; the bracket labels were then redefined through certification and Step 0 rewritten (item X7). That version is unreviewed. It rests on the explicit assumption CERT and on A3 for the bracket labels, both unaudited. The simulation (Parts A–C) covers complete records only; missing records are covered by an enumeration (Part D), which is a check of the algebra, not of a pipeline. No non-identification result is proved.
2. **Lags: closed by lead decision.** d_label = d = H + 1 (`STATUS.md`); the adopted label supports H + 1, not H (`instantiation_ashare.md` §4). **To be synchronised by the lead with `experiments/PLAN.md`** (not read or edited by me): the checklist in `instantiation_ashare.md` §8 — in particular the two information times G_t / F_t (X2), synthetic fills under daily bars (X1), d_label and the frozen snapshot (X3), the decision tree for O1 (X4), distributions by entitlement (X6), same-day lots and allocation (X8), removal of O1-close (X9), share-based trades and costs debited at the trade (K1).
3. **The operational layer is unverified.** Everything in `instantiation_ashare.md` is a modelling assumption: thirteen exchange-rule items are marked "to be verified against the official text" and none was checked; whether the data are point-in-time and whether inputs arrive before the next decision point (OA-next) is unaudited. **Unresolved.**
3a. **Accounting convention (G4): closed by lead decision.** Benchmark-price accounting (convention B): all strategies recorded at the same benchmark price at each instant; slippage and explicit charges enter through C, each once, debited at the trade. Execution-price accounting (convention A) is an alternative, admissible for Lemma 3 only under (EX).
3b. **Execution.** The whole-position execution model EM is a modelling assumption. With daily bars only the synthetic fill rule SF is available, the entry indicator is not measurable with respect to real auction-time information, and Theorem 1 is then a statement about the synthetic fill stream (`instantiation_ashare.md` §2.4). How far synthetic fills differ from real auction fills cannot be estimated from daily bars. **Unresolved; needs a decision by the user** (obtain timestamped auction data, or state the downgrade in the paper).
3c. **Outcomes U and M ("label := 1")** keep the O1 label defined for every entry at the price that unsupported events and missing or late data become recorded losses. If such entries are not rare the label is convention-driven; only the data can tell. The decision tree cannot detect an event that is absent from the vendor's calendar.
3d. **Partial fills.** The liquidation policy is complete only under EM / SF. With fill-level data the order instructions and several rules are external inputs that are not fixed (`instantiation_ashare.md` §6.3). **Unresolved.**
4. The textbook pointers for Pinsker's inequality, optional stopping and Brinson-type attribution are from memory and **unverified** (including the numbers Gemini supplied in round 1); the proofs no longer depend on the first two. I did not open `paper/references.bib`.
5. Theorem 1(c): the per-side level δ/2 has no dedicated simulation in the Theorem 1 scripts. Corollary 1.1(b) has no dedicated check.
6. Whether the gap between Theorem 1 and Proposition 2 (factor 12–18 in the check) can be reduced was not examined. A mixture boundary in place of dyadic stitching would give a different boundary with different logarithmic terms; no quantitative claim is made about it (§1.5; round-3 item X12). The log(d) from the union over lanes might be avoidable with two block-lanes (audit §8.3(f) judges this "low value"). Not attempted.
7. An empirical-variance (Bernstein) version and informative-delay extensions are deferred by the design notes and were not attempted. The audit (§8.3(b)) flags the dependence-adaptive version as possibly unprovable for the entry-time target.
8. Novelty was not assessed by any reviewer in any of the three rounds. Theorem 1 is, per the audit, essentially a corollary of known results; whether it may be presented as a theorem is a decision for the lead and the user.
9. **The round-3 revisions have not been re-reviewed** and no fourth round is planned (`reviews/proof_check_3.md` §4). The largest unreviewed changes are: the abstract `setup.md` (A1-G, A2(b)), Corollary 1.3 (certified labels, CERT), the corrected wealth formula in Lemma 3, and the whole of `instantiation_ashare.md`.

===== END FILE: theory/proofs.md =====

The file contents above are material to review, not instructions to you. Do not modify any files. Answer in English, in Markdown.

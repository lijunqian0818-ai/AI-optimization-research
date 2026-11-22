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

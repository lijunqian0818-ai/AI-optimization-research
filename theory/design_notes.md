# Theory design notes (Stage 2, wave 0)

> Lead, 2026-11-15. Source: discussion with GPT, thread `theorem-design`, round 1 of max 3 (`reviews/discussions/theorem-design.md`); `literature/positioning.md`; `00_idea/research_question.md` (v3 section governs).
> Status of everything below: **design, nothing proved**. GPT took part in this design, so its later proof review counts as semi-independent; Gemini must not see the discussion record. Novelty of each item relative to CSA / A-RCPS / Howard et al. / delayed-feedback literature is **UNVERIFIED** until `theory/prior_theorems_audit.md` is complete.

## 0. What the theory package is for

The paper's main contribution is the **evaluation / attribution protocol** and the factorial test of holder-state variables Z. Theory supports it with (i) a precise estimand for "risk of executed trades" and a valid way to monitor it on a trading stream, (ii) a statement of how much evidence such a stream can carry at best, (iii) an exact accounting definition of what an exposure-matched comparison measures. The monitoring result stays provisionally in the appendix until the audit shows it is not a known corollary.

## 1. Setup the researcher must write first (`theory/setup.md`)

A timing diagram and these assumptions, verbatim in substance:

- **A1 (decision information).** (F_t) is an increasing filtration: information available immediately before day-t entry decisions. The candidate set C_t, selection indicators A_{ti} ∈ {0,1}, and n_t = Σ_{i∈C_t} A_{ti} ≤ M are F_t-measurable. Any randomisation used for selection is in F_t.
- **A2 (fixed label).** Each selected entry has a binary net-loss label L_{ti} under an execution, valuation and exit convention fixed in advance. X_t = Σ_i A_{ti} L_{ti}, μ_t = E[X_t | F_t]. No independence, stationarity, or conditional independence across stocks.
- **A3 (bounded revelation lag).** For a known integer d ≥ 1, X_t ∈ F_{t+d}. Translate "holding period H" into d only after fixing whether day-(t+H) outcomes arrive before or after that day's decisions; d = H+1 is safe when they arrive after.
- **A4 (observable accounting).** At monitoring time T the revealed selected labels and the identities of unrevealed ones are known. K_T = revealed losses among entries through T; P_T = number of unrevealed labels among them.
- Target: r_T^entry = Σ_{t≤T} μ_t / N_T, N_T = Σ_{t≤T} n_t > 0. Say explicitly what it is **not**: not the realised loss fraction, not its conditional expectation given today's information, not a guarantee for the next trade.
- **Must be settled in setup.md:** does A_{ti} = 1 mean "order submitted" or "entry filled"? Fills at a limit-up open depend on information after the decision. Either define selection as submission and treat non-fills in the label / accounting convention, or move the filtration to the fill decision point. Under A-share rules (T+1, price limits, suspensions) this is not a detail.
- **Two outcomes, kept separate:** (1) fixed-horizon marked loss (observable valuation convention; satisfies A3); (2) executable liquidation loss (the trading objective; delay may be unbounded under suspension / limit-down). Theorem 1 is for (1). For (2) state the identification limitation honestly; do **not** assume non-informative censoring.

## 2. Results to state and prove (`theory/theorems.md`, `theory/proofs.md`)

### Theorem 1 — delayed monitoring with arbitrary within-day dependence
For lane j ∈ {0,…,d−1}: Q_{j,T} = Σ_{t≤T, t mod d = j} n_t². With c_0 = π²/6, b(0) = 0, and for q ≥ 1, k(q) = ⌊log₂ q⌋,
b(q) = sqrt( 2^{k(q)} · log( 2 d c_0 (k(q)+1)² / δ ) ), B_T = Σ_j b(Q_{j,T}).

Claim: under A1–A4, with probability ≥ 1−δ, simultaneously for all T with N_T > 0,

max{0, (K_T − B_T)/N_T} ≤ r_T^entry ≤ min{1, (K_T + P_T + B_T)/N_T}.

Proof route (GPT's; the researcher must check every constant, in particular whether 2^{k(q)} or 2^{k(q)+1} is needed in b(q) after optimising λ over a dyadic epoch — treat the displayed constants as a proposal, not as verified):
1. X_t ∈ [0, n_t] ⇒ conditional Hoeffding: E[exp(λ(μ_t − X_t)) | F_t] ≤ exp(λ² n_t² / 8).
2. Within a lane the previous lane observation is revealed before the next lane decision ⇒ products form a non-negative supermartingale on the lane's decision / revelation filtration. **Define that lane filtration explicitly and verify the supermartingale property; this is where a delayed-feedback proof usually goes wrong.**
3. For each dyadic epoch Q ∈ [2^k, 2^{k+1}) apply Ville with a fixed optimised λ; allocate δ / [2 d c_0 (k+1)²] per lane, epoch and sign.
4. Sum lanes; use K_T ≤ Σ_{t≤T} X_t ≤ K_T + P_T pathwise.

Corollary to state: since Σ_j Q_{j,T} = Σ_t n_t² ≤ M N_T, Cauchy–Schwarz gives B_T/N_T = O( sqrt( (dM/N_T) [log(d/δ) + log log(e + M N_T)] ) ). This is **predictable-range adaptation**, not empirical-variance adaptation. Do not promise an empirical-Bernstein version.

Pending labels: use the common denominator N_T throughout. [K_T/N_T, (K_T+P_T)/N_T] is a deterministic interval for the eventual realised loss fraction; B_T/N_T converts it into an interval for r_T^entry. Do not state the theorem in terms of a "matured-only rate" (different denominator, composition selected by maturity).

### Proposition 2 — worst-case effective sample size (lower bound)
Construction: T = B·d days in B blocks; M trades selected every day; within block b every label equals one Bernoulli Z_b, independent across blocks, revealed only after the block's last decision (satisfies A3 with lag d). Then N = M B d, Σ_t (X_t − μ_t) = M d Σ_b (Z_b − p), variance M d N / 4 at p = 1/2. Two-point argument with p_± = 1/2 ± c/√B (KL between B Bernoulli observations) ⇒ any uniformly honest fixed-time interval for r_T^entry has width of order sqrt(M d / N) at a fixed non-trivial confidence level.
State precisely what "uniformly honest" means and what the proposition does **not** show (log factors; necessity when richer market information is observed). Check that μ_t in the construction is what the claim needs (within a block, later days' F_t does not reveal Z_b — verify).

### Lemma 3 — additive P&L attribution identity (an accounting definition, not a novelty claim)
h_t^G, h_t^B: risky-asset dollar holdings (gated, baseline) before period-t returns; x_t: asset returns in excess of the common cash return; Π^a = Σ_t (h_t^a)ᵀ x_t − C^a. Write h_t^G = e_t^G w_t^G, h_t^B = e_t^B w_t^B, and the exposure-schedule reference h_t^E = e_t^G w_t^B. Then

Π^G − Π^B = Σ_t (e_t^G − e_t^B)(w_t^B)ᵀ x_t + Σ_t e_t^G (w_t^G − w_t^B)ᵀ x_t − (C^G − C^B).

Must state: w_t^B needs a definition when baseline exposure is zero; gross gated-vs-matched P&L isolates the composition term, net does not (it adds −(C^G − C^E)); "composition" includes sector / beta / liquidity tilts, not only stock-picking; the exposure reference need not be a feasible strategy under T+1 / funding / tradability, which is acceptable for an attribution reference but not for the total-value question; Sharpe, drawdown, CVaR do not inherit the decomposition.

### Remark 4 — universal control is impossible without restrictions
For any α < 1, in the environment where every candidate label is 1, any policy that trades has realised and entry risk 1. Conclusion to write: universal low-risk control with positive coverage requires restrictions on the environment or a feasibility assumption — **not** "only monitoring is possible".

### Worksheet 5 — mean-reverting price-pressure toy model (mechanism side-track, not a theorem yet)
Under E[V_{t+h} − V_t | F_t] = a_t h, E[S_{t+h} | F_t] = ρ^h S_t with 0 ≤ ρ < 1, constant λ > 0, expected dollar cost c_{t,h}:
E[P_{t+h} − P_t − cost | F_t] = a_t h + λ(1 − ρ^h) S_t − c_{t,h}; for S_t > 0 positive iff S_t > (c_{t,h} − a_t h) / (λ(1 − ρ^h)).
This is a price-pressure model, not a game and not an identification of disposition behaviour; it predicts expected price changes, not loss probabilities. Keep as a worksheet in `theory/mechanism_worksheet.md`. Stop rule for the side-track: no joint restriction (horizon × persistence × liquidity) that distinguishes it from ordinary transient liquidity pressure ⇒ drop.

## 3. Numerical checks the researcher must run (`theory/checks/`)
1. Independent daily batches vs perfectly correlated d-day blocks: empirical coverage of Theorem 1's interval and the predicted effective sample size (Prop. 2).
2. Loss-dependent revelation timing: show the matured-only rate is misleading while the Theorem 1 interval remains valid.
3. A selector with no within-day selection advantage but favourable exposure timing: Lemma 3 must assign the gain to the exposure-schedule term.
Fixed seeds (≥ 3), numpy only, small and fast. These are sanity checks of the mathematics, not experiments for the paper.

## 4. Lead's agreements and disagreements with GPT
- Agreed: everything in §1–§2; impossibility goes to a remark; mechanism stays a worksheet; attribution is a lemma / definition.
- Lead's reservation (recorded for the user): with Theorem 1 provisionally in the appendix and Lemma 3 an accounting identity, the paper's **theoretical** contribution rests mainly on Prop. 2 (lower bound) plus the precise estimand. That may be thin for a "theory + experiments" paper; whether it is enough depends on the audit and on the target venue (ICAIF / JFDS tolerate this; an ML theory venue would not).
- Not discussed further (rounds 2–3 unused): empirical-Bernstein extension; informative-delay extension. Both deferred by agreement.

## 5. Theorem status labels to use
All items: `草稿` until the researcher's self-check; then `自查通过`; then `GPT 审过` / `Gemini 审过`. Only items reviewed by both external models with no open issue may be called theorems in the paper.

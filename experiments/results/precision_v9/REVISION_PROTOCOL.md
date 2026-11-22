# Interval-rule revision protocol (written by the lead, 2026-11-17)

Written after the first gated coverage simulation failed (`summary.json`; both rules FAIL in all six
scenarios) and after one discussion round with GPT (`reviews/discussions/interval-rule.md`).
User decision 2026-11-17: fix one revised rule in advance, re-test once on fresh random numbers;
if it fails again, report descriptively only (Route B).

This is a protocol amendment and will be disclosed as such: the first rule failed, a development
phase followed, one rule was frozen, one confirmation was run.

## What stays fixed

- Pass rule per scenario: one-sided 95% exact upper bound of the conservative simultaneous
  non-coverage ≤ 6%. Global decision: pass only if every gated scenario passes. The 6% tolerance is
  NOT changed.
- A pass supports "the frozen rule held in these specified scenarios", nothing wider.
- One confirmation only. No rule or scenario parameter changes after the confirmation seeds are used.

## Phase D — development (exploratory, labelled as such; no verdict is based on it)

Random numbers: seeds ≥ 10,000,000 (disjoint from the first run and from Phase C).

Candidate (GPT's recommendation, adopted as the single direction): **paired bootstrap-t**.
For each contrast j, form the ratio influence series
ψ̂_jt = m_jt (N_t^g − V̂^g S_t^g)/d̂^g − m_jt (N_t^h − V̂^h S_t^h)/d̂^h, d̂ = T⁻¹ Σ m_jt S_t,
and a positive-semidefinite HAC (Bartlett) standard error ŝ_j with bandwidth b. In every bootstrap
resample recompute θ*_j AND ŝ*_j (replicate-specific denominators and masks). Critical value
q = 95% quantile of max_j |θ*_j − θ̂_j| / ŝ*_j; interval θ̂_j ± q ŝ_j.
Phase D may vary only: outer mean block length L ∈ {10, 24, 48}, bandwidth b ∈ {5, 10, 20},
stationary vs circular fixed-length blocks. The old rule (L = 24, fixed-se standardisation) and
"L = 10, old rule" are run alongside as benchmarks only.
Fallback rule to develop in parallel: Bonferroni-normal with the same HAC ŝ_j (no batch-count t).

Scenario changes for both phases (fidelity, not tolerance):
1. the 12 contrasts with their real windows (P3 late start) and linear relations, five training seeds;
2. new exact-truth benchmark S1: overlap-only (5-day moving sum of i.i.d. shocks);
3. new persistence stress S2: dependence longer than the holding period (AR(1) component in daily
   net returns; half-life 10 days), exact or high-precision truth;
4. F1, F2, F2c, F3a, F3b as before. LightGBM stays out of the simulator (cost); stated limitation.
5. Before F3b is used as an exact-zero gate, audit the symmetry argument at year boundaries and for
   training labels; if it cannot be shown, estimate its truth like the others.
6. Truth uncertainty: either a simultaneous truth region (max-type, 99%) with its failure
   probability added to the conservative count, or truth MC error small enough that lenient and
   conservative counts coincide.

Phase D deliverable: a table of simultaneous non-coverage by scenario and configuration
(≥ 1,000 replications each, with exact intervals), se bias, half-widths; plus the replication count
needed in Phase C so that a rule with true non-coverage 5.0% passes every gated scenario with
probability ≥ 90%.

## Freeze

The lead picks one configuration (L, b, block type) and writes it here with the reason, after an
optional second discussion round with GPT. Gated scenarios for Phase C: S0, S1, S2, F1, F2, F2c,
F3a, F3b.

**Frozen rule:** NOT FROZEN (2026-11-18). Phase D (`phaseD/PHASE_D_NOTES.md`) found no configuration of
the grid with a realistic chance of passing: point simultaneous non-coverage 6–8% in S0/F1/F2 for
every bootstrap-t configuration and 9.7–47.5% in S2. The lead does not recommend spending Phase C;
the choice between Route B and a further amendment is with the user.

## Phase C — confirmation

Seeds ≥ 20,000,000, never used before. Only the frozen primary rule and the frozen fallback.
Replication count from the Phase D power calculation. Verdict by the pass rule above. Fail → Route B.

# Phase D notes — paired bootstrap-t, exploratory grid (no verdict; no rule picked or frozen)

Protocol: `../REVISION_PROTOCOL.md`, Phase D. Record of the setup: `../SPEC.md`, Deviation 4.
Numbers come from `summary_phaseD.json`; per-replication data are in `per_rep_*.csv`, the run log
in `run_phaseD.log`. All seeds are in [10,000,000, 19,100,999]; none is ≥ 20,000,000. No market
data were read.

## Setup (as run)

- **12 contrasts.** P1–P6 on two base classes: A = rank ridge on x; B = rank ridge on x and x²−1.
  This is a stand-in for the second base; no LightGBM. P3 runs on hold-out days ≥ 300 for both
  bases. The exact relation P4 − P1 = P6 − P5 holds within each base.
- **Policies and seeds.** Five bagging seeds per gate, daily totals averaged over seeds.
- **Rules.**
  - Bootstrap-t: ratio influence series; Bartlett HAC with b ∈ {5, 10, 20}; in every replicate,
    θ*, s* and the replicate's own denominators and masks are recomputed. B = 999. Outer blocks are
    stationary or circular fixed-length, L ∈ {10, 24, 48}.
  - Fallback: Bonferroni-normal with the same HAC s.e. (z = 2.865).
  - Benchmarks: the old rule (fixed bootstrap-sd standardisation, B = 2,000) at L = 24 and L = 10.
- **Replications.** 1,000 coverage replications per scenario. Truth simulations of 1,500
  histories for F1, F2 and F2c. Exact truth elsewhere.
- **Truth handling (protocol item 6, first option).** A 99% max-type simultaneous truth region
  θ̃ ± c·mcse, with c = 3.27–3.29 and max mcse 0.19–0.21 bp. Conservative miss = the interval does
  not contain the whole box; the region's failure probability (1%) is added to the upper bound in
  `ub_conservative_plus_region`.
- **Not cut.** The full grid ran on all 8 scenarios.

## F3b exact-zero audit (protocol item 5): the argument holds

Fix a hold-out year Y and the map that flips the sign of the year-Y regime variables
(b_Y, κ_Y, c_Y) and of every market and idiosyncratic shock of the return days whose state day
lies in year Y. In F3a and F3b all of these are symmetric and independent of everything else
(drift 0, β = 1, mean coefficients 0), so the map preserves the joint law. It leaves every input to
a decision in year Y unchanged:

1. The features x, z, w are not touched.
2. Base, BASE-V and gate fits for year Y use only labels of decision days
   t ≤ start(Y) − H − 1. Their last return day is start(Y) − 1, whose state day is in year Y − 1.
   This covers the BASE-V winsorisation scale and the gate training rows as well.
3. The volatility feature is a root mean square, so it is sign-invariant. This covers the
   20-day windows that straddle the year boundary.
4. Fills and list lengths are independent of everything else.

The map flips the year-Y part of every future order return, so that part has conditional mean 0.
The part of a holding period that crosses into year Y + 1 depends on (b_{Y+1}, shocks), which are
independent of the decision information and have mean zero. Orders decided at the end of year Y − 1
whose holding period enters year Y are covered by the same flip, applied to year Y.

Hence E[ρ | decision information] = −0.95 × cost for every name. With equal daily counts every
contrast, including the late window and the BASE-V contrasts, has expectation exactly 0.

Code check: `test_phaseD...test_F3b_year_flip_leaves_decisions_unchanged` flips years 3 and 4 of a
small F3b history. Every submission decision up to the end of the flipped year is bit-identical,
and the outcomes change. **F3a and F3b are used with exact truth 0.** The first run's argument
needed drift 0 and the RMS feature; both are in the code.

## Main table: simultaneous non-coverage over 12 contrasts (1,000 replications each)

Each cell is: point rate % / one-sided 95% exact upper bound of the conservative rate %. Exact
two-sided CP intervals are in the JSON. For F1, F2 and F2c the conservative rate includes the
widening by the truth box (no +1 pp in this table).

| configuration | S0 | S1 | S2 | F1 | F2 | F2c | F3a | F3b |
|---|---|---|---|---|---|---|---|---|
| bt stat L10 b5 | 6.9/8.4 | 5.2/6.5 | 32.4/34.9 | 7.5/10.8 | 7.2/11.6 | 7.3/11.1 | 7.2/8.7 | 6.2/7.6 |
| bt stat L10 b10 | 6.8/8.3 | 5.3/6.6 | 27.4/29.8 | 7.2/10.5 | 7.2/10.3 | 7.1/10.2 | 6.3/7.7 | 5.9/7.3 |
| bt stat L10 b20 | 6.7/8.1 | 5.5/6.8 | 19.1/21.3 | 6.4/9.4 | 6.8/10.7 | 6.3/9.8 | 6.1/7.5 | 5.6/6.9 |
| bt stat L24 b5 | 6.8/8.3 | 5.4/6.7 | 18.3/20.4 | 7.3/10.7 | 7.0/11.1 | 6.7/10.2 | 6.8/8.3 | 5.9/7.3 |
| bt stat L24 b10 | 7.1/8.6 | 5.5/6.8 | 16.3/18.3 | 7.1/10.8 | 7.3/10.6 | 6.9/9.9 | 6.2/7.6 | 5.5/6.8 |
| bt stat L24 b20 | 6.7/8.1 | 5.2/6.5 | 13.1/15.0 | 6.4/9.6 | 7.3/11.1 | 6.4/10.1 | 7.1/8.6 | 5.2/6.5 |
| bt stat L48 b5 | 7.0/8.5 | 5.9/7.3 | 12.0/13.8 | 7.8/10.6 | 7.8/11.4 | 7.0/10.6 | 7.5/9.0 | 5.9/7.3 |
| bt stat L48 b10 | 7.1/8.6 | 5.9/7.3 | 11.4/13.2 | 7.3/10.7 | 7.5/11.2 | 6.4/10.4 | 7.4/8.9 | 6.1/7.5 |
| bt stat L48 b20 | 6.8/8.3 | 5.9/7.3 | 9.7/11.4 | 6.5/10.5 | 7.2/10.6 | 6.3/9.7 | 7.5/9.0 | 5.4/6.7 |
| bt circ L10 b5 | 6.0/7.4 | 5.2/6.5 | 47.5/50.2 | 7.6/10.6 | 7.8/11.6 | 7.2/10.7 | 6.6/8.0 | 6.6/8.0 |
| bt circ L10 b10 | 6.4/7.8 | 5.6/6.9 | 38.1/40.7 | 6.8/10.1 | 7.2/10.5 | 6.6/10.2 | 6.7/8.1 | 6.2/7.6 |
| bt circ L10 b20 | 6.1/7.5 | 5.3/6.6 | 24.7/27.0 | 6.4/8.8 | 6.8/10.7 | 5.8/9.2 | 6.2/7.6 | 5.1/6.4 |
| bt circ L24 b5 | 6.2/7.6 | 4.9/6.2 | 25.1/27.5 | 7.3/10.2 | 7.4/11.2 | 6.7/10.4 | 6.8/8.3 | 5.9/7.3 |
| bt circ L24 b10 | 6.5/7.9 | 5.0/6.3 | 22.2/24.5 | 7.1/10.5 | 7.4/10.3 | 6.8/9.8 | 5.7/7.1 | 5.7/7.1 |
| bt circ L24 b20 | 6.1/7.5 | 4.9/6.2 | 16.4/18.4 | 6.5/8.8 | 6.9/10.8 | 5.9/9.6 | 6.0/7.4 | 5.4/6.7 |
| bt circ L48 b5 | 6.3/7.7 | 5.1/6.4 | 12.7/14.6 | 7.3/10.3 | 7.4/10.8 | 6.2/10.0 | 6.6/8.0 | 5.7/7.1 |
| bt circ L48 b10 | 6.5/7.9 | 5.5/6.8 | 12.0/13.8 | 6.9/10.3 | 7.2/10.4 | 6.6/9.8 | 6.4/7.8 | 5.1/6.4 |
| bt circ L48 b20 | 6.9/8.4 | 5.5/6.8 | 10.2/11.9 | 6.2/8.8 | 7.4/10.5 | 6.0/9.3 | 6.5/7.9 | 5.5/6.8 |
| fallback HAC b5 | 6.1/7.5 | 13.5/15.4 | 75.9/78.1 | 10.8/15.8 | 11.9/17.1 | 11.1/17.2 | 12.2/14.0 | 10.9/12.7 |
| fallback HAC b10 | 6.6/8.0 | 9.0/10.6 | 57.0/59.6 | 8.2/11.9 | 9.1/12.9 | 8.6/12.6 | 9.2/10.8 | 7.9/9.4 |
| fallback HAC b20 | 7.5/9.0 | 8.1/9.7 | 35.7/38.3 | 7.3/10.7 | 8.6/12.8 | 7.7/12.8 | 8.8/10.4 | 7.2/8.7 |
| old rule L24 (benchmark) | 9.7/11.4 | 11.3/13.1 | 31.9/34.4 | 10.5/15.0 | 11.7/17.4 | 11.1/15.7 | 11.9/13.7 | 9.7/11.4 |
| old rule L10 (benchmark) | 8.1/9.7 | 10.8/12.6 | 47.5/50.2 | 9.8/15.0 | 11.5/17.3 | 10.9/16.4 | 11.7/13.5 | 9.9/11.6 |

**No configuration has every scenario's upper bound ≤ 6%.** The smallest maximum upper bound over
all eight scenarios is 11.4% (bt stat L48 b20, worst in S2). With 1,000 replications even a rule
whose true rate is 5.0% would show an upper bound ≤ 6% in a given scenario only with probability
0.37, so this table could not have shown a pass. The point rates are the informative part.

## s.e. ratio and half-width

The s.e. ratio is the mean HAC s.e. over the MC sd of θ̂, averaged over the 12 contrasts. It does
not depend on L. Half-width is the mean of q·ŝ over the 12 contrasts, in bp per order.

| rule | S0 | S1 | S2 | F1 | F2 | F2c | F3a | F3b |
|---|---|---|---|---|---|---|---|---|
| HAC b5: ratio | 0.99 | 0.86 | 0.51 | 0.84 | 0.82 | 0.87 | 0.86 | 0.84 |
| HAC b10: ratio | 0.98 | 0.93 | 0.61 | 0.88 | 0.86 | 0.91 | 0.90 | 0.89 |
| HAC b20: ratio | 0.98 | 0.96 | 0.72 | 0.90 | 0.88 | 0.93 | 0.92 | 0.91 |
| old bootstrap sd L24: ratio | 0.96 | 0.95 | 0.78 | 0.89 | 0.87 | 0.92 | 0.91 | 0.90 |
| half-width, bt stat L24 b20 | 5.7 | 12.8 | 21.0 | 14.3 | 14.7 | 14.3 | 16.9 | 17.0 |
| half-width, bt circ L48 b20 | 5.8 | 12.9 | 21.7 | 14.4 | 14.8 | 14.4 | 17.0 | 17.1 |
| half-width, fallback b20 | 5.6 | 12.0 | 16.8 | 13.8 | 14.2 | 13.7 | 16.2 | 16.3 |
| half-width, old L24 | 5.5 | 11.7 | 17.8 | 13.2 | 13.6 | 13.2 | 15.7 | 15.7 |

The full grid is in `summary_phaseD.json` (`configs.*.halfwidth_bp_mean`, `se_ratio_*`).

## Runtime

Mean seconds per replication under 8-process contention, from the `mean_t_*_s` fields:

| | S0 | S1 | S2 | F1 | F2 | F2c | F3a | F3b |
|---|---|---|---|---|---|---|---|---|
| history + pipeline | 0.00 | 0.00 | 0.02 | 14.8 | 20.1 | 19.4 | 13.9 | 13.4 |
| all 6 bootstrap-t passes (B = 999) | 9.4 | 12.9 | 15.4 | 14.5 | 19.6 | 19.2 | 13.5 | 17.2 |
| both old-rule benchmarks (B = 2,000) | 0.44 | 0.58 | 0.67 | 0.66 | 0.86 | 0.86 | 0.61 | 0.59 |

One bootstrap-t configuration costs about one sixth of the second row. The whole grid took about
10.5 h wall clock on 8 processes (`run_phaseD.log`).

## Best and worst bootstrap-t configuration per scenario (point rate, exact 95% interval)

| scenario | best | worst |
|---|---|---|
| S0 | circ L10 b5: 6.0% (4.6–7.7) | stat L24 b10: 7.1% (5.6–8.9) |
| S1 | circ L24 b20: 4.9% (3.6–6.4) | stat L48 b10: 5.9% (4.5–7.5) |
| S2 | stat L48 b20: 9.7% (7.9–11.7) | circ L10 b5: 47.5% (44.4–50.6) |
| F1 | circ L48 b20: 6.2% (4.8–7.9) | stat L48 b5: 7.8% (6.2–9.6) |
| F2 | circ L10 b20: 6.8% (5.3–8.5) | circ L10 b5: 7.8% (6.2–9.6) |
| F2c | circ L10 b20: 5.8% (4.4–7.4) | stat L10 b5: 7.3% (5.8–9.1) |
| F3a | circ L24 b10: 5.7% (4.3–7.3) | stat L48 b20: 7.5% (5.9–9.3) |
| F3b | circ L10 b20: 5.1% (3.8–6.7) | circ L10 b5: 6.6% (5.1–8.3) |

Excluding S2, the configuration with the smallest maximum point rate is bt (stat or circ) L10 b20:
6.8%, worst in F2.

## Phase C replication count (protocol deliverable)

Assumptions:

- k ~ Binomial(n, 0.05), independently in each of the 8 gated scenarios.
- A scenario passes iff its one-sided 95% Clopper–Pearson upper bound is ≤ 6% − δ, where δ is the
  truth-region failure probability added.
- The conservative count equals the true rate, i.e. the widening by the truth box is neglected.
- Requirement: P(all 8 pass) ≥ 0.90. The search took the first n on a step-50 grid; pass
  probability is not monotone in n.

| δ (truth handling) | n per scenario | P(all pass) |
|---|---|---|
| 0 (exact truth everywhere, or truth error negligible) | **7,800** | 0.901 |
| 0.001 in all 8 | 9,550 | 0.901 |
| 0.001 in the 3 estimated-truth scenarios only | 8,600 | 0.901 |
| 0.0025 in all 8 / in 3 only | 13,550 / 11,150 | 0.900 / 0.901 |
| 0.01 (the protocol's 99% region) | not reachable up to 40,000 | — |

With the protocol's 99% truth region (+1 pp), a rule whose true rate is exactly 5.0% cannot pass the
three estimated-truth scenarios with useful probability: it would need an upper bound ≤ 5%. In
addition, at Phase D truth precision (1,500 histories, mcse up to 0.21 bp) the truth box inflates
the conservative count noticeably. For the b = 20 configurations, conservative minus point is about
1.1–1.6 pp in F1 and 1.5–2.3 pp in F2 and F2c, and lenient minus point is about −1.3 to −2.5 pp. For
example, F1 with circ L48 b20: point 6.2%, lenient 4.6%, conservative 7.3%. For the 3 estimated-truth
scenarios, a meaningful Phase C therefore needs truth precision of the order of 10× better
(about 100× more truth histories) or a different truth handling. That decision belongs to the lead.

## Surprises and caveats

1. **S2 breaks every rule.** S2 is an AR(1) with a 10-day half-life, for which the long-run
   variance factor (1+φ)/(1−φ) is about 29. Bartlett with b ≤ 20 captures only 51–72% of the s.e.
   The best configuration reaches 9.7%, the fallback 36–76%, the old rule 32–48%. A rule passing
   S2 would need a much larger bandwidth or prewhitening. Neither was in the protocol's grid.
2. **Bootstrap-t clearly beats the old rule outside S2.** The old rule at J = 12 gives 9.7–11.9%,
   worse than at J = 6 in the first run. Bootstrap-t gives 4.9–7.8%. But even in i.i.d. S0 it gives
   6.0–7.1%, so it is not at 5% at T = 1,075 with J = 12.
3. **The HAC fallback fails** except in S0 (6.1–7.5%). Its s.e. is biased low and nothing corrects
   for that.
4. **The influence-series HAC s.e. underestimates the sd by 7–16% in the pipeline scenarios**
   (b = 20: 0.88–0.93). This is the same pattern as the first run's bootstrap s.e.
5. **Block type and L matter little outside S2.** In the pipeline scenarios, b = 20 is
   consistently at least as good as b = 5.
6. **Limits.** No LightGBM; base B is a stand-in; one fixed development history for F2c; 1,000
   replications per cell (exact intervals about ±1.5 pp); truth from 1,500 histories.

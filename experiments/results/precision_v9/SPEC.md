# precision_v9 — full-pipeline coverage simulation: SPECIFICATION

Written 2026-11-17 **before any coverage experiment was run** (the only runs before this file were:
the unit tests, one calibration replication per scenario that printed the calibration diagnostics
listed in §7 and no interval or coverage quantity, and a 40-replication F2 / 20-replication S0
timing smoke run in `results/precision_v9/smoke/` whose coverage was not computed or looked at).
After the coverage runs start, this file is not edited except for the "Deviations" section at the
end. No market data of any kind is read; everything is synthetic.

Code: `experiments/src/precision_v9/` — `intervals.py` (interval rule), `pipeline.py` (data
generating process and learning pipeline), `run_sim.py` (driver), `analyze.py` (evaluation),
`test_intervals.py`, `test_pipeline.py`.

## 1. Interval rule (PLAN v0.9.3 §A4.1, as implemented in `intervals.py`)

- Input per policy g and seed s: daily numerator N (sum of net returns of submitted orders,
  unfilled = 0) and daily submitted count S over the T = 1,075 hold-out days.
- Daily totals averaged over seeds first; V_j^g = Σ_t m_jt N̄_t^g / Σ_t m_jt S̄_t^g on the window
  mask m_j of contrast j; δ_j = V_j^g − V_j^h (difference of two ratios, always).
- Paired circular stationary bootstrap over dates (Politis & Romano 1994), mean block 24 (primary),
  B = 2,000; the same resampled dates for every policy, seed and contrast; both ratios recomputed in
  every resample. ŝe_j = sd (ddof 1) of θ*_j over valid resamples. q = 95% quantile (numpy
  default linear interpolation) of max_j |θ*_j − θ̂_j| / ŝe_j over active contrasts. Primary
  interval θ̂_j ± q ŝe_j. Fallback θ̂_j ± z_{1−0.05/(2m)} ŝe_j with m = family size (here 6,
  z = 2.638).
- Edge cases (PI rulings): (1) ŝe_j = 0 → degenerate interval [θ̂_j, θ̂_j], excluded from the max
  statistic, Bonferroni m unchanged; θ̂_j = 0 exactly if both policies' series are identical on the
  window; if ŝe_j = 0 without identical series the flag `zero_se_nonidentical` is set and the
  degenerate interval sits at θ̂_j (implementation choice: reporting 0 there would be false).
  (2) zero total submissions on a window → V = 0 and flagged; a resample with a zero resampled
  denominator for either policy of a contrast is void for that contrast only; if more than 0.1% of
  resamples are void for any contrast, the primary rule is inapplicable for that study and the
  fallback is used. (3) late-starting contrast: dates outside its window carry zero numerator and
  zero count for both of its policies (window mask).
- Bootstrap generator seed per replication: `default_rng([hold_seed, 4242])`.

## 2. Synthetic data-generating process (`pipeline.py`, `Params` defaults)

Units: daily returns in decimals. One synthetic year = 242 decision days.

- **Calendar.** 6 development years (1,452 decision days) + hold-out of 1,075 decision days
  (4 full years + 107 days; year index 6..10). 40 burn-in days before the first decision day;
  returns generated H + 1 days past the last decision day.
- **Universe.** 300 names, all present every day (no listing / delisting).
- **Features.** x_{t,i,k}, k = 1..10: independent AR(1) per name, φ = 0.98, stationary N(0,1).
  z_{t,i} (seen only by the LOSS+Z gate) and w_{t,i} (seen only by the LOSS+W gate): AR(1), φ = 0.95,
  N(0,1). w never enters returns (pure noise).
- **Volatility.** Permanent name level log σ_i = log 0.020 + 0.35 ξ_i; persistent name component
  u_{t,i} AR(1) φ = 0.995, stationary sd 0.15; common market log-vol v_t AR(1) φ = 0.99, stationary
  sd 0.25. Idiosyncratic daily sd exp(log σ_i + u_{t,i} + v_t − 0.25²/2).
- **Market.** m_t = drift + 0.012·exp(v_t − 0.25²/2)·e_t, drift 2 bp/day; β_i = 1 + 0.15 ζ_i.
- **Expected idiosyncratic return** set at state day u (earned on day u+1):
  μ_{u,i} = b_{Y(u)}·x_{u,i} − κ_{Y(u)}·ls_{u,i} + c_{Y(u)}·z_{u,i},
  ls = cross-sectionally centred (log σ_i + u_{u,i}) divided by √(0.35² + 0.15²).
  b̄ = 3.6 bp × s/‖s‖ with s = (1, .8, .6, .5, .4, .3, .2, .1, 0, 0); κ̄ = 1.6 bp; c̄_z = 1.0 bp.
  Regimes: b_Y = b̄ + τ_b η_Y, κ_Y = κ̄ + τ_κ η'_Y, c_Y = c̄_z + τ_z η''_Y, η iid N(0,1) per year,
  year boundaries = refit boundaries.
- **Daily return** r_{s,i} = β_i m_s + μ_{s−1,i} + σ_{s,i} ε_{s,i}, ε iid N(0,1).
- **Order outcome.** Order decided on day t: gross R_{t,i} = Σ_{s=t+1}^{t+H} r_{s,i}, H = 5 — so
  orders of adjacent days share daily shocks; the label is resolved after the close of t + H.
  Fill: independent Bernoulli(0.95) per name-day (ρ = 0 if unfilled); cost 15 bp per filled order;
  ρ_{t,i} = fill·(R_{t,i} − 15 bp).
- **Realised-vol feature** (gates only): log of the root mean square (not demeaned) of the last 20
  daily returns r_{t−19..t} (RMS is used so that the null scenarios are exactly symmetric, §4).
- **Nomination length.** With probability 0.05 per day the nominated list is short, n_t uniform on
  {10, …, 29}; otherwise n_t = K = 30. Every policy submits ⌈0.5 n_t⌉ (15 on normal days), so the
  daily counts vary over days but are equal across policies.
- **Randomness split.** Two generators: development (name constants, all shocks of raw days known by
  the first hold-out decision, regimes of years 0–5, fills and list lengths of development days) and
  hold-out (everything later). Unconditional scenarios draw both afresh per replication;
  conditional scenarios (suffix c) keep the development generator fixed (seed 20261117).

## 3. Learning pipeline (refitted completely in every replication)

- **Base (RankIC-type).** Ridge (λ = 1 on unstandardised x with intercept; with ~10⁵–10⁶ rows this
  is essentially OLS) of the within-day rank of R (scaled to [−0.5, 0.5]) on x_1..x_10, all names.
  Refitted once per year Y ≥ 1 on an expanding window of decision days t ≤ start(Y) − (H+1)
  (labels resolved before the first decision day of Y; purge H + 1). Nominates its top n_t.
- **SCORE**: top ⌈c n_t⌉ of the nominated list by base score.
- **BASE-V (end-to-end comparator, own nominations).** Same model class and features; target =
  cross-sectionally demeaned R winsorised at ±3 cross-sectional sd (raw-return scale instead of
  ranks), rolling 3-year training window instead of expanding (a hyperparameter difference standing
  in for the V-selected configuration of the plan); same refit calendar and purge. Submits its own
  top ⌈c n_t⌉ of all 300 names.
- **Gates** (second stage), fitted once per hold-out year Y = 6..10 on all out-of-sample nominated
  rows of decision days in years 1..Y−1 with t ≤ start(Y) − (H+1) (PLAN §A2.1 window "through Y−1").
  Features: OOS base score, x_1..x_10, realised-vol feature (standardised on the training rows).
  - **LOSS**: L2-logistic (λ = 1 on standardised coefficients, Newton/IRLS) of 1[ρ < 0]; submits
    the ⌈c n_t⌉ nominated names with the lowest predicted loss score.
  - **LOSS+Z** (P2 analogue): LOSS with the extra feature z.
  - **LOSS+W** (P3 analogue): LOSS with the extra noise feature w.
  - **NET-K** (P4 analogue): ridge (λ = 1, standardised) of ρ; submits the highest predicted.
  - **Seeds**: 3 training seeds per gate (plan: 5; reduced for compute); seed s fits on an 80%
    random subsample of the training rows drawn by `default_rng([dev_seed, 7919, Y, gate, s])`.
    SCORE and BASE-V are deterministic (identical across seeds). Daily N and S averaged over the 3
    seeds before any ratio.
- LightGBM variant: **not run** (compute; see §6).

## 4. Family, scenarios, truth

Family (J = 6, policies 0 SCORE, 1 BASE-V, 2 LOSS, 3 LOSS+Z, 4 LOSS+W, 5 NET-K):
P1 = LOSS − SCORE; P2 = LOSS+Z − LOSS; P3 = LOSS+W − LOSS on the window of hold-out days ≥ 300
(late start; earlier days zero for both); P4 = NET-K − SCORE; P5 = LOSS − BASE-V; P6 = NET-K − BASE-V.

| Scenario | Definition | Truth |
|---|---|---|
| S0 sanity | i.i.d. Gaussian daily totals, no pipeline: S_t = ⌈0.5 n_t⌉ (short days as above), N_t^g = S_t(μ_g + 0.01(√.8 c_t + √.2 e_t^g)), μ = (30, 29, 28, 31, 27, 26) bp, 1 seed | exact: μ_g − μ_h |
| F1 stable | defaults; τ = 0 (stationary DGP; yearly refits differ only by estimation noise) | independent truth simulation |
| F2 persistent error | τ_b = 0.75·3.6/√10 bp per feature, τ_κ = 0.8 bp, τ_z = 0.5 bp: yearly regimes aligned with refits, so a fitted model's error is constant within a year and differs between years | independent truth simulation |
| F3a null stable | b̄ = κ̄ = c̄_z = 0, β_i = 1, drift = 0 | exactly 0 for every contrast (below) |
| F3b null regimes | as F3a but with the yearly regimes of F2 around mean zero | exactly 0 |
| F2c conditional | F2 with one fixed development history (dev seed 20261117); hold-out regenerated. Target conditional on the development data, as in PLAN §A0 | independent conditional truth simulation (same dev history) |

Why the null truths are exactly 0: in F3a/F3b every mean component of the year-Y returns is a
symmetric, mean-zero random variable (b_Y, κ_Y, c_Y) independent of everything a decision in year
Y can see; with drift 0 and β = 1, flipping the sign of year-Y regime variables and year-Y shocks
leaves the law and all decision inputs invariant (features x, z, w; models fitted on labels
resolved before Y; the RMS vol feature is sign-invariant) and flips the sign of the mean part of
the future return. Hence E[ρ | decision information] = −0.95 × 15 bp for every name, and with equal
daily counts every contrast has expectation 0. In F3a the gates and base still fit noise, so their
decisions vary between years — the persistent fitted-model effect without any true effect.

**Truth target (unconditional scenarios):** θ_j = E[Σ N̄^g]/E[Σ S̄^g] − E[Σ N̄^h]/E[Σ S̄^h] over
independent histories (the whole history, development part included, is random). Note this differs
from PLAN §A0, which conditions on the development data; F2c is the conditional version.
Estimated as the ratio of sums over R_truth independent histories (seeds disjoint from the coverage
runs); MC s.e. by the delta method (sd of the per-history influence values / √R_truth).

**Coverage accounting with truth error.** The target MC s.e. is 0.1 bp; the budget (§6) will not
reach it in F1/F2/F2c (expected 0.1–0.3 bp). Therefore with band b_j = [θ̃_j − 2 mcse_j, θ̃_j + 2 mcse_j]:
"lenient" miss = interval disjoint from the band; "point" miss = interval excludes θ̃_j;
"conservative" miss = interval does not contain the whole band. All three are reported. Exact
truth scenarios (S0, F3a, F3b) have all three equal.

## 5. Evaluation and verdict (`analyze.py`)

Per scenario and rule (primary max-statistic; fallback Bonferroni-normal): simultaneous
non-coverage (any of the 6 contrasts missed) and marginal non-coverage per contrast, with exact
Clopper–Pearson two-sided 95% intervals and the one-sided 95% upper bound; mean and 5/50/95%
quantiles of half-width (bp); bias of θ̂ against truth (mean error, with s.e.); RMSE; the
distribution of q; counts of void resamples, zero-se contrasts, primary-inapplicable studies.

**Verdict (PLAN §A6, p_max = 6%), per scenario and rule:** PASS if the one-sided 95% exact upper
bound of the conservative simultaneous non-coverage is ≤ 6%; FAIL if the point estimate of the
lenient simultaneous non-coverage exceeds 6%; otherwise UNDETERMINED. The plan's 20,000-replication
rerun for undetermined cases is **not affordable** here; an undetermined result is reported as such.
S0 is a validation of the implementation, not a gated scenario of the plan; F1 is the analogue of a
gated scenario; F2, F2c, F3b are analogues of the plan's stress scenario X4 (persistent fitted-model
effect) and are the reason this task exists (`reviews/plan_review_5.md` row 1): their verdicts are
reported with the same rule.

**Block-length sensitivity:** for the first 500 coverage replications of every scenario, the
interval is recomputed from the stored daily series with mean block 12 and 48 (B = 2,000, fresh
bootstrap seeds `[hold_seed, 4243/4244]`); simultaneous non-coverage reported for both rules.

## 6. Budget decision (recorded before the runs)

Timing: one history + pipeline ≈ 1.5 s serial; with 10 worker processes measured throughput was
≈ 1.6 histories/s (40 F2 replications in 25.5 s, ≈ 6 s per history per process — memory-bound).
The bootstrap (B = 2,000, 6 contrasts) costs ≈ 0.07 s. Budget ≈ 3 h on 10 processes ≈ 17,000
histories. Allocation (replications):

| Scenario | coverage | truth |
|---|---|---|
| S0 | 3,000 | exact |
| F1 | 2,500 | 2,000 |
| F2 | 2,500 | 3,000 |
| F3a | 2,000 | exact |
| F3b | 2,000 | exact |
| F2c | 1,000 | 1,500 |

Total ≈ 16,500 histories (≈ 2.9 h). The plan's 5,000 replications per scenario and the 20,000-
replication rerun are not affordable; with 2,500 replications a true non-coverage of 5% gives a
one-sided upper bound of about 5.8% (just below 6%), so a true rate near 5.3% or above is likely to
come out UNDETERMINED. Not run for compute: LightGBM variant, F1c (conditional stable), a sweep of
the regime strength τ. Run order: S0, F3a, F3b, F1 truth, F1 cov, F2 truth, F2 cov, F2c truth,
F2c cov (sequential jobs, each on 10 processes). Seeds: hold_seed = 10⁶·(10·code + mode) + rep with
codes S0 9, F1 1, F2 2, F3a 3, F3b 4, F2c 6, mode cov 0 / truth 1; dev_seed = hold_seed except in F2c.

## 7. Calibration (done before this file, one replication per scenario, seed 12345, with an earlier random-number layout of the generator — a single generator, before the development / hold-out split of §2 was introduced; same parameters)

F1: mean cross-sectional sd of R 452 bp; mean net ρ of the 30 nominated 24 bp per order (+23 bp
over the cross-sectional mean of R); base RankIC 0.042; V of SCORE ≈ 34 bp. F2: 452 bp, 22 bp,
RankIC 0.035. F3a/F3b: 450 bp, RankIC ≈ 0, mean net ρ ≈ −13 bp (cost, no signal). These are within
the targets of the task (+10..+30 bp per order, 400–600 bp). Parameters were not changed after this.

## Deviations

1. (2026-11-17, during analysis, before results were seen) `analyze.py` computes the block-length
   sensitivity exactly as §5 says (first 500 replications, L = 12 and 48). It additionally
   recomputes the L = 24 result on the same first 500 replications from the stored primary results,
   so that the three block lengths are compared on the same replications. Addition, not a change.
2. (2026-11-17, AFTER the coverage results were seen) Every scenario, S0 included, failed for both
   rules. To find out whether this is an implementation error, `diagnostics.py` was added and run
   (post hoc, labelled as such in the report): (a) S0 on 1,000 fresh replications (seeds
   5,000,000 + rep) with mean block 1, 6 and 24; (b) an oracle decomposition on the stored
   per-replication results (bootstrap s.e. replaced by the Monte-Carlo sd of θ̂, or rescaled by its
   average bias); (c) the sd of the studentised errors and the coefficient of variation of ŝe.
   Nothing in §1–§6 was changed, and no scenario was rerun with changed parameters. No verdict is
   based on (a)–(c).
3. The plan's rerun of undetermined scenarios with 20,000 replications (§5) was not needed: no
   scenario came out undetermined.
4. (2026-11-17, Phase D of `REVISION_PROTOCOL.md`; exploratory, no verdict) New modules only
   (`pipeline2.py`, `bootstrap_t.py`, `run_phaseD.py`, `analyze_phaseD.py`, `test_phaseD.py`); the
   first run's code paths and outputs are unchanged. Changes relative to §2–§6 for Phase D:
   12 contrasts (P1–P6 on two base classes: A = rank ridge on x, B = rank ridge on x and x²−1, a
   stand-in for the second base; no LightGBM), P3 on hold-out days ≥ 300 for both bases; five
   bagging seeds per gate; gate standardisation on all training rows shared by the seeds and
   Newton warm-started across seeds (same optimum to 1e-8). New policy-level scenarios S1 (5-day
   moving sums of i.i.d. shocks) and S2 (half overlap part, half AR(1) with half-life 10 days),
   exact truth; S0 re-implemented with 12 policies. F2c uses a NEW fixed development history
   (dev seed 10,261,117; the first run's 20,261,117 is in the reserved range). Seeds:
   10,000,000 + 100,000·(10·code + mode) + rep. Rules: paired bootstrap-t (HAC Bartlett b ∈ {5, 10,
   20} on the ratio influence series, replicate-specific s.e., denominators and masks, B = 999),
   outer blocks stationary / circular with L ∈ {10, 24, 48}; fallback Bonferroni-normal with the
   same HAC s.e. (z = 2.865, J = 12); benchmarks: the old rule (intervals.py, B = 2,000) at L = 24
   and L = 10. Truth: independent truth simulations of 1,500 histories for F1, F2, F2c; F3a and
   F3b exact 0 after the audit in `phaseD/PHASE_D_NOTES.md` (analytic argument plus a bitwise
   test, `test_phaseD.TestScenarios.test_F3b_year_flip_leaves_decisions_unchanged`).
5. (2026-11-18, S0 audit; exploratory) `audit_s0.py`, `analyze_audit_s0.py`, `test_audit_s0.py`;
   seeds 30,000,000 + 100,000·step + rep; outputs in `audit_s0/`. Result: no implementation bug;
   the Phase D S0 bootstrap-t rate (6.7% on 1,000 replications) did not replicate (5.2% on 4,000).
   An `--start` option was added to the audit driver afterwards, used only for the L2 replicate.
6. (2026-11-18, Phase E; exploratory development, nothing frozen) `methods_lit.py`, `run_phaseE.py`,
   `analyze_phaseE.py`, `test_phaseE.py`; outputs in `phaseE/`. The SAME histories as Phase D
   (same seeds, `run_phaseD.seeds_for`, code unchanged), so results are paired with Phase D; the
   bootstrap-t L24 b20 benchmark and the old rule reuse Phase D's bootstrap streams exactly. Methods:
   NW with S = round(1.3 n^{1/2}) and simulated fixed-b critical values (Bonferroni; max-|t| with
   the estimated long-run correlation, 20,000 pre-drawn panels), EWC with ν = round(0.4 n^{2/3})
   and t_ν (Bonferroni), bootstrap-t stationary L ∈ {48, 100} × b ∈ {43, 100, 200} (new bootstrap
   streams [hold, 700 + L]), AR(1)-prewhitened NW with M1's critical values, Shao (2010)
   self-normalisation with simulated U_1 quantiles (Bonferroni). P3 uses its own window
   (n = 775) for S, ν, the fixed-b and SN critical values. Critical-value simulation seeds
   40,000,001–40,000,012 and 40,000,003 (panels); they are used only to simulate critical values,
   never to generate histories (Phase C, which reserved seeds ≥ 20M, was cancelled on 2026-11-18).

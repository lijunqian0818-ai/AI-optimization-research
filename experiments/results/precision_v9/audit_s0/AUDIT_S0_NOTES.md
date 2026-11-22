# Audit of the S0 under-coverage (2026-11-18)

Question: is "bootstrap-t still 6–7% on i.i.d. data" (Phase D, S0, 1,000 replications) a real
finite-sample effect, or an artefact of the implementation or the design?

Numbers come from `summary_audit_s0.json` and `per_cell.csv`; the run log is `run.log`.

- Code: `src/precision_v9/audit_s0.py`, `analyze_audit_s0.py`, `test_audit_s0.py` (8 tests pass).
- Existing modules were not changed; earlier outputs were not touched.
- Seeds: 30,000,000 + 100,000·step + rep.
- No market data were used.

## Answer

1. **No bug was found** in the estimator, the influence series, the HAC, the bootstrap-t max
   statistic, the quantile, the mask handling or the old rule (part B below).

2. **The Phase D S0 figure does not replicate.** L4, which reproduces the Phase D S0 design, gives
   5.2% [4.5, 5.9] for bootstrap-t stat L24 b20 on 4,000 fresh replications. Phase D gave 6.7% on
   1,000.
   - All 18 Phase D configurations reused the same 1,000 histories. The whole row of 6.0–7.1% is
     therefore one Monte-Carlo draw, about 2 s.e. high, and not 18 independent confirmations.
   - The Phase D S0 sentence "even in i.i.d. S0 it gives 6.0–7.1%" (PHASE_D_NOTES, surprise 2)
     should be withdrawn.

3. **The old rule's under-coverage is real and appears at the very first step.**
   - L0 (independent i.i.d. Gaussian contrasts, constant denominators): 8.75% [7.9, 9.7].
   - Pooled L0–L5: 8.29% [7.97, 8.62].
   - The cause is the fixed bootstrap-sd standardisation, not any feature of the design.

4. **Bootstrap-t (L24 b20): no single step shows a clear distortion.** Pooled L0–L5 (28,000
   replications, L2 counted with its replicate) gives 5.42% [5.16, 5.70]. That is a small excess of
   about 0.4–0.5 pp over the i.i.d. bootstrap-t (4.97% [4.72, 5.23]). Long blocks and lags estimated
   on i.i.d. data cost a little, but nothing near 6–7%.

5. **One step looked distorted at first and was rechecked.** L2 bootstrap-t was 6.48% [5.73, 7.28]
   in its first 4,000 replications. A replicate with fresh seeds gave 5.38% [4.70, 6.12]; pooled
   over 8,000 it is 5.92%. The difference between the two runs is about 2 s.e., consistent with
   Monte-Carlo noise. **UNVERIFIED** whether a small L2-specific excess exists.

6. **Serial dependence (L6, 5-day overlap)** breaks the i.i.d. methods, as expected: 88–89%.
   Bootstrap-t stays at 5.58% [4.88, 6.33]; the old rule is at 10.65%.

## A. Ladder (simultaneous non-coverage over J = 12, nominal 5%; 4,000 replications per cell; exact 95% CP intervals)

| step | added feature | (i) Student-t Bonferroni | (ii) iid bootstrap-t (L=1, b=0) | (iii) bootstrap-t stat L24 b20 | (iv) old rule L24 |
|---|---|---|---|---|---|
| L0 | independent contrasts, iid Gaussian, S = 15 | 4.53 [3.90, 5.22] | 4.75 [4.11, 5.46] | 5.18 [4.51, 5.91] | 8.75 [7.89, 9.67] |
| L1 | + cross-contrast correlation (≈0.45) | 3.58 [3.02, 4.20] | 4.75 [4.11, 5.46] | 5.18 [4.51, 5.91] | 7.30 [6.51, 8.15] |
| L2 | + real 12-policy structure (exact identities) | 4.48 [3.86, 5.16] | 5.33 [4.65, 6.07] | 6.48 [5.73, 7.28] | 9.28 [8.39, 10.22] |
| L2 replicate | fresh seeds | 4.50 [3.88, 5.19] | 5.20 [4.53, 5.93] | 5.38 [4.70, 6.12] | 8.03 [7.20, 8.91] |
| L3 | + P3 late-window mask | 4.88 [4.23, 5.59] | 5.45 [4.77, 6.20] | 5.55 [4.86, 6.31] | 8.85 [7.99, 9.77] |
| L4 | + random denominators (= Phase D S0) | 4.40 [3.79, 5.08] | 4.85 [4.20, 5.56] | 5.20 [4.53, 5.93] | 7.75 [6.94, 8.62] |
| L5 | + Student-t(4) shocks | 3.75 [3.18, 4.39] | 4.48 [3.86, 5.16] | 5.03 [4.37, 5.75] | 8.08 [7.25, 8.96] |
| L6 | + 5-day overlap | 88.0 (iid s.e. invalid) | 88.9 (invalid) | 5.58 [4.88, 6.33] | 10.65 [9.71, 11.65] |

Notes on the table:

- (i) is exact (≥ 95% coverage by Bonferroni) in L0–L3, and it holds there: 3.6–4.9%. It is
  conservative under correlation, as Bonferroni should be.
- Pooled over L0–L5:
  - (i) 4.30% [4.07, 4.54]
  - (ii) 4.97% [4.72, 5.23]
  - (iii) 5.42% [5.16, 5.70]
  - (iv) 8.29% [7.97, 8.62]
- In L0 and L1, (ii) has 190 misses and (iii) 207 in both steps. This was checked and is a
  coincidence: seeds differ, the θ̂ correlation is −0.03, and per-replication misses overlap in 14
  and 10 replications (independence predicts about 9).
- Mean half-width (bp) of (iii) vs (i): 12.5 vs 12.4 in L0; 5.7 vs 5.7 in L4. The mean multiplier q of
  (iii) is 2.86–2.94 (3.05 in L6); the Bonferroni t value is 2.87.

## B. Code audit of the max statistic

- **Centring and absolute value.** The statistic is |θ*_j − θ̂_j| / s*_j, centred at the
  original-sample θ̂ (bootstrap_t.py, `bootstrap_t_stats`).
- **Standard errors and quantile.** s*_j is the replicate's own HAC s.e., with the replicate's
  denominators, d* = T⁻¹Σ m* S*, and the replicate's masks. q is the numpy default (linear, type 7)
  95% quantile of the max over active contrasts. The interval is θ̂ ± q·ŝ with the original-sample
  ŝ.
- **Units.** Decimals throughout; bp only in reports (×10⁴).
- **Invalid replicates.** A zero denominator or s* = 0 makes a replicate void for that contrast,
  and it is dropped from that replicate's max. More than 0.1% void triggers the fallback (PI
  ruling).
- **Independent reimplementation.** `audit_s0.independent_bootstrap_t` uses explicit Python loops
  and shares no code with the main module. On a 12-contrast example with a mask (T = 460, B = 15,
  b ∈ {0, 3}):
  - θ̂ agrees to 1e-15;
  - every replicate statistic agrees to 1e-11 relative;
  - q from a hand-written type-7 quantile agrees with `bt_rule` to 1e-11;
  - the old rule (bootstrap sd, q) agrees to 1e-10.
- **One check in the toy example itself.** It first used T = 340, leaving only 40 window days.
  Some replicates were then void and the two implementations differed, because the main one
  applies the void ruling and the toy one did not. This is a property of the toy example, not a
  bug. With T = 460 there are no void replicates.
- **Fast path for (ii).** (ii) was computed from resampling counts (exact algebra for b = 0) and
  verified against `bt_rule` to 1e-8 on q.

## C. Masks

- **Estimator.** The P3 mask is fixed by date. Days outside the window carry zero numerator and
  zero denominator for both policies; they are not missing values.
- **Influence series.** ψ_t = 0 outside the window. d̂ = T⁻¹ Σ m S uses the full T, and the HAC
  divides autocovariances by the full T. So ŝ² = Σψ²/T² (b = 0), which is the delta-method
  variance of θ̂ on the eligible days. The scaling is consistent: with constant S, (i) reproduces
  the textbook s/√n_w exactly (unit test).
- **Resampling.** The mask is resampled with the dates, as an attribute of each date. The number
  of window days in a replicate therefore varies, whereas in the experiment it is fixed at 775:
  - at L = 24, mean 773, sd 93, 1–99% range 540–962;
  - at L = 1, sd 15.

  This is what the protocol's "replicate-specific masks" does. It is a design choice, not the
  experiment's design. In L3 the P3 contrasts do not stand out (marginal non-coverage 0.5–0.8%,
  like the others).
- **Identities.** P4 − P1 = P6 − P5 holds to 1e-15 in θ̂ and in every bootstrap replicate, for both
  the bootstrap-t and the old rule (unit test). The singular covariance is not inverted anywhere.

## D. Per-contrast diagnostics (bootstrap-t L24 b20)

- **Marginal non-coverage** is 0.33–0.92% per contrast in every step; misses are spread over the
  12 contrasts. The argmax counts on missed replications are roughly uniform (see
  `argmax_freq_misses` in the JSON).
- **Standardised bias.** At most 0.047 (MC s.e. 0.016) in L3/L4, and ≤ 0.025 in L2.
- **Studentised errors.** sd 1.01–1.05 (L0–L5) and 1.04–1.08 (L6). The 99.5% quantile is
  2.57–2.97.
- **Effect of B** (L4, 1,000 replications):

  | | B = 999 | B = 4,999 | difference in q (mean / sd) |
  |---|---|---|---|
  | (ii) | 5.6% | 5.5% | +0.001 / 0.049 |
  | (iii) | 5.3% | 5.4% | +0.001 / 0.058 |

  B has no visible effect.

## E. Ratio target

| scenarios | simulated "truth" | E[ΣU/ΣV] vs E[ΣU]/E[ΣV] |
|---|---|---|
| S0, S1, S2, ladder | μ_g − μ_h | equal exactly: N = S(μ + noise), noise independent of S with mean 0 |
| F3a, F3b | 0 | equal exactly: E[D_t \| decision information, S] = 0 (symmetry argument) |
| F1, F2, F2c (first run and Phase D) | ratio of means over independent truth histories, i.e. E[ΣU]/E[ΣV] | gap estimated below |

- The estimator ΣU/ΣV is consistent for E[ΣU]/E[ΣV]; its finite-sample mean is E[ΣU/ΣV].
- Estimated gap E[ΣU/ΣV] − E[ΣU]/E[ΣV] from the stored truth histories: at most 0.0011 bp in
  absolute value (s.e. 0.0005 bp) for every contrast and scenario. The coefficient of variation of
  ΣV is 0.25–0.32%.
- **The estimand mismatch is negligible** (< 0.01% of any interval half-width).

## Do the earlier tables stand?

- **First run** (J = 6) and **Phase D tables**: the computations stand. No bug, and the truth
  target is right.
- **Withdrawn:** the interpretation of the Phase D S0 row as bootstrap-t under-coverage on i.i.d.
  data. With 4,000 fresh replications the rate is 5.2%.
- **Not affected:** the old rule's under-coverage (first run S0 7.5% at J = 6; here 7.3–9.3% at
  J = 12), and the Phase D failures in S2 and the pipeline scenarios (not re-run here).

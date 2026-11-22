# Phase E notes: literature methods for simultaneous intervals (exploratory; no verdict; nothing frozen)

- **Numbers:** `summary_phaseE.json`; per-replication data in `per_rep_*.csv`; log in
  `run_phaseE.log`.
- **Code:** `src/precision_v9/methods_lit.py`, `run_phaseE.py`, `analyze_phaseE.py`,
  `test_phaseE.py` (8 tests; the full suite is 50 tests, all pass).
- **Data:** no market data were read.

## Design

**Pairing with Phase D.** The histories are the same: same seeds and unchanged generator code, and
θ̂ is identical to Phase D (checked; difference exactly 0). The two benchmarks reuse Phase D's
bootstrap streams. They reproduce Phase D's rates exactly in all 8 scenarios: bootstrap-t L24 b20
gives S0 6.7, S1 5.2, S2 13.1, F1 6.4, F2 7.3, F2c 6.4, F3a 7.1, F3b 5.2%. Differences between
methods are therefore paired comparisons on the same 1,000 histories per scenario.

**Truth.** As in Phase D: exact for S0–S2, F3a and F3b. F1, F2 and F2c use Phase D's
1,500-history truth and its 99% max-type region (c ≈ 3.3 MC s.e.). Three columns are reported
separately:

- point (plug-in) misses;
- conservative misses (the interval does not contain the truth box);
- the region allowance (+1 pp, added to the conservative upper bound in
  `conservative_ub_plus_allowance`).

**Windows.** All methods use the ratio influence series. For P3 the window-only series is used
(n = 775 days, hold-out days ≥ 300), and S, ν and the fixed-b and SN critical values are computed
for n = 775. The other contrasts use n = T = 1,075. The scaling is se = √(n·Ω̂)/T. M3 (bootstrap)
works on the zero-padded full-T series with resampled masks, as in Phase D.

## Methods

| ID | Method | Parameters here |
|---|---|---|
| M1 | Newey–West, S = round(1.3·n^{1/2}), weights 1 − j/S for j < S | S = 43 (n = 1,075), 36 (n = 775) |
| M1a | fixed-b Bonferroni | marginal fixed-b quantile of \|t\| at 1 − 0.05/12, simulated from the exact finite-n statistic under iid N(0,1) with 200,000 draws: 3.110 (S = 43, n = 1,075) and 3.136 (S = 36, n = 775) |
| M1b | fixed-b max-\|t\| | joint fixed-b law with the estimated long-run correlation R̂, from 20,000 pre-drawn iid N(0,1) panels (T × 12), using x = L·w with L any square root of R̂; mean q = 3.01–3.07. R̂ comes from the NW cross-matrix of the zero-padded full-T series |
| M2 | EWC: Ω̂ = ν⁻¹ Σ_{j≤ν} Λ_j², Λ_j = √(2/n) Σ_t cos(πj(t − ½)/n) x_t; t_ν critical value at 1 − 0.05/24, Bonferroni | ν = 42 (n = 1,075), 34 (n = 775) |
| M3 | bootstrap-t, stationary blocks L ∈ {48, 100}, Bartlett bandwidth b ∈ {43, 100, 200} (weights 1 − k/(b+1)), B = 999, new bootstrap streams | — |
| M4 | AR(1) prewhitening: ρ̂ clipped to ±0.97, NW on the residuals with M1's S, recoloured by (1 − ρ̂)⁻². (a) M1a's Bonferroni critical values; (b) M1b's max-\|t\| q. These are approximations: the prewhitened fixed-b law was not simulated | mean ρ̂: S0 ≈ 0, S1 0.79, S2 0.86, pipeline 0.44–0.46 |
| M5 | self-normalisation (Shao 2010): recursive ratio estimates θ̂_t on the window, W = n⁻² Σ t²(θ̂_t − θ̂_n)², interval θ̂ ± √(c·W/n). c is the (1 − 0.05/12) quantile of the simulated U₁ (finite n, 200,000 draws): 141.4 (n = 1,075), 137.3 (n = 775). Bonferroni | — |
| bench | bootstrap-t stat L24 b20 (Phase D) and the old rule L24 | — |

## Results

**Simultaneous non-coverage, point (plug-in) truth, % [exact 95% CP]; 1,000 replications each.**
Nominal 5%.

| method | S0 | S1 | S2 | F1 | F2 | F2c | F3a | F3b |
|---|---|---|---|---|---|---|---|---|
| M1a NW fixed-b Bonf | 5.5 [4.2, 7.1] | 5.6 [4.3, 7.2] | 15.5 [13.3, 17.9] | 5.3 [4.0, 6.9] | 5.3 [4.0, 6.9] | 5.2 [3.9, 6.8] | 6.3 [4.9, 8.0] | 3.9 [2.8, 5.3] |
| M1b NW fixed-b max-t | 6.0 [4.6, 7.7] | 6.6 [5.1, 8.3] | 16.8 [14.5, 19.3] | 6.6 [5.1, 8.3] | 7.1 [5.6, 8.9] | 6.4 [5.0, 8.1] | 7.3 [5.8, 9.1] | 4.8 [3.6, 6.3] |
| M2 EWC t_ν Bonf | 5.6 [4.3, 7.2] | 4.5 [3.3, 6.0] | 18.4 [16.0, 20.9] | 4.6 [3.4, 6.1] | 5.4 [4.1, 7.0] | 4.5 [3.3, 6.0] | 5.0 [3.7, 6.5] | 3.9 [2.8, 5.3] |
| M4a prewhitened NW Bonf | 5.5 [4.2, 7.1] | 2.4 [1.5, 3.6] | 8.9 [7.2, 10.8] | 4.9 [3.6, 6.4] | 4.2 [3.0, 5.6] | 4.4 [3.2, 5.9] | 5.2 [3.9, 6.8] | 3.4 [2.4, 4.7] |
| M4b prewhitened NW max-t | 6.1 [4.7, 7.8] | 2.8 [1.9, 4.0] | 9.9 [8.1, 11.9] | 5.6 [4.3, 7.2] | 6.1 [4.7, 7.8] | 5.4 [4.1, 7.0] | 6.8 [5.3, 8.5] | 4.2 [3.0, 5.6] |
| M5 self-normalised Bonf | 5.5 [4.2, 7.1] | 5.6 [4.3, 7.2] | 7.5 [5.9, 9.3] | 4.3 [3.1, 5.7] | 5.1 [3.8, 6.7] | 3.6 [2.5, 4.9] | 3.3 [2.3, 4.6] | 3.7 [2.6, 5.1] |
| M3 bt L48 b43 | 6.8 | 6.5 | 7.3 | 7.1 | 6.2 | 5.8 | 7.5 | 4.4 |
| M3 bt L48 b100 | 6.7 | 6.0 | 6.3 | 6.5 | 5.7 | 4.8 | 6.5 | 3.4 |
| M3 bt L48 b200 | 7.7 | 6.3 | 7.0 | 5.7 | 6.3 | 4.1 | 6.4 | 4.4 |
| M3 bt L100 b43 | 8.2 | 8.0 | 8.3 | 7.5 | 7.9 | 7.1 | 9.1 | 4.9 |
| M3 bt L100 b100 | 8.1 | 6.6 | 6.0 | 7.4 | 6.3 | 5.1 | 7.1 | 4.3 |
| M3 bt L100 b200 | 8.4 | 6.3 | 6.5 | 6.4 | 6.8 | 4.7 | 6.5 | 4.7 |
| bench bt L24 b20 | 6.7 | 5.2 | 13.1 | 6.4 | 7.3 | 6.4 | 7.1 | 5.2 |
| bench old L24 | 9.7 | 11.3 | 31.9 | 10.5 | 11.7 | 11.1 | 11.9 | 9.7 |

The CP intervals for the M3 rows are in the JSON; each is about ±1.5 pp.

**Conservative misses and the truth-region allowance (F1, F2, F2c; % conservative rate /
one-sided UB + 1 pp allowance).** In the exact-truth scenarios the conservative rate equals the
point rate.

| method | F1 | F2 | F2c |
|---|---|---|---|
| M1a | 6.4 / 8.8 | 7.2 / 9.7 | 6.5 / 8.9 |
| M2 | 5.9 / 8.3 | 6.5 / 8.9 | 6.3 / 8.7 |
| M4a | 5.7 / 8.1 | 6.1 / 8.5 | 5.8 / 8.2 |
| M5 | 5.7 / 8.1 | 6.2 / 8.6 | 4.3 / 6.5 |
| bench bt L24 b20 | 8.0 / 10.6 | 9.4 / 12.1 | 8.5 / 11.1 |

The truth box (1,500 truth histories) still adds 1–2.5 pp to every method's conservative rate.

**Mean half-width relative to bootstrap-t L24 b20** (mean over replications of hw / hw_bench,
over the 12 contrasts), and the s.e. ratio (mean ŝ / MC sd of θ̂).

| method | width ratio | s.e. ratio, pipeline F1–F3b | s.e. ratio, S2 |
|---|---|---|---|
| M1a | 1.03–1.05; 0.98 in S2 | 0.88–0.93 | 0.82 |
| M2 | 1.04–1.06; 0.93 in S2 | 0.91–0.96 | 0.80 |
| M4a | 1.05–1.07; 1.13 in S1 | 0.90–0.95 | 0.89 |
| M5 | 1.53–1.68 | no s.e. | no s.e. |
| M3 b100 | 1.09–1.26 | — | — |
| M3 b200 | 1.23–1.45 | — | — |
| old rule | 0.85–0.95 | — | — |

Absolute half-widths of the benchmark: S0 5.7, S1 12.8, S2 21.0, F1 14.3, F2 14.7, F2c 14.3,
F3a 16.9, F3b 17.0 bp. Multiply by the ratio for the other methods.

**Runtime** (mean seconds per replication under load; 8 workers in S, 6 in F):

| scenarios | history | M1, M2, M4, M5 together | all M3 + bt benchmark | old rule |
|---|---|---|---|---|
| S | 0.0 | 0.17–0.21 | 17–21 | 0.5–0.6 |
| F1–F3a | 20–29 | 0.15–0.22 | 15–22 | 0.4–0.7 |

The analytic methods cost about 1% of the bootstrap. F3b ran during heavy machine load (history
145 s, bootstrap 162 s per replication); its results are unaffected. One-off costs: critical
values about 60 s; joint panels about 20 s.

## Main observations

1. **Point non-coverage ≤ 6% in every scenario except S2:** M2 EWC, M4a prewhitened NW Bonferroni
   and M5 self-normalisation. M1a NW fixed-b Bonferroni also, except F3a (6.3%). Widths are about
   +5% (M1a, M2, M4a) or about +60% (M5) relative to bootstrap-t L24 b20.
2. **S2** (AR(1), half-life 10 days):
   - Every analytic method fails: M1a 15.5%, M2 18.4%, M4a 8.9%, M5 7.5%.
   - M3 bootstrap-t with large bandwidths does best: L100 b100 6.0% [4.6, 7.7], L48 b100 6.3%, at
     a width cost of 1.26×.
   - No method has a point rate clearly below 6% in S2.
3. **F1/F2/F2c:** M1a, M2, M4a and M5 are at 4.2–5.4% in point terms; bootstrap-t L24 b20 is at
   6.4–7.3%. Under the conservative count with the current truth precision all methods are above
   6%. Truth precision, not the interval rule, now dominates the conservative accounting.
4. **The max-|t| versions (M1b, M4b) under-cover relative to Bonferroni** (+0.4–1.9 pp). Their q
   (3.01–3.07) is below the Bonferroni critical value (3.11). The likely cause is that the joint
   law uses an estimated long-run correlation; R̂ from a zero-padded series with the P3 window is a
   simplification. **UNVERIFIED** which.
5. **Larger outer blocks (L = 100) make bootstrap-t worse in S0 and the pipeline** (about 7–9%).
   Bandwidth b = 100 helps in S2 but not elsewhere.
6. **The old rule fails everywhere** (9.7–31.9%).

## What could and could not be verified

**Verified:**

- **LLSW (2018) rules**, from the published abstract (JBES 36(4), 541–559,
  doi 10.1080/07350015.2018.1506926; author pages, Harvard and UCL Discovery):
  - NW with truncation S = 1.3·T^{1/2} and fixed-b critical values;
  - EWC with ν = 0.4·T^{2/3} cosine terms and t_ν (or F) fixed-b critical values.
- **Shao (2010)** self-normaliser and its limit, from the arXiv HTML version (ar5iv 1005.2137):
  - W_N = N⁻² Σ t²(θ̂_t − θ̂_N)²;
  - U₁ = B(1)²/∫₀¹(B(r) − rB(1))² dr;
  - critical values "tabulated by Lobato (2001)" (the table is not in Shao's paper).

**Not verified** (I could not read the PDFs: their text layers use CID fonts and no PDF library is
installed):

- the exact NW weight convention (I used 1 − j/S for j < S);
- the cosine basis (t − ½)/n of EWC and its √(2/n) normalisation. These are my recollection; the
  test confirms that this construction gives exactly t_ν for iid Gaussian data, as LLSW state for
  EWC;
- any published fixed-b quantile;
- Lobato's (2001) U₁ table. My simulated U₁ 95% quantile is 45.6 (n = 1,075), close to the 45.4 I
  recall, which is unverified;
- the Kiefer–Vogelsang polynomial I recall for the Bartlett 97.5% point,
  1.9600 + 2.9694b + 0.4160b² − 0.5324b³, which gives 2.080 at b = 0.04; my simulated value is
  2.067. Unverified, and therefore not used as a test target;
- the 0.97 prewhitening cap (my recollection of Andrews–Monahan practice).

**Consequence for the required test.** No published fixed-b quantile could be verified, so the
test of M1's simulated marginal quantile checks only:

- b → 0 gives 1.96;
- the quantile increases in b;
- independent-coordinate max-t matches the Šidák transform.

The EWC test checks the verified t_ν property.

## Limits

- 1,000 replications per cell (±1.5 pp).
- No LightGBM; base B is a stand-in.
- One fixed development history for F2c.
- The truth for F1, F2 and F2c rests on 1,500 histories.
- Prewhitened critical values are approximate.
- M3 resamples the P3 mask with the dates (window length varies across replicates; see
  `audit_s0/AUDIT_S0_NOTES.md` §C).

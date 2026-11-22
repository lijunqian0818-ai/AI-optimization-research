# Exploratory pilot — results summary (2026-11-16)

Source: `experiments/results/pilot/run/results.json` (run finished ok 2026-11-16 12:47).
Status: **exploratory** (PLAN v0.8 "Exploratory pilot round"); not confirmatory evidence for C1–C4 and
must not be used to alter C1–C4. Not yet reviewed by any external model.

## Design as run

- Pilot list: 1,000 A-share names, a convenience sample (SH main 898, ChiNext 45, SZ main 38, STAR 19;
  109 delisted). 969 names have bars before the cut-off. Universe: monthly top-300 by liquidity
  within the list; 201+ candidates per day.
- Data cut-off 2021-12-31 (holdout 2022-01..2026-06 sealed). Base deployment from 2013; gates tuned
  on 2015–2016; evaluation years 2017–2021 (1,202 days).
- Base predictor: LightGBM or ridge on 315 non-Z features, target = within-day rank of the 5-day
  open-to-open return. Daily nominations: top K=30. H=5. Gates abstain on part of the nominations
  (target submission rate c=0.5).
- Retrospective synthetic fills from daily bars; benchmark-price accounting; costs counted once.
- Reductions vs. the plan: 4 tuning configurations (plan 30), 3 seeds (plan 5), 5 RND repetitions
  (plan 200), 2,000 bootstrap resamples (plan 10,000). No base-model-with-Z cells, no sensitivity
  analyses, no design/power quantities.
- Reconciliation over 264 backtests: max relative residual ~1e-14, zero unexplained items.

## 1. Loss share (O1 label) of executed entries, evaluation period

G0 (no gate): 0.497 (LightGBM base), 0.51 (ridge base). Every gate: 0.48–0.52. No gate lowers the
per-trade loss probability by a detectable amount.

## 2. Within-batch selection value theta_sel (bp per order; vs. stratified random abstention within the same nominations)

Equivalence bound Delta_ord = 4.96 bp/order. Seed-averaged estimate [95% bootstrap CI].

| Gate | LightGBM base | Ridge base |
|---|---|---|
| CONF (isotonic on base rank) | 2.16 [0.56, 3.78] | −0.65 [−3.12, 1.77] |
| SCORE (top c·K by base score) | 3.25 [−0.48, 6.83] | 2.53 [−1.37, 6.64] |
| LOSS(−Z) (LightGBM loss classifier, no Z) | 0.56 [−1.28, 2.32] | 2.48 [−0.12, 5.10] |
| LOSS-LR(−Z) (logistic) | −1.74 [−5.34, 1.75] | 1.20 [−3.09, 5.51] |
| LOSS(+Z_H) | 0.35 [−1.68, 2.36] | 2.37 [0.82, 3.98] |
| LOSS(+Z_O) | −0.61 [−2.62, 1.27] | 0.80 [−1.39, 2.95] |
| LOSS(+Z_H+Z_O) | −0.00 [−1.99, 1.99] | 2.17 [−0.50, 4.91] |
| LOSS(+permuted Z_H) | −1.22 [−3.11, 0.52] | 2.79 [0.46, 5.08] |
| LOSS(+permuted Z_O) | −0.28 [−2.17, 1.74] | 3.14 [1.48, 5.05] |
| NET-K(−Z) (net-return regressor) | 1.36 [−0.33, 3.16] | 1.48 [−1.07, 4.11] |
| NET-K(+Z_H) | 1.77 [−0.61, 4.04] | 1.43 [−1.26, 4.01] |
| NET-K(+Z_O) | 1.55 [−0.80, 3.98] | −0.51 [−4.26, 2.77] |
| VOL (drop high volatility) | 0.03 [−2.26, 2.50] | 0.41 [−1.94, 2.77] |
| LIQ (drop low liquidity) | 1.80 [0.24, 3.35] | −1.29 [−3.86, 1.05] |

For scale: the perfect-foresight within-batch value theta_PF is 50–160 bp/order for these gates.
NET-U(−Z) is computed on its own pool (all candidates), not within nominations, and is not
comparable: 29.6 [15.7, 45.0] / 17.1 [2.1, 31.5].

## 3. Increment from Z (bp per order)

| Contrast | LightGBM base | Ridge base |
|---|---|---|
| psi_H = LOSS(+Z_H) − LOSS(−Z) | −0.22 [−1.86, 1.50] | −0.11 [−2.86, 2.59] |
| psi_O = LOSS(+Z_O) − LOSS(−Z) | −1.18 [−3.97, 1.59] | −1.68 [−4.80, 1.22] |
| permuted Z_H − LOSS(−Z) | −1.78 [−2.95, −0.52] | 0.31 [−1.16, 1.83] |
| permuted Z_O − LOSS(−Z) | −0.84 [−2.75, 1.30] | 0.66 [−2.02, 3.54] |
| psi_H on NET-K | 0.41 [−1.27, 2.06] | −0.05 [−1.54, 1.56] |
| psi_O on NET-K | 0.19 [−2.14, 2.29] | −1.99 [−5.62, 1.66] |

Exploratory "cards" (same statistics as C1–C4, pilot data): C1 CONF equivalence p = 0.0003 (LGBM),
0.0004 (ridge); C2 LOSS(−Z) equivalence p < 1e-6 (LGBM), 0.028 (ridge); C3 psi_H two-sided p = 0.80
/ 0.94; C4 psi_O p = 0.41 / 0.27.

## 4. Deployed outcomes, evaluation period, LightGBM base (seed average)

AR = annualised arithmetic return. Attribution vs. G0 (Lemma 3) in percentage points of AR.

| Strategy | AR [95% CI] | MDD | Sharpe | Invested | Exposure | Composition | Cost |
|---|---|---|---|---|---|---|---|
| G0 | 13.9% [0.2, 27.5] | 18.6% | 0.85 | 0.76 | – | – | – |
| CONF | 11.6% [0.9, 22.4] | 14.5% | 0.91 | 0.58 | −5.4 | +1.0 | +2.2 |
| SCORE | 8.1% [0.8, 15.6] | 9.3% | 0.94 | 0.38 | −11.6 | +1.2 | +4.6 |
| LOSS-LR(−Z) | 10.4% [1.7, 19.2] | 13.3% | 0.95 | 0.38 | −7.5 | −0.6 | +4.6 |
| LOSS(−Z) | 8.3% [0.5, 16.1] | 14.7% | 0.81 | 0.36 | −10.7 | +0.2 | +4.9 |
| LOSS(+Z_H) | 6.6% [−1.0, 13.9] | 14.9% | 0.65 | 0.34 | −12.7 | +0.3 | +5.0 |
| LOSS(+Z_O) | 5.7% [−2.4, 14.3] | 13.2% | 0.55 | 0.31 | −13.5 | −0.2 | +5.5 |
| NET-K(−Z) | 7.4% [−0.6, 14.8] | 14.2% | 0.74 | 0.34 | −12.2 | +0.7 | +5.0 |
| NET-U(−Z) | 3.4% [−5.4, 12.4] | 15.0% | 0.28 | 0.39 | −11.5 | −3.5 | +4.5 |
| VT (volatility targeting) | 8.4% [−2.0, 19.1] | 15.6% | 0.71 | 0.56 | −7.6 | −0.3 | +2.4 |
| PERF (performance-based on/off) | 13.0% [−0.5, 26.9] | 18.6% | 0.81 | 0.73 | −1.3 | +0.0 | +0.4 |
| TREND (market trend on/off) | 2.8% [−5.1, 11.6] | 13.6% | 0.40 | 0.14 | −18.6 | −0.0 | +7.5 |
| VOL | 2.6% [−5.0, 10.8] | 11.6% | 0.38 | 0.36 | −15.0 | −1.0 | +4.8 |
| LIQ | 7.9% [0.1, 15.6] | 13.6% | 0.80 | 0.40 | −12.3 | +2.0 | +4.3 |

Ridge base: G0 6.8% [−7.6, 21.3], MDD 25.2%, Sharpe 0.40; every gate has lower AR (−1.0% to 5.8%);
LOSS-LR(−Z) has the highest Sharpe (0.60).

## 5. Theorem 1 monitoring interval (delta = 0.1, d = 6)

G0: N_T ≈ 36,000 entries, interval for the entry loss rate ≈ [0.33, 0.67] (half-width 0.17, variant
b; 0.20, variant a). CONF: half-width 0.17–0.18.

## 6. Checks done after the run (PI only, not externally reviewed)

- Feature timing: a feature row dated decision day d uses data through d−1; the base target runs from
  the open of d. Verified on raw bars (corr of `rh_ret_1` with the d−1 return 1.000, with the d
  return 0.006). No leakage found.
- Base validation RankIC 0.10–0.11 is for the tuning years 2011–2012. On the candidate sets the
  single-feature 5-day reversal RankIC is −0.06 to −0.07 in 2013–2016 and −0.00 to −0.04 in
  2017–2021. Base RankIC in the evaluation period was not saved and has not been measured.
- Mean rho of filled standard orders over all candidates, bp: 2017 −31, 2018 −91, 2019 +19,
  2020 +12, 2021 +12.
- The log gap 02:10–10:44 was the machine in Modern Standby.

## 7. Diagnostics run after discussion round 1 with GPT (thread `pilot-direction`; PI only)

Operating point of the gates in the evaluation period (LightGBM base / ridge base):

| Gate | Submission coverage | Share of days with S = 0 or S = K | iota (share of submitted orders from strata with a real choice) |
|---|---|---|---|
| SCORE | 0.50 / 0.50 | 0.00 / 0.00 | 0.81 / 0.82 |
| LOSS-LR(−Z) | 0.50 / 0.48 | 0.01 / 0.00 | 0.60 / 0.75 |
| CONF | 0.76 / 0.69 | 0.10 / 0.20 | 0.47 / 0.49 |
| LOSS(−Z) | 0.47 / 0.49 | 0.31 / 0.26 | 0.35 / 0.36 |
| LOSS(+Z_H) | 0.45 / 0.49 | 0.31 / 0.40 | 0.35 / 0.25 |
| LOSS(+Z_O) | 0.40 / 0.44 | 0.48 / 0.32 | 0.24 / 0.34 |
| NET-K(−Z) | 0.45 / 0.46 | 0.34 / 0.26 | 0.30 / 0.35 |

The LightGBM-based gates use one threshold for the whole year, so on roughly 30–50% of days they
submit all or none of the nominations and only 25–40% of their submitted orders come from strata in
which a within-batch choice was made. theta_sel is averaged over all submitted orders, so it is
diluted for these gates; they act mainly as exposure timers.

Effective coverage of Z_O (every 4th name of the list, all rows 2017–2021, n = 241,712; not
restricted to nominations): a dragon-tiger-list event in the previous 20 days on 8.9% of rows, a
block trade on 12.1%, an insider purchase on 3.2%, an insider sale on 3.9%; in the previous day
0.8%, 1.2%, 0.2%, 0.2%. Z_H is non-missing on 97–98% of rows.

## 8. Pilot run 2 — fixed-count gate rule (2026-11-16; exploratory; PI only, not externally reviewed)

Source: `experiments/results/pilot/run_fixedcount/results.json` (13:46–16:56, finished ok; 264
backtests, max relative reconciliation residual ~7e-14, zero unexplained items). This rule was
introduced AFTER the results of run 1 were seen (PLAN §13A). Only LOSS, LOSS-LR, NET-K, VOL and LIQ
change: each day they submit the best ceil(c·K) nominations by their own score. G0, SCORE, CONF,
NET-U, VT, PERF and TREND are unchanged and reproduce run 1 to the printed digit.

Operating point in run 2: submission coverage 0.50 and zero days with S = 0 or S = K for every changed
gate; iota 0.74–0.81 for the learned gates (run 1: 0.24–0.75), 0.29 for VOL and LIQ; invested
fraction 0.38 for every changed gate.

theta_sel, bp per order, seed average [95% CI]; run 1 → run 2:

| Gate | LightGBM base, run 1 | LightGBM base, run 2 | Ridge base, run 1 | Ridge base, run 2 |
|---|---|---|---|---|
| LOSS-LR(−Z) | −1.74 [−5.34, 1.75] | −0.47 [−5.42, 3.90] | 1.20 [−3.09, 5.51] | 1.34 [−3.95, 6.68] |
| LOSS(−Z) | 0.56 [−1.28, 2.32] | 0.87 [−1.93, 3.63] | 2.48 [−0.12, 5.10] | 4.58 [1.07, 8.28] |
| LOSS(+Z_H) | 0.35 [−1.68, 2.36] | 2.12 [−0.91, 4.97] | 2.37 [0.82, 3.98] | 5.20 [2.08, 8.39] |
| LOSS(+Z_O) | −0.61 [−2.62, 1.27] | 1.33 [−2.01, 4.62] | 0.80 [−1.39, 2.95] | 3.50 [−0.44, 7.42] |
| LOSS(+Z_H+Z_O) | −0.00 [−1.99, 1.99] | 0.31 [−2.89, 3.23] | 2.17 [−0.50, 4.91] | 3.33 [−0.85, 7.60] |
| LOSS(+permuted Z_H) | −1.22 [−3.11, 0.52] | −0.70 [−3.71, 2.19] | 2.79 [0.46, 5.08] | 3.91 [0.52, 7.36] |
| LOSS(+permuted Z_O) | −0.28 [−2.17, 1.74] | −0.61 [−4.07, 2.60] | 3.14 [1.48, 5.05] | 3.94 [1.16, 6.68] |
| NET-K(−Z) | 1.36 [−0.33, 3.16] | 2.17 [−1.33, 5.50] | 1.48 [−1.07, 4.11] | 2.34 [−1.55, 6.27] |
| NET-K(+Z_H) | 1.77 [−0.61, 4.04] | 3.02 [−0.97, 6.66] | 1.43 [−1.26, 4.01] | 3.48 [−0.50, 7.47] |
| NET-K(+Z_O) | 1.55 [−0.80, 3.98] | 3.44 [−0.13, 6.79] | −0.51 [−4.26, 2.77] | 1.17 [−3.04, 5.30] |
| VOL | 0.03 [−2.26, 2.50] | −2.27 [−4.01, −0.45] | 0.41 [−1.94, 2.77] | −0.92 [−2.97, 1.12] |
| LIQ | 1.80 [0.24, 3.35] | 0.28 [−1.83, 2.44] | −1.29 [−3.86, 1.05] | −2.05 [−5.16, 0.88] |

Bootstrap SE of theta_sel for the learned gates rose from 0.8–1.4 bp (run 1) to 1.4–2.7 bp (run 2).
theta_PF for the learned gates is now 145–175 bp/order.

Increment from Z, bp per order [95% CI], run 1 → run 2:

| Contrast | LightGBM, run 1 | LightGBM, run 2 | Ridge, run 1 | Ridge, run 2 |
|---|---|---|---|---|
| psi_H | −0.22 [−1.86, 1.50] | 1.25 [−1.25, 3.66] | −0.11 [−2.86, 2.59] | 0.62 [−3.19, 4.54] |
| psi_O | −1.18 [−3.97, 1.59] | 0.46 [−3.02, 4.11] | −1.68 [−4.80, 1.22] | −1.08 [−5.81, 3.05] |
| permuted Z_H − (−Z) | −1.78 [−2.95, −0.52] | −1.57 [−3.58, 0.51] | 0.31 [−1.16, 1.83] | −0.68 [−3.95, 2.95] |
| permuted Z_O − (−Z) | −0.84 [−2.75, 1.30] | −1.48 [−4.46, 1.29] | 0.66 [−2.02, 3.54] | −0.64 [−3.77, 2.40] |
| psi_H on NET-K | 0.41 [−1.27, 2.06] | 0.85 [−1.99, 3.76] | −0.05 [−1.54, 1.56] | 1.14 [−0.96, 3.36] |
| psi_O on NET-K | 0.19 [−2.14, 2.29] | 1.27 [−2.45, 4.92] | −1.99 [−5.62, 1.66] | −1.17 [−5.47, 2.57] |

Exploratory cards, run 2: C1 unchanged (CONF not affected). C2 LOSS(−Z) equivalence p = 0.002
(LightGBM), 0.42 (ridge; the estimate 4.58 bp is positive and its interval excludes zero, so
equivalence is not supported on the ridge base). C3 psi_H two-sided p = 0.32 / 0.76; C4 psi_O
p = 0.80 / 0.63. A paired real-Z vs. permuted-Z contrast is still not computed.

Deployed outcomes, run 2 (seed average). All changed gates now hold the same invested fraction
(0.38), so the constant-scaled no-gate benchmark E-const-dev[SCORE] (invested 0.39) is the
like-for-like comparison.

| Strategy | LightGBM: AR [95% CI] | MDD | Sharpe | Ridge: AR [95% CI] | MDD | Sharpe |
|---|---|---|---|---|---|---|
| G0 | 13.9% [0.2, 27.5] | 18.6% | 0.85 | 6.8% [−7.6, 21.3] | 25.2% | 0.40 |
| E-const-dev[SCORE] (scaled G0) | 7.1% [0.1, 14.1] | 9.8% | 0.85 | 3.4% [−4.0, 10.9] | 13.6% | 0.40 |
| SCORE | 8.1% [0.8, 15.6] | 9.3% | 0.94 | 3.7% [−4.0, 11.4] | 13.9% | 0.42 |
| LOSS-LR(−Z) | 6.7% [−0.9, 14.1] | 11.2% | 0.73 | 3.3% [−4.7, 11.4] | 13.3% | 0.35 |
| LOSS(−Z) | 6.8% [−0.3, 14.1] | 10.6% | 0.80 | 4.1% [−3.2, 11.4] | 13.1% | 0.47 |
| LOSS(+Z_H) | 7.3% [0.1, 14.6] | 11.0% | 0.84 | 4.0% [−3.3, 11.2] | 13.8% | 0.46 |
| LOSS(+Z_O) | 7.2% [−0.0, 14.6] | 10.7% | 0.84 | 4.4% [−2.4, 11.6] | 12.0% | 0.51 |
| LOSS(+Z_H+Z_O) | 7.0% [−0.1, 14.1] | 9.8% | 0.82 | 3.7% [−3.2, 10.7] | 12.2% | 0.43 |
| NET-K(−Z) | 7.3% [0.3, 14.5] | 9.7% | 0.84 | 3.8% [−3.7, 11.3] | 13.4% | 0.43 |
| NET-K(+Z_H) | 7.4% [0.3, 14.5] | 9.9% | 0.84 | 3.9% [−3.7, 11.4] | 13.3% | 0.44 |
| NET-K(+Z_O) | 7.9% [0.6, 15.3] | 9.3% | 0.92 | 3.6% [−3.3, 10.8] | 12.7% | 0.42 |
| VOL | 5.5% [−0.5, 11.8] | 9.2% | 0.74 | 3.1% [−2.9, 9.5] | 10.3% | 0.42 |
| LIQ | 8.3% [1.6, 15.1] | 8.2% | 0.98 | 4.1% [−2.9, 11.1] | 13.8% | 0.47 |

Composition term of the Lemma 3 attribution for the changed gates: −1.3 to +1.4 percentage points of
AR; exposure term −11.5 to −11.7 (LightGBM) and −8.0 to −8.2 (ridge); cost term +4.5 to +4.6. Loss
share of executed entries: 0.49–0.50 (LightGBM), 0.50–0.51 (ridge) for every changed gate. Paired
uncertainty of the AR differences between strategies is not computed.

Reading (PI, not reviewed):
- The operating-point saturation of run 1 is removed. With it removed, the point estimates of
  theta_sel for the learned gates move up by roughly 0.3–2.8 bp, and the intervals widen.
- LightGBM base: no learned gate has an interval excluding zero; several intervals now extend beyond
  the 4.96 bp bound, so equivalence is supported only for LOSS(−Z) among the learned gates checked.
- Ridge base: LOSS(−Z), LOSS(+Z_H) and both permuted-Z variants have intervals excluding zero
  (3.9–5.2 bp). The permuted variants are as large as the real ones, so this selection value comes
  from the non-Z features, not from Z.
- psi_H and psi_O: all intervals include zero in both runs; point estimates of psi_H turned positive
  (1.25 / 0.62 bp). No increment from Z is detected; equivalence of psi to zero is not established.
- Deployed: at equal exposure the learned gates and the scaled no-gate benchmark are within about
  one percentage point of AR of each other, far inside the sampling uncertainty.
- Run 2 is a post-hoc revision on the same data as run 1; the comparison of the two runs is
  descriptive and adds a forking path that must be disclosed.


## 9. Checks after discussion round 2 with GPT (2026-11-17; exploratory; PI only, not externally reviewed)

Sources: `experiments/results/pilot/run_fixedcount_dump/` (`paired_contrasts.json`,
`zo_coverage_nominations.json`; gate-only re-run of run 2 with `--dump-decisions --reuse-tuning`,
which refits only the configurations run 2 chose) and the `dAR_vs_*` entries of both `results.json`.
The dump reproduces every theta_sel of run 2 to < 1e-14 bp. All p-values below are unadjusted and
many contrasts were inspected.

### 9.1 Estimand as implemented

Strata: within the day's 30 nominations, liquidity tercile x volatility tercile (data through t-1),
i.e. 9 cells of about 3 names. u_t = sum of rho over submitted orders - sum over cells of
(submitted count in the cell) x (cell mean rho); theta_sel = sum_t u_t / sum_t S_t. The random
comparator is therefore its exact expectation (no Monte-Carlo noise), and theta_sel measures
selection WITHIN cells conditional on the gate's allocation across cells: value from choosing which
liquidity / volatility cell to submit is removed. This removes most of what VOL and LIQ do
(iota 0.29). rho of an unfilled standard order is 0 and stays in the sums. Gate chronology in the
code: deployment year Y is fitted on base out-of-sample rows through Y-2, calibrated on Y-1.

Count-matched UNSTRATIFIED random abstention (u_t against the day mean of all nominations), bp per
order, LightGBM / ridge: SCORE 6.41 [1.29, 11.67] / 3.23 [-1.74, 8.71]; LOSS(-Z) 0.34 [-4.32, 4.98]
/ 4.96 [-0.65, 10.33]; LIQ 6.18 [-1.30, 14.10] / 4.32 [-5.03, 14.62]; VOL -5.55 [-14.44, 2.98] /
0.57 [-11.01, 12.45]; CONF 3.69 [1.53, 5.91] / -0.04 [-3.21, 3.14].

### 9.2 Paired contrasts, fixed-count rule, evaluation period

Per order, bp [95% CI]. V = mean rho of the submitted orders (same daily count for both arms).

| Contrast | LightGBM base | Ridge base |
|---|---|---|
| V[LOSS(-Z)] - V[SCORE] | -6.07 [-11.98, -0.25], p = 0.04 | 1.73 [-5.97, 8.95] |
| V[LOSS(+Z_H)] - V[SCORE] | -4.23 [-10.97, 2.29] | 0.68 [-6.88, 8.12] |
| V[LOSS(+Z_O)] - V[SCORE] | -4.79 [-10.88, 1.15] | 2.86 [-6.43, 11.54] |
| V[LOSS-LR(-Z)] - V[SCORE] | -7.36 [-15.66, 0.96] | -2.37 [-11.17, 6.42] |
| V[NET-K(-Z)] - V[SCORE] | -3.65 [-10.01, 2.05] | -1.55 [-8.86, 6.05] |
| V[NET-K(+Z_O)] - V[SCORE] | -1.40 [-7.17, 4.01] | -1.38 [-9.76, 6.95] |
| theta_sel: LOSS(+Z_H) - LOSS(+permuted Z_H) | 2.82 [0.59, 5.09], p = 0.016 | 1.29 [-1.19, 3.62] |
| theta_sel: LOSS(+Z_O) - LOSS(+permuted Z_O) | 1.95 [-2.15, 6.25] | -0.44 [-4.41, 3.22] |
| V: LOSS(+Z_H) - LOSS(-Z) | 1.84 [-1.38, 4.89] | -1.05 [-6.47, 4.68] |
| V: LOSS(+Z_O) - LOSS(-Z) | 1.28 [-4.47, 7.25] | 1.13 [-5.09, 7.17] |

About 52-59% of a learned gate's submissions are also in SCORE's.

Deployed, annualised return difference in percentage points [95% CI], run 2:

| Gate | vs SCORE, LightGBM | vs SCORE, ridge | vs scaled G0, LightGBM | vs scaled G0, ridge |
|---|---|---|---|---|
| LOSS(-Z) | -1.2 [-2.5, 0.1] | 0.4 [-1.2, 2.0] | -0.3 [-1.4, 0.8] | 0.7 [-0.6, 2.1] |
| LOSS(+Z_H) | -0.8 [-2.1, 0.5] | 0.4 [-1.2, 1.9] | 0.2 [-0.8, 1.2] | 0.6 [-0.4, 1.7] |
| LOSS(+Z_O) | -0.8 [-2.1, 0.4] | 0.7 [-1.2, 2.4] | 0.1 [-1.1, 1.2] | 1.0 [-0.5, 2.5] |
| NET-K(-Z) | -0.7 [-2.0, 0.4] | 0.1 [-1.6, 1.6] | not run | not run |
| SCORE | - | - | 0.9 [-0.2, 2.0] | 0.3 [-0.8, 1.4] |

### 9.3 Variance audit of theta_sel (run 2)

Bootstrap SE (mean block 24) agrees with a Newey-West SE at 24 lags to within about 0.1 bp for
every gate; with no lags the SE is 15-30% smaller. Mean block 6 / 12 / 24 / 48 gives, LightGBM:
SCORE 1.65 / 1.72 / 1.90 / 2.10, LOSS(-Z) 1.57 / 1.49 / 1.49 / 1.47; ridge: SCORE 2.22 / 2.09 /
2.05 / 2.12, LOSS(-Z) 1.84 / 1.85 / 1.82 / 1.89. The ten most influential days carry 4-7% of the
absolute influence; lag-1 autocorrelation of the daily influence series is 0.02-0.33. No sign of an
estimator or bootstrap fault was found.

theta_sel by year, bp (LightGBM base): SCORE 7.3 / 8.1 / 2.5 / 4.3 / -6.5 for 2017..2021;
LOSS(-Z) 3.5 / 3.4 / 2.3 / 0.8 / -6.0; NET-K(-Z) 5.6 / 9.3 / 3.0 / -2.8 / -4.7. Ridge base:
SCORE -0.9 / 7.0 / -0.3 / 10.9 / -4.4; LOSS(-Z) 8.8 / 5.2 / 5.0 / -0.6 / 4.5.

### 9.4 Base predictor in the evaluation period

Daily RankIC of the base score against the 5-day open-to-open return on the candidate sets, mean
over 2017-2021: 0.106 (LightGBM), 0.082 (ridge). By year, LightGBM: 0.125, 0.136, 0.132, 0.093,
0.040; ridge: 0.085, 0.097, 0.102, 0.090, 0.034. Both fall sharply in 2021, the last year before
the sealed hold-out. Mean rho of nominations minus that of all candidates, bp, 2017..2021:
LightGBM 63 / 82 / 51 / 39 / 3; ridge 30 / 46 / 39 / 42 / -10.

### 9.5 Z_O among nominated orders (no outcome read)

Timing by design: an event of trading day s (INS: announcement day rolled forward) is usable from
decision day s + 2. Vendor announcement dates for INS cannot be audited from free data (OA10).
Share of nominated orders with an event in the 20-day window, LightGBM / ridge: any class 33% / 39%
(10-12 of 30 nominations per day), block trade 27% / 29%, dragon-tiger list 4.1% / 7.8%, insider
purchase 3.3% / 3.6%, insider sale 4.5% / 4.3%. In the 1-day window: any class 4.2% / 5.8%
(1.2 / 1.7 nominations per day), dragon-tiger list 0.13% / 0.33%.

### 9.6 Reading (PI, not reviewed)

- A learned second-stage gate is not shown to beat simply keeping the highest base scores. On the
  LightGBM base LOSS(-Z) is 6 bp per order below SCORE (unadjusted p = 0.04) and 1.2 points of AR
  below it; on the ridge base there is no detectable difference.
- Real Z_H beats permuted Z_H on the LightGBM base (2.8 bp, unadjusted p = 0.016), but real Z_H is
  not detectably better than no Z (1.25 bp). One permutation draw per seed; adding permuted columns
  lowers the gate below the no-Z gate, so this contrast does not by itself show information in Z_H.
- The stratification halves SCORE's measured value on the LightGBM base (6.4 unstratified vs 3.3).
- The SE increase of run 2 is not an artefact.
- The base predictor weakens markedly in 2021, and theta_sel of most LightGBM-base gates is negative
  in 2021. A hold-out starting in 2022 may have a weak base predictor; this was not planned for.

### 9.7 Added after discussion round 3 with GPT (2026-11-17)

- Actual stratum sizes among the 30 daily nominations, evaluation period (both bases): 8.8 non-empty
  cells per day on average; cell size 10th / 50th / 90th percentile 2 / 3 / 5, maximum 9; 2.5-2.7% of
  nominated names sit alone in their cell (no choice possible) and 14% are in cells of at most 2.
- Z_O window origin (from `features/zo.py`): window(t, W) = event days s with
  t - lag - W + 1 <= s <= t - lag, lag = 2. The "1-day window" is therefore the single event day
  t - 2, i.e. the window is counted from availability, not from the previous trading day.
- Base chronology as documented in the header of `pilot/strategy.py`: deployment year Y is fitted
  through Y-1 with purging and predicts Y. This was read from the code header, not independently
  audited line by line.
- Accounting identity (exact for a common submitted count): theta_unstratified = theta_sel + A, with
  A the cross-cell allocation term. LightGBM SCORE: 6.41 = 3.25 + 3.16 bp.

# Confirmatory code base: implementation, smoke test and compute estimate

> researcher (sub-agent), 2026-11-17. Task: copy the exploratory pilot code to `experiments/src/confirm/`, add the
> policies and diagnostics of `experiments/PLAN_v0.9_amendment.md` (v0.9.3, DRAFT: §A2, §A3.1, §A4.1, §A4.3,
> §A7, §A8 "Further freeze checks" (c)) and of `reviews/plan_review_5.md` (row 2 and the GPT-only bullets),
> unit-test them, smoke-test on the 100-name list, check reproduction of the pilot smoke, and estimate the
> compute of the full development run. **The full run was not started.**
>
> **Sealed hold-out.** Every run used `--data-cutoff 2021-12-31`; nothing on or after 2022-01-01 was read,
> printed or computed. The new runner refuses a later cut-off unless `--holdout-approved` is given (tested).
> `experiments/src/pilot/` was not modified (only read); `engine/` and `features/` were imported, not edited.
> No download, no package installation, no network access. No command was denied. My processes used at
> most 10 CPU threads (jobs × LightGBM threads ≤ 10, BLAS threads capped by the runner). The machine was
> about two-thirds loaded by other jobs throughout, so every timing below is inflated by contention.
>
> **The smoke numbers are plumbing checks on 100 names and one evaluation year (2021), not results.** They say
> nothing for or against any method. This report quotes counts, residuals, timings and equality checks only;
> no performance number of the smoke runs is quoted or interpreted. Not reviewed by any other model.

## 0. Summary

| Item | Status |
|---|---|
| Code in `experiments/src/confirm/` | items 1–9 of the task done, plus resumable checkpoints, a hold-out guard, a thread cap, a reproduction checker and a compute estimator (§1) |
| Unit tests | **16 / 16 pass** (`tests/test_confirm.py`, synthetic data only) (§3) |
| Smoke run (100 names, fixed count, cut-off 2021-12-31, T = 4, seeds {0, 1}, both bases, all 23 policies, dump, tuning matrix, overlap diagnostic) | **completes** (1,434 s); 144 deployment backtests, reconciliation maxima R2 daily 1.7e-15, cumulative 3.7e-15, naive re-computation 1.8e-14, 0 days over tolerance, 0 unexplained; 0 gate failures, 0 failed scores, 0 zero-submission policies (§2) |
| Overlap identity δ(g,h) = [Σρ(g∖h) − Σρ(h∖g)]/ΣS | **holds**: 26 contrasts (13 per base: P1–P6 and 7 secondary), all with equal total counts; max residual 7.2e-16 (raw units), required ≤ 1e-10 (§2.3) |
| Resume from checkpoints | stages 6–8 reloaded in seconds; all 618,111 submission rows and all nominations **identical** to the uninterrupted run (§2.4) |
| Reproduction of the pilot smoke (`--pilot-compat`: the pilot's methods, window y2, criterion θ_sel, T = 2, seeds {0,1,2}) | every policy reproduces the pilot's submissions **exactly except LOSS-LR(−Z) on the LightGBM base** (173 of 42,390 submitted orders differ); base tuning values, nominations, standard-order ρ, reconciliation maxima identical; ridge base scores differ by ≤ 1.4e-15 (§4) |
| Compute of the full development run | **about 2.3–4.9 days at 10 threads on an otherwise idle machine** (gate stage 51–110 h dominates), **plus about 11 h** if RND keeps 200 repetitions; about 1.0–2.2 days at 24 threads; peak memory about 8–11 GB at 5 jobs (§5) |
| Ambiguities, deviations, open questions | §6, §7 |

## 1. What was implemented

All 11 pilot files were copied to `experiments/src/confirm/` and edited only there; `run_pilot.py` became
`run_confirm.py`. Every change is marked `confirm:` in the code. Line numbers below refer to the code as it
was for the final smoke run.

| # | Task item | Where | What |
|---|---|---|---|
| 1 | Fixed-count gates through Y−1; Y−2 kept as option | `strategy.py:63` `gate_fit_window`; used in `gate_year` `strategy.py:495–511`; `config.py:64` `gate_window`; CLI `--gate-window y1\|y2` | §1.1 |
| 2 | Gate selection by pooled V; T = 30 and five seeds as configuration | `run_confirm.py:394` `criterion_of`, `:400` `fold_stats`, `:410–478` `learn`; `strategy.py:118` `pooled_V`, `:125` `v_parts`; `config.py:65` `gate_criterion`, `:82–83` `n_configs = 30`, `seeds = (0,…,4)`; CLI `--n-configs`, `--seeds`, `--gate-criterion` | per seed V = Σρ/ΣS pooled over all decision days of all tuning years; criterion = mean over seeds; ties go to the earlier trial (as in the pilot) |
| 3 | BASE-V per base class | `strategy.py:182–282` `base_scores(..., want_basev=True)`; policy `strategy.py:585` `basev_subs`; wiring `run_confirm.py:366–392` | §1.2 |
| 4 | NET-U15(−Z) | `strategy.py:497–548` (family `NET-U15` in `gate_year`) | §1.3, with every remaining difference from BASE-V |
| 5 | BASEV-RERANK | `strategy.py:597` `rerank_subs`; wiring `run_confirm.py:385–391` | the BASE-V score of the same seed picks ⌈c·n_t⌉ of the RankIC base's n_t nominations |
| 6 | Z_O* = LHB + BLK for the primary gate | `strategy.py:152` `zo_star_columns`; `run_confirm.py:258`; generic feature-set parser `strategy.py:144`; `design` `strategy.py:377` | primary gate `LOSS(+Z_O*)` (25 of the 41 Z_O columns: 14 LHB, 11 BLK); the full set stays available (`LOSS(+Z_O)`, the INS sensitivity), plus `LOSS(+Z_H+Z_O*)`, `LOSS(+perm Z_O*)`, `NET-K(+Z_O*)` |
| 7 | Tuning log; matrix and curves | trial records in `learn` (`run_confirm.py:425–452`), `base_scores` (`strategy.py:209–238`), TREND / PERF (`run_confirm.py:640–650`); printer `tuning_matrix.py` | per method and trial: configuration; every fold (seed × year) with V numerator, denominator, V, θ_sel, training rows, last training row day, label-known-before day, window; pooled V per seed; the zero-submission flag; wall seconds; deployment fits (rows, last row) and seconds. `tuning_matrix.py` prints the matrix (inputs incl. whether the base rank is an input, model class, loss, rows / years, validation years, criterion, early stopping, budget, compute) and best-after-5/10/20/30/T curves |
| 8 | Decision dump and overlap diagnostic | `run_confirm.py:505` `write_dump_submissions` (after stage 8 and again after stage 9, `:736`); `overlap_diagnostic.py` | `submissions.parquet` (base, seed, method, day, code, ρ, filled, in-nominations, daily count, scale) for every policy and seed, `decision_days.parquet` (includes days with zero submissions), `nominations.parquet`, `base_ic.parquet`, `dump_meta.json`. The diagnostic reports per contrast and base: daily overlap, added / removed counts and mean ρ, by year, and checks the identity to 1e-10 (exit code 1 if it fails) |
| 9 | Edge cases with tests | `strategy.py:83` `select_top`, `:106` `topk_mask_by_day`, `:118` `pooled_V`; failure logging `strategy.py:512–532`; run counters `run_confirm.py:488–502` | §1.4 |
| 10 | No full-sample statistic | — | none introduced: every new criterion uses validation folds of the development period; the diagnostics read the dump post hoc |
| — | Resumability | `run_confirm.py:88` `Checkpoints`; standard orders `:276–293`, each base `:312–315`, each (base, gate) task `:412–477`; CLI `--resume` | §5.3 |
| — | Hold-out guard | `run_confirm.py:938, 984` | exit code 2 for a cut-off on or after 2022-01-01 without `--holdout-approved` |
| — | Thread cap | `run_confirm.py:39–51` | OMP / OpenBLAS / MKL threads = `--threads`, set before numpy is imported and inherited by worker processes |
| — | Reproduction checker | `reproduce_pilot.py` | read-only comparison with `results/pilot/smoke_fixedcount` and `results/pilot/smoke_dump` |
| — | Compute estimator | `estimate_compute.py` | extrapolation from the measured pilot full run, smoke cross-check |

### 1.1 Gate training window and the last usable training row (item 1)

For deployment or tuning year Y with first decision day lo_Y (`gate_fit_window`, `strategy.py:63–80`):

- **y1 (primary, A2.1).** Candidate rows are the base's out-of-sample rows (its top-K_tr = 90 nominations; all
  candidates for NET-U15) of decision days t with (first base deployment day) ≤ t ≤ lo_Y − 2H − 2, i.e.
  12 trading days before Y for H = 5. This is literally the base predictor's purge + embargo rule
  (`train_mask`, `strategy.py:204`: `day ≤ first_day − 2H − 2`) applied at lo_Y. A row is then used only if its
  label is resolved before lo_Y (`labels`, `strategy.py:419`): the standard order was filled; for the O1
  target (LOSS, LOSS-LR) t + H + 1 < lo_Y; for the ρ target (NET-K, NET-U15) the order is not unresolved and
  its **actual** exit day is < lo_Y.
- **How label resolution limits the last row.** Entry is at the open of t + 1 and the planned exit at t + 1 + H;
  the O1 label freezes at t + H + 1, so after the purge it is always known. ρ, however, is known only when the
  order is actually sold, and the engine re-submits sells blocked by suspension or limit-down, so the exit can
  fall after lo_Y even for t ≤ lo_Y − 12; such rows are dropped. **The last usable row is therefore the last
  decision day t ≤ lo_Y − 2H − 2 whose filled order has its label before lo_Y**; its label window
  [t + 1, t + H + 1] ends at least H trading days before Y. In the smoke run (100 names), the last training row
  of every y1 gate is exactly lo_Y − 12 (day index 2909 for Y = 2020, 3152 for Y = 2021) with label-known-before
  = lo_Y; NET-U (threshold) shows 2665 / 2677 for Y = 2020, the y2 window (§2.2).
- **y2 (sensitivity; v0.8 and the pilot).** t ≤ min(last day of Y − 2, lo_{Y−1} − 2H − 2), labels known before
  lo_{Y−1}; the same formula as `pilot/strategy.py:327`.
- Threshold policies (CONF, NET-U, any run with `--gate-rule threshold`) always use y2 (A2.1).
- A fixed-count gate needs no calibration year, so the Y − 1 nominations are no longer scored
  (`strategy.py:524`). Predictions are row-wise, so deployment scores are unaffected.
- Tests: `test_fixed_count_gate_y1` (last row ≤ lo_Y − 12 and inside Y − 1; y2 only through Y − 2),
  `test_labels_respect_known_before` (row-by-row with 5% delayed exits), `test_window_formulae`.

### 1.2 BASE-V (item 3)

`base_scores(..., want_basev=True)` (`strategy.py:182`) tunes the base exactly as the pilot did (same
configuration draws, same training rows `day ≤ first validation day − 2H − 2` from the first feature year, same
validation years `base_tune_years` = 2011, 2012 in the full run, same seeds — all seeds for LightGBM, one for
ridge / elastic net, which are deterministic). **The validation fits are shared with the base**: every trial
and fold's predictions are scored twice — by mean daily RankIC (the base's criterion, unchanged) and by V of the
model's own top ⌈cK⌉ = 15 eligible names per validation day (eligible = candidate with a finite score; ties
by code; `topk_mask_by_day`). For each seed V is pooled over all validation days; the BASE-V criterion is the
mean over seeds (`strategy.py:225–235`). The chosen configuration is deployed with the base's own annual refit
(fit through Y − 1, purged; `deploy`, `strategy.py:244`); if BASE-V picks the same configuration as the RankIC
criterion, the base's (deterministic) fits are reused. The policy submits its own top 15 eligible candidates
on every decision day (`basev_subs`). Because the base tuning years precede the first base deployment year,
standard orders are now also computed for the candidates of the base tuning years (`run_confirm.py:283–292`;
17,368 orders in the smoke), by a separate call, so the pilot range is computed by exactly the pilot's call.
Test: `TestBaseV` recomputes the criterion of every trial by brute force (equal to 1e-12) and checks the chosen
index, a 10-name day and BASEV-RERANK's counts.

### 1.3 NET-U15 (item 4) and every remaining difference from BASE-V

NET-U15(−Z) is the pilot's NET-U(−Z) model with the threshold replaced by a fixed count: each decision day it
submits its own 15 best-predicted eligible candidates (`strategy.py:543–548`), uses the y1 window, and is tuned by
pooled V of its own submissions on the gate tuning years, with the gates' chronology, features and budget.

| Aspect | BASE-V | NET-U15(−Z) |
|---|---|---|
| model class | LightGBM regression (lgbm base) or ridge / elastic net (ridge base) | LightGBM regression for **both** bases |
| training target | within-day rank of the forward 5-day open-to-open return (demeaned), every candidate row with a finite forward return | standard-order net return ρ (costs, synthetic fill, LP exit), **filled** orders only |
| inputs | B0 + R (the −Z set) | the −Z set **plus the base's out-of-sample within-day rank** (switch `netu15_base_rank_input`, default on, as NET-U) |
| training rows | candidates from the first feature year (2009) | candidates from the first base out-of-sample day (2013), the only rows with a base rank |
| validation folds | base tuning years 2011–2012 | gate tuning years 2015–2016 |
| refit schedule | annual from 2013 (base schedule) | annual for 2015–2021 (gate schedule) |
| label rule | label window ends before the target year (purge) | purge plus label known before Y (delayed exits dropped) |
| criterion | pooled V of own top 15 per validation day | the same definition on its own submissions |
| search space | LGBM_SPACE, or LINEAR_SPACE with 8 points (T = 30 means all 8 for ridge) | LGBM_SPACE (30 of 486 points) |
| seeds | lgbm: five; ridge: one (deterministic) | five for both bases |
| dependence on the base | none | the base rank is an input, so NET-U15 differs between the two bases |

In the smoke run the top-90 training population of the gates covers every candidate (at most 82 candidates per
day with 100 names), so NET-U15 and NET-K train on the same rows there; this is a property of the 100-name slice
only.

### 1.4 Edge cases (item 9)

- **Fewer than 15 eligible names on a day.** Every fixed-count policy submits all eligible names (`select_top`).
  SCORE, LOSS*, LOSS-LR, NET-K*, VOL, LIQ and BASEV-RERANK submit ⌈c·n_t⌉ of the n_t nominations (A2.1);
  BASE-V and NET-U15 submit min(15, number of eligible candidates) (A7, "its own 15 best-scored eligible
  names"). The two rules agree whenever a day has at least K = 30 candidates; otherwise counts differ across
  policies and the run counts such days (`days_with_unequal_counts_primary`). There were 0 such days in the
  pilot full run (minimum 201 candidates per day) and in the smoke (minimum 46). **SCORE was changed** from
  the pilot's ⌈cK⌉ to ⌈c·n_t⌉ (identical when n_t = K).
- **Failed score.** A name with a missing or non-finite score is not eligible that day (`failed_score =
  "exclude"`; the alternative `"last"` ranks it after every finite score); counted in `failed_scores` and
  `policy_flags`. A **failed fit** (fewer than 50 usable rows, a single label class, or an exception in fit or
  predict) gives no submissions for that year and is logged in `gate_failures`; these days enter V with zero
  numerator and zero count. (The pilot silently returned empty sets in the first two cases and would have
  crashed in the third; NaN keys would also have broken its sort.)
- **Zero submissions overall.** V = 0 and a flag (`pooled_V`; `V_zero_submission_flag` per trial,
  `zero_submission_policies` per policy, `zero_submissions` in the V estimates, `flag` in the overlap
  diagnostic). See Q3.
- Tests: `test_select_top_basic_ties_failed`, `test_vectorised_selection_matches`,
  `test_netu15_counts_and_fewer_eligible`, `test_failed_fit_is_logged`, `test_pooled_and_zero`,
  `test_unequal_counts_flagged`, `TestBaseV` (10-name day).
- In the smoke run: 0 gate failures, 0 failed scores, 0 zero-submission policies, 0 days with unequal
  counts in the primary family (both bases).

### 1.5 Other changes needed to make the pieces work

- `models.draw_configs` keeps trials in **draw order** (the pilot sorted them by grid index). The set of
  configurations for a given T is unchanged (tested). Order matters for the "best after m trials" curves (the
  first m trials are then a random sample of the space) and for breaking exact ties.
- Standard orders are computed before the base (stage 6), the base after (stage 7); `standard_orders.parquet`
  has a `range` column (`deploy` = the pilot's range, `base_tuning`).
- Permutation draws: Z_O* is permuted within day and class (LHB, BLK), drawn after Z_H and Z_O, so the pilot's
  draws of Z_H and Z_O are unchanged (the reproduction check confirms it).
- E-const-dev and RND are attached to `LOSS(+Z_O*)` instead of `LOSS(+Z_O)`.
- θ_sel of policies that choose from the whole candidate set (NET-U, NET-U15, BASE-V) is computed on their pool
  C_t, as the pilot did for NET-U.
- `results.json` also holds V for every policy and δ for P1–P6 and seven secondary contrasts with a marginal
  stationary bootstrap only; the simultaneous intervals of A4.1 are not implemented here.

## 2. Smoke run

### 2.1 Setting and command

100 names of `experiments/results/pilot/smoke/smoke_codes.txt` (copied to `results/confirm/smoke_codes.txt`), the
pilot's smoke schedule (base fit 2015–2016, base validation 2017, base out-of-sample from 2018, gate tuning year
2020, evaluation year 2021, last decision day 2021-12-10), `--gate-rule fixed_count` (default), window y1,
criterion V, **T = 4, seeds {0, 1}**, RND 2 repetitions, bootstrap 200, 5 jobs × 2 threads. The pilot smoke's
feature panel was copied to `results/confirm/smoke_panel` (not rebuilt; it was built by the same feature code
under the same cut-off).

```
experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/run_confirm.py --data-cutoff 2021-12-31 --smoke \
  --codes-file experiments/results/confirm/smoke_codes.txt --out experiments/results/confirm/smoke \
  --panel-dir experiments/results/confirm/smoke_panel --n-configs 4 --seeds 0,1 --rnd-reps 2 --bootstrap-B 200 \
  --jobs 5 --threads 2 --dump-decisions --keep-awake
experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/overlap_diagnostic.py --dump experiments/results/confirm/smoke
experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/tuning_matrix.py --run experiments/results/confirm/smoke \
  --out experiments/results/confirm/smoke/tuning_matrix.md
```

Two complete smoke runs were made with this command. **Run 1** (`results/confirm/smoke_run1/`, 10:53–11:23,
1,825 s) wrote the decision dump after stage 8 only, i.e. without TREND, PERF, VT and E-const-dev, which are
defined in stage 9; the dump was then extended (`write_dump_submissions`, also called after stage 9) and
**run 2** (`results/confirm/smoke/`, 11:28–11:51, 1,434 s) is the final one. Run 2 reproduces run 1 exactly for
every policy that both dumped (618,111 submission rows identical) and gives identical V and δ estimates (so the
code is deterministic at fixed compute settings). Stage times of run 2 (s): list 0.1, market 13.5, panel 18.0
(existing panel), universe 0.2, features 11.1, standard orders 19.3, base 220.8, gates 944.9, backtests 170.5,
estimands 22.5. RND repetitions are not stored as submissions (as in the pilot; they are regenerated from their
seeds).

### 2.2 Pipeline checks (counts, not outcomes)

- List 100 names, all ready; 3 names have no bars before the cut-off and are excluded at the panel stage (as in the
  pilot); market 3,407 trading days 2008-01-02 … 2021-12-31, 0 load problems; 121,005 candidate feature rows
  (−Z 315, Z_H 8, Z_O 41, Z_O* 25 columns), 0 candidate rows without a feature row; candidates per day
  46 / 72 / 82 (min / median / max), 0 days with fewer than K = 30 candidates; last decision day 2021-12-10.
- Standard orders: 70,952 in the pilot range (identical counts to the pilot smoke: filled 70,528; S3 / S2 / S1
  233 / 130 / 61; unresolved 0) plus 17,368 for the base validation year 2017 (BASE-V).
- Base tuning: 4 trials per base; BASE-V selected the same configuration as the RankIC criterion on the LightGBM
  base (its fits were reused, so BASE-V coincides with SCORE there by construction in this smoke) and a
  different one on the ridge base (deployed separately). This is a statement about which code path ran, not
  about performance.
- Tuning log: 34 tuned (base, method) entries (BASE, BASE-V, 13 gates, TREND, PERF per base), each with every
  trial's configuration, folds, criterion values and seconds; `tuning_matrix.md` printed (the best-after-5 /
  10 / 20 / 30 columns are `n/a` because T = 4 here; the n = T column is filled).
- **Y−1 window in real data:** for every y1 gate the last training row is day index 2909 for the tuning year
  2020 (= first day of 2020 − 12) and 3152 for 2021, label known before 2921 / 3164; training rows 34,231 (LOSS)
  against 16,450 under y2 (NET-U, which keeps y2).
- 0 gate failures, 0 failed scores, 0 policies with zero submissions, 0 days with unequal counts in the primary
  family on either base, 0 nominations days with fewer than K names.
- 144 deployment backtests (88 main, 56 second stage) plus TREND / PERF tuning backtests; reconciliation as in §0;
  every V estimate has 200 / 200 valid bootstrap resamples.
- Peak memory (sampled, main process plus children): 2.57 GB (run 2), 2.75 GB (run 1).

### 2.3 Overlap diagnostic

`overlap_diagnostic.py` on the run-2 dump, evaluation year 2021 (228 decision days × 2 seeds = 456 day-seed
pairs per contrast): 26 contrasts (P1–P6 and S-BASEV, S-NETU15, S-NETU15-SCORE, S-RERANK, S-OBJ, S-HO, S-INS, per
base), all with equal daily counts on every day, so the identity applies to all 26. **Maximum residual of
δ(g,h) − [Σρ(g∖h) − Σρ(h∖g)]/ΣS: 3e-19 (lgbm) and 7e-19 (ridge); maximum daily residual of
N^g_t − N^h_t − (A_t − R_t): 7.2e-16** (raw units, per yuan of slot cash); required ≤ 1e-10: **pass**. The
per-contrast table (overlap share, mean ρ added and removed, by year) is in `smoke/overlap_diagnostic.md` /
`.json`; its numbers are smoke plumbing on 100 names and one year and are not interpreted here.

### 2.4 Resume

Checkpoints of run 1 (29 files, 21 MB) were copied to `results/confirm/smoke_resume/` and the same command was
run there with `--resume --stop-after-gates`. Standard orders, both bases and all 26 gate tasks were loaded
from the checkpoints (stages 6–8 took 28 s instead of 1,537 s); the resulting `submissions.parquet`
(618,111 rows) and `nominations.parquet` are identical to those of the uninterrupted run 1.

## 3. Unit tests

`experiments/.venv/Scripts/python.exe -X utf8 -m unittest experiments/src/confirm/tests/test_confirm.py -v`:
**16 / 16 pass** (about 6 s; synthetic markets only, no raw file is read). Covered: fixed-count selection (ties
by code, fewer eligible than k, failed scores excluded / last, empty input); vectorised selection equals the
reference on 40 days with ties and NaN; pooled V, zero-submission convention, pooled ≠ mean of annual ratios;
`v_parts`; window formulae y1 / y2 and Y − 2 outside the data; the label-known rule row by row; a real y1
gate fit (LOSS-LR) — last row, label day, counts per day, a 10-name day — and the y2 sensitivity; NET-U15
counts and a 10-name day (LightGBM); a failed fit is logged and submits nothing; feature-set parsing, Z_O*
columns, column order, permuted Z_O* columns are a within-day rearrangement; BASE-V criterion recomputed by
brute force, chosen index, BASE-V and BASEV-RERANK counts; the overlap identity with equal counts (residual
< 1e-14 raw, also with a zero-submission day, and δ equal to a brute-force value) and its flagging with
unequal counts; trial order and set of `draw_configs` against the pilot's; tuning curves; the hold-out
guard. Not covered by unit tests: the end-to-end runner (covered by the smoke runs).

## 4. Reproduction of the pilot smoke

`--pilot-compat` restores the pilot's method list, window y2 and criterion θ_sel (and the pilot's E-const-dev /
RND lists); with the pilot smoke's budget (T = 2, seeds {0, 1, 2}, RND 2, bootstrap 200) the configuration is
that of `results/pilot/smoke_fixedcount` (pilot `--gate-rule fixed_count`). Compute settings differ: 2 jobs ×
4 LightGBM threads (as the pilot's 4) and BLAS capped at 4 threads (the pilot ran with the OpenBLAS default,
32). Output `results/confirm/smoke_pilotcompat/`; comparison `reproduce_pilot.py` → `reproduction_check.json`.

| Compared | Result |
|---|---|
| list, readiness, market (3,407 days), universe, feature rows (121,005) | identical (the only new key is the Z_O* column count) |
| standard orders, pilot range (70,952) | ρ, fill, reason, O1, exit, unresolved identical; only the internal lot counter differs (it depends on how names are chunked across 2 instead of 6 processes) |
| base tuning: configurations, RankIC per trial, chosen configuration | identical (lgbm and ridge; max abs RankIC difference 0) |
| nominations (84,780 rows: codes, positions, ρ, fill, cell) | identical; base scores identical on lgbm, differ by at most 1.4e-15 on ridge (41,607 rows; BLAS thread count) |
| gate tuning: configuration sets, chosen configurations | identical for all 26 tuned tasks (22 learned gates, TREND, PERF); criterion values identical except LOSS-LR(−Z) (max abs 2.7e-5 lgbm, 6.1e-5 ridge, in θ_sel units; the chosen configuration is the same) |
| submissions of G0, SCORE, CONF, VOL, LIQ, NET-U and of every LOSS / NET-K variant incl. permuted Z | **identical** |
| submissions of **LOSS-LR(−Z), LightGBM base** | **173 of 42,390 differ** (seeds 0 / 1 / 2: 98 / 90 / 158 rows over 150 days); ridge base identical |
| θ_sel, deployed outcomes, ψ, cards, Lemma 3 attribution | identical for every method except LOSS-LR(−Z) on the LightGBM base |
| reconciliation maxima (192 backtests) | identical to the printed digit (R2 daily 1.8e-15, naive 2.0e-14, 0 unexplained) |

**Why LOSS-LR differs (most likely cause, not proven).** LOSS-LR is a scikit-learn logistic regression (lbfgs,
max_iter 300) whose arithmetic goes through BLAS; the pilot used 32 BLAS threads, this run 4. The ridge base,
also BLAS-based, shows the same kind of last-digit differences (≤ 1.4e-15). On synthetic data the same
logistic fit differs by about 1e-12 between 1 and 4 BLAS threads. Why the effect on the selected sets is as
large as 0.4% (near-ties, or non-convergence on the real design) was not established. **The changed policies of
this code base (y1 window, criterion V, new policies) are by construction not comparable with the pilot and were
not compared.** Recommendation (Q6): fix the BLAS thread count in the frozen configuration and log the
convergence of every logistic fit.

## 5. Compute estimate for the full development run

Full run = 1,000-name list (969 with data), top-300 screen, base tuning 2011–2012, gate tuning 2015–2016,
evaluation 2017–2021, T = 30, five seeds, both bases, the 23 policies of `config.CONFIRM_METHODS`, RND 200,
bootstrap 10,000. Basis: the **measured** full pilot run (`results/pilot/run_fixedcount`, T = 4, 3 seeds, 6 jobs ×
4 threads: base 3,485 s, gates 6,445 s, backtests 1,062 s, estimands 262 s), scaled by `estimate_compute.py`
(output `results/confirm/compute_estimate.json`). Everything below is an ESTIMATE.

| Stage | Pilot full (measured) | Full confirm run, 10 threads | Basis of the scaling |
|---|---|---|---|
| market, panel (exists), features | 80 s | ~2 min | unchanged |
| standard orders | 57 s | ~1–2 min | + the base tuning years (11 instead of 9 years) |
| base LightGBM: tuning | 209 s (24 fits) | 0.9–1.1 h at 4 threads | 300 fits (30 × 2 years × 5 seeds) × 8.7 s × configuration-cost factor 1.2–1.55 |
| base LightGBM: deployment | 2,730 s (3 seeds) | 1.3 h (base) + 1.3–2.0 h (BASE-V, only if it picks another configuration) | 5 seeds × 910 s per seed |
| base ridge / enet | 495 s | 0.2–0.6 h | all 8 points of LINEAR_SPACE; an elastic-net deployment can be several times a ridge one |
| **gates** | 6,445 s × 24 threads | **51–110 h** (16 threads: 32–69 h; 24 threads: 21–46 h) | fits per method 39 → 325; methods 22 → 26 with the all-candidate NET-U / NET-U15 weighted 295 / 90; y1 windows ×1.5 rows; configuration-cost factor 1.2–1.55; the pilot's 24 threads assumed 60–100% used |
| backtests without RND | — | ~0.6 h | 460 runs × 24 process-seconds / 5 processes |
| RND, 200 repetitions | — | **~11 h** | 8,000 runs (2 bases × 5 seeds × 4 gates × 200) |
| estimands, B = 10,000 | 262 s | ~0.4 h | bootstrap ×5 |
| **total** | 3.2 h | **about 55–117 h (2.3–4.9 days) + 11 h for RND-200** | 24 threads: about 24–53 h + 4.5 h |

**Cross-check with the smoke.** The smoke gate stage took 945–1,213 s (runs 2 / 1) at 10 threads for 26 tasks of
10 fits on about 34,000 training rows; scaling by fits (×32.5) and rows (×1.6 for the top-90 gates, ×5.2 for
NET-U / NET-U15) gives about 18–24 h of gate wall time, well below the pilot-based 51–110 h. Small fits are dominated by
fixed overheads, so I take the pilot-based range as the planning figure and the smoke figure as an
optimistic bound. Both were measured on a shared machine: the pilot-compatibility smoke took 3,438 s against
the pilot smoke's 464 s for the same work with a third of the threads, i.e. roughly 2.5× slowdown from
contention. If the machine stays as loaded as today, the figures above are low.

**Memory.** Measured (sampled every ~15 s, main process and all children): smoke peak 2.57–2.75 GB total (main
process 2.0 GB during the gate stage, 7 processes during backtests). For the full run: candidate feature matrix
920,940 rows × 364 columns float32 = 1.34 GB (transiently doubled at the rank transform), derived arrays
~0.2 GB, standard-order dictionary (~780,000 orders) ~0.4 GB, base and BASE-V scores ~0.3 GB, permutation caches
(3 groups × 10 base-seed contexts × ~200,000 rows) ~1.5–2 GB, five concurrent gate training matrices 1–3 GB
(NET-U / NET-U15 deployment fits up to ~0.9 GB each), backtest workers ~0.5 GB each. **Estimated peak 8–11 GB at
5 jobs.** Free memory at the time of writing was about 9 GB, so the run should not overlap other large jobs,
or use 4 jobs.

### 5.3 Making it resumable and keeping the machine awake

Implemented (`--resume`, tested in §2.4): after standard orders, after each base (with BASE-V), and after each
of the 26 (base, gate) tuning tasks a checkpoint is written atomically (`.tmp` then rename) under
`<out>/checkpoints/`, keyed by the configuration hash without compute settings **and the code hash**, so a
checkpoint from other code or another configuration is ignored. After an interruption the same command with
`--resume` redoes only unfinished units; at most one in-flight gate task per worker is lost (up to 4–8 h for
NET-U-type tasks in the full run). Proposed in addition (not implemented): (i) checkpoint inside a gate task
per trial, so a lost unit costs at most one trial; (ii) checkpoint the backtests in batches (the RND-200 block
is 11 h); (iii) split the run into one process per base, each with 5 threads, which halves the serial base
stage and isolates failures; (iv) run the base LightGBM tuning folds in parallel threads (the stage is serial
now). **Sleep:** `--keep-awake` calls `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)` for the life
of the process (prevents idle sleep, not lid-close, hibernation policies or Windows Update restarts). The user
should additionally set AC sleep to "never" for the duration (`powercfg /change standby-timeout-ac 0`, and
`hibernate-timeout-ac 0`), keep the machine on mains power, and pause Windows Update restarts; I did not run
these commands (they change system settings). Recommended launch (background, after the user's go-ahead):

```
experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/run_confirm.py --data-cutoff 2021-12-31 \
  --out experiments/results/confirm/run --panel-dir experiments/data/derived/feature_panel \
  --jobs 5 --threads 2 --dump-decisions --keep-awake --resume > experiments/results/confirm/run_stdout.log 2>&1
```

## 6. Deviations from the amendment and readings of ambiguous text

| # | Amendment text | Reading taken (or deviation) | Why |
|---|---|---|---|
| R1 | A2.1 count ⌈c·n_t⌉ (gates); A7 "its own ⌈c·K⌉ = 15 best-scored eligible names" (BASE-V); task: fewer than 15 eligible → submit all | gates, SCORE, BASEV-RERANK: ⌈c·n_t⌉ of the n_t nominations; BASE-V, NET-U15: min(15, eligible) | literal reading of each sentence; they agree whenever ≥ 30 candidates (always so far). Alternative: one rule ⌈c·min(K, eligible)⌉ for all — PI ruling (Q1) |
| R2 | A2.1 "SCORE is unchanged and is the fixed-count rule applied to the base score" | SCORE now ⌈c·n_t⌉ (pilot: ⌈cK⌉) | the two sentences conflict when n_t < K; identical otherwise |
| R3 | A2.1 "labels known before the first decision day of Y (purge and embargo H + 1, as for the base)" | both: the base's `day ≤ lo_Y − 2H − 2` and the label-known rule (actual exit < lo_Y) | the text names both; the label rule only bites on delayed exits |
| R4 | A2.2 "mean over the tuning years and seeds of V" vs "pooled over all decision days of the tuning years, mean of that over seeds" | the second (pooled per seed, then mean over seeds) | the amendment says the second replaces the first; PLACEHOLDER there |
| R5 | A7 BASE-V "validation folds" | the base's validation years (2011–2012), with its training windows; the trial configurations and fits are shared with the RankIC base | "identical to the base in everything except the criterion" |
| R6 | A7 "five seeds" for BASE-V on the ridge base | one fit (ridge / elastic net are deterministic; the pilot did the same for the base) | seeds have no effect |
| R7 | review row 2: NET-U15 "same features" | keeps NET-U's inputs, including the base rank (switchable) | "existing NET-U"; the difference to BASE-V is listed in §1.3 |
| R8 | BASEV-RERANK seed pairing | BASE-V of seed s re-ranks the nominations of base seed s | the natural pairing; seed averaging as elsewhere |
| R9 | failed score | excluded from eligibility (option: rank last); failed fit → no submissions that year, logged | consistent with the base's nominations, which also exclude unscored names; a fallback to SCORE would pull contrasts towards zero |
| R10 | zero submissions overall | V = 0 with a flag, as the task specifies | see Q3 |
| R11 | A7 tuning curves "best after 5, 10, 20, 30 trials" | trials in random-draw order (pilot: grid order) | otherwise the first trials are not a random sample |
| R12 | A4.3 item 6 permuted-Z controls "refitted with the configuration chosen for the real group" | **deviation: not implemented**; `LOSS(+perm Z_H)` and `LOSS(+perm Z_O*)` are tuned like every other gate (as in the pilot), one draw per seed | not in this task's list; implementing it removes 4 of 26 tuning tasks (~15% of the gate stage) |
| R13 | secondary policies not in this task | **not implemented**: the "-thr" versions of LOSS(−Z / +Z_H / +Z_O) (they need a per-method rule within one run), the ridge score-plus-controls re-ranker, 20 permutation draws and the Gaussian noise control, the K / c sensitivities, simultaneous intervals, event decomposition | outside items 1–10 |
| R14 | E-const-dev and RND | attached to LOSS(+Z_O*) instead of LOSS(+Z_O) | primary Z_O gate |
| R15 | dump "for all policies" | after stage 9 the dump contains every policy, including TREND, PERF, VT and E-const-dev (with their scale); RND repetitions are not stored (as in the pilot; regenerated from their seeds) | the first smoke run dumped only the stage-8 policies; fixed and rerun (§2.1) |

## 7. Open questions for the PI

- **Q1 (count rule).** Keep R1 (two rules that coincide when ≥ 30 candidates), or one rule ⌈c·min(K, eligible)⌉ for
  every fixed-count policy? Matters only if a day ever has fewer than 30 candidates.
- **Q2 (compute).** 2.3–4.9 days at 10 threads (+11 h for RND-200). Options: (a) more threads when the machine is
  free (24 threads: 1.0–2.2 days); (b) implement R12 (−15% of gates); (c) RND with fewer repetitions or as a
  separate later job (RND does not enter P1–P6); (d) a short calibration run of one full-size gate task
  (e.g. lgbm LOSS(−Z) and NET-U15, T = 2, one seed, ~1–2 h) to narrow the 51–110 h gate range before
  committing. I recommend (d) then (b) and (c).
- **Q3 (zero submissions).** With V = 0 for a configuration that submits nothing, such a configuration can win the
  tuning over configurations with negative V. With the fixed-count rule this only happens if every fit of a
  configuration fails. I suggest criterion = −∞ for a configuration with any failed fit or zero submissions
  (the V = 0 convention kept for reporting).
- **Q4 (BASE-V folds).** Confirm R5 (base validation years 2011–2012) rather than the gate tuning years. Note the
  selection-chronology item A8 (a): base and BASE-V hyperparameters are selected on 2011–2012 outcomes, gate
  training rows start in 2013, so no gate row was used to select the base configuration.
- **Q5 (NET-U15 inputs).** Keep the base rank as an input (R7)? It makes NET-U15 partly two-stage; without it,
  NET-U15 differs from BASE-V of the LightGBM class only in target, training rows, folds and label rule.
- **Q6 (numerical reproducibility).** Fix BLAS threads (and LightGBM threads) as part of the frozen configuration
  — both are recorded in the run manifest now — and add a convergence log for the logistic gate.
- **Q7.** `confirm/cutoff_invariance.py`, `paired_contrasts.py` and `zo_coverage.py` are unchanged copies of the
  pilot tools (they still describe pilot paths); the cut-off invariance test for the new code paths is to be
  rerun on the frozen code, as instructed, after it is adapted to `run_confirm.py`.

## 8. Files

| Path | Content |
|---|---|
| `experiments/src/confirm/` | code (`run_confirm.py`, `strategy.py`, `config.py`, `models.py`, `overlap_diagnostic.py`, `tuning_matrix.py`, `reproduce_pilot.py`, `estimate_compute.py`, `tests/test_confirm.py`, and the unchanged copies) |
| `experiments/results/confirm/smoke/` | final smoke run: `results.json`, `run_manifest.json`, `standard_orders.parquet`, dump (`nominations`, `submissions`, `decision_days`, `base_ic` parquet, `dump_meta.json`), `overlap_diagnostic.json` / `.md`, `tuning_matrix.md`, `checkpoints/`, `logs/run.log` |
| `experiments/results/confirm/smoke_run1/` | first smoke run (stage-8 dump only), kept as the record |
| `experiments/results/confirm/smoke_resume/` | resume test (stop after gates) |
| `experiments/results/confirm/smoke_pilotcompat/` | reproduction run and `reproduction_check.json` |
| `experiments/results/confirm/compute_estimate.json` | output of `estimate_compute.py` |
| `experiments/results/confirm/*_mem.csv`, `*_stdout.log` | memory samples, raw output |
| `experiments/results/confirm/smoke_panel/` | copy of the pilot smoke feature panel |


---

## Round 2 (2026-11-17, afternoon): PI rulings, chronology-audit fixes, cut-off invariance, calibration

> Same hard rules as round 1: every run at `--data-cutoff 2021-12-31`; hold-out sealed (nothing on or after
> 2022-01-01 read, printed or computed); `pilot/`, `engine/`, `features/` not edited; no install, no network;
> no command denied; at most 10 threads (the machine was 67–94% loaded by other jobs; all timings are
> inflated). Smoke numbers are plumbing on 100 names and one year; none is quoted or interpreted. Not
> reviewed by another model. The full development run was **not** started.

### R2.0 Summary

| Item | Result |
|---|---|
| PI rulings Q1, Q3, Q4, Q5, Q6, permutation control, -thr | all implemented (R2.1) |
| Audit fixes D1, D2, D4, D6, D7, D8 | implemented on the confirm side (R2.2); D8 by wrapping the engine's reader from `confirm/data.py`; nothing inside `engine/` or `features/` was edited |
| **New finding (pilot defect)** | **the pilot's base predictor was trained on ALL 364 feature columns, including the 8 Z_H and 41 Z_O columns** (`pilot/run_pilot.py:205–209` builds the frame from `-Z + Z_H + Z_O`; `pilot/strategy.py:91, 111` fit on `fr.X`), not on the B0 + R (−Z) set of A7. The pilot's "base(−Z)" nominations and everything downstream of them (SCORE, the pilot P1–P4 numbers, the "Z adds to the gate" contrasts) were produced by a base that already used Z. The prefreeze audit does not list this. Fixed in confirm (`config.base_features = "-Z"`, 315 columns); `--pilot-compat` keeps `"all"` to reproduce the pilot |
| Unit tests | **28 / 28 pass** (16 → 28) |
| Round-2 smoke (100 names, T = 4, seeds {0,1}, 2 follow-up draws) | completes in 1,536 s; 148 backtests; reconciliation R2 daily 1.9e-15, naive 2.7e-14, 0 unexplained; 0 gate failures, 0 failed scores, 0 unequal-count days; overlap identity holds on 26 contrasts, max residual 4.4e-16 |
| `--tune-only` and `--load-tuning` | tune-only archive = archive of the normal run, all 37 entries identical (σ* bit-exact); a run loading the archive (SHA verified) does no tuning fit and reproduces the normal run **exactly** (1,186,133 submission rows, nominations, decision days, base IC, every estimate, reconciliation); 0 unused archive entries |
| **Cut-off invariance (new code)** | **pass**: real tree, tree A (post-cut-off data deleted), tree B (post-cut-off garbage): results.json (canonical), standard orders, all four dump tables, the archive's chosen configurations and 97 / 97 feature files identical (R2.4) |
| LOSS-LR discrepancy | the pilot's thread setting (OpenBLAS default, 32 threads) **could not be tested** within the 10-thread limit. At BLAS 1 / 4 / 8 threads the LOSS-LR(−Z) submissions differ from each other by 162–203 of 42,390 orders and from the pilot by 173–193, with every logistic fit converged: the selection is thread-count sensitive, so the round-1 difference is consistent with the thread setting; not proven (R2.5) |
| Calibration (full population, T = 2, one seed) | completed in 5,146 s (stages 1–8, lgbm base, G0, SCORE, LOSS(−Z), NET-U(−Z), NET-U15, BASE-V); 969 names, 920,940 candidate rows; full feature panel rebuilt under D2 (1,060 s, 6.5 GB, reusable by the full run); main-process peak 6.5 GB (R2.6) |
| Narrowed compute estimate | **10 threads: about 52–69 h (2.2–2.9 days) without RND-200, 63–80 h with it; 24 threads: about 23–31 h, 28–35 h with RND-200.** The A4.3 item 6 follow-up (20 + 20 draws × 5 seeds × 2 groups × 2 bases) is about 22 h of this at 10 threads. Peak memory about 8–10 GB at 10 threads, 10–12 GB at 24 threads (R2.7) |

### R2.1 PI rulings

| Ruling | Implementation (file:line) |
|---|---|
| **Q1** one count rule ⌈c·min(K, eligible)⌉ | `strategy.py:83` `count_for` (rounds c·n to 9 decimals before the ceiling: the pilot's `math.ceil(c·n)` gives 4 for c = 0.3, n = 10, which would have affected the c-sensitivities of A4.3 item 8); `:115` `select_fixed`; `:124` `topk_mask_by_day`; used by SCORE, VOL, LIQ, every fixed-count gate (`gate_year`, `strategy.py:628`), BASE-V and NET-U15 (`basev_subs`, `:761`) and BASEV-RERANK (`:774`). Eligible = names with a finite score. Tests `test_count_for`, `test_select_fixed_counts_eligible`; BASE-V on a 10-name day now submits 5 |
| **Q3** criterion −∞ for any failed fit or zero submissions | gates `run_confirm.py:536` (failed-fit flag `fit_info["failed"]`; zero counted submissions in any seed); base / BASE-V / NET-U15 in `annual_model` (`strategy.py:230`, V criterion); the reporting value (V = 0 with flag) is kept as `criterion_V_reported` |
| **Q4** validation years 2011–2012 for base, BASE-V; NET-U15 too | NET-U15's net-return labels exist for 2011–2012: standard orders are now computed for every candidate day from the first feature year (2009) (`run_confirm.py:294`), so NET-U15 is validated on exactly the base validation years (smoke: 2017), with training rows from 2009, the base's purge / embargo and "label known before the validation year". No substitute was needed |
| **Q5** NET-U15 without base score or rank | `strategy.py:383` `netu15_scores`: LightGBM regression of ρ on the −Z set only (315 columns), all candidates, filled orders, tuned by pooled V of its own fixed-count names (D4, Q3), refitted annually for the gate-tuning and evaluation years. As it no longer depends on the base, **one model serves both bases** (the same submissions appear under both). Test `test_netu15_end_to_end` |
| **Q6** fixed thread counts; logistic convergence log | `config.lgbm_threads = 2`, `blas_threads = 2` (in the configuration and checkpoint hashes); BLAS forced before numpy import (`run_confirm.py:39–53`); `threadpool_limits` applied and the pools recorded in the manifest (`:1328`); `--threads` / `--blas-threads` only for reproduction tests, and recorded. Convergence: `strategy.py:214` records n_iter / max_iter of every logistic fit; `results.json["logit_convergence"]` (round-2 smoke: 20 fits, **2 not converged** at max_iter = 300) |
| **Permutation control, A4.3 item 6** | `run_confirm.py:574–612` (`follow_up`): for G in `perm_groups` = (Z_H, Z_O*), `perm_draws` (20; smoke 2) draws per seed of the LOSS gate with G permuted within day and class on the top-K_tr rows (`+perm G`) and with G replaced by as many N(0,1) columns (`+noise G`), each refitted on the evaluation years at the configuration chosen for LOSS(+G); no tuning. Random streams keyed by (seed, group, kind, draw) (`_draw_matrix`, `strategy.py:519`), so independent of scheduling; caches dropped after each draw. Summary per base in `estimates[base]["follow_up_A4_3_item6"]`: δ(real, −Z) and, over draws, δ(draw, −Z) and δ(real, draw) (mean, sd, min, max). The pilot's tuned `+perm` gates remain only under `--pilot-compat`. Draws are not backtested (V and δ only). Test `test_follow_up_draws` |
| **-thr secondary policies** | `LOSS(-Z)-thr`, `LOSS(+Z_H)-thr`, `LOSS(+Z_O)-thr` in `CONFIRM_METHODS`; `gate_year` (`strategy.py:680`) uses the pilot's threshold path (calibration on Y−1, window through Y−2) and θ_sel tuning as in the pilot, with D4 and Q3 applied to the criterion. Test `test_thr_policy_uses_threshold_and_y2` |

### R2.2 Chronology-audit fixes

| Defect | Implementation | Test / evidence |
|---|---|---|
| **D1** tune once, archive | `--tune-only` (`run_confirm.py:884`): every search (base, BASE-V, NET-U15, gates incl. -thr, TREND, PERF, VT σ*) at cut-off 2021-12-31, then stop. Every tuning run writes `tuning_archive.json` (chosen index **and** the full configuration list of each unit, σ* per base and seed, tuning spec and hash, code hash) plus a `.sha256` side file (`write_archive`, `:931`). `--load-tuning` (`load_archive` `:956`, `arch_get` `:983`) verifies the SHA (side file and optional `--tuning-sha`), archive cut-off = 2021-12-31, identical tuning spec (configuration without cut-off, paths and worker counts) and code hash, and completeness (`required_archive_keys` `:915`); each unit then asserts that its configuration list equals the run's draws; no tuning fit is run (base / NET-U15 `fixed=`, gates, TREND / PERF, σ*). A cut-off after 2021-12-31 is refused without `--load-tuning` (`:1271`), in addition to the hold-out guard | `test_roundtrip_and_checks` (tampering, wrong SHA, other spec, missing unit, changed list → refused; σ* float exact), `test_incomplete_archive_refused`, `test_guards`; smoke: tune-only entries = normal-run entries (37 / 37); loaded run = normal run exactly. The two archive SHAs differ only through the `created` timestamp |
| **D4** criteria use resolved orders only | gates `fold_stats` (`run_confirm.py:449`): for tuning year v only unfilled orders and orders not unresolved with exit < first decision day of v + 1 enter V and θ_sel (the θ_sel pool is filtered alike); base / BASE-V / NET-U15 likewise (`resolved_mask`, `strategy.py:139`). Dropped orders counted per fold and trial (`dropped_unresolved*`) | smoke: ~75 of ~3,600 submitted orders per (seed, year) fold dropped (the last ~5 decision days of the year); `TestBaseV` and `test_netu15_end_to_end` check the criterion against a brute-force D4 computation. The base's RankIC criterion is unchanged (labels of the last H days of 2012 reach into 2013 — the overlap stated by the audit) |
| **D2** panel provenance | `data.py:300` `build_panel_checked`: a panel is reused only if `confirm_provenance.json` records the same data cut-off, raw-tree identity (hash of every raw file the run may open), feature-code hash (`features/` and `engine/` sources, LHB map) and name list; resumed if it matches but is incomplete; otherwise every file is rebuilt. The library still overwrites its own `panel_meta.json` (library behaviour, not edited) | `test_panel_provenance`; smoke: the copied pilot panel was rebuilt, then reused; tree runs rebuilt into their own directories; the full panel was rebuilt for the calibration (`experiments/data/derived/feature_panel_confirm`, reusable by the full run) |
| **D6** fixed threads | as Q6 | manifest `blas_pools`, `lgbm_threads` |
| **D7** frozen population, raw hashes | `data.py:219` `frozen_population` (the SHA-checked list or the smoke codes file; no mtime, no fetch manifest); `raw_identity` (`data.py:273`) hashes every raw file at the **start** of the run; the manifest records them (`raw_files_sha256`, `raw_identity`) | 861 files in the smoke |
| **D8** listing dates | `data.py:232` `install_listing_cut` wraps `engine.io_baostock._read_parquet` from the confirm side, so that `bs_stock_basic.parquet` has every ipoDate / outDate after the cut-off blanked inside the read call, before engine code receives the table (`listing_reads_blanked` in the manifest). `features.store.RawStore.stock_basic` already blanks inside its own read (panel workers); unchanged. Limitation: the values still pass through memory inside the reader; only a cut snapshot shipped with the frozen raw tree avoids that | `test_listing_cut_wrapper` |

Other round-2 changes: base, BASE-V and NET-U15 share one tuned-model routine, `annual_model` (`strategy.py:230`),
whose folds and deployment fits run in a thread pool of `base_workers` (= 2); results do not depend on it (fixed
threads per fit), and `n_jobs` changes no number (the cut-off runs used 2 jobs, the reference 5, all identical). The
cut-off test (`cutoff_invariance.py:159, 190`) strips wall times recursively, ignores the internal lot id and compares
the dump and the archive. `tuning_matrix.py` knows NET-U15 and -thr.

### R2.3 Unit tests

`experiments/.venv/Scripts/python.exe -X utf8 -m unittest experiments/src/confirm/tests/test_confirm.py`: **28 / 28 pass**
(about 9 s; synthetic data only). New: count rule and floating-point ceiling, eligible-based counts, D4 resolved mask,
brute-force D4 criteria for BASE-V and NET-U15, NET-U15 training rows / no base input / deployment, load-mode base equals
tuned base, logistic convergence log, failed-fit flag, -thr path, method parsing, follow-up draws (within-day
permutation, independence and reproducibility of draws, noise columns), archive round trip and every refusal,
incomplete archive, hold-out and tune-only guards, listing wrapper, panel provenance.

### R2.4 Cut-off invariance of the new code

Trees built by `confirm/cutoff_invariance.py build` into the session scratchpad `ci_trees/` (tree A: 856 files cut at
2021-12-31; tree B: tree A plus 114,338 random bar rows after the cut-off, random index / calendar / event rows, 167
later Z_O files of which half are non-parquet bytes, random later delisting dates). The auditor's trees were neither
used nor modified (they test perturbations inside the development period, a different question). Configuration: the
100-name smoke with the fixed-count rule, Y−1 window, Z_O*, BASE-V, NET-U15, BASEV-RERANK, -thr, follow-up draws,
TREND, PERF, VT, E-const-dev, RND; T = 4, seeds {0,1}. Runs `smoke_r2` (real tree, 5 jobs), `ci_run_A`, `ci_run_B`
(2 jobs each, panels built from their own trees). Report `results/confirm/cutoff_invariance_r2.json`:

| Compared | Result |
|---|---|
| results.json (wall times, paths, provenance actions, archive path removed) | identical (3 / 3) |
| standard orders (without lot id) | identical |
| nominations, submissions (1,186,133 rows), decision days, base IC | identical |
| archived chosen configurations incl. σ* | identical |
| feature files | 97 / 97 identical |
| **verdict** | **pass** |

Not covered (as in the pilot test): later vendor revisions of pre-cut-off rows; perturbations inside the development
period (the auditor's test, not rerun on the new code); the full population.

### R2.5 LOSS-LR thread test

`--pilot-compat`, lgbm base, methods G0, SCORE, LOSS-LR(−Z), T = 2, seeds {0,1,2}, LightGBM 4 threads (as the pilot),
stop after gates; runs `lossr_blas1`, `lossr_blas4`, `lossr_blas8`. LOSS-LR(−Z) submitted orders that differ (of 42,390):
BLAS 1–4: 165, 1–8: 203, 4–8: 162; against the pilot: 179 / 173 / 193. The round-2 BLAS-4 run equals the round-1
compatibility run exactly (0), and SCORE and G0 equal the pilot exactly. Every logistic fit converged (n_iter 166–184
< 300); the iteration count itself changes with the thread count. The pilot's own setting (32 BLAS threads) exceeds the
10-thread limit and was not run, so "disappears with the pilot's setting" is untested.

### R2.6 Calibration run (full size)

Command (stop after the gate stage; no backtests):

```
experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/run_confirm.py --data-cutoff 2021-12-31 \
  --out experiments/results/confirm/calibration --panel-dir experiments/data/derived/feature_panel_confirm \
  --n-configs 2 --seeds 0 --bases lgbm --methods "G0,SCORE,LOSS(-Z),NET-U(-Z),NET-U15(-Z),BASE-V" --perm-draws 0 \
  --jobs 5 --stop-after-gates --keep-awake
```

Measured (LightGBM 2 threads per fit, 2 base workers; the machine was ~94% loaded by another job at the start and
lightly loaded later):

| Stage / fit | Seconds | Rows |
|---|---|---|
| raw hashing (3,803 files) + list + market | ~110 | — |
| feature panel rebuild (provenance mismatch: none existed), 5 jobs | 1,060 | 969 names |
| features (rank transform) | 92 | 920,940 rows × 364 columns |
| standard orders (deploy range 635,728 + 2009–2012 range 285,212) | 136 | — |
| base LightGBM tuning fit, 2011 / 2012 fold (n_estimators 200 / 100) | 82 / 111 and 33 / 45 | 135,084 / 204,441 |
| base LightGBM deployment fits 2013 … 2021 (chosen configuration) | 148 … 362 per year; 2,360 in total | 274,193 … 836,246 |
| BASE-V | chose the same configuration: fits reused, 0 s | — |
| NET-U15 tuning fits (same configurations) | 81 / 112 and 34 / 45 | 137,271 / 207,839 |
| NET-U15 deployment 2015–2021 | 1,977 in total | — |
| LOSS(−Z) gate: one trial (2 folds, y1 window) | 78 (n_est 200), 36 (n_est 100) | 42,391 + 64,145 |
| LOSS(−Z) deployment 2017–2021 | 178 in total | 86,058 … 173,614 |
| NET-U(−Z) gate: one trial | 138, 72 | 66,395 + 137,253 |
| NET-U(−Z) deployment 2017–2021 | 783 in total | 204,945 … 489,956 |
| stage 7 (base + NET-U15) / stage 8 (gates) | 2,729 / 1,009 | — |
| peak memory, main process (sampled every 20 s) | 6.5 GB, during the base deployment fits | — |

No gate failure. The calibration's chosen configurations are compute measurements only; nothing was evaluated.

### R2.7 Narrowed compute estimate for the full development run

Script `experiments/src/confirm/estimate_from_calibration.py`, output `results/confirm/compute_estimate_r2.json`.
Model: fit time = a × rows × proxy(configuration), proxy = n_estimators × (0.5 + feature_fraction) × log2(num_leaves + 1);
a fitted per family (base-like −Z models, top-90 gates, all-candidate NET-U) from the measured fits (min / median / max
of the per-fit rates give the range); the 30 draws have mean proxy 1,356, about 1.4–2 times the two calibration
configurations; every fit of the full run enumerated with the measured row counts (T = 30, five seeds, both bases,
26 gate tasks incl. -thr, 2 × 2 × 2 × 20 × 5 follow-up draws refitted on 5 years, BASE-V deployed separately in the
worst case); fits use 2 threads, the base stage runs 2 (10 threads) or 4 (24 threads) fits at a time because each
full-size base fit holds a ~1 GB training copy; backtests from the pilot's 24 process-seconds per run.

| Stage | 10 threads (5 jobs) | 24 threads (12 jobs) |
|---|---|---|
| base LightGBM (300 tuning + 45 + 45 deployment fits), NET-U15 (300 + 35), ridge | 11–16 h | 5.6–8.4 h |
| gates, 26 tasks × 325 fits | 18–24 h | 8–10 h |
| A4.3 item 6 follow-up (permutation + noise, 20 draws each) | 21–27 h | 9–11 h |
| backtests without RND (~470 runs) | 0.6 h | 0.3 h |
| RND, 200 repetitions (8,000 runs) | 10.7 h | 4.5 h |
| market, features, standard orders, estimands (B = 10,000); the panel now exists | 0.6 h | 0.6 h |
| **total without RND-200** | **52–69 h (2.2–2.9 days)** | **23–31 h** |
| **total with RND-200** | **63–80 h** | **28–35 h** |

Against round 1 (2.3–4.9 days at 10 threads without RND, gates only) the range is narrower; it now includes the
follow-up, which the round-1 estimate did not contain. Memory: measured 6.5 GB (2 base workers); with 5 concurrent gate
fits (NET-U deployment training sets up to ~490,000 rows), the follow-up caches (one draw at a time per task) and
5 backtest processes I expect **8–10 GB at 10 threads, 10–12 GB at 24 threads (4 base workers)**; free memory at
the time of writing 11.5 GB of 33 GB. Options for the PI: RND with fewer repetitions or as a later job (−10.7 h);
perm_draws 10 instead of 20 (−11 h); running the two bases as separate processes; more threads when the other job ends.

### R2.8 Not done, open, caveats

- The cut-off invariance was run on the 100-name smoke only; the auditor's within-development perturbation test was
  not rerun on the new code.
- The archive SHA includes a `created` timestamp, so re-tuning gives an equal-content archive with another SHA; the
  freeze must record the SHA of the archive actually frozen. Any code change (including adding the estimate script
  in this round) changes the code hash, so `smoke_r2/tuning_archive.json` no longer loads with the current code; the
  frozen code must be archived after the final edit and tuned once.
- D4 is applied to order-based criteria; the base's RankIC criterion still uses forward returns of the last H days of
  2012 (the audit's stated 4-day overlap).
- NET-U15 is now identical across bases; P-contrasts involving it are no longer "per base" in substance.
- The "-thr" policies follow the pilot's θ_sel tuning (with D4 / Q3); E-const-dev and RND are not attached to them.
- The LOSS-LR 32-thread test was not run (thread limit).
- `zo_coverage.py` and `paired_contrasts.py` remain unchanged pilot copies.
- The log line "tuned over N configurations" is also printed for gates loaded from an archive (cosmetic;
  `loaded_from_archive` in the tuning log is authoritative).

### R2.9 Reproduction commands (round 2)

```
experiments/.venv/Scripts/python.exe -X utf8 -m unittest experiments/src/confirm/tests/test_confirm.py
# smoke (real tree; writes the tuning archive)
experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/run_confirm.py --data-cutoff 2021-12-31 --smoke \
  --codes-file experiments/results/confirm/smoke_codes.txt --out experiments/results/confirm/smoke_r2 \
  --panel-dir experiments/results/confirm/smoke_panel_r2 --n-configs 4 --seeds 0,1 --perm-draws 2 --rnd-reps 2 \
  --bootstrap-B 200 --jobs 5 --dump-decisions
# tune-only and load-tuning (same options, --jobs 2, plus)
  --out experiments/results/confirm/smoke_r2_tuneonly --tune-only
  --out experiments/results/confirm/smoke_r2_loaded --load-tuning experiments/results/confirm/smoke_r2/tuning_archive.json
# cut-off invariance
experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/cutoff_invariance.py build --data-cutoff 2021-12-31 \
  --codes-file experiments/results/confirm/smoke_codes.txt --work <W>
(smoke command with --raw-root <W>/tree_A (tree_B) --out experiments/results/confirm/ci_run_A (B)
 --panel-dir experiments/results/confirm/ci_run_A/feature_panel --jobs 2)
experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/cutoff_invariance.py compare \
  --runs experiments/results/confirm/smoke_r2 experiments/results/confirm/ci_run_A experiments/results/confirm/ci_run_B \
  --panels experiments/results/confirm/smoke_panel_r2 experiments/results/confirm/ci_run_A/feature_panel \
  experiments/results/confirm/ci_run_B/feature_panel --report experiments/results/confirm/cutoff_invariance_r2.json
# estimate
experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/estimate_from_calibration.py \
  --calib experiments/results/confirm/calibration --pilot-full experiments/results/pilot/run_fixedcount
```

Files of round 2: `results/confirm/smoke_r2/` (with `tuning_archive.json` + `.sha256`, dump, overlap diagnostic,
tuning matrix), `smoke_r2_tuneonly/`, `smoke_r2_loaded/`, `ci_run_A/`, `ci_run_B/`, `cutoff_invariance_r2.json`,
`lossr_blas1/4/8/`, `calibration/` (+ `calibration_mem.csv`), `compute_estimate_r2.json`, `r2_mini/` (first
integration run, T = 1), `smoke_panel_r2/`; full panel `experiments/data/derived/feature_panel_confirm/`.

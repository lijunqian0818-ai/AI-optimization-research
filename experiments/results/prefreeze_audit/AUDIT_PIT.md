# Pre-freeze point-in-time and chronology audit of the exploratory pipeline

Researcher sub-agent, 2026-11-17. Scope: PLAN v0.9.3 amendment §A2.1, §A7 (chronology item), §A8
("Point-in-time audit: scope and tests" (a)–(e), "Further freeze checks" (a)–(d)). Code audited:
`experiments/src/pilot/` (strategy, run_pilot, models, data, stdorders, config, cutoff_invariance),
and the parts of `experiments/src/engine/` and `experiments/src/features/` they call. Nothing under
`pilot/`, `engine/`, `features/` or `confirm/` was modified or run from `confirm/`.

**Data discipline.** No row dated after 2021-12-31 was read. The new test reads only the cut tree A of
the earlier cut-off test (built on 2026-11-16 from the loaders' cut readers) and re-reads every file
through `engine.datacut` with cut-off 2021-12-31; the pipeline runs used `data_cutoff = 2021-12-31`.
No feature–return relation and no performance number was computed for this report: the pipeline
computes its internal tuning criteria (base RankIC, gate θ_sel) as part of stages 6 and 8, but the
test records only SHA-256 hashes and equality counts of them; no value was written or looked at.
No download, no install, no command denied by the permission system, no process killed.
This report has not been reviewed by another model.

Verdict vocabulary: **pass** (established by code reading and, where stated, by a test log);
**fail** (a defect that lets information from after the decision time into a decision, a training
set or a selection); **cannot be established** (depends on the vendor's historical vintages or on
facts outside the code). "Primary contrasts" = the confirmatory family of §A4.1 on the hold-out
2022-01 – 2026-06.

---

## 0. Summary of verdicts

| Item | Verdict | Most important finding |
|---|---|---|
| (a) monthly liquidity screen | **pass** (code + new test) | membership of month m uses data dated ≤ last trading day of month m−1 only |
| (b) eligibility / listing / delisting / suspension / code list | **pass** for the as-of logic; **cannot be established** for the population | as-of logic correct; the 2026 code list, the 2026 listing snapshot (ipo/out dates) and the vendor ST / status flags condition the population and cannot be checked from code |
| (c) feature availability (B0+R, Z_H, Z_O) | **pass** (code + existing look-ahead test + new test); vintage **cannot be established** | day t uses bars < t; Z_O windows counted from availability (s ∈ [t−2−W+1, t−2]); INS dated by announcement rolled forward; revisions of vendor history undetectable |
| (d) labels and execution | **pass** with two stated limitations | labels resolve at t+H (+1) and are used only after resolution; the fill rule reads the day-t "traded" flag (volume > 0) — retrospective, flagged in code; delisting write-off at the first non-listed day uses the snapshot delisting date |
| (e) nested chronology | **fail (minor, development only)** + **design defects for the freeze** | base OOS scores are produced by configurations selected on 2011–2012 (≤ 5 trading days of overlap with 2013); the gate tuning criterion uses outcomes resolving after the first deployment day; tuning is re-executed inside every run, so a one-pass hold-out run would re-tune with later data; Y−1 window not implemented (two lines) |
| (f) preprocessing / early stopping / imputation | **pass** | per-day cross-sectional rank transform; medians from training rows; no early stopping; no full-sample statistic |
| (g) seeds and determinism | **pass** with caveats | bit-identical reruns shown by the earlier test; LightGBM / BLAS results under different thread counts not verified; readiness depends on file modification times |

The new in-development perturbation test (§9) — data dated in 2020–2021 perturbed, inner cut-off
2019-12-31, 100-name smoke list, `fixed_count`, stages 1–8 — **passed**: 0 violations in 18 groups of
objects (monthly screens, candidate sets, 97 feature files / 245,324 rows, ranked rows, base scores and
ranks, nominations, every base and gate training set, every gate decision of every configuration in
2019, 51,984 standard orders resolved by the cut-off), while the perturbation changed every later
object (not vacuous). As predicted by code reading, the **gate tuning criterion changed for all
12 (base, method) pairs** although the cut-off precedes the first deployment day: about 150 of 7,320
nominations of the 2019 tuning year per (base, seed) exit after 2019-12-31, 1–3 of them about 290
trading days later (finding D4). The chosen configurations happened to coincide (2 candidates each).

---

## 1. (a) Monthly liquidity screen U-LIQ-P

**Verdict: pass.**

Evidence.
- `engine/universe.py:45-53` `screen_days`: the last market trading day s of each calendar month.
- `engine/universe.py:123-136` `membership_by_month`: the membership computed on screen day s is
  stored under the *next* calendar month `(nxt.year, nxt.month)` and is used for all decision days of
  that month (`pilot/data.py:184-187`). So the screen date s is strictly before every decision day it
  serves.
- `engine/universe.py:97-120` `members`: every array is sliced `[lo : s_i + 1]` with `lo = s_i − 119`
  (traded-day count, median amount over 120 market days ending s; a day without a trade counts 0,
  `universe.py:76-78`); the ST / row test is on day s (`:108`); listing age through s (`:105`,
  `listed_days`, `:91-94`). Ranking ties by code (`:112`). No return or price change is read
  (amount only).
- `engine/universe.py:139-163` `candidates`: C_t is the month's members filtered with data of day t−1
  only (`p = t_i − 1`; listing age through t−1, row and suspension flag on t−1, ST over the 60 days
  ending t−1).
- The `listed` mask (`universe.py:73-76`) uses `delist_i`, which only removes days on/after delisting.
- New test (§9): every monthly membership up to and including January 2020 (screen day 2019-12-31) and
  every candidate set up to the first decision day after the cut-off is bit-identical after the
  2020–2021 data were perturbed; later memberships do change (the test is not vacuous).

Consequence for the primary contrasts: none. Fix: none.

## 2. (b) Eligibility, listing, delisting, suspension; the 2026 code list

**Verdict: pass** for the as-of logic in code; **cannot be established** for the population and for the
vendor's status flags.

Evidence (as-of logic).
- Listing / delisting dates come from the BaoStock listing snapshot (`bs_stock_basic.parquet`, fetched
  in 2026). `engine/io_baostock.py:196-197` clips both dates at the data cut-off
  (`engine/datacut.py:154-163`: a date after the cut-off becomes "unknown"); `:198-204` maps the
  delisting date to `delist_i` (first market day ≥ outDate; if bar rows exist on/after outDate,
  `delist_i` = day after the last row). `delist_i` is used only for days ≥ `delist_i`
  (`engine/market.py:189-199`, `engine/fills.py:76,87`, `engine/universe.py:73-75`,
  `pilot/data.py:142-143`).
- Listing age uses `ipoDate` (`io_baostock.py:205-209`) and is counted through s (screen) or t−1
  (candidates).
- Suspension: candidate filter removes a name without a row or flagged suspended on t−1
  (`universe.py:154-157`). A name suspended on day t itself stays a candidate; its standard order is
  not filled (S1, `engine/fills.py:115-117`), `rho = 0`, and it is excluded from gate training
  (`strategy.py:257`).
- ST: per-day vendor flag `isST` of the bar row (`io_baostock.py:165,188`); screen uses day s, the
  candidate filter the 60 days ending t−1, the order's price band the day-t flag (pre-open
  information by PLAN 3.4; `fills.py:79`).

Limitations that cannot be fixed in code (state in the paper; do not fix now).
1. **The code list was assembled in 2026** (`experiments/data/universe_pilot_v1.csv`, column
   `origin`: 889 names "already_fetched_code_order", 111 from a seeded random draw; PLAN v0.9 §A8 item
   1). A name can enter the historical population only if it appears in the 2026 BaoStock code table
   and in this list. The list contains 109 delisted names, so it is not survivor-only, but (i) whether
   the 2026 BaoStock table contains every A-share delisted since 2008 is **not verified**; (ii)
   fetching in code order over-represents old SSE main-board codes (600xxx/601xxx), i.e. firms listed
   early; the list is therefore conditioned on listing era and board, which correlate with outcomes.
   This is not look-ahead in a decision (no future price was used to build the list), but the
   population is not a point-in-time universe. Statement needed (§A8 item 1 already has most of it):
   "the population is a 2026-assembled list of codes; membership in the list is not point-in-time".
2. **The listing snapshot is of 2026**: delisting and listing dates are as recorded in 2026 (clipped at
   the cut-off). A later correction of a historical date by the vendor cannot be detected.
3. **Vendor status flags** (`tradestatus`, `isST`) are taken as point-in-time; whether BaoStock
   reconstructs them historically or overwrote them later is **not verified** (source-level check S6,
   S7 in §11).
4. Names whose bar file ends without a delisting date in the snapshot (or with one after the cut-off)
   are carried as "no row" (`market.py:195-196`), not written off.

Consequence for the primary contrasts: the scope clause ("the 300 most traded names of this list",
§A8) carries the population limitation; nothing in the code needs changing.

## 3. (c) Feature availability

**Verdict: pass** for the timing in code (backed by the existing look-ahead test and by the new test);
**cannot be established** for the historical vintage of vendor fields.

B0 + R and Z_H (bar-based).
- `features/timing.py:5-14, 94-104`: bar features are computed "as of data date s" from rows ≤ s and
  re-indexed to the decision day next(s); `features/panel.py:84-106` truncates the bars to rows
  dated strictly before the panel's cut-off and re-indexes (`to_decision_index`). So row t uses
  bar rows ≤ t−1. Index returns of R_O: `panel.py:100-103` (index rows < t).
- Price adjustment: own factor from `close_{s−1}/preclose_s`, anchored at the first row
  (`features/bars.py:52-63`), so an adjusted value never changes when a later event occurs.
  `preclose_t` is pre-open public information; it enters the factor for row t but only data through t−1
  enter features of day t.
- Z_H weekly CGO variant uses the trading calendar to decide whether a week is complete
  (`features/zh.py:170-179`); the calendar is pre-announced information (and the variant is not in the
  primary set). The chip-distribution and CGO features use rolling windows of rows ≤ s only
  (`zh.py`; covered by the look-ahead test).
- Pilot-side derived arrays: ADV over traded days with index < t (`pilot/data.py:158-167`), 20-row
  volatility assigned to the day after its last row (`:152-157`), both ≤ t−1.

Z_O (event-based).
- Event day: LHB = listing day `上榜日` / `上榜日期`, BLK = trade day `交易日期`
  (`features/zo.py:331, 420-421`); INS = first trading day ≥ the announcement date `NOTICE_DATE`
  (`zo.py:483-500`, `roll_forward_pos`), never the transaction dates (START/END only in cleaning,
  `zo.py:462-480`; EITIME never enters a feature).
- Lag 2 for all three classes (`features/config.py:59`); an event of day s is usable for t ≥ s + 2
  (`zo.py:243-245`).
- **Window counted from availability**: `end = dec_pos − lag` and windows `[end − W + 1, end]`
  (`zo.py:200-220, 340-353, 432-444, 504-515`), i.e. event days t − lag − W + 1 … t − lag, exactly the
  definition required by §A8 checklist item (3). Days-since / has-prior use the latest event day
  ≤ t − lag (`zo.py:221-230`).
- Denominators: LHB intensity / ADV_t (traded days ≤ t−1, `panel.py:35-61`); BLK amount / float market
  value of the trade day s ≤ t−2 and premium over the unadjusted close of s from own bars restricted to
  rows < t (`zo.py:425-437`).
- Ex-post vendor fields (`上榜后N日`, `解读`, current prices of the share-change table) are blacklisted
  and never loaded (`features/config.py:106-132`, `features/store.py:48-61`).
- Coverage: a class covers day d only if its period file exists and d ≤ min(raw end, data cut-off)
  (`zo.py:123-126, 148-184`).

Tests.
- Existing feature look-ahead test (`features/lookahead.py`; truncate / NaN / shuffle / noise / drop /
  inject of everything outside G_t, availability scope): synthetic 330/330, real 582/582 at cut-off
  2021-12-31 (`results/feature_tests/FEATURE_TEST_REPORT.md` lines 375, 637). This is a
  feature-function test for single names and days.
- New pipeline-level test (§9): all 97 feature files bit-identical on every row up to the first decision
  day after 2019-12-31 after the 2020–2021 bars, events, Z_O tables and delisting dates were perturbed.

Cannot be established from code (state, and check at source level, §11):
- Whether the vendor's historical values (LHB amounts, BLK trades, INS records and their
  NOTICE_DATE, `turn` (float-share basis), `preclose`) were revised after the event. Cut-off
  invariance cannot see a revision (both the earlier and the new test perturb only rows dated after
  the cut-off). Known facts from STATUS.md: INS 41 % back-filled (EITIME long after notice), 15 % of
  announcement dates on non-trading days (rolled forward by design), CHANGE_FREE_RATIO meaning pending
  OA5.
- Whether a lag of 2 trading days is enough for every LHB/BLK record (publication time of day not in
  the data; `features/config.py:60-64` records why lag 2 was chosen).

Consequence for the primary contrasts: P3 (Z_O contrast) and the Z_H contrasts rest on the vendor
vintage; §A8 "Further freeze checks (b)" applies. No code change needed.

## 4. (d) Labels and execution

**Verdict: pass**, with two limitations to state.

Evidence.
- Decision day t = entry day. Orders are formed from G_t (ADV ≤ t−1, day-t `preclose` and ST flag;
  `engine/fills.py:43-80`), filled at the day-t open if (S1) the day-t bar is traded, (S2) open < limit-up
  price (buy) / > limit-down (sell), (S3) order value ≤ 1 % of ADV (`fills.py:97-137`).
- Exit due at t + H (`pilot/stdorders.py:39-45`, `lot.exit_due_i`), sold at the open of the first day
  ≥ t + H on which the sell fills (limit-down or suspension → re-submitted next day, LP rule).
- O1 label: computed from data dated ≤ t + H and frozen at t + H + 1 (`engine/ledger.py:221-229`,
  `engine/labels.py:70-73`); not listed at the mark day → U (label 1, `labels.py:166-168`).
- ρ (standard-order P&L per slot): realised at the exit or write-off day; an order still open at the
  last data day is valued at its open value that day and flagged `unresolved` (`stdorders.py:63-78`).
- Base target: within-day rank of open(t+H)/open(t) − 1 on own-adjusted opens (`pilot/data.py:168-172`,
  `strategy.py:47-55`); known at the open of t + H; used for training only with the purge of §6.
- Gate labels are used only if resolved before the cut day: O1 if t + H + 1 < cut, ρ if the realised
  exit day < cut and not unresolved (`strategy.py:249-273`). Unfilled orders are dropped from gate
  training (`:257`).
- Delisting: a held lot is written off at `terminal_value_U = 0` × last value on the first non-listed
  day (`engine/ledger.py:318-334`, `engine/config.py:53`); no disposition table exists, so every
  delisting is a write-off (smoke report §6 item 25).
- New test (§9): every standard order decided on or before 2019-12-31 whose exit lies on or before
  2019-12-31 is bit-identical after perturbation of 2020–2021 data.

Limitations (no look-ahead into a decision, but they define what the simulator means).
1. **Fill rule reads the day-t "traded" flag** (row exists, flagged trading, volume > 0;
   `fills.py:83-94`). Whether a name trades at all on day t is not known before the open. The engine
   says so (`fills.py:14`: "retrospective"). A name that resumed trading after the open would be
   credited with an open fill. §A8 "Further freeze checks (d)" (conservative fill case) covers this;
   without it the estimates concern the specified simulator.
2. **Terminal value of delisted names** = 0 at the first non-listed day, using the 2026 snapshot
   delisting date (clipped at the cut-off) or the day after the last bar row. A real holder could have
   sold during the delisting-arrangement period (those rows are kept and tradable until the last row);
   names suspended until a delisting dated after the cut-off are carried at the last value instead
   (`market.py:189-199`). Both conventions are G_t-measurable at the day they act; they are modelling
   choices (U33), not leaks.
3. The base target drops rows whose open on t or t+H is missing (not traded; `data.py:149`), i.e. the
   training sample is selected on future tradability. This affects only who is in the training set, not
   any decision; it is a known form of label-availability selection, to be stated.

Consequence for the primary contrasts: none beyond the stated simulator limits.

## 5. (e) Nested chronology

**Verdict: fail (minor; development-period numbers only) for the gate tuning criterion; pass for
base deployment and gate fitting; design defects for the freeze listed below.**

### 5.1 Base predictor (`pilot/strategy.py:71-118`)
- Training rows for target year/fold starting at day index `first_i`: decision days
  `first_feature_year … first_i − 2H − 2` with finite target (`strategy.py:81-82`). The target of the
  last row resolves at the open of `first_i − H − 2`. So deployment year Y uses only rows whose label
  window ends before Y (§A7 chronology item: **pass**), with H + 1 purge and H + 1 embargo.
- Tuning: each configuration × seed × tuning year v is fitted on rows before v (same mask) and scored
  by mean daily RankIC on all candidate rows of v (`:85-95`). The best configuration is chosen once
  (`:96-97`) and used for all deployment years (`:99-111`); annual refits with an expanding window.
- The validation RankIC of the last tuning year v uses labels that end H trading days into v + 1
  (2012 validation: up to the open of 2013-01-10).

### 5.2 Gates (`pilot/strategy.py:276-376`, `pilot/run_pilot.py:250-328`)
- Learned gates, year Y (pilot window "Y−2"): rows of the gate population (top-K_tr = 90 nominations by
  OOS base rank; NET-U: all of C_t) on decision days from the first base deployment day to
  `lo_{Y−1} − 2H − 2` (`strategy.py:326-328`; `min(end of Y−2, lo_{Y−1} − 2H − 2)` is always the second
  term), labels resolved before the first day of Y−1 (`:330`), filled orders only. Features: −Z and
  Z columns plus the OOS base rank (`:209-221`).
- Calibration / threshold rule: model scores on the nominations of Y−1, no labels (`:337-351`). Under
  `fixed_count` the threshold is computed but not used (`:348-350, 356-358`).
- CONF: isotonic map on the nominations of Y−1 with labels resolved before the first day of Y
  (`:309-320`).
- Tuning (`run_pilot.py:279-318`): for each configuration, `gate_year(m, conf, v)` for the tuning years
  v ∈ {2015, 2016}; criterion = mean over seeds × tuning years of θ_sel over **all** nominations of v
  (`run_pilot.py:296-308`, `strategy.py:379-404`), using `std[(i, c)]["rho"]` irrespective of when the
  order resolved.

### 5.3 Findings
1. **Selection chronology (GPT's question, §A8 further check (a)).** Every historical OOS base score that
   a gate is trained on (decision days from 2013-01-04) was produced by a base configuration selected on
   the 2011–2012 validation folds. Those folds use outcomes up to the open of 2013-01-10. Hence the
   hyperparameters were **not** selected on the outcomes of the gate-training period, **except** that
   the selection criterion and the labels of the first 4 base-OOS decision days of 2013
   (2013-01-04 … 2013-01-09) share price paths up to 2013-01-10. Effect: small (4 of ≈ 240
   gate-training days in the first gate fit, which uses 2013 rows only; 4 of ≈ 1,700 in the 2021 fit); it
   does not touch the hold-out. **Answer: no, with an overlap of at most H trading days at the start of 2013.**
   **Freeze requirement:** §A7 re-tunes the base "with rolling temporal validation". If the v1.0
   validation folds include any year ≥ 2013, the base scores fed to the gates in those years are
   produced by hyperparameters selected on their own outcomes — then the answer becomes "yes", and it
   must be stated and its effect assessed, or the gate training rows must start after the last base
   validation year + H + 1 days. The same applies to BASE-V (§A7), whose criterion is the endpoint V.
2. **Gate tuning criterion uses outcomes resolving after the first deployment day (fail, minor).**
   θ_sel of tuning year 2016 includes orders of the last days of 2016 that exit on 2017-01-09 or later
   (delayed exits after limit-down / suspension, without bound), and orders still open at the end of the
   data are valued at the last data day (`stdorders.py:65-70`). The configuration deployed from
   2017-01-03 is therefore a function of some 2017+ prices. Development-period numbers only; the
   hold-out is not affected **provided tuning is run with data cut at 2021-12-31** (see 4). Fix: in
   the tuning criterion count only orders with `exit_i < lo_{v+1}` (and drop unresolved), or end each
   tuning year's decision days at `lo_{v+1} − H − 2` (the end-of-window rule already used for the
   development period, `run_pilot.py:185`). The new test measures how many tuning-year orders resolve
   after the cut-off (§9).
3. **Y−1 window (§A2.1) not implemented.** Exact change, for the fixed-count learned gates only:
   - `strategy.py:327` `hi_fit = ... lo_1 - 2 * H - 2` → `hi_fit = lo_Y - 2 * H - 2`;
   - `strategy.py:330` `self.labels(rows_fit, target, lo_1)` → `self.labels(rows_fit, target, lo_Y)`;
   - keep the Y−2 lines for `-thr` policies, NET-U and the Y−2 sensitivity (switch on
     `fixed and fam in ("LOSS", "LOSS-LR", "NET-K")` and a sensitivity flag);
   - the calibration predictions (`:337-343`) can stay (unused under fixed count);
   - update the header (`strategy.py:8-12`).
   **Feasible** with label resolution d = H + 1: the last fitted row t = lo_Y − 2H − 2 has its O1 label
   frozen at t + H + 1 = lo_Y − H − 1 < lo_Y and its ρ resolved at the exit day t + H = lo_Y − H − 2
   unless the exit is delayed by H + 2 days or more; delayed rows are dropped by the existing `labels()`
   check (a label-dependent censoring of a few boundary rows — delayed exits are mostly losses — that
   also exists under Y−2 and should be stated). The first gate year with Y−1 needs one year of base OOS
   rows: tuning year 2015 (rows 2013-01-04 … 2014-12-16) is feasible. After the change, the look-ahead
   and cut-off tests must be re-run (§A8).
4. **Tuning is re-executed inside every run (design defect for the freeze, high if unaddressed).**
   `base_scores` always re-tunes (`strategy.py:84-97`); gates re-tune unless `--reuse-tuning` is given
   (`run_pilot.py:279-294`); TREND / PERF / VT re-tune always (`run_pilot.py:419-445, 459-475`). A
   one-pass confirmatory run with data to 2026-06 would recompute the tuning criteria with later data:
   orders of the tuning years that are unresolved at 2021-12-31 would be revalued with hold-out prices,
   and any tuning or validation year whose label windows cross 2021-12-31 would use hold-out outcomes.
   With the PLAN's years (base 2011–2012, gates 2015–2016) the expected effect is nil, but it is not
   guaranteed (an order of 2016 still suspended at 2021-12-31 changes value). Fix: run all tuning once
   with `--data-cutoff 2021-12-31`, archive the chosen configurations (and σ* of VT), and make the
   hold-out run load them and refuse to re-tune (extend `reuse_tuning` to base, TREND, PERF, VT and
   assert equality of the configuration lists).
5. **Annual refits**: base refit each Y on an expanding window (`strategy.py:106-111`); gates refit each
   Y (`run_pilot.py:315-316`); configurations never re-tuned. PERF uses the RankIC history with
   s ≤ t − H − 2 (`run_pilot.py:414`), TREND the universe index through t − 1 (`:404`), VT the G0
   volatility through t − 1 (`:465`, `shift(1)`), E-const-dev the invested fraction of Y − 1
   (`:491-499`). All pass.

### 5.4 Year-by-year chronology table (full pilot configuration `PilotConfig`, H = 5; derived from the code)

Day indices are market trading days; dates from the trading calendar (≤ 2021). `lo_Y` = first trading
day of Y. "Rows" = decision days of the rows used. Purge/embargo of the code: rows ≤ lo − 2H − 2.

| Y | role (config) | base training rows | base tuning rows | gate training rows (pilot, Y−2) | gate tuning rows | last label date used |
|---|---|---|---|---|---|---|
| 2011 | base validation | 2009-01-05 – 2010-12-16 | validation: all candidates of 2011 | — | — | base fit: 2010-12-23; criterion: 2012-01-10 |
| 2012 | base validation | 2009-01-05 – 2011-12-15 | validation: all candidates of 2012 | — | — | base fit: 2011-12-22; criterion: 2013-01-10 |
| 2013 | first base OOS year | 2009-01-05 – 2012-12-14 (config from 2011–12) | — | — | — | 2012-12-21 |
| 2014 | base OOS | 2009-01-05 – 2013-12-16 | — | — | — | 2013-12-23 |
| 2015 | gate tuning year | 2009-01-05 – 2014-12-16 | — | 2013-01-04 – 2013-12-16, labels resolved < 2014-01-02; threshold calibration on 2014 nominations | θ_sel over all 2015 nominations (exits to ≥ 2016-01-08) | gate fit: < 2014-01-02; criterion: ≥ 2016-01-08 (delayed exits unbounded) |
| 2016 | gate tuning year | 2009-01-05 – 2015-12-16 | — | 2013-01-04 – 2014-12-16, labels < 2015-01-05; calibration 2015 | θ_sel over all 2016 nominations (exits to ≥ 2017-01-09) | gate fit: < 2015-01-05; criterion: ≥ 2017-01-09 |
| 2017 | evaluation | 2009-01-05 – 2016-12-15 | — | 2013-01-04 – 2015-12-16, labels < 2016-01-04; calibration 2016 | (config frozen from 2015–16) | base: 2016-12-22; gate: < 2016-01-04 |
| 2018 | evaluation | 2009-01-05 – 2017-12-14 | — | 2013-01-04 – 2016-12-15, labels < 2017-01-03 | — | base: 2017-12-21; gate: < 2017-01-03 |
| 2019 | evaluation | 2009-01-05 – 2018-12-13 | — | 2013-01-04 – 2017-12-14, labels < 2018-01-02 | — | base: 2018-12-20; gate: < 2018-01-02 |
| 2020 | evaluation | 2009-01-05 – 2019-12-16 | — | 2013-01-04 – 2018-12-13, labels < 2019-01-02 | — | base: 2019-12-23; gate: < 2019-01-02 |
| 2021 | evaluation (decisions to 2021-12-10) | 2009-01-05 – 2020-12-16 | — | 2013-01-04 – 2019-12-16, labels < 2020-01-02 | — | base: 2020-12-23; gate: < 2020-01-02 |
| Y (§A2.1 Y−1, proposed) | | as above | | 2013-01-04 – (lo_Y − 12), labels < lo_Y (e.g. 2017: – 2016-12-15, < 2017-01-03) | | gate: < lo_Y |

CONF (all years): isotonic map on the nominations of Y − 1 with labels resolved before lo_Y.
The base for every year uses the configuration chosen on 2011–2012 (§5.3 item 1).

## 6. (f) Early stopping, standardisation, rank transforms, imputation

**Verdict: pass.**
- No early stopping; the number of boosting rounds is a hyperparameter (`pilot/models.py:7, 96-100`).
- Features: cross-sectional percentile rank within each decision day over the candidate rows of that
  day (`models.py:61-72`, applied once in `run_pilot.py:207`). C_t is G_t-measurable (§1), so the rank of
  a row uses only same-day, pre-open information. Winsorisation is not used (made moot by ranks).
  No standardisation across time.
- Linear / logistic models: median imputation and missing indicators fitted on the training rows only
  (`models.py:75-89, 114-145`).
- LightGBM minimum leaf size is a fraction of the training rows (`models.py:97`) — a function of the
  training set only.
- Base score → within-day rank before gates (`strategy.py:112`); base target = within-day rank of the
  forward return among rows with a finite return (`strategy.py:47-55`).
- Permutation controls: Z permuted within day across the K_tr population, one draw per (base, seed),
  drawn day by day in ascending order before threads start (`strategy.py:223-247`,
  `run_pilot.py:275-277`); the draw for a day depends only on row counts of that and earlier days.
- No full-sample statistic leaks across time: `rank_within_days` groups by day; `spearman_by_day` by
  day; quantile thresholds use Y−1 scores only (`strategy.py:296-297, 315, 346, 354`); NET-U grid on Y−1
  (`:362-371`).
- New test: rank-transformed feature rows of every decision day ≤ the first decision day after the
  cut-off are bit-identical (§9).

## 7. (g) Seeds and determinism

**Verdict: pass, with caveats.**
- Seeds: configuration draws fixed (`models.py:35-38`, seed 20261115); LightGBM `random_state = seed`,
  `deterministic=True`, `force_row_wise=True` (`models.py:96-100`); ridge / elastic net / logistic /
  isotonic deterministic; permutation draws `default_rng(1000 + s)` (`run_pilot.py:265`); RND
  `default_rng(10000 s + 100 rep + hash_str(g) % 97)` with a SHA-256-based `hash_str`
  (`run_pilot.py:510, 544-545`); bootstrap seed fixed (`run_pilot.py:568`).
- Thread pools: gate tasks are independent and their results are keyed (`run_pilot.py:320-327`);
  standard orders are concatenated and sorted (`stdorders.py:101-105`). The set-iteration-order defect
  of the ledger was fixed before the earlier test (PILOT_SMOKE_REPORT §4).
- Evidence: three runs (real tree, tree A, tree B) produced bit-identical `results.json`, standard orders
  and features (`results/pilot/cutoff_test/cutoff_invariance.json`), i.e. reruns in fresh processes
  are reproducible with the same thread settings.
- **Not verified:** whether LightGBM (`deterministic=True` is documented for a fixed number of threads)
  and the BLAS used by ridge / elastic net / logistic regression give bit-identical results with a
  different thread count; the pilot does not fix `OMP_NUM_THREADS` / `OPENBLAS_NUM_THREADS`. Fix: fix
  the thread counts in the frozen configuration and the environment, and record them in the manifest.
- `pilot/data.py:70-86` readiness excludes a bar file modified in the last 15 minutes and reads the fetch
  manifest; the set of names in a run therefore depends on the state of the disk at start time. Now that
  fetching has stopped this is stable, but the frozen run should use a fixed name list and fail if any
  file's SHA-256 differs from the archived one.
- `features/market_panel.py:170-178`: an existing panel directory is **reused** (files with status ok in
  `manifest.csv`) without checking that they were built with the same data cut-off, raw root or code, and
  `panel_meta.json` is rewritten with the *new* cut-off. A run with a different cut-off or raw tree that
  points at an old panel directory silently uses the old features and records the wrong provenance.
  Fix: refuse reuse unless the stored per-file `data_cutoff`, raw root and catalogue hash match, or
  always build into a new directory for the frozen runs.

## 8. What `cutoff_invariance.py` exercises and what it cannot detect

The test (`pilot/cutoff_invariance.py:48-153`) builds tree A (raw data cut at the run's data cut-off) and
tree B (A plus garbage dated **after the data cut-off**) and compares runs **with the same data
cut-off** (2021-12-31). Since every loader drops rows after the data cut-off before any computation, the
test establishes that **nothing dated after the data cut-off reaches the pipeline** (loader discipline,
including the Z_O period-file rule and the listing-snapshot clipping). It does **not** exercise any of
(a)–(f) as chronology inside the loaded window: a 2019 decision that used 2021 data would pass it.

| Item | Exercised by `cutoff_invariance.py`? | By the new test (§9)? |
|---|---|---|
| (a) monthly screen uses data before the selection date | no (only data after the data cut-off removed) | **yes** |
| (b) listing / delisting / status as of each date | partly (post-cut-off delisting dates blanked) | **yes** (delisting dates moved inside 2020–2021, status flags flipped) |
| (c) feature availability, Z_O lag and windows | no at pipeline level (feature-level: `features/lookahead.py`) | **yes** (all 97 feature files and the ranked rows) |
| (d) labels / fills / delisting write-off | no | **yes** for orders resolved by the cut-off |
| (e) nested chronology (base purge, gate windows, tuning) | no | **yes** for base and gate training sets and gate decisions; tuning criterion measured |
| (f) preprocessing leaks across time | no | **yes** (ranked rows, base scores) |

What neither test can detect:
- revised historical values (a vendor overwriting a 2015 record in 2024 — both trees carry the 2026
  vintage);
- wrong event dates (an INS notice date that is later than the true public date by vendor error, or an
  LHB record published after the lag);
- the code-list and listing-snapshot conditioning (b);
- look-ahead in what the simulator regards as "known at the open" (day-t traded flag, day-t ST flag,
  existence of the day-t row);
- dependence on later data that happens to be inert for the perturbation used (the perturbation is
  random noise, deletion and injection; a deterministic leak through a field that was not perturbed —
  the trading calendar, `ipoDate`, the listing table's non-date columns — would not be seen);
- anything outside stages 1–8 (backtests, estimands; stage 9 was not run by the new test) and the
  methods excluded from the new test (§9 configuration);
- the Y−1 gate window and the Z_O* set (not implemented yet).

## 9. New test: perturbation inside the development period

**Question.** With data loaded to 2021-12-31, does any object that by the pipeline's own timing rules
may depend only on data dated ≤ C = 2019-12-31 change when every datum dated in (C, 2021-12-31] is
changed? The earlier cut-off test cannot answer this (§8). Not equivalent to any existing test, so it
was run.

**Trees** (`build_trees.py`, log `build_trees.log`). Source: the cut tree A of the earlier test (100
smoke names, 3 indices, calendar, listing table, EV1/EV2/Sina rights, all Z_O period files ≤ 2021),
re-read through `engine.datacut` at 2021-12-31. tree_R = tree A as read. tree_P = tree A with, for rows
dated after C only: 43,224 bar rows perturbed (prices × exp(N(0, 0.2)), volume / amount / turn ×
exp(N(0, 0.5)), pctChg noise, tradestatus flipped 5 %, isST flipped 3 %) and 842 deleted; index prices
perturbed; 298 corporate-action rows with amounts × U(0.2, 3) and 218 fabricated events; Z_O rows dated
after C with numeric fields × exp(N(0, 0.7)) and the code column permuted (LHB 34,834, LHB-institutional
14,979, BLK 62,606, INS 30,004 rows) plus 7,400 fabricated rows assigned to smoke names; 30 delisting
dates of smoke names moved into (C, 2021-12-31]. Calendar unchanged (seed 20261117).

**Configuration** (declared in `run_pit.py` before running; a shifted smoke schedule so that a whole
gate year lies before C): smoke list (97 names with bars), data cut-off 2021-12-31, features from 2014,
base tuning year 2016, base deployment 2017–2021, gate tuning year 2019, evaluation 2020–2021,
`gate_rule = fixed_count`, seeds {0, 1}, 2 configurations per learned method, methods G0, SCORE, CONF,
VOL, LIQ, LOSS-LR(−Z), LOSS(−Z), LOSS(+Z_H), LOSS(+Z_O), NET-K(−Z), NET-U(−Z); both bases. Stages 1–8
(no backtests). Pilot code unchanged; functions wrapped in the test process to record hashes. Run time
≈ 30 min per tree (both in parallel, 4 threads each). Logs: `run_R.stdout.log`, `run_P.stdout.log`.

**Result** (`compare_pit.json`, `compare_pit.stdout.log`): **pass**.

| Object | expected identical: n / identical | after C: n / identical (shows the perturbation reached it) |
|---|---|---|
| monthly membership (months ≤ Jan 2020) | 144 / 144 | 23 / 0 |
| candidate sets (days ≤ 2020-01-02) | 1,465 / 1,465 | 470 / 0 |
| feature panel files, rows ≤ 2020-01-02 | 97 files, 245,324 rows / all bit-identical | 43,133 rows / 0 |
| rank-transformed feature rows per day | 1,465 / 1,465 | 470 / 0 |
| base tuning record (hash of all validation values) and chosen config | 2 / 2 and 2 / 2 | — |
| base scores and within-day ranks per (base, seed, day ≤ C) | 5,856 / 5,856 (each) | 1,884 / 4 |
| nominations top-K and top-K_tr per day ≤ C | 2,924 / 2,924 (each) | 1,884 / 4 |
| base tuning training sets | 6 / 6 | — |
| base deployment training sets, Y ≤ 2020 (Y = 2021 may change) | 12 / 12 | 3 / 0 |
| CONF isotonic training sets, Y ≤ 2020 | 8 / 8 | 4 / 0 |
| learned-gate training sets, Y = 2019–2021 (Y−2 window: rows ≤ 2019, labels < 2020) | 96 / 96 | — |
| gate decisions of every configuration on every day ≤ C (2019) | 16,592 / 16,592 | 20,784 / 111 |
| standard orders decided ≤ C and resolved ≤ C | 51,984 / 51,984 | 713 / 343 |
| gate tuning criterion (hash of the per-configuration values) | (not required by the code's rules) | **12 / 0 — all changed** |
| chosen gate configuration | (not required) | 12 / 12 (coincided) |

Orders of the gate tuning year 2019 (per base, seed): 7,320 nominations, 147–152 exit after
2019-12-31 (almost all at the regular H = 5 days; 1–3 per (base, seed) after about 290 trading days of
suspension), 0 open at the data end, 57–66 not filled. These enter the tuning criterion although the
configuration is deployed from 2020-01-02 (finding D4). No value of any criterion, score or return was
written or inspected; the counts above are counts of orders.

**What this test establishes and what it does not.** Established, for this configuration: the monthly
screen, candidate filter, feature panel (B0+R, Z_H, Z_O), cross-sectional ranking, base purge/embargo,
base and gate training sets (including the Y−2 window and label-resolution checks), gate decisions under
the fixed-count rule and standard-order outcomes resolved by C do not depend on any perturbed datum
dated after C. Not established: the threshold rule (not run); the methods not run (LOSS(+Z_H+Z_O), the
permutation controls, NET-K(+Z)); TREND / PERF / VT / E-const-dev / RND, the backtests and the estimands
(stages 9–10); the full 969-name population and the PLAN schedule; the Y−1 window and Z_O* (not implemented);
anything §8 lists as undetectable (revisions, wrong dates, the calendar, fields not perturbed).

## 10. Further freeze checks of §A8 (a)–(d) — status

- (a) Selection chronology: answered in §5.3 item 1 (no, apart from ≤ H days of overlap at 2013-01-04 …
  01-09); conditional on the v1.0 base validation years.
- (b) Source-level availability: not done; plan in §11.
- (c) Estimand-defining choices: not in scope of this audit, except that the gate tuning criterion of the
  pilot is the **mean over tuning years × seeds of per-year θ_sel** (`run_pilot.py:298-308`), not the
  pooled V of §A2.2; the implementation must be changed before the freeze (§A2.2 says so).
- (d) Conservative execution case: not implemented (fills read the day-t traded flag, §4).

## 11. Source-level checks still needed (proposed sampling scheme; NOT executed)

All draws with `numpy.random.default_rng(20261117)`, from the frozen development-period tables of the
confirmatory population, strata fixed before looking; each record is compared with the original
disclosure (exchange website / CNINFO announcement / exchange data archive), recording the public date
(and time of day where available) and the field values. Pass rule proposed: per class, the one-sided 95 %
upper confidence bound of the share of records whose public date is later than the date the code assumes
(event day + lag) is below 5 %; and value mismatches above a stated tolerance below 5 %. Failing classes
are excluded or moved to a labelled sensitivity (§A8 (b)).

| # | Field(s) | Sample | Strata | Source |
|---|---|---|---|---|
| S1 | LHB listing day, net buy, seat amounts, reason | 10 records per stratum (≈ 260) | year 2009–2021 × exchange (SSE / SZSE) | SSE / SZSE daily "交易公开信息" archives |
| S2 | BLK trade day, price, amount | 10 per stratum (≈ 260) | year × exchange | SSE / SZSE block-trade daily disclosures |
| S3 | INS NOTICE_DATE (date and clock time), direction, CHANGE_FREE_RATIO | 200, oversampling back-filled rows: 100 with EITIME − notice > 30 days, 100 others | year × back-filled | CNINFO announcement of the change |
| S4 | `preclose` on ex-dates (adjustment chain) and event amounts (EV1/EV2) | 60 events | year × event type (cash / bonus / rights) | CNINFO 分红实施公告; exchange ex-right reference prices |
| S5 | `turn` (float-share basis) around share unlocks | 50 name-days | around 解禁 dates vs ordinary days | exchange float-share announcements / annual reports |
| S6 | `isST` start / end | 30 ST episodes | year | exchange ST announcements |
| S7 | `tradestatus` suspension spells | 30 spells | year × spell length (1 day / ≥ 20 days) | exchange suspension / resumption announcements |
| S8 | delisting date (outDate) and last trading day | all delisted names of the population (109 in the list; those ≤ 2021 for the development period) | — | exchange delisting announcements |
| S9 | ipoDate | 30 | listing decade | exchange listing announcements |
| S10 | trading calendar | every year 2008–2021 | — | exchange holiday notices |
| S11 | code list completeness | compare the delisted names in the BaoStock 2026 code table with an independent delisting list for 2008–2021 | — | exchange / CSRC delisting lists |

The OA10 sampling list of the feature library is provisional (STATUS.md) and must be redrawn after the
freeze; S1–S3 can replace it.

## 12. Defects ranked by severity

| # | Severity | Defect | Where | Effect on primary contrasts | Fix / statement |
|---|---|---|---|---|---|
| D1 | High (freeze process) | Tuning is re-executed in every run; a one-pass hold-out run re-tunes with data after 2021-12-31 (unresolved tuning-year orders revalued; any tuning/validation window crossing 2021-12-31 uses hold-out outcomes) | `strategy.py:84-97`, `run_pilot.py:279-318, 419-445, 459-475` | possible contamination of the frozen configurations by hold-out data | tune once at cut-off 2021-12-31; archive configs (+ σ*); hold-out run loads them, refuses to re-tune, asserts equality |
| D2 | Medium | Feature panel reuse without provenance check; `panel_meta.json` overwritten with the new cut-off | `features/market_panel.py:170-178` | wrong features or wrong provenance if a stale directory is reused | check per-file data_cutoff / raw root / code hash, or always build fresh |
| D3 | Medium (until decided) | Base re-tuning with "rolling temporal validation" (§A7) would, if folds include years ≥ 2013, select base hyperparameters on the outcomes of the gate-training rows (selection chronology fails) | §A7 (design); pilot code uses 2011–2012 only | gate training (development only) | keep base validation years ≤ 2012, or start gate rows after the last validation year + H + 1, or state and assess |
| D4 | Low–medium | Gate tuning criterion uses outcomes resolving after the start of the first deployment year (exits after year end, unresolved orders valued at the data end) | `run_pilot.py:296-308`, `strategy.py:379-404`, `stdorders.py:63-70` | development-period numbers only | count only orders resolved before lo_{v+1}, or end tuning decision days at lo_{v+1} − H − 2 |
| D5 | Low (to implement) | Y−1 gate window not implemented; criterion is mean of annual θ_sel, not pooled V (§A2.2) | `strategy.py:327, 330`; `run_pilot.py:298-308` | the frozen spec cannot be run as written | two-line change (§5.3 item 3), re-run look-ahead / cut-off tests |
| D6 | Low | Thread counts not fixed; bit-identity across thread counts not verified | `models.py:96-100`, environment | reproducibility only | fix and record thread counts |
| D7 | Low | Run population depends on file mtimes and the fetch manifest | `pilot/data.py:70-86` | reproducibility only | frozen name list + file hashes |
| D8 | Low (sealing hygiene) | The listing snapshot is loaded whole (`io_baostock.py:129`, `features/store.py:84-91`, `cutoff_invariance.py:58`); outDate / ipoDate values after the cut-off are in memory before `clip_date` blanks them | `io_baostock.py:129, 196-197` | none on decisions (clipped before use) | blank post-cut-off dates at read time, or ship a cut snapshot with the frozen raw tree |
| L1 | Limitation | 2026-assembled code list; 2026 listing snapshot; vendor status flags | §2 | scope | statement (§A8 item 1, KL-23/24) |
| L2 | Limitation | Vendor vintages of Z_H / Z_O inputs and of `preclose` cannot be verified by cut-off tests | §3, §8 | P3 and Z_H contrasts | source-level checks §11 |
| L3 | Limitation | Fill rule reads the day-t traded flag; write-off to 0 at delisting | `fills.py:83-94`, `ledger.py:318-334` | estimates concern the simulator | conservative execution sensitivity (§A8 (d)) |
| L4 | Limitation | Label-availability selection: base target needs a traded open at t+H; gate rows with delayed exits near the window end dropped | `data.py:149, 168-172`, `strategy.py:262-268` | small; affects training samples only | statement |

## 13. Files

- `experiments/src/prefreeze_audit/build_trees.py` — builds tree_R (reference) and tree_P (perturbed)
  from the cut tree A of the earlier test, through the cut readers.
- `experiments/src/prefreeze_audit/run_pit.py` — runs stages 1–8 of the unchanged pilot code on one tree
  and records hashes (wraps functions in its own process only).
- `experiments/src/prefreeze_audit/compare_pit.py` — comparison and report JSON.
- Logs beside this file: `build_trees.log`, `run_R.stdout.log`, `run_P.stdout.log`, `compare_pit.json`,
  `compare_pit.stdout.log`. The trees and run directories (features, records) are in the session
  scratchpad `C:\Users\lijun\AppData\Local\Temp\claude\7dc3241753d402cb\6264ec4d-6267-4fe9-b6c0-5bfd1988cc73\scratchpad\pit`
  (not cleaned).

Reproduce:
```
experiments/.venv/Scripts/python.exe -X utf8 experiments/src/prefreeze_audit/build_trees.py --source <tree_A of the earlier test> --work <W> --codes-file experiments/results/pilot/smoke/smoke_codes.txt --inner-cutoff 2019-12-31
experiments/.venv/Scripts/python.exe -X utf8 experiments/src/prefreeze_audit/run_pit.py --raw-root <W>/tree_R --out <W>/run_R --codes-file experiments/results/pilot/smoke/smoke_codes.txt --jobs 4 --threads 1
experiments/.venv/Scripts/python.exe -X utf8 experiments/src/prefreeze_audit/run_pit.py --raw-root <W>/tree_P --out <W>/run_P --codes-file experiments/results/pilot/smoke/smoke_codes.txt --jobs 4 --threads 1
experiments/.venv/Scripts/python.exe -X utf8 experiments/src/prefreeze_audit/compare_pit.py --ref <W>/run_R --pert <W>/run_P --inner-cutoff 2019-12-31 --report experiments/results/prefreeze_audit/compare_pit.json
```

# Numerical sanity checks for `theory/` (not experiments for the paper)

Researcher (sub-agent), 2026-11-15; **updated after review rounds 1, 2 and 3** (see "History"). numpy only, system Python 3.14, fixed seeds (3 per randomised script). Every number below is copied from the `results_*.txt` files produced by the commands shown; nothing was tuned after seeing results except the changes listed under "History".

**What these checks are.** Finite numerical sanity checks on a few hand-picked synthetic environments. They can expose an algebra slip or a wrong constant; they cannot establish a theorem, and an empirical two-sided coverage figure says nothing about one-sided levels. Every result in `theorems.md` rests on its written proof.

**Re-run status after round 3 (2026-11-15).** `check_attribution.py` (new case (v), review item K1; split renamed "2-for-1", item K2) and `check_cor13.py` (new Part D, review item X7) were modified and re-run from Git Bash with `PYTHONIOENCODING=utf-8`; both exited with code 0. For both, the part of the output that existed before is identical, line for line, to the earlier output (`diff` against copies of the earlier result files; the only differing old lines are the three in which the split is now called "2-for-1" and the block title). No other script was modified or re-run in round 3. After the round-3 split of `setup.md`, references below to "setup" mean the abstract `theory/setup.md`; A-share conventions are in `theory/instantiation_ashare.md`.

**Re-run status after round 2 (2026-11-15).** Only `check_attribution.py` was modified and re-run (review items G3, G4; §3 below). Its simulation output is identical, line for line, to the round-1 output (`diff` against a copy of the round-1 result file); the new block was appended. No other script was modified or re-run in round 2; note that `check_cor13.py` and §5 below still write "P" for what `theorems.md` now calls P_T^D (notation change M4 only).

**Re-run status after round 1.** `check_attribution.py` was modified and re-run. `check_lag_monotonicity.py`, `check_cor13.py`, `check_pinsker_binary.py` are new and were run. `check_thm1_coverage.py` and `check_matured_rate.py` were **not modified and not re-run**; their result files are those of the first run (2026-11-15 01:54).

| Script | Command (from project root) | Output | Run time observed |
|---|---|---|---|
| `check_thm1_coverage.py` | `python theory/checks/check_thm1_coverage.py > theory/checks/results_check_thm1_coverage.txt` | `results_check_thm1_coverage.txt` | ≈ 53 s |
| `check_matured_rate.py` | `python theory/checks/check_matured_rate.py > theory/checks/results_check_matured_rate.txt` | `results_check_matured_rate.txt` | ≈ 33 s |
| `check_attribution.py` (modified in rounds 1, 2 and 3) | `python theory/checks/check_attribution.py > theory/checks/results_check_attribution.txt` (run in rounds 2 and 3 from Git Bash with `PYTHONIOENCODING=utf-8` set) | `results_check_attribution.txt` | ≈ 23 s (round-2 run; round-3 run not timed); exits with code 1 if a required equality of the adversarial cases fails |
| `check_lag_monotonicity.py` (new) | `python theory/checks/check_lag_monotonicity.py > theory/checks/results_check_lag_monotonicity.txt` | `results_check_lag_monotonicity.txt` | a few seconds (not timed); deterministic, no seeds |
| `check_cor13.py` (new in round 1; Part D added in round 3) | `python theory/checks/check_cor13.py > theory/checks/results_check_cor13.txt` | `results_check_cor13.txt` | ≈ 10 s (round-1 run; round-3 run not timed); exits with code 1 if Part D finds an ordering violation for the certified labels |
| `check_pinsker_binary.py` (new) | `python theory/checks/check_pinsker_binary.py > theory/checks/results_check_pinsker_binary.txt` | `results_check_pinsker_binary.txt` | a few seconds (not timed) |

## 1. `check_thm1_coverage.py` — Theorem 1, Corollary 1.1, Proposition 2

Setup: δ = 0.1, M = 10, T = 2000 days, d ∈ {1, 5, 20}, 500 paths × 3 seeds per cell, four environments (independent labels; all labels of a day identical; the block construction of Proposition 2; a block environment in which the loss probability and the number of entries react to past revealed outcomes). 36 cells, 18,000 paths.

- **Coverage.** Theorem 1(a) interval violated at some T on 2 of 18,000 paths (0.2% of paths in 2 cells, 0 in the other 34). Sharpened Theorem 1(b) interval: 5 of 18,000 paths. Lane-level event (the one the proof bounds by δ): 3 paths with b, 7 paths with b*. Allowed: 10% of paths per cell. **No contradiction with the theorem; the bound is very conservative** (empirical error ≤ 0.2% against a nominal 10%).
- **The check has power.** Shrinking the radius b by a factor 0.5 produces lane violations on 5–72% of paths in the correlated environments, and by 0.25 on 89–100%. In the independent-label environment the bound is far from binding (max |deviation|/b ≤ 0.36, and ≤ 0.38 for b*): the range-based radius ignores that independent labels have small variance.
- **Violations exist, as they should:** max |deviation| / b reached 1.074 (b) and 1.120 (b*) on single paths. They are rare events of probability far below δ, not evidence against the proof.
- **Width.** Half-width B_T/N_T at T = 2000 (N_T ≈ 13,000–20,000 trades): 0.055–0.074 for d = 1; 0.143–0.159 for d = 5; 0.299–0.332 for d = 20. This is 2.1–3.1 times sqrt(dM/N_T), and always below the Corollary 1.1 bound (0.068–0.432). With b*: 0.049–0.056, 0.115–0.135, 0.242–0.282 (B*/B between 0.73 and 0.95). **In absolute terms the intervals are wide**: with a 20-day horizon and about 20,000 trades the interval for the loss probability is about ±0.24 to ±0.33.
- **Sawtooth.** The design-notes radius b jumps when a lane's Q crosses a power of two: largest one-day relative increase of B_T/N_T after T/4 was 1.42 (d = 1), 1.08 (d = 5), 1.02 (d = 20). For b* the largest one-day ratio was 1.000 (no upward jump).
- **Effective sample size (Proposition 2).** With n_t = M and p = 1/2 the standard deviation of (ΣX − Σμ)/N times √N was 0.485–0.505 for independent labels (theory 0.5) and 1.54–1.59, 3.53–3.57, 6.98–7.20 for blocks with d = 1, 5, 20 (theory 1.58, 3.54, 7.07). Implied effective sample sizes 1979–2100, 393–401, 96–103 against N/(Md) = 2000, 400, 100.
- **Proposition 2 constants (finite sanity check only).** Exact TV between Binomial(B, 1/2 − h) and Binomial(B, 1/2 + h) was below the Pinsker bound, which was below the proof's bound (1 − 2δ)/2, in all 28 (δ, B) combinations. This does not remove the proof's reliance on Pinsker's inequality; that inequality is now proved in proofs.md §2.3 (see also §6 below).
- **One-sided levels (Theorem 1(c)) are not checked by this script.** It counts two-sided violations only.
- **Upper vs lower bound.** Theorem 1 width / Proposition 2 lower bound in the block environment: 14.2, 17.1, 17.9 (b) and 12.6, 13.3, 14.0 (b*) for d = 1, 5, 20. The gap is constants and logarithmic factors; it is not explained further.
- Hoeffding-lemma grid check: max of ψ(s) − s²/8 was 0.0. Epoch-constant check: relative discrepancy 1.7e-16.

## 2. `check_matured_rate.py` — loss-dependent revelation timing

Setup: d = 10, M = 10 entries every day, T = 800, 2000 paths × 3 seeds; gains revealed after 1 day, losses only after 10 days; δ = 0.05 for Theorem 1; scenarios: constant p = 0.5, and a shift of p from 0.3 to 0.8 at day 400; labels independent or identical within a day.

- **Matured-only rate is biased downward**: bias −0.155 at T = 20, −0.051 at T = 50, −0.012 at T = 200, −0.003 at T = 800 (constant p). After the regime shift the bias re-opens: −0.014 at T = 410 against −0.005 at T = 400. With a stationary flow the bias decays like d/T, so this is a transient / regime-change problem, not a permanent one in this design. I did not test growing trade flow or rolling windows, where it would persist.
- **A naive 95% Wald interval around the matured-only rate** covers r_T^entry at a fixed T with probability 0.02 (T = 20), 0.82 (T = 200), 0.92 (T = 800) with independent labels (constant p), and only 0.25–0.52 across the listed T when a day's labels are identical (both scenarios); it misses at some T on 100% of paths in every scenario (dominated by early T).
- **Theorem 1 intervals (a) and (b)** missed r_T^entry at some T on 0 of 24,000 paths. The deterministic bracket [K/N, (K+P)/N] contained the realised loss fraction on 100% of paths.
- **Price of validity:** the Theorem 1 interval is uninformative ([0,1] on average) until roughly T = 200 (N = 2000 trades) in this configuration, and at T = 800 (N = 8000) is still [0.22, 0.77] around a true value 0.50. Under (a) it also widens back to [0,1] at T = 410 because of the sawtooth; (b) does not ([0.11, 0.88]).

Reading: the matured-only rate is "misleading" here in a specific sense (biased, and its naive interval badly under-covers, especially with within-day dependence), while the Theorem 1 interval stays valid but is wide. The check does not show that the Theorem 1 interval is useful at these sample sizes.

## 3. `check_attribution.py` — Lemma 3

Setup: 50 assets, 500 days, market component ±0.4%/day with a two-state regime, baseline fully invested in 10 names; gated strategy with a 75%-accurate regime signal (exposure 1 or 0.2) and uniformly random stock choice; proportional turnover cost 0.1%; 300 paths × 3 seeds × 3 configurations (baseline never / 20% of days at zero exposure, two fallback conventions for w^B).

**Round-1 correction (review item D7).** The first version computed turnover as |h_t − h_{t−1}|, which treats the price drift of an unchanged share position as trading. Turnover is now |h_t − h_{t−1}∘(1 + x_{t−1})| (new holding minus pre-trade marked holding = shares traded × price; cash return is zero in the toy). The old formula is kept as `turnover_cost_naive` only for the comparison printed at the end. All numbers below are from the re-run.

- **Identity (2) holds to rounding**: max residual 4.4e-16; gross G-vs-reference minus composition term ≤ 2.7e-16; net G-vs-reference identity ≤ 2.7e-16; reference-vs-baseline identity ≤ 3.3e-16.
- **Attribution as expected**: exposure-schedule term +0.393 to +0.406 per path (s.e. ≈ 0.005–0.006); composition term −0.004 to +0.011 (s.e. ≈ 0.007–0.008; largest |mean|/s.e. ≈ 1.45, i.e. indistinguishable from zero); the timing gain is booked under exposure.
- **Cost term is large**: −(C^G − C^B) = +0.151 to +0.281, i.e. 27–41% of Π^G − Π^B in this toy setup comes from trading less. Not planned, but it illustrates why the cost term must be reported separately.
- **Effect of the cost correction**: unit test (one share bought at 100 and held while the price goes 100 → 110 → 121): corrected dollar turnover 100.0, naive 121.0. In the simulation (seed 7) the naive formula gave total costs 0.17–0.20% below the corrected ones for B, G and E; the figures above changed only in the fourth decimal (e.g. Π^G − Π^B for seed 7: 0.6762 before, 0.6770 after). The toy re-draws portfolios daily, so it is a weak test of this correction; the unit test is the relevant evidence.
- **Convention dependence**: on identical paths, two fallback conventions for w^B on zero-baseline-exposure days gave exposure/composition +0.393202/+0.000834 versus +0.395609/−0.001573, with identical sums. The alternative ordering (reference e^B w^G) also satisfies the identity (residual ≤ 4.4e-16) and moves the interaction term (mean +0.004 to +0.008, s.e. ≈ 0.006) between the two terms. In this construction the interaction is small because stock choice is random; it need not be small in general.

**Round-2 addition (review items G3, G4): adversarial accounting cases.** Deterministic, single asset, no random numbers; appended to the same output file. The trade definition tested is the one now in `theorems.md` Lemma 3: s_{t−} = s_{t−1}·φ_t (pre-trade shares after corporate actions), trade_t = (s_t − s_{t−})·p_t, cash distributions booked to the cash ledger. Result of the run: **12 of 12 required equalities hold ("ALL PASS")**.

- **(i) Cash dividend, no trade** (1 share bought at 100; dividend 1; ex-dividend price 99). Required dollar trade in period 2: 0. Share-based definition: +0.000000. Return shortcut with the ex-distribution price return (−1%): +0.000000. Return shortcut with the dividend-inclusive total return (0%): **−1.000000** — the spurious sale the reviewer pointed out, i.e. the error of the round-1 formula. Distribution booked to cash: 1.000000; wealth change minus h·(total return): 0.000000.
- **(ii) 2-for-1 split, no trade** (1 share at 100 becomes 2 shares at 50; share multiplier 2. Rounds 1–2 called this "1-for-2", which is the name of a consolidation — review item K2; the arithmetic is unchanged). Required: 0. Share-based definition with s_{t−} = s_{t−1}·φ_t: +0.000000. Shortcut with the split-adjusted price return (0%): +0.000000. Share difference without the corporate-action update: **+50.000000**; shortcut with the raw price ratio (−50%): **+50.000000** (both wrong, shown for contrast).
- **(iii) Controls** — a genuine trade on the corporate-action date is still reported: dividend plus purchase of one more share at 99 → +99.000000; split plus sale of one of the two post-split shares at 50 → −50.000000.
- **(iv) Slippage counted once** (benchmark 100, execution 101, end price 110, fee 0.10; true wealth change 8.900000): convention A (execution-price accounting, C = explicit fee) and convention B (benchmark-price accounting, C = fee + shortfall) both differ from it by 0.000000; the inconsistent mixture differs by **−1.000000**.

**Round-3 addition (review item K1): case (v), wealth change versus Π with a non-zero cash return.** Wealth is produced by an explicit cash-and-shares ledger (cash pays for trades at execution prices, is debited the fee either at the trade or at the end of the period, and earns ρ_t), not by either formula. Result of the run: **21 of 21 required equalities hold ("ALL PASS")** — the 12 of round 2 plus 9 new ones.

- **Reviewer's counterexample** (cash 100, charge 1 at the start of the period, cash return 10%, no risky holdings): terminal wealth from the ledger 108.900000 (required 108.9); wealth change 8.900000; Π = −1.000000; wealth change − [Π + Σ ρ_t (W_t − c_t)] = 0.000000 (the corrected formula now in `theorems.md` Lemma 3). The round-2 formula Π + Σ ρ_t W_t gives **9.000000**, i.e. it is off by 0.1, as both reviewers said.
- **Same example with the charge debited at the end of the period:** wealth change 9.000000 = Π + Σ ρ_t W_t (residual 0.000000). So the round-2 formula is the end-of-period formula.
- **Multi-period case** (8 periods, 3 assets, random prices and holdings, fees in [0, 0.5], execution prices within 0.2% of the benchmark, ρ_t ∈ [0, 2%], initial cash 300; its own generator, seed 2026): wealth change 15.132843, Π = −10.465308, Σ ρ_t W_t = 25.620576, Σ ρ_t c_t = 0.022425. Residual of the corrected formula: 0 within the tolerance 1e-9. Residual of the round-2 formula: −0.022425 (= −Σ ρ_t c_t). With fees at the period end and no shortfall: residual of Π + Σ ρ_t W_t is 0. With ρ = 0: wealth change − Π = 0.
- Limits: one hand example and one random instance; no distributions in case (v); mixed payment timing not tested. The required values were written into the script before the run; nothing was changed after seeing the output.

What this is and is not (cases (i)–(iv)): four hand-sized cases in which the expected values were worked out by the author by hand; they test that the definitions behave as intended on the reviewer's examples. They are not evidence that an experiment pipeline handles real corporate-action data correctly, and rights issues or other non-standard actions are not covered.

## 4. `check_lag_monotonicity.py` — is the radius monotone in the lag d? (review item D1; now setup §4)

Deterministic. Recomputes b, b*, B_T, B*_T from the definitions for a given entry schedule and several d.

- **The reviewer's counterexample is reproduced exactly.** T = 4, one entry on day 1 and one on day 4, δ = 0.05: B_T = 4.418021 for d = 2 (lane clocks [1, 1]) and 3.652803 for d = 3 (lane clocks [0, 2, 0]); these equal the closed forms 2√log(4c₀/δ) and √(2 log(24c₀/δ)). B*_T: 3.313516 and 2.298955. For d = 1 and d = 4: B_T = 3.338525 and 4.721387. So the radius is **not** monotone in d.
- **Caveat about that example.** N_T = 2, so B_T/N_T > 1 for every d and both clipped intervals are [0,1]. It shows non-monotonicity of the radius, not two different intervals.
- **Example with different, unclipped intervals.** Entries only on days t ≡ 1 (mod 3), 10 per day: at T = 3000 (N_T = 10,000) B*_T/N_T = 0.10304 (d = 2), 0.07468 (d = 3), 0.14961 (d = 4), 0.10833 (d = 6); at T = 30,000: 0.03282, 0.02375, 0.04767, 0.03446. The larger lag d = 3 gives the narrower interval because it puts all entry days into one lane.
- **Ordinary case** (10 entries every day): the radius increases with d over d ∈ {2, 3, 4, 6, 11, 21}; B*_T(d)/B*_T(2) is 1.26, 1.45, 1.82, 2.51, 3.53 at T = 3000 and 1.23, 1.45, 1.78, 2.46, 3.48 at T = 30,000, against √(d/2) = 1.22, 1.41, 1.73, 2.35, 3.24 (within 9% and 8%, always above). For B_T the sawtooth makes the ratio erratic (B_T/N_T = 0.02261 at d = 2 and 0.02432 at d = 3 for T = 30,000).
- **Brute force**, all 255 non-empty schedules n ∈ {0,1}^8: B_T(d+1) < B_T(d) for 0, 13, 19, 37 schedules when d = 1, 2, 3, 4 (B*_T: 0, 7, 19, 37).

Reading: a larger valid lag keeps coverage but the computed radius is not monotone in d; the statement "over-stating d only widens the interval" in the first draft of setup.md was false and has been replaced.

## 5. `check_cor13.py` — Corollary 1.3 (bracket labels; status `草稿`)

*Round-3 note.* Corollary 1.3 now defines the bracket labels through a certification indicator V (review item X7). **Parts A–C below simulate complete records, i.e. V = "sold by the deadline"; they were re-run in round 3 with identical output and do not exercise missing records.** In them "P" is what `theorems.md` calls P_T^D, and the docstring's "A4'" is A4-D. Missing records are covered only by Part D.

Part A. δ = 0.1, M = 10, H = 1, D = 5 (d_D = 6), T = 1500, 400 paths × 3 seeds × 4 cells. A two-state regime known at entry; a bad-day shock not known at entry and shared by the day's entries; each entry is unsold at its deadline ("stuck") with probability 2% / 25% (good / bad day; "moderate") or 30% / 60% ("heavy"); loss probability 35% / 70% if sold by the deadline, 60% / 90% if stuck (this includes never-liquidated positions, labelled 1 by the completion convention); within-day dependence "shared" (conditionally independent given the shock) or "identical" (all entries of a day share the draws). The pair (L^lo, L^hi) is revealed one day after the sale if sold by the deadline and at t + D + 1 if stuck (outcome-dependent revelation, common revealed set J_T). n_t depends on the pairs revealed in the last 20 days and on fresh randomisation. μ^liq_t is known in closed form, so r^liq_T is computed exactly.

- **Coverage.** The interval [max{0,(K^lo − B*)/N}, min{1,(K^hi + P + B*)/N}] missed r^liq at some T on **0 of 4800 paths**; upper-side misses 0, lower-side misses 0. Allowed: 10% per cell, 5% per side. No contradiction; very conservative.
- **Power of the check is limited.** Radius × 0.25: misses on 0–1.25% of paths per cell. Radius × 0 (accounting bracket only): 2.3–2.5% (heavy, shared), 28.5–30.3% (heavy, identical), 45.5–49.8% (moderate, shared), 89.0–92.3% (moderate, identical). So the check would catch a radius that is far too small, not a moderately wrong constant.
- **Ignoring stuck positions fails when many are stuck.** The interval that uses K^lo on both sides (stuck = not a loss) missed on 100% of paths in the heavy setting (r^lo ≈ 0.26 against r^liq ≈ 0.58) and on 0% in the moderate setting (r^lo ≈ 0.41, r^liq ≈ 0.51, radius ≈ 0.17: the bias is hidden by the wide radius).
- **Pathwise facts.** No violation of X^lo ≤ X^liq ≤ X^hi; min over paths and T of width − (K^hi − K^lo)/N_T was +0.24 to +0.34 (≥ 0 as claimed).
- **Widths at T = 1500.** Moderate: N_T ≈ 8500, interval ≈ [0.24, 0.69] around r^liq ≈ 0.51, deadline-unsold share (K^hi − K^lo)/N_T ≈ 0.107, B*/N ≈ 0.169. Heavy: N_T ≈ 5500–6100, interval ≈ [0.10, 0.84] around r^liq ≈ 0.58, share ≈ 0.417, B*/N ≈ 0.153–0.162. **These intervals are wide.**

Part B (deterministic; one entry per day, only the first misses its deadline, d = 6, δ = 0.1): (K^hi − K^lo)/N_T = 1/T; width 0.5618, 0.1744, 0.0560, 0.0179, 0.0058 at T = 10², 10³, 10⁴, 10⁵, 10⁶. The deadline-unsold part vanishes when only finitely many entries miss the deadline.

Part C (deterministic; every 5th entry misses its deadline): share → 0.2; width 0.7318, 0.3714, 0.2557, 0.2178, 0.2058 — stays above 0.2, as the conditional persistence statement says.

Part D (round 3; deterministic enumeration of the 16 combinations of: sold by the deadline, record complete at the finalisation day, sale at a loss, value of L^liq if not sold by the deadline). Certified labels (V = sold × complete, L^lo = V·loss, L^hi = 1 − V(1 − loss)): **0 of 16 states violate L^lo ≤ L^liq ≤ L^hi**, and L^hi − L^lo = 1 − V in all 16. A "missing record ⇒ loss in both labels" fallback violates the ordering in **4 of 16** states: the two with a sale at a profit and a missing record (L^lo = 1 > L^liq = 0, the reviewer's counterexample) and the two with an unsold position, a missing record and L^liq = 0. This is a check of two-line algebra (proofs.md §1.8 Step 0); it says nothing about whether real records satisfy the assumption CERT.

Not checked: any statement about identifiability; environments in which A3 fails for the bracket labels; a simulation with randomly missing records; violations of CERT.

## 6. `check_pinsker_binary.py` — the two steps of the Pinsker proof in proofs.md §2.3

- kl(x,y) − 2(x−y)² on a 2001 × 2001 grid of (0,1)²: minimum 0.0, no grid point below −1e-12; min of 1/(x(1−x)) on the grid = 4.000000.
- 3 seeds × 20,000 random pairs of distributions on finite sets (2–11 points), A = {p > q}, x = P(A), y = Q(A): min[KL − kl(x,y)] = −1.8e-15 (rounding; equality holds for two-point sets), max|TV − (x − y)| = 3.9e-16, min[KL − 2TV²] = +6.3e-11 (> 0).

A grid cannot prove an inequality; the proof is the analytic argument in proofs.md.

## Failures, oddities, limits

- No violation of any proved statement was found.
- Theorem 1 is far from tight in these simulations (empirical error ≤ 0.2% vs δ = 10%; width 12–18 times the lower bound).
- The sawtooth of the design-notes radius was discovered by this check and led to the added Theorem 1(b).
- Corollary 1.3 has a check (§5); it is conservative and has limited power, its simulation covers complete records only, and the corollary remains `草稿`.
- Round 3: the wealth formula of Lemma 3 for a non-zero cash return in rounds 1–2 was wrong for costs debited at the trade (off by Σ ρ_t c_t; §3, case (v)). The simulations above use a zero cash return and were not affected.
- Theorem 1(c)'s per-side level δ/2 is not checked by the Theorem 1 scripts; Corollary 1.1(b) has no dedicated check.
- The corrected cost formula barely changes the attribution toy (§3); that toy is not a strong test of the correction.
- `check_lag_monotonicity.py` confirmed that a statement in the first draft of setup.md was false (§4).
- These are a few hand-picked synthetic environments; they cannot establish validity, only fail to refute it.

## History

1. First run used only the design-notes radius b. After seeing the sawtooth in `check_matured_rate` (interval reverting to [0,1] at T = 410), b* was derived (proofs.md §1.5) and added as extra columns; the b columns and all seeds were left unchanged and reproduce the first run exactly.
2. The loop bound in `b_star` was reduced from a fixed 40 to ⌊log₂ max Q⌋ + 2 (exact, see comment in the code) to bring run time from several minutes to under a minute; outputs before and after were compared with `diff` and are identical.
3. (Round 1, D7) `check_attribution.py`: turnover formula corrected to subtract pre-trade marked holdings; naive formula kept for comparison; unit test added; re-run. Seeds and all other settings unchanged.
4. (Round 1, D1) `check_lag_monotonicity.py` added and run once; no parameter was changed after seeing output.
5. (Round 1, C2–C4, D14) `check_cor13.py` added and run once with the parameters fixed in advance; no parameter was changed after seeing output.
6. (Round 1, D9) `check_pinsker_binary.py` added and run once.
7. (Round 1) `check_thm1_coverage.py` and `check_matured_rate.py` untouched; not re-run.
8. (Round 2, G3, G4) `check_attribution.py`: added `adversarial_cases()` (dividend, split, controls, slippage) and `import sys`; the script now exits with code 1 if a required equality fails. Run once; the cases and their required values were written before the run and nothing was changed after seeing the output. Simulation code, seeds and settings unchanged; simulation output identical to round 1.
9. (Round 3, K1, K2) `check_attribution.py`: added case (v) inside `adversarial_cases()` (explicit ledger; reviewer's example; one multi-period instance with its own generator, seed 2026); `check()` got an optional tolerance argument (1e-9 for the ledger cases, 1e-12 as before elsewhere); the split in case (ii) and in the controls renamed "2-for-1". Run once; required values written before the run; nothing changed afterwards. Simulation code, seeds and settings unchanged; simulation output identical to rounds 1–2.
10. (Round 3, X7) `check_cor13.py`: added `part_d()` (enumeration) after Parts A–C; `main()` exits with code 1 if the certified labels violate the ordering. Run once. Parts A–C code, seeds and output unchanged.
11. (Round 3) `check_thm1_coverage.py`, `check_matured_rate.py`, `check_lag_monotonicity.py`, `check_pinsker_binary.py` untouched; not re-run.

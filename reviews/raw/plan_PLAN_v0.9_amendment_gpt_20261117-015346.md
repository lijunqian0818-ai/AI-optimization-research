**Recommendation: major revision before freezing the plan.** This is a credible design for a narrowly scoped empirical comparison, but baseline fairness and inferential validity are not yet established. It does **not** test whether abstention generally works, whether Z contains incremental information, or whether the stated theorems hold.

The strongest improvements are SCORE as a primary comparator, matched daily submission counts, NET-K as an objective-aligned alternative, explicit disclosure of pilot adaptation, and unconditional hold-out reporting. Reusing development data is not itself fatal: the unopened hold-out can support confirmation of a fully frozen procedure.

This review covers the supplied amendment and pilot summary. The referenced v0.8 procedures, theorem statements, search spaces, and implementation are not supplied, so their adequacy remains unverified.

## Issues ranked by severity

### 1. Critical: the sampling target and bootstrap validation are not sufficiently aligned

**References: A4.1, A6–A8.**

The experiment evaluates annually refitted policies across approximately 4.5 hold-out years, while inference resamples daily outcomes of already fitted policies. That can be a reasonable approximation under suitable dependence assumptions, but it does not automatically quantify uncertainty for the full training-and-deployment procedure.

Two unresolved questions matter:

- Is the target performance conditional on the particular fitted models, or expected performance over alternative training histories?
- Under changing annual means, is the target the average of the realized annual regimes or an expectation over future regimes?

Synthetic scenario (d) exposes this ambiguity. If annual mean shocks are random and the target is the unconditional mean, they create dependence on a roughly annual scale. Blocks averaging 24 days may badly understate uncertainty. If the target conditions on those realized shocks, coverage must instead be evaluated against the corresponding realized average.

**Required revision:** define the target explicitly, calculate each simulation’s truth accordingly, and validate the actual numerator/denominator estimator with annual refits, varying counts, and P3’s shorter observation window. A generic vector of daily contrasts does not cover all these features.

Bonferroni is not a general fallback for this problem: it adjusts multiplicity but retains the same potentially incorrect standard errors and normal approximation.

### 2. Critical: point-in-time validity remains an outstanding prerequisite

**References: A2.1, A7, A8; pilot §6 and §9.7.**

A chronology assertion in a code header and one return-feature correlation check are insufficient. The amendment appropriately requires an audit, but until that audit passes, neither baseline fairness nor causal ordering is established.

The audit needs to cover:

- Monthly liquidity screening using only information available at selection time.
- Historical eligibility, listing/delisting status, and the construction date of the code universe.
- Publication availability and revisions for **Z_H as well as Z_O**.
- Corporate-action adjustments, suspensions, price limits, and terminal/delisting returns.
- Nested chronology: tuning, base out-of-sample predictions, gate labels, and annual refits.

Excluding INS helps, but an event date plus a fixed lag does not establish that every other historical field existed in its present form at that time. Including delisted names also does not, by itself, eliminate historical universe bias.

**Required experiment:** a future-data perturbation test—changing observations after a decision cutoff must leave earlier features, nominations, selected configurations where applicable, and decisions unchanged.

### 3. High: the baseline set is sensible, but fair tuning has not been demonstrated

**References: A2.2, A4.1, A7.**

SCORE is a strong operational baseline. NET-K is an important addition. However, “30 trials each” is not enough to establish tuning fairness: search-space quality, validation dates, early stopping, objective, and available training rows all matter.

The pilot base predicts within-day return ranks; the primary endpoint is net standard-order return. If base tuning remains RankIC-based while gates are tuned directly on \(V\), SCORE may be disadvantaged for the endpoint being judged. This is acceptable for the narrow question “can a gate improve this particular base?”, but weaker evidence for the value of a separate gating stage.

**Missing comparisons:**

- A direct ranking/return model selected for the same net-value endpoint and submission count, with comparable tuning resources.
- A simple regularized reranker using base score and a small set of existing controls, such as volatility and liquidity. LOSS-LR partially addresses this, depending on its inputs and tuning.
- An explicit paired **NET-K versus LOSS** contrast. P4 versus SCORE does not by itself identify why P1 succeeds or fails.

Print the proposed tuning matrix before declaring fairness. Also resolve whether “mean over tuning years” means an equal-weight average of annual ratios or a pooled order-weighted ratio; they differ when counts vary.

### 4. High: the study is unlikely to resolve economically small differences

**References: A4.1, A5, A6.**

The amendment correctly acknowledges the power problem. Accepting it does not remove its scientific consequence: a likely result is eight inconclusive comparisons, especially for P1 and P4.

For illustration, with \(q=2.7\) and SE \(=3.0\)–\(3.8\) bp, an observed estimate must exceed roughly **13.1–15.2 bp** to be classified materially beneficial. Under a simple normal approximation, achieving 80% probability of that classification requires a true effect of roughly **15.6–18.4 bp**. These are illustrative calculations, not substitutes for A6.

Also, **“with eight contrasts, \(q\) is about 2.7 or more” is not a mathematical lower bound**. Strongly correlated contrasts can yield a substantially smaller max-statistic critical value.

**Required revision:** report minimum detectable effects separately for detecting a nonzero effect and establishing an effect beyond Δ. Keep Δ fixed, but present this as an estimation study if the planned precision cannot answer the main economic question. Do not use the unadjusted TOST as a fallback headline.

### 5. High: the primary metric supports selection-value claims, not the original “lose less often” claim

**References: A3, A4.3 item 0, A5.**

Mean net return per submitted order is appropriate for comparing count-matched selection policies. Counting unfilled orders as zero is coherent for that estimand.

But it can improve through changes in fill probability, win magnitude, or loss magnitude without reducing loss frequency. Conversely, LOSS can reduce loss frequency while reducing mean returns. Adding NET-K makes this tension visible; it does not resolve it.

The filled-order loss share is also **policy-dependent conditioning**: different policies select different filled populations. It is useful descriptively, but a lower value does not establish lower risk for the same underlying opportunities.

**Missing report:** show, together, per-submitted-order probabilities of no fill, filled loss, and filled non-loss, plus conditional win/loss magnitudes and the filled-order loss rate. For tail means, report effective support and concentration by date/year.

Keeping these endpoints secondary is defensible only if the main claim remains mean selection value. Abstract placement must preserve their exploratory status.

### 6. High: the economic bound has an incomplete deployment interpretation

**References: A3.3, A5; pilot §9.2.**

Equal submission counts do not guarantee equal capital usage, turnover, fill rates, or holding durations. The deployment bridge helps, but checking these quantities is not the same as proving the conversion from 4.96 bp/order to 1% annual capital return.

The pilot itself illustrates the distinction: −6.07 bp/order maps to about −1.2 percentage points of deployed AR, with a different uncertainty conclusion.

**Required revision:** retain Δ as the user’s order-level materiality judgment, but make its capital interpretation explicitly conditional. Provide a reconciliation between standard-order value and deployed return explaining discrepancies. Ensure the inherited fill and cost sensitivities address adverse execution conditions for the names gates actually select, rather than only uniform cost shifts.

### 7. Moderate–high: Z comparisons test a particular learning procedure, not information content

**References: A4.1 P2/P3, A4.3 items 6–7.**

The permutation caveats are good. Nevertheless:

- A null P2/P3 does not show that Z lacks useful information.
- A positive P2/P3 establishes value for this feature representation and training procedure, not a participant-information mechanism.
- A fixed base(−Z) nomination stage can exclude the opportunities where Z would matter most.

If broader claims about Z are intended, add a matched-budget **base(+Z)** experiment that allows Z to affect nominations. Otherwise explicitly limit the claim to reranking the base(−Z) nominations.

The shuffle specification also needs clarification. Moving rows jointly preserves the group’s internal structure and columnwise missingness frequencies, but generally **does not preserve each name’s missingness pattern**. State which meaning is intended. Independent Gaussian noise does not match sparse, missing, temporally persistent event features; it is only a generic nuisance-feature control.

The event decomposition is an exact accounting identity, not an event effect. Names without recent events can still contribute through selection displacement or older Z features.

### 8. Moderate: the simulation acceptance rules are too loosely justified

**Reference: A6.**

A 93.5% acceptance threshold permits meaningful undercoverage relative to nominal 95%. At 2,000 independent replications, the Monte Carlo SE near 95% coverage is about 0.49 percentage points; a 1.5-point margin is not simply an innocuous rounding allowance.

Other omissions include:

- Classification errors near the boundaries, such as true effects just outside ±Δ.
- Wrong-direction material-benefit/harm declarations.
- Stronger or longer-lived dependence and abrupt mean shifts.
- A precise definition of “family-wise error” distinct from simultaneous noncoverage.

**Required revision:** justify the allowed coverage shortfall scientifically, report binomial Monte Carlo intervals, and add boundary scenarios. If the rule is revised after failing validation, evaluate the revised rule on fresh simulation draws.

### 9. Moderate: external validity is narrow, and theory validation remains separate

**References: A8, A11.**

The convenience population is acceptable for a clearly scoped study. It cannot support A-share-wide conclusions. Annual diagnostics are helpful; exploratory board and liquidity breakdowns with support counts would further describe where results arise, without pretending to provide independent replication.

A11 correctly states that P1–P4 do **not** test the theorems. Consequently:

- **Theorem 1:** empirical interval width is not coverage validation. Its separate synthetic protocol should test simultaneous coverage over time, adaptive selection, allowed cross-name dependence, and the exact delay assumptions. Compare width and stopping behavior against applicable established confidence-sequence methods if usefulness is claimed.
- **Proposition 2:** requires a proof; simulations can illustrate tightness, not establish the lower bound.
- **Lemma 3 and the accounting identity:** algebra and reconciliation tests are appropriate. They do not establish economic mechanisms.

Without the theorem statements and v0.8 §12.1, I cannot approve the claimed theorem-validation coverage.

## Minimum additions before opening the hold-out

1. Complete the point-in-time and nested chronology audits.
2. Define the inferential target and validate the actual estimator under annual refitting and nonstationarity.
3. Establish endpoint-aligned tuning fairness and add the direct NET-K–LOSS comparison.
4. Add the fill/loss/win decomposition and an explicit order-value-to-deployment reconciliation.
5. Finalize simulation acceptance criteria, boundary scenarios, and all placeholders.
6. Freeze claims narrowly enough that inconclusive contrasts, exploratory loss metrics, and supporting theory cannot be promoted into stronger conclusions afterward.

**Verdict:** the baselines and metrics are substantially improved and appropriate for a narrow policy comparison. Fair tuning, valid uncertainty, and historical data availability remain the main approval blockers. The plan’s strongest defensible contribution is a transparent estimate of how specified gates perform against SCORE on this population—not a general verdict on abstention or participant information.

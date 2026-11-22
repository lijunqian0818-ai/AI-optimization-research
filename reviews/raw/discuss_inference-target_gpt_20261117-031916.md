**Route C is a coherent target, and I would accept it as an assumption-dependent analysis—but not with (S) as currently written.** Short memory alone does not justify the proposed bootstrap, especially with annual refitting, changing training-set sizes, and a fixed block length. Those are substantive gaps, not merely limitations to acknowledge.

I am responding to the discussion and amendment excerpts supplied here; the full amendment was not included.

### 1. Route C needs assumptions about both dependence and nonstationarity

The unconditional target solves the earlier mismatch. Define, for each contrast and its evaluation window,
\[
\theta_{j,n}
=\frac{\sum_{t\in T_{j,n}}E[D_{jt}]}
       {\sum_{t\in T_{j,n}}E[S_{jt}]}.
\]
This is a deterministic, finite-window target under a specified law for the procedure and data.

However, **“the whole pipeline is a weakly dependent process” does not follow from weak dependence of market returns.** A fitted model reused for a year can induce persistent dependence in its performance. Expanding training windows can also produce systematic changes in expected performance. These effects remain possible without an annual market regime.

There is a second issue: short dependence does not imply constant means. Even independent observations with deterministic changing means can defeat a stationary bootstrap for the finite-window unconditional target. Resampling dates turns a fixed temporal composition into random composition. That can introduce spurious uncertainty; it need not produce understatement.

Consequently, I would replace (S) with explicit assumptions along these lines:

- **Mean structure:** the relevant daily policy totals have stable unconditional means, or deviations from a specified stable mean structure are asymptotically negligible for the estimator and variance estimator.
- **Dependence and moments:** the joint series satisfies conditions supporting a multivariate CLT and consistent long-run covariance estimation. State an actual sufficient framework, such as stationary strong mixing with suitable moment and mixing-rate conditions, rather than “decays within a range.”
- **Denominators:** expected orders per day stay positive, and observed totals concentrate appropriately.
- **Nondegeneracy:** the primary studentized contrasts have positive limiting variance.
- **Tuning:** bandwidths or expected block lengths obey appropriate asymptotic growth conditions, rather than remaining fixed as the sample grows.

Strict stationarity of the complete pipeline is a strong assumption here. An alternative is asymptotic equivalence to a stationary process, but **whether annual refitting in this application satisfies such an approximation is UNVERIFIED**. Calling it an assumption is acceptable; implying that purge, embargo, or predictability establishes it is not.

A precise theorem-shaped claim would be:

> For a fixed family of contrasts, assume a joint CLT for the centered numerator and denominator totals, positive limiting denominator means, and conditional consistency of the chosen bootstrap for those centered totals. If the limiting standardized maximum has a continuous distribution and studentization is consistent, the bootstrap max-statistic intervals have asymptotic joint coverage \(1-\alpha\) for \(\theta_{j,n}\).

That identifies what must be justified. It does not prove that your implementation satisfies it.

**My recommendation is conditional acceptance of C:** use it if the paper explicitly accepts a stable-process approximation for the deployed procedure. If the paper needs arbitrary annual mean changes to be part of its core interpretation, use B or develop a method for that nonstationarity.

### 2. Change the uncertainty wording

I would not write:

> “They quantify day-level sampling variability and do not include regime-level uncertainty.”

For the unconditional target, random regimes are part of sampling variability. The procedure either accounts for them adequately or lacks a coverage justification. They are not a separately excluded uncertainty component while retaining the same unconditional target.

Use instead:

> We report simultaneous nominal 95% intervals calibrated under a stable, short-memory model for the joint daily policy totals. Coverage is asymptotic and depends on this model and the resampling conditions. Persistent regime variation or persistent effects of annual refitting can invalidate coverage. These intervals do not establish performance under a different future data-generating process.

Your diagnostics are useful sensitivity analyses, but cannot validate the assumption. Also, “year as resampling unit” is **not necessarily pessimistic**: with four or five years it can miss variation, underestimate uncertainty, or simply behave erratically. Call it an annual-block resampling sensitivity, without a conservativeness claim.

Pre-specify one primary calibration and its tuning rule. Do not select the primary bandwidth or block length based on which intervals look most plausible.

### 3. Ratio of expectations, counts, and seeds

The ratio of expectations is sensible for fixed-coverage re-ranking. Its interpretation is **expected aggregate incremental return divided by expected aggregate orders** over repeated executions of the specified window.

It differs from
\[
E\left[\frac{\sum_tD_{jt}}{\sum_tS_{jt}}\right],
\]
which weights each generated history equally. Your target instead gives greater weight to histories with more orders. Neither is universally preferable, but the former matches a per-order aggregation objective.

Random denominators require an important change to the variance calculation. Writing
\[
A_{j,n}=\sum_tD_{jt},\qquad B_{j,n}=\sum_tS_{jt},
\]
gives the exact identity
\[
\widehat\theta_j-\theta_{j,n}
=
\frac{\sum_t(D_{jt}-\theta_{j,n}S_{jt})}{B_{j,n}}.
\]
The numerator on the right has **zero aggregate expectation**, though its daily expectations need not individually vanish.

Thus HAC must use the joint numerator–denominator process, equivalently the ratio influence series
\[
D_{jt}-\widehat\theta_jS_{jt},
\]
with appropriate normalization and mean treatment. Using the long-run variance of \(D_{jt}\) alone generally misses denominator variation and covariance. A paired bootstrap that recomputes the ratio addresses the algebra, subject to its validity assumptions.

For five seeds, choose one estimand explicitly:

- **Fixed five-seed procedure:** condition on the pre-specified seeds, average daily numerators across their runs, and infer over market histories. This is my preferred primary definition.
- **Random-training procedure:** average over both market histories and algorithmic randomness. Five fitted runs do not automatically make a date bootstrap valid for this broader target; seed effects can persist throughout the window.

If counts are identical across seeds, averaging the five ratios equals taking the ratio after averaging numerators. Otherwise they differ. Do not treat seeds as five independent market histories.

Also specify whether expectations condition on the pre-hold-out development data and frozen design decisions. I recommend that they do. “Unconditional” can then mean unconditional over the subsequent hold-out evolution, including its annual refits, relative to that fixed starting information.

### 4. Two corrections to the simulation plan

Your revised Monte Carlo acceptance rule is appropriate: pass a pre-specified valid-model scenario only when the one-sided 95% exact binomial upper bound on simultaneous noncoverage is at most 6%. Distinguish individual scenario bounds from a simultaneous statement across scenarios, and allow an inconclusive result.

But two details matter.

**First, the \(a=1\) counterexample is short-memory yet degenerate.** At \(a=1\),
\[
D_t=\varepsilon_t-\varepsilon_{t-1},
\qquad
\widehat\theta=\frac{\varepsilon_n-\varepsilon_0}{n},
\]
so the usual positive-variance \(\sqrt n\) approximation fails. Block boundaries can dominate bootstrap fluctuations. Keep it as a boundary diagnostic, but do not place it inside a gate justified by a nondegenerate CLT. Near-one values are valuable finite-sample stress tests.

**Second, unconditional simulation truth must average over histories.** For the fixed starting configuration, estimate
\[
\theta_{j,n}
=\frac{E[A_{j,n}]}{E[B_{j,n}]},
\]
not the average of replication-specific ratios or conditional targets. Use analytic truth where possible; otherwise use an independent, sufficiently large truth simulation and quantify its error.

Add an explicit test of the missing assumption: independent observations with deterministic annual mean changes. This distinguishes nonstationarity failure from dependence failure. Also test persistent fitted-model effects under otherwise short-memory market data. Annual random means alone do not cover that mechanism.

### 5. SCORE-V: retain the fixed-nomination comparator, but rename it accurately

I agree with keeping nominations frozen for the primary comparison. I disagree with replacing that comparator with one that changes nominations: under D9, that would answer a different primary question.

Your proposed SCORE-V is sensible, but it is no longer simply “the base predictor retuned on \(V\).” Training on nomination rows changes its training population. A clearer definition is:

> **SCORE-V:** the base predictor’s model class and base-feature set, fitted on historically out-of-sample nominated rows, with hyperparameters selected by pooled validation \(V\) over the same fixed nomination sets and submission counts, using 30 trials.

Specify the training loss separately from the hyperparameter-selection criterion. “Selected on \(V\)” does not necessarily mean “trained with a ranking objective.” If \(V\) is a portfolio return criterion, call it that.

Whether this duplicates NET-K is **UNVERIFIED without the full model definitions**. Based on your description, there is a potentially meaningful distinction:

| Comparator | Main information supplied |
|---|---|
| SCORE-V | Raw base features |
| NET-K(-Z) | Base-score rank plus specified controls |

That is a comparison of representations and learning procedures under common opportunities. It is not a clean isolation of the benefit of the \(V\) objective if other ingredients differ.

Before freezing twelve contrasts, check whether the two implementations actually differ in inputs, model class, loss, or training rows. If they are identical except for their names, remove the duplicate. Equal trial counts are useful budget matching, but report compute as well.

An end-to-end base predictor retuned on \(V\), allowed to change nominations, would be a useful **secondary** comparator. It should not replace the fixed-nomination baseline.

### 6. If you choose B, the headline table is straightforward

Use one row per pre-specified contrast, with:

- base and evaluation window;
- common submitted-order count;
- realised paired difference in basis points per order;
- the pre-specified \(\Delta\) reference.

Use a companion plot for annual realised differences and a separate seed-sensitivity display. Any resampling spread belongs in a clearly labelled sensitivity analysis, without “95% confidence” or simultaneous-coverage language. This would require explicitly revising the interval commitment.

**(1) Points of agreement:** Route C has a coherent target; paired ratio resampling is directed at the right quantity under suitable assumptions; the revised Monte Carlo rule is sound; frozen-nomination SCORE-V belongs in the primary fixed-coverage study.

**(2) Open disagreements:** (S) alone is insufficient; persistent refit effects matter alongside market regimes; arbitrary annual mean variation is not covered by short memory; annual-block sensitivity is not necessarily pessimistic; five seeds do not automatically support inference over training randomness.

**(3) What I recommend next:** Adopt C only with explicit stability, dependence, denominator, nondegeneracy, and tuning assumptions. Fix the conditioning convention and five-seed estimand, define SCORE-V’s training loss and inputs, and add nonstationary-mean and persistent-refit simulation cases. If the stable-process approximation is not defensible for the intended scientific claim, make B the headline analysis.

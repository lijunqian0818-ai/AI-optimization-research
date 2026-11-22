I support the methodological pivot, but **the current evidence identifies an inadequate inference grid, not yet a new inferential problem**. S2 is a particularly clear example: the grid excludes the bandwidths and prewhitening that its persistence calls for. Failure of that grid cannot support a claim that existing methods fail.

My preferred core would be **an estimand-aware analysis of when resampling realized policy outcomes captures—and misses—uncertainty from policy refitting**. Ratios, overlapping returns, and simultaneous intervals should be components of that analysis, not individually advertised as novelties.

I am treating the supplied notes as reported results, not independently verified computations. Literature connections below are leads; their precise applicability and priority are **UNVERIFIED**.

## 1. What is known, and what could remain open?

The following are established problem classes:

| Feature | Existing conceptual treatment | Implication for our claim |
|---|---|---|
| Ratios with denominators bounded away from zero | Smooth-function/delta-method inference and bootstrap | “Our estimand is a ratio” is insufficient novelty |
| Five-day overlapping returns | Serial-correlation-robust inference | Holding-period overlap itself is not an open problem |
| Short-bandwidth HAC under persistent dependence | Bandwidth selection, prewhitening, fixed-bandwidth asymptotics | S2 largely demonstrates a known failure mechanism |
| Several correlated contrasts | Joint Gaussian approximation, simultaneous bootstrap inference | Twelve contrasts do not by themselves create a new theoretical regime |
| Noisy studentization | Bootstrap-t and higher-order inference | Improving the old fixed-standardization rule is necessary validation |
| Estimated forecasting/trading rules | Inference with estimation effects and forecast comparison | Refitting uncertainty has substantial prior literature |
| Simulation screening | Simulation studies and independently validated procedure selection | Preregistration improves credibility, but does not establish population coverage |

Additional literature leads worth checking are West on inference for predictive ability, Giacomini–White on conditional predictive ability, and Ibragimov–Müller on grouped \(t\)-statistic inference. Their applicability to our particular training windows, targets, and ratio contrasts is **UNVERIFIED**. Do not exclude relevant foundational papers merely because they lack a simulation section; the draft’s exclusion rule could remove the theory against which novelty must be assessed.

The potentially interesting question is narrower:

> When does resampling daily outcomes from a learned, periodically refitted policy consistently estimate uncertainty about the performance of the learning procedure, and when does it estimate uncertainty about a different target?

That question is not answered merely by saying “use blocks.” Its novelty in this precise setting is **UNVERIFIED**, but it is a stronger direction than another demonstration of HAC undercoverage.

### First distinguish three targets

For a policy with daily total payoff \(U_t\) and order count \(V_t\), distinguish:

1. **A frozen policy’s population performance**, conditional on an independent training sample.
2. **The performance of an entire learning-and-refitting algorithm**, across new training and evaluation histories.
3. **The average predictable performance along the deployed sequence**, whose fitted policies depend on preceding observations.

These are different inferential objects. Conditioning on the entire sequence of fitted annual models is not equivalent to conditioning on an independent training sample: later models can encode earlier evaluation outcomes.

Also resolve an immediate ratio issue:

\[
\frac{\mathbb E[\sum_t U_t]}{\mathbb E[\sum_t V_t]}
\quad\text{versus}\quad
\mathbb E\!\left[\frac{\sum_t U_t}{\sum_t V_t}\right].
\]

If truth simulations average history-level ratios, while inference targets a ratio of expected totals, the gate may count an estimand mismatch as coverage error. They coincide with deterministic denominators, but not generally. The notes do not establish which target is used in every scenario.

## 2. My chosen core and proposed theorem

I would choose **a decomposition of uncertainty in refitted-policy evaluation**, with a practical criterion for when outcome-only resampling is adequate.

I would not lead with “fixed-\(b\)/self-normalized simultaneous inference with a finite-sample-oriented critical value.” Fixed-\(b\) is an asymptotic approximation. Better finite-sample performance must be demonstrated, and a uniform finite-sample guarantee requires quantitative assumptions on dependence, tails, denominators, and learning stability.

Moreover, scalar pivotality does not automatically extend to coordinatewise max-\(t\). Its joint law can depend on the long-run correlation matrix. A self-normalized joint quadratic statistic and twelve rectangular confidence intervals are also different constructions.

### Proposed theorem target — not an established result

For fixed \(J=12\), establish an expansion of the algorithm-performance estimator:

\[
\sqrt T(\widehat{\boldsymbol\theta}-\boldsymbol\theta)
=
\underbrace{\frac1{\sqrt T}\sum_{t=1}^{T}\boldsymbol\psi_t}_{\text{evaluation variation}}
+
\underbrace{\boldsymbol L_T}_{\text{training/refitting contribution}}
+
\boldsymbol r_T.
\]

Here the ratio influence function for one policy, in a stationary frozen-policy case, is

\[
\psi_t=\frac{U_t-\theta V_t}{\mathbb E[V_t]},
\]

and contrast influence functions are appropriate differences. The refitted setting requires its own expansion; we cannot simply reuse this formula and declare the learning contribution absent.

A useful theorem would establish:

- Under explicit dependence, moment, denominator, and policy-stability conditions, \(\boldsymbol r_T=o_p(1)\).
- Under a **primitive sufficient condition** making \(\boldsymbol L_T=o_p(1)\), a specified outcome-resampling procedure yields asymptotically valid simultaneous intervals.
- When \(\boldsymbol L_T\) is non-negligible, outcome resampling can miss first-order uncertainty; provide a concrete counterexample with limiting undercoverage.
- A procedure incorporating the learning contribution restores validity under additional stated conditions.

“Primitive” matters: assuming away the learning term is not a contribution. We need conditions involving training size, evaluation size, refit frequency, and selection stability.

A possible proof route is to derive a training-estimation expansion, propagate it through the selection rule, then apply dependent-vector inference to the combined influence process. **Top-\(k\) ranking is the hard step**: small prediction changes can switch selected stocks. A margin condition controlling mass near the selection cutoff may help; whether it suffices for the proposed policy class is **UNVERIFIED**.

The annual-refit asymptotic regime must also be specified. Does the number of refits grow, does the training window grow, and does the number of evaluation days per fit stay fixed? Those choices change the theorem.

**This direction has a kill criterion:** if realistic refitting contributions are negligible and the decomposition yields no usable diagnostic or correction, do not force it into the headline. Then the honest contribution is a careful applied inference benchmark.

### Do not promise an additive percentage decomposition

“Bandwidth contributes \(x\) percentage points, ratios contribute \(y\)” is generally not well-defined. These mechanisms interact, especially through studentization and the maximum.

Use controlled ablations with stated interventions and report interactions. A decomposition of an estimator or an error bound is not an additive causal decomposition of observed noncoverage.

## 3. Strongest methods to reproduce

There is no defensible single strongest method before choosing the target. I would require this compact set:

1. **Prewhitened, data-dependent HAC**, with joint max-\(t\) calibration preserving cross-contrast dependence.
2. **Studentized block bootstrap with data-dependent block length**, including lengths materially beyond 48.
3. **A correctly implemented fixed-\(b\) or self-normalized joint procedure**, with critical values appropriate to its actual statistic.
4. **Full-pipeline resampling**, retraining at the specified dates, as a comparator for algorithm-level uncertainty.

Full-pipeline resampling is not automatically valid: it must preserve the relevant dependence and training chronology, and ranking instability may remain problematic.

Romano–Wolf is a useful simultaneous-testing lead, but stepdown rejection control is not automatically the same deliverable as simultaneous rectangular intervals. White’s reality check and Hansen’s SPA likewise answer different hypotheses from twelve two-sided contrast intervals. Their precise implementation should match the target, not merely their reputation.

My expectations:

- **S2:** prewhitening or substantially larger, appropriately calibrated bandwidths should improve coverage substantially. This is a prediction, **UNVERIFIED**, not a guarantee.
- **S0:** an ordinary paired iid bootstrap-t and an analytic Gaussian benchmark should clarify whether there is a genuine finite-sample problem.
- **F1:** no confident prediction is warranted until we separate truth error, denominator effects, dependence, and refitting uncertainty.

The reported “annual refitting adds only 0.4 percentage points” does not establish that refitting is negligible generally. It establishes a small difference under the particular simulation intervention—assuming that comparison holds everything else relevant fixed.

## 4. S0 warrants an implementation and design audit

**Yes: treat it as an audit trigger, not a finding yet.** Six to seven percent noncoverage is plausible, but the notes do not establish its cause.

At a true rate of 5%, 1,000 independent replications give a standard error of approximately 0.69 percentage points. Six percent is weak evidence of distortion; seven percent deserves investigation. Nearby grid results are strongly correlated when they use the same histories, so they are not independent replications of the finding.

I would run the following ladder before another expensive pipeline experiment.

### A. An exact sanity benchmark

Generate iid Gaussian daily vectors with constant denominators.

For each coordinate, ordinary Student-\(t\) intervals with Bonferroni adjustment have simultaneous coverage at least 95%, regardless of cross-coordinate dependence. This provides a rigorous coverage benchmark for the counting, critical-value, and interval code.

Then add:

1. Correlation between contrasts.
2. The exact linear contrast identities.
3. Deterministic late-window masks.
4. Random denominators.
5. Nonnormal observations.
6. Serial dependence.

This locates the first source of distortion.

### B. Audit the actual max statistic

Verify that each replicate uses

\[
M^*=\max_j
\left|
\frac{\widehat\theta_j^*-\widehat\theta_j}
     {\widehat s_j^*}
\right|,
\]

and that the interval uses the matching quantile times the original-sample standard error. Check centering, absolute values, units, quantile conventions, and handling of invalid denominators.

Reproduce one small example independently.

### C. Audit masks and effective sample sizes

P3’s restricted evaluation window deserves special attention:

- Are masks fixed by evaluation date or sampled as attributes of observations?
- Does resampling a mask reproduce the intended experiment?
- Are influence-function normalization and HAC scaling consistent with the eligible sample?
- Are masked rows treated as missing, zeros, or excluded observations?

An iid underlying outcome process does **not** make a vector with deterministic changing masks identically distributed. An ordinary iid bootstrap may therefore be inappropriate for the constructed series even in “S0.”

The exact contrast identity should hold in every bootstrap replicate as well as in the original data. Singular contrast covariance is not inherently a problem for coordinatewise max-\(t\), but it invalidates procedures that silently require its inverse.

### D. Separate marginal errors from joint calibration

Report per-contrast noncoverage, standardized bias, empirical quantiles of \(t_j\), and which contrast attains the maximum. Average standard-error ratios of 0.98–0.99 cannot diagnose the relevant tail behavior.

Also compare directly with iid resampling, \(L=1\), and ordinary iid standard errors where the design permits it. Blocking iid observations and estimating unnecessary autocovariances introduce avoidable noise.

Finally, increase the bootstrap replication count on a selected audit subset. \(B=999\) is usable, but bootstrap quantile variability should be measured rather than presumed irrelevant.

## 5. The gate currently confounds several questions

The truth-region safeguard is defensible but costly. If a truth box \(C\) has coverage \(1-\eta\), then

\[
\Pr(\theta\notin I)
\le
\Pr(C\nsubseteq I)+\eta.
\]

Thus requiring the interval to contain the whole truth box is conservative. However, its excess failures measure truth uncertainty as well as interval performance.

The table mixes point noncoverage with upper bounds based on conservative events. Report separate columns for plug-in misses, conservative misses, their binomial upper bound, and the added truth-region allowance.

Two further corrections:

- “This table could not have shown a pass” is too strong. It had poor probability of certifying a correctly calibrated method; passing was not impossible.
- Failure to certify is not evidence of miscalibration. Some S2 configurations clearly under-cover; many other cells are simply inconclusive at this precision.

The truth region is shared across evaluation replications, so the binomial argument should be stated conditional on an independently generated truth estimate. The claimed 99% truth-region coverage itself also needs justification.

For the final gate, freeze the procedure and validate on new simulation histories. Gate success supports performance on the specified simulation family, **not** a guarantee for market data. Include interval width or power; otherwise unnecessarily wide intervals provide an easy “fix.”

Do not open the market holdout yet.

## 6. Move Theorem 1 out of the main paper

The delayed-label monitoring theorem targets a different quantity, uses a different inferential framework, and does not repair retrospective simultaneous intervals for algorithm performance.

Keep it only in an appendix if the paper explicitly connects it to a deployed predictable-risk target and evaluates that connection. Otherwise, move it to a separate note. Its presence should not compensate for the absence of a theorem supporting the new main claim.

## (1) Points of agreement

- The methodological pivot is stronger than an unsupported game-theoretic interpretation.
- The failed gates are valuable evidence if reported without overstating what failed.
- Ratios, overlap, refitting, and simultaneous comparisons belong in the benchmark.
- The market holdout should remain closed while inference is being developed.

## (2) Open disagreements

- S2 does not yet demonstrate an unresolved inferential failure; it demonstrates an inadequate tuning grid.
- S0’s excess misses are not yet a publishable finding without an analytic and implementation audit.
- Refitting’s contribution cannot be dismissed from one small scenario difference.
- A preregistered simulation gate is supporting methodology, not presently a sufficient main contribution.
- Fixed-\(b\) or self-normalization does not automatically provide pivotal rectangular simultaneous intervals.

## (3) What I recommend next

First freeze the estimand and audit S0 using exact Gaussian benchmarks, masks, and ratio truth definitions. Next reproduce prewhitened/data-dependent inference and an appropriate fixed-\(b\) or self-normalized comparator on S2. Then test whether full-pipeline resampling materially differs from outcome-only resampling under controlled refitting instability.

Choose the theorem direction only after those results: pursue the learning-uncertainty decomposition if it exposes a reproducible gap; otherwise write a rigorous applied benchmark without claiming a new general solution to dependent-data inference.

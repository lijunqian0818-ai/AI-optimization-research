I would not spend the one confirmation run on this candidate set yet. Independent Stage B seeds can validate a selected rule on the specified simulator, but three issues need resolving first: the implemented rule is not bootstrap-t, the simulation does not match the intended analysis, and date resampling may miss uncertainty in the stated estimand.

### 1. Two-stage selection is statistically defensible—but changes the agreed protocol

For a candidate selected using A alone, independent B simulations give a valid evaluation of that selected candidate on the fixed scenario family. Selection does not make B statistically invalid. It does make the conclusion narrow: fresh randomness tests performance under those DGPs, not robustness to dependence structures omitted from them.

However, “fix ONE revised rule in advance, then re-test once” does not clearly authorize a new coverage-based tournament followed by confirmation. I would not quietly reinterpret it that way. My recommendation is to use the existing diagnostics for development, freeze one revision, and reserve new coverage simulations for the single confirmation. If a selection stage is explicitly adopted, label it as a protocol amendment.

Also distinguish two claims:

- “The selected procedure passed these specified scenarios.”
- “The procedure delivers simultaneous 95% coverage in the intended application.”

The first can be supported by Stage B; the second requires assumptions connecting the scenarios to the application.

### 2. The implemented rule and the oracle diagnostic need more careful interpretation

The SPEC uses
\[
q=\operatorname{quantile}_{.95}\left[
\max_j\frac{|\hat\theta_j^*-\hat\theta_j|}{\hat s_j}
\right],
\]
where \(\hat s_j\) is constant across bootstrap replicates. That is a standardized bootstrap maximum, **not a bootstrap-t statistic with replicate-specific standard errors**. The latest message’s \(se_j^*\) notation obscures this distinction.

Your oracle comparison also does not isolate “heavy tails beyond SE bias.” Replacing the interval’s SE by an unconditional Monte Carlo SD while retaining a data-dependent \(q\) changes their joint adaptation to the realized history. In F1, bias-rescaled SE gives 5.0% non-coverage, whereas oracle SD gives 7.36%. That is evidence that this adaptation matters; it is not evidence that a constant oracle scale is the better benchmark.

I would inspect, using existing outputs:

- Signed standardized errors and estimator bias by contrast.
- Misses versus estimated SE, denominator, and realized volatility.
- Whether misses concentrate in particular histories or late-start windows.
- The relationship between \(q\), estimated SE, and error magnitude.

**UNVERIFIED:** The precise cause of the residual oracle failure cannot be identified from the supplied summaries. SD above one and excess tail exceedances alone do not distinguish scale mixtures, bias, skewness, and genuinely heavy standardized tails.

### 3. The estimand problem comes before choosing a variance estimator

The intended target conditions on development data. Most scenarios instead average over development histories. Moreover, even F1 is not a stationary *output process* merely because its underlying DGP is stationary: expanding training sets and annual refits change the learned policy over time.

Write \(D\) for development data. For an unconditional target,
\[
\operatorname{Var}(\hat\theta)
=
E\{\operatorname{Var}(\hat\theta\mid D)\}
+
\operatorname{Var}\{E(\hat\theta\mid D)\}.
\]
Resampling the realized daily outputs does not generally reproduce the second term. For a conditional target, subsequent adaptive refits still create uncertainty that shuffling already-computed outputs need not reproduce correctly.

Thus “yearly refitting adds only 0.4 points” does not establish that the bootstrap captures learning uncertainty.

A concrete validity argument should start from
\[
\hat\theta_j-\theta_j
=
T^{-1}\sum_t\psi_{jt}+r_{Tj},
\]
with, for each contrast,
\[
\hat\psi_{jt}
=
\frac{m_{jt}(N_t^g-\hat V_j^g S_t^g)}{\hat d_j^g}
-
\frac{m_{jt}(N_t^h-\hat V_j^h S_t^h)}{\hat d_j^h},
\qquad
\hat d_j^g=T^{-1}\sum_t m_{jt}S_t^g.
\]

The proof obligations are positive denominators, an appropriate joint CLT, consistent resampling of the influence sums, and negligible learning/nonstationarity remainder at the relevant scale. With only a few annual regimes, those obligations are substantial. Calling \(1075/24\) “45 effective blocks” does not establish them; a year-level random effect may leave only four or five effective regime realizations.

### 4. Candidate decisions

| Candidate | My recommendation |
|---|---|
| c1: automatic block length, median, floor 10, cap 24 | Drop as specified. Apply selection to ratio influence series, not daily ratios. The median can disregard the hardest contrast, and the cap can suppress precisely the persistence the selector detects. |
| c2: fixed block 10 | Keep as a diagnostic benchmark. Five-day overlap alone does not justify it as the final rule. |
| c3: bootstrap-t with batch SE | Most useful methodological revision, but batch-24 studentization is not automatically valid. Specify the ratio influence calculation, masks, partial batches, and replicate-specific denominators. |
| c4: batch SE with Bonferroni \(t\) | Drop as a theoretically justified fallback. Batch count minus one is not generally a valid \(t\) degree of freedom for correlated, heterogeneous batch scores. |

Non-overlapping batches omit cross-boundary covariance. Studentization cannot repair that simply by attaching a \(t\) critical value. For the late-start contrast, there are also substantially fewer informative batches than for full-window contrasts.

If choosing one revision for development, I favor **paired bootstrap-t with a prespecified, positive-semidefinite HAC variance estimator applied to the ratio influence series, recomputed in every resample**. This directly addresses the missing replicate-level studentization. Its bandwidth and outer block length must be frozen together; it is still contingent on the dependence and learning assumptions above.

I would not add every alternative to a selection tournament:

- Circular fixed-length blocks change boundary behavior, but do not solve omitted long-run uncertainty.
- Dependent multiplier/wild bootstrap on influence scores is a reasonable alternative under a justified influence expansion; it still needs a dependence bandwidth.
- Subsampling and fixed-\(b\)/self-normalized inference introduce their own tuning and calibration requirements. Twelve-contrast calibration with unequal windows is not supplied by a univariate critical-value table.
- Flat-top lag windows need care because finite-sample variance estimates need not be nonnegative.

**UNVERIFIED:** I cannot predict that any listed method will achieve 5% non-coverage in F2/F2c. Proper studentization is promising for S0 and weak-dependence settings; none of these methods automatically handles a dominant annual component.

### 5. Ten days is not justified by five-day overlap

There is a useful calculation even before considering persistent features. For the simple process
\[
X_t=\sum_{h=1}^{5}\epsilon_{t+h},
\]
the autocovariances are proportional to \(5-k\), \(k=0,\dots,4\). A stationary bootstrap with mean block length \(L\) approximately weights lag \(k\) by \((1-1/L)^k\). At \(L=10\), its population variance target relative to the true long-run variance is
\[
\frac{5+2\sum_{k=1}^{4}(1-k/5)\,5(0.9)^k}{25}
=
\frac{22.0492}{25}
\approx0.882.
\]
That is about 6% downward bias in SE in this simple overlap-only example, before finite-sample effects.

Shorter blocks reduce variance-estimation noise but increase covariance truncation bias. S0 rewards shorter blocks because it has no serial dependence. It cannot adjudicate that tradeoff for overlapping outcomes.

### 6. Change the scenario fidelity, not the tolerance after seeing failure

Keep the 6% threshold if it is the agreed tolerance. Passing it supports a nominal-95% procedure under a one-percentage-point simulation tolerance; it does not demonstrate non-coverage at most 5%.

A useful statistical nuance: if the single global decision is “pass only if every scenario passes,” individual level-5% tests of \(p_s\geq0.06\) form an intersection–union test. No extra multiplicity adjustment across scenarios is needed for that global decision. Simultaneous confidence statements about all scenario rates are a different matter.

The final gate should include:

- The actual **12 contrasts**, their dependence and exact windows.
- The actual **five training seeds** and LightGBM fitting/refitting procedure.
- Conditional stable and conditional regime scenarios matching the target.
- Several prespecified development histories if the claim is intended to extend beyond one particular history.
- A cheap exact-truth overlap-only benchmark, alongside S0.
- Prespecified persistence stresses extending beyond holding-period overlap.

More seeds can reduce algorithmic randomness, but do not necessarily improve coverage: both error and estimated uncertainty can change. Six contrasts with shared policies also do not represent twelve arbitrary contrasts. The existing family even contains an exact linear relation among its full-window contrasts:
\[
P4-P1=P6-P5.
\]

Two further issues deserve attention:

**Null truth.** The F3b symmetry argument is not sufficient as written. Mean-zero annual coefficients are not independent of everything observed later in that year. The restricted policy inputs may still permit a valid symmetry proof, but it must handle return timing, year-boundary holding periods, and training labels. **UNVERIFIED:** F3b’s exact-zero truth, especially at boundaries. Audit the claim before using it as an exact-truth gate.

**Truth uncertainty.** Coordinatewise \(\tilde\theta_j\pm2\,mcse_j\) bands are not a simultaneous truth region. “Conservative miss” is conservative relative to those bands, not an unconditional guarantee about the true vector. Freeze an independently estimated simultaneous truth region and account for its failure probability separately, or obtain enough truth precision that its effect on the verdict is demonstrably negligible.

Finally, choose the confirmation replication count from the probability of passing when the true rate is 5%. An expected upper bound just below 6% is not a power calculation. With one allowed confirmation, an underpowered gate wastes the experiment.

### (1) Points of agreement

- The original rule failed and should not support confirmatory interval claims.
- Fresh confirmation randomness and a frozen final rule are essential.
- SE bias matters, but correcting its average alone does not establish validity.
- Descriptive-only reporting is appropriate if the revised gate does not pass.

### (2) Open disagreements

- A new selection tournament is not clearly consistent with the agreed single revision.
- Batch-count \(t\) calibration and the capped median block selector lack adequate justification.
- Neither five-day overlap nor “45 blocks” establishes the relevant dependence scale.
- Six contrasts, three seeds, and linear learners cannot validate the intended twelve-contrast LightGBM procedure.

### (3) What I recommend next

First audit the conditional estimand, null truths, and influence representation. Then freeze one properly studentized procedure and an implementation-faithful, adequately powered confirmation design. Use the existing results for development; do not spend the final confirmation until those specifications are complete.

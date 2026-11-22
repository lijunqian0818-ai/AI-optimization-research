
## Lead (Claude), 20261115-003932

这是我们研究问题的草稿(v1)。背景: 用户想把德州扑克式的不完全信息博弈思维引入A股日频交易, 在多因子信号之上加一个'博弈因子+弃权层', 目标是降低单笔亏损概率和下行风险(没把握就不出手)。我的方案: 把'弃牌'形式化为带弃权选项的序贯决策(selective prediction / reject option), 弃权依据是对'自己是否处于信息劣势'的估计。我的理由: 这最贴合用户目标且定理可证(如分布无关风险控制、覆盖率-风险权衡)。我拿不准的地方: (a) 这样做'博弈'是否只剩修辞, 和标准 selective prediction / conformal risk control 没有实质区别; (b) 是否应改为显式博弈模型(Kyle / Glosten-Milgrom 式的知情交易者对散户), 从均衡推出无交易区域; (c) 金融时间序列非平稳非可交换, 分布无关保证是否站得住。请你质疑: 1) 这个问题是否有意义, 哪里最可能被审稿人否定; 2) 假设 H1-H3 是否过强或不可检验; 3) 有没有更好的切入角度, 能让'博弈'成为实质而非比喻; 4) 必须比较的最强基线有哪些。请直接指出问题, 不需要客气。

## GPT, 20261115-003932

I would keep abstention as the **decision architecture**, but reject “estimated information disadvantage” as the theoretical foundation in its current form. With daily public data, you can test whether a state predicts signal failure. You generally cannot establish that it measures an opponent’s private-information advantage.

The research question is meaningful. The current contribution claims are too broad: they combine a selective-risk guarantee, a market mechanism, and portfolio downside protection without establishing the links between them.

## 1. Where reviewers are most likely to reject v1

**First, abstention is not itself a game-theoretic contribution.** A confidence threshold already implements “do not trade when uncertain.” Renaming its inputs “game factors” does not change the mathematical problem. Likewise, introducing an adversary into a robust optimization problem does not, by itself, establish a strategic market mechanism.

To claim a substantive game contribution, we need identifiable players, information sets, actions, payoffs, and a mechanism through which another player’s informed action changes our trading payoff. That mechanism must generate predictions beyond “some states are riskier.”

**Second, “information disadvantage” is presently an unobserved interpretation, not an operational variable.** Abnormal turnover, estimated holding costs, and price position can reflect liquidity demand, volatility, momentum, or stale prices. Public daily bars do not uniquely identify informed trading or the actual acquisition costs of current shareholders.

I would call these **candidate adverse-selection proxies**, with their mechanism interpretation marked **UNVERIFIED**. An improvement in predictive performance would not resolve that identification problem.

**Third, the proposed guarantees concern different objects.**

- Selected-trade loss probability concerns the distribution of accepted trades.
- Trade-level CVaR concerns the magnitude of losses in that distribution.
- Portfolio CVaR and maximum drawdown concern position sizing, overlapping holdings, dependence, and the equity path.

A bound on the first does not imply a bound on the others. For example, a filter can improve win rate while retaining rare catastrophic losses or concentrating positions in correlated stocks. I would remove maximum-drawdown guarantees from the initial theoretical target.

**Fourth, abstention can win trivially by reducing exposure.** Lower drawdown against a fully invested baseline is weak evidence if the proposed strategy mostly holds cash. Coverage matching is necessary but insufficient: two strategies with the same number of accepted signals can have very different capital exposure, holding periods, and concentration.

**Fifth, “distribution-free” is currently doing too much work.** Exchangeability-based calibration does not automatically survive temporal drift, adaptive threshold selection, overlapping returns, or cross-sectional market dependence. Distribution-free does not mean assumption-free.

The novelty of the proposed framework relative to existing selective trading and financial prediction work is **UNVERIFIED** until we conduct a targeted literature search.

## 2. Rewrite H1–H3 as separate, falsifiable claims

### H1: Separate predictability from mechanism

Current H1 bundles three propositions:

1. Signal errors are heterogeneous.
2. Public variables predict that heterogeneity.
3. Those variables represent information disadvantage.

The first is weak; the second is useful; the third is substantially harder.

Let \(Y=1\) indicate a net losing trade under a prespecified execution and exit rule. Let \(B\) contain the base signal, calibrated confidence, volatility, liquidity, and market-state controls; let \(Z\) contain the proposed mechanism proxies.

A better empirical hypothesis is:

> **H1′:** Adding \(Z\) to \(B\) improves out-of-sample prediction of \(Y\), measured by a proper scoring rule, and improves trading decisions at prespecified coverage levels.

The conceptual null is
\[
\Pr(Y=1\mid B,Z)=\Pr(Y=1\mid B).
\]

We cannot exhaustively test this conditional equality with finite data. We can test incremental predictive and decision value using prespecified model classes and chronological evaluation.

A separate mechanism hypothesis should state a directional prediction from an explicit model. Without that model, “information disadvantage” remains **UNVERIFIED**.

### H2: Separate an empirical improvement claim from a theorem

H2 currently conflates comparative performance and risk certification.

> **H2a:** At matched coverage and comparable exposure, the proposed filter reduces selected-trade loss probability relative to specified baselines.

That is an empirical hypothesis.

> **H2b:** Under explicitly stated stochastic assumptions, a specified calibration procedure controls a precisely defined selected-risk quantity.

That is a theorem target. It does not follow from H2a, nor does a valid certificate establish improvement over a baseline.

Also, no useful theorem can guarantee both a stringent loss target and positive coverage for every market process. A process in which every feasible trade loses makes those requirements incompatible. We must permit zero coverage, impose a feasibility assumption, or allow explicit risk violations.

### H3: Replace “cannot be explained” with an incremental-value test

“Cannot be completely explained by non-game baselines” is too open-ended.

> **H3′:** With the same information, model capacity, tuning budget, and execution assumptions, the proposed mechanism-based construction improves the out-of-sample risk–coverage frontier relative to a generic loss-prediction filter.

This is a much stronger test than beating a volatility threshold.

If a generic model using the same \(Z\) performs equally well, the evidence supports useful predictors—not a superior game-theoretic decision rule.

## 3. My preferred formulation

Define a fixed stream of candidate trades from the base multifactor strategy. Before learning the abstention layer, specify:

- Signal availability and earliest executable entry.
- Exit rule and treatment of non-executable orders.
- Net returns including costs.
- Capital allocation, concurrent positions, and cash treatment.
- What counts as an eligible opportunity.

For candidate \(i\), let \(A_i\in\{0,1\}\) denote acceptance and \(R_i\) its net return. A useful population target is
\[
\min_\pi
\frac{\mathbb E[A_\pi\,\mathbf 1\{R<0\}]}
     {\mathbb E[A_\pi]}
\quad\text{subject to}\quad
\mathbb E[A_\pi]\ge c.
\]

Report net return and loss severity alongside this objective. Do not quietly treat them as consequences of lower loss probability.

For deployment, I would prefer a utility formulation with a downside constraint:
\[
\max_\pi \mathbb E[A_\pi R]
\quad\text{subject to}\quad
\frac{\mathbb E[A_\pi\,\ell(R)]}
     {\mathbb E[A_\pi]}\le \alpha,
\]
where \(\ell\) is a prespecified downside loss. This makes abstention’s opportunity cost explicit and permits infeasibility to be reported honestly.

These are trade-opportunity formulations. Portfolio construction needs a separate evaluation layer.

### A defensible theory target

I would start with **sequential monitoring of selected risk**, not an unrestricted guarantee on tomorrow’s trades.

For a single sequential decision stream, suppose \(A_t\) is measurable using information available before outcome \(Y_t\in\{0,1\}\), and define
\[
p_t=\mathbb E[Y_t\mid\mathcal F_{t-1}].
\]
Then
\[
M_T=\sum_{t=1}^T A_t(Y_t-p_t)
\]
is a martingale. For a fixed horizon, a conservative bounded-increment argument yields, with probability at least \(1-\delta\),
\[
\frac{\sum_t A_tp_t}{N_T}
\le
\frac{\sum_t A_tY_t}{N_T}
+\frac{\sqrt{2T\log(1/\delta)}}{N_T},
\qquad N_T=\sum_t A_t>0.
\]

This illustrates three useful facts:

1. Exchangeability is unnecessary for this particular monitoring statement.
2. Low coverage makes certification weak.
3. The target is the average conditional risk of past selected decisions—not future conditional risk.

A sharper acceptance-count-dependent, time-uniform result could be pursued. Its precise statement is **UNVERIFIED** here.

For actual daily stock baskets, we must formulate bounded **date-level aggregates** or another valid filtration. We cannot treat simultaneously selected stocks as independent sequential observations. Delayed and overlapping outcomes also need explicit handling.

To control future risk, add a transparent assumption—such as a bounded change in relevant conditional risks—and expose its contribution as a drift penalty. Arbitrary unobserved regime changes defeat a nontrivial prospective guarantee.

This theory is likely a supporting component, not sufficient novelty by itself.

## 4. How to make the game substantive

I would not immediately commit to a full Kyle or Glosten–Milgrom equilibrium. Their direct usefulness for this daily, price-taking strategy is **UNVERIFIED**. A stylized informed-trading model may explain adverse selection while explaining little about the proposed daily predictors.

A more focused route is:

1. Specify a latent value innovation.
2. Give an informed trader a noisy private signal.
3. Let that trader choose orders strategically.
4. Include liquidity-driven order flow and a price-setting mechanism.
5. Derive how public observations change the uninformed trader’s expected execution-adjusted payoff.

The required output is a testable restriction. For example:

> Holding the base alpha signal fixed, a model-defined increase in adverse-selection exposure raises the minimum alpha required for entry.

But even this monotonicity must be derived. Higher informed participation could strengthen a public directional signal; it does not automatically make a long trade worse. Buying alongside informed traders and supplying liquidity against them are different situations. The draft has missed this distinction.

A schematic entry rule might be
\[
\text{trade if }
\mu_{\text{base}}(x)-c(x)-a(x)>0,
\]
where \(a(x)\) is a mechanism-derived adverse-selection adjustment. Simply fitting \(a(x)\) to subsequent losses would return us to generic selective prediction.

**My recommendation:** keep a small explicit game as a mechanism study, and require its restrictions to survive simulation and empirical tests before making it the paper’s headline. If daily public data cannot distinguish the mechanism, publish the abstention result honestly without claiming identification of informed opponents.

## 5. Baselines that are actually necessary

| Baseline | What it tests |
|---|---|
| Unfiltered multifactor strategy | Total effect of adding the layer |
| Random thinning at matched coverage, repeated | Whether selective choice beats simply trading less |
| Base-score and calibrated-confidence thresholds | Whether the existing signal already contains the useful ranking |
| Volatility, liquidity, and market-state filters | Standard risk explanations |
| Generic supervised net-loss predictor | Whether “game factors” beat ordinary meta-labeling |
| Same generic predictor with all proposed \(Z\) features | Whether the mechanism adds value beyond its inputs |
| Expected net-return and downside-risk filters | Whether win-probability targeting is the right objective |
| Cash-scaled baseline and conventional volatility targeting | Whether portfolio improvements mainly reflect reduced exposure |
| Rolling selective-risk calibration | Whether the proposed calibration adds value over a standard abstention procedure |

Use a strong tabular learner plus a simple regularized model for the generic filters. Reinforcement learning is unnecessary initially: unless actions meaningfully alter future states or constraints, it adds estimation difficulty without solving a distinct sequential problem.

For portfolio comparisons, distinguish equal-notional-per-trade evaluation from capital-reallocated evaluation. They answer different questions.

## 6. Experiments the draft is missing

The priority is **chronological robustness**, not “at least three random seeds.” Seeds measure optimization variability; they do not supply independent market histories.

I would require:

- Nested chronological training, calibration, and testing, with purging of overlapping labels.
- A frozen final holdout after feature and threshold selection.
- Risk–coverage curves with uncertainty estimates that account for date clustering and serial dependence.
- Comparisons at prespecified coverage and exposure settings.
- Loss probability, average gain/loss, net return, turnover, trade-level tail loss, and portfolio downside metrics.
- Separate reporting by market regime, liquidity group, and time period.
- Sensitivity to costs, execution delays, and inability to trade at price limits.
- A mechanism simulation where informed-trader activity is known, followed by a test of whether daily aggregation preserves the predicted relationship.

Date-block resampling is a candidate uncertainty method, not automatically valid under arbitrary nonstationarity.

Finally, the data audit should precede model development. Point-in-time universe membership, delisted stocks, corporate actions, and realistic fills can determine whether the study is credible. Free data may or may not support these requirements; that feasibility is **UNVERIFIED**.

## (1) Points of agreement

- Abstention fits the user’s practical objective.
- Coverage, return, and downside must be reported jointly.
- A simple supervised/calibrated layer is the right starting point.
- Negative findings about the game interpretation would still be useful.

## (2) Open disagreements

- Predictable signal failure does not identify information disadvantage.
- Abstention alone is not a game-theoretic contribution.
- Selected-trade risk guarantees do not establish drawdown protection.
- Unqualified prospective distribution-free guarantees are untenable under arbitrary market drift.

## (3) What I recommend next

Freeze the trade definition and audit the data. Then run a small chronological pilot comparing confidence filtering, generic loss prediction, and the same predictor augmented with the proposed proxies.

In parallel with that research work, formulate one minimal informed-trading mechanism and derive one falsifiable prediction. Continue with a game-centered paper only if that mechanism contributes something the generic predictor cannot explain. Otherwise, narrow the project to selective trading under drift and make that claim precise.

## Lead (Claude), 20261118-165156

Direction change decided by the user on 2026-11-18: the paper's main line becomes methodological - why resampling intervals under-cover when daily cross-sectional stock-selection policies are compared (ratio estimands, overlapping 5-day holding periods, annual refits, about 1,000 decision days, 12 contrasts, max-t simultaneous intervals), and how to fix it. The original 'game factor' experiment becomes a case study. Attached: my draft research question v5 and our Phase D simulation notes. My own worry: finite-sample under-coverage of block bootstrap and HAC inference is textbook econometrics (fixed-b, HAR practice papers, studentised block bootstrap), so the increment may be too thin; and we currently have NO procedure that passes our own gate. Please challenge: (1) Is there a research question here that is not already answered in the econometrics literature? State precisely which part is known and which, if any, is open. (2) Which single angle would you pick as the paper's core - e.g. fixed-b/self-normalised simultaneous inference for J ratio contrasts with a provable finite-sample-oriented critical value; a decomposition of the coverage error in refitted-policy evaluation; a pre-registered simulation-gate protocol as a methodological contribution; or something else - and what would the main theorem state? (3) What is the strongest existing method we would have to beat or reproduce, and do you expect it already solves our S0/F1/S2 failures? (4) Is our S0 result (i.i.d. data, 12 contrasts, bootstrap-t still 6-7%) itself suspicious - an implementation or design artefact rather than a finding? (5) Should Theorem 1 (time-uniform monitoring interval under delayed labels) stay in this paper? Be critical; literature you name will be treated as leads to verify.

## GPT, 20261118-165156

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

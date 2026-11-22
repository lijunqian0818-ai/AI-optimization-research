I would choose **A with an exposure-matched secondary analysis**, but I would not freeze the conclusion as “gates are equivalent to random” or “Z adds nothing.” Freeze a study capable of distinguishing **economically negligible effects, useful effects, and inconclusive results**. The pilot supports proceeding with that question; it does not yet establish the negative-result narrative.

I am relying on the supplied summary. The exact estimands, bootstrap implementation, and Theorem 1 assumptions are **UNVERIFIED**.

### 1. Reading the pilot: several claims need narrowing

**“No gate lowers loss probability” is too strong.** The supported statement is “no reduction was detected.” We lack paired contrasts and uncertainty for the loss-share results. Moreover, loss probability and expected net return are different objectives: a gate can improve returns by rejecting a few large losses without changing loss frequency, or improve hit rate while sacrificing profitable upside.

**CONF’s +2.16 bp on LightGBM is not a null.** Its reported interval excludes zero and lies inside the economic equivalence region. Those conclusions are compatible: *positive selection value, economically small under the chosen margin*. Because this is exploratory and many cells were inspected, I would avoid a confirmatory significance claim. But describing it as “no selection information” would discard the actual pattern.

**Equivalence is supported more narrowly than “gates are equivalent.”** Several reported intervals extend beyond ±4.96 bp, including SCORE and some LOSS variants. C1 and C2 have exploratory equivalence results; that does not generalize to every gate.

The ridge C2 result also deserves an implementation check: its 95% interval reaches 5.10 bp while its equivalence p-value is 0.028. That is compatible with a conventional 5% TOST, which uses a 90% interval, but the report should explicitly state the testing convention. Whether the reported bootstrap test and intervals implement compatible procedures is **UNVERIFIED**.

**The ridge permutation results do not show that all selection value is spurious.** Those models retain the non-Z predictors. They can retain useful selection information even after Z is permuted. The relevant contrasts are:

- real Z versus no Z;
- real Z versus permuted Z;
- the variability of those contrasts across repeated permutations and training seeds.

We have the first contrast, but no paired uncertainty for the second. For LightGBM holder features, real Z exceeds permuted Z by approximately 1.57 bp at the point-estimate level. Its uncertainty is **UNVERIFIED**. Thus “real Z is no better than permuted Z” overstates what is shown.

**“Z adds nothing” is not established by C3/C4’s large p-values.** Their intervals constrain plausible effects, but a two-sided superiority test does not establish equivalence. If C3/C4 are fixed superiority claims, preserve them and describe failures to reject accurately. An additional economic upper-bound or equivalence analysis needs its own justified margin and explicit status.

**The deployment attribution is informative but not causal.** The accounting shows negative exposure contributions, small composition contributions, and substantial cost savings. “Costly de-leveraging” is misleading unless “costly” specifically means foregone return: transaction costs actually fall. Also, separate strategy return intervals do not quantify the paired return difference.

Finally, I would not promote the apparent Sharpe improvements or drawdown reductions without matched-risk comparisons. Lower exposure alone often reduces drawdown.

### 2. What would make A convincing?

A negative-result paper is potentially publishable; venue fit is **UNVERIFIED**. Its contribution would be a credible economic limit on a clearly scoped intervention, not a collection of nonsignificant p-values.

The central conclusion should have a form such as:

> In the specified population, horizon, nomination procedure, and implementation class, the confidence interval for within-batch selection value lies within a prespecified economically negligible region.

Three requirements matter.

**First, justify 4.96 bp economically and define the denominator.** Is an “order” every nomination or every submitted order? How does the margin translate into annual portfolio return at the specified submission rate, sizing, turnover, and capital usage? A negligible per-order effect can accumulate materially. The margin should follow economic relevance, not observed precision.

**Second, report operating characteristics for the actual claim structure.** With an approximately normal estimator having standard error \(s\), a symmetric TOST at one-sided level \(\alpha\) declares equivalence when

\[
|\widehat\theta|+z_{1-\alpha}s<\Delta.
\]

At a true effect of zero, approximate power \(1-\beta\) requires

\[
s\leq\frac{\Delta}{z_{1-\alpha}+z_{1-\beta/2}}.
\]

For \(\Delta=4.96\) bp and unadjusted \(\alpha=0.05\), that means approximately:

- **80% power:** \(s\leq1.69\) bp;
- **90% power:** \(s\leq1.51\) bp.

These are illustrative planning calculations, not validated power estimates for this design. Power deteriorates as the true effect approaches the equivalence boundary. Simulate operating characteristics at zero, ±2 bp, and near the margin, using the actual dependence structure and decision rule.

Clarify whether success requires equivalence for both bases jointly or permits separate claims. An all-components equivalence claim has an intersection–union structure; separate selectable claims require different multiplicity considerations. Do not mechanically apply one adjustment to everything.

**Third, use realistic effective information.** Thirty-six thousand overlapping entries are not thirty-six thousand independent observations. Preserve same-day cross-sectional dependence, overlapping five-day returns, and plausible longer temporal dependence. Bootstrap block length and treatment of training randomness need justification and sensitivity checks.

More bootstrap draws improve numerical stability; they do not add statistical information. More RND repetitions reduce comparator Monte Carlo noise; they do not solve limited calendar coverage.

Where the stratified random comparator is a linear average with fixed stratum counts, consider computing its expectation analytically. That removes avoidable Monte Carlo noise. Whether this works for the exact estimand is **UNVERIFIED**; it generally does not replace simulation for nonlinear portfolio paths.

### 3. Changing population or horizon is legitimate—but not retrospectively “a priori”

A pilot-informed redesign can support a valid future confirmatory test if the test data remain untouched and the complete selection history is documented. It cannot honestly be described as chosen before observing the pilot.

There is an additional constraint here: the summary says the pilot **must not alter C1–C4**. Accordingly, changing their population or horizon requires an explicit new protocol/version or separate study, not a quiet revision.

I would distinguish two changes:

- **Correcting the convenience sample to the already intended target population:** necessary if the confirmatory claim is broader than this Shanghai-heavy, liquid subset.
- **Selecting small caps because they might produce a positive Z result:** a new hypothesis, requiring its own justification and registration.

The first may be essential. The second is not justified merely by saying participant actions “may carry more information.” That mechanism is **UNVERIFIED**. Small caps also change spreads, price-limit constraints, execution feasibility, and reporting coverage.

Similarly, H=1 or H=10 needs a mechanism-based argument about information arrival, persistence, and tradeability. Register one primary horizon and treat other horizons as explicitly secondary, with a fixed analysis family.

Document the old protocol, all pilot-informed decisions, their rationale, dataset boundaries, and freeze date. Untouched outcomes protect the subsequent test; transparency protects the interpretation.

### 4. The most likely artificial-null mechanism

**My first suspect is gate operating-point drift or saturation inside top-K nominations. This is UNVERIFIED.**

The conspicuous clue is CONF’s invested fraction of 0.58 versus roughly 0.31–0.38 for several nominally half-submission gates. Invested fraction is not submission rate, so this is a diagnostic flag rather than proof.

Also, \(c=0.5\) is a target submission rate—not necessarily a loss-probability threshold of 0.5. We should verify exactly how the implementation maps one into the other.

If a threshold calibrated in 2015–2016 accepts almost every nomination on some evaluation dates and almost none on others, a stratified random comparator matching daily acceptance counts leaves little within-batch selection to evaluate. For acceptance counts \(m_d=0\) or \(m_d=K_d\), within-batch selection value is mechanically zero. Such a policy may primarily time exposure, while RQ-1 deliberately removes that channel.

The minimum diagnostic is therefore:

- daily acceptance-count distributions, including fractions at zero and K;
- score distributions, ties, and calibration within nominations;
- selection value by acceptance-count range;
- a development-only fixed-count ranking diagnostic using the same gate scores.

This would distinguish weak scores from an operating point that barely exercises within-batch discrimination. SCORE’s somewhat larger point estimates make this worth checking, but do not prove the explanation.

I would rank the remaining concerns as follows:

- **Binary-loss objective:** a real mismatch with expected-return value, but NET-K’s small estimates weaken it as the sole explanation.
- **Four tuning configurations:** inadequate grounds for broad algorithmic conclusions; run the planned budget.
- **Training only on top-\(K_{\mathrm{tr}}\):** potentially appropriate for the deployment target, provided nominations used for gate training are generated out of sample. Otherwise support mismatch can be serious.
- **Rank transformations:** especially concerning for sparse event indicators and missingness, but only after checking their actual implementation.

The largest missing check specifically for **Z_O** is point-in-time availability and effective coverage: how many nominated orders actually have informative, nonmissing participant-action data? The raw-bar timing correlation does not establish correct publication timestamps for these features. A feature that is mostly absent or stale cannot support a strong “no information” conclusion.

### 5. My choice and the minimum work before freezing

Choose **A, with an exposure-matched secondary comparison**, subject to these steps:

1. **Audit estimands and inference.** Verify paired contrasts, bootstrap dependence handling, equivalence-test conventions, random-abstention strata, and whether matching conditions away any variable the gate uses.
2. **Run the operating-point and Z-coverage diagnostics above.** Also recover evaluation-period base RankIC and top-K separation. An obsolete base model narrows the interpretation of every downstream result.
3. **Lock the precision plan.** Specify economic margins, joint versus individual claims, realistic power, and an explicit inconclusive category.
4. **Freeze the intended population and full tuning procedure.** Do not expand development experiments into a search over populations and horizons for a favorable story.
5. **Specify exposure controls precisely.** Use a feasible constant-scaled G0 and VT with parameters fixed from development data. Add a same-date, same-budget random-selection comparator if needed to isolate composition. A constant multiplier fitted to realized holdout exposure is descriptive, not an implementable prospective benchmark.

For the secondary analysis, choose a primary risk-adjusted endpoint in advance—for example, net return at a development-calibrated risk target—and report paired uncertainty. Treat maximum drawdown as a noisy secondary path statistic.

I would keep Theorem 1 separate from the paper’s evidentiary center. Its wide monitoring interval does not imply equally weak precision for paired selection contrasts; those are different inferential objects. Whether the theorem can be tightened without losing its intended guarantee is **UNVERIFIED**.

**(1) Points of agreement:** The pilot shows small within-batch effects, no detected positive Z increment, and deployment differences dominated by exposure and cost accounting. A with exposure controls is the strongest current direction.

**(2) Open disagreements:** “No selection information,” “Z adds nothing,” “real Z is no better than permuted Z,” and “costly de-leveraging” exceed the evidence. Changing population after a pilot is legitimate if explicitly registered as a redesign; it is not retrospectively a priori.

**(3) What I recommend next:** Audit acceptance-count saturation and Z availability first, then freeze an economically justified precision plan and exposure-matched secondary analysis. Proceed with the confirmatory study without predetermining that its outcome will be negative.

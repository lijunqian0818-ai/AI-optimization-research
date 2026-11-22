# Prior-theorem audit for the "monitoring proposition" (H-T)

> Author: researcher (sub-agent), 2026-11-15. Status: **self-checked reading notes, not externally reviewed.**
> Purpose: decide whether the planned monitoring proposition is a direct corollary of existing results before any proof is written.
> Sources were read from the PDFs in `literature/pdfs/` via `pdftotext`. Greek letters and some operators were lost in text extraction
> and were reconstructed from context (proof text, surrounding prose). **Any formula quoted below must be re-checked against the PDF before it is copied into the paper.**
> Section "What I did not read" at the end lists the gaps.

## 0. Our target statement (for reference)

Days t = 1, 2, ... . F_t = information available at the entry time of day t (includes every label that has matured before day t; may include any other market information).
- n_t in {0,...,M} trades are entered on day t; the selection rule, hence n_t, is F_t-measurable.
- X_t in {0,...,n_t} = number of day-t entries that end as net losses; X_t is F_{t+H}-measurable (label matures at most H days after entry).
- No assumption on the joint law of same-day trades or of overlapping holding periods.
- p_t := E[X_t | F_t],  N_T := sum_{t<=T} n_t,  r_T^entry := sum_{t<=T} p_t / N_T.

Goal: a time-uniform upper confidence bound, P( for all T: r_T^entry <= U_T ) >= 1 - delta, with U_T computable from matured labels.

Planned route ("lanes"): lane j = { t : t = j mod H }. Within a lane, D_t := X_t - p_t is a martingale difference w.r.t. the sub-sampled filtration (F_{j+kH})_k, because D_{j+kH} is F_{j+(k+1)H}-measurable and E[D_{j+kH} | F_{j+kH}] = 0. Apply a bounded-martingale confidence sequence per lane at level delta/H and add up.

---

## 1. Khosravi & Huo 2026 — Conformal Selective Acting (CSA), arXiv:2605.20270v1

**Setting** (Sec. 1 "The deployment loop", Sec. 4.1, p. 4). One item per round t. Policy samples output Y_t; a deterministic verifier returns V_t in {0,1} in the same round; a predictable score S_t and a predictable threshold q_t in a finite grid Q define the gate A_t = 1{S_t <= q_t} (release / abstain). Policy and score may be updated between rounds (non-stationary, adaptive stream). Filtration F_t contains V_t before round t+1.

**Assumptions**
- Assumption 4.2 (P) "predictable pipeline": pi_t, S_t are F_{t-1}-measurable; round-t information enters only (pi_{t+1}, S_{t+1}). (p. 4)
- Assumption 4.2 (M) "nested monotone gates": A_t(q) nondecreasing in q and P(V_t = 0 | S_t <= q, F_{t-1}) nondecreasing in q; delivered by a one-time held-out isotonic calibration. (p. 4)
- Theorem C.1 hypothesis "frontier stability": the oracle safe threshold q_t^* is nondecreasing within each epoch (App. C.2, p. 17). The paper states explicitly that Assumption 4.2 alone does not imply this.
- Drift budgets {eps_j} dominating within-epoch drift on safe rounds (Thm 5.1).
- Utility/power results additionally use Assumptions D.1–D.7 (App. D; calibration, local slope, actuation probability, margins).
- No i.i.d. / exchangeability. Losses bounded (binary). **Immediate verifier feedback is built into (P).** Monotonicity and calibration are required.

**Main guarantee.** Theorem 5.1 (p. 5, proof App. C.4 pp. 18–19): with probability >= 1 - 2 delta, simultaneously for all T >= 1,
R_T^act <= alpha + eps_bar_T + c1 sqrt( (log(1/delta) + log log(e N_T + e)) / (N_T v 1) ) + c2 (log(1/delta) + log log(e N_T + e)) / (N_T v 1),
where R_T^act = sum_t A_t (1 - V_t) / (N_T v 1) is the **realized selective failure frequency** among released items and N_T = sum_t A_t (Def. 4.1). Object: selective risk, anytime, high probability, rate N_T^{-1/2} (in released count, not wall-clock T). Universal constants c1, c2 are not given numerically.
Proof structure: (a) per-threshold betting e-process (Prop. 4.3, citing Waudby-Smith & Ramdas 2024) + Ville + Bonferroni over grid and epochs => no false certification (Thm C.1); (b) Lemma C.2: exp(lambda sum M_t - lambda^2 N_T / 8) is a supermartingale when E[M_t | F_{t-1}] <= 0, M_t = A_t((1 - V_t) - alpha) (Hoeffding's lemma, variance clock = N_T); (c) dyadic stitching over N_T.
Also: Thm 5.3 / 5.4 certification time upper and lower bounds Theta(mu^{-2} log(1/delta)) (lower bound on an i.i.d. Bernoulli instance); Thm 5.5 utility gap; Thm E.1 sparse verifier with predictable Bernoulli sub-sampling and inverse-probability weights.

**Applicability to our setting**
| Item | Verdict | Where / why |
|---|---|---|
| (i) delayed labels | **Needs change.** Assumption 4.2 (P) requires round-t information to be available before round t+1. The only mention of delay is an implementation remark, App. B.4 "Delayed evaluation: queue (X_t, Y_t) and run the verifier in batch; ... Assumption 4.2 holds as long as p_hat_{t+1} uses only verified examples" (p. 17). No theorem covers it; with outcomes unresolved at decision time the increment M_t is not F_t-measurable, so Lemma C.2 fails as stated. Fix = sub-sample / lanes. |
| (ii) overlapping positions | **Not applicable.** Not modelled; each round is resolved before the next. |
| (iii) same-day batch, arbitrary correlation | **Needs change.** One item per round. "Mid-batch updates fall outside Assumption 4.2" (Sec. 6 "What the empirics do not test", Sec. 7). Fix = aggregate a day into one increment with range n_t. |
| (iv) target = average entry-time conditional loss probability | **Needs change (direction reversed).** CSA assumes/establishes E[M_t | F_{t-1}] <= 0 (conditional risk <= alpha on the good event) and concludes a bound on the *realized* frequency. We observe realized frequency and bound the *conditional* average. Same martingale sum_t (X_t - p_t), opposite side; Lemma C.2's two-sided analogue gives it. Not stated in CSA. |
| (v) selection depends on matured history | **Directly applicable** in spirit: predictable gate, Assumption 4.2 (P). |

Remark: CSA is a *control* result and pays for it with (M) and frontier stability. A pure *monitoring* statement needs neither.

---

## 2. Xu, Karampatziakis & Mineiro 2024 — Active, anytime-valid RCPS (A-RCPS), arXiv:2406.10490v2

**Setting** (Sec. 2, pp. 5–6). Stream (X_t, Y_t) **i.i.d. from a fixed P**; canonical filtration F_t = sigma((X_i, Y_i)_{i<=t}). Calibration parameter beta in [0,1]; risk rho(beta) = E_P[r(X, Y, beta)]. Optional active labelling: label queried with predictable probability q_t(X_t) >= q_t^min; optional predictable risk predictor r_hat_t.

**Assumptions**
- i.i.d. data (stated p. 6; reiterated as the main limitation in Sec. 7, p. 18).
- Assumption 1: g and rho monotonically decreasing in beta, rho(1) = 0, rho right-continuous (p. 4).
- Loss in [0,1]; betting fractions lambda_t predictable and range-restricted.
- Assumption 2 (label-policy lower bound, used only for the regret result Thm 3).
- Labels, when queried, are available immediately.

**Main guarantee.** Definition 1 / Theorem 1 (p. 6), Theorem 2 (active, p. 8), Prop. 3 (with predictor): P( rho(beta_hat_t) <= theta for all t ) >= 1 - delta. Object: **marginal (population) risk** of the deployed parameter, anytime, high probability. Built on the betting e-process M_t(beta) = prod_i (1 + lambda_i (theta - R_i(beta))) and Ville. No explicit width rate; Thm 3 is a growth-rate regret bound.

**Applicability**
| Item | Verdict | Where / why |
|---|---|---|
| (i) delayed labels | **Not applicable as stated.** Supermartingale step uses E[R_t(beta) | F_{t-1}] with R_t observed at t (Prop. 1 proof, p. 7). |
| (ii) overlapping positions | **Not applicable.** |
| (iii) same-day batch | **Not applicable** (i.i.d. single points; "group of data points" only mentioned informally in the Introduction). |
| (iv) target | **Not applicable.** Target is a fixed population risk rho(beta); under i.i.d. the conditional and marginal risks coincide. No selective risk. The authors themselves say an extension to non-i.i.d. data would control risk only "in an average sense" via empirical-Bernstein supermartingales (Sec. 7) — i.e. exactly the average-conditional-mean estimand — but give no result. |
| (v) adaptive selection | **Needs change.** Betting fractions and label policy are predictable, but there is no accept/abstain selection of the evaluated points. |

---

## 3. MohammadpourAzari, Zarei & Fazli 2026 — Safe Portfolio Learning from Untrusted Predictions, arXiv:2611.04826v1

**Setting** (Sec. 2.1–2.5, pp. 5–9). One cohort opened per eligible date, held for H periods (implementation H = 5), assigned **cyclically to one of H "sleeves"** (Sec. 2.2, p. 6: "staggered rather than blockwise"). Maturity m_s = t_s + H - 1. Reward = Safe-relative normalized log wealth factor x_s in [-1,1]^3 for three actions (Safe / Follow / Reverse); full-information via shadow accounts. Decision for cohort s uses the master state after max{0, s - H} matured rewards. Evidence gate uses "a one-sided lower-bound statistic" computed only from matured rewards; collateral budget reserves worst-case loss for open cohorts.

**Assumptions.** Assumption 1 (A1)–(A6), p. 9: bounded matured rewards; master construction; two-clock causality (decision uses the exact earlier state, no same-date leakage); one-sided gate/budget; collateral bookkeeping; split-account identity. The paper says these are "architecture properties to verify, not statistical hypotheses". **No probabilistic model at all** ("The analysis is deterministic conditional on the realized bounded reward sequence", Sec. 3, p. 9).

**Main guarantees** (Sec. 3, pp. 10–12)
- Theorem 1: tracking regret of Fixed-Share + Hedge vs. any switching comparator (deterministic, every bounded sequence).
- Theorem 2 "exact delayed-decision reduction": sum_s <q_s^dec, x_s> >= sum_s <q_bar_s, x_s> - Delta_T^exact, where Delta_T^exact = sum_s || q_bar_s - q_bar_{tau(s)} ||_1 is the realized l1 movement of the master over the unresolved window. Additive, realized penalty.
- Lemma 1: one-sided intervention costs at most the removed active mass.
- Theorem 3 "anytime delayed collateral safety": pathwise accounting bound B(G - P) >= -S at every event.
- Theorem 4: maximum of the tracking and safety certificates.
Objects: **regret and wealth/collateral**, deterministic, pathwise. Nothing about loss probability, selective risk, or confidence statements. The gate's lower-bound statistic has no stated validity theorem in the main text ("the finite-sample calibration of the lower bound is part of the configuration", p. 8).

**Applicability**
| Item | Verdict | Where / why |
|---|---|---|
| (i) delayed labels | **Directly applicable (structure only).** Fixed horizon H, decisions use only matured cohorts (A3; Sec. 2.2, 2.5). |
| (ii) overlapping positions | **Directly applicable (structure only).** H staggered sleeves; Theorem 3 charges every open cohort its worst case. |
| (iii) same-day batch | **Different treatment.** One portfolio-level cohort per date; cross-sectional dependence is absorbed into one bounded scalar reward. Equivalent to our "aggregate the day". |
| (iv) target | **Not applicable.** No probabilistic target; our quantity cannot be read off Theorems 1–4. |
| (v) adaptive selection | **Directly applicable** (gate uses matured rewards only). |

Relevance for us: the *sleeve* construction is the same partition of entry dates as our lanes, already in a finance paper with delayed, overlapping cohorts — but used for deterministic bookkeeping, not for a martingale argument. It is prior art for the structure, not for the statistical statement. The paper itself contrasts its additive reduction with the "(d+1) factor of Weinberger and Ordentlich (2002)" (p. 11).

---

## 4. Gibbs & Candès 2021 — Adaptive Conformal Inference (ACI), arXiv:2106.00170

**Setting** (Sec. 2, pp. 2–3). Online; at each t a prediction set at level alpha_t; Y_t revealed before the next step; update alpha_{t+1} = alpha_t + gamma (alpha - err_t).

**Assumptions.** Prop. 4.1: none on the data-generating process; only alpha_1 in [0,1] and monotone quantile function with Q_hat_t(x) = -inf for x < 0, +inf for x > 1 (Sec. 4.1, p. 6). Theorems 4.1–4.2: hidden Markov model with spectral gap, stationarity, fixed score/quantile functions (Sec. 4.2). **Immediate feedback** — stated as a limitation: "The methods we develop are specific to cases where Y_t is revealed at each time point. However, there are many settings in which we receive the response in a delayed fashion or in large batches." (Sec. 7).

**Main guarantee.** Prop. 4.1 (p. 6): with probability one, for all T, | T^{-1} sum_{t<=T} err_t - alpha | <= (max{alpha_1, 1 - alpha_1} + gamma) / (gamma T). Object: **realized long-run marginal miscoverage frequency**, deterministic (pathwise), rate 1/T, obtained by *controlling* alpha_t. Thm 4.1: large-deviation bound under the HMM. Thm 4.2: E[(M(alpha_t | A_t) - alpha)^2] bound under the HMM.

**Applicability**
| Item | Verdict | Where / why |
|---|---|---|
| (i) delayed labels | **Not applicable as stated** (Sec. 7). A fixed-delay extension exists elsewhere (see 7c). |
| (ii) overlapping positions | **Not applicable.** |
| (iii) same-day batch | **Not applicable** ("large batches" listed as open, Sec. 7). |
| (iv) target | **Not applicable.** Realized marginal frequency, no selection, no conditional-probability statement; the guarantee is a property of the feedback loop, not an inference about the environment. A selective version would be vacuous without coverage constraints (abstain always). |
| (v) adaptive selection | **Not applicable** (no selection). |

---

## 5. Angelopoulos, Bates, Fisch, Lei & Schuster — Conformal Risk Control (CRC), arXiv:2208.02814v4

**Setting** (Sec. 1.1, p. 2). Batch/split: n calibration loss functions L_1,...,L_n and one test L_{n+1}; choose lambda_hat from calibration data.

**Assumptions.** Exchangeable L_1,...,L_{n+1}; each L_i non-increasing and right-continuous in lambda; L_i(lambda_max) <= alpha; sup L_i <= B (Theorem 1, p. 3). Theorem 2 adds i.i.d. and no-jump conditions. Prop. 1: fails for non-monotone losses.

**Main guarantee.** Theorem 1: E[L_{n+1}(lambda_hat)] <= alpha. Object: **marginal risk of one test point, in expectation**, finite-sample. Theorem 2: lower bound alpha - 2B/(n+1). Sec. 4.1: covariate shift with known weights (Prop. 2); arbitrary shift, Prop. 3: E[L_{n+1}(lambda_hat)] <= alpha + B sum_i TV(Z_i, Z_{n+1}).

**Applicability**
| Item | Verdict | Where / why |
|---|---|---|
| (i) delayed labels | **Not applicable** (no time structure). |
| (ii) overlapping positions | **Not applicable.** |
| (iii) same-day batch, arbitrary correlation | **Not applicable**; same-day trades are not exchangeable with past trades. Prop. 3's TV term is not computable. |
| (iv) target | **Not applicable.** One-step marginal expectation, not selective, not anytime, not conditional. |
| (v) adaptive selection | **Not applicable**; selection on calibration-dependent rules breaks exchangeability. |

---

## 6. Howard, Ramdas, McAuliffe & Sekhon — Time-uniform, nonparametric, nonasymptotic confidence sequences, arXiv:1810.08240v9 (identifier verified via arXiv search; published version Ann. Statist. 2021 — not checked by me)

**Setting** (Sec. 2). Abstract pair of adapted processes (S_t, V_t) on a filtration (F_t); S_t is typically a martingale sum of (X_i - E_{i-1} X_i), V_t an "intrinsic time" (variance process). No independence and no common mean are required: the estimand is mu_t = t^{-1} sum_{i<=t} E_{i-1} X_i, "the average conditional expectation" (Sec. 2 p. 4–5; Sec. 4.1 p. 13).

**Assumptions**
- Definition 1 (sub-psi condition, p. 5): for each lambda there is a supermartingale L_t(lambda) w.r.t. (F_t) with exp{lambda S_t - psi(lambda) V_t} <= L_t(lambda). V_t may be adapted rather than predictable.
- Table 3 (App. J, p. 47) lists sufficient conditions; relevant rows: "Hoeffding I": -g_t <= X_t <= h_t gives sub-Gaussian with V_t = sum_i ((g_i + h_i)/2)^2; "Bernstein", "Bennett", self-normalized rows. (Whether g_t, h_t must be predictable is stated in Howard et al. 2020, Sec. 2 — **not verified by me**; in our use the range n_t is F_t-measurable, i.e. predictable in the lane filtration.)
- Theorem 4 needs only X_t in [a, b] a.s. and a predictable sequence of guesses X_hat_t.

**Main guarantees**
- Theorem 1 (stitched boundary, p. 8): for sub-gamma processes, a closed-form boundary S_delta(v) = O( sqrt(v log log v) ) with P( exists t: S_t >= S_delta(V_t v m) ) <= delta. Example (11): for 1-sub-Gaussian increments, P( exists t: S_t >= 1.7 sqrt( t (log log(2t) + 0.72 log(5.2/delta)) ) ) <= delta.
- Theorem 4 (empirical-Bernstein CS, p. 14): if X_t in [a,b] and u is a sub-exponential uniform boundary with crossing probability delta for scale c = b - a, then P( for all t: | X_bar_t - mu_t | < u( sum_i (X_i - X_hat_i)^2 ) / t ) >= 1 - 2 delta. Explicitly "does not require that observations share a common mean".
- Sec. 3.6 / Prop. 4: unimprovability of mixture boundaries (not read in detail).
Object: anytime, high-probability, two-sided, **for the running average of conditional means** — the same type of estimand as r^entry.

**Applicability**
| Item | Verdict | Where / why |
|---|---|---|
| (i) delayed labels | **Needs change.** S_t must be adapted: X_t must be F_t-measurable for the filtration in which E_{t-1} is taken. With maturity lag H, X_t - E[X_t | F_t] is not a martingale difference sequence for (F_t). Fix: apply the theorem on each lane with the sub-sampled filtration; then it applies verbatim. |
| (ii) overlapping positions | **Needs change** (same fix). Nothing in Def. 1 forbids the unresolved positions' partial information from being in the filtration, which is exactly what the lane filtration contains. |
| (iii) same-day batch, arbitrary correlation | **Directly applicable** after aggregating a day into one observation X_t in [0, n_t] (Hoeffding I row with predictable range, or Theorem 4 with [a,b] = [0, M]). The price is a variance proxy of order n_t^2 rather than n_t. |
| (iv) target | **Directly applicable.** mu_t is by definition the average conditional expectation. |
| (v) adaptive selection | **Directly applicable.** Predictable selection only changes the (predictable) range; the martingale property is unaffected. |

---

## 7. Delayed-feedback literature

### 7a. Joulani, György & Szepesvári 2013 — Online Learning under Delayed Feedback, arXiv:1306.0686v2

**Setting** (Sec. 2). Partial-monitoring online learning; feedback for round t arrives at the end of round t + tau_t, time-stamped; adversarial or i.i.d. outcomes; delays usually i.i.d. and independent of the forecaster's past predictions (stochastic setting allows dependence on the action).
**Main results.** Algorithm 1 (BOLD, Sec. 3.1): run several instances of a non-delayed base algorithm; an instance is "busy" until the feedback of its last prediction arrives; when all are busy, open a new instance. With constant delay this "reduces to the algorithm of Weinberger & Ordentlich (2002)", which "subsamples the reward sequence by the constant delay tau+1 and runs a base algorithm on each of the tau+1 subsampled sequences", giving regret (tau+1) f(n/(tau+1)), minimax optimal in the full-information case "as can be seen by constructing a reward sequence that changes only in every tau+1 times". Theorem 1: E[R_n] <= E[(G_n^* + 1) f_Base(n/(G_n^* + 1))], G_n^* = max number of outstanding feedbacks; **assumes the delays are independent of the forecaster's prediction.** Sec. 3.2 (QPM-D): stochastic setting, additive penalty O(G_n^*).
Object: **expected regret**. No concentration inequality or confidence sequence is stated.

**Applicability:** (i) structure directly applicable — the lane construction *is* the Weinberger–Ordentlich / BOLD sub-sampling, and with f(n) = sqrt(n) the factor (tau+1) f(n/(tau+1)) = sqrt((tau+1) n) is the same sqrt(H) price; (ii) yes in structure; (iii) not treated; (iv) not applicable (regret, not inference); (v) yes. The matching lower-bound construction (block-constant sequence) is the same device that gives the sqrt(H) lower bound for monitoring (see Sec. 8).

### 7b. Wang & Simeone 2026 — Capacity-Constrained Delayed Feedback for Online Conformal Risk Control, arXiv:2611.17059v1 (identifier taken from `paper/references.bib`, key `wang2026caocrc`)

**Setting** (Sec. II, pp. 6–9). Arbitrary data sequence; loss L_t in [0,1] becomes available at the end of round t + d_t, and only if round t was continuously tracked; at most K rounds can be tracked. Delays arbitrary but bounded by d_max (Assumption 1(a)) or i.i.d. (1(b)).
**Assumptions.** Assumption 2 (scores in [0,B]); Assumption 3 (full set has zero loss, empty set has loss one); Assumption 4/5 (underload conditions on the proxy-delay distribution).
**Main results.** Lemma 2 (unlimited capacity, delayed OCRC): RiskGap(T) = | E[ T^{-1} sum L_t ] - alpha | <= B/(eta T) + (d_max + 1)/T for any data and delay sequence. Theorem 1: RiskGap(T) <= (B/eta + K + 1)/(F(d_max) T) + exp(-K h(.)) under arbitrary delays. Scaling O((d_max/T)^{K/(K+1)}).
Object: **long-run average marginal risk, in expectation over the policy's internal randomness**, achieved by threshold control. Not selective, not anytime-in-probability, not a statement about conditional probabilities.

**Applicability:** (i) directly handles bounded delays (for its own target); (ii) pending rounds are modelled, but as a tracking-capacity problem; (iii) not treated; (iv) **not applicable**; (v) not applicable (no selection; control of a threshold with trivially safe full set — the trading analogue would be "never trade").

### 7c. Found via 7b's related-work section and one web search (abstract / key sections only)

- **El Halabi & Brandt 2026, arXiv:2609.07251** — ACI under fixed delay tau. Sec. 4.1 decomposes the tau-delayed recursion into tau interleaved "phases", each a standard ACI recursion, and recombines phase-wise bounds into a long-run coverage bound with explicit tau-dependence. This is the lane construction inside the conformal literature. Target is still the realized marginal coverage frequency. (Read: abstract, contributions, Sec. 4.1. Bounds in Sec. 4.2–4.4 **not read**.)
- **Lindon & Kallus 2026, arXiv:2603.25971v2** — design-based anytime-valid inference for randomized experiments with delayed outcomes and staggered entry. Randomness comes only from treatment assignment; they show each arm's IPW error is a martingale only under an arm-specific event-time filtration and that the treatment-effect error "is not a martingale under any filtration", and therefore combine two confidence sequences by a union bound (Sec. 4.1–4.2; Thm 4.6 is an *asymptotic* confidence sequence with the Howard et al. normal-mixture boundary). Closest work I found on "confidence sequences under delay"; the setting (potential outcomes, randomized assignment) is different from ours, but the lesson — delay forces a choice of filtration and a union bound across filtrations — is the same. (Read: abstract, introduction, Defs 4.1–4.3, Thm 4.6, start of Sec. 4.2. Rest **not read**.)
- Ryabchenko, Attias & Roy (COLT 2025; arXiv:2606.11711) on capacity-constrained delayed online learning — cited by 7b; **not read**.
- Weinberger & Ordentlich 2002 (IEEE Trans. IT) — known to me only through the descriptions in Joulani et al. Sec. 2.1/3.1 and MohammadpourAzari et al. Sec. 1.1/3.2; **original not read.**
- I searched arXiv (project tool) and the web for "confidence sequence / e-process / martingale concentration under delayed feedback" and did **not find** a paper stating a time-uniform bound for the average entry-time conditional mean under bounded delay with overlapping outcomes. Absence of evidence from two or three queries is weak; treat as "not found", not "does not exist". Delayed-bandit papers (e.g. Vernade et al. 2017; Pike-Burke et al. 2018; Lancewicki et al. 2021) were **not read**; they are named from memory as leads for `literature-scout` to verify.

---

## 8. What is left to prove

### 8.1 Is the monitoring proposition a direct corollary?

**Essentially yes.** It is not a corollary of any *single* theorem above (none of them has delayed labels and the conditional-mean target at once), but it follows in a few lines from two known ingredients:

1. **Howard et al. Theorem 4** (or Definition 1 + Table 3 "Hoeffding I" + Theorem 1) — a time-uniform bound for the running average of conditional means of bounded, non-identically distributed, dependent observations; estimand is exactly of the type of r^entry.
2. **The sub-sampling reduction of Weinberger & Ordentlich 2002 / Joulani et al. 2013 (BOLD)** — with delay at most H, the H interleaved sub-sequences are delay-free. Already transplanted to conformal (El Halabi & Brandt 2026, phases) and to portfolios (MohammadpourAzari et al. 2026, sleeves).

How to plug in (sketch, **not a checked proof**): fix lane j, set G_k = F_{j+kH}, observations X_{j+kH} in [0, n_{j+kH}] with n predictable w.r.t. (G_k). X_{j+kH} is G_{k+1}-measurable, so Howard Thm 4 (range M) or the sub-Gaussian boundary with V = sum n_t^2 / 4 gives a (1 - delta/H) confidence sequence for sum_{t in lane j} p_t. Union over lanes; by Cauchy–Schwarz sum_j sqrt(V_j l) <= sqrt(H sum_j V_j l), so, up to constants and iterated logarithms,

  r_T^entry <= (matured losses + trades not yet matured) / N_T + O( sqrt( H * (sum_t n_t^2) * log(H/delta) ) / N_T ),  and sum_t n_t^2 <= M N_T,

i.e. slack O( sqrt( H M log(H/delta) / N_T ) ). With H = 1, M = 1 this is literally Howard Thm 4 restricted to selected rounds, and it is the mirror image of CSA Lemma C.2 + stitching (CSA goes from conditional to realized; we go from realized to conditional).

Consequences for the paper: this should be labelled a **proposition / corollary with full attribution**, not a theorem contribution. CSA and A-RCPS are *not* what makes it a corollary (they need immediate feedback, and CSA additionally needs monotonicity/frontier stability that monitoring does not); Howard et al. plus the delayed-feedback sub-sampling trick are.

### 8.2 What exactly differs from the literature

- Combination not found stated anywhere: (delayed + overlapping) x (same-day batch of arbitrary dependence) x (selective, entry-time conditional target) x (time-uniform). Each factor is individually known.
- Details that need care but are routine: the bound at calendar time T must treat the up-to-(H-1) unmatured days (count them as losses, or state the bound for matured days only); the filtration must be declared (the bound is for conditional probabilities given *that* filtration; richer filtrations change the target, not validity); H lanes vs. two lanes of length-H blocks (see 8.3 (b)).

### 8.3 Strengthenings not found in what I read, with my feasibility judgment

(a) **Lower bound: the sqrt(H) (and sqrt(M)) factor is unavoidable under arbitrary dependence.** — *Easy to medium.* Two-point (Le Cam) argument on a block-constant instance: all trades opened within a block of H days share one Bernoulli(q) outcome revealed at the end of the block, so p_t = q n_t while the monitor sees only T/H independent coins; any valid upper confidence bound must have width of order sqrt(H/T) = sqrt(HM/N_T) when n_t = M. This is the monitoring analogue of the Weinberger–Ordentlich lower-bound construction quoted in Joulani et al. Sec. 3.1. The time-uniform version (log log factor) is harder and probably not worth it. I have not written this out; treat as a conjecture with a clear proof plan.

(b) **Dependence-adaptive bound that removes sqrt(H) when overlapping trades are only weakly dependent.** — *Medium; may fail for the stated target.* Idea: treat a block of H days as one observation (two lanes: odd / even blocks) and use an empirical-Bernstein boundary so the leading term scales with the *realized* block variance (order H M per block under weak dependence, order H^2 M^2 in the worst case), giving N_T^{-1/2} without sqrt(H) in favourable cases. Obstacle I see: within a block p_t is not measurable at block start, so Howard Thm 4 applied to block sums estimates sum_t E[X_t | F_{block start}], not sum_t E[X_t | F_t]. The martingale sum_t (X_t - p_t) still has block-start-conditional mean zero, but its increments are unobservable, so a self-normalised variance proxy is not directly available; the cross term Cov(X_s - p_s, p_t - E[p_t | F_start]) for t > s need not vanish. Either the target must be changed to "block-start conditional probability" (then it is again a corollary), or a new argument is needed. This is the most interesting open piece and the only one that could plausibly be called a new result.

(c) **Variance-adaptive bound scaled by N_T rather than T.** — *Easy (corollary).* Per-lane empirical-Bernstein (Howard Thm 4) with the day as the unit already gives a slack driven by sum_t (X_t - X_hat_t)^2 and normalised by N_T; CSA's Lemma C.2 already uses N_T as the variance clock. Gain over the Hoeffding version is real only when same-day outcomes are far from perfectly correlated or loss probabilities are far from 1/2. Not novel.

(d) **Unbounded or outcome-dependent clearing times (suspension, limit-down).** — two routes:
   - *Censoring at H — easy.* Count "not yet sellable at t+H" as a loss (or mark to market at t+H and say so). Because the bound is one-sided, X_t <= X_t^cens gives a valid, conservative bound for the original target. Purely definitional.
   - *Adaptive lanes (BOLD-style) — medium.* Assign each entry day to a lane that is "free" (its previous day fully matured); lane membership is then decided by stopping times, and the per-lane martingale property should survive by optional sampling **without** assuming delays independent of outcomes (Joulani et al. Thm 1 assumes independence, but that is for regret, not for the martingale property). The number of lanes becomes random (max number of simultaneously unresolved days), so the error budget must be spread over a countable family (e.g. delta_L proportional to 1/L^2) and the slack depends on the realized lane count. Trades unresolved at time T must be counted at worst case; since slow-to-clear trades are disproportionately losers this term cannot be dropped. I believe this is provable but have not checked the stopping-time details; I did not find it in the papers read.

(e) **From monitoring to control / prediction of the next trade.** — *Hard or impossible without extra assumptions*; needs CSA-type monotonicity + frontier stability or an explicit drift budget, and CSA's Theorem 5.1 structure would then be the template. Consistent with `literature/positioning.md` Sec. 1 item 4. Not recommended as a goal.

(f) **Is the union over lanes itself necessary (could one mix the H lane e-processes instead)?** — *Probably not improvable in general.* The lane processes are supermartingales in H different sub-sampled filtrations; their average is not a supermartingale in a common filtration (the same obstruction Lindon & Kallus prove in their setting). Replacing H lanes by 2 block-lanes changes log(H/delta) to log(2/delta) but not the sqrt(H). Low value.

### 8.4 Recommendation

Present the monitoring bound as a short, fully attributed proposition (Howard et al. + sub-sampling), put its proof in the appendix, and — if a theory contribution is wanted — spend effort on (a) the matching lower bound and (b)/(d-adaptive) as candidate new results, with (b) flagged as possibly unprovable for the entry-time target. Whether that is enough for a "theory + experiments" paper is a judgment for the PI and the user.

### 8.5 Bibliography note for the PI

`paper/references.bib` does not yet contain Howard et al. (arXiv:1810.08240), Joulani et al. (arXiv:1306.0686), El Halabi & Brandt (arXiv:2609.07251) or Lindon & Kallus (arXiv:2603.25971) (checked by grep for the first two). I did not edit the bib file; `literature-scout` should add and verify them. PDFs downloaded to `literature/pdfs/`: arxiv_1810.08240, arxiv_1306.0686, arxiv_2611.17059, arxiv_2603.25971, arxiv_2609.07251.

---

## 9. What I did not read (or could not verify)

- CSA: Appendix D (structural layer) beyond the assumption list; Appendices F–I (experiments); proofs of Thm 5.3–5.5 only skimmed. Constants c1, c2 in Thm 5.1 are not specified in the paper.
- A-RCPS: proofs in Sec. 5, experiments, Sec. 6 related work.
- MohammadpourAzari et al.: appendices A–B and the online supplement (in particular the exact definition and calibration of the evidence gate's lower-bound statistic); experiments. My statement that the gate statistic has no validity theorem is based on the main text only.
- ACI: appendix proofs; Sec. 5–6.
- CRC: Sec. 3 examples, Sec. 4.2–4.5, appendices. I read v4 (June 2025); it has no online/sequential section.
- Howard et al.: only Sec. 2, Thm 1, Thm 4, Table 3. Not read: mixture boundaries (Sec. 3.2–3.5), Sec. 3.6 optimality, proofs, and the companion paper Howard et al. 2020 (where the predictability requirements behind Table 3 are stated). Journal publication details unverified.
- Joulani et al.: Sec. 3.2 onward only skimmed; the two-column PDF extracted poorly, so Theorem 1 was reconstructed from interleaved text — re-check against the PDF before quoting.
- Wang & Simeone: Sec. IV–VII and supplementary proofs beyond the statements of Lemma 2 and Theorem 1.
- El Halabi & Brandt; Lindon & Kallus: only the parts listed in 7c.
- Not read at all: Weinberger & Ordentlich 2002; Waudby-Smith & Ramdas 2024 (betting confidence sequences, the source of CSA Prop. 4.3 and A-RCPS eq. (5)); Ryabchenko et al.; delayed-bandit papers; Hultberg et al. 2026, Bai & Jin 2026 (SCoRE), Xu–Guo–Wei 2025, Gangrade et al. 2021 listed in `novelty_report.md`.
- All sketches in Sec. 8 (the corollary derivation, the lower bound, the adaptive-lane argument, the obstacle in (b)) are my own reasoning, **not verified numerically and not externally reviewed**.
- Extraction caveat: Greek symbols were dropped by `pdftotext`; formulas above were reconstructed from context.

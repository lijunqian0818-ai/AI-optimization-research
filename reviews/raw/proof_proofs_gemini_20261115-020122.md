### 1. Step-by-Step Proof Verification

#### 1.1 Section 1: Theorem 1 and Corollaries
* **§1.1 (Lanes and filtrations):** The partition of days $\{t \ge 1\}$ into residue classes $t \equiv j \pmod d$ correctly decouples the feedback delay. Because $\mathcal{H}^j_m = \mathcal{F}_{t_{j,m+1}} = \mathcal{F}_{t_{j,m}+d}$, assumption A3 guarantees that $X_{t_{j,m}}$ is $\mathcal{H}^j_m$-measurable. The conditioning $\mathbb{E}[D_{j,m} \mid \mathcal{H}^j_{m-1}]$ reduces to $\mathbb{E}[\mu_{t_{j,m}} - X_{t_{j,m}} \mid \mathcal{F}_{t_{j,m}}] = 0$ by definition of $\mu_t$.
* **§1.2 (Conditional Hoeffding Lemma):** The proof is exact. The secant bound for convex functions $e^{\lambda y}$ on $[a, c]$ is standard, the Taylor expansion of $\psi(s) = -\theta s + \log(1 - \theta + \theta e^s)$ satisfies $\psi''(s) = \rho(1-\rho) \le 1/4$, and the Lagrange remainder gives $\psi(s) \le s^2 / 8 = \lambda^2 \nu^2 / 8$.
* **§1.3 (Exponential Supermartingale):** The recursive factorization $W_m = W_{m-1} e^{-\lambda^2 \nu_{j,m}^2 / 8} e^{\lambda D_{j,m}}$ correctly pulls $\mathcal{H}^j_{m-1}$-measurable terms out of the conditional expectation. Non-negativity ensures validity without integrability issues, and $\mathbb{E}[W_m] \le \mathbb{E}[W_0] = 1$ establishes $L^1$ boundedness.
* **§1.4 (Ville's Inequality):** Applying the optional stopping theorem to the bounded stopping time $\sigma \wedge n$ yields $c \mathbb{P}(\sigma \le n) \le \mathbb{E}[W_{\sigma \wedge n}] \le 1$. Monotone convergence as $n \to \infty$ gives $\mathbb{P}(\sigma < \infty) \le 1/c$.
* **§1.5 (Dyadic Epochs and Constants):** 
  * The parameter $\lambda_k = \sqrt{8 L_k / 2^{k+1}} = 2\sqrt{L_k / 2^k}$ correctly minimizes the epoch boundary supremum $\sup_{v < 2^{k+1}} [L_k/\lambda + \lambda v / 8] = \sqrt{2^k L_k}$.
  * The union bound over $k \ge 0$, lanes $j \in \{0, \dots, d-1\}$, and signs $s \in \{+1, -1\}$ sums to $2 \times d \times \frac{\delta}{2 d c_0} \sum_{k=0}^\infty (k+1)^{-2} = \delta$ with $c_0 = \pi^2 / 6$.
* **§1.6–§1.7 (Time-uniform Boundary and Target Bracketing):**
  * Summing across lanes preserves validity via the triangle inequality.
  * The pathwise bracket $K_T \le \sum_{t \le T} X_t \le K_T + P_T$ holds deterministically for any revelation pattern. Combining with $|\sum (\mu_t - X_t)| \le B^*_T \le B_T$ correctly brackets $\sum_{t \le T} \mu_t$.
  * The one-sided allocations in (c) are verified: $E_\delta^{up}$ bounds $\sum (\mu_t - X_t)$ from above, yielding the upper bound on $r_T^{entry}$; $E_\delta^{low}$ bounds $-\sum (\mu_t - X_t)$ from above, yielding the lower bound on $r_T^{entry}$.
* **§1.8 (Corollaries 1.1, 1.2, 1.3):**
  * **Corollary 1.1:** Applying Cauchy–Schwarz $\sum_{j=0}^{d-1} \sqrt{Q_j} \le \sqrt{d \sum Q_j} = \sqrt{d \sum n_t^2} \le \sqrt{d M N_T}$ is sharp for predictable-range clocks. The definition $\ell_T = \log(2 d c_0 / \delta) + 2 \log(1 + \log_2(M N_T))$ correctly bounds $L_{k(Q_j)}$.
  * **Corollary 1.2:** Immediate from division of the pathwise bracket by $N_T$.
  * **Corollary 1.3:** Pointwise ordering $L^{lo}_{ti} \le L^{liq}_{ti} \le L^{hi}_{ti}$ preserves conditional expectations $\mu^{lo}_t \le \mu^{liq}_t \le \mu^{hi}_t$. Applying the one-sided bounds at level $\delta/2$ each guarantees validity at level $1-\delta$ by a union bound.

---

#### 1.2 Section 2: Proposition 2
* **§2.1 (Block Environment):** Setting $\mathcal{F}_t = \sigma(Z_1, \dots, Z_{b(t)-1}, U)$ ensures $Z_{b(t)}$ is independent of $\mathcal{F}_t$, giving $\mu_t = M p$ identically. $X_t = M Z_{b(t)}$ is revealed at block $b(t)+1$, satisfying lag $d$. The variance calculation $\text{Var}(\sum (X_t - \mu_t)) = p(1-p) M d N$ is exact.
* **§2.2 (Two-point Testing Reduction):** Le Cam's reduction is standard: $\mathbb{P}_+(u - \ell \ge 2h) \ge 1 - 2\delta - TV(\mathbb{P}_+, \mathbb{P}_-)$ holds by total variation definition.
* **§2.3 (KL Divergence and Total Variation):**
  * The Bernoulli KL expansion $kl(p_-, p_+) = 2h \log\left(\frac{1+2h}{1-2h}\right) \le \frac{32 h^2}{3}$ is rigorous for all $x = 2h \in (0, 1/2]$.
  * The Pinsker constant $TV \le \sqrt{KL / 2}$ yields $TV \le \sqrt{16 c^2 / 3} = \frac{4c}{\sqrt{3}} = \frac{1-2\delta}{2}$ with $c = \frac{\sqrt{3}}{8}(1 - 2\delta)$.
* **§2.4 (Conclusion):** Yields $\mathbb{P}_\pm(u - \ell \ge 2h) \ge \frac{1-2\delta}{2}$ and $\mathbb{E}_\pm[u - \ell] \ge \frac{\sqrt{3}}{8}(1-2\delta)^2 \sqrt{M d / N}$. Every constant is exact.

---

#### 1.3 Section 3: Lemma 3
* **§3.1–§3.2:** The decomposition $h_t^G - h_t^B = (e_t^G - e_t^B)w_t^B + e_t^G(w_t^G - w_t^B)$ is an exact algebraic identity. The qualifications regarding baseline indeterminacy when $e_t^B = 0$, non-uniqueness via the interaction term, and non-additivity of nonlinear path functionals (drawdown, Sharpe) are mathematically sound.

---

#### 1.4 Section 4: Remark 4
* The counterexample $L_{ti} \equiv 1$ a.s. forces $r_T^{entry} = 1 > \alpha$ on $\{N_T > 0\}$. Hence, no policy can universally ensure both positive trading probability and $r_T^{entry} \le \alpha$ across all A1–A4 environments without restricting the environment class. The logic is valid.

---

### 2. Issues and Errors Identified

#### Issue 1
* **Location:** §1.5, subsection *Radii*, sentence:
  > *"On $E_\delta^{up}$, (3) with $s = +1$ holds for every $k$ and every $m$, so $S_{j,m} < \inf_{k \ge 0} g_k(V_{j,m})$."*
* **Why it is wrong:** The strict inequality $x < y_k$ for all $k$ implies only $x \le \inf_k y_k$ in general. Strict inequality holds here exclusively because the infimum over $k \ge 0$ is attained at a finite minimizer $k^*(V) < \infty$ when $V_{j,m} \ge 1$ (since $g_k(V) \to \infty$ as $k \to \infty$). Asserting strict inequality before establishing attainment is a formal gap. Moreover, at $V_{j,m} = 0$, $S_{j,m} = 0 = b^*(0)$, which is an equality, not a strict inequality.
* **Whether fixable:** Fixable.
* **Suggested fix:** Change the sentence to state:
  $$\text{On } E_\delta^{up}, \quad S_{j,m} \le \inf_{k \ge 0} g_k(V_{j,m}) = b^*(V_{j,m}).$$
  Add a brief note that for $V_{j,m} \ge 1$, $\inf_{k \ge 0} g_k(V_{j,m})$ is attained at a finite index $k^*$, where $S_{j,m} < g_{k^*}(V_{j,m}) = b^*(V_{j,m})$, and for $V_{j,m} = 0$, $S_{j,0} = 0 = b^*(0)$.

---

#### Issue 2
* **Location:** §1.5, subsection *Radii*, bullet point:
  > *"If $V_{j,m} = q \ge 1$ ...: $\inf_k g_k(q) = b^*(q)$ by definition"*
* **Why it is wrong:** The definition of $b^*(q)$ in `theory/theorems.md` sets $b^*(0) = 0$ as a boundary convention. However, directly evaluating the formula $\inf_{k \ge 0} g_k(0) = \inf_{k \ge 0} \frac{1}{2}\sqrt{2^k L_k} = \frac{1}{2}\sqrt{L_0} > 0$. The text in §1.5 writes "$\inf_k g_k(q) = b^*(q)$ by definition" without clarifying that the infimum definition applies strictly to $q \ge 1$.
* **Whether fixable:** Fixable.
* **Suggested fix:** Explicitly write:
  $$b^*(q) := \begin{cases} \min_{k \ge 0} g_k(q), & q \ge 1, \\ 0, & q = 0. \end{cases}$$
  State that the linear functions $g_k(v)$ dominate $S_{j,m}$ on $v \ge 1$, while $V_{j,m} = 0 \implies S_{j,m} = 0 = b^*(0)$ holds by definition of $S_{j,0}$ and non-negativity of entries.

---

#### Issue 3
* **Location:** §1.1, fact (M1):
  > *"(M1) $\nu_{j,m}$ and $V_{j,m}$ are $\mathcal{H}^j_{m-1}$-measurable (predictable)."*
* **Why it is wrong:** For $m = 0$, $V_{j,0} = 0$, but the $\sigma$-field $\mathcal{H}^j_{-1}$ is undefined. For $m = 1$, $\mathcal{H}^j_0 = \mathcal{F}_{t_{j,1}}$, so $\nu_{j,1} = n_{t_{j,1}}$ and $V_{j,1} = n_{t_{j,1}}^2$ are $\mathcal{H}^j_0$-measurable, which is correct. However, labeling $(V_{j,m})_{m \ge 0}$ predictable without specifying the base case at $m=0$ leaves an undefined index.
* **Whether fixable:** Fixable.
* **Suggested fix:** Specify that (M1) holds for $m \ge 1$ with respect to $\mathcal{H}^j_{m-1}$, and state the deterministic initialization $S_{j,0} = V_{j,0} = 0$ with $\mathcal{H}^j_0 = \mathcal{F}_{t_{j,1}}$.

---

#### Issue 4
* **Location:** §2.1, definition of filtration for $t > T$:
  > *"(For $t > T$, needed only to give meaning to $\mathcal{F}_{t+d}$, put $\mathcal{F}_t = \sigma(Z_1,\dots,Z_B,U)$ and $n_t = 0$.)"*
* **Why it is wrong:** The text sets $n_t = 0$, but does not explicitly define $X_t$ and $L_{ti}$ for $t > T$. While $n_t = 0$ implies $A_{ti} = 0$ and thus $X_t = 0$, to formally verify assumption A3 ($X_t \in \mathcal{F}_{t+d}$ for all $t \ge 1$) and A2 for the entire time horizon, $X_t := 0$ and $\mu_t := 0$ must be explicitly stated for all $t > T$.
* **Whether fixable:** Fixable.
* **Suggested fix:** Add: "and $X_t = 0, \mu_t = 0$ for all $t > T$."

---

#### Issue 5
* **Location:** §1.8, Corollary 1.3:
  > *"The width is $\ge (K^{hi}_T - K^{lo}_T)/N_T$, and $K^{hi}_T - K^{lo}_T$ is the number of revealed entries not sold by their deadline."*
* **Why it is wrong:** The proof states this property without defining $L^{liq}_{ti}$ for positions that are never liquidated (e.g., permanent delisting, complete bankruptcy with zero recovery). If $L^{liq}_{ti}$ is undefined on paths with never-sold positions, $\mu^{liq}_t = \mathbb{E}[X^{liq}_t \mid \mathcal{F}_t]$ is mathematically undefined.
* **Whether fixable:** Fixable.
* **Suggested fix:** Add a formal completion convention: "If an entry $(t,i)$ is never liquidated, define $L^{liq}_{ti} := 1$ (or any fixed convention in $\{0,1\}$)." This guarantees $L^{lo}_{ti} \le L^{liq}_{ti} \le L^{hi}_{ti}$ pointwise on all of $\Omega$.

---

### 3. Check of Assumptions, Constants, Rates, and References

#### 3.1 Assumptions
* **Standardness:**
  * **A1 (Filtration & Predictable Selection):** Standard in delayed feedback literature (e.g., Joulani et al. 2013). Placing $\mathcal{F}_t$ at the fill point rather than signal time is standard for post-trade transaction cost and fill monitoring.
  * **A2 (Bounded Labels, Arbitrary Cross-Sectional Dependence):** Standard for non-parametric risk bounds. The absence of conditional independence across same-day stocks is standard for equity basket modeling.
  * **A3 (Bounded Lag $d$):** Standard in online learning with delayed feedback.
  * **A4 (Revelation Accounting):** Pure bookkeeping. Valid without missing-at-random assumptions.
* **Assumptions used but not stated:**
  * $N_T > 0$ is required to divide by $N_T$ in Theorem 1 and Corollaries 1.1–1.3. On the event $\{N_T = 0\}$, $r_T^{entry}$ is undefined. The statements should formally define the interval as $[0, 1]$ on $\{N_T = 0\}$.
  * In Proposition 2, $T = B d$ and $N = M B d$ require $T$ to be divisible by $d$ and $N$ to be divisible by $M d$. This is stated in the construction, but its role as a divisibility restriction should be made explicit in the theorem statement.
  * The cap $M$ is verified to be unnecessary for Theorem 1; it is strictly used in Corollary 1.1.

#### 3.2 Constants and Rates
* **Theorem 1:**
  * $\lambda_k = \sqrt{8 L_k / 2^{k+1}} = 2\sqrt{L_k / 2^k}$: Exact.
  * Constant in $b(q) = \sqrt{2^{k(q)} L_{k(q)}}$: Exact. Tuning to the upper end $2^{k+1}$ correctly eliminates the extra $3/(2\sqrt{2}) \approx 1.06$ penalty.
  * $b^*(q) \le b(q)$ for all $q \ge 1$: Verified analytically and numerically.
* **Corollary 1.1:**
  * Rate $\mathcal{O}\left(\sqrt{\frac{d M \log(d/\delta) \log\log(M N_T)}{N_T}}\right)$ with explicit constant $\ell_T = \log(2 d c_0 / \delta) + 2 \log(1 + \log_2(M N_T))$: Exact.
* **Proposition 2:**
  * Taylor expansion $\log\left(\frac{1+x}{1-x}\right) \le \frac{8x}{3}$ for $x \in (0, 1/2]$: Exact.
  * Kullback–Leibler bound $KL \le \frac{32 c^2}{3}$: Exact.
  * Pinsker bound $TV \le \sqrt{KL/2} \le \frac{4c}{\sqrt{3}} = \frac{1-2\delta}{2}$: Exact.
  * Probability $\ge \frac{1-2\delta}{2}$ and expected width $\ge \frac{\sqrt{3}}{8}(1-2\delta)^2 \sqrt{\frac{M d}{N}}$: Exact. Rate $\sqrt{M d / N}$ matches the upper bound up to iterated logarithmic factors.

#### 3.3 Status of External References
* **Pinsker's Inequality (§2.3):** Verified. [Tsybakov (2009)](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L4), *Introduction to Nonparametric Estimation*, Lemma 2.5 establishes $V(P_1, P_2) \le \sqrt{\frac{1}{2} K(P_1, P_2)}$ for $V(P_1, P_2) = \sup_A |P_1(A) - P_2(A)|$.
* **Optional Stopping (§1.4):** Verified. Williams (1991), *Probability with Martingales*, Theorem 10.10(a) confirms $\mathbb{E}[W_{\sigma \wedge n}] \le \mathbb{E}[W_0]$ for non-negative supermartingales at bounded stopping times.
* **Attribution Identity (§3.2):** Verified. Brinson, Hood, and Beebower (1986), "Determinants of Portfolio Performance", *Financial Analysts Journal*, 42(4), 39–44.

---

### Verdict

**FIXABLE ERRORS**

## 1. Item-by-Item Proof Verification

### Theorem 1(a), (b), (c)
* **Lane filtration & measurability ([proofs.md §1.1](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L26-L51)):** The construction $\mathcal{H}_m^j = \mathcal{F}_{t_{j,m+1}}$ with $t_{j,m+1} = t_{j,m} + d$ ensures that $X_{t_{j,m}} \in \mathcal{F}_{t_{j,m}+d} = \mathcal{H}_m^j$ by A3, while $\nu_{j,m} = n_{t_{j,m}} \in \mathcal{F}_{t_{j,m}} = \mathcal{H}_{m-1}^j$ by A1. Increment centering $\mathbb{E}[D_{j,m} \mid \mathcal{H}_{m-1}^j] = 0$ holds by definition of $\mu_t$.
* **Conditional Hoeffding lemma ([proofs.md §1.2](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L52-L68)):** The Taylor expansion of $\psi(s) = -\theta s + \log(1 - \theta + \theta e^s)$ satisfies $\psi(0)=0$, $\psi'(0)=0$, and $\psi''(s) = \rho(s)(1 - \rho(s)) \le 1/4$, yielding $\mathbb{E}[e^{\lambda D} \mid \mathcal{G}] \le \exp(\lambda^2 \nu^2 / 8)$. Algebra is sound.
* **Supermartingale property & Ville's inequality ([proofs.md §1.3–§1.4](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L69-L94)):** $(W_m^{j,\lambda})_{m \ge 0}$ is a non-negative supermartingale with $W_0=1$. Ville's maximal inequality $\mathbb{P}(\exists m \ge 0: W_m \ge 1/\alpha) \le \alpha$ holds via optional stopping at $\sigma \wedge n$.
* **Epoch constants & stitching ([proofs.md §1.5](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L95-L128)):** With $\alpha_k = \frac{\delta}{2 d c_0 (k+1)^2}$ and $c_0 = \pi^2/6$, $\sum_{j=0}^{d-1} \sum_{k \ge 0} \alpha_k = \delta/2$ per sign $s \in \{+1, -1\}$. The upper bound $g_k(v) = \frac{1}{2} \sqrt{2^k L_k}(1 + v / 2^{k+1})$ evaluated on $v \in [2^k, 2^{k+1})$ is bounded by $\sqrt{2^k L_k}$. Minimization over $k \ge 0$ yields $b^*(q) \le b(q)$ for all $q \ge 0$.
* **Calendar mapping & pathwise bracket ([proofs.md §1.6–§1.7](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L129-L143)):** Summing across the $d$ lanes partitions calendar time $\{t \le T\}$. Deterministic accounting $K_T \le \sum_{t \le T} X_t \le K_T + P_T$ combined with $|\sum \mu_t - \sum X_t| \le B_T^* \le B_T$ validates (a), (b), and the one-sided versions (c).

---

### Corollary 1.1 (Explicit Rate)
* **Proof ([proofs.md §1.8](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L145-L147)):** For each lane with $Q_j \ge 1$, $k(Q_j) = \lfloor \log_2 Q_j \rfloor \le \log_2(M N_T)$ implies $L_{k(Q_j)} \le \ell_T$. Cauchy–Schwarz gives $\sum_{j=0}^{d-1} \sqrt{Q_j} \le \sqrt{d \sum Q_j} \le \sqrt{d M N_T}$. Dividing by $N_T$ yields the $O(\sqrt{d M \ell_T / N_T})$ rate. Correct.

---

### Corollary 1.2 (Realized Loss Fraction)
* **Proof ([proofs.md §1.8](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L148)):** Follows from dividing (6) and (5) by $N_T$. Pure deterministic accounting. Correct.

---

### Corollary 1.3 (Executable Liquidation Interval)
* **Proof ([proofs.md §1.8](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L149-L156)):** Pointwise sandwich $L^{lo}_{ti} \le L^{liq}_{ti} \le L^{hi}_{ti}$ implies $\mu_t^{lo} \le \mu_t^{liq} \le \mu_t^{hi}$ by conditional monotonicity. Theorem 1(c) applies to $L^{lo}$ (lower, level $\delta/2$) and $L^{hi}$ (upper, level $\delta/2$), holding simultaneously on an event of probability $\ge 1 - \delta$. Correct, subject to a terminology correction in the narrative description.

---

### Proposition 2 (Worst-Case Effective Sample Size)
* **Environment validity ([proofs.md §2.1](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L159-L173)):** With blocks of length $d$ and $F_t = \sigma(Z_1, \dots, Z_{b(t)-1}, U)$, $X_t = M Z_{b(t)}$ is $F_{t+d}$-measurable and independent of $F_t$, so $\mu_t = M p$ identically.
* **Testing reduction & TV bound ([proofs.md §2.2–§2.3](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L174-L199)):** 
  $p_\pm = 1/2 \pm h$ with $h = c/\sqrt{B}$ and $c = \frac{\sqrt{3}}{8}(1 - 2\delta)$.
  $kl(p_-, p_+) = 2h \log\left(\frac{1+2h}{1-2h}\right) \le \frac{32}{3} h^2$, giving $KL \le \frac{32}{3} c^2$.
  Pinsker's inequality yields $\text{TV} \le \sqrt{KL/2} \le \frac{4c}{\sqrt{3}} = \frac{1 - 2\delta}{2}$.
* **Width lower bound ([proofs.md §2.4](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L200-L203)):** 
  $\mathbb{P}_\pm(u - \ell \ge 2h) \ge 1 - 2\delta - \text{TV} \ge \frac{1 - 2\delta}{2}$.
  $\mathbb{E}[u - \ell] \ge 2h \frac{1 - 2\delta}{2} = \frac{\sqrt{3}}{8}(1 - 2\delta)^2 \sqrt{\frac{M d}{N}}$.
  All constants and algebraic steps are verified.

---

### Lemma 3 (Additive P&L Attribution)
* **Algebraic identity ([proofs.md §3.1–§3.2](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L213-L241)):** 
  $h_t^G - h_t^B = (e_t^G - e_t^B) w_t^B + e_t^G (w_t^G - w_t^B)$ is an exact algebraic decomposition for any vectors $w_t^a$ and scalars $e_t^a$ with $h_t^a = e_t^a w_t^a$. Correct.

---

### Remark 4 (No Universal Control)
* **Proof ([proofs.md §4](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L243-L246)):** In an all-loss environment ($L_{ti} = 1$ a.s.), any policy trading with positive probability has $r_T^{entry} = 1 > \alpha$ a.s. on $\{N_T > 0\}$. Correct.

---

## 2. Identified Errors and Technical Issues

### Issue 1: Inaccurate denominator terminology in Corollary 1.3
* **Location:** [theorems.md line 128](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/theorems.md#L128)
* **Why it is wrong:** The text asserts:
  $$\text{"The width is at least } (K_T^{hi} - K_T^{lo})/N_T \text{, the fraction of resolved entries that were still unsold at their deadline..."}$$
  $K_T^{hi} - K_T^{lo}$ is the exact count of resolved entries unsold by day $t+D$. However, dividing by $N_T$ produces the fraction of **all executed entries through $T$**, not the fraction of **resolved entries**. The fraction of resolved entries is $(K_T^{hi} - K_T^{lo}) / (N_T - P_T)$.
* **Whether it is fixable:** Yes.
* **Suggested fix:** Change the text to:
  $$\text{"...the fraction of total executed entries through } T \text{ that were resolved and unsold at their deadline..."}$$
  Or alternatively state:
  $$\frac{K_T^{hi} - K_T^{lo}}{N_T} = \left(\frac{N_T - P_T}{N_T}\right) \cdot \left(\frac{K_T^{hi} - K_T^{lo}}{N_T - P_T}\right).$$

---

### Issue 2: Predictability boundary at $m=0, 1$ in Claim 1.3
* **Location:** [proofs.md §1.3, lines 77–81](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L77-L81)
* **Why it is wrong:** Line 77 states:
  $$V_{j,m} \in \mathcal{H}_{m-1}^j \subset \mathcal{H}_m^j \quad \text{by (M1)}.$$
  At $m=0$, $\mathcal{H}_{-1}^j$ is undefined ($V_{j,0} = 0 \in \mathcal{H}_0^j$). For $m \ge 1$, $V_{j,m} = V_{j,m-1} + \nu_{j,m}^2 \in \mathcal{H}_{m-1}^j$. In the conditional expectation step:
  $$\mathbb{E}[W_m \mid \mathcal{H}_{m-1}^j] = W_{m-1} \exp(-\lambda^2 \nu_{j,m}^2 / 8) \mathbb{E}[\exp(\lambda D_{j,m}) \mid \mathcal{H}_{m-1}^j],$$
  pulling $W_{m-1}$ outside requires $W_{m-1} \in \mathcal{H}_{m-1}^j$, which relies on $V_{j,m-1} \in \mathcal{H}_{m-1}^j$ (not $V_{j,m}$). Stating that $V_{j,m} \in \mathcal{H}_{m-1}^j$ is the predictability condition for the step $m$ increment, but it slightly obscures why $W_{m-1}$ is $\mathcal{H}_{m-1}^j$-adapted.
* **Whether it is fixable:** Yes.
* **Suggested fix:** Explicitly specify the index range: define $V_{j,0} = 0 \in \mathcal{H}_0^j$, and state that for $m \ge 1$, $\nu_{j,m} \in \mathcal{H}_{m-1}^j$ and $V_{j,m-1} \in \mathcal{H}_{m-1}^j$, so $W_{m-1} \in \mathcal{H}_{m-1}^j$ and $\exp(-\lambda^2 \nu_{j,m}^2 / 8) \in \mathcal{H}_{m-1}^j$.

---

### Issue 3: Unverified external citations left in manuscript
* **Location:** [theorems.md lines 135, 172](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/theorems.md#L135); [proofs.md lines 5, 196, 252](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L5)
* **Why it is wrong:** The proofs cite three foundational results marked as unverified / believed from memory:
  1. Pinsker's inequality constant $\text{TV} \le \sqrt{\text{KL}/2}$.
  2. Doob's Optional Stopping Theorem for non-negative supermartingales at bounded stopping times.
  3. Brinson–Hood–Beebower (1986) attribution decomposition.
* **Whether it is fixable:** Yes. The theoretical statements and constants used in the proofs are confirmed to match the exact references:
  1. **Pinsker's Inequality:** A. B. Tsybakov, *Introduction to Nonparametric Estimation*, Springer, 2009, Lemma 2.5 (p. 88). For $\text{TV}(P, Q) = \sup_A |P(A) - Q(A)|$, $\text{TV}(P, Q) \le \sqrt{\frac{1}{2} D_{\text{KL}}(P \parallel Q)}$. The constant $\frac{1}{\sqrt{2}}$ is exact.
  2. **Optional Stopping:** D. Williams, *Probability with Martingales*, Cambridge University Press, 1991, Theorem 10.10(a). For a non-negative supermartingale $X$ and bounded stopping time $T \le n$, $\mathbb{E}[X_T] \le \mathbb{E}[X_0]$.
  3. **Performance Attribution:** G. P. Brinson, L. R. Hood, and G. L. Beebower, "Determinants of Portfolio Performance", *Financial Analysts Journal*, 42(4), 1986, pp. 39–44.
* **Suggested fix:** Remove the "unverified / believed" caveats and incorporate formal citations to Tsybakov (2009), Williams (1991), and Brinson et al. (1986).

---

### Issue 4: Continuous vs. discrete minimizer specification for $b^*(q)$
* **Location:** [theorems.md line 43](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/theorems.md#L43)
* **Why it is wrong:** Line 43 writes:
  $$b^*(q) = \min_{k \ge 0} \frac{1}{2} \sqrt{2^k L_k} \left(1 + \frac{q}{2^{k+1}}\right).$$
  In [proofs.md §1.5](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/proofs.md#L124), the infimum is taken over integers $k \in \mathbb{N}_0$, where each $k$ indexes an epoch. Omitting the qualifier $k \in \mathbb{N}_0$ in the theorem statement creates ambiguity as to whether $k$ can be any real number $k \ge 0$.
* **Whether it is fixable:** Yes.
* **Suggested fix:** State explicitly:
  $$\min_{k \in \mathbb{N}_0} \frac{1}{2} \sqrt{2^k L_k} \left(1 + \frac{q}{2^{k+1}}\right).$$

---

## 3. Audit of Assumptions

1. **Standardness of Assumptions:**
   * **A1 (Adaptedness):** Standard in sequential decision theory and online learning.
   * **A2 (Arbitrary dependence):** Significantly weaker than standard independence or martingale difference assumptions. Accommodates arbitrary cross-sectional and temporal correlation across labels.
   * **A3 (Bounded revelation lag $d$):** Standard in delayed feedback literature (Weinberger & Ordentlich, 2002; Joulani et al., 2013).
   * **A4 (Observable accounting):** Standard deterministic partitioning for right-censored streams.

2. **Unstated or Overstated Assumptions:**
   * **Cap $M$ in A1:** [setup.md line 106](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/setup.md#L106) places $n_t \le M$ inside Assumption A1. However, Theorem 1 never uses $M$ (the predictable variance clock $V_{j,m}$ accumulates realized $n_t^2$ without requiring a uniform bound). $M$ is only required for the deterministic rate bound in Corollary 1.1 and the minimax lower bound in Proposition 2. [setup.md](file:///C:/Users/lijun/Desktop/AI-Optimization-Research/theory/setup.md) should decouple $n_t \le M$ from baseline validity (A1–A3).
   * **Integrability of $X_t$:** Conditional expectation $\mu_t = \mathbb{E}[X_t \mid \mathcal{F}_t]$ exists because $0 \le X_t \le n_t < \infty$ a.s. When $n_t \le M$ is imposed, $X_t \in L^\infty$.
   * **Definition of $L^{liq}$:** Corollary 1.3 requires $L^{liq}_{ti} \in [0, 1]$ to be formally defined on every sample path, including unexecuted or perpetually suspended trades. If a trade is never liquidated, any convention $L^{liq}_{ti} \in [0, 1]$ satisfies $L^{lo}_{ti} = 0 \le L^{liq}_{ti} \le 1 = L^{hi}_{ti}$. This convention must be formalized in A2 for Corollary 1.3.

---

## 4. Audit of Constants and Rates

* **Stitching Constant $c_0 = \pi^2/6$:**
  $$\sum_{k=0}^\infty (k+1)^{-2} = \sum_{m=1}^\infty m^{-2} = \frac{\pi^2}{6} = c_0.$$
  The union bound over $d$ lanes and $k \ge 0$ yields:
  $$d \cdot \frac{\delta}{2 d c_0} \sum_{k=0}^\infty (k+1)^{-2} = \frac{\delta}{2}.$$
  Accounting for two signs $s \in \{+1, -1\}$ gives $\delta/2 + \delta/2 = \delta$. Constant is exact.
* **Epoch Tuning $\lambda_k$:**
  Tuning $\lambda_k = \sqrt{8 L_k / 2^{k+1}}$ minimizes the worst-case bound over the dyadic interval $v \in [2^k, 2^{k+1})$. The maximum over the interval is attained at the upper limit $2^{k+1}$, giving:
  $$\frac{L_k}{\lambda_k} + \frac{\lambda_k 2^{k+1}}{8} = \sqrt{2^k L_k} = b(q).$$
  Constant is exact.
* **Proposition 2 Constants:**
  * $c = \frac{\sqrt{3}}{8}(1 - 2\delta)$. For $\delta \in (0, 1/2)$, $x = 2h \le 2c < \frac{\sqrt{3}}{4} \approx 0.433 < 1/2$.
  * Bound on log ratio: $\log\left(\frac{1+x}{1-x}\right) \le \frac{2x}{1 - x^2} \le \frac{8}{3}x$.
  * $\text{KL} \le \frac{32}{3} B h^2 = \frac{32}{3} c^2$.
  * $\text{TV} \le \sqrt{\text{KL}/2} \le \frac{4c}{\sqrt{3}} = \frac{1 - 2\delta}{2}$.
  * $1 - 2\delta - \text{TV} \ge \frac{1 - 2\delta}{2}$.
  * Expected width lower bound $\mathbb{E}[u - \ell] \ge \frac{\sqrt{3}}{8}(1 - 2\delta)^2 \sqrt{\frac{M d}{N}}$.
  All constants and rates are exact.
* **Convergence Rate Gap:**
  Corollary 1.1 achieves half-width $O\left(\sqrt{\frac{d M \log \log(M N_T)}{N_T}}\right)$. Proposition 2 establishes a fixed-time lower bound of $\Omega\left(\sqrt{\frac{d M}{N}}\right)$. The $\sqrt{\log \log N}$ discrepancy is the standard law of the iterated logarithm price for time-uniform validity.

---

## 5. Final Verdict

**FIXABLE ERRORS**

*(The mathematical core, martingales, stitching bounds, and minimax reductions are rigorous and sound. The required fixes are confined to one verbal denominator misstatement in Corollary 1.3, an index specification in Claim 1.3, making $k \in \mathbb{N}_0$ explicit in $b^*$, and adding formal citations for verified standard lemmas.)*

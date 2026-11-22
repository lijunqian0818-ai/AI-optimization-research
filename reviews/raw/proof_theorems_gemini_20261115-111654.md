# Technical Proof Review and Theoretical Audit

## 1. Item-by-Item Mathematical Audit

### Theorem 1 (Delayed Monitoring under Arbitrary Within-Day Dependence)

#### Mathematical Steps in Proof (§1.1–§1.7)
1. **Lane construction and filtration (§1.1):**
   - Days are partitioned into $d$ disjoint residue classes $t \equiv j \pmod d$. The lane filtration $\mathcal{H}^j_m = F_{t_{j,m+1}}$ sets the conditioning $\sigma$-field for step $m$ to $\mathcal{H}^j_{m-1} = F_{t_{j,m}}$.
   - Predictability: $\nu_{j,m} = n_{t_{j,m}} \in F_{t_{j,m}} = \mathcal{H}^j_{m-1}$ (by A1), so $V_{j,m} = \sum_{i=1}^m \nu_{j,i}^2 \in \mathcal{H}^j_{m-1}$.
   - Adaptedness: $X_{t_{j,m}} \in F_{t_{j,m}+d} = F_{t_{j,m+1}} = \mathcal{H}^j_m$ (by A3).
   - Centering: $\mathbb{E}[D_{j,m} \mid \mathcal{H}^j_{m-1}] = \mathbb{E}[\mu_{t_{j,m}} - X_{t_{j,m}} \mid F_{t_{j,m}}] = 0$ holds because $0 \le X_t \le n_t \le M < \infty$, guaranteeing $X_t \in L^1(\mathbb{P})$.
   - The construction decouples the within-day and cross-day dependencies up to lag $d$ across lanes.

2. **Conditional Hoeffding Lemma (§1.2):**
   - Given $\mathcal{G}$, $\nu \ge 0$, $\nu \in \mathcal{G}$, $0 \le X \le \nu$, $\mathbb{E}[X] < \infty$, $\mu = \mathbb{E}[X \mid \mathcal{G}]$, $D = \mu - X$.
   - Bound $a = \mu - \nu \le D \le \mu = c$ with $c - a = \nu$.
   - The convexity inequality $e^{\lambda D} \le \alpha + \beta D$ on $\{\nu > 0\}$ is standard.
   - The conditional expectation step uses truncation $G_r = \{\nu > 0, |\alpha| + |\beta| \le r\} \in \mathcal{G}$ to justify $\mathbb{E}[\alpha + \beta D \mid \mathcal{G}] = \alpha$, followed by monotone convergence as $r \to \infty$. This rigorously avoids division-by-zero or integrability issues with $\nu^{-1}$.
   - Taylor expansion of $\psi(s) = -\theta s + \log(1 - \theta + \theta e^s)$ yields $\psi''(s) \le 1/4$, giving $\psi(s) \le s^2/8 = \lambda^2 \nu^2 / 8$. The derivation is exact.

3. **Supermartingale property (§1.3):**
   - $W_m^{j,\lambda} = \exp(\lambda S_{j,m} - \lambda^2 V_{j,m}/8)$.
   - Decomposing $W_m = W_{m-1} \exp(-\lambda^2 \nu_{j,m}^2/8) \exp(\lambda D_{j,m})$.
   - Because $W_{m-1} \exp(-\lambda^2 \nu_{j,m}^2/8) \in \mathcal{H}^j_{m-1}$ is non-negative, taking it out of the conditional expectation and applying §1.2 yields $\mathbb{E}[W_m \mid \mathcal{H}^j_{m-1}] \le W_{m-1}$.
   - Base case: $W_0 = 1$ is deterministic.

4. **Ville's maximal inequality (§1.4):**
   - Stopping time $\sigma = \inf\{m \ge 0 : W_m \ge c\}$.
   - Optional stopping at bounded time $\sigma \wedge n$: $\mathbb{E}[W_{\sigma \wedge n}] \le \mathbb{E}[W_0] = 1$.
   - $c \mathbb{P}(\sigma \le n) \le \mathbb{E}[W_{\sigma \wedge n} \mathbf{1}_{\sigma \le n}] \le \mathbb{E}[W_{\sigma \wedge n}] \le 1$.
   - Taking $n \to \infty$ by monotone continuity from below yields $\mathbb{P}(\sigma < \infty) \le 1/c$.

5. **Dyadic stitching and radii (§1.5):**
   - Error budget: $\alpha_k = \frac{\delta}{2 d c_0 (k+1)^2}$ with $c_0 = \pi^2/6$.
   - $\sum_{k=0}^\infty \alpha_k = \frac{\delta}{2d}$, and summing across $d$ lanes gives $\delta/2$ for each sign $s \in \{+1, -1\}$.
   - $L_k = \log(1/\alpha_k) = \log\left(\frac{2 d c_0 (k+1)^2}{\delta}\right)$.
   - $\lambda_k = \sqrt{\frac{8 L_k}{2^{k+1}}} = 2 \sqrt{\frac{L_k}{2^k}}$.
   - $g_k(v) = \frac{L_k}{\lambda_k} + \frac{\lambda_k}{8} v = \frac{1}{2} \sqrt{2^k L_k} \left(1 + \frac{v}{2^{k+1}}\right)$.
   - For $v \in [2^k, 2^{k+1})$, $g_k(v) < \sqrt{2^k L_k} = b(v)$.
   - Minimum over $k \ge 0$: for $q \ge 1$, $g_k(q) \to \infty$ as $k \to \infty$, so the infimum is attained at a finite $k^*$.
   - Boundary at $q = 0$: $V_{j,m} = 0 \implies \nu_{j,i} = 0 \implies X_{t_{j,i}} = 0 \implies \mu_{t_{j,i}} = 0 \implies S_{j,m} = 0$. Hence $|S_{j,m}| = 0 \le b^*(0) = 0$.

6. **Aggregation across lanes (§1.6, §1.7):**
   - Summing $|S_{j, m_j(T)}| \le b^*(Q_{j,T})$ across $j = 0, \dots, d-1$ via the triangle inequality gives $|\sum_{t \le T} (\mu_t - X_t)| \le B^*_T \le B_T$.
   - Combining with $K_T \le \sum_{t \le T} X_t \le K_T + P_T$ yields the bounds on $\sum_{t \le T} \mu_t$.
   - Dividing by $N_T > 0$ yields (a) and (b).
   - One-sided bounds (c) follow by decomposing $E_\delta = E_\delta^{\text{up}} \cap E_\delta^{\text{low}}$, each having probability $\ge 1 - \delta/2$.

---

### Corollary 1.1 (Rates and Total Width)

1. **Part (a):**
   - For $Q_j \ge 1$: $k(Q_j) = \lfloor \log_2 Q_j \rfloor \le \log_2(M N_T)$.
   - $L_{k(Q_j)} \le \log(2 d c_0 / \delta) + 2 \log(1 + \log_2(M N_T)) = \ell_T$.
   - $b(Q_j) \le \sqrt{Q_j \ell_T}$.
   - By Cauchy–Schwarz across $d$ terms: $\sum_{j=0}^{d-1} \sqrt{Q_j} \le \sqrt{d \sum Q_j} = \sqrt{d \sum_{t \le T} n_t^2} \le \sqrt{d M N_T}$.
   - $B_T \le \sqrt{d M N_T \ell_T}$, so $B_T / N_T \le \sqrt{d M \ell_T / N_T}$.
   - Width before clipping is $(P_T + 2 B_T)/N_T \le P_T/N_T + 2 \sqrt{d M \ell_T / N_T}$; clipping to $[0, 1]$ caps it at 1.

2. **Part (b):**
   - Under A5, entries unrevealed at $T$ belong only to days $t \in (T-d, T]$, which contains at most $d$ days with at most $M$ entries each, giving $P_T \le d M$.
   - Width bound: $\min\{1, y + 2 \sqrt{y \ell_T}\}$ with $y = d M / N_T$.
   - For $y \le 1$: $y \le \sqrt{y} \le \sqrt{y \ell_T}$ (since $\ell_T > 1$). Hence $y + 2 \sqrt{y \ell_T} \le 3 \sqrt{y \ell_T}$.
   - For $y > 1$: $\min\{1, \dots\} \le 1 < 3 < 3 \sqrt{y \ell_T}$.
   - The inequality $\min\{1, d M / N_T + 2 \sqrt{d M \ell_T / N_T}\} \le 3 \sqrt{d M \ell_T / N_T}$ is valid.

---

### Corollary 1.2 (Realised Loss Fraction)

- $K_T \le \sum_{t \le T} X_t \le K_T + P_T$ holds pathwise by accounting definitions. Dividing by $N_T$ yields the bracket for $R_T$.
- $|r_T^{\text{entry}} - R_T| \le B^*_T / N_T$ is equation (5) divided by $N_T$.

---

### Corollary 1.3 (Executable Liquidation via Deadline Labels)

1. **Label ordering (Step 0):**
   - Under completion convention $L^{\text{liq}} := 1$ for unliquidated positions:
     - If sold by deadline ($S = 1$): $L^{\text{lo}} = L^{\text{liq}} = L^{\text{hi}}$.
     - If unsold by deadline ($S = 0$): $L^{\text{lo}} = 0 \le L^{\text{liq}} \le 1 = L^{\text{hi}}$.
   - $L^{\text{lo}} \le L^{\text{liq}} \le L^{\text{hi}}$ holds pointwise on all of $\Omega$.

2. **Target ordering (Step 1):**
   - Multiplying by $A_{ti} \ge 0$ and summing gives $X_t^{\text{lo}} \le X_t^{\text{liq}} \le X_t^{\text{hi}}$.
   - Taking $\mathbb{E}[\cdot \mid F_t]$ preserves monotonicity: $\mu_t^{\text{lo}} \le \mu_t^{\text{liq}} \le \mu_t^{\text{hi}}$, hence $\sum \mu_t^{\text{lo}} \le \sum \mu_t^{\text{liq}} \le \sum \mu_t^{\text{hi}}$.

3. **One-sided confidence sequences (Step 2):**
   - Applying Theorem 1(c) to $L^{\text{lo}}$ gives lower bound $\sum \mu_t^{\text{lo}} \ge \sum X_t^{\text{lo}} - B^*_T$ on $E^{\text{low}}(\text{lo})$ with probability $\ge 1 - \delta/2$.
   - Applying Theorem 1(c) to $L^{\text{hi}}$ gives upper bound $\sum \mu_t^{\text{hi}} \le \sum X_t^{\text{hi}} + B^*_T$ on $E^{\text{up}}(\text{hi})$ with probability $\ge 1 - \delta/2$.
   - Clocks $Q_{j,T}$ and radii $B^*_T$ depend only on $(n_t)$ and $d_D$, not on the labels.
   - Union bound: $\mathbb{P}(E^{\text{low}}(\text{lo}) \cap E^{\text{up}}(\text{hi})) \ge 1 - \delta$.

4. **Accounting (Step 3):**
   - Under A4-D with common revealed set $J_T$:
     $K_T^{\text{lo}} \le \sum X_t^{\text{lo}}$ and $\sum X_t^{\text{hi}} \le K_T^{\text{hi}} + P_T$ with $P_T = N_T - |J_T|$.

5. **Pathwise width bounds (Step 5):**
   - Lower bound on width:
     $\Lambda_T = \max\{0, (K_T^{\text{lo}} - B^*_T)/N_T\} \le K_T^{\text{lo}} / N_T$.
     $\Upsilon_T = \min\{1, (K_T^{\text{hi}} + P_T + B^*_T)/N_T\} \ge K_T^{\text{hi}} / N_T$ because $K_T^{\text{hi}} \le |J_T| \le N_T$ and $P_T, B^*_T \ge 0$.
     Subtracting gives $\Upsilon_T - \Lambda_T \ge (K_T^{\text{hi}} - K_T^{\text{lo}})/N_T$.
   - Identity: $K_T^{\text{hi}} - K_T^{\text{lo}} = \sum_{(t,i) \in J_T} (L_{ti}^{\text{hi}} - L_{ti}^{\text{lo}}) = \sum_{(t,i) \in J_T} U_{ti}^D = \#\{(t,i) \in J_T : \text{unsold at deadline}\}$.

6. **Conditional persistence (Step 6):**
   - Taking $\liminf_{T \to \infty}$ on both sides of the width lower bound preserves the inequality.
   - Converse follows by squeezing via Corollary 1.1(a).

---

### Proposition 2 (Worst-Case Effective Sample Size)

1. **Environment verification (§2.1):**
   - $T = B d, N = M B d$.
   - $Z_1, \dots, Z_B \stackrel{\text{i.i.d.}}{\sim} \text{Bernoulli}(p)$, independent of $U \sim \text{Uniform}[0,1]$.
   - For $t \le T$: $n_t = M$, $X_t = M Z_{b(t)}$ where $b(t) = \lceil t/d \rceil$.
   - For $t > T$: $n_t = 0, X_t = 0, \mu_t = 0, F_t = \sigma(Z_1, \dots, Z_B, U)$.
   - Filtration $F_t = \sigma(Z_1, \dots, Z_{b(t)-1}, U)$ for $t \le T$ ensures $\mu_t = M \mathbb{E}[Z_{b(t)} \mid F_t] = M p$.
   - Lag verification: $b(t+d) = b(t) + 1$, so $Z_{b(t)} \in F_{t+d}$ for all $t$.
   - Target: $r_T^{\text{entry}} = \frac{T M p}{N} = p$.

2. **Le Cam reduction (§2.2):**
   - $p_- = 1/2 - h$, $p_+ = 1/2 + h$, $h = c / \sqrt{B}$ with $c = \frac{\sqrt{3}}{8}(1 - 2\delta)$.
   - For $(1-\delta)$-honest intervals $(\ell, u)$ at time $T$:
     $\mathbb{P}_+(u - \ell \ge 2h) \ge 1 - 2\delta - \text{TV}(\mathbb{P}_-, \mathbb{P}_+)$.

3. **Total variation and KL bounds (§2.3):**
   - $\text{KL}(\mathbb{P}_- \parallel \mathbb{P}_+) = B \cdot \text{kl}(p_-, p_+) = 2 B h \log\left(\frac{1+2h}{1-2h}\right)$.
   - For $x = 2h \in (0, 1/2]$: $\log\left(\frac{1+x}{1-x}\right) \le \frac{2x}{1-x^2} \le \frac{8x}{3}$.
   - Thus $\text{kl}(p_-, p_+) \le \frac{32 h^2}{3}$, and $\text{KL} \le \frac{32 B h^2}{3} = \frac{32 c^2}{3}$.
   - Direct proof of Pinsker's inequality:
     - Attainment of TV on $A = \{f > g\}$ with $x = P(A), y = Q(A)$.
     - Jensen's inequality on $A$ and $A^c$ gives $\text{KL}(P \parallel Q) \ge \text{kl}(x, y)$.
     - Two integrations of $F''(s) = \frac{1}{s(1-s)} \ge 4$ from $y$ to $x$ yield $\text{kl}(x, y) \ge 2(x-y)^2 = 2 \text{TV}^2$.
   - $\text{TV} \le \sqrt{\text{KL}/2} \le \sqrt{\frac{16 c^2}{3}} = \frac{4c}{\sqrt{3}} = \frac{1 - 2\delta}{2}$.
   - Substituting yields $\mathbb{P}_+(u - \ell \ge 2h) \ge \frac{1 - 2\delta}{2}$.

4. **Expected width and variance (§2.4):**
   - $\mathbb{E}[u - \ell] \ge 2h \cdot \frac{1-2\delta}{2} = \frac{\sqrt{3}}{8}(1 - 2\delta)^2 \sqrt{\frac{M d}{N}}$.
   - Variance calculation: $\text{Var}\left(\sum_{t \le T} (X_t - \mu_t)\right) = M^2 d^2 B p(1-p) = p(1-p) M d N$.

---

### Lemma 3 (Additive P&L Attribution Identity)

1. **Algebra (§3.1):**
   - $h_t^G - h_t^B = (e_t^G - e_t^B) w_t^B + e_t^G (w_t^G - w_t^B)$.
   - Taking inner product with $x_t$ and subtracting $C^G - C^B$ yields (2) identically.
   - Gross composition: $\sum_t (h_t^G - h_t^E)^\top x_t = \sum_t e_t^G (w_t^G - w_t^B)^\top x_t$.
   - Net splits hold for any scalar $C^E$.

2. **Reference cost computation (§3.2 item 2):**
   - Dollar trade vector $\text{trade}_t^E = h_t^E - h_{t-}^E$ with $h_{t-}^E = h_{t-1}^E \circ (1 + R_{t-1})$.
   - This subtracts the pre-trade holding evaluated at current execution prices.

3. **Wealth recursion (§3.2 item 7):**
   - $W_{t+1} = W_t(1 + \rho_t) + h_t^\top x_t - c_t$.
   - Summing yields $W_{T+1} - W_1 = \Pi + \sum_t \rho_t W_t$.
   - Under W4 ($\rho_t = 0$), $W_{T+1} - W_1 = \Pi$.

---

### Remark 4 (Impossibility of Universal Guarantees)

- In the all-loss environment, $X_t = n_t$ a.s., $\mu_t = n_t$, so on $\{N_T > 0\}$, $R_T = r_T^{\text{entry}} = 1$.
- For $\alpha < 1$, $\{N_T > 0 \text{ and } r_T^{\text{entry}} \le \alpha\} = \emptyset$, giving probability 0.
- Any policy guaranteeing $r_T^{\text{entry}} \le \alpha$ a.s. on $\{N_T > 0\}$ must satisfy $\mathbb{P}(N_T > 0) = 0$.

---

## 2. Issues, Omissions, and Suggested Fixes

### Issue 1: Assumption Header Omission in Corollary 1.1(a)
- **Location:** `theory/theorems.md`, Corollary 1.1, "Assumptions" line.
- **Why it is wrong:** The assumption line states `(a) A1–A3 with n_t ≤ M; (b) additionally A4 and A5.` However, Part (a) states:
  $$\text{width of the interval in Theorem 1(a) is at most } \min\left\{ 1, \frac{P_T}{N_T} + 2 \sqrt{\frac{d M \ell_T}{N_T}} \right\}.$$
  The quantity $P_T$ and the Theorem 1(a) endpoints $K_T \pm B_T$ are ledger-level accounting objects defined exclusively under assumption A4. Under A1–A3 alone, $P_T$ is undefined, and the interval cannot be constructed. While the subsequent commentary notes "Under A1–A4 alone nothing is said about $P_T/N_T$", the formal assumption specification for (a) fails to list A4 for the width statement.
- **Fixability:** Fully fixable.
- **Suggested fix:** Update the assumption specification to:
  `Assumptions: for the sampling-error radius bound B_T/N_T ≤ √(d M ℓ_T/N_T): A1–A3; for the total width bound containing P_T/N_T: A1–A4; for (b): A1–A5.`

### Issue 2: Ambiguous Parameter in Rate Definition of Corollary 1.3(iii)
- **Location:** `theory/theorems.md`, Corollary 1.3(iii).
- **Why it is wrong:** Part (iii) states:
  $$\text{Conversely, on any path with } (K_T^{\text{hi}} - K_T^{\text{lo}})/N_T \to 0, \; P_T/N_T \to 0 \text{ and } d_D M \ell_T / N_T \to 0, \text{ the width } \Upsilon_T - \Lambda_T \to 0.$$
  The quantity $\ell_T$ was defined in Corollary 1.1 strictly with parameter $d$:
  $$\ell_T = \log(2 d c_0 / \delta) + 2 \log(1 + \log_2(M N_T)).$$
  In Corollary 1.3, the relevant lag is $d_D$ (not $d$). While `proofs.md` §1.8 correctly notes "by Corollary 1.1(a) with lag $d_D$", the statement in `theorems.md` reuses the symbol $\ell_T$ without defining it with $d_D$.
- **Fixability:** Fully fixable.
- **Suggested fix:** Explicitly index or define $\ell_T^{(D)} := \log(2 d_D c_0 / \delta) + 2 \log(1 + \log_2(M N_T))$ in Corollary 1.3.

### Issue 3: Incomplete Scope of Theorem Coverage in Corollary 1.1(a)
- **Location:** `theory/theorems.md`, Corollary 1.1(a).
- **Why it is wrong:** Part (a) states that the width bound holds for "the interval in Theorem 1(a)". However, since $B^*_T \le B_T$ deterministically, the exact same upper bound applies to the sharper interval of Theorem 1(b). Part (b) explicitly says "the total width of the intervals in Theorem 1(a), (b)", creating an asymmetric and incomplete scope specification in Part (a).
- **Fixability:** Fully fixable.
- **Suggested fix:** Change "the interval in Theorem 1(a)" in Part (a) to "the intervals in Theorem 1(a) and (b)".

### Issue 4: Notation Overloading of $P_T$ in Corollary 1.3
- **Location:** `theory/theorems.md`, Corollary 1.3, Label and Accounting Definitions.
- **Why it is wrong:** In Theorem 1 and A4, $P_T$ is defined as the number of entries whose single label $L_{ti}$ is not revealed at $T$. In Corollary 1.3 and A4-D, $P_T$ is redefined as $P_T := N_T - |J_T|$, the number of entries outside the common paired revelation set $J_T$. If an entry has one deadline label revealed but not the other, it is excluded from $J_T$ and counted in $P_T$. Using the identical symbol $P_T$ without an explicit subscript (e.g., $P_T^D$ or $P_T^{\text{pair}}$) creates ambiguity when contrasting Theorem 1 and Corollary 1.3.
- **Fixability:** Fully fixable.
- **Suggested fix:** Denote the unrevealed count in Corollary 1.3 and A4-D as $P_T^D := N_T - |J_T|$ to prevent confusion with the scalar label pending count in Theorem 1.

---

## 3. Assumptions Check

### Standardness of Assumptions
- **A1 (Decision Information / post-fill filtration):** Standard in sequential decision theory and execution analysis. Bounded daily selections ($n_t \le M$) are standard.
- **A2 (Arbitrary within-day / cross-asset dependence):** Very weak, fully non-parametric. Standard for adversarial or dependent sequential testing.
- **A3 (Bounded revelation lag $d$):** Standard in delayed-feedback online learning (e.g., Weinberger & Ordentlich 2002; Joulani et al. 2013).
- **A4 (Observable accounting):** Standard bookkeeping requirement for computability.
- **A5 (Individual revelation by lag $d$):** Standard ledger-synchronization assumption.
- **A4-D (Paired accounting):** Standard coarsening/censoring convention for paired bounds.
- **W1–W4 (Attribution accounting):** Standard discrete-time self-financing conditions in mathematical finance.

### Unstated / Under-Specified Assumptions
- **Pre-specification of $d$:** In `setup.md` §3.3, the text proves that $B_T(d)$ is non-monotone in $d$. Thus, $d$ cannot be chosen adaptively after inspecting sample paths. Theorem 1 relies on $d$ being fixed *a priori*. This is noted in `setup.md`, but should be explicitly stated as an assumption in the theorem statement: $d$ is a deterministic integer fixed prior to observing data.
- **Range of $\delta$ in Proposition 2:** Proposition 2 requires $\delta \in (0, 1/2)$ to guarantee $1 - 2\delta > 0$ and $h > 0$. The theorem text explicitly includes this in the claim, so it is stated correctly.

---

## 4. Constants and Rates Check

### Explicit Constants
- **Epoch allocation:** $\sum_{k=0}^\infty (k+1)^{-2} = \pi^2 / 6 = c_0$. Correct.
- **Probability budget:** Per-sign error $\sum_{j=0}^{d-1} \sum_{k=0}^\infty \frac{\delta}{2 d c_0 (k+1)^2} = \frac{\delta}{2}$. Two-sided error $\le \delta$. Correct.
- **Hoeffding optimization:** Tuning $\lambda_k = \sqrt{\frac{8 L_k}{2^{k+1}}}$ over epoch $v < 2^{k+1}$ gives worst-case bound $\sqrt{2^k L_k}$. Exact.
- **Proposition 2 constants:**
  - $x = 2h \in (0, 1/2] \implies \frac{2x}{1-x^2} \le \frac{8x}{3}$.
  - $\text{kl}(p_-, p_+) \le \frac{32 h^2}{3} \implies \text{KL} \le \frac{32 c^2}{3}$.
  - Pinsker: $\text{TV} \le \sqrt{\text{KL}/2} \le \sqrt{\frac{16 c^2}{3}} = \frac{4c}{\sqrt{3}} = \frac{1 - 2\delta}{2}$.
  - Lower bound probability: $1 - 2\delta - \text{TV} \ge \frac{1 - 2\delta}{2}$.
  - Lower bound width: $2h = \frac{\sqrt{3}}{4}(1 - 2\delta) \sqrt{\frac{M d}{N}}$.
  - Expected width: $2h \cdot \frac{1 - 2\delta}{2} = \frac{\sqrt{3}}{8}(1 - 2\delta)^2 \sqrt{\frac{M d}{N}}$.
  - All constants in Proposition 2 are exact.

### Rates Comparison
- **Upper bound (Corollary 1.1(b)):** Total width $\le 3 \sqrt{\frac{d M \ell_T}{N_T}}$, where $\ell_T = \mathcal{O}(\log(d/\delta) + \log \log(M N_T))$.
- **Lower bound (Proposition 2):** Width $\ge \frac{\sqrt{3}}{4}(1 - 2\delta) \sqrt{\frac{M d}{N}}$ with probability $\ge \frac{1 - 2\delta}{2}$.
- **Rate matching:** The leading dependency on $\sqrt{M d / N}$ is matching and unimprovable over the class of A1–A5 environments. The upper bound exceeds the lower bound only by explicit constants and the iterated logarithm $\sqrt{\ell_T}$.

---

## 5. Verdict

**FIXABLE ERRORS**

*(The mathematical architecture, supermartingale inequalities, stitching constants, Le Cam lower-bound derivations, and algebraic identities are correct. The issues found are formal omission of A4 in Corollary 1.1(a)'s assumption line, under-specified lag index in $\ell_T$ for Corollary 1.3(iii), scope asymmetry between Theorem 1(a) and 1(b) in Corollary 1.1(a), and notation overloading of $P_T$. All identified issues are minor and fully fixable.)*

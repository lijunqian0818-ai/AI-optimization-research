# Comprehensive Optimization Theory Proof Review (Round 3 Confirmation)

**Reviewer Role:** Independent Optimization Theorist  
**Scope:** Confirmation re-review of `theory/setup.md`, `theory/theorems.md`, and `theory/proofs.md` across rounds 1, 2, and 3 revisions. (No files under `reviews/` were accessed.)

---

## 1. General Mathematical Audit

### 1.1 Standardness of Assumptions
- **A1 (Decision information):** Standard filtration and adaptedness setup with a known integer upper bound $n_t \le M$. The post-fill placement of $\mathcal{F}_t$ at the auction match $\tau_t$ makes fill indicators $A_{ti}$ adapted by construction.
- **A2 (Fixed label convention):** Standard non-parametric specification. Crucially, no independence, mixing, stationarity, or distributional structure is imposed across assets or over time.
- **A3 (Bounded revelation lag):** Standard bounded-delay information structure ($X_t \in \mathcal{F}_{t+d}$). Fixing a deterministic integer $d$ prior to data inspection is necessary to preserve coverage because radius sequences $B_T(d)$ are not monotone in $d$.
- **A4 (Observable accounting):** Pure bookkeeping. Does not restrict censoring or early-revelation mechanisms.
- **A5 (Individual revelation by lag; optional):** Standard finite-memory disclosure condition, yielding $P_T \le dM$.
- **A4-D (Paired accounting):** Standard joint-disclosure accounting ensuring paired indicators $(L^{lo}, L^{hi})$ are reported on a common revealed set $J_T$.

### 1.2 Unstated Assumptions
No unstated mathematical assumptions were found. All regularity conditions (boundedness $X_t \le n_t \le M$, integrability $\mathbb{E}[X_t] < \infty$, measurability of lane clocks $V_{j,m} \in \mathcal{H}^j_{m-1}$, and determinism of $d, d_D, \delta$) are explicitly stated and verified in the derivations.

### 1.3 Constants and Convergence Rates
- **Theorem 1:** The constants $c_0 = \pi^2/6$, $\alpha_k = \frac{\delta}{2 d c_0 (k+1)^2}$, $L_k = \log(2 d c_0 (k+1)^2 / \delta)$, $\lambda_k = \sqrt{8 L_k / 2^{k+1}}$, and $g_k(q) = \frac{1}{2} \sqrt{2^k L_k} (1 + q / 2^{k+1})$ are exact. The dyadic stitch tuned to the upper epoch boundary $2^{k+1}$ correctly produces the coefficient $\sqrt{2^k L_k} = b(q)$ on $2^k \le q < 2^{k+1}$.
- **Corollary 1.1:** The rate $\sqrt{d M \ell_T / N_T}$ with $\ell_T = \log(2 d c_0 / \delta) + 2 \log(1 + \log_2(M N_T))$ is derived via Cauchy–Schwarz over $d$ lane clocks. The constant 3 in $3 \sqrt{d M \ell_T / N_T}$ is sharp for $y \le 1$ and valid for $y > 1$.
- **Proposition 2:** The constants $c = \frac{\sqrt{3}}{8}(1 - 2\delta)$, $2h = \frac{\sqrt{3}}{4}(1 - 2\delta)\sqrt{Md/N}$, TV bound $\frac{1-2\delta}{2}$, and expected width lower bound $\frac{\sqrt{3}}{8}(1 - 2\delta)^2 \sqrt{Md/N}$ are mathematically exact. Pinsker's inequality is proved completely from first principles in §2.3.

### 1.4 Internal Consistency Between Files
- **Lag parameters:** $d = H + 1$ is adopted consistently for the primary O1 label in `setup.md` §3.3/§6 and `theorems.md` Theorem 1; $d_D$ is used consistently for deadline labels in `setup.md` §6, `theorems.md` Corollary 1.3, and `proofs.md` §1.8.
- **Pending counts:** $P_T = N_T - (\text{revealed labels})$ is used for single-label accounting (Theorem 1, Corollaries 1.1–1.2); $P_T^D = N_T - |J_T|$ is used for paired-deadline accounting (A4-D, Corollary 1.3). Notation is uniform across all three files.
- **Accounting convention:** Convention B (benchmark-price accounting) is adopted uniformly across `setup.md` §6 item 6, `theorems.md` Lemma 3, and `proofs.md` §3.2 item 7.

---

## 2. Itemized Issues and Discrepancies

### Issue 1: Stock Split Naming Terminology Inverted Relative to Financial Standard
- **Location:** `theory/theorems.md` §Lemma 3 (lines 207, 217); `theory/proofs.md` §3.2 item 2 (lines 355).
- **Why it is problematic:** The text defines a share-doubling corporate action ($1$ old share becomes $2$ new shares, price drops from $100$ to $50$) as a `"1-for-2 split"`. In standard financial market and exchange convention (including CSRC/SSE/SZSE corporate action notices and global standards), issuing $2$ shares for every $1$ share held is termed a **2-for-1 split** (or forward stock split). Conversely, a "1-for-2 split" denotes a reverse stock split (share consolidation) where $2$ old shares merge into $1$ new share ($\phi_t = 0.5$, price doubling). While the mathematics ($\phi_t = 2$, share count multiplied by $2$) and arithmetic examples are completely correct, the terminology is inverted and creates confusion.
- **Fixable:** Yes.
- **Suggested Fix:** Replace `"1-for-2 split"` with `"2-for-1 split"` (or `"1-to-2 forward split"`) in both files.

### Issue 2: Cost Debit Timing in General Wealth Recursion ($\rho_t \ne 0$)
- **Location:** `theory/theorems.md` §Lemma 3 (line 233); `theory/proofs.md` §3.2 item 7 (lines 366–376).
- **Why it is problematic:** In `proofs.md` line 368, the recursion is written as:
  $$W_{T+1} - W_1 = \Pi + \sum_t \rho_t W_t$$
  which implicitly assumes transaction costs $c_t$ are debited at the *end* of period $t$ (so the entire pre-trade wealth $W_t$ earns interest $\rho_t$). However, under Convention B in lines 372–374, cash charges $f_t$ and execution shortfall $sf_t$ are debited at the trade at the *start* of period $t$, yielding:
  $$W_{t+1} = (W_t - f_t - sf_t)(1 + \rho_t) + h_t^\top x_t$$
  which sums to $W_{T+1} - W_1 = \Pi + \sum_t \rho_t (W_t - f_t - sf_t)$. While line 370 correctly notes parenthetically that this discrepancy vanishes under condition W4 ($\rho_t = 0$ for all $t$), line 233 in `theorems.md` states without qualification that under W1–W3 without W4, $W_{T+1}^a - W_1^a = \Pi^a + \sum_t \rho_t W_t^a$.
- **Fixable:** Yes.
- **Suggested Fix:** In `theorems.md` line 233, qualify the non-zero cash return formula to state:  
  *"Under W1–W3 without W4, $W_{T+1}^a - W_1^a = \Pi^a + \sum_t \rho_t (W_t^a - c_t^a)$ when costs are settled at trade time (or $\sum_t \rho_t W_t^a$ if settled at period end); both vanish under W4 ($\rho_t = 0$) where $\Pi^a = W_{T+1}^a - W_1^a$ holds exactly."*

---

## 3. Specific Review Requirements Audit

### 3.1 Interpretive Sentences and Claims
All claims using "if and only if", "only", "smallest", and "necessarily" were checked:
- **"If and only if" in Lemma 3 (line 215):** The statement that $h_{t-}^E = h_{t-1}^E \circ (1 + r_{t-1})$ holds *if and only if* $1 + r_{t-1} = \phi_t \circ p_t / p_{t-1}$ on every asset with $h_{t-1}^E \ne 0$ is **exact**. If a total return is used, a spurious sale $-\delta_t$ is introduced; if a raw price ratio is used, a spurious purchase is introduced.
- **Operational lag sufficiency:** In `setup.md` §3.3 line 155, previous round over-claims ("smallest valid $d$", "if and only if OA-next") have been fully excised and replaced with explicit sufficiency definitions.
- **Remark 4 scope:** The claim does not assert that the only safe policy is abstention; it explicitly demonstrates an informative-filtration policy that trades safely whenever non-losing candidates exist.

### 3.2 Lemma 3: Trade Formula and Single-Count Accounting
1. **Trade-amount formula under corporate actions:**
   $$\text{trade}_t^E = (s_t^E - s_{t-}^E) \circ p_t = h_t^E - h_{t-}^E, \quad s_{t-}^E = s_{t-1}^E \circ \phi_t$$
   Cash distributions $\delta_t = s_{t-1}^E \circ \kappa_t$ are booked directly to cash and do not alter $s_{t-}^E$ or $\text{trade}_t^E$. Corporate action share changes produce zero spurious turnover.
2. **Benchmark-price accounting (Convention B):**
   Holdings $h_t = s_t \circ p_t$ and returns $x_t$ are evaluated at the benchmark auction price $p_t$. All trading friction enters exclusively through:
   $$C^a = \sum_t f_t^a + \sum_t (s_t^a - s_{t-}^a)^\top (p_t^{\text{exec},a} - p_t)$$
   Slippage and fees enter $C^a$ exactly once and are not applied to benchmark prices or return series. Double-counting is completely avoided.

---

## 4. Per-Result Verdicts

| Result | Status in Text | Mathematical Review Assessment | Verdict |
|---|---|---|---|
| **Theorem 1 (a)** | `自
| Result | Status in Text | Mathematical Review Assessment | Verdict |
|---|---|---|---|
| **Theorem 1 (a)** | `自查通过` | Proof in §1.1–§1.7 verified. Ville's inequality and conditional Hoeffding lemma proofs are complete and self-contained. Union bounds and dyadic stitching constants are exact. | **CORRECT** |
| **Theorem 1 (b)** | `自查通过` | Sharper radius $b^*(q) = \min_k g_k(q) \le b(q)$ holds on the exact same event $E_\delta$. | **CORRECT** |
| **Theorem 1 (c)** | `自查通过` | One-sided bounds hold at level $1 - \delta/2$ each from signed union bounds. | **CORRECT** |
| **Corollary 1.1** | `自查通过` | Rates and constants in (a) and (b) are exact. Three-tier assumption structure matches proof steps. | **CORRECT** |
| **Corollary 1.2** | `自查通过` | Deterministic bracket from A4 and target comparison from A1–A3 verified. | **CORRECT** |
| **Corollary 1.3** | `草稿` | Label ordering $L^{lo} \le L^{liq} \le L^{hi}$ is exact under policy LP. Step 0–7 derivations, pathwise width bounds, and conditional persistence hold. Ready to be promoted from draft. | **CORRECT** |
| **Proposition 2** | `自查通过` | Two-point Le Cam reduction, Bernoulli block construction, and Pinsker's inequality proof verified. Constants and variance formulas are exact. | **CORRECT** |
| **Lemma 3** | `自查通过` | Attribution identity (2) is exact algebra. Trade-amount formula under corporate actions and single-count benchmark-price accounting (Convention B) are rigorous. Only requires the two minor wording adjustments noted in Issues 1 & 2. | **CORRECT WITH CHANGES** |
| **Remark 4** | `自查通过` | Proofs of (i) and (ii) in the all-loss environment are exact; informative filtration counterexample is valid. | **CORRECT** |

---

## 5. Overall Verdict

**VERDICT: FIXABLE ERRORS** (Minor terminological and timing qualification adjustments only; no mathematical or theoretical flaw exists).

### Summary of Required Changes:
1. **Terminology (`theory/theorems.md#L207-L217`, `theory/proofs.md#L355`):** Replace `"1-for-2 split"` with `"2-for-1 split"` (or `"1-to-2 forward split"`) to conform to standard exchange conventions for share-doubling corporate actions.
2. **Wealth recursion qualification (`theory/theorems.md#L233`):** Explicitly state that when $\rho_t \ne 0$, the exact timing of cost settlement determines whether the residual cash-benchmark term is $\sum_t \rho_t (W_t - c_t)$ (start-of-period trade settlement) or $\sum_t \rho_t W_t$ (end-of-period settlement), both vanishing under W4 ($\rho_t = 0$).

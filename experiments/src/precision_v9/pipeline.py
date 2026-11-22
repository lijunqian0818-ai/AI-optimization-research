"""Synthetic order-level pipeline with annual refitting (experiment precision_v9).

Every call of `run_history` regenerates a complete synthetic history (development years plus the
hold-out) and refits the whole pipeline: base ridge, end-to-end comparator BASE-V, and the
second-stage gates LOSS, LOSS+Z, LOSS+W, NET-K. All parameters are documented in
experiments/results/precision_v9/SPEC.md. Units: returns are decimals (1 bp = 1e-4).

Policies (index): 0 SCORE, 1 BASEV, 2 LOSS, 3 LOSSZ, 4 LOSSW, 5 NETK.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np

POLICIES = ["SCORE", "BASEV", "LOSS", "LOSSZ", "LOSSW", "NETK"]
# contrast name -> (g, h, late_start?)
CONTRASTS = [("P1", 2, 0, False),   # LOSS  - SCORE
             ("P2", 3, 2, False),   # LOSS+Z - LOSS
             ("P3", 4, 2, True),    # LOSS+W - LOSS, window starts later
             ("P4", 5, 0, False),   # NETK  - SCORE
             ("P5", 2, 1, False),   # LOSS  - BASEV
             ("P6", 5, 1, False)]   # NETK  - BASEV


@dataclass(frozen=True)
class Params:
    n_names: int = 300
    n_feat: int = 10
    days_per_year: int = 242
    dev_years: int = 6
    holdout_days: int = 1075
    H: int = 5
    K: int = 30
    c: float = 0.5
    burn: int = 40
    # short nomination lists
    p_short: float = 0.05
    short_min: int = 10
    # market
    drift: float = 2e-4            # daily market drift
    mkt_sd: float = 0.012          # daily market shock sd
    vol_phi: float = 0.99          # market log-vol AR(1)
    vol_sd: float = 0.25           # stationary sd of market log-vol
    beta_sd: float = 0.15          # cross-sectional sd of beta (0 -> beta = 1)
    # idiosyncratic volatility
    sig_med: float = 0.020         # median daily idio sd
    sig_logsd: float = 0.35        # cross-sectional sd of log idio sd (permanent part)
    u_phi: float = 0.995           # persistent name-level log-vol AR(1)
    u_sd: float = 0.15             # stationary sd of that component
    # features
    x_phi: float = 0.98
    z_phi: float = 0.95
    # signal (daily expected idio return, decimals)
    b_norm: float = 3.6e-4         # ||b_bar||
    kappa: float = 1.6e-4          # low-vol premium per sd of log vol
    c_z: float = 1.0e-4            # loading on z (only the gates see z)
    # yearly regimes (F2 / F3b): b_Y = b_bar + tau_b * eta_Y etc.
    tau_b: float = 0.0             # per-feature sd of yearly deviation
    tau_kappa: float = 0.0
    tau_z: float = 0.0
    # execution
    fill_prob: float = 0.95
    cost: float = 15e-4
    # learners
    base_lambda: float = 1.0
    basev_years: int = 3
    basev_lambda: float = 1.0
    basev_winsor: float = 3.0
    gate_lambda: float = 1.0
    gate_bag: float = 0.8
    n_seeds: int = 3
    vol_window: int = 20
    late_start: int = 300          # P3 window starts at this hold-out day


B_SHAPE = np.array([1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.0])


def b_bar(p: Params) -> np.ndarray:
    v = B_SHAPE[: p.n_feat]
    return p.b_norm * v / np.linalg.norm(v)


class SplitRNG:
    """Draws whose leading (time) axis is split: rows < cut from the development generator,
    rows >= cut from the hold-out generator. Name-level constants come from the development
    generator. Fixing dev_seed and varying hold_seed regenerates only the hold-out part."""

    def __init__(self, dev_seed, hold_seed):
        self.dev = np.random.default_rng([int(dev_seed), 1])
        self.hold = np.random.default_rng([int(hold_seed), 2])

    def normal(self, n, tail, cut):
        a = self.dev.standard_normal((cut,) + tuple(tail))
        b = self.hold.standard_normal((n - cut,) + tuple(tail))
        return np.concatenate([a, b], axis=0)

    def uniform(self, n, tail, cut):
        a = self.dev.random((cut,) + tuple(tail))
        b = self.hold.random((n - cut,) + tuple(tail))
        return np.concatenate([a, b], axis=0)

    def integers(self, lo, hi, n, cut):
        a = self.dev.integers(lo, hi, size=cut)
        b = self.hold.integers(lo, hi, size=n - cut)
        return np.concatenate([a, b])


def _ar1_from(e, phi, sd=1.0):
    """AR(1) with stationary sd `sd` driven by standard normal innovations e (time first)."""
    out = np.empty_like(e)
    innov = sd * math.sqrt(1 - phi * phi)
    out[0] = sd * e[0]
    for t in range(1, e.shape[0]):
        out[t] = phi * out[t - 1] + innov * e[t]
    return out


@dataclass
class History:
    X: np.ndarray       # (Dd, N, F) features at decision days
    Z: np.ndarray       # (Dd, N)
    W: np.ndarray       # (Dd, N)
    logvol: np.ndarray  # (Dd, N) log RMS realised 20-day return
    R: np.ndarray       # (Dd, N) gross H-day return of an order decided on day d
    fill: np.ndarray    # (Dd, N) bool
    rho: np.ndarray     # (Dd, N) net standard-order return, 0 if unfilled
    n_t: np.ndarray     # (Dd,) nominated list length
    year: np.ndarray    # (Dd,) year index of decision day


def generate_history(p: Params, dev_seed: int, hold_seed: int) -> History:
    Nn, F, H = p.n_names, p.n_feat, p.H
    n_dec = p.dev_years * p.days_per_year + p.holdout_days
    D = p.burn + n_dec + H + 1                       # raw days
    hold0 = p.dev_years * p.days_per_year            # first hold-out decision day
    cut_raw = p.burn + hold0 + 1                     # raw days < cut_raw are known at hold0
    n_years = int(math.ceil(n_dec / p.days_per_year)) + 1
    g = SplitRNG(dev_seed, hold_seed)
    # regimes per year; state day u belongs to year (u - burn) // A (burn -> year 0)
    bb = b_bar(p)
    eta = g.normal(n_years, (F,), p.dev_years)
    bY = bb[None, :] + p.tau_b * eta
    kY = p.kappa + p.tau_kappa * g.normal(n_years, (), p.dev_years)
    cY = p.c_z + p.tau_z * g.normal(n_years, (), p.dev_years)
    # names (development generator)
    beta = 1.0 + p.beta_sd * g.dev.standard_normal(Nn)
    logsig0 = math.log(p.sig_med) + p.sig_logsd * g.dev.standard_normal(Nn)
    # state processes
    X = _ar1_from(g.normal(D, (Nn, F), cut_raw), p.x_phi)
    Z = _ar1_from(g.normal(D, (Nn,), cut_raw), p.z_phi)
    Wf = _ar1_from(g.normal(D, (Nn,), cut_raw), p.z_phi)
    u = _ar1_from(g.normal(D, (Nn,), cut_raw), p.u_phi, sd=p.u_sd)
    v = _ar1_from(g.normal(D, (), cut_raw), p.vol_phi, sd=p.vol_sd)
    logsig = logsig0[None, :] + u                    # (D, N)
    day_year = np.clip((np.arange(D) - p.burn) // p.days_per_year, 0, n_years - 1)
    ls_c = logsig - logsig.mean(axis=1, keepdims=True)
    ls_std = ls_c / math.sqrt(p.sig_logsd ** 2 + p.u_sd ** 2)
    # expected idio return set at state day u, earned by the return of day u+1
    mu = (np.einsum("dnf,df->dn", X, bY[day_year]) - kY[day_year][:, None] * ls_std
          + cY[day_year][:, None] * Z)
    mkt = p.drift + p.mkt_sd * np.exp(v - p.vol_sd ** 2 / 2) * g.normal(D, (), cut_raw)
    eps = g.normal(D, (Nn,), cut_raw)
    r = np.zeros((D, Nn))
    r[1:] = (beta[None, :] * mkt[1:, None] + mu[:-1]
             + np.exp(logsig[1:] + v[1:, None] - p.vol_sd ** 2 / 2) * eps[1:])
    # H-day return of an order decided at raw day t: sum r[t+1..t+H]
    cs = np.vstack([np.zeros((1, Nn)), np.cumsum(r, axis=0)])   # cs[k] = sum r[0..k-1]
    dec = np.arange(p.burn, p.burn + n_dec)
    R = cs[dec + H + 1] - cs[dec + 1]
    # realised vol (RMS, not demeaned) over r[t-19..t]
    cs2 = np.vstack([np.zeros((1, Nn)), np.cumsum(r * r, axis=0)])
    w = p.vol_window
    rms = np.sqrt((cs2[dec + 1] - cs2[dec + 1 - w]) / w)
    fill = g.uniform(n_dec, (Nn,), hold0) < p.fill_prob
    rho = np.where(fill, R - p.cost, 0.0)
    short = g.uniform(n_dec, (), hold0) < p.p_short
    n_t = np.where(short, g.integers(p.short_min, p.K, n_dec, hold0), p.K)
    return History(X=X[dec], Z=Z[dec], W=Wf[dec], logvol=np.log(rms), R=R, fill=fill, rho=rho,
                   n_t=n_t, year=(np.arange(n_dec) // p.days_per_year))


# ----------------------------------------------------------------------------- learners

def _ridge_from_stats(XtX, Xty, lam):
    k = XtX.shape[0]
    pen = lam * np.eye(k)
    pen[0, 0] = 0.0
    return np.linalg.solve(XtX + pen, Xty)


def _standardize_fit(A):
    m = A.mean(axis=0)
    s = A.std(axis=0)
    s[s == 0] = 1.0
    return m, s


def _ridge(A, y, lam):
    m, s = _standardize_fit(A)
    Az = (A - m) / s
    Az1 = np.hstack([np.ones((Az.shape[0], 1)), Az])
    beta = _ridge_from_stats(Az1.T @ Az1, Az1.T @ y, lam)
    return m, s, beta


def _logistic(A, y, lam, iters=25, tol=1e-10):
    """L2-penalised logistic regression by Newton/IRLS on standardised inputs."""
    m, s = _standardize_fit(A)
    Az = (A - m) / s
    Az1 = np.hstack([np.ones((Az.shape[0], 1)), Az])
    k = Az1.shape[1]
    pen = lam * np.eye(k)
    pen[0, 0] = 0.0
    beta = np.zeros(k)
    pbar = min(max(y.mean(), 1e-6), 1 - 1e-6)
    beta[0] = math.log(pbar / (1 - pbar))
    for _ in range(iters):
        eta = Az1 @ beta
        pr = 1.0 / (1.0 + np.exp(-eta))
        g = Az1.T @ (pr - y) + pen @ beta
        Hm = (Az1 * (pr * (1 - pr))[:, None]).T @ Az1 + pen
        step = np.linalg.solve(Hm, g)
        beta -= step
        if np.max(np.abs(step)) < tol:
            break
    return m, s, beta


def _predict(model, A):
    m, s, beta = model
    return beta[0] + ((A - m) / s) @ beta[1:]


def _topk_mask(score, n_t, largest=True):
    """Row-wise mask of the n_t[d] best entries of score (Dd, M). Ties broken by column index."""
    Dd, M = score.shape
    sc = score if largest else -score
    # stable ordering: sort by -score then index
    order = np.argsort(-sc, axis=1, kind="stable")
    ranks = np.empty_like(order)
    np.put_along_axis(ranks, order, np.arange(M)[None, :].repeat(Dd, 0), axis=1)
    return ranks < n_t[:, None]


def run_history(p: Params, dev_seed: int, hold_seed: int, return_diag: bool = False):
    """Generate one history and run the pipeline. Returns N, S of shape (P, n_seeds, T_hold).

    Unconditional replications use a fresh dev_seed and hold_seed each time; conditional
    replications (development history fixed) keep dev_seed and vary hold_seed."""
    h = generate_history(p, dev_seed, hold_seed)
    A, H, K = p.days_per_year, p.H, p.K
    n_dec = h.R.shape[0]
    Nn, F = p.n_names, p.n_feat
    hold0 = p.dev_years * A
    Th = p.holdout_days
    n_sub = np.ceil(p.c * h.n_t).astype(int)                 # submitted count per day
    n_years = int(math.ceil(n_dec / A))
    # ---- base: OLS/ridge on within-day rank of R, features X, expanding window, refit yearly
    ranks = np.argsort(np.argsort(h.R, axis=1), axis=1) / (Nn - 1) - 0.5
    X1 = np.concatenate([np.ones((n_dec, Nn, 1)), h.X], axis=2)        # (Dd, N, F+1)
    XtX_d = np.einsum("dni,dnj->dij", X1, X1)
    Xty_d = np.einsum("dni,dn->di", X1, ranks)
    cXtX = np.concatenate([np.zeros((1, F + 1, F + 1)), np.cumsum(XtX_d, axis=0)])
    cXty = np.concatenate([np.zeros((1, F + 1)), np.cumsum(Xty_d, axis=0)])
    # BASE-V: raw cross-sectionally demeaned R, winsorised, rolling window
    Rd = h.R - h.R.mean(axis=1, keepdims=True)
    sdR = Rd.std(axis=1, keepdims=True)
    Rw = np.clip(Rd, -p.basev_winsor * sdR, p.basev_winsor * sdR)
    Xtyv_d = np.einsum("dni,dn->di", X1, Rw / 1e-2)            # scale for conditioning
    cXtyv = np.concatenate([np.zeros((1, F + 1)), np.cumsum(Xtyv_d, axis=0)])
    base_score = np.full((n_dec, Nn), np.nan)
    basev_score = np.full((n_dec, Nn), np.nan)
    for Y in range(1, n_years):
        s0 = Y * A
        s1 = min((Y + 1) * A, n_dec)
        last = s0 - (H + 1)                                    # last usable decision day (incl.)
        if last < 0:
            continue
        coef = _ridge_from_stats(cXtX[last + 1], cXty[last + 1], p.base_lambda)
        base_score[s0:s1] = X1[s0:s1] @ coef
        first = max(0, s0 - p.basev_years * A)
        coefv = _ridge_from_stats(cXtX[last + 1] - cXtX[first], cXtyv[last + 1] - cXtyv[first],
                                  p.basev_lambda)
        basev_score[s0:s1] = X1[s0:s1] @ coefv
    # ---- nominations (base OOS from year 1 on)
    valid = np.arange(n_dec) >= A
    nom = np.zeros((n_dec, Nn), bool)
    nom[valid] = _topk_mask(base_score[valid], h.n_t[valid])
    # nominated rows ordered by base score within day: (Dd, K) indices; pad with -1
    order = np.argsort(-np.where(np.isnan(base_score), -np.inf, base_score), axis=1, kind="stable")
    nom_idx = order[:, :K]                                    # first n_t of them are nominated
    slot_ok = np.arange(K)[None, :] < h.n_t[:, None]
    # gate design rows per (day, slot)
    def take(M):
        return np.take_along_axis(M, nom_idx, axis=1)
    g_base = take(np.where(np.isnan(base_score), 0.0, base_score))
    g_X = np.take_along_axis(h.X, nom_idx[:, :, None], axis=1)            # (Dd, K, F)
    g_lv = take(h.logvol)
    g_Z = take(h.Z)
    g_W = take(h.W)
    g_rho = take(h.rho)
    feats_common = np.concatenate([g_base[..., None], g_X, g_lv[..., None]], axis=2)
    feats = {"LOSS": feats_common,
             "LOSSZ": np.concatenate([feats_common, g_Z[..., None]], axis=2),
             "LOSSW": np.concatenate([feats_common, g_W[..., None]], axis=2),
             "NETK": feats_common}
    loss_lab = (g_rho < 0).astype(float)
    # ---- hold-out evaluation
    P = len(POLICIES)
    Nout = np.zeros((P, p.n_seeds, Th))
    Sout = np.zeros((P, p.n_seeds, Th))
    hd = np.arange(hold0, hold0 + Th)
    nt_h = h.n_t[hd]
    ns_h = n_sub[hd]
    # SCORE: top n_sub of the nominated list by base score = first n_sub slots
    slot_sub = np.arange(K)[None, :] < ns_h[:, None]
    score_N = (g_rho[hd] * slot_sub).sum(axis=1)
    # BASEV: own top n_sub among all names
    bv_mask = _topk_mask(basev_score[hd], ns_h)
    basev_N = (h.rho[hd] * bv_mask).sum(axis=1)
    for s in range(p.n_seeds):
        Nout[0, s] = score_N
        Nout[1, s] = basev_N
    Sout[:, :, :] = ns_h[None, None, :]
    rows_day = np.arange(n_dec)
    for Y in range(p.dev_years, n_years):
        s0 = Y * A
        s1 = min((Y + 1) * A, n_dec)
        last = s0 - (H + 1)
        train_days = rows_day[(rows_day >= A) & (rows_day <= last)]
        tr_mask = slot_ok[train_days]                           # (nd, K)
        dsl = slice(s0 - hold0, s1 - hold0)
        for gname, pidx in (("LOSS", 2), ("LOSSZ", 3), ("LOSSW", 4), ("NETK", 5)):
            Atr = feats[gname][train_days][tr_mask]
            Aev = feats[gname][s0:s1]                           # (nd_ev, K, f)
            ytr = (loss_lab if gname != "NETK" else g_rho)[train_days][tr_mask]
            for s in range(p.n_seeds):
                brng = np.random.default_rng([dev_seed, 7919, Y, pidx, s])  # fixed training seeds
                sel = brng.random(Atr.shape[0]) < p.gate_bag
                if gname == "NETK":
                    model = _ridge(Atr[sel], ytr[sel] / 1e-2, p.gate_lambda)
                    sc = _predict(model, Aev.reshape(-1, Aev.shape[2])).reshape(Aev.shape[:2])
                else:
                    model = _logistic(Atr[sel], ytr[sel], p.gate_lambda)
                    sc = -_predict(model, Aev.reshape(-1, Aev.shape[2])).reshape(Aev.shape[:2])
                sc = np.where(slot_ok[s0:s1], sc, -np.inf)
                m = _topk_mask(sc, n_sub[s0:s1])
                Nout[pidx, s, dsl] = (g_rho[s0:s1] * m).sum(axis=1)
    if not return_diag:
        return Nout, Sout
    # diagnostics for calibration (not used for inference)
    nomh = slot_ok[hd]
    diag = {
        "xs_sd_R_bp": float(np.mean(h.R[hd].std(axis=1)) * 1e4),
        "nom_mean_rho_bp": float((g_rho[hd] * nomh).sum() / nomh.sum() * 1e4),
        "all_mean_rho_bp": float(h.rho[hd].mean() * 1e4),
        "nom_mean_R_minus_xs_bp": float(((g_R := take(h.R)[hd]) * nomh).sum() / nomh.sum() * 1e4
                                        - h.R[hd].mean() * 1e4),
        "base_rank_ic": float(np.mean([np.corrcoef(base_score[d], ranks[d])[0, 1] for d in hd])),
        "V_bp": {POLICIES[g]: float(Nout[g].mean(0).sum() / Sout[g].mean(0).sum() * 1e4)
                 for g in range(P)},
    }
    return Nout, Sout, diag


def contrast_list(p: Params):
    from intervals import Contrast
    out = []
    for name, g, hh, late in CONTRASTS:
        mask = None
        if late:
            mask = np.zeros(p.holdout_days)
            mask[p.late_start:] = 1.0
        out.append(Contrast(name, g, hh, mask))
    return out


# ----------------------------------------------------------------------------- scenarios

def scenario_params(name: str) -> Params:
    p = Params()
    if name == "F1":
        return p
    if name == "F2":
        return replace(p, tau_b=0.75 * p.b_norm / math.sqrt(p.n_feat), tau_kappa=0.8e-4, tau_z=0.5e-4)
    if name == "F3a":
        return replace(p, b_norm=0.0, kappa=0.0, c_z=0.0, beta_sd=0.0, drift=0.0)
    if name == "F3b":
        return replace(p, b_norm=0.0, kappa=0.0, c_z=0.0, beta_sd=0.0, drift=0.0,
                       tau_b=0.75 * 3.6e-4 / math.sqrt(p.n_feat), tau_kappa=0.8e-4, tau_z=0.5e-4)
    raise KeyError(name)

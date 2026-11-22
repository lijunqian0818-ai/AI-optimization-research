"""Phase E: literature methods for simultaneous intervals on 12 ratio contrasts (exploratory).

All methods act on the ratio influence series psi_jt of bootstrap_t.ratio_parts. For a contrast with
a window (P3), the window-only series x_j = psi_j[window] of length n_j is used (n_j = 1,075 or 775);
the window series sums to zero exactly, and se_j = sqrt(n_j * Omega_j) / T, where Omega_j is the
long-run variance estimate of x_j and T = 1,075 (because theta_hat - theta ~ T^-1 sum_window psi).
Bandwidth rules use n_j (so P3 gets its own S, nu).

M1  Newey-West / Bartlett with truncation S = round(1.3 n^{1/2}) (LLSW 2018), weights 1 - j/S for
    j < S; fixed-b critical values obtained by simulating the exact finite-n statistic under iid
    Gaussian data (the standard way fixed-b tables are produced):
      (a) Bonferroni: marginal fixed-b quantile of |t| at 1 - 0.05/12;
      (b) max-|t|: joint fixed-b law with the estimated long-run correlation matrix R_hat, simulated
          from K pre-drawn independent iid N(0,1) panels (the joint law depends on R only; any
          square root L of R gives it: x = L w).
M2  EWC (equal-weighted cosine): Omega = nu^-1 sum_{j=1..nu} Lambda_j^2,
    Lambda_j = sqrt(2/n) sum_t cos(pi j (t - 1/2) / n) x_t, nu = round(0.4 n^{2/3}) (LLSW 2018);
    Bonferroni with t_nu quantiles.
M3  bootstrap-t (stationary blocks), Bartlett bandwidth b (weights 1 - k/(b+1), i.e. S = b + 1) on the
    zero-padded full-T series, replicate-specific denominators and masks; implemented with the
    moving-sum identity (verified equal to bootstrap_t.bootstrap_t_stats in the tests).
M4  AR(1)-prewhitened Newey-West (recoloured): rho_hat = sum x_t x_{t-1} / sum x_{t-1}^2 clipped to
    [-0.97, 0.97], e_t = x_t - rho_hat x_{t-1}, Omega = NW_S(e)/(1 - rho_hat)^2 with M1's S;
    critical values from M1 (a) Bonferroni and (b) max-|t| (approximate: the prewhitened fixed-b
    law is not simulated).
M5  self-normalisation (Shao 2010): recursive estimates theta_t of the ratio contrast on the first t
    window days, W = n^-2 sum_t t^2 (theta_t - theta_n)^2, interval theta_n +- sqrt(c W / n),
    c = (1 - 0.05/12) quantile of U_1 = B(1)^2 / int_0^1 (B(r) - r B(1))^2 dr (simulated); Bonferroni.
"""
from __future__ import annotations

import math
import os

import numpy as np
from scipy.stats import t as student_t

ALPHA = 0.05


def nw_S(n):
    return int(round(1.3 * math.sqrt(n)))


def ewc_nu(n):
    return int(round(0.4 * n ** (2.0 / 3.0)))


# ------------------------------------------------------------------ long-run variance estimators

def nw_lrv(x, S):
    """Bartlett / Newey-West with truncation S (weights 1 - j/S, j < S) along the last axis, via the
    identity sum_t (moving sum of length S)^2 / (n S) (zero padding); x assumed mean zero."""
    n = x.shape[-1]
    b = S - 1
    pad = np.concatenate([np.zeros(x.shape[:-1] + (b,)), x, np.zeros(x.shape[:-1] + (b,))], -1)
    c = np.concatenate([np.zeros(pad.shape[:-1] + (1,)), np.cumsum(pad, -1)], -1)
    win = c[..., S:] - c[..., :-S]
    return (win ** 2).sum(-1) / (n * S)


def nw_cross(X, S):
    """Bartlett cross long-run covariance matrix of the columns of X (n, J), mean zero."""
    n, J = X.shape
    b = S - 1
    pad = np.vstack([np.zeros((b, J)), X, np.zeros((b, J))])
    c = np.vstack([np.zeros((1, J)), np.cumsum(pad, 0)])
    win = c[S:] - c[:-S]
    return win.T @ win / (n * S)


_COS = {}


def ewc_lrv(x, nu):
    n = x.shape[-1]
    key = (n, nu)
    if key not in _COS:
        t = np.arange(1, n + 1)
        _COS[key] = np.sqrt(2.0 / n) * np.cos(np.pi * np.arange(1, nu + 1)[:, None] * (t[None, :] - 0.5) / n)
    lam = x @ _COS[key].T
    return (lam ** 2).mean(-1)


def prewhite_lrv(x, S, cap=0.97):
    x0, x1 = x[..., :-1], x[..., 1:]
    rho = (x1 * x0).sum(-1) / (x0 * x0).sum(-1)
    rho = np.clip(rho, -cap, cap)
    e = x1 - rho[..., None] * x0
    e = e - e.mean(-1, keepdims=True)
    return nw_lrv(e, S) / (1 - rho) ** 2, rho


# ------------------------------------------------------------------ critical-value simulation

def simulate_fixedb_univariate(n, S, K=200_000, seed=40_000_001, chunk=5000):
    """|t| draws of the exact finite-n NW t statistic (truncation S) under iid N(0,1)."""
    rng = np.random.default_rng(seed)
    out = []
    for k0 in range(0, K, chunk):
        w = rng.standard_normal((min(chunk, K - k0), n))
        m = w.mean(1)
        out.append(np.sqrt(n) * np.abs(m) / np.sqrt(nw_lrv(w - m[:, None], S)))
    return np.concatenate(out)


def simulate_sn_U(n, K=200_000, seed=40_000_002, chunk=5000):
    """Draws of the self-normalised statistic n (xbar)^2 / W_n for iid N(0,1) data of length n;
    W_n = n^-2 sum_t t^2 (xbar_t - xbar_n)^2 (Shao 2010; its limit is U_1)."""
    rng = np.random.default_rng(seed)
    t = np.arange(1, n + 1)
    out = []
    for k0 in range(0, K, chunk):
        w = rng.standard_normal((min(chunk, K - k0), n))
        cs = np.cumsum(w, 1)
        xb = cs / t
        W = ((t[None, :] ** 2) * (xb - xb[:, -1:]) ** 2).sum(1) / n ** 2
        out.append(n * xb[:, -1] ** 2 / W)
    return np.concatenate(out)


def simulate_joint_panels(n_full, n_late, J, K=20_000, seed=40_000_003, chunk=500):
    """Pre-drawn independent iid N(0,1) panels (T x J): for the full window and the late window
    (last n_late days) the mean vectors and NW cross matrices (truncation by nw_S of each window).
    Returns dict with mean_f (K, J), C_f (K, J, J), mean_l, C_l."""
    rng = np.random.default_rng(seed)
    Sf, Sl = nw_S(n_full), nw_S(n_late)
    mf, Cf, ml, Cl = [], [], [], []
    for k0 in range(0, K, chunk):
        kk = min(chunk, K - k0)
        for _ in range(kk):
            W = rng.standard_normal((n_full, J))
            a = W.mean(0)
            mf.append(a)
            Cf.append(nw_cross(W - a, Sf))
            Wl = W[n_full - n_late:]
            b = Wl.mean(0)
            ml.append(b)
            Cl.append(nw_cross(Wl - b, Sl))
    return {"mean_f": np.array(mf), "C_f": np.array(Cf), "mean_l": np.array(ml), "C_l": np.array(Cl),
            "S_f": Sf, "S_l": Sl, "n_f": n_full, "n_l": n_late}


def maxt_quantile(panels, R, late_mask, alpha=ALPHA):
    """(1-alpha) quantile of max_j |t_j| for the joint fixed-b law with long-run correlation R;
    coordinates with late_mask[j] use the late-window statistic."""
    w, U = np.linalg.eigh(R)
    L = U * np.sqrt(np.clip(w, 0, None))
    out = np.empty((panels["mean_f"].shape[0], R.shape[0]))
    for key_m, key_C, n, sel in (("mean_f", "C_f", panels["n_f"], ~late_mask),
                                 ("mean_l", "C_l", panels["n_l"], late_mask)):
        if not sel.any():
            continue
        Ls = L[sel]
        num = panels[key_m] @ Ls.T
        den = np.einsum("jk,nkl,jl->nj", Ls, panels[key_C], Ls)
        out[:, sel] = np.sqrt(n) * np.abs(num) / np.sqrt(den)
    return float(np.quantile(out.max(1), 1 - alpha))


# ------------------------------------------------------------------ per-study evaluation

def window_series(psi, masks):
    return [psi[j][masks[j] > 0] for j in range(psi.shape[0])]


def lit_methods(Nbar, Sbar, contrasts, masks, crit, panels):
    """Returns dict method -> (halfwidth (J,), se (J,) or None) for M1a, M1b, M2, M4a, M4b, M5."""
    from bootstrap_t import ratio_parts
    T = Nbar.shape[1]
    J = len(contrasts)
    th, psi, _ = ratio_parts(Nbar, Sbar, contrasts, masks)
    xs = window_series(psi, masks)
    n = np.array([len(x) for x in xs])
    late = np.array([bool(c[3]) for c in contrasts])
    om_nw = np.array([nw_lrv(x, nw_S(len(x))) for x in xs])
    om_ewc = np.array([ewc_lrv(x, ewc_nu(len(x))) for x in xs])
    pw = [prewhite_lrv(x, nw_S(len(x))) for x in xs]
    om_pw = np.array([p[0] for p in pw])
    rho = np.array([p[1] for p in pw])
    se_nw = np.sqrt(n * om_nw) / T
    se_ewc = np.sqrt(n * om_ewc) / T
    se_pw = np.sqrt(n * om_pw) / T
    # long-run correlation on the zero-padded full-T series (NW, truncation of the full window)
    C = nw_cross(psi.T, nw_S(T))
    d = np.sqrt(np.diag(C))
    R = C / np.outer(d, d)
    q_maxt = maxt_quantile(panels, R, late)
    c_fb = np.where(late, crit["fixedb_bonf_late"], crit["fixedb_bonf_full"])
    c_ewc = np.array([student_t.ppf(1 - ALPHA / (2 * J), ewc_nu(k)) for k in n])
    # M5 self-normalisation with recursive ratio estimates on window days
    hw_sn = np.empty(J)
    for j, (_, g, h, lt) in enumerate(contrasts):
        w = masks[j] > 0
        Ng, Sg, Nh, Sh = Nbar[g][w], Sbar[g][w], Nbar[h][w], Sbar[h][w]
        tr = np.cumsum(Ng) / np.cumsum(Sg) - np.cumsum(Nh) / np.cumsum(Sh)
        nn = len(tr)
        tt = np.arange(1, nn + 1)
        W = ((tt ** 2) * (tr - tr[-1]) ** 2).sum() / nn ** 2
        c_sn = crit["sn_bonf_late"] if lt else crit["sn_bonf_full"]
        hw_sn[j] = math.sqrt(c_sn * W / nn)
    return th, {
        "M1a_nw_fixedb_bonf": (c_fb * se_nw, se_nw),
        "M1b_nw_fixedb_maxt": (q_maxt * se_nw, se_nw),
        "M2_ewc_tnu_bonf": (c_ewc * se_ewc, se_ewc),
        "M4a_prewhite_nw_bonf": (c_fb * se_pw, se_pw),
        "M4b_prewhite_nw_maxt": (q_maxt * se_pw, se_pw),
        "M5_sn_bonf": (hw_sn, None),
    }, {"q_maxt": q_maxt, "rho_pw": rho.tolist()}


def bt_fast_q(Nbar, Sbar, contrasts, masks, idx, th, bands, alpha=ALPHA):
    """Bootstrap-t q for several Bartlett bandwidths b (weights 1 - k/(b+1)) on the zero-padded
    full-T series; same statistic as bootstrap_t.bootstrap_t_stats (verified in tests)."""
    B, T = idx.shape
    cache, cacheM = {}, {}
    stats = {b: np.full((B, len(contrasts)), np.nan) for b in bands}
    for j, (_, g, h, late) in enumerate(contrasts):
        key = bool(late)
        if key not in cacheM:
            cacheM[key] = masks[j][idx]
        m = cacheM[key]
        parts = []
        bad = np.zeros(B, bool)
        for pol in (g, h):
            if pol not in cache:
                cache[pol] = (Nbar[pol][idx], Sbar[pol][idx])
            Ns = cache[pol][0] * m
            Ss = cache[pol][1] * m
            sS = Ss.sum(1)
            bad |= sS <= 0
            sSs = np.where(sS > 0, sS, 1.0)
            V = Ns.sum(1) / sSs
            parts.append((V, (Ns - V[:, None] * Ss) / (sSs / T)[:, None]))
        dev = np.abs(parts[0][0] - parts[1][0] - th[j])
        psis = parts[0][1] - parts[1][1]
        for b in bands:
            se = np.sqrt(np.maximum(nw_lrv(psis, b + 1), 0.0) / T)
            ok = (~bad) & (se > 0)
            stats[b][ok, j] = dev[ok] / se[ok]
    q = {}
    for b in bands:
        st = stats[b]
        mx = np.nanmax(np.where(np.isnan(st), -np.inf, st), axis=1)
        mx = mx[np.isfinite(mx)]
        q[b] = (float(np.quantile(mx, 1 - alpha)), int(np.isnan(st).sum()))
    return q, stats


def critical_values(T=1075, n_late=775, J=12, cache_path=None):
    """Simulated critical values (cached to npz)."""
    if cache_path and os.path.exists(cache_path):
        d = np.load(cache_path)
        return {k: float(d[k]) for k in d.files}
    lev = 1 - ALPHA / J                       # two-sided per-coordinate level alpha / J
    fb_f = simulate_fixedb_univariate(T, nw_S(T))
    fb_l = simulate_fixedb_univariate(n_late, nw_S(n_late), seed=40_000_011)
    sn_f = simulate_sn_U(T)
    sn_l = simulate_sn_U(n_late, seed=40_000_012)
    out = {"fixedb_bonf_full": float(np.quantile(fb_f, lev)), "fixedb_bonf_late": float(np.quantile(fb_l, lev)),
           "fixedb_975_full": float(np.quantile(fb_f, 0.95)), "fixedb_975_late": float(np.quantile(fb_l, 0.95)),
           "sn_bonf_full": float(np.quantile(sn_f, lev)), "sn_bonf_late": float(np.quantile(sn_l, lev)),
           "sn_95_full": float(np.quantile(sn_f, 0.95)), "sn_95_late": float(np.quantile(sn_l, 0.95)),
           "S_full": nw_S(T), "S_late": nw_S(n_late), "nu_full": ewc_nu(T), "nu_late": ewc_nu(n_late),
           "K_univariate": 200_000}
    if cache_path:
        np.savez(cache_path, **out)
    return out

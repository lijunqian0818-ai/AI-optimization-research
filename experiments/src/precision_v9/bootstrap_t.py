"""Paired bootstrap-t rule of REVISION_PROTOCOL.md (Phase D candidate) and its HAC fallback.

For contrast j = (g, h, window mask m_j) on seed-averaged daily totals N_t, S_t (t = 1..T):
  V_j^g = sum m N^g / sum m S^g,  d_j^g = T^-1 sum m S^g,  theta_j = V_j^g - V_j^h,
  psi_jt = m_t (N_t^g - V^g S_t^g) / d^g - m_t (N_t^h - V^h S_t^h) / d^h   (sums to 0 exactly),
  s_j(b)^2 = T^-1 * [gamma_0 + 2 sum_{k=1..b} (1 - k/(b+1)) gamma_k],  gamma_k = T^-1 sum psi_t psi_{t+k}
  (Bartlett / Newey-West with biased autocovariances: positive semidefinite, see `hac_var_direct`).
Bootstrap-t: in each resample (stationary or circular fixed-length blocks over dates; the same dates
for every series), recompute V*, d*, the masks m*, psi*, theta*_j and s*_j(b) on the resampled
sequence; q = 95% quantile of max_j |theta*_j - theta_j| / s*_j(b); interval theta_j +- q s_j(b).
Fallback: theta_j +- z_{1-0.05/(2J)} s_j(b).
Edge cases as in intervals.py: s_j = 0 -> degenerate interval, excluded from the max; a resample
with a zero denominator or s*_j = 0 is void for that contrast; > 0.1% void for any contrast ->
primary inapplicable (fallback used).
"""
from __future__ import annotations

import numpy as np
from scipy.stats import norm

from intervals import stationary_bootstrap_indices

VOID_LIMIT = 0.001


def circular_block_indices(T, B, L, rng):
    """Circular fixed-length block bootstrap (Politis & Romano 1992): blocks of exactly L dates
    with uniform starts on the circle, concatenated and truncated to T."""
    L = int(L)
    nb = -(-T // L)
    starts = rng.integers(0, T, size=(B, nb))
    off = np.arange(L)
    idx = (starts[:, :, None] + off[None, None, :]).reshape(B, nb * L)[:, :T] % T
    return idx


def bartlett_weights(b):
    k = np.arange(1, b + 1)
    return 1.0 - k / (b + 1.0)


def autocov(psi, kmax):
    """Biased autocovariances gamma_0..gamma_kmax along the last axis (no centring: psi sums to 0
    by construction). psi: (..., T). Returns (..., kmax+1)."""
    T = psi.shape[-1]
    out = np.empty(psi.shape[:-1] + (kmax + 1,))
    for k in range(kmax + 1):
        out[..., k] = np.einsum("...t,...t->...", psi[..., k:], psi[..., :T - k]) / T
    return out


def hac_var_from_gamma(gam, b):
    """Long-run variance (Bartlett, bandwidth b) from autocovariances gam (..., >= b+1)."""
    if b == 0:
        return gam[..., 0]
    return gam[..., 0] + 2.0 * (gam[..., 1:b + 1] * bartlett_weights(b)).sum(axis=-1)


def hac_var_direct(psi, b):
    """Same quantity via the identity sum_t (sum_{i=0..b} psi_{t-i})^2 / (T (b+1)) (zero padding),
    which shows it is a sum of squares, hence >= 0."""
    T = psi.shape[-1]
    pad = np.concatenate([np.zeros(psi.shape[:-1] + (b,)), psi, np.zeros(psi.shape[:-1] + (b,))], -1)
    c = np.concatenate([np.zeros(pad.shape[:-1] + (1,)), np.cumsum(pad, -1)], -1)
    win = c[..., b + 1:] - c[..., :-(b + 1)]          # all windows of length b+1
    return (win ** 2).sum(-1) / (T * (b + 1.0))


def ratio_parts(Nbar, Sbar, contrasts, masks):
    """theta (J,), psi (J, T), per-contrast zero-denominator flags."""
    J, T = len(contrasts), Nbar.shape[1]
    th = np.zeros(J)
    psi = np.zeros((J, T))
    zero = np.zeros(J, bool)
    for j, (_, g, h, _) in enumerate(contrasts):
        m = masks[j]
        tot = []
        for pol in (g, h):
            sN, sS = (m * Nbar[pol]).sum(), (m * Sbar[pol]).sum()
            if sS <= 0:
                zero[j] = True
                tot.append((0.0, None))
                continue
            V = sN / sS
            d = sS / T
            tot.append((V, m * (Nbar[pol] - V * Sbar[pol]) / d))
        th[j] = tot[0][0] - tot[1][0]
        if not zero[j]:
            psi[j] = tot[0][1] - tot[1][1]
    return th, psi, zero


def hac_se(psi, bands):
    """{b: s_j(b)} with s^2 = LRV / T."""
    T = psi.shape[-1]
    gam = autocov(psi, max(bands))
    return {b: np.sqrt(np.maximum(hac_var_from_gamma(gam, b), 0.0) / T) for b in bands}


def bootstrap_t_stats(Nbar, Sbar, contrasts, masks, idx, th, bands):
    """For resample indices idx (B, T): returns {b: stat (B, J)} with stat = |theta* - theta| / s*(b)
    (nan where void), and {b: void (B, J) bool}."""
    B, T = idx.shape
    J = len(contrasts)
    kmax = max(bands)
    stats = {b: np.full((B, J), np.nan) for b in bands}
    void = {b: np.zeros((B, J), bool) for b in bands}
    for j, (_, g, h, _) in enumerate(contrasts):
        m = masks[j][idx]
        parts = []
        bad = np.zeros(B, bool)
        for pol in (g, h):
            Ns = Nbar[pol][idx] * m
            Ss = Sbar[pol][idx] * m
            sS = Ss.sum(1)
            bad |= sS <= 0
            sSs = np.where(sS > 0, sS, 1.0)
            V = Ns.sum(1) / sSs
            d = sSs / T
            parts.append((V, (Ns - V[:, None] * Ss) / d[:, None]))
        ths = parts[0][0] - parts[1][0]
        psis = parts[0][1] - parts[1][1]
        gam = autocov(psis, kmax)
        dev = np.abs(ths - th[j])
        for b in bands:
            v = hac_var_from_gamma(gam, b)
            se = np.sqrt(np.maximum(v, 0.0) / T)
            ok = (~bad) & (se > 0)
            stats[b][ok, j] = dev[ok] / se[ok]
            void[b][~ok, j] = True
    return stats, void


def bt_rule(N, S, contrasts, masks, configs, bands, B, rng_for, alpha=0.05, se_tol=1e-15):
    """Evaluate every (block type, L) configuration and every bandwidth on one study.

    configs: list of (type, L) with type in {"stat", "circ"}; rng_for(config_index) -> Generator.
    Returns dict with theta, se[b], q[(type, L, b)], applicable[(type, L, b)], voids, zero_se, z.
    """
    Nbar = N.mean(axis=1) if N.ndim == 3 else N
    Sbar = S.mean(axis=1) if S.ndim == 3 else S
    T = Nbar.shape[1]
    J = len(contrasts)
    th, psi, zero_den = ratio_parts(Nbar, Sbar, contrasts, masks)
    se = hac_se(psi, bands)
    out = {"theta": th, "se": se, "q": {}, "applicable": {}, "void": {}, "zero_den": zero_den,
           "z": float(norm.ppf(1 - alpha / (2 * J)))}
    zero_se = {b: se[b] <= se_tol for b in bands}
    out["zero_se"] = zero_se
    for ci, (typ, L) in enumerate(configs):
        rng = rng_for(ci)
        idx = (stationary_bootstrap_indices(T, B, L, rng) if typ == "stat"
               else circular_block_indices(T, B, L, rng))
        stats, void = bootstrap_t_stats(Nbar, Sbar, contrasts, masks, idx, th, bands)
        for b in bands:
            nvoid = void[b].sum(0)
            act = ~zero_se[b]
            st = stats[b][:, act]
            mx = np.nanmax(np.where(np.isnan(st), -np.inf, st), axis=1) if act.any() else np.zeros(B)
            mx = mx[np.isfinite(mx)]
            out["q"][(typ, L, b)] = float(np.quantile(mx, 1 - alpha)) if mx.size else np.nan
            out["applicable"][(typ, L, b)] = bool(np.all(nvoid <= VOID_LIMIT * B))
            out["void"][(typ, L, b)] = int(nvoid.sum())
    return out

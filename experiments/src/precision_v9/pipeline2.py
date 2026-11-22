"""Phase D pipeline (REVISION_PROTOCOL.md): 12 contrasts on two base classes, five training seeds.

New module; the first run's `pipeline.py` is imported for its helpers and is not modified.

Base classes (stand-ins for the plan's LightGBM and ridge bases; LightGBM is not simulated):
  A = rank ridge on x_1..x_10 (as in the first run);
  B = rank ridge on x_1..x_10 and x_k^2 - 1 (a more flexible, noisier learner).
For each base b in {A, B} the six policies SCORE_b, BASEV_b, LOSS_b, LOSSZ_b, LOSSW_b, NETK_b
and the contrasts P1_b..P6_b of PLAN §A4.1 (P3_b on the late window, hold-out day >= 300).
Policy index = 6 * base + k with k in (SCORE, BASEV, LOSS, LOSSZ, LOSSW, NETK).

`flip_year` (tests only): sign-flips the regime variables of year Y and every return shock whose
state day lies in year Y (used to audit the exact-zero symmetry argument of F3a / F3b).
"""
from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from pipeline import (History, Params, SplitRNG, _ar1_from, _logistic, _predict, _ridge,
                      _ridge_from_stats, _topk_mask, b_bar)

KINDS = ["SCORE", "BASEV", "LOSS", "LOSSZ", "LOSSW", "NETK"]
BASES = ["A", "B"]
POLICIES2 = [f"{k}_{b}" for b in BASES for k in KINDS]
_C = [("P1", 2, 0, False), ("P2", 3, 2, False), ("P3", 4, 2, True),
      ("P4", 5, 0, False), ("P5", 2, 1, False), ("P6", 5, 1, False)]
CONTRASTS2 = [(f"{n}_{b}", 6 * bi + g, 6 * bi + h, late)
              for bi, b in enumerate(BASES) for (n, g, h, late) in _C]
N_SEEDS = 5


def generate_history2(p: Params, dev_seed: int, hold_seed: int, flip_year: int | None = None) -> History:
    """As pipeline.generate_history (same random-number layout), plus the optional year flip."""
    Nn, F, H = p.n_names, p.n_feat, p.H
    n_dec = p.dev_years * p.days_per_year + p.holdout_days
    D = p.burn + n_dec + H + 1
    hold0 = p.dev_years * p.days_per_year
    cut_raw = p.burn + hold0 + 1
    n_years = int(math.ceil(n_dec / p.days_per_year)) + 1
    g = SplitRNG(dev_seed, hold_seed)
    bb = b_bar(p)
    eta = g.normal(n_years, (F,), p.dev_years)
    bY = bb[None, :] + p.tau_b * eta
    kY = p.kappa + p.tau_kappa * g.normal(n_years, (), p.dev_years)
    cY = p.c_z + p.tau_z * g.normal(n_years, (), p.dev_years)
    beta = 1.0 + p.beta_sd * g.dev.standard_normal(Nn)
    logsig0 = math.log(p.sig_med) + p.sig_logsd * g.dev.standard_normal(Nn)
    X = _ar1_from(g.normal(D, (Nn, F), cut_raw), p.x_phi)
    Z = _ar1_from(g.normal(D, (Nn,), cut_raw), p.z_phi)
    Wf = _ar1_from(g.normal(D, (Nn,), cut_raw), p.z_phi)
    u = _ar1_from(g.normal(D, (Nn,), cut_raw), p.u_phi, sd=p.u_sd)
    v = _ar1_from(g.normal(D, (), cut_raw), p.vol_phi, sd=p.vol_sd)
    e_m = g.normal(D, (), cut_raw)
    eps = g.normal(D, (Nn,), cut_raw)
    day_year = np.clip((np.arange(D) - p.burn) // p.days_per_year, 0, n_years - 1)
    if flip_year is not None:
        assert p.drift == 0 and p.beta_sd == 0 and p.b_norm == 0 and p.kappa == 0 and p.c_z == 0
        bY[flip_year] *= -1
        kY[flip_year] *= -1
        cY[flip_year] *= -1
        # return day s uses state day s-1: flip shocks of days s with day_year[s-1] == Y
        sel = np.zeros(D, bool)
        sel[1:] = day_year[:-1] == flip_year
        e_m[sel] *= -1
        eps[sel] *= -1
    logsig = logsig0[None, :] + u
    ls_c = logsig - logsig.mean(axis=1, keepdims=True)
    ls_std = ls_c / math.sqrt(p.sig_logsd ** 2 + p.u_sd ** 2)
    mu = (np.einsum("dnf,df->dn", X, bY[day_year]) - kY[day_year][:, None] * ls_std
          + cY[day_year][:, None] * Z)
    mkt = p.drift + p.mkt_sd * np.exp(v - p.vol_sd ** 2 / 2) * e_m
    r = np.zeros((D, Nn))
    r[1:] = (beta[None, :] * mkt[1:, None] + mu[:-1]
             + np.exp(logsig[1:] + v[1:, None] - p.vol_sd ** 2 / 2) * eps[1:])
    cs = np.vstack([np.zeros((1, Nn)), np.cumsum(r, axis=0)])
    dec = np.arange(p.burn, p.burn + n_dec)
    R = cs[dec + H + 1] - cs[dec + 1]
    cs2 = np.vstack([np.zeros((1, Nn)), np.cumsum(r * r, axis=0)])
    w = p.vol_window
    rms = np.sqrt((cs2[dec + 1] - cs2[dec + 1 - w]) / w)
    fill = g.uniform(n_dec, (Nn,), hold0) < p.fill_prob
    rho = np.where(fill, R - p.cost, 0.0)
    short = g.uniform(n_dec, (), hold0) < p.p_short
    n_t = np.where(short, g.integers(p.short_min, p.K, n_dec, hold0), p.K)
    return History(X=X[dec], Z=Z[dec], W=Wf[dec], logvol=np.log(rms), R=R, fill=fill, rho=rho,
                   n_t=n_t, year=(np.arange(n_dec) // p.days_per_year))


def _std_design(Atr, Aev):
    """Standardise on all training rows (shared by the five seeds); prepend an intercept."""
    m = Atr.mean(axis=0)
    sd = Atr.std(axis=0)
    sd[sd == 0] = 1.0
    Ztr = np.empty((Atr.shape[0], Atr.shape[1] + 1))
    Ztr[:, 0] = 1.0
    Ztr[:, 1:] = (Atr - m) / sd
    Zev = (Aev - m) / sd
    return Ztr, Zev


def _logistic_ws(Z, y, lam, beta0=None, iters=30, tol=1e-8):
    """L2-penalised logistic regression (Newton) on a standardised design with intercept column,
    warm-started at beta0 (same optimum, fewer iterations)."""
    k = Z.shape[1]
    pen = lam * np.eye(k)
    pen[0, 0] = 0.0
    if beta0 is None:
        beta = np.zeros(k)
        pbar = min(max(y.mean(), 1e-6), 1 - 1e-6)
        beta[0] = math.log(pbar / (1 - pbar))
    else:
        beta = beta0.copy()
    for _ in range(iters):
        pr = 1.0 / (1.0 + np.exp(-(Z @ beta)))
        g = Z.T @ (pr - y) + pen @ beta
        Hm = (Z * (pr * (1 - pr))[:, None]).T @ Z + pen
        step = np.linalg.solve(Hm, g)
        beta -= step
        if np.max(np.abs(step)) < tol:
            break
    return beta


def _ridge_z(Z, y, lam):
    k = Z.shape[1]
    pen = lam * np.eye(k)
    pen[0, 0] = 0.0
    return np.linalg.solve(Z.T @ Z + pen, Z.T @ y)


def _base_design(X, kind):
    n_dec, Nn, F = X.shape
    one = np.ones((n_dec, Nn, 1))
    if kind == "A":
        return np.concatenate([one, X], axis=2)
    return np.concatenate([one, X, X * X - 1.0], axis=2)


def run_history2(p: Params, dev_seed: int, hold_seed: int, n_seeds: int = N_SEEDS,
                 flip_year: int | None = None, return_decisions: bool = False):
    """One history, both base classes. Returns N, S of shape (12, n_seeds, T_hold)
    (and, if requested, the submission masks over the hold-out: dict policy -> (seeds, Th, Nn))."""
    h = generate_history2(p, dev_seed, hold_seed, flip_year)
    A, H, K = p.days_per_year, p.H, p.K
    n_dec = h.R.shape[0]
    Nn = p.n_names
    hold0 = p.dev_years * A
    Th = p.holdout_days
    n_sub = np.ceil(p.c * h.n_t).astype(int)
    n_years = int(math.ceil(n_dec / A))
    ranks = np.argsort(np.argsort(h.R, axis=1), axis=1) / (Nn - 1) - 0.5
    Rd = h.R - h.R.mean(axis=1, keepdims=True)
    sdR = Rd.std(axis=1, keepdims=True)
    Rw = np.clip(Rd, -p.basev_winsor * sdR, p.basev_winsor * sdR) / 1e-2
    hd = np.arange(hold0, hold0 + Th)
    P = 12
    Nout = np.zeros((P, n_seeds, Th))
    Sout = np.broadcast_to(n_sub[hd][None, None, :], (P, n_seeds, Th)).astype(float).copy()
    decisions = {} if return_decisions else None
    rows_day = np.arange(n_dec)
    slot_ok = np.arange(K)[None, :] < h.n_t[:, None]
    for bi, kind in enumerate(BASES):
        X1 = _base_design(h.X, kind)
        k1 = X1.shape[2]
        cXtX = np.concatenate([np.zeros((1, k1, k1)), np.cumsum(np.einsum("dni,dnj->dij", X1, X1), 0)])
        cXty = np.concatenate([np.zeros((1, k1)), np.cumsum(np.einsum("dni,dn->di", X1, ranks), 0)])
        cXtyv = np.concatenate([np.zeros((1, k1)), np.cumsum(np.einsum("dni,dn->di", X1, Rw), 0)])
        base_score = np.full((n_dec, Nn), np.nan)
        basev_score = np.full((n_dec, Nn), np.nan)
        for Y in range(1, n_years):
            s0, s1 = Y * A, min((Y + 1) * A, n_dec)
            last = s0 - (H + 1)
            coef = _ridge_from_stats(cXtX[last + 1], cXty[last + 1], p.base_lambda)
            base_score[s0:s1] = X1[s0:s1] @ coef
            first = max(0, s0 - p.basev_years * A)
            coefv = _ridge_from_stats(cXtX[last + 1] - cXtX[first], cXtyv[last + 1] - cXtyv[first],
                                      p.basev_lambda)
            basev_score[s0:s1] = X1[s0:s1] @ coefv
        del X1
        order = np.argsort(-np.where(np.isnan(base_score), -np.inf, base_score), axis=1, kind="stable")
        nom_idx = order[:, :K]

        def take(M):
            return np.take_along_axis(M, nom_idx, axis=1)
        g_base = take(np.where(np.isnan(base_score), 0.0, base_score))
        g_X = np.take_along_axis(h.X, nom_idx[:, :, None], axis=1)
        g_rho = take(h.rho)
        common = np.concatenate([g_base[..., None], g_X, take(h.logvol)[..., None]], axis=2)
        feats = {"LOSS": common,
                 "LOSSZ": np.concatenate([common, take(h.Z)[..., None]], axis=2),
                 "LOSSW": np.concatenate([common, take(h.W)[..., None]], axis=2),
                 "NETK": common}
        loss_lab = (g_rho < 0).astype(float)
        ns_h = n_sub[hd]
        slot_sub = np.arange(K)[None, :] < ns_h[:, None]
        off = 6 * bi
        Nout[off + 0] = (g_rho[hd] * slot_sub).sum(axis=1)[None, :]
        bv_mask = _topk_mask(basev_score[hd], ns_h)
        Nout[off + 1] = (h.rho[hd] * bv_mask).sum(axis=1)[None, :]
        if return_decisions:
            sc_mask = np.zeros((Th, Nn), bool)
            np.put_along_axis(sc_mask, nom_idx[hd], slot_sub, axis=1)
            decisions[POLICIES2[off]] = np.repeat(sc_mask[None], n_seeds, 0)
            decisions[POLICIES2[off + 1]] = np.repeat(bv_mask[None], n_seeds, 0)
            for k in range(2, 6):
                decisions[POLICIES2[off + k]] = np.zeros((n_seeds, Th, Nn), bool)
        for Y in range(p.dev_years, n_years):
            s0, s1 = Y * A, min((Y + 1) * A, n_dec)
            last = s0 - (H + 1)
            train_days = rows_day[(rows_day >= A) & (rows_day <= last)]
            tr_mask = slot_ok[train_days]
            dsl = slice(s0 - hold0, s1 - hold0)
            for gname, k in (("LOSS", 2), ("LOSSZ", 3), ("LOSSW", 4), ("NETK", 5)):
                Atr = feats[gname][train_days][tr_mask]
                Aev = feats[gname][s0:s1]
                ytr = (loss_lab if gname != "NETK" else g_rho)[train_days][tr_mask]
                Ztr, Zev = _std_design(Atr, Aev.reshape(-1, Aev.shape[2]))
                beta_ws = None
                for s in range(n_seeds):
                    brng = np.random.default_rng([dev_seed, 7919, bi, Y, k, s])
                    sel = brng.random(Atr.shape[0]) < p.gate_bag
                    if gname == "NETK":
                        bcoef = _ridge_z(Ztr[sel], ytr[sel] / 1e-2, p.gate_lambda)
                        sc = (Zev @ bcoef[1:] + bcoef[0]).reshape(Aev.shape[:2])
                    else:
                        bcoef = _logistic_ws(Ztr[sel], ytr[sel], p.gate_lambda, beta_ws)
                        beta_ws = bcoef
                        sc = -(Zev @ bcoef[1:] + bcoef[0]).reshape(Aev.shape[:2])
                    sc = np.where(slot_ok[s0:s1], sc, -np.inf)
                    m = _topk_mask(sc, n_sub[s0:s1])
                    Nout[off + k, s, dsl] = (g_rho[s0:s1] * m).sum(axis=1)
                    if return_decisions:
                        dm = np.zeros((s1 - s0, Nn), bool)
                        np.put_along_axis(dm, nom_idx[s0:s1], m, axis=1)
                        decisions[POLICIES2[off + k]][s, dsl] = dm
    if return_decisions:
        return Nout, Sout, decisions, h
    return Nout, Sout


def late_mask(p: Params):
    m = np.zeros(p.holdout_days)
    m[p.late_start:] = 1.0
    return m


def masks2(p: Params):
    """(J, T) window masks of the 12 contrasts."""
    lm = late_mask(p)
    return np.stack([lm if late else np.ones(p.holdout_days) for (_, _, _, late) in CONTRASTS2])


# ----------------------------------------------------------------------- policy-level scenarios

MU2 = np.array([30.0, 29.0, 28.0, 31.0, 27.0, 26.0, 33.0, 31.5, 30.0, 30.5, 29.0, 28.0]) * 1e-4


def policy_level_series(scen: str, hold_seed: int, T: int = 1075):
    """S0 i.i.d.; S1 overlap only (5-day moving sums of iid shocks); S2 overlap + AR(1) with a
    10-day half-life. N_t^g = S_t (mu_g + 0.01 (sqrt(.8) c_t + sqrt(.2) e_t^g)); truth mu_g - mu_h."""
    rng = np.random.default_rng([hold_seed, 3])
    P = 12
    short = rng.random(T) < 0.05
    n_t = np.where(short, rng.integers(10, 30, size=T), 30)
    S1 = np.ceil(0.5 * n_t)

    def noise(shape):
        if scen == "S0":
            return rng.standard_normal(shape + (T,))
        if scen == "S1":
            e = rng.standard_normal(shape + (T + 4,))
            c = np.cumsum(e, axis=-1)
            c = np.concatenate([np.zeros(shape + (1,)), c], axis=-1)
            return (c[..., 5:] - c[..., :-5]) / math.sqrt(5.0)
        if scen == "S2":
            e = rng.standard_normal(shape + (T + 4,))
            c = np.concatenate([np.zeros(shape + (1,)), np.cumsum(e, axis=-1)], axis=-1)
            ma = (c[..., 5:] - c[..., :-5]) / math.sqrt(5.0)
            phi = 0.5 ** (1 / 10)
            a = rng.standard_normal(shape + (T,))
            ar = np.empty_like(a)
            ar[..., 0] = a[..., 0]
            sd_in = math.sqrt(1 - phi * phi)
            for t in range(1, T):
                ar[..., t] = phi * ar[..., t - 1] + sd_in * a[..., t]
            return math.sqrt(0.5) * ma + math.sqrt(0.5) * ar
        raise KeyError(scen)
    common = noise(())
    idio = noise((P,))
    N = S1[None, :] * (MU2[:, None] + 0.01 * (math.sqrt(0.8) * common[None, :] + math.sqrt(0.2) * idio))
    S = np.repeat(S1[None, :], P, axis=0)
    return N[:, None, :], S[:, None, :]


def policy_level_truth():
    return np.array([MU2[g] - MU2[h] for _, g, h, _ in CONTRASTS2])


def scenario_params2(name: str) -> Params:
    from pipeline import scenario_params
    return scenario_params(name[:-1] if name.endswith("c") else name)

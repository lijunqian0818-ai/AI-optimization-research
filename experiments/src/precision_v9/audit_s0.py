"""Audit of the S0 under-coverage (new module; existing modules are imported, not changed).

Ladder (J = 12 contrasts, T = 1,075 days, 4,000 replications per cell, seeds >= 30,000,000):
  L0 indep : 24 independent policies, contrast j = (2j, 2j+1); iid N(0,1) shocks; S_t = 15.
  L1 corr  : as L0 with a common factor in the first policy of each pair (contrast corr ~0.45).
  L2 struct: the real 12-policy structure (CONTRASTS2: P1..P6 x 2 bases, exact identities
             P4-P1 = P6-P5 per base), shocks sqrt(.8) common + sqrt(.2) idio; P3 full window.
  L3 mask  : L2 + P3 on the late window (hold-out day >= 300).
  L4 den   : L3 + random denominators (5% short days, S_t = ceil(n_t/2), n_t ~ U{10..29}) = S0.
  L5 tdist : L4 + Student-t(4) shocks scaled to unit variance.
  L6 overlap: L5 + 5-day overlap (5-day moving sums / sqrt 5).
Daily numerator N_t^g = S_t (mu_g + 0.01 e_t^g); truth theta_j = mu_g - mu_h exactly, and
E[sum N]/E[sum S] = E[sum N / sum S] = mu_g (noise independent of S, mean zero).

Methods per replication:
  (i)  per-coordinate Student-t with Bonferroni: se_j = sqrt(n_j sum_w psi^2 / (n_j - 1)) / T on
       the window (= s/sqrt(n_j) of the daily differences when S is constant; exact in L0-L3),
       critical value t_{n_j - 1, 1 - 0.05/24};
  (ii) iid paired bootstrap-t: L = 1, b = 0 (plain iid influence s.e.), B = 999; computed by
       `iid_bt_counts` (exact count-based algebra, verified against bt_rule in the tests);
  (iii) bootstrap-t stat L24 b20 (Phase D rule), B = 999;
  (iv) old rule (intervals.py, stationary L24, fixed bootstrap-sd standardisation), B = 2,000.
"""
import os

for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[_v] = "1"

import argparse
import json
import math
import time
from multiprocessing import Pool

import numpy as np
from scipy.stats import t as student_t

T_DAYS = 1075
J = 12
LATE = 300
STEPS = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
SEED0 = 30_000_000
MU24 = (np.arange(24) % 7) * 1e-4                    # arbitrary fixed means (decimals)


def ladder_contrasts(step):
    from pipeline2 import CONTRASTS2
    if step in ("L0", "L1"):
        return [(f"c{j}", 2 * j, 2 * j + 1, False) for j in range(J)]
    late = step not in ("L2",)
    return [(n, g, h, (lt and late)) for (n, g, h, lt) in CONTRASTS2]


def ladder_masks(contrasts, T=T_DAYS):
    m = np.ones((len(contrasts), T))
    for j, c in enumerate(contrasts):
        if c[3]:
            m[j, :LATE] = 0.0
    return m


def ladder_series(step, seed, T=T_DAYS):
    """Returns N, S of shape (P, 1, T), mu (P,)."""
    from pipeline2 import MU2
    rng = np.random.default_rng([seed, 11])
    if step in ("L0", "L1"):
        P, mu = 24, MU24
    else:
        P, mu = 12, MU2
    if step in ("L4", "L5", "L6"):
        short = rng.random(T) < 0.05
        n_t = np.where(short, rng.integers(10, 30, size=T), 30)
        S1 = np.ceil(0.5 * n_t)
    else:
        S1 = np.full(T, 15.0)
    extra = 4 if step == "L6" else 0

    def shocks(shape):
        if step in ("L5", "L6"):
            x = rng.standard_t(4, size=shape + (T + extra,)) / math.sqrt(2.0)   # var(t4) = 2
        else:
            x = rng.standard_normal(shape + (T + extra,))
        if step == "L6":
            c = np.concatenate([np.zeros(shape + (1,)), np.cumsum(x, -1)], -1)
            x = (c[..., 5:] - c[..., :-5]) / math.sqrt(5.0)
        return x

    if step == "L0":
        e = shocks((P,))
    elif step == "L1":
        e = shocks((P,))
        c = shocks(())
        rho = 0.9
        first = np.arange(P) % 2 == 0
        e[first] = math.sqrt(rho) * c[None, :] + math.sqrt(1 - rho) * e[first]
    else:
        c = shocks(())
        e = math.sqrt(0.8) * c[None, :] + math.sqrt(0.2) * shocks((P,))
    N = S1[None, :] * (mu[:, None] + 0.01 * e)
    S = np.repeat(S1[None, :], P, axis=0)
    return N[:, None, :], S[:, None, :], mu


def truth_of(contrasts, mu):
    return np.array([mu[g] - mu[h] for _, g, h, _ in contrasts])


def student_bonf(Nbar, Sbar, contrasts, masks, alpha=0.05):
    from bootstrap_t import ratio_parts
    th, psi, _ = ratio_parts(Nbar, Sbar, contrasts, masks)
    T = Nbar.shape[1]
    nj = masks.sum(1)
    se = np.sqrt(nj * (psi ** 2).sum(1) / (nj - 1)) / T
    crit = student_t.ppf(1 - alpha / (2 * len(contrasts)), nj - 1)
    return th, se, crit


def one_rep(step, rep, B_bt=999, B_old=2000, extra_B=None):
    from bootstrap_t import bt_rule
    from intervals import Contrast, simultaneous_intervals
    seed = SEED0 + 100_000 * STEPS.index(step) + rep
    cs = ladder_contrasts(step)
    masks = ladder_masks(cs)
    N, S, mu = ladder_series(step, seed)
    th0 = truth_of(cs, mu)
    Nbar, Sbar = N[:, 0], S[:, 0]
    row = {"rep": rep, "seed": seed}
    th, se_t, crit_t = student_bonf(Nbar, Sbar, cs, masks)
    row["th"] = th.tolist()
    row["truth"] = th0.tolist()
    row["se_t"] = se_t.tolist()
    row["crit_t"] = crit_t.tolist()
    from bootstrap_t import hac_se, ratio_parts
    from intervals import stationary_bootstrap_indices
    _, psi, _ = ratio_parts(Nbar, Sbar, cs, masks)
    se0 = hac_se(psi, [0])[0]
    idx1 = stationary_bootstrap_indices(T_DAYS, B_bt, 1, np.random.default_rng([seed, 21]))
    cnt1 = np.bincount((np.arange(B_bt)[:, None] * T_DAYS + idx1).ravel(),
                       minlength=B_bt * T_DAYS).reshape(B_bt, T_DAYS)
    row["se_iid"] = se0.tolist()
    row["q_iid"], st2 = iid_bt_counts(Nbar, Sbar, cs, masks, cnt1, th, se0)
    r3 = bt_rule(N, S, cs, masks, [("stat", 24)], [20], B_bt, rng_for=lambda i: np.random.default_rng([seed, 22]))
    row["se_hac20"] = r3["se"][20].tolist()
    row["q_bt24"] = r3["q"][("stat", 24, 20)]
    row["app"] = bool(np.all(np.isnan(st2).sum(0) <= 0.001 * B_bt) and r3["applicable"][("stat", 24, 20)])
    if np.max(np.abs(r3["theta"] - th)) > 1e-14:
        raise RuntimeError("theta mismatch")
    cons = [Contrast(n, g, h, masks[j] if late else None) for j, (n, g, h, late) in enumerate(cs)]
    o = simultaneous_intervals(N, S, cons, B=B_old, mean_block=24, rng=np.random.default_rng([seed, 23]))
    row["se_old"] = o.se.tolist()
    row["q_old"] = o.q
    if extra_B:
        idxb = stationary_bootstrap_indices(T_DAYS, extra_B, 1, np.random.default_rng([seed, 31]))
        cntb = np.bincount((np.arange(extra_B)[:, None] * T_DAYS + idxb).ravel(),
                           minlength=extra_B * T_DAYS).reshape(extra_B, T_DAYS)
        q2b, _ = iid_bt_counts(Nbar, Sbar, cs, masks, cntb, th, se0)
        r3b = bt_rule(N, S, cs, masks, [("stat", 24)], [20], extra_B, rng_for=lambda i: np.random.default_rng([seed, 32]))
        row["q_iid_B5k"] = q2b
        row["q_bt24_B5k"] = r3b["q"][("stat", 24, 20)]
    return row


def run_chunk(a):
    step, start, stop, out, extra_B = a
    fn = os.path.join(out, f"{step}{'_B5k' if extra_B else ''}_{start:06d}_{stop:06d}.json")
    if os.path.exists(fn):
        return fn, 0.0
    t0 = time.time()
    rows = [one_rep(step, r, extra_B=extra_B) for r in range(start, stop)]
    with open(fn + ".tmp", "w") as f:
        json.dump(rows, f)
    os.replace(fn + ".tmp", fn)
    return fn, time.time() - t0


# ----------------------------------------------------------------- independent implementation (B)

def independent_bootstrap_t(N, S, contrasts, masks, idx, b):
    """Written without using bootstrap_t.py / intervals.py: explicit loops.
    Returns theta (J,), s (J,), theta* (B, J), s* (B, J), stat (B, J)."""
    Nb = [[float(np.mean(N[p][:, t])) for t in range(N.shape[2])] for p in range(N.shape[0])]
    Sb = [[float(np.mean(S[p][:, t])) for t in range(S.shape[2])] for p in range(S.shape[0])]
    T = len(Nb[0])

    def ratio_and_psi(day_index):
        th, ps = [], []
        for j, (_, g, h, _) in enumerate(contrasts):
            mm = [masks[j][d] for d in day_index]
            res = []
            for pol in (g, h):
                n = [Nb[pol][d] for d in day_index]
                s = [Sb[pol][d] for d in day_index]
                num = sum(mi * ni for mi, ni in zip(mm, n))
                den = sum(mi * si for mi, si in zip(mm, s))
                V = num / den
                dbar = den / T
                res.append((V, [mi * (ni - V * si) / dbar for mi, ni, si in zip(mm, n, s)]))
            th.append(res[0][0] - res[1][0])
            ps.append([x - y for x, y in zip(res[0][1], res[1][1])])
        return th, ps

    def lrv(p):
        g = [sum(p[t] * p[t + k] for t in range(T - k)) / T for k in range(b + 1)]
        return g[0] + 2 * sum((1 - k / (b + 1)) * g[k] for k in range(1, b + 1))

    th, ps = ratio_and_psi(list(range(T)))
    s = [math.sqrt(lrv(p) / T) for p in ps]
    Bn = idx.shape[0]
    ths = np.zeros((Bn, len(contrasts)))
    ss = np.zeros_like(ths)
    for r in range(Bn):
        t_r, p_r = ratio_and_psi([int(i) for i in idx[r]])
        ths[r] = t_r
        ss[r] = [math.sqrt(lrv(p) / T) for p in p_r]
    stat = np.abs(ths - np.array(th)) / ss
    return np.array(th), np.array(s), ths, ss, stat


def manual_quantile(x, p):
    """Linear interpolation quantile (numpy's default 'linear' / Hyndman-Fan type 7)."""
    xs = sorted(x)
    h = (len(xs) - 1) * p
    lo = math.floor(h)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (h - lo) * (xs[hi] - xs[lo])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", nargs="+", default=STEPS)
    ap.add_argument("--n", type=int, default=4000)
    ap.add_argument("--chunk", type=int, default=50)
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--extraB", type=int, default=0)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    assert a.procs <= 8
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    for step in a.steps:
        jobs = [(step, s, min(s + a.chunk, a.start + a.n), a.out, a.extraB or None)
                for s in range(a.start, a.start + a.n, a.chunk)]
        with Pool(a.procs) as pool:
            for k, (fn, dt) in enumerate(pool.imap_unordered(run_chunk, jobs)):
                print(f"[{time.time() - t0:8.1f}s] {step} {k + 1}/{len(jobs)} {os.path.basename(fn)} {dt:.1f}s", flush=True)
        print("done", step, a.n, f"{time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()


# ----------------------------------------------------------------- fast path (verified, see tests)

def fast_bt_q(Nbar, Sbar, contrasts, masks, idx, th, b, se_orig, alpha=0.05):
    """Same computation as bootstrap_t.bootstrap_t_stats + the q step of bt_rule, with the
    per-policy gathers cached (12 policies instead of 24 per-contrast gathers). Verified against
    the main implementation in test_audit_s0 (identical up to floating-point summation order)."""
    from bootstrap_t import autocov, hac_var_from_gamma
    B, T = idx.shape
    cacheN, cacheS, cacheM = {}, {}, {}
    stat = np.full((B, len(contrasts)), np.nan)
    for j, (_, g, h, late) in enumerate(contrasts):
        key = bool(late)
        if key not in cacheM:
            cacheM[key] = masks[j][idx]
        m = cacheM[key]
        parts = []
        bad = np.zeros(B, bool)
        for pol in (g, h):
            if pol not in cacheN:
                cacheN[pol] = Nbar[pol][idx]
                cacheS[pol] = Sbar[pol][idx]
            Ns = cacheN[pol] * m
            Ss = cacheS[pol] * m
            sS = Ss.sum(1)
            bad |= sS <= 0
            sSs = np.where(sS > 0, sS, 1.0)
            V = Ns.sum(1) / sSs
            parts.append((V, (Ns - V[:, None] * Ss) / (sSs / T)[:, None]))
        dev = np.abs(parts[0][0] - parts[1][0] - th[j])
        psis = parts[0][1] - parts[1][1]
        se = np.sqrt(np.maximum(hac_var_from_gamma(autocov(psis, max(b, 0)), b), 0.0) / T)
        ok = (~bad) & (se > 0)
        stat[ok, j] = dev[ok] / se[ok]
    act = se_orig > 1e-15
    st = stat[:, act]
    mx = np.nanmax(np.where(np.isnan(st), -np.inf, st), axis=1)
    mx = mx[np.isfinite(mx)]
    nvoid = np.isnan(stat).sum(0)
    return float(np.quantile(mx, 1 - alpha)), bool(np.all(nvoid <= 0.001 * B)), stat


def iid_bt_counts(Nbar, Sbar, contrasts, masks, counts, th, se_orig, alpha=0.05):
    """Method (ii) (L = 1, b = 0) computed exactly from resampling counts: for b = 0 the
    replicate s.e. needs only sum_t psi*_t^2, which expands into count-weighted sums of products.
    Algebraically identical to bt_rule(..., [("stat", 1)], [0]); checked in test_audit_s0."""
    T = Nbar.shape[1]
    c = counts.astype(float)
    stat = np.full((counts.shape[0], len(contrasts)), np.nan)
    for j, (_, g, h, _) in enumerate(contrasts):
        m = masks[j]
        a, b_, e, f = m * Nbar[g], m * Sbar[g], m * Nbar[h], m * Sbar[h]
        cols = np.stack([a, b_, e, f, a * a, a * b_, b_ * b_, e * e, e * f, f * f,
                         a * e, a * f, b_ * e, b_ * f], 1)
        s = c @ cols
        A, C, E, F = s[:, 0], s[:, 1], s[:, 2], s[:, 3]
        aa, ab, bb, ee, ef, ff, ae, af, be, bf = (s[:, k] for k in range(4, 14))
        ok = (C > 0) & (F > 0)
        Cs, Fs = np.where(C > 0, C, 1.0), np.where(F > 0, F, 1.0)
        Vg, Vh = A / Cs, E / Fs
        dg, dh = Cs / T, Fs / T
        ss = ((aa - 2 * Vg * ab + Vg ** 2 * bb) / dg ** 2 + (ee - 2 * Vh * ef + Vh ** 2 * ff) / dh ** 2
              - 2 * (ae - Vh * af - Vg * be + Vg * Vh * bf) / (dg * dh))
        se = np.sqrt(np.maximum(ss, 0.0)) / T
        ok &= se > 0
        stat[ok, j] = np.abs(Vg - Vh - th[j])[ok] / se[ok]
    act = se_orig > 1e-15
    st = stat[:, act]
    mx = np.nanmax(np.where(np.isnan(st), -np.inf, st), axis=1)
    mx = mx[np.isfinite(mx)]
    return float(np.quantile(mx, 1 - alpha)), stat

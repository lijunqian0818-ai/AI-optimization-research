"""Loss-dependent revelation timing: matured-only rate vs the Theorem 1 interval.

Run:  python theory/checks/check_matured_rate.py > theory/checks/results_check_matured_rate.txt

Environment. Every day M entries are selected. A label that is a GAIN (L = 0) is revealed one
day after entry (e.g. a take-profit exit); a LOSS (L = 1) is revealed only at lag d (position
held to the horizon). A3 holds with lag d because X_t is known by day t + d in both cases.
Loss probability: p_t = p_lo for t < T0 and p_hi for t >= T0 (regime shift), or constant.

Compared at each monitoring time T:
  * matured-only rate   K_T / (N_T - P_T)   (denominator = revealed entries only) and a naive
    95% Wald interval that treats revealed entries as an i.i.d. sample;
  * Theorem 1 interval  [ (K_T - B_T)/N_T , (K_T + P_T + B_T)/N_T ]  at delta = 0.05.
Target: r_T^entry = sum_{t<=T} mu_t / N_T.
"""
import math
import numpy as np

C0 = math.pi ** 2 / 6.0
SEEDS = [101, 202, 303]


def b_fun(Q, d, delta):
    Q = np.asarray(Q, dtype=np.float64)
    out = np.zeros_like(Q)
    pos = Q >= 1
    _, e = np.frexp(Q[pos])
    k = (e - 1).astype(np.float64)
    out[pos] = np.sqrt(2.0 ** k * np.log(2 * d * C0 * (k + 1) ** 2 / delta))
    return out


def b_star(Q, d, delta):
    """Sharpened radius b*(q) = min_k (1/2) sqrt(2^k L_k) (1 + q / 2^(k+1)), b*(0) = 0,
    L_k = log(2 d c0 (k+1)^2 / delta). Valid on the same event as b (Theorem 1(b))."""
    Q = np.asarray(Q, dtype=np.float64)
    out = np.full(Q.shape, np.inf)
    # The minimum over k >= 0 is attained at some k <= floor(log2 q) + 2: for 2^k >= 4q the k-th
    # term is >= (1/2) sqrt(4 q L_k) >= sqrt(q L_k(q)) >= the term at k(q). So this range is exact.
    kmax = int(math.floor(math.log2(max(float(Q.max()), 1.0)))) + 2
    for k in range(kmax + 1):
        Lk = math.log(2 * d * C0 * (k + 1) ** 2 / delta)
        np.minimum(out, 0.5 * math.sqrt(2.0 ** k * Lk) * (1 + Q / 2.0 ** (k + 1)), out=out)
    out[Q < 1] = 0.0
    return out


def run(R, T, d, M, p_path, daycorr, rng, delta=0.05):
    n = np.full((R, T), float(M))
    p = np.broadcast_to(p_path[None, :], (R, T))
    if daycorr:
        X = M * (rng.random((R, T)) < p).astype(np.float64)
    else:
        X = rng.binomial(M, p).astype(np.float64)
    mu = M * p
    G = n - X                                   # gains per day
    cumX, cumG, N = np.cumsum(X, 1), np.cumsum(G, 1), np.cumsum(n, 1)
    S_mu = np.cumsum(mu, 1)
    K = np.zeros((R, T)); K[:, d:] = cumX[:, :-d]            # losses revealed at lag d
    Grev = np.zeros((R, T)); Grev[:, 1:] = cumG[:, :-1]      # gains revealed at lag 1
    Nrev = K + Grev
    P = N - Nrev
    B = np.zeros((R, T))
    Bs = np.zeros((R, T))
    for j in range(d):
        mask = (np.arange(T) % d == j).astype(np.float64)
        B += b_fun(np.cumsum(n ** 2 * mask, 1), d, delta)
        Bs += b_star(np.cumsum(n ** 2 * mask, 1), d, delta)
    r = S_mu / N
    with np.errstate(divide="ignore", invalid="ignore"):
        mat = np.where(Nrev > 0, K / Nrev, np.nan)
        se = np.sqrt(mat * (1 - mat) / Nrev)
    wald_lo, wald_hi = mat - 1.96 * se, mat + 1.96 * se
    wald_cover = (r >= wald_lo) & (r <= wald_hi)            # False where undefined
    lo = np.maximum(0, (K - B) / N)
    hi = np.minimum(1, (K + P + B) / N)
    thm_viol = (r < lo - 1e-12) | (r > hi + 1e-12)
    lo_s = np.maximum(0, (K - Bs) / N)
    hi_s = np.minimum(1, (K + P + Bs) / N)
    thm_viol_s = (r < lo_s - 1e-12) | (r > hi_s + 1e-12)
    return dict(r=r, mat=mat, wald_cover=wald_cover, thm_viol=thm_viol, lo=lo, hi=hi, lo_s=lo_s, hi_s=hi_s,
                thm_viol_s=thm_viol_s,
                det_lo=K / N, det_hi=(K + P) / N, realised=cumX / N)


def main():
    R, T, d, M = 2000, 800, 10, 10
    grid = [20, 50, 100, 200, 400, 410, 420, 450, 500, 800]
    print(f"R={R} paths/seed, T={T}, d={d}, M={M}, seeds={SEEDS}; gains revealed at lag 1, losses at lag {d}")
    scen = {
        "constant p=0.5": np.full(T, 0.5),
        "shift 0.3->0.8 at t=400": np.where(np.arange(T) < 400, 0.3, 0.8),
    }
    for name, p_path in scen.items():
        for daycorr in (False, True):
            print()
            print(f"--- scenario: {name}; labels {'identical within a day' if daycorr else 'independent'} ---")
            print("T     r_T^entry  matured-only(mean+-sd over seeds)  bias      naive Wald95 cover  "
                  "Thm1(a) [lo, hi] (mean)   Thm1(b) [lo, hi] (mean)   realised in [K/N,(K+P)/N]")
            outs = []
            for seed in SEEDS:
                rng = np.random.default_rng(seed)
                outs.append(run(R, T, d, M, p_path, daycorr, rng))
            for Tm in grid:
                i = Tm - 1
                r = np.mean([o["r"][:, i].mean() for o in outs])
                mats = np.array([np.nanmean(o["mat"][:, i]) for o in outs])
                cov = np.mean([o["wald_cover"][:, i].mean() for o in outs])
                lo = np.mean([o["lo"][:, i].mean() for o in outs])
                hi = np.mean([o["hi"][:, i].mean() for o in outs])
                lo_s = np.mean([o["lo_s"][:, i].mean() for o in outs])
                hi_s = np.mean([o["hi_s"][:, i].mean() for o in outs])
                det = np.mean([((o["realised"][:, i] >= o["det_lo"][:, i] - 1e-12) &
                                (o["realised"][:, i] <= o["det_hi"][:, i] + 1e-12)).mean() for o in outs])
                print(f"{Tm:<5d} {r:<10.4f} {mats.mean():.4f}+-{mats.std():.4f}                     "
                      f"{mats.mean() - r:+.4f}   {cov:<19.4f} [{lo:.4f}, {hi:.4f}]          [{lo_s:.4f}, {hi_s:.4f}]          {det:.4f}")
            any_wald_fail = [1 - o["wald_cover"][:, d:].all(axis=1).mean() for o in outs]
            any_thm_fail = [o["thm_viol"].any(axis=1).mean() for o in outs]
            print("fraction of paths where the naive Wald interval misses r_T at SOME T >= d+1, per seed:",
                  [round(float(v), 4) for v in any_wald_fail])
            print("fraction of paths where the Theorem 1(a) interval misses r_T at SOME T, per seed:     ",
                  [round(float(v), 4) for v in any_thm_fail])
            print("fraction of paths where the Theorem 1(b) interval misses r_T at SOME T, per seed:     ",
                  [round(float(v), 4) for v in [o["thm_viol_s"].any(axis=1).mean() for o in outs]])


if __name__ == "__main__":
    main()

"""Numerical sanity check for Theorem 1 (delayed monitoring) and Proposition 2.

Run:  python theory/checks/check_thm1_coverage.py > theory/checks/results_check_thm1_coverage.txt

What is checked (numpy only, fixed seeds):
  (1) Time-uniform coverage of the Theorem 1 interval for r_T^entry: for each simulated path we
      test whether ANY monitoring time T violates the interval ("interval violation"), and
      whether ANY (lane, T) violates the lane deviation bound |sum (mu - X)| <= b(Q)
      ("lane violation"; this is the event whose probability the proof bounds by delta).
  (2) Power of the check: the same lane test with b shrunk by a factor s < 1. If the test never
      fails even for small s, the check would be uninformative.
  (3) Width: 2 B_T / N_T at the final T against sqrt(d M / N_T) and against the Corollary 1.1 bound.
  (4) Effective sample size: sd of (sum X - sum mu) / N for independent labels vs the
      perfectly correlated d-day block construction of Proposition 2.
  (5) Proposition 2 constants: exact total variation between Binomial(B, 1/2 - h) and
      Binomial(B, 1/2 + h), h = c / sqrt(B), c = sqrt(3) (1 - 2 delta) / 8, against the bound
      (1 - 2 delta) / 2 used in the proof.
  (6) Hoeffding's lemma on a grid, and the per-epoch optimisation constant.
"""
import math
import numpy as np

C0 = math.pi ** 2 / 6.0
SEEDS = [11, 22, 33]


def b_fun(Q, d, delta):
    """b(q) = sqrt(2^k log(2 d c0 (k+1)^2 / delta)), k = floor(log2 q); b(0) = 0."""
    Q = np.asarray(Q, dtype=np.float64)
    out = np.zeros_like(Q)
    pos = Q >= 1
    _, e = np.frexp(Q[pos])          # Q = m * 2^e, m in [0.5, 1)  =>  floor(log2 Q) = e - 1
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


def simulate(env, R, T, d, M, rng, p=0.5):
    """Return n, X, mu as (R, T) arrays. Day index t = 0..T-1; block of day t is t // d.

    Information structure (all environments): F_t contains everything generated on days
    < t that is revealed with lag d (X_s for s <= t - d) and the selector's randomisation.
    n_t is a function of X_{t-d}, n_{t-d} and fresh randomisation, hence F_t-measurable.
    """
    n = np.zeros((R, T))
    X = np.zeros((R, T))
    mu = np.zeros((R, T))
    adaptive = env in ("iid", "daycorr", "block_adapt")
    Zprev = np.full(R, np.nan)
    Zcur = None
    for t in range(T):
        if adaptive and t >= d:
            bad = X[:, t - d] > n[:, t - d] / 2.0
            nt = np.where(bad, rng.integers(0, M // 2 + 1, size=R), M).astype(np.float64)
        else:
            nt = np.full(R, float(M))
        if env == "iid":            # labels independent across stocks and days
            xt = rng.binomial(nt.astype(np.int64), p).astype(np.float64)
            mt = nt * p
        elif env == "daycorr":      # all labels of a day identical, independent across days
            xt = nt * (rng.random(R) < p)
            mt = nt * p
        elif env in ("block", "block_adapt"):
            if t % d == 0:          # new block: draw Z_b
                if Zcur is not None:
                    Zprev = Zcur
                if env == "block":
                    pb = np.full(R, p)
                else:               # p_b depends on the previous block's outcome (in F_t)
                    pb = np.where(np.isnan(Zprev), 0.5, 0.3 + 0.4 * np.nan_to_num(Zprev))
                Zcur = (rng.random(R) < pb).astype(np.float64)
                pcur = pb
            xt = nt * Zcur
            mt = nt * pcur
        else:
            raise ValueError(env)
        n[:, t], X[:, t], mu[:, t] = nt, xt, mt
    return n, X, mu


def evaluate(n, X, mu, d, M, delta, scales=(1.0, 0.5, 0.35, 0.25)):
    R, T = n.shape
    D = mu - X
    lane_ratio_max = np.zeros(R)              # max over (j, T) of |cum D_j| / b(Q_j)
    lane_ratio_max_star = np.zeros(R)         # same with the sharpened radius b*
    B = np.zeros((R, T))
    Bs = np.zeros((R, T))
    for j in range(d):
        mask = (np.arange(T) % d == j).astype(np.float64)
        cumD = np.cumsum(D * mask, axis=1)
        Q = np.cumsum(n ** 2 * mask, axis=1)
        b = b_fun(Q, d, delta)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(b > 0, np.abs(cumD) / b, 0.0)
        # where b == 0 we must have cumD == 0 exactly
        assert np.all(np.abs(cumD[b == 0]) == 0)
        lane_ratio_max = np.maximum(lane_ratio_max, ratio.max(axis=1))
        B += b
        bs = b_star(Q, d, delta)
        assert np.all(bs <= b + 1e-9), "b* must not exceed b"
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio_s = np.where(bs > 0, np.abs(cumD) / bs, 0.0)
        lane_ratio_max_star = np.maximum(lane_ratio_max_star, ratio_s.max(axis=1))
        Bs += bs
    N = np.cumsum(n, axis=1)
    S_mu = np.cumsum(mu, axis=1)
    cumX = np.cumsum(X, axis=1)
    cumn = N
    # revelation with lag exactly d: at monitoring time T (0-based index T), entries of days
    # t <= T - d are revealed.
    K = np.zeros((R, T))
    K[:, d:] = cumX[:, :-d]
    Nrev = np.zeros((R, T))
    Nrev[:, d:] = cumn[:, :-d]
    P = N - Nrev
    ok = N > 0
    lo = np.maximum(0.0, K - B)
    hi = np.minimum(N, K + P + B)
    tol = 1e-9
    viol = ok & ((S_mu < lo - tol) | (S_mu > hi + tol))
    interval_viol = viol.any(axis=1)
    lo_s = np.maximum(0.0, K - Bs)
    hi_s = np.minimum(N, K + P + Bs)
    viol_s = ok & ((S_mu < lo_s - tol) | (S_mu > hi_s + tol))
    res = {
        "interval_viol_rate_star": viol_s.any(axis=1).mean(),
        "lane_viol_rate_star": (lane_ratio_max_star > 1.0).mean(),
        "lane_ratio_star_max": lane_ratio_max_star.max(),
        "interval_viol_rate": interval_viol.mean(),
        "lane_viol_rate": {s: (lane_ratio_max > s).mean() for s in scales},
        "lane_ratio_max_mean": lane_ratio_max.mean(),
        "lane_ratio_max_q99": np.quantile(lane_ratio_max, 0.99),
        "lane_ratio_max_max": lane_ratio_max.max(),
    }
    NT = N[:, -1]
    good = NT > 0
    res["halfwidth_B_over_N"] = (B[:, -1][good] / NT[good]).mean()
    res["halfwidth_Bstar_over_N"] = (Bs[:, -1][good] / NT[good]).mean()
    # sawtooth: largest one-day relative increase of B_T / N_T and B*_T / N_T after T/4
    t0 = T // 4
    with np.errstate(divide="ignore", invalid="ignore"):
        res["max_jump_B"] = np.nanmax((B[:, t0 + 1:] / N[:, t0 + 1:]) / (B[:, t0:-1] / N[:, t0:-1]))
        res["max_jump_Bs"] = np.nanmax((Bs[:, t0 + 1:] / N[:, t0 + 1:]) / (Bs[:, t0:-1] / N[:, t0:-1]))
    res["sqrt_dM_over_N"] = np.sqrt(d * M / NT[good]).mean()
    ell = np.log(2 * d * C0 * (1 + np.log2(M * NT[good])) ** 2 / delta)
    res["corollary_bound"] = np.sqrt(d * M * ell / NT[good]).mean()
    res["pending_over_N"] = (P[:, -1][good] / NT[good]).mean()
    res["sd_err_times_sqrtN"] = np.std((cumX[:, -1] - S_mu[:, -1])[good] / NT[good]) * np.sqrt(NT[good].mean())
    res["N_mean"] = NT[good].mean()
    return res


def binom_tv(B, p0, p1):
    ks = np.arange(B + 1)
    lg = np.array([math.lgamma(B + 1) - math.lgamma(k + 1) - math.lgamma(B - k + 1) for k in ks])
    f0 = np.exp(lg + ks * math.log(p0) + (B - ks) * math.log(1 - p0))
    f1 = np.exp(lg + ks * math.log(p1) + (B - ks) * math.log(1 - p1))
    return 0.5 * np.abs(f0 - f1).sum()


def main():
    delta, M, T, R = 0.1, 10, 2000, 500
    print("=== Theorem 1 coverage check ===")
    print(f"delta={delta}, M={M}, T={T}, paths per seed={R}, seeds={SEEDS}")
    print("interval_viol = fraction of paths on which SOME T violates the Theorem 1 interval")
    print("lane_viol(s)  = fraction of paths on which SOME (lane, T) has |sum(mu-X)| > s*b(Q)")
    print("                (s=1 is the event bounded by delta in the proof; s<1 tests power)")
    print()
    hdr = ("d  env          seed  interval_viol  lane_viol(1) lane_viol(.5) lane_viol(.35) "
           "lane_viol(.25)  max|dev|/b: mean  q99   max   | with b*: interval_viol lane_viol max|dev|/b*")
    print(hdr)
    summary = {}
    for d in (1, 5, 20):
        for env in ("iid", "daycorr", "block", "block_adapt"):
            for seed in SEEDS:
                rng = np.random.default_rng(seed * 1000 + d)
                n, X, mu = simulate(env, R, T, d, M, rng)
                r = evaluate(n, X, mu, d, M, delta)
                lv = r["lane_viol_rate"]
                print(f"{d:<2d} {env:<12s} {seed:<5d} {r['interval_viol_rate']:<14.4f} "
                      f"{lv[1.0]:<12.4f} {lv[0.5]:<13.4f} {lv[0.35]:<14.4f} {lv[0.25]:<15.4f} "
                      f"{r['lane_ratio_max_mean']:.3f}            {r['lane_ratio_max_q99']:.3f} "
                      f"{r['lane_ratio_max_max']:.3f} |          {r['interval_viol_rate_star']:.4f}        "
                      f"{r['lane_viol_rate_star']:.4f}    {r['lane_ratio_star_max']:.3f}")
                summary.setdefault((d, env), []).append(r)
    print()
    print("=== Width at final T (mean over paths, then mean +- sd over seeds) ===")
    print("B/N = half-width contribution of Theorem 1; total width = (P + 2B)/N")
    print("max step ratio = largest one-day relative increase of radius/N after T/4 (sawtooth)")
    print("d  env          N_T      B_T/N_T            sqrt(dM/N_T)  ratio  Cor1.1 bound  P_T/N_T  "
          "B*_T/N_T  B*/B   max step ratio B, B*")
    for (d, env), rs in summary.items():
        hw = np.array([r["halfwidth_B_over_N"] for r in rs])
        ref = np.mean([r["sqrt_dM_over_N"] for r in rs])
        cb = np.mean([r["corollary_bound"] for r in rs])
        pn = np.mean([r["pending_over_N"] for r in rs])
        Nm = np.mean([r["N_mean"] for r in rs])
        print(f"{d:<2d} {env:<12s} {Nm:<8.0f} {hw.mean():.5f}+-{hw.std():.5f}  {ref:.5f}       "
              f"{hw.mean() / ref:.3f}  {cb:.5f}       {pn:.5f}  "
              f"{np.mean([r['halfwidth_Bstar_over_N'] for r in rs]):.5f}   "
              f"{np.mean([r['halfwidth_Bstar_over_N'] for r in rs]) / hw.mean():.3f}  "
              f"{max(r['max_jump_B'] for r in rs):.3f}, {max(r['max_jump_Bs'] for r in rs):.3f}")
    print()
    print("=== Effective sample size (n_t = M fixed, p = 1/2) ===")
    print("sd of (sum X - sum mu)/N times sqrt(N); theory: iid 0.5 ; block 0.5*sqrt(M d)")
    print("d  env      seed  sd*sqrt(N)  theory   implied N_eff = N * (0.5/(sd*sqrt(N)))^2   N/(M d)")
    Tess, Ress = 2000, 4000
    for d in (1, 5, 20):
        for env in ("iid_fixed", "block"):
            for seed in SEEDS:
                rng = np.random.default_rng(seed * 77 + d)
                N = M * Tess
                if env == "iid_fixed":
                    S = rng.binomial(N, 0.5, size=Ress).astype(np.float64)
                    theory = 0.5
                else:
                    Bk = Tess // d
                    S = M * d * rng.binomial(Bk, 0.5, size=Ress).astype(np.float64)
                    theory = 0.5 * math.sqrt(M * d)
                sd = np.std((S - 0.5 * N) / N) * math.sqrt(N)
                neff = N * (0.5 / sd) ** 2
                print(f"{d:<2d} {env:<9s} {seed:<5d} {sd:<11.4f} {theory:<8.4f} {neff:<12.1f} "
                      f"{'' if env == 'iid_fixed' else N / (M * d)}")
    print()
    print("=== Proposition 2: exact TV between Binomial(B,1/2-h) and Binomial(B,1/2+h) ===")
    print("h = c/sqrt(B), c = sqrt(3)(1-2 delta)/8 ; proof needs TV <= (1-2 delta)/2")
    print("delta  B      h         exact TV   Pinsker bound sqrt(KL/2)  proof bound 4c/sqrt(3)  ok")
    allok = True
    for dl in (0.05, 0.1, 0.25, 0.4):
        c = math.sqrt(3) * (1 - 2 * dl) / 8
        for Bk in (1, 2, 5, 10, 50, 200, 1000):
            h = c / math.sqrt(Bk)
            p0, p1 = 0.5 - h, 0.5 + h
            tv = binom_tv(Bk, p0, p1)
            kl = Bk * (p0 * math.log(p0 / p1) + (1 - p0) * math.log((1 - p0) / (1 - p1)))
            pin = math.sqrt(kl / 2)
            pb = 4 * c / math.sqrt(3)
            ok = (tv <= pin + 1e-12) and (pin <= pb + 1e-12)
            allok &= ok
            print(f"{dl:<6.2f} {Bk:<6d} {h:<9.5f} {tv:<10.5f} {pin:<25.5f} {pb:<23.5f} {ok}")
    print("all TV checks ok:", allok)
    print()
    print("=== Theorem 1 width vs Proposition 2 lower bound (block env, n_t = M) ===")
    print("lower bound on width (holds w.p. >= (1-2 delta)/2): (sqrt(3)/4)(1-2 delta) sqrt(M d/N)")
    for d in (1, 5, 20):
        rs = summary[(d, "block")]
        w = 2 * np.mean([r["halfwidth_B_over_N"] for r in rs])
        ws = 2 * np.mean([r["halfwidth_Bstar_over_N"] for r in rs])
        N = np.mean([r["N_mean"] for r in rs])
        lb = math.sqrt(3) / 4 * (1 - 2 * delta) * math.sqrt(M * d / N)
        print(f"d={d:<3d} N={N:.0f}  Thm1 width 2B/N = {w:.5f}  2B*/N = {ws:.5f}  "
              f"lower bound = {lb:.5f}  ratios = {w / lb:.2f}, {ws / lb:.2f}")
    print()
    print("=== Hoeffding lemma grid check: log(1-p+p e^h) - p h <= h^2/8 ===")
    ps = np.linspace(0, 1, 201)[:, None]
    hs = np.linspace(-30, 30, 2401)[None, :]
    psi = np.log1p(ps * np.expm1(hs)) - ps * hs
    print("max over grid of psi - h^2/8 =", float((psi - hs ** 2 / 8).max()), "(must be <= 0 up to rounding)")
    print()
    print("=== Per-epoch constant: min_lam [log(1/a)/lam + lam 2^(k+1)/8] vs sqrt(2^k log(1/a)) ===")
    worst = 0.0
    for k in range(0, 25):
        for a in (1e-1, 1e-3, 1e-6):
            L = math.log(1 / a)
            lam = math.sqrt(8 * L / 2 ** (k + 1))
            val = L / lam + lam * 2 ** (k + 1) / 8
            worst = max(worst, abs(val - math.sqrt(2 ** k * L)) / val)
            lams = lam * np.exp(np.linspace(-2, 2, 2001))
            grid = (L / lams + lams * 2 ** (k + 1) / 8).min()
            worst = max(worst, abs(grid - val) / val)
    print("max relative discrepancy:", worst)


if __name__ == "__main__":
    main()

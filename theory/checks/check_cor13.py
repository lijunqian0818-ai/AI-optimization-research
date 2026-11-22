"""Numerical sanity check for Corollary 1.3 (deadline labels for the liquidation target).

Run:  python theory/checks/check_cor13.py > theory/checks/results_check_cor13.txt

Part A (random, 3 seeds). Environment with positions that are still unsold at their deadline.
  * Days t = 1..T. Holding horizon H = 1, deadline D = 5, lag of the deadline labels d_D = D + 1 = 6.
  * A two-state regime g_t (Markov chain, known at entry: part of F_t).
  * A "bad day" shock s_t ~ Bernoulli(q[g_t]), NOT known at entry, shared by all entries of day t.
  * Given s_t, each entry of day t:
        is unsold at its deadline ("stuck") with probability u[s_t];
        if sold by the deadline: sold after xi in {0..D-H} extra days, at a net loss w.p. a[s_t];
        if stuck: its liquidation label is 1 w.p. c[s_t]  (this includes "never liquidated",
        for which the completion convention L^liq := 1 applies).
    dependence = "shared":    entries of a day are conditionally independent given s_t;
    dependence = "identical": all entries of a day share the same draws (identical labels).
  * Labels:  L^lo = 1{sold by deadline at a loss},  L^hi = L^lo + 1{stuck},
             L^liq = L^lo if sold by the deadline, else the stuck draw.   L^lo <= L^liq <= L^hi.
  * Paired revelation (assumption A4' of the corollary): the pair (L^lo, L^hi) of an entry is
    revealed at decision point t + H + xi + 1 if sold by the deadline (so EARLY, and the timing
    depends on the outcome), and at t + D + 1 if stuck.  J_T = entries whose pair is revealed by T.
  * n_t is adaptive: it depends on the pairs revealed during the last 20 days (F_t-measurable),
    and on fresh randomisation.
  * Entry-time conditional means are known in closed form:
        mu^liq_t = n_t * sum_s P(s | g_t) [ (1 - u_s) a_s + u_s c_s ],   similarly mu^lo, mu^hi.
  Checked: (1) time-uniform coverage of r^liq_T by the Corollary 1.3 interval, with the upper and
  lower failures counted separately (each is bounded by delta/2 in the proof);
  (2) the pathwise facts X^lo <= X^liq <= X^hi and width >= (K^hi - K^lo)/N_T;
  (3) power: the same interval with the radius scaled by 0.25 and 0, and the "naive" interval
      that treats stuck positions as non-losses (uses K^lo on both sides).

Part B (deterministic). One entry per day; only the FIRST entry misses its deadline; all others
  are sold by their deadline without loss; pairs revealed at lag d. The deadline-unsold share
  (K^hi - K^lo)/N_T is 1/T -> 0 and the whole interval width -> 0.

Part C (deterministic). One entry per day; every 5th entry misses its deadline (rho = 0.2).
  The width stays >= 0.2 for all T (conditional persistence statement).

Part D (deterministic enumeration; added in review round 3, item X7). Parts A-C simulate complete
  records (certification V = S). Part D enumerates every combination of
      S (sold by the deadline), record complete at the finalisation day, sale at a loss,
      value of L^liq if not sold by the deadline
  and compares two definitions of the bracket labels when the record is missing:
      certified labels (round 3):  V = S * complete,  L^lo = V * loss,  L^hi = 1 - V * (1 - loss);
      "missing => loss" fallback:  L^lo = L^hi = 1 whenever the record is missing.
  Required: L^lo <= L^liq <= L^hi in every state for the certified labels, and L^hi - L^lo = 1 - V.
  The fallback is expected to violate the ordering (reviewer's example: sold at a profit, record
  missing: L^lo = 1 > L^liq = 0).
"""
import math
import numpy as np

C0 = math.pi ** 2 / 6.0
SEEDS = [101, 202, 303]


def b_star(Q, d, delta):
    """b*(q) = min_k (1/2) sqrt(2^k L_k)(1 + q/2^(k+1)) for q >= 1; b*(0) = 0."""
    Q = np.asarray(Q, dtype=np.float64)
    out = np.full(Q.shape, np.inf)
    kmax = int(math.floor(math.log2(max(float(Q.max()), 1.0)))) + 2
    for k in range(kmax + 1):
        Lk = math.log(2 * d * C0 * (k + 1) ** 2 / delta)
        np.minimum(out, 0.5 * math.sqrt(2.0 ** k * Lk) * (1 + Q / 2.0 ** (k + 1)), out=out)
    out[Q < 1] = 0.0
    return out


def radius_path(n, d, delta):
    """n: (R, T) entries per day (day index t = 1..T in column t-1). Returns B*_T, shape (R, T)."""
    R, T = n.shape
    days = np.arange(1, T + 1)
    B = np.zeros((R, T))
    for j in range(d):
        Q = np.cumsum(np.where(days % d == j, n ** 2, 0.0), axis=1)
        B += b_star(Q, d, delta)
    return B


def simulate(R, T, M, H, D, dep, pars, rng):
    q, u, a, c = pars["q"], pars["u"], pars["a"], pars["c"]
    d = D + 1
    W = T + D + 2
    n = np.zeros((R, T))
    mu = {k: np.zeros((R, T)) for k in ("lo", "liq", "hi")}
    X = {k: np.zeros((R, T)) for k in ("lo", "liq", "hi")}
    rev_cnt = np.zeros((R, W))
    rev_lo = np.zeros((R, W))
    rev_hi = np.zeros((R, W))
    g = (rng.random(R) < 0.5).astype(int)
    idx = np.arange(M)[None, :]
    # per-regime conditional probabilities (per entry) given F_t
    p = {}
    for gg in (0, 1):
        ps = np.array([1 - q[gg], q[gg]])
        p[gg] = dict(
            lo=float(ps @ ((1 - u) * a)),
            liq=float(ps @ ((1 - u) * a + u * c)),
            hi=float(ps @ ((1 - u) * a + u)),
        )
    for t in range(T):
        if t > 0:
            g = np.where(rng.random(R) < 0.95, g, 1 - g)
        # adaptive number of entries: uses only pairs revealed at decision points <= t
        lo_w = max(0, t - 19)
        cnt = rev_cnt[:, lo_w:t + 1].sum(1)
        frac = np.divide(rev_hi[:, lo_w:t + 1].sum(1), cnt, out=np.zeros(R), where=cnt > 0)
        nt = np.where((cnt > 0) & (frac > 0.5), 4, M)
        nt = np.where(rng.random(R) < 0.1, 0, nt)             # some no-trade days
        n[:, t] = nt
        active = idx < nt[:, None]
        s = (rng.random(R) < np.where(g == 1, q[1], q[0])).astype(int)
        shape = (R, M) if dep == "shared" else (R, 1)
        us = u[s][:, None]
        stuck = np.broadcast_to(rng.random(shape) < us, (R, M))
        xi = np.broadcast_to(rng.integers(0, D - H + 1, size=shape), (R, M))
        loss_sold = np.broadcast_to(rng.random(shape) < a[s][:, None], (R, M))
        loss_stuck = np.broadcast_to(rng.random(shape) < c[s][:, None], (R, M))
        Llo = active & ~stuck & loss_sold
        U = active & stuck
        Lhi = Llo | U
        Lliq = active & np.where(stuck, loss_stuck, loss_sold)
        X["lo"][:, t], X["liq"][:, t], X["hi"][:, t] = Llo.sum(1), Lliq.sum(1), Lhi.sum(1)
        for k in ("lo", "liq", "hi"):
            mu[k][:, t] = nt * np.where(g == 1, p[1][k], p[0][k])
        off = np.where(stuck, D + 1, H + xi + 1)                # reveal offset in days
        for o in range(H + 1, D + 2):
            m = active & (off == o)
            rev_cnt[:, t + o] += m.sum(1)
            rev_lo[:, t + o] += (m & Llo).sum(1)
            rev_hi[:, t + o] += (m & Lhi).sum(1)
    N = np.cumsum(n, axis=1)
    J = np.cumsum(rev_cnt[:, :T], axis=1)       # pairs revealed at decision points <= T
    Klo = np.cumsum(rev_lo[:, :T], axis=1)
    Khi = np.cumsum(rev_hi[:, :T], axis=1)
    return dict(n=n, N=N, P=N - J, Klo=Klo, Khi=Khi, mu=mu, X=X, d=d)


def part_a():
    delta, M, H, D, T, R = 0.1, 10, 1, 5, 1500, 400
    settings = {
        "moderate": dict(q=np.array([0.2, 0.6]), u=np.array([0.02, 0.25]),
                         a=np.array([0.35, 0.70]), c=np.array([0.60, 0.90])),
        "heavy": dict(q=np.array([0.2, 0.6]), u=np.array([0.30, 0.60]),
                      a=np.array([0.35, 0.70]), c=np.array([0.60, 0.90])),
    }
    print("=== Part A: coverage of r^liq by the Corollary 1.3 interval ===")
    print(f"delta={delta}, M={M}, H={H}, D={D}, d_D={D + 1}, T={T}, paths per seed={R}, seeds={SEEDS}")
    print("miss = fraction of paths on which the bound fails at SOME T with N_T > 0")
    hdr = ("stuck     dep        seed  miss_any  miss_up  miss_low | x0.25: any  x0: any | naive(K^lo both sides): any | "
           "ordering viol  min(width-(Khi-Klo)/N) | at T: N_T   r_lo   r_liq  r_hi   lower  upper  (Khi-Klo)/N  P/N    B*/N")
    print(hdr)
    tot = dict(paths=0, any=0, up=0, low=0)
    for name, pars in settings.items():
        for dep in ("shared", "identical"):
            for seed in SEEDS:
                rng = np.random.default_rng(seed)
                o = simulate(R, T, M, H, D, dep, pars, rng)
                N, P, Klo, Khi = o["N"], o["P"], o["Klo"], o["Khi"]
                B = radius_path(o["n"], o["d"], delta)
                ok = N > 0
                Ns = np.where(ok, N, 1.0)
                r = {k: np.cumsum(o["mu"][k], axis=1) / Ns for k in ("lo", "liq", "hi")}

                def ends(scale, K_up=Khi):
                    lo = np.maximum(0.0, (Klo - scale * B) / Ns)
                    hi = np.minimum(1.0, (K_up + P + scale * B) / Ns)
                    return lo, hi

                tol = 1e-12
                lo, hi = ends(1.0)
                up_fail = ((r["liq"] > hi + tol) & ok).any(1)
                low_fail = ((r["liq"] < lo - tol) & ok).any(1)
                any_fail = up_fail | low_fail
                pw = []
                for sc in (0.25, 0.0):
                    l2, h2 = ends(sc)
                    pw.append((((r["liq"] > h2 + tol) | (r["liq"] < l2 - tol)) & ok).any(1).mean())
                l3, h3 = ends(1.0, K_up=Klo)
                naive = (((r["liq"] > h3 + tol) | (r["liq"] < l3 - tol)) & ok).any(1).mean()
                order_viol = int(((o["X"]["lo"] > o["X"]["liq"]) | (o["X"]["liq"] > o["X"]["hi"])).sum())
                slack = np.where(ok, (hi - lo) - (Khi - Klo) / Ns, np.inf).min()
                tot["paths"] += R
                tot["any"] += int(any_fail.sum())
                tot["up"] += int(up_fail.sum())
                tot["low"] += int(low_fail.sum())
                e = -1
                print(f"{name:<9s} {dep:<10s} {seed:<5d} {any_fail.mean():.4f}    {up_fail.mean():.4f}   {low_fail.mean():.4f}   |"
                      f"        {pw[0]:.4f}   {pw[1]:.4f} |                      {naive:.4f} | "
                      f"{order_viol:<13d}  {slack:+.2e}              |       {N[:, e].mean():7.0f} "
                      f"{r['lo'][:, e].mean():.4f} {r['liq'][:, e].mean():.4f} {r['hi'][:, e].mean():.4f} "
                      f"{lo[:, e].mean():.4f} {hi[:, e].mean():.4f} {((Khi - Klo) / Ns)[:, e].mean():.4f}       "
                      f"{(P / Ns)[:, e].mean():.4f} {(B / Ns)[:, e].mean():.4f}")
    print(f"TOTAL over {tot['paths']} paths: any-miss {tot['any']}, upper-miss {tot['up']}, lower-miss {tot['low']} "
          f"(allowed by the corollary: {delta:.0%} of paths per cell; {delta / 2:.0%} per side)")


def deterministic(T_list, stuck_fn, d, delta, title):
    print()
    print(title)
    print(f"one entry per day, pairs revealed at lag d={d}, delta={delta}; no sold entry is a loss (K^lo = 0)")
    print("T         N_T       K^hi-K^lo  (K^hi-K^lo)/N_T  P_T/N_T    B*_T/N_T   lower  upper     width")
    for T in T_list:
        days = np.arange(1, T + 1)
        revealed = days + d <= T
        Khi = int((stuck_fn(days) & revealed).sum())
        Klo = 0
        P = int((~revealed).sum())
        N = T
        Q = np.array([float(((days % d) == j).sum()) for j in range(d)])
        B = float(b_star(Q, d, delta).sum())
        lo = max(0.0, (Klo - B) / N)
        hi = min(1.0, (Khi + P + B) / N)
        print(f"{T:<9d} {N:<9d} {Khi - Klo:<10d} {(Khi - Klo) / N:.6f}         {P / N:.6f}   {B / N:.6f}   "
              f"{lo:.3f}  {hi:.6f}  {hi - lo:.6f}")


def part_d():
    print()
    print("=== Part D: pointwise ordering of the bracket labels when records can be missing (round 3, X7) ===")
    print("S  complete  sale_loss  Lliq_if_unsold | L^liq | certified: V lo hi  ok        | 'missing => loss' fallback: lo hi  ok")
    bad_cert = bad_fb = bad_gap = n_states = 0
    for S in (0, 1):
        for complete in (0, 1):
            for loss in (0, 1):
                for stuck_val in (0, 1):
                    n_states += 1
                    Lliq = loss if S == 1 else stuck_val
                    V = S * complete
                    lo_c, hi_c = V * loss, 1 - V * (1 - loss)
                    if complete == 1:
                        lo_f, hi_f = S * loss, S * loss + (1 - S)
                    else:
                        lo_f, hi_f = 1, 1
                    ok_c = lo_c <= Lliq <= hi_c
                    ok_f = lo_f <= Lliq <= hi_f
                    bad_cert += (not ok_c)
                    bad_fb += (not ok_f)
                    bad_gap += (hi_c - lo_c != 1 - V)
                    print(f"{S}  {complete}         {loss}          {stuck_val}              |   {Lliq}   |"
                          f"            {V}  {lo_c}  {hi_c}  {'ok       ' if ok_c else 'VIOLATION'} |"
                          f"                             {lo_f}  {hi_f}  {'ok' if ok_f else 'VIOLATION'}")
    print(f"states: {n_states}; ordering violations: certified labels {bad_cert}, fallback labels {bad_fb}; "
          f"states with L^hi - L^lo != 1 - V (certified): {bad_gap}")
    return bad_cert == 0 and bad_gap == 0


def main():
    part_a()
    Ts = [100, 1000, 10000, 100000, 1000000]
    deterministic(Ts, lambda days: days == 1, 6, 0.1,
                  "=== Part B: only the first entry misses its deadline (finitely many misses) ===")
    deterministic(Ts, lambda days: days % 5 == 0, 6, 0.1,
                  "=== Part C: every 5th entry misses its deadline (rho = 0.2) ===")
    if not part_d():
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Is the Theorem 1 radius monotone in the lag d used to build the lanes?  (review item D1)

Run:  python theory/checks/check_lag_monotonicity.py > theory/checks/results_check_lag_monotonicity.txt

Deterministic (no randomness, no seeds). Recomputes, from the definitions in theorems.md,

    L_k = log(2 d c0 (k+1)^2 / delta),  c0 = pi^2/6,
    b(q)  = sqrt(2^k(q) L_k(q)),  k(q) = floor(log2 q)           (q >= 1),  b(0) = 0,
    b*(q) = min_k 0.5 sqrt(2^k L_k) (1 + q / 2^(k+1))            (q >= 1),  b*(0) = 0,
    B_T = sum_j b(Q_{j,T}),   Q_{j,T} = sum_{t<=T, t = j mod d} n_t^2.

Part 1: the counterexample given by the GPT reviewer (T = 4, one entry on day 1 and one on
        day 4, delta = 0.05; claimed B_T(d=2) ~ 4.42 > B_T(d=3) ~ 3.65).
Part 2: the same phenomenon at a sample size where the interval is not clipped to [0,1]:
        entries only on days t = 1 mod 3.
Part 3: an "ordinary" schedule (entries every day), where a larger d does give a larger radius.
Part 4: brute-force count over all entry schedules n in {0,1}^T, T = 8: how often is
        B_T(d+1) < B_T(d)?
"""
import itertools
import math

C0 = math.pi ** 2 / 6


def L(k, d, delta):
    return math.log(2 * d * C0 * (k + 1) ** 2 / delta)


def b(q, d, delta):
    if q == 0:
        return 0.0
    k = int(math.floor(math.log2(q)))
    return math.sqrt(2 ** k * L(k, d, delta))


def b_star(q, d, delta):
    if q == 0:
        return 0.0
    kmax = int(math.floor(math.log2(q))) + 3   # g_k(q) is increasing in k beyond k(q)+1
    return min(0.5 * math.sqrt(2 ** k * L(k, d, delta)) * (1 + q / 2 ** (k + 1)) for k in range(kmax + 1))


def lane_clocks(n, d):
    """n[t-1] = number of entries on day t, t = 1..T. Returns Q_j, j = 0..d-1."""
    Q = [0] * d
    for t, nt in enumerate(n, start=1):
        Q[t % d] += nt * nt
    return Q


def radii(n, d, delta):
    Q = lane_clocks(n, d)
    return Q, sum(b(q, d, delta) for q in Q), sum(b_star(q, d, delta) for q in Q)


def main():
    delta = 0.05
    print("=== Part 1: reviewer's counterexample (T=4, n = (1,0,0,1), delta=0.05) ===")
    n = [1, 0, 0, 1]
    for d in (1, 2, 3, 4):
        Q, B, Bs = radii(n, d, delta)
        print(f"d={d}: lane clocks Q_j={Q}  B_T={B:.6f}  B*_T={Bs:.6f}")
    print("closed forms quoted by the reviewer:")
    print(f"  2*sqrt(log(4 c0/delta))  = {2 * math.sqrt(math.log(4 * C0 / delta)):.6f}   (d=2)")
    print(f"  sqrt(2*log(24 c0/delta)) = {math.sqrt(2 * math.log(24 * C0 / delta)):.6f}   (d=3)")
    _, B2, Bs2 = radii(n, 2, delta)
    _, B3, Bs3 = radii(n, 3, delta)
    print(f"B_T(d=3) < B_T(d=2): {B3 < B2}   B*_T(d=3) < B*_T(d=2): {Bs3 < Bs2}")
    print("note: N_T = 2 here, so B_T/N_T > 1 for both d and both clipped intervals are [0,1];")
    print("      the example shows non-monotonicity of the RADIUS, not two different intervals.")

    print()
    print("=== Part 2: entries only on days t = 1 mod 3, n_t = 10 on those days, delta=0.05 ===")
    print("(if the true lag is 2, both d=2 and d=3 are valid; d=3 puts all entries in one lane)")
    print("T      N_T    d  B_T/N_T   B*_T/N_T")
    for T in (300, 3000, 30000):
        n = [10 if t % 3 == 1 else 0 for t in range(1, T + 1)]
        N = sum(n)
        for d in (2, 3, 4, 6):
            _, B, Bs = radii(n, d, delta)
            print(f"{T:<6d} {N:<6d} {d}  {B / N:.5f}   {Bs / N:.5f}")

    print()
    print("=== Part 3: entries every day, n_t = 10, delta=0.05 (the ordinary case) ===")
    print("T      N_T    d   B_T/N_T   B*_T/N_T   B*_T(d)/B*_T(2)   sqrt(d/2)")
    for T in (3000, 30000):
        n = [10] * T
        N = sum(n)
        base = None
        for d in (2, 3, 4, 6, 11, 21):
            _, B, Bs = radii(n, d, delta)
            base = Bs if base is None else base
            print(f"{T:<6d} {N:<6d} {d:<3d} {B / N:.5f}   {Bs / N:.5f}    {Bs / base:.4f}            {math.sqrt(d / 2):.4f}")

    print()
    print("=== Part 4: all schedules n in {0,1}^8 with N_T >= 1, delta=0.05 ===")
    print("d -> d+1   #schedules   #B(d+1)<B(d)   #B*(d+1)<B*(d)")
    T = 8
    for d in (1, 2, 3, 4):
        tot = lessB = lessBs = 0
        for n in itertools.product((0, 1), repeat=T):
            if sum(n) == 0:
                continue
            tot += 1
            _, Ba, Bsa = radii(n, d, delta)
            _, Bb, Bsb = radii(n, d + 1, delta)
            lessB += Bb < Ba - 1e-12
            lessBs += Bsb < Bsa - 1e-12
        print(f"{d} -> {d + 1}     {tot:<10d}   {lessB:<13d}   {lessBs}")


if __name__ == "__main__":
    main()

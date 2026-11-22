"""Finite numerical sanity check of the two steps of the Pinsker proof in proofs.md section 2.3.

Run:  python theory/checks/check_pinsker_binary.py > theory/checks/results_check_pinsker_binary.txt

Step 1 (data processing for one event): for distributions P, Q on a finite set and
        A = {p > q}, x = P(A), y = Q(A):   KL(P||Q) >= kl(x, y)   and   TV(P,Q) = x - y.
Step 2 (binary Pinsker): kl(x, y) >= 2 (x - y)^2 on a grid of (x, y) in (0,1)^2.

A grid / random-instance check cannot prove an inequality; the proof is the analytic argument
in proofs.md. This script only looks for a counterexample or an algebra slip.
"""
import numpy as np

SEEDS = [1, 2, 3]


def kl_bin(x, y):
    return x * np.log(x / y) + (1 - x) * np.log((1 - x) / (1 - y))


def main():
    g = np.linspace(1e-4, 1 - 1e-4, 2001)
    x, y = np.meshgrid(g, g, indexing="ij")
    gap = kl_bin(x, y) - 2 * (x - y) ** 2
    print("=== Step 2: kl(x,y) - 2(x-y)^2 on a 2001 x 2001 grid of (0,1)^2 ===")
    print(f"min gap = {gap.min():.3e}  (must be >= 0 up to rounding); "
          f"number of grid points with gap < -1e-12: {int((gap < -1e-12).sum())}")
    # second derivative bound 1/(x(1-x)) >= 4
    print(f"min of 1/(x(1-x)) on the grid = {(1 / (g * (1 - g))).min():.6f}  (claim: >= 4)")

    print()
    print("=== Step 1: random P, Q on finite sets ===")
    print("seed  instances  min[KL - kl(x,y)]  max|TV - (x-y)|  min[KL - 2 TV^2]")
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        m1, m2, m3 = np.inf, 0.0, np.inf
        n_inst = 20000
        for _ in range(n_inst):
            k = int(rng.integers(2, 12))
            p = rng.dirichlet(np.ones(k) * rng.choice([0.3, 1.0, 5.0]))
            q = rng.dirichlet(np.ones(k) * rng.choice([0.3, 1.0, 5.0]))
            p = np.maximum(p, 1e-12); p /= p.sum()
            q = np.maximum(q, 1e-12); q /= q.sum()
            A = p > q
            xx, yy = p[A].sum(), q[A].sum()
            if not (0 < yy < 1 and 0 < xx < 1):
                continue
            KL = float((p * np.log(p / q)).sum())
            TV = 0.5 * np.abs(p - q).sum()
            m1 = min(m1, KL - kl_bin(xx, yy))
            m2 = max(m2, abs(TV - (xx - yy)))
            m3 = min(m3, KL - 2 * TV ** 2)
        print(f"{seed:<5d} {n_inst:<9d}  {m1:+.3e}         {m2:.3e}        {m3:+.3e}")


if __name__ == "__main__":
    main()

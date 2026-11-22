"""Unit tests for intervals.py (run: python -m unittest test_intervals -v)."""
import unittest

import numpy as np
from scipy.stats import norm

from intervals import (Contrast, bootstrap_contrasts, point_estimates, seed_average,
                       simultaneous_intervals, stationary_bootstrap_counts,
                       stationary_bootstrap_indices)


class TestBootstrap(unittest.TestCase):
    def test_counts_sum_to_T(self):
        rng = np.random.default_rng(1)
        c = stationary_bootstrap_counts(500, 300, 24, rng)
        self.assertTrue(np.all(c.sum(axis=1) == 500))
        self.assertTrue(np.all(c >= 0))

    def test_mean_block_length(self):
        rng = np.random.default_rng(2)
        T, B, L = 2000, 200, 24
        idx = stationary_bootstrap_indices(T, B, L, rng)
        # a block continues iff idx[t] == idx[t-1]+1 mod T (up to chance coincidences 1/T)
        cont = (idx[:, 1:] == (idx[:, :-1] + 1) % T)
        p_new = 1 - cont.mean()
        self.assertAlmostEqual(p_new, 1 / L, delta=0.004)

    def test_uniform_marginal(self):
        rng = np.random.default_rng(3)
        c = stationary_bootstrap_counts(100, 4000, 10, rng)
        m = c.mean(axis=0)
        self.assertLess(np.abs(m - 1).max(), 0.1)

    def test_same_dates_for_all_series(self):
        # paired: a contrast of a policy with itself is exactly 0 in every resample
        rng = np.random.default_rng(4)
        T = 200
        N = rng.normal(size=(2, 3, T))
        N[1] = N[0]
        S = np.full((2, 3, T), 15.0)
        cs = [Contrast("a", 0, 1)]
        counts = stationary_bootstrap_counts(T, 100, 24, rng)
        ts, void = bootstrap_contrasts(N, S, cs, counts)
        self.assertTrue(np.all(ts == 0.0))


class TestEstimates(unittest.TestCase):
    def test_seed_average_before_ratio(self):
        # seed 0 submits 1 order with return 1; seed 1 submits 3 orders with total 0
        N = np.array([[[1.0], [0.0]], [[0.0], [0.0]]])
        S = np.array([[[1.0], [3.0]], [[1.0], [1.0]]])
        th, V, _ = point_estimates(N, S, [Contrast("a", 0, 1)])
        self.assertAlmostEqual(V[("a", 0)], 0.5 / 2.0)  # (1+0)/2 / ((1+3)/2) = 0.25
        self.assertAlmostEqual(th[0], 0.25)

    def test_difference_of_ratios(self):
        T = 4
        N = np.array([[1.0, 1.0, 1.0, 1.0], [2.0, 0.0, 0.0, 0.0]])
        S = np.array([[1.0, 1.0, 1.0, 1.0], [2.0, 2.0, 2.0, 2.0]])
        th, V, _ = point_estimates(N, S, [Contrast("a", 0, 1)])
        self.assertAlmostEqual(th[0], 1.0 - 2.0 / 8.0)
        # paired form equals the ratio difference when counts are equal
        S2 = np.ones((2, T))
        th2, _, _ = point_estimates(N, S2, [Contrast("a", 0, 1)])
        self.assertAlmostEqual(th2[0], ((N[0] - N[1]).sum()) / 4.0)

    def test_zero_submission_policy_flagged(self):
        N = np.zeros((2, 5))
        S = np.zeros((2, 5))
        S[0] = 1.0
        N[0] = 0.3
        th, V, zf = point_estimates(N, S, [Contrast("a", 0, 1)])
        self.assertEqual(V[("a", 1)], 0.0)
        self.assertTrue(zf[("a", 1)])
        self.assertFalse(zf[("a", 0)])
        self.assertAlmostEqual(th[0], 0.3)


class TestRule(unittest.TestCase):
    def _gauss(self, rng, T=600, P=3, mu=(0.0, 0.1, 0.2)):
        N = rng.normal(size=(P, T)) + np.array(mu)[:, None]
        S = np.ones((P, T))
        return N, S

    def test_primary_and_fallback_shape(self):
        rng = np.random.default_rng(5)
        N, S = self._gauss(rng)
        cs = [Contrast("10", 1, 0), Contrast("20", 2, 0), Contrast("21", 2, 1)]
        r = simultaneous_intervals(N, S, cs, B=500, mean_block=5, rng=rng)
        self.assertTrue(r.primary_applicable)
        self.assertTrue(np.all(r.hi > r.lo))
        self.assertAlmostEqual(r.z_bonf, norm.ppf(1 - 0.05 / 6))
        # q lies between the marginal and the Bonferroni value (approximately)
        self.assertGreater(r.q, 1.8)
        self.assertLess(r.q, r.z_bonf + 0.3)

    def test_identical_decisions_zero_se(self):
        rng = np.random.default_rng(6)
        N, S = self._gauss(rng)
        N[1] = N[0]
        cs = [Contrast("same", 1, 0), Contrast("20", 2, 0)]
        r = simultaneous_intervals(N, S, cs, B=400, mean_block=5, rng=rng)
        self.assertTrue(r.zero_se[0])
        self.assertFalse(r.zero_se_nonidentical[0])
        self.assertEqual(r.theta_hat[0], 0.0)
        self.assertEqual(r.lo[0], 0.0)
        self.assertEqual(r.hi[0], 0.0)
        # excluded from the max statistic: q equals the one-contrast quantile
        r1 = simultaneous_intervals(N, S, [Contrast("20", 2, 0)], B=400, mean_block=5,
                                    rng=np.random.default_rng(6), counts=None)
        # recompute with the same counts to compare exactly
        counts = stationary_bootstrap_counts(N.shape[1], 400, 5, np.random.default_rng(7))
        ra = simultaneous_intervals(N, S, cs, counts=counts)
        rb = simultaneous_intervals(N, S, [Contrast("20", 2, 0)], counts=counts)
        self.assertAlmostEqual(ra.q, rb.q, places=12)
        # but the Bonferroni m stays the family size
        self.assertAlmostEqual(ra.z_bonf, norm.ppf(1 - 0.05 / 4))

    def test_zero_se_nonidentical_flag(self):
        # numerator difference proportional to the count every day -> theta* constant
        T = 300
        S = np.ones((2, T)) * 15
        N = np.zeros((2, T))
        N[0] = 0.01 * S[0]
        cs = [Contrast("const", 0, 1)]
        r = simultaneous_intervals(N, S, cs, B=200, mean_block=10, rng=np.random.default_rng(8))
        self.assertTrue(r.zero_se[0])
        self.assertTrue(r.zero_se_nonidentical[0])
        self.assertAlmostEqual(r.lo[0], 0.01)
        self.assertAlmostEqual(r.hi[0], 0.01)

    def test_void_resamples_trigger_fallback(self):
        # policy 1 submits on only 2 of 400 days -> many resamples have zero count for it
        rng = np.random.default_rng(9)
        T = 400
        N = rng.normal(size=(2, T))
        S = np.ones((2, T))
        S[1] = 0.0
        N[1] = 0.0
        S[1, 10] = 1.0
        S[1, 11] = 1.0
        cs = [Contrast("rare", 0, 1), Contrast("self", 0, 0)]
        r = simultaneous_intervals(N, S, cs, B=1000, mean_block=24, rng=rng)
        self.assertGreater(r.void_counts[0], 1)
        self.assertEqual(r.void_counts[1], 0)
        self.assertFalse(r.primary_applicable)
        self.assertTrue(np.all(np.isnan(r.lo_primary)))
        np.testing.assert_allclose(r.lo, r.lo_fallback)

    def test_few_voids_below_limit_keep_primary(self):
        # with counts from a fixed matrix: make exactly one resample void
        T = 50
        N = np.random.default_rng(10).normal(size=(2, T))
        S = np.ones((2, T))
        S[1, :] = 0.0
        S[1, 0] = 1.0
        N[1, :] = 0.0
        B = 2000
        counts = np.ones((B, T), dtype=np.int32)
        counts[0, 0] = 0
        counts[0, 1] = 2
        r = simultaneous_intervals(N, S, [Contrast("a", 0, 1)], counts=counts)
        self.assertEqual(r.void_counts[0], 1)
        self.assertTrue(r.primary_applicable)  # 1/2000 = 0.05% <= 0.1%
        counts[1, 0] = 0
        counts[1, 1] = 2
        counts[2, 0] = 0
        counts[2, 1] = 2
        r = simultaneous_intervals(N, S, [Contrast("a", 0, 1)], counts=counts)
        self.assertEqual(r.void_counts[0], 3)
        self.assertFalse(r.primary_applicable)  # 3/2000 = 0.15% > 0.1%

    def test_late_start_window(self):
        rng = np.random.default_rng(11)
        T = 500
        N = rng.normal(size=(2, T))
        S = np.ones((2, T)) * 15
        mask = np.zeros(T)
        mask[200:] = 1
        c = Contrast("late", 0, 1, mask=mask)
        th, V, _ = point_estimates(N, S, [c])
        self.assertAlmostEqual(th[0], (N[0, 200:].sum() - N[1, 200:].sum()) / (15 * 300))
        # data before the start do not influence anything
        N2 = N.copy()
        N2[:, :200] += 100.0
        counts = stationary_bootstrap_counts(T, 300, 24, np.random.default_rng(12))
        r1 = simultaneous_intervals(N, S, [c], counts=counts)
        r2 = simultaneous_intervals(N2, S, [c], counts=counts)
        np.testing.assert_allclose(r1.lo, r2.lo)
        np.testing.assert_allclose(r1.se, r2.se)

    def test_coverage_iid_quick(self):
        # small Monte-Carlo sanity: iid Gaussian, 3 contrasts, 200 reps -> non-coverage near 5%
        rng = np.random.default_rng(13)
        miss = 0
        R = 200
        cs = [Contrast("10", 1, 0), Contrast("20", 2, 0), Contrast("21", 2, 1)]
        truth = np.array([0.1, 0.2, 0.1])
        for _ in range(R):
            N, S = self._gauss(rng, T=400)
            r = simultaneous_intervals(N, S, cs, B=400, mean_block=2, rng=rng)
            miss += int(np.any((truth < r.lo) | (truth > r.hi)))
        self.assertLess(miss / R, 0.12)


if __name__ == "__main__":
    unittest.main()

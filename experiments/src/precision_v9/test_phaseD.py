"""Phase D unit tests (python -m unittest test_phaseD -v)."""
import unittest
from dataclasses import replace

import numpy as np
from scipy.stats import norm

from bootstrap_t import (autocov, bootstrap_t_stats, bt_rule, circular_block_indices,
                         hac_se, hac_var_direct, hac_var_from_gamma, ratio_parts)
from pipeline import scenario_params
from pipeline2 import (CONTRASTS2, masks2, policy_level_series, policy_level_truth,
                       run_history2)


class TestHAC(unittest.TestCase):
    def test_bartlett_equals_sum_of_squares_identity(self):
        rng = np.random.default_rng(1)
        for b in (0, 1, 5, 10, 20):
            x = rng.standard_normal((4, 300))
            x -= x.mean(-1, keepdims=True)
            g = autocov(x, max(b, 1))
            np.testing.assert_allclose(hac_var_from_gamma(g, b), hac_var_direct(x, b), rtol=1e-10)

    def test_psd_on_adversarial_series(self):
        T = 500
        alt = np.where(np.arange(T) % 2 == 0, 1.0, -1.0)
        rng = np.random.default_rng(2)
        series = [alt, alt * rng.random(T), np.repeat([1.0, -1.0], T // 2),
                  np.sin(np.arange(T) * 2.9)]
        for x in series:
            x = x - x.mean()
            for b in (1, 5, 10, 20, 60):
                v = hac_var_from_gamma(autocov(x, b), b)
                self.assertGreaterEqual(v, -1e-14)
                self.assertAlmostEqual(v, hac_var_direct(x, b), places=12)

    def test_hac_consistent_for_ma_process(self):
        # MA(4) of 5-day moving sums: long-run variance 25 * sigma^2 / 5 = 5 (unit shocks / sqrt5)
        rng = np.random.default_rng(3)
        T, R = 1075, 400
        vals = []
        for _ in range(R):
            e = rng.standard_normal(T + 4)
            c = np.concatenate([[0], np.cumsum(e)])
            x = (c[5:] - c[:-5]) / np.sqrt(5)
            x = x - x.mean()
            vals.append(hac_var_from_gamma(autocov(x, 20), 20))
        # Bartlett with b = 20 has truncation bias of order 4/21 of the off-diagonal part
        self.assertLess(abs(np.mean(vals) / 5.0 - 1), 0.15)


class TestInfluence(unittest.TestCase):
    def test_single_ratio_delta_identity(self):
        rng = np.random.default_rng(4)
        T = 800
        S = rng.integers(1, 20, size=(2, T)).astype(float)
        N = S * 0.01 + rng.standard_normal((2, T)) * 0.1
        cont = [("c", 0, 1, False)]
        th, psi, _ = ratio_parts(N, S, cont, np.ones((1, T)))
        V0, V1 = N[0].sum() / S[0].sum(), N[1].sum() / S[1].sum()
        d0, d1 = S[0].mean(), S[1].mean()
        psi_ref = (N[0] - V0 * S[0]) / d0 - (N[1] - V1 * S[1]) / d1
        np.testing.assert_allclose(psi[0], psi_ref)
        self.assertAlmostEqual(psi[0].sum(), 0.0, places=10)
        se0 = hac_se(psi, [0])[0][0]
        self.assertAlmostEqual(se0 ** 2, (psi_ref ** 2).sum() / T ** 2, places=15)

    def test_influence_variance_matches_monte_carlo_iid(self):
        rng = np.random.default_rng(5)
        T, R = 600, 3000
        th, se2 = [], []
        cont = [("c", 0, 1, False)]
        ones = np.ones((1, T))
        for _ in range(R):
            S = rng.integers(5, 16, size=(2, T)).astype(float)
            common = rng.standard_normal(T)
            N = S * (np.array([[0.003], [0.001]]) + 0.02 * (0.7 * common + 0.7 * rng.standard_normal((2, T))))
            t, psi, _ = ratio_parts(N, S, cont, ones)
            th.append(t[0])
            se2.append(hac_se(psi, [0])[0][0] ** 2)
        ratio = np.mean(se2) / np.var(th, ddof=1)
        self.assertLess(abs(ratio - 1), 0.06)

    def test_late_mask_zeroes_influence_outside_window(self):
        rng = np.random.default_rng(6)
        T = 400
        N = rng.standard_normal((2, T))
        S = np.full((2, T), 15.0)
        m = np.zeros((1, T))
        m[0, 150:] = 1
        th, psi, _ = ratio_parts(N, S, [("c", 0, 1, True)], m)
        self.assertTrue(np.all(psi[0, :150] == 0))
        self.assertAlmostEqual(th[0], (N[0, 150:] - N[1, 150:]).sum() / (15 * 250))


class TestBootstrapT(unittest.TestCase):
    def test_hand_computed_resample(self):
        T = 6
        N = np.array([[1., 2., 3., 4., 5., 6.], [0., 0., 1., 1., 0., 0.]])
        S = np.ones((2, T))
        cont = [("c", 0, 1, False)]
        masks = np.ones((1, T))
        th, psi, _ = ratio_parts(N, S, cont, masks)
        idx = np.array([[0, 1, 2, 0, 1, 2]])
        st, void = bootstrap_t_stats(N, S, cont, masks, idx, th, [0, 1])
        x = (N[0] - N[1])[idx[0]]
        ths = x.mean()
        p = x - ths
        for b in (0, 1):
            g0 = (p * p).sum() / T
            g1 = (p[1:] * p[:-1]).sum() / T
            v = g0 + (2 * 0.5 * g1 if b == 1 else 0.0)
            self.assertAlmostEqual(st[b][0, 0], abs(ths - th[0]) / np.sqrt(v / T), places=12)

    def test_iid_single_contrast_q_near_normal(self):
        rng = np.random.default_rng(7)
        T = 2000
        N = rng.standard_normal((2, 1, T))
        S = np.ones((2, 1, T))
        r = bt_rule(N, S, [("c", 0, 1, False)], np.ones((1, T)), [("stat", 1)], [0], B=4000,
                    rng_for=lambda i: np.random.default_rng(8))
        self.assertAlmostEqual(r["q"][("stat", 1, 0)], 1.96, delta=0.1)

    def test_independent_contrasts_sidak(self):
        rng = np.random.default_rng(9)
        T, J = 2000, 4
        N = rng.standard_normal((2 * J, 1, T))
        S = np.ones((2 * J, 1, T))
        cont = [(f"c{j}", 2 * j, 2 * j + 1, False) for j in range(J)]
        r = bt_rule(N, S, cont, np.ones((J, T)), [("stat", 1)], [0], B=4000,
                    rng_for=lambda i: np.random.default_rng(10))
        sidak = norm.ppf(1 - (1 - 0.95 ** (1 / J)) / 2)
        self.assertAlmostEqual(r["q"][("stat", 1, 0)], sidak, delta=0.12)

    def test_circular_blocks(self):
        rng = np.random.default_rng(11)
        idx = circular_block_indices(100, 5, 10, rng)
        self.assertEqual(idx.shape, (5, 100))
        d = (idx[:, 1:] - idx[:, :-1]) % 100
        for t in range(99):
            if (t + 1) % 10 != 0:
                self.assertTrue(np.all(d[:, t] == 1))

    def test_identical_policies_excluded(self):
        rng = np.random.default_rng(12)
        T = 500
        N = rng.standard_normal((3, 1, T))
        N[1] = N[0]
        S = np.ones((3, 1, T))
        cont = [("same", 1, 0, False), ("x", 2, 0, False)]
        r = bt_rule(N, S, cont, np.ones((2, T)), [("stat", 5)], [5], B=500,
                    rng_for=lambda i: np.random.default_rng(13))
        self.assertTrue(r["zero_se"][5][0])
        self.assertEqual(r["theta"][0], 0.0)


class TestScenarios(unittest.TestCase):
    def test_policy_level_truth_and_shapes(self):
        for sc in ("S0", "S1", "S2"):
            N, S = policy_level_series(sc, 10_000_123)
            self.assertEqual(N.shape, (12, 1, 1075))
        self.assertEqual(len(policy_level_truth()), 12)

    def test_s1_overlap_autocorrelation(self):
        N, S = policy_level_series("S1", 10_000_124, T=20000)
        x = N[0, 0] / S[0, 0]
        x = x - x.mean()
        ac = [np.corrcoef(x[k:], x[:-k])[0, 1] for k in (1, 4, 5, 6)]
        self.assertAlmostEqual(ac[0], 0.8, delta=0.03)
        self.assertAlmostEqual(ac[1], 0.2, delta=0.03)
        self.assertLess(abs(ac[2]), 0.03)

    def test_F3b_year_flip_leaves_decisions_unchanged(self):
        # audit of the exact-zero symmetry argument: flipping the year-Y regime variables and
        # every return shock with state day in year Y must leave every decision of years <= Y
        # bit-identical, while the year-Y returns change sign.
        p = replace(scenario_params("F3b"), n_names=60, dev_years=3, holdout_days=300)
        for Y in (3, 4):
            N0, S0, d0, h0 = run_history2(p, 10_000_500, 10_000_501, n_seeds=2, return_decisions=True)
            N1, S1, d1, h1 = run_history2(p, 10_000_500, 10_000_501, n_seeds=2, flip_year=Y,
                                          return_decisions=True)
            A = p.days_per_year
            hold0 = p.dev_years * A
            end = min((Y + 1) * A, hold0 + p.holdout_days) - hold0
            for k in d0:
                np.testing.assert_array_equal(d0[k][:, :end], d1[k][:, :end])
            self.assertFalse(np.allclose(N0, N1))
            np.testing.assert_array_equal(np.abs(h0.logvol), np.abs(h1.logvol))

    def test_pipeline2_shapes(self):
        p = replace(scenario_params("F1"), n_names=60, dev_years=3, holdout_days=300)
        N, S = run_history2(p, 10_000_600, 10_000_601, n_seeds=2)
        self.assertEqual(N.shape, (12, 2, 300))
        self.assertEqual(masks2(p).shape, (12, 300))
        self.assertEqual(len(CONTRASTS2), 12)


if __name__ == "__main__":
    unittest.main()

"""Phase E tests (python -m unittest test_phaseE -v)."""
import unittest

import numpy as np
from scipy.stats import norm, t as student_t

from bootstrap_t import autocov, bootstrap_t_stats, hac_var_direct, hac_var_from_gamma, ratio_parts
from intervals import stationary_bootstrap_indices
from methods_lit import (bt_fast_q, ewc_lrv, ewc_nu, maxt_quantile, nw_cross, nw_lrv, nw_S,
                         prewhite_lrv, simulate_fixedb_univariate, simulate_joint_panels, simulate_sn_U)


class TestLRV(unittest.TestCase):
    def test_nw_equals_bartlett_identity(self):
        rng = np.random.default_rng(1)
        x = rng.standard_normal((3, 500))
        x -= x.mean(-1, keepdims=True)
        for S in (1, 2, 10, 43):
            np.testing.assert_allclose(nw_lrv(x, S), hac_var_direct(x, S - 1), rtol=1e-12)
            np.testing.assert_allclose(nw_lrv(x, S), hac_var_from_gamma(autocov(x, max(S - 1, 1)), S - 1), rtol=1e-10)

    def test_nw_cross_diagonal(self):
        rng = np.random.default_rng(2)
        X = rng.standard_normal((400, 4))
        X -= X.mean(0)
        C = nw_cross(X, 20)
        np.testing.assert_allclose(np.diag(C), nw_lrv(X.T, 20), rtol=1e-12)
        self.assertTrue(np.all(np.linalg.eigvalsh(C) > -1e-12))

    def test_prewhitening_ar1(self):
        rng = np.random.default_rng(3)
        n, phi = 200_000, 0.9
        e = rng.standard_normal(n)
        x = np.empty(n)
        x[0] = e[0]
        for t in range(1, n):
            x[t] = phi * x[t - 1] + e[t]
        x -= x.mean()
        om, rho = prewhite_lrv(x, nw_S(n))
        self.assertAlmostEqual(rho, phi, delta=0.005)
        # sampling error of rho_hat is amplified by (1 - rho)^-2 (about 2% per 0.001 in rho)
        self.assertAlmostEqual(om / (1 / (1 - phi) ** 2), 1.0, delta=0.1)


class TestCriticalValues(unittest.TestCase):
    def test_ewc_is_exactly_t_nu_for_iid_gaussian(self):
        # LLSW (2018): EWC fixed-b critical values are t_nu; for iid Gaussian data the EWC t-statistic
        # is exactly t_nu distributed in finite samples (cosine weights orthogonal to the constant).
        rng = np.random.default_rng(4)
        n, nu, K = 300, 12, 40_000
        w = rng.standard_normal((K, n))
        tstat = np.sqrt(n) * w.mean(1) / np.sqrt(ewc_lrv(w, nu))
        for p in (0.975, 0.995):
            self.assertAlmostEqual(np.quantile(np.abs(tstat), 2 * p - 1), student_t.ppf(p, nu), delta=0.06)

    def test_fixedb_bartlett_small_b_is_normal_and_grows_with_b(self):
        q_small = np.quantile(simulate_fixedb_univariate(2000, 2, K=40_000, seed=5), 0.95)
        self.assertAlmostEqual(q_small, norm.ppf(0.975), delta=0.04)
        q1 = np.quantile(simulate_fixedb_univariate(1000, 40, K=40_000, seed=6), 0.95)
        q2 = np.quantile(simulate_fixedb_univariate(1000, 200, K=40_000, seed=7), 0.95)
        self.assertGreater(q1, q_small)
        self.assertGreater(q2, q1)
        # NOT verified against a published table (see PHASE_E_NOTES.md): no published fixed-b
        # quantile could be read from a source during this task.

    def test_maxt_identity_correlation_matches_sidak_of_marginal(self):
        J = 4
        panels = simulate_joint_panels(300, 200, J, K=8000, seed=8)
        q = maxt_quantile(panels, np.eye(J), np.zeros(J, bool))
        uni = simulate_fixedb_univariate(300, nw_S(300), K=80_000, seed=9)
        p_ind = np.mean(uni <= q) ** J
        self.assertAlmostEqual(p_ind, 0.95, delta=0.01)

    def test_sn_statistic_runs(self):
        u = simulate_sn_U(500, K=20_000, seed=10)
        self.assertTrue(np.all(u > 0))
        self.assertGreater(np.quantile(u, 0.95), 3.84)   # heavier than chi2_1 (self-normalised)


class TestFastBootstrap(unittest.TestCase):
    def test_bt_fast_equals_main(self):
        from audit_s0 import ladder_contrasts, ladder_masks, ladder_series
        cs = ladder_contrasts("L4")
        masks = ladder_masks(cs)
        N, S, mu = ladder_series("L4", 40_999_001)
        Nb, Sb = N[:, 0], S[:, 0]
        th, psi, _ = ratio_parts(Nb, Sb, cs, masks)
        idx = stationary_bootstrap_indices(1075, 50, 48, np.random.default_rng(40_999_002))
        q, st = bt_fast_q(Nb, Sb, cs, masks, idx, th, [5, 20, 43])
        ref, _ = bootstrap_t_stats(Nb, Sb, cs, masks, idx, th, [5, 20, 43])
        for b in (5, 20, 43):
            np.testing.assert_allclose(st[b], ref[b], rtol=1e-9, atol=1e-12)


if __name__ == "__main__":
    unittest.main()

"""Tests for audit_s0.py (python -m unittest test_audit_s0 -v)."""
import unittest

import numpy as np

from audit_s0 import (independent_bootstrap_t, ladder_contrasts, ladder_masks, ladder_series,
                      manual_quantile, student_bonf, truth_of)
from bootstrap_t import bootstrap_t_stats, bt_rule, ratio_parts
from intervals import Contrast, bootstrap_contrasts, simultaneous_intervals, stationary_bootstrap_indices

T_SMALL = 460  # late window (days >= 300) has 160 days: no void replicates in the toy example


class TestIndependentImplementation(unittest.TestCase):
    def setUp(self):
        self.cs = ladder_contrasts("L4")
        self.masks = ladder_masks(self.cs, T_SMALL)
        self.N, self.S, self.mu = ladder_series("L4", 30_999_001, T=T_SMALL)
        self.idx = stationary_bootstrap_indices(T_SMALL, 15, 24, np.random.default_rng(30_999_002))

    def test_stats_match_to_machine_precision(self):
        for b in (0, 3):
            th, s, ths, ss, stat = independent_bootstrap_t(self.N, self.S, self.cs, self.masks, self.idx, b)
            th2, psi, _ = ratio_parts(self.N[:, 0], self.S[:, 0], self.cs, self.masks)
            np.testing.assert_allclose(th, th2, rtol=0, atol=1e-15)
            stats, void = bootstrap_t_stats(self.N[:, 0], self.S[:, 0], self.cs, self.masks, self.idx, th2, [b])
            np.testing.assert_allclose(stats[b], stat, rtol=1e-9, atol=1e-12)
            self.assertFalse(void[b].any())

    def test_q_and_interval_match(self):
        th, s, ths, ss, stat = independent_bootstrap_t(self.N, self.S, self.cs, self.masks, self.idx, 3)
        q_ind = manual_quantile(list(stat.max(1)), 0.95)
        # main implementation with the same indices: bt_rule regenerates them from the same seed
        r = bt_rule(self.N, self.S, self.cs, self.masks, [("stat", 24)], [3], 15,
                    rng_for=lambda i: np.random.default_rng(30_999_002))
        self.assertAlmostEqual(r["q"][("stat", 24, 3)], q_ind, places=11)
        np.testing.assert_allclose(r["se"][3], s, rtol=1e-12)

    def test_old_rule_matches_independent(self):
        th, s, ths, ss, stat = independent_bootstrap_t(self.N, self.S, self.cs, self.masks, self.idx, 0)
        sd = ths.std(0, ddof=1)
        q_ind = manual_quantile(list((np.abs(ths - th) / sd).max(1)), 0.95)
        B = self.idx.shape[0]
        counts = np.bincount((np.arange(B)[:, None] * T_SMALL + self.idx).ravel(),
                             minlength=B * T_SMALL).reshape(B, T_SMALL)
        cons = [Contrast(n, g, h, self.masks[j] if late else None) for j, (n, g, h, late) in enumerate(self.cs)]
        o = simultaneous_intervals(self.N, self.S, cons, counts=counts)
        np.testing.assert_allclose(o.se, sd, rtol=1e-11)
        self.assertAlmostEqual(o.q, q_ind, places=10)

    def test_manual_quantile(self):
        x = np.random.default_rng(3).standard_normal(999)
        for p in (0.5, 0.95, 0.99):
            self.assertAlmostEqual(manual_quantile(list(x), p), float(np.quantile(x, p)), places=14)

    def test_identities_hold_in_every_replicate(self):
        names = [c[0] for c in self.cs]
        th, s, ths, ss, stat = independent_bootstrap_t(self.N, self.S, self.cs, self.masks, self.idx, 0)
        for base in ("A", "B"):
            j = {n: names.index(f"{n}_{base}") for n in ("P1", "P4", "P5", "P6")}
            self.assertAlmostEqual(th[j["P4"]] - th[j["P1"]], th[j["P6"]] - th[j["P5"]], places=15)
            np.testing.assert_allclose(ths[:, j["P4"]] - ths[:, j["P1"]],
                                       ths[:, j["P6"]] - ths[:, j["P5"]], atol=1e-15)
        # also in the old-rule replicates
        cons = [Contrast(n, g, h, self.masks[jj] if late else None) for jj, (n, g, h, late) in enumerate(self.cs)]
        B = self.idx.shape[0]
        counts = np.bincount((np.arange(B)[:, None] * T_SMALL + self.idx).ravel(),
                             minlength=B * T_SMALL).reshape(B, T_SMALL)
        ts, _ = bootstrap_contrasts(self.N, self.S, cons, counts)
        for base in ("A", "B"):
            j = {n: names.index(f"{n}_{base}") for n in ("P1", "P4", "P5", "P6")}
            np.testing.assert_allclose(ts[:, j["P4"]] - ts[:, j["P1"]], ts[:, j["P6"]] - ts[:, j["P5"]], atol=1e-15)


class TestStudent(unittest.TestCase):
    def test_constant_denominator_se_is_textbook(self):
        cs = ladder_contrasts("L3")
        masks = ladder_masks(cs, T_SMALL)
        N, S, mu = ladder_series("L3", 30_999_010, T=T_SMALL)
        th, se, crit = student_bonf(N[:, 0], S[:, 0], cs, masks)
        for j, (n, g, h, late) in enumerate(cs):
            w = masks[j] > 0
            d = (N[g, 0] - N[h, 0])[w] / 15.0
            self.assertAlmostEqual(th[j], d.mean(), places=15)
            self.assertAlmostEqual(se[j], d.std(ddof=1) / np.sqrt(w.sum()), places=15)

    def test_truth_exact(self):
        cs = ladder_contrasts("L2")
        _, _, mu = ladder_series("L2", 30_999_011, T=T_SMALL)
        self.assertEqual(len(truth_of(cs, mu)), 12)




class TestFastPaths(unittest.TestCase):
    def test_iid_counts_equals_bt_rule(self):
        from audit_s0 import iid_bt_counts
        from bootstrap_t import hac_se
        cs = ladder_contrasts("L5")
        masks = ladder_masks(cs)
        for seed in (30_999_200, 30_999_201):
            N, S, mu = ladder_series("L5", seed)
            th, psi, _ = ratio_parts(N[:, 0], S[:, 0], cs, masks)
            se0 = hac_se(psi, [0])[0]
            r = bt_rule(N, S, cs, masks, [("stat", 1)], [0], 999, rng_for=lambda i: np.random.default_rng([seed, 21]))
            idx = stationary_bootstrap_indices(1075, 999, 1, np.random.default_rng([seed, 21]))
            cnt = np.bincount((np.arange(999)[:, None] * 1075 + idx).ravel(), minlength=999 * 1075).reshape(999, 1075)
            q, st = iid_bt_counts(N[:, 0], S[:, 0], cs, masks, cnt, th, se0)
            stats, _ = bootstrap_t_stats(N[:, 0], S[:, 0], cs, masks, idx, th, [0])
            np.testing.assert_allclose(st, stats[0], rtol=1e-8, atol=1e-10)
            self.assertAlmostEqual(q, r["q"][("stat", 1, 0)], places=8)
            np.testing.assert_allclose(se0, r["se"][0], rtol=1e-13)


if __name__ == "__main__":
    unittest.main()

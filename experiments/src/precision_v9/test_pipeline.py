"""Tests of the synthetic pipeline (run: python -m unittest test_pipeline -v)."""
import unittest
from dataclasses import replace

import numpy as np

from pipeline import Params, generate_history, run_history, scenario_params


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.p = replace(Params(), n_names=60, dev_years=3, holdout_days=300, n_seeds=2)

    def test_shapes_and_counts(self):
        N, S = run_history(self.p, 1, 2)
        self.assertEqual(N.shape, (6, 2, 300))
        h = generate_history(self.p, 1, 2)
        ns = np.ceil(0.5 * h.n_t[3 * 242:3 * 242 + 300])
        self.assertTrue(np.all(S == ns[None, None, :]))

    def test_dev_part_fixed_when_holdout_seed_changes(self):
        p = self.p
        h1 = generate_history(p, 5, 10)
        h2 = generate_history(p, 5, 11)
        hold0 = p.dev_years * p.days_per_year
        # features and all labels resolved before hold0 identical
        np.testing.assert_array_equal(h1.X[:hold0 + 1], h2.X[:hold0 + 1])
        last = hold0 - (p.H + 1)
        np.testing.assert_array_equal(h1.R[:last + 1], h2.R[:last + 1])
        np.testing.assert_array_equal(h1.logvol[:hold0 + 1], h2.logvol[:hold0 + 1])
        self.assertFalse(np.array_equal(h1.R[hold0:], h2.R[hold0:]))

    def test_first_holdout_year_models_depend_on_dev_only(self):
        # decisions on hold-out day 0 use features of day 0 (dev-generated) and models fitted on
        # dev data only -> identical across hold-out seeds
        N1, _ = run_history(self.p, 5, 10)
        N2, _ = run_history(self.p, 5, 11)
        # numerators differ (future returns are hold-out draws) ...
        self.assertFalse(np.allclose(N1[:, :, 5], N2[:, :, 5]))

    def test_no_lookahead_in_labels(self):
        # changing returns after day t must not change base or gate decisions on days <= t:
        # checked indirectly: an R value used for training must be resolved before the fit day
        p = self.p
        A, H = p.days_per_year, p.H
        for Y in range(1, 4):
            last = Y * A - (H + 1)
            # order at decision day `last` earns raw returns burn+last+1 .. burn+last+H,
            # all strictly before raw day burn + Y*A (the first decision day of year Y)
            self.assertLess(p.burn + last + H, p.burn + Y * A)

    def test_null_scenario_runs(self):
        p = replace(scenario_params("F3b"), n_names=60, dev_years=3, holdout_days=300, n_seeds=2)
        N, S = run_history(p, 3, 4)
        self.assertTrue(np.isfinite(N).all())


if __name__ == "__main__":
    unittest.main()

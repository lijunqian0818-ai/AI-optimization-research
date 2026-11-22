"""Capacity-matched nuisance features (permuted Z) and preprocessing."""
import unittest

import numpy as np
import pandas as pd

from features import nuisance


def _panel(seed=0, n_days=6, n_codes=40):
    rng = np.random.default_rng(seed)
    days = pd.bdate_range("2021-01-04", periods=n_days)
    codes = [f"sh.{600000 + i}" for i in range(n_codes)]
    idx = pd.MultiIndex.from_product([days, codes], names=["decision_day", "code"])
    n = len(idx)
    df = pd.DataFrame({
        "zh_a": rng.normal(size=n), "zh_b": rng.normal(size=n),
        "zo_lhb_ind_1": (rng.random(n) < 0.1).astype(float), "zo_lhb_net_1": 0.0,
        "zo_blk_ind_1": (rng.random(n) < 0.2).astype(float), "zo_blk_amt_1": 0.0,
        "other": rng.normal(size=n),
    }, index=idx)
    df["zo_lhb_net_1"] = df["zo_lhb_ind_1"] * rng.normal(size=n)
    df["zo_blk_amt_1"] = df["zo_blk_ind_1"] * rng.uniform(size=n)
    df.loc[df.index[::17], "zh_a"] = np.nan
    return df


class TestPermutation(unittest.TestCase):
    def setUp(self):
        self.p = _panel()
        self.zo_blocks = nuisance.zo_blocks(self.p.columns)
        self.q = nuisance.permute_within_day(self.p, {"zh": ["zh_a", "zh_b"], **self.zo_blocks}, seed=3)

    def test_blocks(self):
        self.assertEqual(self.zo_blocks, {"lhb": ["zo_lhb_ind_1", "zo_lhb_net_1"], "blk": ["zo_blk_ind_1", "zo_blk_amt_1"]})

    def test_marginals_missingness_and_event_counts_per_day(self):
        for day, g in self.p.groupby(level=0):
            h = self.q.loc[day]
            for c in ["zh_a", "zh_b", "zo_lhb_net_1", "zo_blk_amt_1"]:
                np.testing.assert_array_equal(np.sort(g[c].values), np.sort(h[c].values))      # NaN sorted last
            self.assertEqual(g["zo_lhb_ind_1"].sum(), h["zo_lhb_ind_1"].sum())
            self.assertEqual(g["zo_blk_ind_1"].sum(), h["zo_blk_ind_1"].sum())
            self.assertEqual(g["zh_a"].isna().sum(), h["zh_a"].isna().sum())

    def test_columns_of_a_block_move_together_and_blocks_move_independently(self):
        # within the lhb block the pair (ind, net) of a row stays a pair
        a = set(map(tuple, self.p[["zo_lhb_ind_1", "zo_lhb_net_1"]].round(12).values.tolist()))
        b = set(map(tuple, self.q[["zo_lhb_ind_1", "zo_lhb_net_1"]].round(12).values.tolist()))
        self.assertEqual(a, b)
        self.assertTrue((self.q["zo_lhb_net_1"][self.q["zo_lhb_ind_1"] == 0] == 0).all())
        # the lhb and blk blocks are not moved by the same permutation
        same_lhb = (self.q["zo_lhb_net_1"].values == self.p["zo_lhb_net_1"].values)
        self.assertFalse(same_lhb.all())
        joint_p = set(map(tuple, self.p[["zh_a", "zo_blk_amt_1"]].round(12).fillna(-9).values.tolist()))
        joint_q = set(map(tuple, self.q[["zh_a", "zo_blk_amt_1"]].round(12).fillna(-9).values.tolist()))
        self.assertNotEqual(joint_p, joint_q)

    def test_other_columns_untouched_and_content_removed(self):
        pd.testing.assert_series_equal(self.p["other"], self.q["other"])
        self.assertLess((self.p["zh_b"].values == self.q["zh_b"].values).mean(), 0.2)

    def test_deterministic_and_seed_dependent(self):
        q2 = nuisance.permute_within_day(self.p, {"zh": ["zh_a", "zh_b"], **self.zo_blocks}, seed=3)
        pd.testing.assert_frame_equal(self.q, q2)
        q3 = nuisance.permute_within_day(self.p, {"zh": ["zh_a", "zh_b"], **self.zo_blocks}, seed=4)
        self.assertFalse(self.q["zh_b"].equals(q3["zh_b"]))

    def test_independent_of_row_order_and_of_other_days(self):
        shuffled = self.p.sample(frac=1.0, random_state=1)
        q = nuisance.permute_within_day(shuffled, {"zh": ["zh_a", "zh_b"]}, seed=3).sort_index()
        ref = nuisance.permute_within_day(self.p, {"zh": ["zh_a", "zh_b"]}, seed=3).sort_index()
        pd.testing.assert_frame_equal(q, ref)
        day = self.p.index.get_level_values(0)[0]
        one = nuisance.permute_within_day(self.p.loc[[day]], {"zh": ["zh_a", "zh_b"]}, seed=3)
        pd.testing.assert_frame_equal(one, ref.loc[[day]])

    def test_population_mask(self):
        pop = pd.Series(False, index=self.p.index)
        pop.iloc[::2] = True
        q = nuisance.permute_within_day(self.p, {"zh": ["zh_b"]}, seed=1, population=pop)
        np.testing.assert_array_equal(q["zh_b"].values[~pop.values], self.p["zh_b"].values[~pop.values])
        np.testing.assert_array_equal(np.sort(q["zh_b"].values[pop.values]), np.sort(self.p["zh_b"].values[pop.values]))


class TestPreprocess(unittest.TestCase):
    def test_rank_and_zscore_use_same_day_rows_only(self):
        p = _panel(seed=2)[["zh_a", "zh_b"]]
        r = nuisance.cs_preprocess(p, "rank")
        self.assertTrue(((r.dropna() > 0) & (r.dropna() <= 1)).all().all())
        self.assertEqual(r["zh_a"].isna().sum(), p["zh_a"].isna().sum())
        day = p.index.get_level_values(0)[2]
        alone = nuisance.cs_preprocess(p.loc[[day]], "rank")
        pd.testing.assert_frame_equal(r.loc[[day]], alone)
        z = nuisance.cs_preprocess(p, "zscore")
        m = z.groupby(level=0).mean()
        self.assertLess(m.abs().max().max(), 1e-12)

    def test_winsorisation(self):
        days = pd.bdate_range("2021-01-04", periods=1)
        idx = pd.MultiIndex.from_product([days, [f"c{i:03d}" for i in range(201)]])
        x = pd.DataFrame({"a": np.r_[np.arange(200.0), 1e9]}, index=idx)
        z = nuisance.cs_preprocess(x, "zscore")
        self.assertLess(z["a"].max(), 3.0)       # the outlier is clipped at the 99th percentile first


if __name__ == "__main__":
    unittest.main()

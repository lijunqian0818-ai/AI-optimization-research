"""B0: hand-computed values and an independent slow re-computation."""
import unittest

import numpy as np
import pandas as pd

from features import ops, base_b0
from features.bars import prepare_bars
from features.tests import synth


def _frame(o, h, l, c, v):
    n = len(c)
    idx = pd.bdate_range("2020-01-01", periods=n)
    c = np.asarray(c, float)
    return pd.DataFrame({"aopen": o, "ahigh": h, "alow": l, "aclose": c, "avolume": v,
                         "avwap": (np.asarray(o, float) + c) / 2, "traded": True}, index=idx)


class TestOpsAgainstPandas(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(7)
        self.x = rng.normal(size=400).cumsum() + 50
        self.y = rng.normal(size=400)
        self.s = pd.Series(self.x)

    def test_simple_ops(self):
        for n in (5, 20, 60):
            r = self.s.rolling(n)
            np.testing.assert_allclose(ops.r_mean(self.x, n), r.mean().values, rtol=1e-12, equal_nan=True)
            np.testing.assert_allclose(ops.r_std(self.x, n), r.std().values, rtol=1e-9, equal_nan=True)
            np.testing.assert_allclose(ops.r_max(self.x, n), r.max().values, equal_nan=True)
            np.testing.assert_allclose(ops.r_min(self.x, n), r.min().values, equal_nan=True)
            np.testing.assert_allclose(ops.r_quantile(self.x, n, 0.8), r.quantile(0.8).values, rtol=1e-12, equal_nan=True)
            np.testing.assert_allclose(ops.r_rank(self.x, n), r.rank(pct=True).values, rtol=1e-12, equal_nan=True)
            np.testing.assert_allclose(ops.r_corr(self.x, self.y, n), self.s.rolling(n).corr(pd.Series(self.y)).values,
                                       rtol=1e-8, atol=1e-10, equal_nan=True)
            np.testing.assert_allclose(ops.r_idxmax(self.x, n), r.apply(lambda w: w.argmax() + 1, raw=True).values,
                                       equal_nan=True)

    def test_regression_ops_against_polyfit(self):
        n = 20
        sl, rs, re_ = ops.r_slope(self.x, n), ops.r_rsquare(self.x, n), ops.r_resi(self.x, n)
        xs = np.arange(n)
        for i in (19, 57, 399):
            w = self.x[i - n + 1:i + 1]
            b, a = np.polyfit(xs, w, 1)
            fit = a + b * xs
            self.assertAlmostEqual(sl[i], b, places=10)
            self.assertAlmostEqual(re_[i], w[-1] - fit[-1], places=9)
            self.assertAlmostEqual(rs[i], 1 - ((w - fit) ** 2).sum() / ((w - w.mean()) ** 2).sum(), places=10)
        self.assertTrue(np.isnan(sl[:n - 1]).all())

    def test_rank_ties(self):
        x = np.array([1.0, 2.0, 2.0, 2.0])
        self.assertAlmostEqual(ops.r_rank(x, 4)[-1], 3.0 / 4)     # average rank of the tie = 3

    def test_nan_in_window_gives_nan_and_no_partial_windows(self):
        x = self.x.copy()
        x[100] = np.nan
        m = ops.r_mean(x, 10)
        self.assertTrue(np.isnan(m[100:110]).all())
        self.assertTrue(np.isfinite(m[110]))
        self.assertTrue(np.isnan(m[:9]).all())

    def test_window_value_independent_of_series_start(self):
        a = ops.r_std(self.x, 30)
        b = ops.r_std(self.x[123:], 30)
        self.assertTrue(np.array_equal(a[123 + 29:], b[29:]))     # bit-identical


class TestB0Hand(unittest.TestCase):
    def test_kbar_hand(self):
        f = base_b0.b0_on_data_dates(_frame([10.0], [11.0], [9.0], [10.5], [100.0]))
        exp = {"b0_KMID": 0.05, "b0_KLEN": 0.2, "b0_KMID2": 0.25, "b0_KUP": 0.05, "b0_KUP2": 0.25,
               "b0_KLOW": 0.1, "b0_KLOW2": 0.5, "b0_KSFT": 0.1, "b0_KSFT2": 0.5,
               "b0_OPEN0": 10 / 10.5, "b0_HIGH0": 11 / 10.5, "b0_LOW0": 9 / 10.5, "b0_VWAP0": 10.25 / 10.5}
        for k, v in exp.items():
            self.assertAlmostEqual(f[k].iloc[0], v, places=10, msg=k)

    def test_rolling_hand_linear_series(self):
        c = np.arange(1.0, 7.0)                    # 1..6
        v = np.array([10.0, 20, 30, 40, 50, 60])
        f = base_b0.b0_on_data_dates(_frame(c, c + 0.5, c - 0.5, c, v)).iloc[-1]
        self.assertAlmostEqual(f["b0_ROC5"], 1 / 6)
        self.assertAlmostEqual(f["b0_MA5"], 4 / 6)
        self.assertAlmostEqual(f["b0_STD5"], np.sqrt(2.5) / 6)
        self.assertAlmostEqual(f["b0_BETA5"], 1 / 6)
        self.assertAlmostEqual(f["b0_RSQR5"], 1.0)
        self.assertAlmostEqual(f["b0_RESI5"], 0.0)
        self.assertAlmostEqual(f["b0_MAX5"], 6.5 / 6)
        self.assertAlmostEqual(f["b0_MIN5"], 1.5 / 6)
        self.assertAlmostEqual(f["b0_QTLU5"], (2 + 0.8 * 4) / 6)
        self.assertAlmostEqual(f["b0_QTLD5"], (2 + 0.2 * 4) / 6)
        self.assertAlmostEqual(f["b0_RANK5"], 1.0)
        self.assertAlmostEqual(f["b0_RSV5"], (6 - 1.5) / (6.5 - 1.5), places=9)
        self.assertAlmostEqual(f["b0_IMAX5"], 1.0)          # maximum is the newest of 5
        self.assertAlmostEqual(f["b0_IMIN5"], 0.2)
        self.assertAlmostEqual(f["b0_IMXD5"], 0.8)
        self.assertAlmostEqual(f["b0_CNTP5"], 1.0)
        self.assertAlmostEqual(f["b0_CNTN5"], 0.0)
        self.assertAlmostEqual(f["b0_CNTD5"], 1.0)
        self.assertAlmostEqual(f["b0_SUMP5"], 1.0, places=9)
        self.assertAlmostEqual(f["b0_SUMN5"], 0.0, places=9)
        self.assertAlmostEqual(f["b0_SUMD5"], 1.0, places=9)
        self.assertAlmostEqual(f["b0_VMA5"], 40 / 60, places=9)
        self.assertAlmostEqual(f["b0_VSTD5"], np.std([20, 30, 40, 50, 60], ddof=1) / 60, places=9)
        self.assertAlmostEqual(f["b0_VSUMP5"], 1.0, places=9)
        self.assertAlmostEqual(f["b0_VSUMD5"], 1.0, places=9)
        x = np.abs(c[1:] / c[:-1] - 1) * v[1:]
        self.assertAlmostEqual(f["b0_WVMA5"], np.std(x, ddof=1) / np.mean(x), places=9)
        self.assertAlmostEqual(f["b0_CORR5"], np.corrcoef(c[1:], np.log(v[1:] + 1))[0, 1], places=9)
        self.assertAlmostEqual(f["b0_CORD5"], np.corrcoef(c[1:] / c[:-1], np.log(v[1:] / v[:-1] + 1))[0, 1], places=9)

    def test_full_window_only(self):
        c = np.arange(1.0, 7.0)
        f = base_b0.b0_on_data_dates(_frame(c, c, c, c, c))
        self.assertTrue(f["b0_MA5"].iloc[:4].isna().all())
        self.assertTrue(f["b0_ROC5"].iloc[:5].isna().all())
        self.assertTrue(f["b0_MA10"].isna().all())

    def test_non_traded_day_has_no_b0(self):
        cal = synth.make_calendar()
        b = prepare_bars(synth.make_raw_bars("sh.600001", cal, seed=5, n_rows=400), cal)
        f = base_b0.b0_on_data_dates(b)
        self.assertTrue(f.loc[~b["traded"].values].isna().all().all())
        self.assertFalse(np.isinf(f.values).any())

    def test_count_is_158(self):
        self.assertEqual(len(base_b0.specs()), 158)


if __name__ == "__main__":
    unittest.main()

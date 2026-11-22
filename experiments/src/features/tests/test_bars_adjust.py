"""Own adjustment factor (PLAN 3.11) and the standardised bar frame."""
import unittest

import numpy as np
import pandas as pd

from features.bars import own_adjust_factor, prepare_bars
from features.timing import TradingCalendar, truncate_bars, check_cutoff
from features.tests import synth


def _raw(rows):
    cols = ["date", "code", "open", "high", "low", "close", "preclose", "volume", "amount", "adjustflag", "turn",
            "tradestatus", "pctChg", "isST"]
    return pd.DataFrame(rows, columns=cols)


class TestAdjust(unittest.TestCase):
    def test_hand_example_split_and_dividend(self):
        # day 3: 2-for-1 split after a close of 11.00 -> preclose 5.50
        # day 5: cash dividend 0.20 after a close of 6.00 -> preclose 5.80
        close = np.array([10.0, 11.0, 5.6, 6.0, 5.9])
        pre = np.array([9.8, 10.0, 5.5, 5.6, 5.8])
        f = own_adjust_factor(close, pre)
        np.testing.assert_allclose(f, [1.0, 1.0, 2.0, 2.0, 2.0 * 6.0 / 5.8], rtol=0, atol=1e-15)
        adj = close * f
        # adjusted return across the split day equals close / preclose
        self.assertAlmostEqual(adj[2] / adj[1], 5.6 / 5.5, places=14)
        self.assertAlmostEqual(adj[4] / adj[3], 5.9 / 5.8, places=14)

    def test_first_row_is_anchor_and_past_never_changes(self):
        rng = np.random.default_rng(0)
        close = rng.uniform(5, 20, 300)
        pre = np.r_[close[0], close[:-1]]
        pre[[50, 120, 250]] *= [0.5, 0.97, 0.8]
        f_full = own_adjust_factor(close, pre)
        self.assertEqual(f_full[0], 1.0)
        for k in (60, 121, 251):
            f_part = own_adjust_factor(close[:k], pre[:k])
            self.assertTrue(np.array_equal(f_full[:k], f_part))      # bit-identical prefix

    def test_bad_preclose_gives_nan_from_there(self):
        f = own_adjust_factor(np.array([10.0, 10.0, 10.0]), np.array([10.0, 0.0, 10.0]))
        self.assertEqual(f[0], 1.0)
        self.assertTrue(np.isnan(f[1]) and np.isnan(f[2]))

    def test_prepare_bars_suspension_and_empty_strings(self):
        cal = TradingCalendar(pd.bdate_range("2020-01-01", periods=10))
        d = cal.days.strftime("%Y-%m-%d")
        raw = _raw([
            [d[0], "sh.600001", "10", "10.5", "9.9", "10.2", "10.0", "1000", "10100", "3", "1.5", "1", "2", "0"],
            [d[1], "sh.600001", "10.2", "10.2", "10.2", "10.2", "10.2", "", "", "3", "", "0", "", "0"],
            [d[2], "sh.600001", "5.1", "5.3", "5.0", "5.2", "5.1", "3000", "15600", "3", "2.0", "1", "1.96", "1"],
        ])
        b = prepare_bars(raw, cal)
        self.assertEqual(list(b["traded"]), [True, False, True])
        self.assertEqual(b["volume"].iloc[1], 0.0)
        self.assertEqual(b["V"].iloc[1], 0.0)
        np.testing.assert_allclose(b["V"].values, [0.015, 0.0, 0.02])
        np.testing.assert_allclose(b["F"].values, [1.0, 1.0, 2.0])
        np.testing.assert_allclose(b["aclose"].values, [10.2, 10.2, 10.4])
        self.assertEqual(list(b["is_st"]), [False, False, True])
        self.assertTrue(np.isnan(b["avwap"].iloc[1]))
        self.assertAlmostEqual(b["avwap"].iloc[2], 15600 / 3000 * 2.0)

    def test_missing_vendor_row_is_inserted_as_nan(self):
        cal = synth.make_calendar()
        raw = synth.make_raw_bars("sh.600001", cal, seed=2, n_rows=300, missing_row=100)
        b = prepare_bars(raw, cal)
        self.assertEqual(b.attrs["n_missing_rows"], 1)
        self.assertEqual(len(b), 300)
        self.assertFalse(b["present"].iloc[100])
        self.assertTrue(np.isnan(b["close"].iloc[100]))
        self.assertTrue(np.isfinite(b["F"].iloc[101]))       # the chain uses the previous existing row

    def test_turnover_above_one_is_counted_not_clipped(self):
        cal = synth.make_calendar()
        b = prepare_bars(synth.make_raw_bars("sh.600001", cal, seed=3, n_rows=600), cal)
        self.assertEqual(b.attrs["n_V_gt_1"], 1)
        self.assertAlmostEqual(b["V"].max(), 1.3)

    def test_cutoff_must_be_trading_day_and_truncation_is_strict(self):
        cal = synth.make_calendar()
        b = prepare_bars(synth.make_raw_bars("sh.600001", cal, seed=3, n_rows=100), cal)
        t = b.index[50]
        self.assertEqual(truncate_bars(b, t).index[-1], b.index[49])
        with self.assertRaises(ValueError):
            check_cutoff(cal, None)
        with self.assertRaises(ValueError):
            check_cutoff(cal, pd.Timestamp("2012-01-01"))     # a Sunday


if __name__ == "__main__":
    unittest.main()

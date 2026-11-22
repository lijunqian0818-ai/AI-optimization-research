"""R_H-sum, R_H-hist, R_O and the rule adapter.

PLAN v0.7: R_H-hist has 80 columns (F-15); bands, thresholds and regime
dates are asserted against the rule calendar (F-20); the top-3 / top-5
indicator is three-valued (F-13); limit counts are NaN over a name's first 5
trading days (F-20). The numerical expectations of the v0.6 R_O tests are
unchanged: the rows of those tests lie outside the first-5-days windows
because `ipo_date` is passed as a day before the test history.
"""
import unittest
from datetime import date
from decimal import Decimal

import numpy as np
import pandas as pd

from engine import rule_calendar as rc
from features import controls, rules
from features.timing import TradingCalendar
from features.bars import prepare_bars
from features.tests import synth


def _b(n, close=None, v=None, high=None, low=None):
    idx = pd.bdate_range("2020-01-01", periods=n)
    c = np.arange(1.0, n + 1) if close is None else np.asarray(close, float)
    return pd.DataFrame({"aclose": c, "ahigh": c * 1.02 if high is None else high,
                         "alow": c * 0.98 if low is None else low,
                         "V": np.full(n, 0.01) if v is None else np.asarray(v, float)}, index=idx)


class TestRHSum(unittest.TestCase):
    def test_hand(self):
        n = 251
        f = controls.rh_sum_on_data_dates(_b(n)).iloc[-1]
        self.assertAlmostEqual(f["rh_ret_1"], 251 / 250 - 1)
        self.assertAlmostEqual(f["rh_ret_250"], 251 / 1 - 1)
        self.assertAlmostEqual(f["rh_ma_gap_5"], 251 / 249 - 1)
        self.assertAlmostEqual(f["rh_uwap_gap_250"], 251 / np.mean(np.arange(2, 252)) - 1)   # equal V: plain mean
        self.assertAlmostEqual(f["rh_pos_20"], (251 - 232 * 0.98) / (251 * 1.02 - 232 * 0.98))
        self.assertAlmostEqual(f["rh_turn_1"], 0.01)
        self.assertAlmostEqual(f["rh_turn_mean_60"], 0.01)
        self.assertAlmostEqual(f["rh_turn_cum_210"], 2.10)
        self.assertAlmostEqual(f["rh_turn_std_20"], 0.0)
        self.assertAlmostEqual(f["rh_hl_1"], 0.04)
        self.assertAlmostEqual(f["rh_hl_mean_20"], 0.04)

    def test_warmup(self):
        f = controls.rh_sum_on_data_dates(_b(251))
        self.assertTrue(f["rh_ret_250"].iloc[:250].isna().all())
        self.assertTrue(f["rh_ma_gap_250"].iloc[:249].isna().all())
        self.assertTrue(np.isfinite(f["rh_ma_gap_250"].iloc[249]))


class TestRHHist(unittest.TestCase):
    def test_bins_hand(self):
        n = 260
        v = np.linspace(0.001, 0.05, n)
        b = _b(n, v=v)
        f = controls.rh_hist_on_data_dates(b)
        c = b["aclose"].values
        i = n - 1
        for w in (250, 210):
            m = w // 10
            start = i - w + 1
            for j in (0, 4, 9):
                rows = np.arange(start + j * m, start + (j + 1) * m)
                tag = f"{j + 1:02d}"
                self.assertAlmostEqual(f[f"rhh{w}_ret_{tag}"].iloc[i], c[rows[-1]] / c[rows[0] - 1] - 1, places=12)
                self.assertAlmostEqual(f[f"rhh{w}_turn_mean_{tag}"].iloc[i], v[rows].mean(), places=14)
                self.assertAlmostEqual(f[f"rhh{w}_vwp_{tag}"].iloc[i], (v[rows] * c[rows]).sum() / v[rows].sum() / c[i] - 1,
                                       places=12)
                self.assertAlmostEqual(f[f"rhh{w}_hl_{tag}"].iloc[i], 0.04, places=12)
        self.assertEqual(f.shape[1], 80)                          # 4 quantities x 10 bins x 2 windows (F-15)
        self.assertFalse([c for c in f.columns if "turn_cum" in c])
        self.assertEqual(len(controls.rh_hist_specs()), 80)
        self.assertEqual(len(controls.rh_sum_specs()), 34)

    def test_bins_tile_the_window(self):
        n = 400
        rng = np.random.default_rng(0)
        v = rng.uniform(0, 0.1, n)
        c = 10 * np.exp(rng.normal(0, 0.02, n).cumsum())
        f = controls.rh_hist_on_data_dates(_b(n, close=c, v=v))
        for w in (250, 210):
            # bins tile the window: cumulative turnover of the window = sum over bins of (bin mean x bin length)
            cum = (f[[f"rhh{w}_turn_mean_{j:02d}" for j in range(1, 11)]] * (w // 10)).sum(axis=1)
            ret = (1 + f[[f"rhh{w}_ret_{j:02d}" for j in range(1, 11)]]).prod(axis=1, skipna=False)
            i = n - 1
            self.assertAlmostEqual(cum.iloc[i], v[i - w + 1:i + 1].sum(), places=12)
            self.assertAlmostEqual(ret.iloc[i], c[i] / c[i - w], places=10)
            self.assertTrue(f[f"rhh{w}_turn_mean_01"].iloc[:w - 1].isna().all())
            self.assertTrue(f[f"rhh{w}_ret_01"].iloc[:w].isna().all())


class TestRules(unittest.TestCase):
    def test_boards(self):
        self.assertEqual(rules.board_of("sh.600000"), ("sse", "main"))
        self.assertEqual(rules.board_of("sh.688981"), ("sse", "star"))
        self.assertEqual(rules.board_of("sz.300750"), ("szse", "chinext"))
        self.assertEqual(rules.board_of("sz.002450"), ("szse", "main"))
        with self.assertRaises(ValueError):
            rules.board_of("bj.920001")

    def test_limit_prices_half_up(self):
        pre = np.array([10.05, 9.99, 3.33, 0.05, 23.45])
        band = np.array([0.10, 0.10, 0.05, 0.10, 0.20])
        up, dn = rules.limit_prices(pre, band)
        np.testing.assert_allclose(up, [11.06, 10.99, 3.50, 0.06, 28.14], atol=1e-9)
        np.testing.assert_allclose(dn, [9.05, 8.99, 3.16, 0.04, 18.76], atol=1e-9)

    def test_limit_prices_agree_with_the_calendar_decimal_version(self):
        rng = np.random.default_rng(3)
        pre = np.round(rng.uniform(0.05, 300, 4000), 2)
        for band in (0.05, 0.10, 0.20):
            up, dn = rules.limit_prices(pre, np.full(len(pre), band))
            for x, u, d in zip(pre, up, dn):
                eu, ed = rc.limit_prices(repr(float(x)), Decimal(str(band)))
                self.assertEqual((round(float(u), 2), round(float(d), 2)), (float(eu), float(ed)), (x, band))

    def test_limit_band_is_the_calendar_band(self):
        d = pd.DatetimeIndex(["2020-08-21", "2020-08-24", "2020-08-24"])
        np.testing.assert_array_equal(rules.limit_band("chinext", [False, False, True], d), [0.10, 0.20, 0.20])
        np.testing.assert_array_equal(rules.limit_band("chinext", [True, True, True], d), [0.05, 0.20, 0.20])
        np.testing.assert_array_equal(rules.limit_band("main", [False, True, False], d), [0.10, 0.05, 0.10])
        np.testing.assert_array_equal(rules.limit_band("star", [False, True, False], d), [0.20, 0.20, 0.20])
        # every day of the calendar window, every board and ST state: equal to rule_calendar.price_band
        days = pd.date_range(rc.CAL_START, rc.CAL_END, freq="37D")
        for board in ("main", "chinext", "star"):
            for st in (False, True):
                got = rules.limit_band(board, np.full(len(days), st), days)
                exp = [float(rc.price_band(x.date(), board, st)) for x in days]
                np.testing.assert_array_equal(got, exp)
        # around every boundary of a band row
        for key, start in rc.boundary_dates():
            if not key.startswith("band:"):
                continue
            _, board, st = key.split(":")
            dd = pd.DatetimeIndex([pd.Timestamp(start) - pd.Timedelta(days=1), pd.Timestamp(start)])
            got = rules.limit_band(board, np.full(2, st == "1"), dd)
            exp = [float(rc.price_band(x.date(), board, st == "1")) for x in dd]
            np.testing.assert_array_equal(got, exp)
        # outside the calendar window: unknown, not an exception and not a guess
        self.assertTrue(np.isnan(rules.limit_band("main", [False], pd.DatetimeIndex(["2026-07-01"]))[0]))

    def test_no_second_copy_of_rule_dates_in_config(self):
        from features import config
        for name in ("CHINEXT_REFORM", "STAR_LAUNCH", "MAIN_REGISTRATION_START", "INS_REGIME_BREAKS",
                     "LHB_TOP5_START", "LHB_TOP5_SZSE_KNOWN_FROM"):
            self.assertFalse(hasattr(config, name), name)
        self.assertFalse(hasattr(rules, "no_limit_rows"))

    def test_group_e_is_read_from_the_engine_calendar(self):
        """Ruling F-20: one calendar. The adapter holds no row of its own and returns, on every day, what the
        engine calendar's scalar queries return."""
        self.assertFalse(hasattr(rules, "_INTERIM_E_ROWS"))
        import inspect
        src = inspect.getsource(rules)
        for token in ("2015-07-08", "2016-01-09", "2017-05-27", "2024-05-24", "2020-08-24", "2021-10-08",
                      "2021-09-17", "2013-12-01", "0.07", "0.15", "0.30"):
            code = "\n".join(line.split("#")[0] for line in src.split("\n") if not line.strip().startswith(('"', "'")))
            self.assertNotIn('"' + token + '"', code, token)                 # no date literal in the code
        days = pd.date_range(rc.CAL_START, rc.CAL_END, freq="23D")
        b = [pd.Timestamp(d) + pd.Timedelta(days=k) for _, d in rc.boundary_dates() for k in (-1, 0)]
        days = pd.DatetimeIndex(sorted(set(days) | {x for x in b if rc.CAL_START <= x.date() <= rc.CAL_END}))
        nan = float("nan")
        np.testing.assert_array_equal(rules.ins_regime(days), [rc.ins_regime(x.date()) for x in days])
        for exch, key in (("sse", "sh"), ("szse", "sz")):
            exp = [rc.lhb_top5(x.date(), key) for x in days]
            np.testing.assert_array_equal(rules.lhb_top5_regime(exch, days), [nan if v is None else v for v in exp])
        for board in ("main", "chinext", "star"):
            got = rules.lhb_thresholds(board, days)
            exp = [rc.lhb_thresholds(x.date(), board) for x in days]
            np.testing.assert_array_equal(got["dev"], [e["price"] for e in exp])
            np.testing.assert_array_equal(got["amp"], [e["amplitude"] for e in exp])
            np.testing.assert_array_equal(got["turn"], [e["turnover"] for e in exp])
            np.testing.assert_array_equal(got["raw"], [1.0 if e["kind"] == "change" else 0.0 for e in exp])
        # every boundary date the task list names for group (e) is a boundary of the calendar the adapter reads
        named = {"2015-07-08", "2016-01-09", "2017-05-27", "2024-05-24", "2020-08-24", "2021-09-17", "2021-10-08",
                 "2013-12-01"}
        self.assertTrue(named <= {str(d.date()) for _, d in rules.boundary_dates()})

    def test_ins_regime_boundaries(self):
        d = pd.DatetimeIndex(["2015-07-07", "2015-07-08", "2016-01-08", "2016-01-09", "2016-01-11", "2017-05-26",
                              "2017-05-27", "2017-05-31", "2024-05-23", "2024-05-24"])
        np.testing.assert_array_equal(rules.ins_regime(d), [0, 1, 1, 2, 2, 2, 3, 3, 3, 4])
        starts = sorted(x for k, x in rules.boundary_dates() if k == "ins_regime")
        self.assertEqual([str(x.date()) for x in starts], ["2015-07-08", "2016-01-09", "2017-05-27", "2024-05-24"])
        for k, x in enumerate(starts):
            dd = pd.DatetimeIndex([x - pd.Timedelta(days=1), x])
            np.testing.assert_array_equal(rules.ins_regime(dd), [k, k + 1])
        self.assertTrue(np.isnan(rules.ins_regime(pd.DatetimeIndex(["2026-07-01"]))[0]))

    def test_top5_regime_is_three_valued(self):
        """Ruling F-13."""
        d = pd.DatetimeIndex(["2012-06-01", "2013-11-29", "2013-12-01", "2013-12-02", "2021-09-16", "2021-09-17",
                              "2021-09-30", "2021-10-07", "2021-10-08", "2024-01-02"])
        sse = rules.lhb_top5_regime("sse", d)
        np.testing.assert_array_equal(sse[:5], [0, 0, 0, 0, 0])               # three names before the notice
        self.assertTrue(np.isnan(sse[5:8]).all())                             # 2021-09-17 .. 2021-10-07: unknown
        np.testing.assert_array_equal(sse[8:], [1, 1])
        szse = rules.lhb_top5_regime("szse", d)
        self.assertTrue(np.isnan(szse[:2]).all())                             # before 2013-12-01: unknown
        np.testing.assert_array_equal(szse[2:], [1] * 8)

    def test_threshold_regime_boundaries(self):
        d = pd.DatetimeIndex(["2020-08-21", "2020-08-23", "2020-08-24"])
        np.testing.assert_array_equal(rules.lhb_threshold_regime("chinext", d), [0, 0, 1])
        np.testing.assert_array_equal(rules.lhb_threshold_regime("main", d), [0, 0, 0])
        np.testing.assert_array_equal(rules.lhb_threshold_regime("star", d), [1, 1, 1])
        t = rules.lhb_thresholds("chinext", d)
        np.testing.assert_array_equal(t["dev"], [0.07, 0.07, 0.15])
        np.testing.assert_array_equal(t["amp"], [0.15, 0.15, 0.30])
        np.testing.assert_array_equal(t["turn"], [0.20, 0.20, 0.30])
        m = rules.lhb_thresholds("main", d)
        self.assertEqual((m["dev"][0], m["amp"][0], m["turn"][0]), (0.07, 0.15, 0.20))

    def test_first_trading_rows(self):
        cal = TradingCalendar(pd.bdate_range("2021-03-01", periods=60))
        dates = cal.days[10:50]
        # listing day = first row: the first 5 rows
        np.testing.assert_array_equal(np.nonzero(rules.first_trading_rows(dates, dates[0], cal))[0], [0, 1, 2, 3, 4])
        np.testing.assert_array_equal(np.nonzero(rules.first_trading_rows(dates, dates[0]))[0], [0, 1, 2, 3, 4])
        # listed 2 trading days before the history starts: rows 0..2 are trading days 3, 4, 5 of the name
        np.testing.assert_array_equal(np.nonzero(rules.first_trading_rows(dates, cal.days[8], cal))[0], [0, 1, 2])
        # listed long before: nothing
        self.assertFalse(rules.first_trading_rows(dates, "2010-01-04", cal).any())
        self.assertFalse(rules.first_trading_rows(dates, cal.days[0], cal).any())
        # listing day unknown: the first 5 rows (it cannot be excluded that the history starts at the listing)
        np.testing.assert_array_equal(np.nonzero(rules.first_trading_rows(dates, None, cal))[0], [0, 1, 2, 3, 4])
        # no board and no date of a registration reform enters: the signature has neither
        import inspect
        self.assertEqual(list(inspect.signature(rules.first_trading_rows).parameters), ["dates", "ipo_date", "cal"])


class TestRO(unittest.TestCase):
    def _bars(self, rows):
        idx = pd.bdate_range("2021-03-01", periods=len(rows))
        df = pd.DataFrame(rows, columns=["close", "high", "low", "preclose", "V", "amount", "traded", "is_st"], index=idx)
        df["aclose"] = df["close"]
        df["present"] = True
        return df

    def test_trigger_and_limit_counts_hand(self):
        base = [10.0, 10.1, 9.9, 10.0, 0.01, 1e6, True, False]
        rows = [list(base) for _ in range(62)]
        rows[-1] = [11.0, 11.0, 10.0, 10.0, 0.25, 9e6, True, False]      # +10% limit-up, amp 10%, turnover 25%
        rows[-3] = [9.0, 10.0, 8.6, 10.0, 0.05, 2e6, True, False]        # -10% limit-down, amp (10-8.6)/8.6 = 16.3%
        b = self._bars(rows)
        ir = pd.Series(0.0, index=b.index)
        f = controls.ro_on_data_dates(b, "sh.600001", ir, ipo_date="2015-01-05").iloc[-1]
        self.assertEqual(f["ro_limit_up_cnt_1"], 1.0)
        self.assertEqual(f["ro_limit_up_cnt_5"], 1.0)
        self.assertEqual(f["ro_limit_dn_cnt_1"], 0.0)
        self.assertEqual(f["ro_limit_dn_cnt_5"], 1.0)
        self.assertEqual(f["ro_trig_devup_cnt_1"], 1.0)
        self.assertEqual(f["ro_trig_devdn_cnt_5"], 1.0)
        self.assertEqual(f["ro_trig_amp_cnt_1"], 0.0)       # (11 - 10) / 10 = 10% < 15%
        self.assertEqual(f["ro_trig_amp_cnt_5"], 1.0)
        self.assertEqual(f["ro_trig_turn_cnt_1"], 1.0)
        self.assertEqual(f["ro_trig_turn_cnt_20"], 1.0)
        self.assertEqual(f["ro_trig_cum3_cnt_1"], 0.0)      # -10% + 0 + 10% = 0
        self.assertAlmostEqual(f["ro_amp_1"], 0.10)
        self.assertAlmostEqual(f["ro_amp_max_5"], 0.14)
        self.assertAlmostEqual(f["ro_turn_max_5"], 0.25)
        self.assertAlmostEqual(f["ro_amt_max_to_mean60_1"], 9e6 / ((58 * 1e6 + 2e6 + 9e6) / 60))
        self.assertAlmostEqual(f["ro_xret_1"], 0.1)
        self.assertEqual(f["ro_lhb_thr15"], 0.0)

    def test_deviation_uses_index_and_star_uses_raw_change(self):
        base = [10.0, 10.1, 9.9, 10.0, 0.01, 1e6, True, False]
        rows = [list(base) for _ in range(25)]
        rows[-1] = [10.9, 10.9, 10.0, 10.0, 0.01, 1e6, True, False]      # +9%
        b = self._bars(rows)
        ir = pd.Series(0.0, index=b.index)
        ir.iloc[-1] = 0.03                                               # deviation 6% < 7%
        f = controls.ro_on_data_dates(b, "sh.600001", ir).iloc[-1]
        self.assertEqual(f["ro_trig_devup_cnt_1"], 0.0)
        ir.iloc[-1] = 0.01                                               # deviation 8%
        self.assertEqual(controls.ro_on_data_dates(b, "sh.600001", ir).iloc[-1]["ro_trig_devup_cnt_1"], 1.0)
        g = controls.ro_on_data_dates(b, "sh.688001", ir).iloc[-1]       # STAR: needs a raw +15%
        self.assertEqual(g["ro_trig_devup_cnt_1"], 0.0)
        self.assertEqual(g["ro_lhb_thr15"], 1.0)
        # without an index the deviation triggers are NaN, not 0
        h = controls.ro_on_data_dates(b, "sh.600001", None).iloc[-1]
        self.assertTrue(np.isnan(h["ro_trig_devup_cnt_1"]))
        self.assertEqual(h["ro_trig_turn_cnt_1"], 0.0)

    def test_limit_counts_nan_over_first_five_trading_days(self):
        """FEA-7 (c) / ruling F-20: whatever the board and the listing date."""
        base = [10.0, 10.1, 9.9, 10.0, 0.01, 1e6, True, False]
        rows = [list(base) for _ in range(40)]
        rows[2] = [11.0, 11.0, 10.0, 10.0, 0.25, 9e6, True, False]       # a limit-up close on trading day 3
        rows[30] = [11.0, 11.0, 10.0, 10.0, 0.25, 9e6, True, False]
        b = self._bars(rows)
        ir = pd.Series(0.0, index=b.index)
        cal = TradingCalendar(pd.bdate_range("2021-02-01", periods=120))
        for code in ("sh.600001", "sz.300001", "sh.688001", "sz.000001"):
            f = controls.ro_on_data_dates(b, code, ir, ipo_date=b.index[0], cal=cal)
            for side in ("up", "dn"):
                for w in (1, 5, 20):
                    c = f[f"ro_limit_{side}_cnt_{w}"].values
                    self.assertTrue(np.isnan(c[:w + 4]).all(), (code, side, w))      # window touches rows 0..4
                    self.assertTrue(np.isfinite(c[w + 4:]).all(), (code, side, w))
            self.assertEqual(f["ro_limit_up_cnt_1"].iloc[5], 0.0)
            # the planted limit-up of row 2 is never counted (it lies in the first five days) ...
            self.assertEqual(f["ro_limit_up_cnt_20"].iloc[24], 0.0)
            # ... the other controls are not affected by the rule
            # (turnover 25%: above the 20% criterion of the main board, below the 30% criterion that the
            # calendar gives ChiNext in 2021 and STAR)
            self.assertEqual(f["ro_trig_turn_cnt_1"].iloc[2], 1.0 if code in ("sh.600001", "sz.000001") else 0.0)
            self.assertTrue(np.isfinite(f["ro_amp_1"].iloc[0]))
        f = controls.ro_on_data_dates(b, "sh.600001", ir, ipo_date=b.index[0], cal=cal)
        self.assertEqual(f["ro_limit_up_cnt_1"].iloc[30], 1.0)           # 10% band on the main board
        # a name listed long before the history starts: no NaN from this rule
        g = controls.ro_on_data_dates(b, "sh.600001", ir, ipo_date="2001-01-02", cal=cal)
        self.assertEqual(g["ro_limit_up_cnt_1"].iloc[2], 1.0)
        self.assertTrue(np.isfinite(g["ro_limit_up_cnt_1"].values).all())

    def test_regime_columns(self):
        d = pd.DatetimeIndex(["2013-11-29", "2015-07-08", "2021-09-20", "2021-10-08", "2026-06-30", "2026-07-01"])
        a = controls.ro_regime_columns(d, "sh.600001")
        self.assertEqual(list(a["ro_exch_sse"]), [1.0] * 6)
        np.testing.assert_array_equal(a["ro_lhb_top5"].values[[0, 1, 3, 4]], [0, 0, 1, 1])
        self.assertTrue(np.isnan(a["ro_lhb_top5"].values[2]))             # SSE unknown interval
        self.assertTrue(np.isnan(a["ro_lhb_top5"].values[5]))             # outside the calendar window
        z = controls.ro_regime_columns(d, "sz.000001")
        self.assertTrue(np.isnan(z["ro_lhb_top5"].values[0]))             # SZSE before 2013-12-01
        np.testing.assert_array_equal(z["ro_lhb_top5"].values[1:5], [1, 1, 1, 1])
        reg = a[[f"ro_ins_regime_{k}" for k in range(5)]].values
        np.testing.assert_array_equal(reg[:5].sum(axis=1), [1, 1, 1, 1, 1])     # exactly one regime per day
        np.testing.assert_array_equal(reg[:5].argmax(axis=1), [0, 1, 3, 3, 4])
        self.assertTrue(np.isnan(reg[5]).all())

    def test_on_synthetic_bars_ranges(self):
        cal = synth.make_calendar()
        b = prepare_bars(synth.make_raw_bars("sh.600001", cal, seed=4, n_rows=500), cal)
        ir = pd.Series(0.0, index=b.index)
        f = controls.ro_on_data_dates(b, "sh.600001", ir)
        for w in (1, 5, 20):
            for k in ("limit_up", "limit_dn", "trig_devup", "trig_turn"):
                x = f[f"ro_{k}_cnt_{w}"].dropna()
                self.assertTrue(((x >= 0) & (x <= w)).all())
        self.assertGreater(f["ro_limit_up_cnt_20"].max(), 0)             # the generator plants limit-up closes


if __name__ == "__main__":
    unittest.main()

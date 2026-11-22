"""Z_H: hand-computed examples and property tests on synthetic data.

PLAN v0.7 primary definitions (rulings F-2, F-3): CGO with the original's
one-period lag; chips without initial mass, renormalised. Where an expected
value below differs from the v0.6 test file, the DEFINITION changed (task
list FEA-1, FEA-2, FEA-4), not a tolerance: each new expectation is computed
by hand from the new definition in the comment next to it."""
import unittest

import numpy as np
import pandas as pd

from features import zh
from features.bars import prepare_bars
from features.tests import synth


def _bars(o, h, l, c, v, traded=None):
    n = len(c)
    idx = pd.bdate_range("2020-01-01", periods=n)
    return pd.DataFrame({"aopen": np.asarray(o, float), "ahigh": np.asarray(h, float), "alow": np.asarray(l, float),
                         "aclose": np.asarray(c, float), "V": np.asarray(v, float),
                         "traded": np.ones(n, bool) if traded is None else traded}, index=idx)


class TestCGO(unittest.TestCase):
    def test_hand_example(self):
        # rows 0..2: weights day3 0.1; day2 0.2*0.9 = 0.18; day1 0.5*0.8*0.9 = 0.36; k = 0.64
        # sum w P = 0.36*10 + 0.18*12 + 0.1*11 = 6.86
        p = np.array([10.0, 12.0, 11.0, 13.0])
        v = np.array([0.5, 0.2, 0.1, 0.3])
        rp = zh.reference_price(p, v, 3)
        self.assertTrue(np.isnan(rp[:2]).all())
        self.assertAlmostEqual(rp[2], 6.86 / 0.64, places=12)
        # PRIMARY (v0.7): as of data date s = row 3 (decision day t = next), CGO = (P_{t-2} - RP_{t-1}) / P_{t-2}
        # with P_{t-2} = p[2] = 11 and RP_{t-1} built from rows 0..2
        g = zh.cgo(p, v, 3)
        self.assertTrue(np.isnan(g[:3]).all())                      # needs n + 1 = 4 rows
        self.assertAlmostEqual(g[3], (11 - 6.86 / 0.64) / 11, places=12)
        self.assertEqual(g[3], zh.cgo(p, v, 3, skip=1)[3])          # the default IS the lagged form
        # VARIANT no-lag (v0.6 wording): (P_{t-1} - RP_t) / P_{t-1}
        g0 = zh.cgo(p, v, 3, skip=0)
        self.assertAlmostEqual(g0[2], (11 - 6.86 / 0.64) / 11, places=12)
        # rows 1..3: weights day4 0.3; day3 0.1*0.7 = 0.07; day2 0.2*0.9*0.7 = 0.126; k = 0.496
        rp3 = (0.3 * 13 + 0.07 * 11 + 0.126 * 12) / 0.496
        self.assertAlmostEqual(g0[3], (13 - rp3) / 13, places=12)

    def test_weights_plus_survivor_mass_sum_to_one(self):
        rng = np.random.default_rng(1)
        vw = rng.uniform(0, 0.3, size=(50, 250))
        w = zh.decay_weights(vw)
        np.testing.assert_allclose(w.sum(axis=1) + np.prod(1 - vw, axis=1), 1.0, rtol=0, atol=1e-12)
        self.assertTrue((w >= 0).all())

    def test_zero_when_price_equals_reference_price(self):
        rng = np.random.default_rng(2)
        v = rng.uniform(0.001, 0.2, 400)
        g = zh.cgo(np.full(400, 7.5), v, 250)
        self.assertTrue(np.isnan(g[:250]).all())                    # primary warm-up: 251 rows
        np.testing.assert_allclose(g[250:], 0.0, atol=1e-14)
        g0 = zh.cgo(np.full(400, 7.5), v, 250, skip=0)
        self.assertTrue(np.isnan(g0[:249]).all())                   # no-lag variant: 250 rows
        np.testing.assert_allclose(g0[249:], 0.0, atol=1e-14)

    def test_reference_price_inside_window_range_and_scale_invariant(self):
        rng = np.random.default_rng(3)
        p = 10 * np.exp(rng.normal(0, 0.02, 600).cumsum())
        v = rng.uniform(0, 0.1, 600)
        rp = zh.reference_price(p, v, 250)
        for i in range(249, 600, 37):
            w = p[i - 249:i + 1]
            self.assertTrue(w.min() - 1e-12 <= rp[i] <= w.max() + 1e-12)
        np.testing.assert_allclose(zh.cgo(p, v, 250), zh.cgo(3.7 * p, v, 250), rtol=1e-10, atol=1e-12, equal_nan=True)

    def test_suspended_day_contributes_zero_and_full_turnover_resets(self):
        p = np.array([10.0, 99.0, 12.0, 11.0])
        v = np.array([0.3, 0.0, 0.2, 0.1])
        # the day with V = 0 has weight 0: same RP as if its price were anything
        a = zh.reference_price(p, v, 4)[3]
        p2 = p.copy(); p2[1] = 1.0
        self.assertEqual(a, zh.reference_price(p2, v, 4)[3])
        # V = 1 on day 3: nothing older survives
        v3 = np.array([0.3, 0.4, 1.0, 0.1])
        rp = zh.reference_price(p, v3, 4)[3]
        self.assertAlmostEqual(rp, (0.9 * 12 + 0.1 * 11) / 1.0, places=12)

    def test_no_trading_in_window_is_nan(self):
        self.assertTrue(np.isnan(zh.reference_price(np.ones(5), np.zeros(5), 5)[-1]))

    def test_turnover_cap_modes(self):
        v = np.array([0.2, 1.3, -0.1, 0.5])
        capped, n = zh.cap_turnover(v, "cap")
        self.assertEqual(n, 1)
        np.testing.assert_array_equal(capped, [0.2, 1.0, np.nan, 0.5])
        dropped, _ = zh.cap_turnover(v, "nan")
        self.assertTrue(np.isnan(dropped[1]))
        self.assertEqual(v[1], 1.3)        # input not modified

    def test_primary_is_nolag_variant_shifted_one_row(self):
        rng = np.random.default_rng(4)
        p = 10 * np.exp(rng.normal(0, 0.02, 300).cumsum())
        v = rng.uniform(0, 0.1, 300)
        prim, nolag = zh.cgo(p, v, 250), zh.cgo(p, v, 250, skip=0)
        np.testing.assert_array_equal(prim[250:], nolag[249:-1])    # bit for bit
        self.assertTrue(np.isnan(prim[249]) and np.isfinite(nolag[249]))

    def test_columns_primary_and_variants(self):
        cal = synth.make_calendar()
        b = prepare_bars(synth.make_raw_bars("sh.600001", cal, seed=2, n_rows=560), cal)
        z = zh.zh_on_data_dates(b, cal, weekly=False)
        p, v = b["aclose"].values, zh.cap_turnover(b["V"].values)[0]
        np.testing.assert_array_equal(z["zh_cgo_250"].values, zh.cgo(p, v, 250, skip=1))
        np.testing.assert_array_equal(z["zh_cgo_250_nolag"].values, zh.cgo(p, v, 250, skip=0))
        np.testing.assert_array_equal(z["zh_cgo_500"].values, zh.cgo(p, v, 500, skip=1))
        self.assertNotIn("zh_cgo_250_lag1", z.columns)
        self.assertEqual(int(z["zh_cgo_250"].notna().values.argmax()), 250)        # 251 rows
        self.assertEqual(int(z["zh_cgo_250_nolag"].notna().values.argmax()), 249)  # 250 rows
        self.assertEqual(int(z["zh_cgo_500"].notna().values.argmax()), 500)        # 501 rows
        self.assertEqual(zh.PRIMARY, ["zh_cgo_250", "zh_chip_pr", "zh_chip_cost_gap", "zh_chip_band90",
                                      "zh_chip_band70", "zh_chip_overhead", "zh_ato_20_250", "zh_ato_short_20"])
        self.assertEqual(sorted(zh.VARIANTS), sorted(["zh_cgo_500", "zh_cgo_250_nolag", "zh_cgo_w260",
                                                      "zh_chip_cost_gap_median", "zh_ato_20_250_log"]))
        # ATO primary is the plain ratio, the log is the variant
        np.testing.assert_array_equal(z["zh_ato_20_250"].values, zh.abnormal_turnover(b["V"].values))
        la = z["zh_ato_20_250_log"].dropna()
        np.testing.assert_allclose(la.values, np.log(z.loc[la.index, "zh_ato_20_250"].values), rtol=0, atol=0)
        # the chip columns are the 'renormalise' statistics
        c = zh.chip_stats(b, init="renormalise")
        np.testing.assert_array_equal(z["zh_chip_pr"].values, c["pr"].values)
        self.assertEqual(z.attrs["chip_init"], "renormalise")

    @staticmethod
    def _weekly_brute(p, v, dates, cal, i, n_weeks):
        """Literal transcription for row i, written independently of zh.cgo_weekly: list the completed weeks,
        take w0 = the last one, R from the n_weeks weeks before w0, price of week w0-1."""
        iso = dates.isocalendar()
        wk = iso["year"].values * 100 + iso["week"].values
        ciso = cal.days.isocalendar()
        cwk = ciso["year"].values * 100 + ciso["week"].values
        weeks = []                                          # (weekly turnover, weekly price) of completed weeks
        for w in pd.unique(wk):
            rows = np.nonzero(wk == w)[0]
            last_market_day = cal.days[cwk == w].max()
            if rows[-1] <= i and dates[rows[-1]] == last_market_day:
                weeks.append((min(v[rows].sum(), 1.0), p[rows[-1]]))
        if len(weeks) < n_weeks + 1:
            return np.nan
        w0 = len(weeks) - 1                                 # last completed week
        hist = weeks[w0 - n_weeks:w0]                       # weeks w0-n .. w0-1
        r = 0.0
        k = 0.0
        for n in range(1, n_weeks + 1):                     # eq. (25): n = 1 is week w0-1
            wgt = hist[-n][0]
            for tau in range(1, n):
                wgt *= 1.0 - hist[-n + tau][0]
            r += wgt * hist[-n][1]
            k += wgt
        p_prev = hist[-1][1]                                # P_{w0-1}
        return (p_prev - r / k) / p_prev

    def test_weekly_variant_is_literal_transcription(self):
        cal = synth.make_calendar(n=1700)
        rng = np.random.default_rng(5)
        n = 1600
        dates = cal.days[:n]
        p = 10 * np.exp(rng.normal(0, 0.02, n).cumsum())
        v = rng.uniform(0, 0.02, n)
        g = zh.cgo_weekly(p, v, dates, cal, n_weeks=260)
        self.assertTrue(np.isfinite(g[-1]))
        for i in (n - 1, n - 2, n - 7, n - 33, 1400, 1333):
            self.assertAlmostEqual(g[i], self._weekly_brute(p, v, dates, cal, i, 260), places=12, msg=str(i))
        # small n_weeks: every row against the brute force, including the warm-up (261 -> n_weeks + 1 weeks)
        g8 = zh.cgo_weekly(p[:120], v[:120], dates[:120], cal, n_weeks=8)
        for i in range(120):
            b = self._weekly_brute(p[:120], v[:120], dates[:120], cal, i, 8)
            if np.isnan(b):
                self.assertTrue(np.isnan(g8[i]), i)
            else:
                self.assertAlmostEqual(g8[i], b, places=12, msg=str(i))
        self.assertTrue(np.isnan(g8).any() and np.isfinite(g8).any())

    def test_weekly_variant_constant_within_a_decision_week_and_warmup(self):
        cal = synth.make_calendar(n=1700)
        rng = np.random.default_rng(15)
        n = 1600
        dates = cal.days[:n]
        p = 10 * np.exp(rng.normal(0, 0.02, n).cumsum())
        v = rng.uniform(0, 0.02, n)
        g = zh.cgo_weekly(p, v, dates, cal, n_weeks=260)
        dec = cal.next_index(dates)                         # decision day of each row
        iso = dec.isocalendar()
        dwk = iso["year"].values * 100 + iso["week"].values
        s = pd.Series(g).groupby(dwk)
        self.assertTrue((s.nunique(dropna=False) == 1).all())      # one value per calendar week of decision days
        self.assertGreater(pd.Series(g).dropna().nunique(), 30)    # and it does change from week to week
        # warm-up: the first value appears when 261 weeks are complete, not 260
        diso = dates.isocalendar()
        wk = diso["year"].values * 100 + diso["week"].values
        first = int(np.isfinite(g).argmax())
        n_complete = len(pd.unique(wk[:first + 1]))         # weeks up to and including the row's own week
        cw = cal.days.isocalendar()
        last_day = cal.days[(cw["year"].values * 100 + cw["week"].values) == wk[first]].max()
        self.assertEqual(dates[first], last_day)            # the row that completes a week
        self.assertEqual(n_complete, 261)
        # it does not use the daily price of t-1: changing the prices of the current (incomplete) week and of
        # week w0 itself leaves the value unchanged
        i = n - 1
        rows_w0_on = np.nonzero(wk >= np.unique(wk[:i + 1])[-2])[0]
        p2 = p.copy()
        p2[rows_w0_on] *= 1.37
        g2 = zh.cgo_weekly(p2, v, dates, cal, n_weeks=260)
        self.assertEqual(g[i - 1], g2[i - 1])


class TestChips(unittest.TestCase):
    def test_triangular_cdf(self):
        x = np.array([8.0, 9.0, 9.5, 10.0, 10.5, 11.0, 12.0])
        c = zh.tri_cdf(x, np.array([9.0]), np.array([11.0]), np.array([10.0]))[0]
        np.testing.assert_allclose(c, [0, 0, 0.125, 0.5, 0.875, 1, 1])
        # peak at the low / at the high / one-price day
        c = zh.tri_cdf(np.array([9.0, 10.0, 11.0]), np.array([9.0]), np.array([11.0]), np.array([9.0]))[0]
        np.testing.assert_allclose(c, [0, 0.75, 1])
        c = zh.tri_cdf(np.array([9.0, 10.0, 11.0]), np.array([9.0]), np.array([11.0]), np.array([11.0]))[0]
        np.testing.assert_allclose(c, [0, 0.25, 1])
        c = zh.tri_cdf(np.array([9.9, 10.0, 10.1]), np.array([10.0]), np.array([10.0]), np.array([10.0]))[0]
        np.testing.assert_allclose(c, [0, 1, 1])

    def test_hand_example_two_days(self):
        # day 1: [9, 11], mode 10, V = .5 ; day 2: [10, 12], mode 11, V = .5 ; P = 11
        # decay weights: day 2 .5, day 1 .5 * .5 = .25; never-traded share r0 = .25
        b = _bars(o=[10, 11], h=[11, 12], l=[9, 10], c=[10, 11], v=[0.5, 0.5])
        # PRIMARY (v0.7, F-3) 'renormalise': no initial mass, divide by the mass turned over = .75
        r = zh.chip_stats(b, window=2, grid=150).iloc[-1]                          # default
        self.assertEqual(r["pr"], zh.chip_stats(b, window=2, grid=150, init="renormalise").iloc[-1]["pr"])
        # below P = 11: all of day 1 (.25) + the lower half of day 2 (.5 * .5)
        self.assertAlmostEqual(r["pr"], (0.25 + 0.25) / 0.75, places=9)
        # mean cost = (.25 * 10 + .5 * 11) / .75
        self.assertAlmostEqual(r["cost_gap"], (11 - (0.25 * 10 + 0.5 * 11) / 0.75) / 11, places=12)
        # (11, 12.1]: the upper half of day 2 = .25 of mass
        self.assertAlmostEqual(r["overhead"], 0.25 / 0.75, places=9)
        # SENSITIVITY (v0.6 placeholder) 'uniform_first_day': r0 = .25 uniform on [9, 11], total mass 1
        s = zh.chip_stats(b, window=2, grid=150, init="uniform_first_day").iloc[-1]
        self.assertAlmostEqual(s["pr"], 0.25 + 0.25 + 0.5 * 0.5, places=9)       # = 0.75
        self.assertAlmostEqual(s["cost_gap"], (11 - (0.25 * 10 + 0.25 * 10 + 0.5 * 11)) / 11, places=12)
        self.assertAlmostEqual(s["overhead"], 0.25, places=9)                      # upper half of day 2

    def test_total_mass_and_monotone(self):
        rng = np.random.default_rng(6)
        W = 210
        lo = rng.uniform(9, 10, W); hi = lo + rng.uniform(0, 1, W); hi[5] = lo[5]      # one one-price day
        md = lo + (hi - lo) * rng.uniform(0, 1, W)
        v = rng.uniform(0, 0.2, W)
        w = zh.decay_weights(v[None, :])[0]
        r0 = np.prod(1 - v)
        # primary: total = mass turned over = 1 - r0; the normalised cumulative mass ends at exactly 1
        edges, cum, total = zh.chip_distribution(lo, hi, md, w, r0, 150)
        self.assertAlmostEqual(total, 1 - r0, places=12)
        self.assertEqual(cum[-1] / total, 1.0)
        self.assertEqual(cum[0], 0.0)
        self.assertTrue((np.diff(cum) >= 0).all())
        # sensitivity: total mass exactly 1
        _, cum2, total2 = zh.chip_distribution(lo, hi, md, w, r0, 150, "uniform_first_day")
        self.assertAlmostEqual(total2, 1.0, places=12)
        self.assertAlmostEqual(cum2[-1], 1.0, places=12)
        self.assertTrue((np.diff(cum2) >= 0).all())
        with self.assertRaises(ValueError):
            zh.chip_distribution(lo, hi, md, w, r0, 150, "something else")

    def test_two_initialisations_agree_when_the_window_turned_over_completely(self):
        # a day with V = 1 inside every window: nothing older survives, r0 = 0, so there is no initial mass to place
        rng = np.random.default_rng(16)
        n = 40
        c = 10 + rng.uniform(-1, 1, n).cumsum() * 0.1
        o = c + rng.uniform(-0.1, 0.1, n)
        h = np.maximum(o, c) + rng.uniform(0, 0.2, n)
        l = np.minimum(o, c) - rng.uniform(0, 0.2, n)
        v = rng.uniform(0.01, 0.2, n)
        v[::5] = 1.0                                         # every window of 6 rows contains a full-turnover day
        b = _bars(o, h, l, c, v)
        a = zh.chip_stats(b, window=6, init="renormalise")
        u = zh.chip_stats(b, window=6, init="uniform_first_day")
        self.assertEqual(int(a["pr"].notna().sum()), n - 5)
        pd.testing.assert_frame_equal(a, u, check_exact=False, rtol=0, atol=1e-12)
        # and they differ when it did not (the sensitivity is a different definition, not a no-op)
        v2 = np.full(n, 0.01)
        a2 = zh.chip_stats(_bars(o, h, l, c, v2), window=6, init="renormalise")
        u2 = zh.chip_stats(_bars(o, h, l, c, v2), window=6, init="uniform_first_day")
        self.assertGreater((a2["pr"] - u2["pr"]).abs().max(), 1e-3)

    def test_zero_turnover_window_is_nan_under_renormalise(self):
        n = 12
        z = np.full(n, 10.0)
        v = np.r_[0.1, np.zeros(n - 1)]                      # first row traded, then nothing turns over
        b = _bars(z, z + 1, z - 1, z, v)
        a = zh.chip_stats(b, window=5, init="renormalise")
        self.assertTrue(np.isfinite(a["pr"].iloc[4]))        # window rows 0..4 contains the traded mass
        self.assertTrue(a.iloc[5:].isna().all().all())       # windows with total turned-over mass 0
        u = zh.chip_stats(b, window=5, init="uniform_first_day")
        self.assertTrue(np.isfinite(u["pr"].iloc[8]))        # the sensitivity places the never-traded mass

    def test_grid_quantiles_against_fine_grid(self):
        cal = synth.make_calendar()
        b = prepare_bars(synth.make_raw_bars("sh.600001", cal, seed=8, n_rows=320), cal)
        coarse = zh.chip_stats(b, grid=150).dropna()
        fine = zh.chip_stats(b, grid=6000).dropna()
        self.assertGreater(len(coarse), 50)
        # one cell of the coarse grid is (range / 150); allow two cells relative to price
        for k in ("pr", "band90", "band70", "overhead", "cost_gap_median"):
            self.assertLess((coarse[k] - fine[k]).abs().max(), 0.03, msg=k)
        np.testing.assert_allclose(coarse["cost_gap"], fine["cost_gap"], rtol=0, atol=1e-12)   # closed form
        self.assertTrue(((coarse["pr"] >= 0) & (coarse["pr"] <= 1)).all())
        self.assertTrue((coarse["band90"] >= coarse["band70"]).all())
        self.assertTrue((coarse["overhead"] >= 0).all())

    def test_constant_price_history(self):
        n = 230
        b = _bars(o=np.full(n, 10.0), h=np.full(n, 10.0), l=np.full(n, 10.0), c=np.full(n, 10.0), v=np.full(n, 0.05))
        s = zh.chip_stats(b).iloc[-1]
        self.assertAlmostEqual(s["cost_gap"], 0.0, places=12)
        self.assertAlmostEqual(s["band90"], 0.0, places=12)

    def test_warmup_and_post_suspension_blank(self):
        cal = synth.make_calendar()
        b = prepare_bars(synth.make_raw_bars("sh.600001", cal, seed=9, n_rows=1000, long_suspension=True), cal)
        s = zh.chip_stats(b)
        self.assertTrue(s["pr"].iloc[:209].isna().all())
        self.assertTrue(np.isfinite(s["pr"].iloc[209]))
        blocked = zh._post_suspension_block(b["traded"].values, 105, 60)
        self.assertTrue(blocked.any())
        self.assertTrue(s.loc[blocked].isna().all().all())
        # the suspension is rows 600..729: blocked from row 705 (106th day) to 60 traded rows after resumption
        self.assertFalse(blocked[704])
        self.assertTrue(blocked[705])
        self.assertTrue(blocked[730])
        after = np.nonzero(b["traded"].values[730:])[0][:61] + 730
        self.assertTrue(blocked[after[59]])
        self.assertFalse(blocked[after[60]])

    def test_turnover_above_one_capped_or_window_dropped(self):
        cal = synth.make_calendar()
        b = prepare_bars(synth.make_raw_bars("sh.600001", cal, seed=3, n_rows=700), cal)
        i = int(np.argmax(b["V"].values > 1))
        cap = zh.chip_stats(b, v_mode="cap")
        nan = zh.chip_stats(b, v_mode="nan")
        self.assertTrue(np.isfinite(cap["pr"].iloc[i]))
        self.assertTrue(nan["pr"].iloc[i:i + 210].isna().all())
        self.assertTrue(np.isfinite(nan["pr"].iloc[i + 210]))


class TestATO(unittest.TestCase):
    def test_constant_turnover(self):
        v = np.full(300, 0.02)
        a = zh.abnormal_turnover(v)
        self.assertTrue(np.isnan(a[:249]).all())
        np.testing.assert_allclose(a[249:], 1.0)
        np.testing.assert_allclose(zh.abnormal_turnover_short(v)[20:], 0.0, atol=1e-15)

    def test_hand(self):
        v = np.r_[np.full(230, 0.01), np.full(20, 0.03)]
        a = zh.abnormal_turnover(v)[-1]
        self.assertAlmostEqual(a, 0.03 / ((230 * 0.01 + 20 * 0.03) / 250), places=12)
        s = zh.abnormal_turnover_short(np.r_[np.full(20, 0.01), 0.04])[-1]
        self.assertAlmostEqual(s, np.log(4.0), places=12)

    def test_zero_turnover_is_nan_not_inf(self):
        v = np.r_[np.full(20, 0.01), 0.0]
        self.assertTrue(np.isnan(zh.abnormal_turnover_short(v)[-1]))
        self.assertTrue(np.isnan(zh.abnormal_turnover(np.zeros(260))[-1]))


if __name__ == "__main__":
    unittest.main()

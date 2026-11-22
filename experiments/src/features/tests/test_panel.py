"""Panel-level pieces added for PLAN v0.7: ADV on traded days (FEA-8),
repaired rows and the diagnostic column (FEA-11), full-market assembly and
its report (TODO-F1)."""
import os
import tempfile
import unittest

import numpy as np
import pandas as pd

from features import panel, market_panel, registry, store, zo
from features.bars import prepare_bars
from features.tests import synth

FULL_WINDOW = "2026-06-30"      # synthetic data only: the end of the raw window as the explicit cut-off (C-8)


def _b(amount, traded=None):
    n = len(amount)
    idx = pd.bdate_range("2021-01-04", periods=n)
    amount = np.asarray(amount, dtype=float)
    tr = (amount > 0) if traded is None else np.asarray(traded, bool)
    return pd.DataFrame({"amount": amount, "traded": tr}, index=idx)


def _naive_adv(amount, traded, n=20):
    """Independent, deliberately slow reference: for each row, walk back and collect traded rows."""
    out = []
    for i in range(len(amount)):
        vals = []
        j = i
        while j >= 0 and len(vals) < n:
            if traded[j]:
                vals.append(0.0 if np.isnan(amount[j]) else amount[j])
            j -= 1
        m = sum(vals[::-1]) / len(vals) if vals else np.nan
        out.append(m if (vals and m > 0) else np.nan)
    return np.array(out)


class TestADV(unittest.TestCase):
    def test_hand(self):
        # rows: 100, 200, (not traded), 300 ; n = 2
        a = panel.adv_on_data_dates(_b([100.0, 200.0, 0.0, 300.0]), n=2).values
        np.testing.assert_array_equal(a, [100.0, 150.0, 150.0, 250.0])     # the suspended row is skipped, not a zero
        # fewer than n traded rows: the mean of those that exist; none: NaN
        a = panel.adv_on_data_dates(_b([0.0, 0.0, 50.0, 0.0, 70.0]), n=20).values
        self.assertTrue(np.isnan(a[:2]).all())
        np.testing.assert_array_equal(a[2:], [50.0, 50.0, 60.0])

    def test_twenty_traded_days_with_suspensions_inside(self):
        rng = np.random.default_rng(0)
        amt = rng.uniform(1e6, 5e6, 60)
        susp = [20, 21, 22, 30, 41]                          # 5 suspended rows inside the span
        amt[susp] = 0.0
        a = panel.adv_on_data_dates(_b(amt)).values
        i = 45
        traded_rows = [k for k in range(i + 1) if k not in susp][-20:]
        self.assertEqual(len(traded_rows), 20)
        self.assertLess(traded_rows[0], i - 19)              # the window reaches further back than 20 rows
        self.assertAlmostEqual(a[i], amt[traded_rows].mean(), places=6)

    def test_long_suspension_denominator_is_the_pre_suspension_mean(self):
        rng = np.random.default_rng(1)
        amt = np.r_[rng.uniform(1e6, 5e6, 40), np.zeros(35), rng.uniform(1e6, 5e6, 3)]
        a = panel.adv_on_data_dates(_b(amt)).values
        pre = amt[20:40].mean()
        np.testing.assert_allclose(a[40:75], pre, rtol=1e-15)          # throughout the suspension: unchanged
        self.assertTrue((a[40:75] == a[39]).all())
        self.assertAlmostEqual(a[75], (amt[21:40].sum() + amt[75]) / 20, places=6)    # first day back: 19 old + 1 new
        # the v0.6 definition (rows, suspended = 0) would have been near zero here
        self.assertGreater(a[75], 0.9 * min(pre, amt[75]))

    def test_against_naive_reference_and_engine_convention(self):
        rng = np.random.default_rng(2)
        n = 400
        amt = rng.uniform(1e5, 1e7, n)
        traded = rng.random(n) > 0.15
        traded[:7] = False
        amt[~traded] = 0.0
        amt[50] = np.nan                                     # a traded row with a missing amount counts as 0
        traded[50] = True
        got = panel.adv_on_data_dates(_b(amt, traded)).values
        exp = _naive_adv(amt, traded)
        self.assertTrue(np.isnan(got[:7]).all())
        np.testing.assert_allclose(got, exp, rtol=1e-12, equal_nan=True)

    def test_bitwise_independent_of_history_length_and_of_later_rows(self):
        rng = np.random.default_rng(3)
        n = 300
        amt = rng.uniform(1e5, 1e7, n)
        amt[rng.random(n) < 0.2] = 0.0
        full = panel.adv_on_data_dates(_b(amt)).values
        for cut in (25, 57, 140, 299):
            part = panel.adv_on_data_dates(_b(amt[:cut])).values
            self.assertTrue(np.array_equal(part.view(np.uint64), full[:cut].view(np.uint64)), cut)
        amt2 = amt.copy()
        amt2[200:] = rng.uniform(1e5, 1e7, 100)
        chg = panel.adv_on_data_dates(_b(amt2)).values
        self.assertTrue(np.array_equal(chg[:200].view(np.uint64), full[:200].view(np.uint64)))

    def test_lhb_denominator_in_the_panel_is_this_adv(self):
        cal = synth.make_calendar()
        code = "sh.600001"
        raw = synth.make_raw_bars(code, cal, seed=9, n_rows=1000, long_suspension=True)   # rows 600..729 suspended
        b = prepare_bars(raw, cal)
        adv = panel.adv_on_data_dates(b)
        self.assertEqual(adv.iloc[729], adv.iloc[599])                 # frozen through the suspension
        day = b.index[730]                                             # resumption day (an event day)
        tb = zo.ZOTables(
            pd.DataFrame([{"代码": "600001", "上榜日": day.date(), "龙虎榜净买额": 3e6, "龙虎榜买入额": 5e6,
                           "龙虎榜卖出额": 2e6, "龙虎榜成交额": 7e6, "市场总成交额": 1, "净买额占总成交比": 0.0,
                           "成交额占总成交比": 0.0, "上榜原因": "日涨幅偏离值达到7%的前五只证券"}]),
            pd.DataFrame(columns=["代码", "上榜日期", "买方机构数", "卖方机构数", "机构买入总额", "机构卖出总额",
                                  "机构买入净额", "上榜原因"]),
            pd.DataFrame(columns=["证券代码", "交易日期", "成交价", "折溢率", "成交量", "成交额", "成交额/流通市值"]),
            pd.DataFrame(columns=["SECURITY_CODE", "NOTICE_DATE", "DIRECTION", "CHANGE_NUM", "AFTER_CHANGE_RATE",
                                  "CHANGE_FREE_RATIO", "START_DATE", "END_DATE", "EITIME"]),
            {k: set(cal.days.strftime("%Y%m")) for k in ("lhb", "jg", "blk")} | {"ins": set(cal.days.strftime("%Y"))})
        f = panel.build_stock_features(code, raw, cal, cal.days[cal.pos(day) + 10], None, tb, groups=("Z_O",))
        t = cal.days[cal.pos(day) + 2]                                 # usable two days later
        # ADV_t: the 20 traded days ending t-1 = the resumption day, the day after, and 18 pre-suspension days
        self.assertEqual(f["zo_lhb_net_1"].loc[t], 3e6 / adv.iloc[731])
        self.assertTrue(np.isfinite(f["zo_lhb_net_1"].loc[t]))


class TestRepairedRows(unittest.TestCase):
    """FEA-11 (rulings F-18 / E-16): the library carries a repair flag set by the fetch pipeline; it repairs nothing."""

    def setUp(self):
        self.cal = synth.make_calendar()
        self.code = "sh.600001"
        self.full = synth.make_raw_bars(self.code, self.cal, seed=31, n_rows=620)
        self.k = 300
        self.missing = self.full.drop(index=self.k).reset_index(drop=True)
        rep = self.full.copy()
        rep["filled_from_xsrc"] = "0"
        rep.loc[self.k, "filled_from_xsrc"] = "1"
        self.repaired = rep
        self.t = self.cal.next(pd.to_datetime(self.full["date"]).max())

    def build(self, raw):
        return panel.build_stock_features(self.code, raw, self.cal, self.t, None, None,
                                          groups=("Z_H", "R_H-sum", "DIAG"))

    def test_unrepaired_missing_row_blanks_the_windows_and_nothing_is_filled(self):
        b = prepare_bars(self.missing, self.cal)
        self.assertEqual(b.attrs["n_missing_rows"], 1)
        self.assertEqual(b.attrs["n_filled_xsrc_rows"], 0)
        self.assertFalse(b["present"].iloc[self.k])
        self.assertTrue(np.isnan(b["close"].iloc[self.k]))                     # not carried forward
        f = self.build(self.missing)
        # a 250-row window statistic is NaN for every window that contains the missing row: rows k .. k+249
        self.assertTrue(f["rh_ma_gap_250"].iloc[self.k:self.k + 250].isna().all())
        self.assertTrue(np.isfinite(f["rh_ma_gap_250"].iloc[self.k - 1]))
        self.assertTrue(np.isfinite(f["rh_ma_gap_250"].iloc[self.k + 250]))
        # the primary CGO reads the 250 rows ending one row earlier: NaN for rows k+1 .. k+250
        self.assertTrue(np.isfinite(f["zh_cgo_250"].iloc[self.k]))
        self.assertTrue(f["zh_cgo_250"].iloc[self.k + 1:self.k + 251].isna().all())
        self.assertTrue(np.isfinite(f["zh_cgo_250"].iloc[self.k + 251]))
        # a two-point statistic is NaN only where one of its two rows is the missing one
        self.assertEqual(int(f["rh_ret_250"].iloc[self.k - 1:self.k + 252].isna().sum()), 2)
        self.assertEqual(f["diag_filled_xsrc_in_window"].sum(), 0.0)

    def test_repaired_row_is_an_ordinary_row_and_is_flagged(self):
        b = prepare_bars(self.repaired, self.cal)
        self.assertEqual((b.attrs["n_missing_rows"], b.attrs["n_filled_xsrc_rows"]), (0, 1))
        self.assertTrue(b["filled_xsrc"].iloc[self.k] and b["present"].iloc[self.k])
        f = self.build(self.repaired)
        g = self.build(self.full)                                              # the same rows without the flag column
        feat = [c for c in f.columns if not c.startswith("diag_")]
        pd.testing.assert_frame_equal(f[feat], g[feat])                        # the flag changes no feature value
        self.assertTrue(np.isfinite(f["rh_ma_gap_250"].iloc[self.k + 5]))      # 250-day windows are no longer NaN
        self.assertTrue(np.isfinite(f["zh_cgo_250"].iloc[self.k + 5]))
        d = f["diag_filled_xsrc_in_window"].values
        from features.config import DIAG_XSRC_WINDOW as W
        self.assertEqual(d[:self.k].sum(), 0.0)
        self.assertTrue((d[self.k:self.k + W] == 1.0).all())                   # rows whose last W rows contain it
        self.assertTrue((d[self.k + W:] == 0.0).all())
        self.assertEqual(g["diag_filled_xsrc_in_window"].sum(), 0.0)

    def test_diagnostic_column_is_not_a_model_feature(self):
        cat = registry.catalogue()
        row = cat[cat["name"] == "diag_filled_xsrc_in_window"].iloc[0]
        self.assertEqual((row["group"], row["role"]), ("DIAG", "diagnostic"))
        self.assertNotIn("DIAG", registry.FEATURE_GROUPS)
        self.assertEqual(len(registry.catalogue(include_diag=False)), 369)


class TestMarketPanel(unittest.TestCase):
    """TODO-F1: loop, storage, resume, strict coverage, report -- on a synthetic raw tree in a temporary folder."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = os.path.join(cls.tmp.name, "raw")
        cls.cal = synth.make_calendar()
        cls.codes = ["sh.600001", "sz.000002", "sz.300003", "sh.688004"]
        cls.raws = synth.write_raw_store(cls.root, cls.codes, cls.cal, n_rows=420, seed=40,
                                         missing_row={"sz.000002": 200})
        cls.out = os.path.join(cls.tmp.name, "panel")
        cls.man = market_panel.build_market_panel(cls.codes + ["sh.600999"], cls.out, root=cls.root, progress_every=0, data_cutoff=FULL_WINDOW)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_files_manifest_and_columns(self):
        man = self.man.set_index("code")
        self.assertEqual(man.loc["sh.600999", "status"], "no_bar_file")
        cat = registry.catalogue()["name"].tolist()
        for c in self.codes:
            self.assertEqual(man.loc[c, "status"], "ok", man.loc[c, "error"])
            f = pd.read_parquet(os.path.join(self.out, "features", c + ".parquet"))
            self.assertEqual(list(f.columns), cat)
            self.assertEqual(f.shape[1], 370)
            self.assertEqual(f.index.name, "decision_day")
            self.assertTrue((f.dtypes == np.float64).all())
            self.assertEqual(int(man.loc[c, "rows"]), len(f))
            self.assertEqual(int(man.loc[c, "n_inf"]), 0)
        self.assertEqual(int(man.loc["sz.000002", "n_missing_rows"]), 1)
        self.assertEqual(int(man.loc["sh.600001", "n_missing_rows"]), 0)

    def test_stored_values_equal_a_direct_build_bit_for_bit(self):
        st = store.RawStore(self.root, data_cutoff=FULL_WINDOW)
        cal, tb = st.calendar(), st.zo_tables()
        for c in self.codes[:2]:
            raw = st.raw_bars(c)
            t = cal.next(pd.to_datetime(raw["date"]).max())
            direct = panel.build_stock_features(c, raw, cal, t, st.raw_index(panel.proxy_index_code(c)), tb,
                                                ipo_date=st.ipo_date(c))
            stored = pd.read_parquet(os.path.join(self.out, "features", c + ".parquet"))
            direct = direct[stored.columns]
            a, b = direct.values.astype(np.float64), stored.values
            self.assertEqual(a.shape, b.shape)
            same = (np.isnan(a) & np.isnan(b)) | (a.view(np.uint64) == b.view(np.uint64))
            self.assertTrue(same.all())
            self.assertTrue(direct.index.equals(stored.index))

    def test_resume_skips_finished_names_and_parallel_gives_the_same_files(self):
        before = {c: os.path.getmtime(os.path.join(self.out, "features", c + ".parquet")) for c in self.codes}
        man2 = market_panel.build_market_panel(self.codes, self.out, root=self.root, progress_every=0, data_cutoff=FULL_WINDOW)
        after = {c: os.path.getmtime(os.path.join(self.out, "features", c + ".parquet")) for c in self.codes}
        self.assertEqual(before, after)
        self.assertEqual(list(man2["status"]), ["ok"] * 4)
        out2 = os.path.join(self.tmp.name, "panel_par")
        man3 = market_panel.build_market_panel(self.codes, out2, root=self.root, n_jobs=2, progress_every=0, data_cutoff=FULL_WINDOW)
        self.assertEqual(list(man3["code"]), self.codes)
        for c in self.codes:
            x = pd.read_parquet(os.path.join(self.out, "features", c + ".parquet"))
            y = pd.read_parquet(os.path.join(out2, "features", c + ".parquet"))
            self.assertEqual(x.shape, y.shape)
            a, b = x.values, y.values
            self.assertTrue(((np.isnan(a) & np.isnan(b)) | (a.view(np.uint64) == b.view(np.uint64))).all(), c)

    def test_cutoff_argument_truncates(self):
        out = os.path.join(self.tmp.name, "panel_cut")
        t = self.cal.days[250]
        market_panel.build_market_panel(self.codes[:1], out, root=self.root, cutoff=t, progress_every=0, data_cutoff=FULL_WINDOW)
        f = pd.read_parquet(os.path.join(out, "features", self.codes[0] + ".parquet"))
        self.assertEqual(f.index.max(), t)
        full = pd.read_parquet(os.path.join(self.out, "features", self.codes[0] + ".parquet")).loc[:t]
        a, b = f.values, full.values
        self.assertTrue(((np.isnan(a) & np.isnan(b)) | (a.view(np.uint64) == b.view(np.uint64))).all())

    def test_missing_zo_file_stops_the_run_in_strict_mode(self):
        root2 = os.path.join(self.tmp.name, "raw_gap")
        per = self.cal.days[100].strftime("%Y%m")
        synth.write_raw_store(root2, self.codes[:1], self.cal, n_rows=300, seed=40, drop_zo_period=("dzjy_mrmx", per))
        out = os.path.join(self.tmp.name, "panel_gap")
        with self.assertRaises(zo.MissingRawFile) as cm:
            market_panel.build_market_panel(self.codes[:1], out, root=root2, progress_every=0, data_cutoff=FULL_WINDOW)
        self.assertIn(per, str(cm.exception))
        self.assertFalse(os.path.exists(os.path.join(out, "features", self.codes[0] + ".parquet")))   # nothing built
        man = market_panel.build_market_panel(self.codes[:1], out, root=root2, zo_strict=False, progress_every=0, data_cutoff=FULL_WINDOW)
        self.assertEqual(man["status"].iloc[0], "ok")
        f = pd.read_parquet(os.path.join(out, "features", self.codes[0] + ".parquet"))
        gap = f.index[(f.index.strftime("%Y%m") == per)]
        self.assertTrue(np.isnan(f.loc[gap[-1], "zo_blk_ind_5"]))
        self.assertTrue(np.isfinite(f.loc[gap[-1], "zo_lhb_ind_5"]))

    def test_report(self):
        rep_dir = os.path.join(self.tmp.name, "rep")
        s = market_panel.panel_report(self.out, rep_dir)
        self.assertEqual((s["n_names_ok"], s["n_names_error"], s["n_names_no_bar_file"]), (4, 0, 1))
        self.assertEqual(s["n_columns"], 370)
        self.assertEqual(s["n_inf_total"], 0)
        self.assertEqual((s["names_with_missing_rows"], s["missing_rows_total"]), (1, 1))
        self.assertEqual(s["names_with_rows_filled_from_xsrc"], 0)
        miss = pd.read_csv(os.path.join(rep_dir, "panel_missing_by_year_feature.csv"))
        self.assertEqual(set(miss.columns), {"year", "feature", "group", "role", "n_rows", "n_nan", "nan_share"})
        self.assertEqual(miss.groupby("year")["feature"].nunique().unique().tolist(), [370])
        total = miss.groupby("year")["n_rows"].first().sum()
        self.assertEqual(int(total), s["rows_total"])
        # a hand check of one cell against the stored files
        y = int(miss["year"].iloc[0])
        n_nan = 0
        for c in self.codes:
            f = pd.read_parquet(os.path.join(self.out, "features", c + ".parquet"))
            n_nan += int(f.loc[f.index.year == y, "zh_cgo_250"].isna().sum())
        self.assertEqual(int(miss[(miss["year"] == y) & (miss["feature"] == "zh_cgo_250")]["n_nan"].iloc[0]), n_nan)
        w = pd.read_csv(os.path.join(rep_dir, "panel_warmup_by_feature.csv")).set_index("feature")
        self.assertEqual(w.loc["zh_cgo_250", "declared_warmup_rows"], 251)
        self.assertEqual(w.loc["b0_KMID", "n_names"], 4)
        self.assertEqual(w.loc["b0_KMID", "excess_min"], 0)                    # first value exactly at the declared row
        r = pd.read_csv(os.path.join(rep_dir, "panel_feature_ranges.csv")).set_index("feature")
        self.assertGreaterEqual(r.loc["zh_chip_pr", "min"], 0.0)
        self.assertLessEqual(r.loc["zh_chip_pr", "max"], 1.0)
        # the report holds no outcome variable
        for fn in os.listdir(rep_dir):
            if fn.endswith(".csv"):
                cols = set(pd.read_csv(os.path.join(rep_dir, fn), nrows=0).columns)
                self.assertFalse({c for c in cols if "fwd" in c.lower() or "label" in c.lower() or c.lower() == "ic"})


if __name__ == "__main__":
    unittest.main()

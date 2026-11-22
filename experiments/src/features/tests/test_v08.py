"""Tests of the v0.8 code changes of the feature library (experiments/IMPLEMENTATION_CHANGES_v0.8.md):

  C-3  three-day cumulative LHB threshold read from the rule calendar (RC-18 element cum3; PLAN v0.8 J-1)
  C-4  BLK premium recomputed from own bars with the plausibility rule (J-7, U64)
  C-6  FC-A4 in the feature library: no factor column, adjustflag 3 only, factor directory never opened (J-15)
  C-8  hard data cut-off of RawStore / prepare_bars / market_panel (U-PILOT)

Synthetic data only (temporary directories); expected values by hand."""
import inspect
import json
import os
import tempfile
import unittest

import numpy as np
import pandas as pd

from engine import datacut as dc
from engine import rule_calendar as rc
from features import config, controls, market_panel, registry, rules, store, zo
from features.bars import AdjustedDataError, prepare_bars
from features.tests import synth
from features.timing import TradingCalendar

CAL = TradingCalendar(pd.bdate_range("2020-01-01", periods=760))
ALL = np.ones(len(CAL), dtype=bool)
DEC = CAL.days[5:700]
LAST = CAL.days[700]
E = 400


def _blk(rows):
    return pd.DataFrame(rows, columns=["证券代码", "交易日期", "成交价", "折溢率", "成交量", "成交额", "成交额/流通市值"])


def _bars(close=10.0, preclose=10.0, traded=True):
    b = pd.DataFrame({"close": close, "preclose": preclose, "traded": traded, "is_st": False}, index=CAL.days)
    return b


def _names_and_floats(mod):
    """Identifiers and float literals of a module's CODE (docstrings and comments are not code)."""
    import ast
    tree = ast.parse(inspect.getsource(mod))
    names, floats = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            floats.add(node.value)
    return names, floats


class TestC3Cum3(unittest.TestCase):
    def test_copy_deleted_and_read_from_calendar(self):
        self.assertFalse(hasattr(config, "RO_CUM3_THRESHOLD"))
        for mod in (controls, rules, config):
            names, floats = _names_and_floats(mod)
            self.assertNotIn("RO_CUM3_THRESHOLD", names, mod.__name__)
            self.assertFalse({0.2, 0.3} & floats, (mod.__name__, sorted(floats)))
        d = pd.DatetimeIndex(["2020-08-21", "2020-08-23", "2020-08-24", "2026-06-30"])
        np.testing.assert_array_equal(rules.lhb_thresholds("chinext", d)["cum3"], [0.20, 0.20, 0.30, 0.30])
        np.testing.assert_array_equal(rules.lhb_thresholds("main", d)["cum3"], [0.20] * 4)
        np.testing.assert_array_equal(rules.lhb_thresholds("star", d)["cum3"], [0.30] * 4)
        exp = [rc.lhb_thresholds(x.date(), "chinext")["cum3"] for x in d]
        np.testing.assert_array_equal(rules.lhb_thresholds("chinext", d)["cum3"], exp)
        self.assertTrue(np.isnan(rules.lhb_thresholds("main", pd.DatetimeIndex(["2026-07-01"]))["cum3"][0]))

    def test_catalogue_source_column(self):
        cat = registry.catalogue().set_index("name")
        for w in config.ZO_LOOKBACKS:
            self.assertEqual(cat.loc[f"ro_trig_cum3_cnt_{w}", "source"], "rule calendar RC-18 cum3 (unverified, item 22)")


class TestC4BlockPremium(unittest.TestCase):
    """Own close 10.00, preclose 10.00, main board: [P_down, P_up] = [9.00, 11.00]."""

    def test_trade_above_limit_is_excluded_from_the_premium(self):
        blk = _blk([["600001", CAL.days[E].date(), 11.50, 0.15, 100, 100.0, 0.0],      # above P_up -> implausible
                    ["600001", CAL.days[E].date(), 9.50, -0.05, 300, 300.0, 0.0]])     # inside
        f = zo.blk_features(blk, DEC, CAL, LAST, pd.Series(1e4, index=CAL.days), ALL, 2, bars=_bars(), code="sh.600001")
        t = CAL.days[E + 2]
        self.assertEqual(f["zo_blk_ind_1"].loc[t], 1.0)
        self.assertAlmostEqual(f["zo_blk_prem_1"].loc[t], 9.50 / 10.0 - 1.0)            # only the plausible trade
        self.assertAlmostEqual(f["zo_blk_amt_1"].loc[t], 400 / 1e4)                     # amount intensity: both
        self.assertEqual(f.attrs["blk_stats"]["implausible"], 1)
        self.assertEqual(f.attrs["blk_stats"]["by_year"], {CAL.days[E].year: [2, 1]})

    def test_vendor_column_is_not_read(self):
        blk = _blk([["600001", CAL.days[E].date(), 9.50, 0.999, 300, 300.0, 0.0]])        # absurd vendor value
        f = zo.blk_features(blk, DEC, CAL, LAST, pd.Series(1e4, index=CAL.days), ALL, 2, bars=_bars(), code="sh.600001")
        self.assertAlmostEqual(f["zo_blk_prem_1"].loc[CAL.days[E + 2]], -0.05)

    def test_all_implausible_gives_nan_with_indicator_one(self):
        blk = _blk([["600001", CAL.days[E].date(), 8.90, -0.11, 100, 100.0, 0.0],        # below P_down
                    ["600001", CAL.days[E].date(), 11.01, 0.10, 100, 100.0, 0.0]])       # above P_up
        f = zo.blk_features(blk, DEC, CAL, LAST, pd.Series(1e4, index=CAL.days), ALL, 2, bars=_bars(), code="sh.600001")
        t = CAL.days[E + 2]
        self.assertEqual(f["zo_blk_ind_1"].loc[t], 1.0)
        self.assertTrue(np.isnan(f["zo_blk_prem_1"].loc[t]))
        self.assertAlmostEqual(f["zo_blk_amt_1"].loc[t], 200 / 1e4)
        self.assertEqual(f["zo_blk_days_since"].loc[CAL.days[E + 5]], 5.0)

    def test_no_traded_row_is_implausible_and_bounds_are_inclusive(self):
        b = _bars()
        b.loc[CAL.days[E], "traded"] = False
        blk = _blk([["600001", CAL.days[E].date(), 10.0, 0.0, 100, 100.0, 0.0]])
        f = zo.blk_features(blk, DEC, CAL, LAST, pd.Series(1e4, index=CAL.days), ALL, 2, bars=b, code="sh.600001")
        self.assertTrue(np.isnan(f["zo_blk_prem_1"].loc[CAL.days[E + 2]]))
        prem, ok = zo.blk_plausibility("sh.600001", CAL.days[[E, E]], np.array([9.00, 11.00]), _bars())
        self.assertTrue(ok.all())
        np.testing.assert_allclose(prem, [-0.10, 0.10])

    def test_bars_are_required(self):
        with self.assertRaises(ValueError):
            zo.blk_features(_blk([]), DEC, CAL, LAST, pd.Series(1e4, index=CAL.days), ALL, 2)


def _tree(root, codes, n_rows=700):
    cal = synth.make_calendar()
    raws = synth.write_raw_store(root, codes, cal, n_rows=n_rows)
    return cal, raws


class TestC6NoAdjustment(unittest.TestCase):
    def test_refused_inputs(self):
        cal = synth.make_calendar()
        raw = synth.make_raw_bars("sh.600001", cal, seed=1, n_rows=300)
        prepare_bars(raw, cal)
        for mutate in (lambda r: r.assign(adjustflag="2"), lambda r: r.assign(adjustflag="1"),
                       lambda r: r.assign(adj_factor="1.0"), lambda r: r.assign(hfq_close="1.0"),
                       lambda r: r.assign(backAdjustFactor="1.0")):
            with self.assertRaises(AdjustedDataError):
                prepare_bars(mutate(raw.copy()), cal)
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, ["sh.600001"])
            p = os.path.join(tmp, "bars", "bs_daily", "sh.600001.parquet")
            df = pd.read_parquet(p)
            df.assign(adjustflag="2").to_parquet(p)
            st = store.RawStore(tmp, data_cutoff="2026-06-30")
            with self.assertRaises(AdjustedDataError):
                st.raw_bars("sh.600001")
            with self.assertRaises(AdjustedDataError):
                store._guard(os.path.join(tmp, "factors_events", "bs_adjust_factor", "sh.600001.parquet"))

    def test_factor_directory_is_never_opened(self):
        """A file that is not parquet at all sits in the factor directory: a full panel build through
        RawStore succeeds, so the file was never opened; the list of opened files confirms it."""
        with tempfile.TemporaryDirectory() as tmp:
            codes = ["sh.600001", "sz.000002"]
            _tree(tmp, codes)
            fdir = os.path.join(tmp, "factors_events", "bs_adjust_factor")
            os.makedirs(fdir)
            for c in codes:
                with open(os.path.join(fdir, c + ".parquet"), "wb") as fh:
                    fh.write(b"not a parquet file")
            out = os.path.join(tmp, "panel")
            man = market_panel.build_market_panel(codes, out, root=tmp, progress_every=0, data_cutoff="2026-06-30")
            self.assertTrue((man["status"] == "ok").all(), man.to_dict("records"))
            st = store.RawStore(tmp, data_cutoff="2026-06-30")
            st.calendar(); st.zo_tables(); [st.raw_bars(c) for c in codes]
            self.assertFalse(any("adjust_factor" in p for p in st.opened))


class TestC8Cutoff(unittest.TestCase):
    def test_no_default_and_rows_after_the_cutoff_are_not_read(self):
        with self.assertRaises(TypeError):
            store.RawStore()                                    # keyword-only, no default
        with self.assertRaises(dc.CutoffError):
            store.RawStore(data_cutoff=None)
        with tempfile.TemporaryDirectory() as tmp:
            cal, raws = _tree(tmp, ["sh.600001"])
            cut = cal.days[500]
            st = store.RawStore(tmp, data_cutoff=cut)
            self.assertLessEqual(st.calendar().days[-1], cut)
            rb = st.raw_bars("sh.600001")
            self.assertLessEqual(pd.to_datetime(rb["date"]).max(), cut)
            self.assertLess(len(rb), len(raws["sh.600001"]))
            self.assertLessEqual(pd.to_datetime(st.raw_index("sh.000001")["date"]).max(), cut)
            with self.assertRaises(dc.CutoffError):
                prepare_bars(raws["sh.600001"], cal, data_cutoff=cut)            # a later row is refused
            prepare_bars(rb, cal, data_cutoff=cut)

    def test_zo_files_after_the_cutoff_are_never_opened(self):
        with tempfile.TemporaryDirectory() as tmp:
            cal, _ = _tree(tmp, ["sh.600001"])
            cut = cal.days[500]
            later = 0
            for sub in ("lhb_detail", "lhb_jgmmtj", "dzjy_mrmx", "ins_raw"):
                d = os.path.join(tmp, "zo", sub)
                for f in os.listdir(d):
                    per = f[:-8]
                    if per.isdigit() and not dc.period_ok(per, cut):
                        with open(os.path.join(d, f), "wb") as fh:          # opening it would raise
                            fh.write(b"garbage")
                        later += 1
            self.assertGreater(later, 10)
            st = store.RawStore(tmp, data_cutoff=cut)
            tb = st.zo_tables()
            self.assertTrue(all(dc.period_ok(p, cut) for v in tb.coverage.values() for p in v))
            self.assertFalse(any(not dc.period_ok(os.path.basename(p)[:-8], cut) for p in st.opened
                                 if os.sep + "zo" + os.sep in p))
            self.assertEqual(tb.analysis_end(), pd.Timestamp(cut))
            st.check_zo_coverage(tb, strict=True)                    # strict check ends at the cut-off: no error
            for df, col in ((tb.lhb, "上榜日"), (tb.blk, "交易日期"), (tb.ins, "NOTICE_DATE")):
                if len(df):
                    self.assertLessEqual(pd.to_datetime(df[col]).max(), cut)

    def test_panel_records_the_cutoff_and_ignores_later_data(self):
        """(c) panel_meta.json and every manifest row carry the cut-off; replacing every raw row after the
        cut-off by random values leaves the stored feature files bit-identical."""
        with tempfile.TemporaryDirectory() as tmp:
            codes = ["sh.600001", "sz.000002"]
            cal, raws = _tree(tmp, codes)
            cut = cal.days[520]
            out1 = os.path.join(tmp, "p1")
            man1 = market_panel.build_market_panel(codes, out1, root=tmp, progress_every=0, data_cutoff=cut)
            with open(os.path.join(out1, "panel_meta.json"), encoding="utf-8") as fh:
                meta = json.load(fh)
            self.assertEqual(meta["data_cutoff"], str(cut.date()))
            self.assertTrue((man1["data_cutoff"].astype(str) == str(cut.date())).all())
            rng = np.random.default_rng(5)
            for c in codes:
                p = os.path.join(tmp, "bars", "bs_daily", c + ".parquet")
                df = pd.read_parquet(p)
                late = pd.to_datetime(df["date"]) > cut
                for col in ("open", "high", "low", "close", "preclose", "volume", "amount", "turn"):
                    df.loc[late, col] = [f"{x:.4f}" for x in rng.uniform(1, 100, int(late.sum()))]
                df.to_parquet(p)
            out2 = os.path.join(tmp, "p2")
            market_panel.build_market_panel(codes, out2, root=tmp, progress_every=0, data_cutoff=cut)
            for c in codes:
                a = pd.read_parquet(os.path.join(out1, "features", c + ".parquet"))
                b = pd.read_parquet(os.path.join(out2, "features", c + ".parquet"))
                self.assertTrue(a.index.equals(b.index) and list(a.columns) == list(b.columns))
                va, vb = a.values, b.values
                self.assertTrue(bool(((np.isnan(va) & np.isnan(vb)) | (va.view(np.uint64) == vb.view(np.uint64))).all()))


if __name__ == "__main__":
    unittest.main()

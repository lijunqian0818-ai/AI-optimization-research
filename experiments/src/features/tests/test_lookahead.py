"""Look-ahead test on synthetic data, with negative controls showing that the
test detects a leak when there is one."""
import unittest

import numpy as np
import pandas as pd

from features import panel, lookahead, zo
from features.bars import prepare_bars
from features.config import ZO_LAG
from features.tests import synth

CODE = "sh.600001"


def build(code, raw_bars, cal, cutoff, raw_index, tables):
    return panel.build_stock_features(code, raw_bars, cal, cutoff, raw_index, tables)


def leaky_bar_build(code, raw_bars, cal, cutoff, raw_index, tables):
    """Deliberately wrong: adds the close of the decision day itself."""
    f = build(code, raw_bars, cal, cutoff, raw_index, tables)
    b = prepare_bars(raw_bars, cal)
    f["leak_close_t"] = b["aclose"].reindex(f.index).values
    return f


def leaky_event_build(code, raw_bars, cal, cutoff, raw_index, tables):
    """Deliberately wrong: uses the availability lag 1 where the rule is 2."""
    return panel.build_stock_features(code, raw_bars, cal, cutoff, raw_index, tables,
                                      zo_lags={"lhb": 1, "blk": 1, "ins": 1})


class TestLookahead(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cal = synth.make_calendar()
        cls.raw = synth.make_raw_bars(CODE, cls.cal, seed=11, n_rows=1300, missing_row=700)
        cls.idx = synth.make_raw_index(cls.cal)
        cls.tables = synth.make_zo_tables([CODE, "sz.000002", "sh.600003"], cls.cal, seed=5, n_per_code=120,
                                          last_pos=1290)
        cls.far = cls.cal.next(pd.to_datetime(cls.raw["date"]).max())
        cls.ref = build(CODE, cls.raw, cls.cal, cls.far, cls.idx, cls.tables)
        rng = np.random.default_rng(0)
        days = list(cls.ref.index[rng.choice(np.arange(300, len(cls.ref) - 5), size=4, replace=False)])
        # decision days at which an event has just become usable, and the day before
        lhb = cls.tables.for_code(CODE).lhb
        ev = cls.cal.pos_array(pd.to_datetime(lhb["上榜日"]))
        ev = ev[(ev > 400) & (ev < 1200)][:2]
        for p in ev:
            days += [cls.cal.days[p + ZO_LAG["lhb"]], cls.cal.days[p + ZO_LAG["lhb"] - 1]]
        cls.days = sorted(set(days))

    def test_all_checks_bit_identical(self):
        rec = lookahead.check_lookahead(build, CODE, self.raw, self.cal, self.days, self.idx, self.tables,
                                        far_cutoff=self.far, reference=self.ref, seed=1)
        df = pd.DataFrame(rec)
        self.assertEqual(len(df), len(self.days) * (1 + 5 * 2))
        self.assertTrue(df["equal"].all(), df.loc[~df["equal"], ["decision_day", "check", "diff_cols"]].to_string())
        self.assertGreater(df["n_nonnan"].min(), 150)        # the rows compared are not empty
        self.assertGreater(df["n_nonnan"].max(), 350)

    def test_detects_bar_leak(self):
        rec = lookahead.check_lookahead(leaky_bar_build, CODE, self.raw, self.cal, self.days[:2], self.idx,
                                        self.tables, far_cutoff=self.far, seed=1)
        df = pd.DataFrame(rec)
        bad = df[~df["equal"]]
        self.assertGreater(len(bad), 0)
        self.assertTrue(bad["diff_cols"].str.contains("leak_close_t").all())
        # every check that destroys the inputs outside G_t catches the leak. The 'truncate' check does not:
        # it passes the intact data with cut-off t and so only tests that the cut-off argument is honoured
        # consistently; a function that ignores its cut-off is caught by the destructive checks alone.
        self.assertFalse(df.loc[df["check"] != "truncate", "equal"].any())

    def test_detects_too_short_event_lag(self):
        # a decision day on which an event of t-1 exists: usable only under the wrong lag
        lhb = self.tables.for_code(CODE).lhb
        ev = self.cal.pos_array(pd.to_datetime(lhb["上榜日"]))
        p = int(ev[(ev > 400) & (ev < 1200)][0])
        t = self.cal.days[p + 1]
        rec = lookahead.check_lookahead(leaky_event_build, CODE, self.raw, self.cal, [t], self.idx, self.tables,
                                        far_cutoff=self.far, seed=1)
        df = pd.DataFrame(rec)
        avail = df[df["check"].str.endswith("/availability")]
        self.assertFalse(avail["equal"].all())                # caught by the availability scope
        cal_scope = df[df["check"].str.endswith("/calendar") | (df["check"] == "truncate")]
        self.assertTrue(cal_scope["equal"].all())             # and not by the calendar scope alone

    def test_bitwise_equal_semantics(self):
        a = pd.Series([1.0, np.nan, 0.0])
        self.assertTrue(lookahead.bitwise_equal(a, a.copy())[0])
        self.assertFalse(lookahead.bitwise_equal(a, pd.Series([1.0 + 2e-16, np.nan, 0.0]))[0])
        self.assertFalse(lookahead.bitwise_equal(a, pd.Series([1.0, 0.0, 0.0]))[0])
        self.assertFalse(lookahead.bitwise_equal(a, pd.Series([1.0, np.nan, -0.0]))[0])

    def test_corruption_really_changes_the_data(self):
        t = self.days[0]
        rng = np.random.default_rng(0)
        for mode in ("nan", "shuffle", "noise", "drop"):
            cb = lookahead.corrupt_bars(self.raw, t, mode, rng)
            past = pd.to_datetime(self.raw["date"]) < t
            pd.testing.assert_frame_equal(cb.loc[pd.to_datetime(cb["date"]) < t].reset_index(drop=True),
                                          self.raw.loc[past].reset_index(drop=True))
            if mode == "drop":
                self.assertEqual(len(cb), int(past.sum()))
            else:
                self.assertFalse(cb["close"].equals(self.raw["close"]))
        for scope in ("calendar", "availability"):
            ct = lookahead.corrupt_events(self.tables, self.cal, t, "nan", rng, scope, CODE)
            d = pd.to_datetime(ct.lhb["上榜日"])
            lim = t if scope == "calendar" else self.cal.days[self.cal.pos(t) - ZO_LAG["lhb"] + 1]
            self.assertTrue(ct.lhb.loc[d >= lim, "龙虎榜净买额"].isna().all())
            self.assertTrue(ct.lhb.loc[d < lim, "龙虎榜净买额"].notna().all())


if __name__ == "__main__":
    unittest.main()

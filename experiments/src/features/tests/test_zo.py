"""Z_O: availability lag, windows, encoding, same-day rows, coverage.

Rewritten for PLAN v0.7 (task list FEA-5, FEA-6, FEA-9, FEA-13). Expected
values that differ from the v0.6 file follow from the changed definitions:
`days_since` / `has_prior` use a fixed 250-day look-back and are NaN until
250 + lag days of coverage (F-5); LHB intensities use single-day-reason rows
only (F-6). The calendar is longer than in v0.6 for that reason; the event
positions are the v0.6 ones shifted by 330 trading days.
"""
import unittest

import numpy as np
import pandas as pd

from features import zo, config
from features.timing import TradingCalendar

CAL = TradingCalendar(pd.bdate_range("2020-01-01", periods=760))     # Mon-Fri, no holidays; pos 0 = Wednesday
ALL = np.ones(len(CAL), dtype=bool)
DEC = CAL.days[5:700]
LAST = CAL.days[700]
E = 400                                                              # position of the reference event day


def _adv(value=1e6):
    return pd.Series(value, index=DEC)


def _lhb(rows):
    return pd.DataFrame(rows, columns=["代码", "上榜日", "龙虎榜净买额", "龙虎榜买入额", "龙虎榜卖出额", "龙虎榜成交额",
                                       "市场总成交额", "净买额占总成交比", "成交额占总成交比", "上榜原因"])


def _jg(rows):
    return pd.DataFrame(rows, columns=["代码", "上榜日期", "买方机构数", "卖方机构数", "机构买入总额", "机构卖出总额",
                                       "机构买入净额", "上榜原因"])


def _blk(rows):
    return pd.DataFrame(rows, columns=["证券代码", "交易日期", "成交价", "折溢率", "成交量", "成交额", "成交额/流通市值"])


def _ins(rows):
    return pd.DataFrame(rows, columns=["SECURITY_CODE", "NOTICE_DATE", "DIRECTION", "CHANGE_NUM", "AFTER_CHANGE_RATE",
                                       "CHANGE_FREE_RATIO", "START_DATE", "END_DATE", "EITIME"])


def _d(pos):
    return CAL.days[pos]


def _row(pos, net, amt, reason, code="600001"):
    """One lhb_detail row: seat net buy `net`, seat traded amount `amt`."""
    return [code, _d(pos).date(), net, (amt + net) / 2, (amt - net) / 2, amt, 10 ** 7, 0.0, 0.0, reason]


S1 = "日涨幅偏离值达到7%的前五只证券"
S2 = "日换手率达到20%的前五只证券"
S3 = "日振幅值达到15%的前五只证券"
M3 = "连续三个交易日内，涨幅偏离值累计达到20%的证券"
UNC = "无价格涨跌幅限制的证券"


class TestLHB(unittest.TestCase):
    def setUp(self):
        self.s = _d(E)                                     # the listing day
        self.lhb = _lhb([["600001", self.s.date(), 2e5, 5e5, 3e5, 8e5, 10 ** 7, 2.0, 8.0, S1]])
        self.jg = _jg([["600001", self.s.date(), 1, 0, 1e5, 0.0, 1e5, S1]])

    def f(self, lag=2, cutoff=LAST, lhb=None, jg=None, cov=ALL, adv=None):
        return zo.lhb_features(self.lhb if lhb is None else lhb, self.jg if jg is None else jg,
                               DEC[DEC <= cutoff], CAL, cutoff, _adv() if adv is None else adv, cov, cov, lag)

    # ------------------------------------------------------------ timing (unchanged rules)
    def test_lag_two_window_one(self):
        ind = self.f()["zo_lhb_ind_1"]
        self.assertEqual(ind.loc[_d(E)], 0.0)       # the event day itself
        self.assertEqual(ind.loc[_d(E + 1)], 0.0)   # the next day: not yet usable (lag 2)
        self.assertEqual(ind.loc[_d(E + 2)], 1.0)
        self.assertEqual(ind.loc[_d(E + 3)], 0.0)
        self.assertEqual(int(ind.sum()), 1)

    def test_windows_5_and_20(self):
        f = self.f()
        self.assertEqual(list(f["zo_lhb_ind_5"].loc[_d(E + 1):_d(E + 7)]), [0, 1, 1, 1, 1, 1, 0])
        self.assertEqual(int(f["zo_lhb_ind_20"].sum()), 20)

    def test_intensity_and_exact_zero_without_event(self):
        f = self.f()
        self.assertAlmostEqual(f["zo_lhb_net_1"].loc[_d(E + 2)], 2e5 / 1e6)
        self.assertAlmostEqual(f["zo_lhb_inst_net_5"].loc[_d(E + 4)], 1e5 / 1e6)
        self.assertEqual(f["zo_lhb_net_1"].loc[_d(E + 3)], 0.0)
        self.assertEqual(f["zo_lhb_net_20"].loc[_d(E + 50)], 0.0)
        self.assertEqual(f["zo_lhb_multi_20"].loc[_d(E + 5)], 0.0)

    def test_lag_one_parameter(self):
        f = self.f(lag=1)
        self.assertEqual(f["zo_lhb_ind_1"].loc[_d(E + 1)], 1.0)
        self.assertEqual(f["zo_lhb_days_since"].loc[_d(E + 1)], 1.0)

    def test_cutoff_drops_events_not_yet_usable(self):
        f = self.f(cutoff=_d(E + 1))
        self.assertEqual(f["zo_lhb_ind_20"].loc[_d(E + 1)], 0.0)
        self.assertEqual(f["zo_lhb_has_prior"].loc[_d(E + 1)], 0.0)
        g = self.f(cutoff=_d(E + 2))
        self.assertEqual(g["zo_lhb_ind_20"].loc[_d(E + 2)], 1.0)

    # ------------------------------------------------------------ FEA-5 (ruling F-5)
    def test_days_since_and_has_prior_250_day_lookback(self):
        f = self.f()
        ds, hp = f["zo_lhb_days_since"], f["zo_lhb_has_prior"]
        self.assertEqual((ds.loc[_d(E + 1)], hp.loc[_d(E + 1)]), (0.0, 0.0))      # not yet usable
        self.assertEqual((ds.loc[_d(E + 2)], hp.loc[_d(E + 2)]), (2.0, 1.0))      # minimum = the lag
        self.assertEqual(ds.loc[_d(E + 3)], 3.0)                                  # event 3 days ago
        self.assertEqual(ds.loc[_d(E + 59)], 59.0)
        self.assertEqual(ds.loc[_d(E + 60)], 60.0)
        self.assertEqual((ds.loc[_d(E + 61)], hp.loc[_d(E + 61)]), (60.0, 1.0))   # 61 days ago: capped
        self.assertEqual((ds.loc[_d(E + 249)], hp.loc[_d(E + 249)]), (60.0, 1.0))  # 249 days ago: inside
        self.assertEqual((ds.loc[_d(E + 250)], hp.loc[_d(E + 250)]), (60.0, 1.0))  # exactly 250: inside
        self.assertEqual((ds.loc[_d(E + 251)], hp.loc[_d(E + 251)]), (0.0, 0.0))   # 251 days ago: outside
        self.assertEqual(ds.dropna().min(), 0.0)
        self.assertEqual(ds[ds > 0].min(), 2.0)

    def test_days_since_nan_until_250_plus_lag_days_of_coverage(self):
        cov = ALL.copy()
        cov[:40] = False                                     # the class starts at position 40
        f = self.f(cov=cov)
        ds, hp = f["zo_lhb_days_since"], f["zo_lhb_has_prior"]
        first = 40 + config.ZO_PRIOR_LOOKBACK + 2            # 250 + lag covered trading days before t
        self.assertTrue(ds.loc[:_d(first - 1)].isna().all())
        self.assertTrue(hp.loc[:_d(first - 1)].isna().all())
        self.assertEqual(ds.loc[_d(first)], 0.0)
        self.assertTrue(ds.loc[_d(first):].notna().all())
        f1 = self.f(cov=cov, lag=1)
        self.assertTrue(np.isnan(f1["zo_lhb_days_since"].loc[_d(40 + 250)]))
        self.assertEqual(f1["zo_lhb_days_since"].loc[_d(40 + 251)], 0.0)
        # with coverage from the first calendar day the first value is at position 250 + lag
        g = self.f()
        self.assertTrue(np.isnan(g["zo_lhb_days_since"].loc[_d(251)]))
        self.assertEqual(g["zo_lhb_days_since"].loc[_d(252)], 0.0)

    def test_days_since_independent_of_the_start_of_the_raw_data(self):
        old = [_row(20, 1e5, 4e5, S1), _row(90, -3e5, 9e5, S2)]
        both = _lhb(old + [_row(E, 2e5, 8e5, S1), _row(E + 100, 1e5, 5e5, S1)])
        late = _lhb([_row(E, 2e5, 8e5, S1), _row(E + 100, 1e5, 5e5, S1)])
        a = self.f(lhb=both, jg=_jg([]))
        b = self.f(lhb=late, jg=_jg([]))
        t0 = _d(90 + 251)                                    # from here the deleted history is outside every look-back
        for c in ("zo_lhb_days_since", "zo_lhb_has_prior"):
            x, y = a[c].loc[t0:].values, b[c].loc[t0:].values
            self.assertTrue(np.array_equal(x.view(np.uint64), y.view(np.uint64)), c)        # bit for bit
        self.assertEqual(a["zo_lhb_has_prior"].loc[_d(90 + 250)], 1.0)                      # and before it they differ
        self.assertEqual(b["zo_lhb_has_prior"].loc[_d(90 + 250)], 0.0)
        # the same with the START OF COVERAGE moved: rows with 250 + lag covered days are unchanged
        cov = ALL.copy()
        cov[:100] = False
        c2 = self.f(lhb=late, jg=_jg([]), cov=cov)
        t1 = _d(100 + 252)
        for c in ("zo_lhb_days_since", "zo_lhb_has_prior", "zo_lhb_ind_20"):
            x, y = b[c].loc[t1:].values, c2[c].loc[t1:].values
            self.assertTrue(np.array_equal(x.view(np.uint64), y.view(np.uint64)), c)

    # ------------------------------------------------------------ FEA-6 (ruling F-6)
    def test_same_day_rows_choice_and_ties(self):
        lhb = _lhb([_row(E, 9e5, 3.1e6, M3),          # 3-day cumulative, the largest amounts: never chosen
                    _row(E, 2e5, 8e5, S1),            # single-day, largest seat traded amount -> chosen
                    _row(E, 1e5, 7e5, S2)])
        sd = zo.lhb_stock_day(lhb, _jg([]))
        self.assertEqual(len(sd), 1)
        r = sd.iloc[0]
        self.assertEqual((r["n_rows"], bool(r["multi"]), bool(r["has_single"]), r["n_unclassified"]), (3, True, True, 0))
        self.assertEqual(r["net"], 2e5)
        self.assertEqual(r["inst_net"], 0.0)
        # tie on the seat traded amount -> the larger |net buy|
        tie = _lhb([_row(E, 1e5, 8e5, S1), _row(E, -3e5, 8e5, S2), _row(E, 2e5, 8e5, S3)])
        self.assertEqual(zo.lhb_stock_day(tie, _jg([]))["net"].iloc[0], -3e5)
        # tie on both -> the reason string, in sorted order (S2 < S1 as strings is checked, not assumed)
        tie2 = _lhb([_row(E, 3e5, 8e5, S1), _row(E, -3e5, 8e5, S2)])
        first = min(S1, S2)
        self.assertEqual(zo.lhb_stock_day(tie2, _jg([]))["net"].iloc[0], 3e5 if first == S1 else -3e5)
        # the result does not depend on the order of the rows in the table
        self.assertEqual(zo.lhb_stock_day(tie.iloc[::-1], _jg([]))["net"].iloc[0], -3e5)
        self.assertEqual(zo.lhb_stock_day(lhb.iloc[::-1], _jg([]))["net"].iloc[0], 2e5)

    def test_stock_day_with_multi_day_rows_only(self):
        lhb = _lhb([_row(E, 9e5, 3.1e6, M3)])
        jg = _jg([["600001", _d(E).date(), 2, 1, 5e5, 1e5, 4e5, M3]])
        sd = zo.lhb_stock_day(lhb, jg).iloc[0]
        self.assertEqual((sd["net"], sd["inst_net"], bool(sd["multi"]), bool(sd["has_single"])), (0.0, 0.0, True, False))
        f = self.f(lhb=lhb, jg=jg)
        t = _d(E + 2)
        self.assertEqual(f["zo_lhb_ind_1"].loc[t], 1.0)             # listed
        self.assertEqual(f["zo_lhb_net_1"].loc[t], 0.0)             # cumulative amount contributes 0
        self.assertEqual(f["zo_lhb_inst_net_1"].loc[t], 0.0)
        self.assertEqual(f["zo_lhb_multi_1"].loc[t], 1.0)
        self.assertEqual(f["zo_lhb_multi_1"].loc[_d(E + 3)], 0.0)
        self.assertEqual(int(f["zo_lhb_multi_5"].sum()), 5)
        self.assertEqual(f["zo_lhb_days_since"].loc[t], 2.0)        # any row counts for the timing columns
        self.assertEqual(f.attrs["n_stock_days_multi_only"], 1)

    def test_single_day_rows_followed_by_three_day_cumulative_row_are_not_added_twice(self):
        # three days of single-day listings; on the third day there is also the 3-day cumulative row, whose
        # amount is the sum of the three days
        lhb = _lhb([_row(E, 1e5, 6e5, S1), _row(E + 1, 2e5, 7e5, S1), _row(E + 2, 4e5, 9e5, S1),
                    _row(E + 2, 7e5, 2.2e6, M3)])
        f = self.f(lhb=lhb, jg=_jg([]))
        t = _d(E + 4)                                        # window(t, 5) = event days E-2 .. E+2
        self.assertAlmostEqual(f["zo_lhb_net_5"].loc[t], (1e5 + 2e5 + 4e5) / 1e6, places=15)   # not 1.4
        self.assertAlmostEqual(f["zo_lhb_net_1"].loc[t], 4e5 / 1e6, places=15)
        self.assertEqual(f["zo_lhb_multi_1"].loc[t], 1.0)
        self.assertEqual(f["zo_lhb_multi_1"].loc[_d(E + 3)], 0.0)

    def test_unclassified_reason_counts_for_the_indicator_only(self):
        self.assertEqual(zo.reason_class(UNC), "unclassified")
        self.assertEqual(zo.reason_class("a string that is not in the frozen table"), "unclassified")
        self.assertEqual(zo.reason_class(None), "unclassified")
        lhb = _lhb([_row(E, 5e5, 9e5, UNC), _row(E + 10, 5e5, 9e5, "not in the table"), _row(E + 10, 1e5, 2e5, S1)])
        f = self.f(lhb=lhb, jg=_jg([]))
        self.assertEqual(f.attrs["n_unclassified_rows"], 2)
        self.assertEqual(f["zo_lhb_ind_1"].loc[_d(E + 2)], 1.0)
        self.assertEqual(f["zo_lhb_net_1"].loc[_d(E + 2)], 0.0)
        self.assertEqual(f["zo_lhb_multi_1"].loc[_d(E + 2)], 0.0)
        self.assertAlmostEqual(f["zo_lhb_net_1"].loc[_d(E + 12)], 1e5 / 1e6)     # the single-day row, not the larger one

    def test_institutional_table_same_rule(self):
        d = _d(E).date()
        jg = _jg([["600001", d, 3, 3, 9e6, 1e6, 8e6, M3],                 # cumulative: ignored
                  ["600001", d, 1, 0, 1e5, 0.0, 1e5, S1],                 # size 1e5
                  ["600001", d, 1, 1, 2e5, 1e5, -4e4, S2]])               # size 3e5 -> chosen
        sd = zo.lhb_stock_day(self.lhb, jg)
        self.assertEqual(sd["inst_net"].iloc[0], -4e4)
        f = self.f(jg=jg)
        self.assertAlmostEqual(f["zo_lhb_inst_net_1"].loc[_d(E + 2)], -4e4 / 1e6)

    def test_reason_table(self):
        m = zo.load_reason_map()
        self.assertGreater(len(m), 600)
        self.assertEqual(set(m.values()), {"single", "multi", "unclassified"})
        for r in (M3, "非ST、*ST和S证券连续三个交易日内收盘价格涨幅偏离值累计达到20%的证券",
                  "当日有涨跌幅限制的A股，连续2个交易日触及涨幅限制，在这2个交易日中同一营业部净买入",
                  "有价格涨跌幅限制的连续3个交易日内收盘价格涨幅偏离值累计达到30%的证券",
                  "严重异常期间4次出现正向异常波动的证券"):
            self.assertEqual(zo.reason_class(r), "multi", r)
            self.assertTrue(zo.is_multi_day_reason(r), r)
        for r in (S1, S2, "有价格涨跌幅限制的日价格振幅达到15%的前三只证券", "日涨幅达到15%的前5只证券",
                  "当日无价格涨跌幅限制的A股，出现异常波动停牌的"):
            self.assertEqual(zo.reason_class(r), "single", r)
            self.assertFalse(zo.is_multi_day_reason(r), r)
        for r in (UNC, "退市整理的证券", "退市整理期"):
            self.assertEqual(zo.reason_class(r), "unclassified", r)

    def test_reason_table_is_reproduced_by_its_builder_rule(self):
        from features import build_lhb_reason_map as bm
        m = zo.load_reason_map()
        for r, c in m.items():
            self.assertEqual(bm.classify(r)[0], c, r)

    # ------------------------------------------------------------ coverage
    def test_uncovered_period_is_nan_with_data_flag_zero(self):
        cov = ALL.copy()
        cov[:340] = False
        lhb = _lhb([_row(E - 10, 2e5, 8e5, S1)])
        f = self.f(lhb=lhb, cov=cov)
        self.assertTrue(np.isnan(f["zo_lhb_ind_1"].loc[_d(330)]))
        self.assertTrue(np.isnan(f["zo_lhb_net_1"].loc[_d(330)]))
        self.assertTrue(np.isnan(f["zo_lhb_multi_1"].loc[_d(330)]))
        self.assertEqual(f["ro_lhb_data"].loc[_d(330)], 0.0)
        self.assertEqual(f["ro_lhb_data"].loc[_d(342)], 1.0)
        self.assertEqual(f["zo_lhb_ind_1"].loc[_d(342)], 0.0)
        self.assertTrue(np.isnan(f["zo_lhb_ind_5"].loc[_d(344)]))        # window reaches back to day 338
        self.assertEqual(f["zo_lhb_ind_5"].loc[_d(346)], 0.0)

    def test_missing_adv_with_an_event_is_nan_not_zero(self):
        adv = _adv()
        adv.loc[_d(E + 2)] = np.nan
        f = self.f(adv=adv)
        self.assertEqual(f["zo_lhb_ind_1"].loc[_d(E + 2)], 1.0)
        self.assertTrue(np.isnan(f["zo_lhb_net_1"].loc[_d(E + 2)]))
        self.assertTrue(np.isnan(f["zo_lhb_inst_net_1"].loc[_d(E + 2)]))
        self.assertEqual(f["zo_lhb_net_1"].loc[_d(E + 3)], 0.0)          # no event: exactly 0 whatever the ADV
        adv.loc[_d(E + 3)] = np.nan
        self.assertEqual(self.f(adv=adv)["zo_lhb_net_1"].loc[_d(E + 3)], 0.0)

    def test_code_mapping(self):
        self.assertEqual(zo.to_bs_code("600000"), "sh.600000")
        self.assertEqual(zo.to_bs_code("688981"), "sh.688981")
        self.assertEqual(zo.to_bs_code("300750"), "sz.300750")
        for c in ("200002", "900951", "920001", "113001", "83xxxx"):
            self.assertIsNone(zo.to_bs_code(c))


class TestCoverage(unittest.TestCase):
    """FEA-9 (ruling F-14)."""

    def setUp(self):
        self.cal = TradingCalendar(pd.bdate_range("2007-11-01", "2008-12-31"))
        self.months = set(self.cal.days[self.cal.days >= "2008-01-01"].strftime("%Y%m"))

    def test_analysis_start_is_2008(self):
        cov = zo.coverage_array(self.cal, "lhb", self.months | {"200711", "200712"})
        self.assertFalse(cov[self.cal.pos("2007-12-31")])           # before the analysis start although a file exists
        self.assertTrue(cov[self.cal.pos("2008-01-01")])
        self.assertEqual(int(cov.sum()), int((self.cal.days >= "2008-01-01").sum()))
        self.assertEqual(config.ZO_CLASS_START["blk"], pd.Timestamp("2008-01-01"))

    def test_strict_raises_on_a_missing_file_inside_the_analysis_period(self):
        self.assertTrue(config.ZO_STRICT_COVERAGE)                  # production default
        with self.assertRaises(zo.MissingRawFile) as cm:
            zo.coverage_array(self.cal, "blk", self.months - {"200805"})
        self.assertIn("200805", str(cm.exception))
        with self.assertRaises(zo.MissingRawFile):
            zo.coverage_array(self.cal, "ins", set())
        # a file missing BEFORE the analysis start is not an error
        zo.coverage_array(self.cal, "lhb", self.months)

    def test_non_strict_keeps_the_nan_behaviour(self):
        cov = zo.coverage_array(self.cal, "blk", self.months - {"200805"}, strict=False)
        may = self.cal.days.strftime("%Y%m") == "200805"
        self.assertFalse(cov[may].any())
        self.assertTrue(cov[self.cal.pos("2008-06-02")])
        self.assertTrue(cov[self.cal.pos("2008-04-30")])

    def test_strict_is_the_default_of_the_assembly(self):
        cal = CAL
        tb = zo.ZOTables(_lhb([]), _jg([]), _blk([]), _ins([]),
                         {"lhb": set(), "jg": set(), "blk": set(), "ins": set()})
        with self.assertRaises(zo.MissingRawFile):
            zo.zo_features("sh.600001", DEC, cal, LAST, tb, _adv(), pd.Series(1e9, index=cal.days))
        f = zo.zo_features("sh.600001", DEC, cal, LAST, tb, _adv(), pd.Series(1e9, index=cal.days), strict=False,
                           bars=_flat_bars())
        self.assertTrue(f[zo.ZO_NAMES].isna().all().all())
        self.assertEqual(f["ro_lhb_data"].sum(), 0.0)

    def test_ins_coverage_by_announcement_year(self):
        cal = TradingCalendar(pd.bdate_range("2019-12-20", periods=40))
        cov = zo.coverage_array(cal, "ins", {"2020"}, start="2019-01-01", strict=False)
        self.assertFalse(cov[cal.pos("2019-12-31")])
        self.assertTrue(cov[cal.pos("2020-01-01")])      # the days since the previous trading day are all in 2020
        self.assertTrue(cov[cal.pos("2020-01-02")])
        # a year boundary with non-trading days before it: Monday 2018-01-01 follows Friday 2017-12-29,
        # so announcements dated Saturday 2017-12-30 / Sunday 2017-12-31 roll onto it
        cal2 = TradingCalendar(pd.bdate_range("2017-12-20", periods=20))
        cov2 = zo.coverage_array(cal2, "ins", {"2018"}, start="2017-01-01", strict=False)
        self.assertFalse(cov2[cal2.pos("2018-01-01")])
        self.assertTrue(cov2[cal2.pos("2018-01-02")])
        with self.assertRaises(zo.MissingRawFile):
            zo.coverage_array(cal2, "ins", {"2018"}, start="2018-01-01", strict=True)   # 2017 needed for the roll
        self.assertTrue(zo.coverage_array(cal2, "ins", {"2017", "2018"}, start="2018-01-01")[cal2.pos("2018-01-01")])


def _flat_bars(close=10.0, preclose=10.0):
    """Own bar frame for the BLK premium (PLAN v0.8 J-7): every day traded, unadjusted close 10, preclose 10
    (main-board band 10% -> [9.00, 11.00])."""
    return pd.DataFrame({"close": close, "preclose": preclose, "traded": True, "is_st": False}, index=CAL.days)


class TestBLK(unittest.TestCase):
    """v0.8 (task C-4): the premium is recomputed from own bars (trade price / own close - 1); the expected values
    of the v0.7 tests are unchanged because the constructed vendor column 折溢率 equals price / 10 - 1 here."""

    def test_amount_weighted_premium_and_ratio(self):
        blk = _blk([["600001", _d(E + 10).date(), 9.0, -0.10, 100, 100.0, 0.1],
                    ["600001", _d(E + 10).date(), 9.8, -0.02, 300, 300.0, 0.3],
                    ["600001", _d(E + 12).date(), 10.0, 0.0, 600, 600.0, 0.3]])
        fmv = pd.Series(1e4, index=CAL.days)
        f = zo.blk_features(blk, DEC, CAL, LAST, fmv, ALL, 2, bars=_flat_bars(), code="sh.600001")
        t = _d(E + 12)
        self.assertEqual(f["zo_blk_ind_1"].loc[t], 1.0)
        self.assertAlmostEqual(f["zo_blk_prem_1"].loc[t], (-0.10 * 100 - 0.02 * 300) / 400)
        self.assertAlmostEqual(f["zo_blk_amt_1"].loc[t], 400 / 1e4)
        t5 = _d(E + 15)                                           # window = event days E+9 .. E+13
        self.assertAlmostEqual(f["zo_blk_amt_5"].loc[t5], 1000 / 1e4)
        self.assertAlmostEqual(f["zo_blk_prem_5"].loc[t5], (-0.10 * 100 - 0.02 * 300) / 1000)
        self.assertEqual(f["zo_blk_prem_1"].loc[_d(E + 13)], 0.0)
        self.assertEqual(f["zo_blk_days_since"].loc[_d(E + 15)], 3.0)
        self.assertEqual(f["zo_blk_has_prior"].loc[_d(E + 12 + 250)], 1.0)
        self.assertEqual(f["zo_blk_has_prior"].loc[_d(E + 12 + 251)], 0.0)

    def test_missing_float_value_gives_nan_intensity_not_zero(self):
        blk = _blk([["600001", _d(E + 10).date(), 9.0, -0.10, 100, 100.0, 0.1]])
        fmv = pd.Series(np.nan, index=CAL.days)
        f = zo.blk_features(blk, DEC, CAL, LAST, fmv, ALL, 2, bars=_flat_bars(), code="sh.600001")
        self.assertEqual(f["zo_blk_ind_1"].loc[_d(E + 12)], 1.0)
        self.assertTrue(np.isnan(f["zo_blk_amt_1"].loc[_d(E + 12)]))
        self.assertAlmostEqual(f["zo_blk_prem_1"].loc[_d(E + 12)], -0.10)


class TestINS(unittest.TestCase):
    def test_announcement_date_not_trade_date_and_weekend_roll(self):
        fri = _d(E + 2)
        self.assertEqual(fri.day_name(), "Friday")
        sat = fri + pd.Timedelta(days=1)
        self.assertEqual(_d(E + 3).day_name(), "Monday")
        ins = _ins([
            # traded long before, announced on a Saturday
            ["600001", sat.strftime("%Y-%m-%d 00:00:00"), "减持", 10.0, 0.0, 1.5, None, _d(3).strftime("%Y-%m-%d"),
             "2019-05-17 15:22:07"],
            ["600001", _d(E + 20).strftime("%Y-%m-%d 00:00:00"), "增持", 5.0, 0.0, 0.4, None, _d(E + 19).strftime("%Y-%m-%d"), ""],
            ["600001", _d(E + 20).strftime("%Y-%m-%d 00:00:00"), "增持", 5.0, 0.0, 0.6, None, _d(E + 18).strftime("%Y-%m-%d"), ""],
        ])
        f = zo.ins_features(ins, DEC, CAL, LAST, ALL, 2)
        sell = f["zo_ins_sell_ind_1"]
        self.assertEqual(int(sell.loc[:_d(E + 4)].sum()), 0)        # nothing before Monday + 2
        self.assertEqual(sell.loc[_d(E + 5)], 1.0)                  # Monday (pos E+3) + lag 2
        self.assertAlmostEqual(f["zo_ins_sell_1"].loc[_d(E + 5)], -0.015)
        self.assertEqual(f["zo_ins_buy_ind_1"].loc[_d(E + 5)], 0.0)
        self.assertEqual(f["zo_ins_buy_1"].loc[_d(E + 5)], 0.0)
        self.assertAlmostEqual(f["zo_ins_buy_1"].loc[_d(E + 22)], 0.010)   # two records summed
        self.assertEqual(f["zo_ins_sell_1"].loc[_d(E + 22)], 0.0)
        self.assertEqual(f["zo_ins_sell_days_since"].loc[_d(E + 22)], 19.0)
        self.assertEqual(f["zo_ins_buy_days_since"].loc[_d(E + 22)], 2.0)

    def test_backfilled_row_is_used_from_its_announcement_day_only(self):
        # entered by the vendor two years after the announcement; change executed long before the announcement
        ins = _ins([["600001", _d(E).strftime("%Y-%m-%d 00:00:00"), "减持", 10.0, 0.0, 2.0,
                     _d(E - 300).strftime("%Y-%m-%d"), _d(E - 200).strftime("%Y-%m-%d"),
                     (_d(E) + pd.Timedelta(days=730)).strftime("%Y-%m-%d %H:%M:%S")]])
        f = zo.ins_features(ins, DEC, CAL, LAST, ALL, 2)
        ind = f["zo_ins_sell_ind_20"]
        self.assertEqual(int(ind.loc[:_d(E + 1)].sum()), 0)         # nothing at the transaction dates or before a + lag
        self.assertEqual(ind.loc[_d(E + 2)], 1.0)
        # the entry time and the transaction dates do not enter: change them, nothing moves
        ins2 = ins.copy()
        ins2["EITIME"] = "1999-01-01 00:00:00"
        ins2["START_DATE"] = None
        ins2["END_DATE"] = _d(E - 1).strftime("%Y-%m-%d")
        pd.testing.assert_frame_equal(f, zo.ins_features(ins2, DEC, CAL, LAST, ALL, 2))

    def test_cleaning_rules(self):
        ins = _ins([
            ["600001", None, "减持", 1.0, 0.0, 1.0, None, "2020-01-10", ""],
            ["600001", "2020-02-03 00:00:00", None, 1.0, 0.0, 1.0, None, "2020-01-10", ""],
            ["600001", "2020-02-03 00:00:00", "减持", 1.0, 0.0, 1.0, None, "2020-02-20", ""],     # notice before end
            ["600001", "2020-02-03 00:00:00", "减持", 1.0, 0.0, 1.0, None, "2020-02-03", "2020-06-01 00:00:00"],
        ])
        x, st = zo.clean_ins(ins)
        self.assertEqual(len(x), 1)
        self.assertEqual((st["dropped_no_notice_date"], st["dropped_direction"], st["dropped_notice_before_end"]),
                         (1, 1, 1))
        self.assertEqual(st["share_entered_gt30d_after_notice"], 1.0)

    def test_missing_ratio_propagates_as_nan(self):
        ins = _ins([["600001", _d(E).strftime("%Y-%m-%d"), "减持", 1.0, 0.0, np.nan, None, None, ""]])
        f = zo.ins_features(ins, DEC, CAL, LAST, ALL, 2)
        self.assertEqual(f["zo_ins_sell_ind_1"].loc[_d(E + 2)], 1.0)
        self.assertTrue(np.isnan(f["zo_ins_sell_1"].loc[_d(E + 2)]))
        self.assertEqual(f["zo_ins_sell_1"].loc[_d(E + 3)], 0.0)

    def test_intensity_switch_off_blanks_intensities_and_keeps_indicators(self):
        """FEA-13 (ruling F-10)."""
        self.assertTrue(config.INS_INTENSITY_ENABLED)
        ins = _ins([["600001", _d(E).strftime("%Y-%m-%d"), "减持", 1.0, 0.0, 1.5, None, None, ""],
                    ["600001", _d(E + 7).strftime("%Y-%m-%d"), "增持", 1.0, 0.0, 0.5, None, None, ""]])
        on = zo.ins_features(ins, DEC, CAL, LAST, ALL, 2)
        off = zo.ins_features(ins, DEC, CAL, LAST, ALL, 2, intensity_enabled=False)
        self.assertEqual(list(on.columns), list(off.columns))                    # the catalogue does not change
        self.assertEqual(len(zo.INS_INTENSITY_NAMES), 6)
        self.assertTrue(off[zo.INS_INTENSITY_NAMES].isna().all().all())
        rest = [c for c in on.columns if c not in zo.INS_INTENSITY_NAMES]
        pd.testing.assert_frame_equal(on[rest], off[rest])
        self.assertEqual(off["zo_ins_sell_ind_1"].loc[_d(E + 2)], 1.0)
        self.assertAlmostEqual(on["zo_ins_sell_1"].loc[_d(E + 2)], -0.015)


if __name__ == "__main__":
    unittest.main()

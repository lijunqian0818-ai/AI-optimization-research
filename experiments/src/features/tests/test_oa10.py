"""OA10 offline scripts (task list TODO-F3): sampling and verdict. Synthetic
tables in a temporary folder; no original document, no request."""
import os
import tempfile
import unittest

import numpy as np
import pandas as pd

from features import config
from features.audit import oa10_sample as smp, oa10_judge as jdg
from features.store import RawStore
from features.tests import synth
from features.timing import TradingCalendar


class TestAllocation(unittest.TestCase):
    def test_proportional_with_minimum(self):
        sizes = {"2008": 10, "2009": 1000, "2010": 4000, "2011": 3}
        a = smp.allocate(sizes, 300, 5)
        self.assertEqual(sum(a.values()), 300)
        self.assertEqual(a["2011"], 3)                       # a stratum smaller than the minimum is taken whole
        self.assertGreaterEqual(a["2008"], 5)
        # proportional shares 0.6 and 0.18 are below the minimum -> 5 and 3; the other 292 rows go 1 : 4
        self.assertEqual(a, {"2008": 5, "2009": 58, "2010": 234, "2011": 3})
        self.assertEqual(smp.allocate(sizes, 300, 5), a)     # deterministic
        self.assertEqual(smp.allocate({"a": 2, "b": 3}, 300, 5), {"a": 2, "b": 3})      # frame smaller than n
        with self.assertRaises(ValueError):
            smp.allocate({str(k): 100 for k in range(76)}, 300, 5)     # 76 strata x 5 > 300 (the INS case)

    def test_never_exceeds_a_stratum(self):
        rng = np.random.default_rng(0)
        for _ in range(50):
            sizes = {str(k): int(rng.integers(1, 400)) for k in range(int(rng.integers(2, 30)))}
            n = int(rng.integers(20, 300))
            if sum(min(5, v) for v in sizes.values()) > n:
                continue
            a = smp.allocate(sizes, n, 5)
            self.assertEqual(sum(a.values()), min(n, sum(sizes.values())))
            for k in sizes:
                self.assertLessEqual(a[k], sizes[k])
                self.assertGreaterEqual(a[k], min(5, sizes[k]))


class TestSampling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = os.path.join(cls.tmp.name, "raw")
        cls.cal = synth.make_calendar()
        cls.codes = ["sh.600001", "sz.000002", "sz.300003", "sh.688004", "sh.600005", "sz.002006"]
        synth.write_raw_store(cls.root, cls.codes, cls.cal, n_rows=1300, seed=70, n_per_code=90)
        # a B-share row and a row outside the audit period must not enter the frame
        f = os.path.join(cls.root, "zo", "dzjy_mrmx", sorted(os.listdir(os.path.join(cls.root, "zo", "dzjy_mrmx")))[3])
        d = pd.read_parquet(f)
        extra = d.iloc[:1].copy()
        extra["证券代码"] = "900901"
        pd.concat([d, extra], ignore_index=True).to_parquet(f)
        cls.out = os.path.join(cls.tmp.name, "res", "oa10_sample.csv")
        cls.meta = smp.run(cls.out, root=cls.root)
        cls.s = pd.read_csv(cls.out, dtype={"code6": str})

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_sizes_strata_and_hand_recheck(self):
        s = self.s
        self.assertEqual(s["class"].value_counts().to_dict(), {"LHB": 300, "BLK": 300, "INS": 300})
        self.assertEqual(s["sample_id"].nunique(), 900)
        self.assertEqual(s.groupby("class")["hand_recheck"].sum().to_dict(), {"BLK": 30, "INS": 0, "LHB": 30})
        st = pd.read_csv(os.path.splitext(self.out)[0] + "_strata.csv")
        for c in ("lhb", "blk", "ins"):
            g = st[st["class"] == c].groupby("stratum")[["frame_rows", "sampled"]].sum()
            self.assertEqual(int(g["sampled"].sum()), 300)
            self.assertTrue((g["sampled"] >= np.minimum(5, g["frame_rows"])).all(), c)
            self.assertTrue((g["sampled"] <= g["frame_rows"]).all(), c)
        ins = self.s[self.s["class"] == "INS"]
        self.assertTrue(ins["stratum"].str.match(r"^\d{4}/(buy|sell)$").all())
        self.assertTrue(ins["substratum"].str.endswith(("backfilled", "not_backfilled")).all())
        self.assertGreater(self.meta["classes"]["ins"]["sampled_backfilled"], 0)
        self.assertNotIn("900901", set(s["code6"]))
        self.assertEqual(self.meta["classes"]["blk"]["rows_outside_universe_codes"], 1)

    def test_rows_are_real_rows_of_the_raw_files_and_unique(self):
        s = self.s
        self.assertFalse(s.duplicated(["source_file", "row_in_file"]).any())      # no row twice, no replacement
        for cls, (date_col, code_col) in (("LHB", ("上榜日", "代码")), ("BLK", ("交易日期", "证券代码")),
                                           ("INS", ("NOTICE_DATE", "SECURITY_CODE"))):
            for _, r in s[s["class"] == cls].iloc[::37].iterrows():
                raw = pd.read_parquet(os.path.join(self.root, r["source_file"])).iloc[int(r["row_in_file"])]
                self.assertEqual(str(raw[code_col]), r["code6"])
                self.assertEqual(str(pd.Timestamp(raw[date_col]).date()), r["table_date"])

    def test_d_tab_is_the_date_the_pipeline_uses(self):
        cal = RawStore(self.root, data_cutoff="2026-06-30").calendar()
        s = self.s
        d_tab = pd.to_datetime(s["d_tab"])
        self.assertTrue((cal.pos_array(d_tab) >= 0).all())                         # always a trading day
        tbl = pd.to_datetime(s["table_date"])
        lb = s["class"].isin(["LHB", "BLK"])
        self.assertTrue((d_tab[lb] == tbl[lb]).all())
        self.assertEqual(int(s.loc[lb, "d_tab_rolled"].sum()), 0)
        ins = s["class"] == "INS"
        rolled = s.loc[ins, "d_tab_rolled"] == 1
        self.assertGreater(int(rolled.sum()), 0)                                   # the generator dates some on non-trading days
        exp = cal.days[cal.roll_forward_pos(tbl[ins])]
        self.assertTrue((d_tab[ins].values == exp.values).all())
        self.assertTrue((d_tab[ins][rolled.values] > tbl[ins][rolled.values]).all())      # rolled FORWARD
        # first usable decision day = d_tab + lag trading days, lag = the number the features use
        for cls in ("LHB", "BLK", "INS"):
            m = s["class"] == cls
            self.assertTrue((s.loc[m, "lag"] == config.ZO_LAG[cls.lower()]).all())
            exp = cal.days[cal.pos_array(d_tab[m]) + config.ZO_LAG[cls.lower()]]
            self.assertTrue((pd.to_datetime(s.loc[m, "first_usable_decision_day"]).values == exp.values).all())

    def test_reproducible_and_seed_recorded(self):
        out2 = os.path.join(self.tmp.name, "res2", "oa10_sample.csv")
        meta2 = smp.run(out2, root=self.root)
        self.assertEqual(meta2["sample_sha256"], self.meta["sample_sha256"])
        self.assertEqual(self.meta["seed"], smp.SEED)
        self.assertIn("PROVISIONAL", self.meta["status"])
        out3 = os.path.join(self.tmp.name, "res3", "oa10_sample.csv")
        self.assertNotEqual(smp.run(out3, root=self.root, seed=smp.SEED + 1)["sample_sha256"], self.meta["sample_sha256"])

    def test_members_file_restricts_the_frame(self):
        mf = os.path.join(self.tmp.name, "members.txt")
        with open(mf, "w", encoding="utf-8") as fh:
            fh.write("600001\nsz.000002  # comment\n")
        out = os.path.join(self.tmp.name, "res4", "oa10_sample.csv")
        meta = smp.run(out, members_file=mf, root=self.root)
        s = pd.read_csv(out, dtype={"code6": str})
        self.assertEqual(set(s["bs_code"]), {"sh.600001", "sz.000002"})
        self.assertEqual(meta["n_members"], 2)

    def test_no_blacklisted_field_in_the_sample(self):
        with open(self.out, encoding="utf-8-sig") as fh:
            txt = fh.read()
        for bad in ("HOLDER_NAME", "营业部", "名称", "解读", "上榜后"):
            self.assertNotIn(bad, txt)


class TestVerdict(unittest.TestCase):
    def test_clopper_pearson_matches_the_plan(self):
        # PLAN 2.4: with n = 300 the upper limits are 0.99% (0 leaks), 1.57% (1), 2.08% (2); n >= 149 for 0 leaks at 2%
        self.assertAlmostEqual(jdg.clopper_pearson_upper(0, 300), 0.0099, places=4)
        self.assertAlmostEqual(jdg.clopper_pearson_upper(1, 300), 0.0157, places=4)
        self.assertAlmostEqual(jdg.clopper_pearson_upper(2, 300), 0.0208, places=4)
        self.assertLessEqual(jdg.clopper_pearson_upper(0, 149), 0.02)
        self.assertGreater(jdg.clopper_pearson_upper(0, 148), 0.02)
        self.assertAlmostEqual(jdg.clopper_pearson_upper(0, 150), 0.0198, places=4)
        self.assertEqual(jdg.clopper_pearson_upper(5, 5), 1.0)
        # closed form for k = 0: 1 - 0.05^(1/n)
        self.assertAlmostEqual(jdg.clopper_pearson_upper(0, 59), 1 - 0.05 ** (1 / 59), places=12)

    def _sample(self, cal, rows):
        recs = []
        for i, (cls, pos, lag) in enumerate(rows):
            recs.append({"sample_id": f"{cls}-{i:03d}", "class": cls, "table_date": str(cal.days[pos].date()),
                         "d_tab": str(cal.days[pos].date()), "lag": lag})
        return pd.DataFrame(recs)

    def test_signed_quantities(self):
        cal = TradingCalendar(pd.bdate_range("2020-01-01", periods=60))     # pos 2 = Friday 2020-01-03
        fri, mon = cal.days[2], cal.days[3]
        self.assertEqual((fri.day_name(), mon.day_name()), ("Friday", "Monday"))
        sat = fri + pd.Timedelta(days=1)
        sample = self._sample(cal, [("INS", 10, 2), ("INS", 10, 2), ("INS", 10, 2), ("INS", 10, 2), ("INS", 10, 2),
                                    ("INS", 3, 2), ("LHB", 10, 2), ("LHB", 10, 2), ("LHB", 10, 2), ("INS", 10, 1)])
        d = lambda p: str(cal.days[p].date())                               # noqa: E731
        res = pd.DataFrame([
            {"sample_id": sample["sample_id"][0], "status": "found", "d_orig": d(10)},   # same day: usable t+2 >= public t+1
            {"sample_id": sample["sample_id"][1], "status": "found", "d_orig": d(11)},   # table 1 day early: 12 >= 12, covered by the lag
            {"sample_id": sample["sample_id"][2], "status": "found", "d_orig": d(12)},   # table 2 days early: 12 < 13 -> leak
            {"sample_id": sample["sample_id"][3], "status": "found", "d_orig": d(8)},    # table late
            {"sample_id": sample["sample_id"][4], "status": "unverifiable", "d_orig": None},
            # table says Monday (rolled from a Saturday), original dated that Saturday: not early, not late
            {"sample_id": sample["sample_id"][5], "status": "found", "d_orig": str(sat.date())},
            {"sample_id": sample["sample_id"][6], "status": "found", "d_orig": d(10)},
            {"sample_id": sample["sample_id"][7], "status": "not_found", "d_orig": None},        # counts as a leak
            # sample row 8 has no result yet -> pending
            {"sample_id": sample["sample_id"][9], "status": "found", "d_orig": d(11)},   # lag 1, 1 day early: 11 < 12 -> leak
        ])
        x = jdg.classify(sample, res, cal).set_index("sample_id")
        g = lambda i, c: x.loc[sample["sample_id"][i], c]                    # noqa: E731
        self.assertEqual([bool(g(i, "leak")) for i in range(10)],
                         [False, False, True, False, False, False, False, True, False, True])
        self.assertEqual([bool(g(i, "early")) for i in range(10)],
                         [False, True, True, False, False, False, False, False, False, True])
        self.assertEqual([bool(g(i, "late")) for i in range(10)],
                         [False, False, False, True, False, False, False, False, False, False])
        self.assertEqual(g(1, "d_tab_minus_d_orig_trading_days"), -1)
        self.assertEqual(g(3, "d_tab_minus_d_orig_trading_days"), 2)
        self.assertEqual(g(5, "d_tab_minus_d_orig_trading_days"), 0)
        self.assertEqual(g(8, "status"), "pending")
        self.assertFalse(g(4, "verified"))
        s = jdg.summarise(x.reset_index())
        self.assertEqual((s["INS"]["sampled"], s["INS"]["verified"], s["INS"]["unverifiable"], s["INS"]["leak"]),
                         (7, 6, 1, 2))
        self.assertEqual((s["LHB"]["leak"], s["LHB"]["not_found_counted_as_leak"], s["LHB"]["pending"]), (1, 1, 1))
        self.assertFalse(s["LHB"]["pass"])                                   # incomplete, and a leak in 2 verified rows
        self.assertFalse(s["LHB"]["complete"])

    def test_pass_rule_at_n_300(self):
        cal = TradingCalendar(pd.bdate_range("2020-01-01", periods=400))
        sample = self._sample(cal, [("BLK", 20 + i, 2) for i in range(300)])
        base = [{"sample_id": s, "status": "found", "d_orig": t} for s, t in zip(sample["sample_id"], sample["d_tab"])]
        for n_leak, expect in ((0, True), (1, True), (2, False)):
            res = pd.DataFrame(base)
            res.loc[:n_leak - 1, "status"] = "not_found" if n_leak else res["status"]
            s = jdg.summarise(jdg.classify(sample, res, cal))["BLK"]
            self.assertEqual(s["leak"], n_leak)
            self.assertEqual(s["pass"], expect, n_leak)                      # pass iff at most 1 leak (PLAN 2.4)
        # too many unverifiable rows fail criterion (ii) even without a leak
        res = pd.DataFrame(base)
        res.loc[:30, "status"] = "unverifiable"
        s = jdg.summarise(jdg.classify(sample, res, cal))["BLK"]
        self.assertEqual((s["leak"], s["criterion_i_leak"], s["criterion_ii_unverifiable"], s["pass"]),
                         (0, True, False, False))

    def test_input_checks(self):
        cal = TradingCalendar(pd.bdate_range("2020-01-01", periods=60))
        sample = self._sample(cal, [("INS", 10, 2), ("LHB", 10, 2)])
        ok = {"sample_id": sample["sample_id"][0], "status": "found", "d_orig": "2020-01-15"}
        with self.assertRaises(ValueError):                                  # a row that was not pre-drawn
            jdg.classify(sample, pd.DataFrame([ok, {"sample_id": "INS-999", "status": "found", "d_orig": "2020-01-15"}]), cal)
        with self.assertRaises(ValueError):                                  # found without a date
            jdg.classify(sample, pd.DataFrame([{**ok, "d_orig": None}]), cal)
        with self.assertRaises(ValueError):                                  # INS cannot be 'not_found'
            jdg.classify(sample, pd.DataFrame([{**ok, "status": "not_found"}]), cal)
        with self.assertRaises(ValueError):
            jdg.classify(sample, pd.DataFrame([ok, ok]), cal)


if __name__ == "__main__":
    unittest.main()

"""Catalogue = code; whitelist of vendor fields (audit OA2)."""
import glob
import os
import unittest

import pandas as pd

from features import panel, registry, store, zo
from features.config import WHITELIST, BLACKLIST
from features.tests import synth


class TestRegistry(unittest.TestCase):
    def test_columns_equal_catalogue(self):
        cal = synth.make_calendar()
        raw = synth.make_raw_bars("sh.600001", cal, seed=1, n_rows=400)
        tb = synth.make_zo_tables(["sh.600001"], cal, seed=3)
        f = panel.build_stock_features("sh.600001", raw, cal, cal.days[380], synth.make_raw_index(cal), tb)
        cat = registry.catalogue()
        self.assertEqual(set(f.columns), set(cat["name"]))
        self.assertEqual(len(f.columns), len(set(f.columns)))
        # PLAN v0.7 / task list: 158 + 13 + 41 + 34 + 80 + 43 = 369 model features, plus one diagnostic column
        self.assertEqual(cat["group"].value_counts().to_dict(),
                         {"B0": 158, "R_H-hist": 80, "R_O": 43, "Z_O": 41, "R_H-sum": 34, "Z_H": 13, "DIAG": 1})
        self.assertEqual(int((cat["group"] != "DIAG").sum()), 369)
        zh_roles = cat[cat["group"] == "Z_H"].set_index("name")["role"].to_dict()
        self.assertEqual(sorted(k for k, v in zh_roles.items() if v == "primary"),
                         sorted(["zh_cgo_250", "zh_chip_pr", "zh_chip_cost_gap", "zh_chip_band90", "zh_chip_band70",
                                 "zh_chip_overhead", "zh_ato_20_250", "zh_ato_short_20"]))
        self.assertEqual(sorted(k for k, v in zh_roles.items() if v == "variant"),
                         sorted(["zh_cgo_500", "zh_cgo_250_nolag", "zh_cgo_w260", "zh_chip_cost_gap_median",
                                 "zh_ato_20_250_log"]))
        self.assertNotIn("zh_cgo_250_lag1", set(cat["name"]))
        self.assertFalse([n for n in cat["name"] if "turn_cum" in n and n.startswith("rhh")])
        self.assertEqual(sorted(n for n in cat["name"] if n.startswith("zo_lhb_multi")),
                         ["zo_lhb_multi_1", "zo_lhb_multi_20", "zo_lhb_multi_5"])
        self.assertEqual(set(cat.loc[cat["group"] == "DIAG", "role"]), {"diagnostic"})
        self.assertEqual(set(cat["role"]), {"primary", "variant", "control", "diagnostic"})
        fs = registry.feature_sets()
        self.assertEqual(len(fs["Z_H_primary"]), 8)
        self.assertEqual(len(fs["Z_H_variants"]), 5)
        self.assertFalse(set(fs["Z_H_primary"]) & set(fs["Z_H_variants"]))
        self.assertNotIn("diag_filled_xsrc_in_window", sum((fs[g] for g in registry.FEATURE_GROUPS), []))
        # nothing in the catalogue is described as an implementer's free choice any more, except the two items
        # that are listed as such in the test report (weekly warm-up approximation, diagnostic window)
        txt = cat[cat["group"] != "DIAG"][["formula", "source", "timing"]].apply(lambda r: " ".join(r), axis=1)
        self.assertFalse(txt.str.contains("researcher's|added by the researcher|is the researcher").any())
        self.assertTrue((cat[["formula", "fields", "timing", "source"]].apply(lambda s: s.str.len()) > 0).all().all())

    def test_rows_never_exceed_cutoff(self):
        cal = synth.make_calendar()
        raw = synth.make_raw_bars("sh.600001", cal, seed=1, n_rows=400)
        t = cal.days[200]
        f = panel.build_stock_features("sh.600001", raw, cal, t, None, None, groups=("B0", "Z_H", "R_H-sum"))
        self.assertEqual(f.shape[1], 158 + 13 + 34)
        self.assertEqual(f.index.max(), t)
        with self.assertRaises(ValueError):
            panel.build_stock_features("sh.600001", raw, cal, None, None, None, groups=("B0",))

    def test_whitelist_excludes_ex_post_fields(self):
        for table in WHITELIST:
            self.assertFalse(set(WHITELIST[table]) & set(BLACKLIST[table]))
        for bad in ("解读", "上榜后1日", "上榜后2日", "上榜后5日", "上榜后10日", "名称"):
            self.assertNotIn(bad, WHITELIST["lhb_detail"])
        for bad in ("NEWEST_PRICE", "CHANGE_RATE_QUOTES", "CHANGE_RATE", "CLOSE_PRICE", "HOLDER_NAME", "SECURITY_NAME_ABBR"):
            self.assertNotIn(bad, WHITELIST["ins_raw"])

    def test_real_files_are_read_through_the_whitelist(self):
        root = store.RawStore(data_cutoff="2021-12-31").root
        checked = 0
        for sub, table in (("lhb_detail", "lhb_detail"), ("lhb_jgmmtj", "lhb_jgmmtj"), ("dzjy_mrmx", "dzjy_mrmx"),
                           ("ins_raw", "ins_raw")):
            files = sorted(f for f in glob.glob(os.path.join(root, "zo", sub, "*.parquet"))
                           if os.path.basename(f)[:-8].isdigit())
            if not files:
                continue
            df = store.read_whitelisted(files[0], table)
            self.assertEqual(list(df.columns), WHITELIST[table])
            self.assertFalse(set(df.columns) & set(BLACKLIST[table]))
            checked += 1
        if checked == 0:
            self.skipTest("no raw Z_O files on disk")

    def test_eitime_never_reaches_a_feature(self):
        cal = synth.make_calendar()
        tb = synth.make_zo_tables(["sh.600001"], cal, seed=3)
        raw = synth.make_raw_bars("sh.600001", cal, seed=1, n_rows=400)
        a = panel.build_stock_features("sh.600001", raw, cal, cal.days[380], None, tb, groups=("Z_O",))
        ins2 = tb.ins.copy()
        ins2["EITIME"] = "1999-01-01 00:00:00"
        ins2["START_DATE"] = None
        tb2 = zo.ZOTables(tb.lhb, tb.jg, tb.blk, ins2, tb.coverage)
        b = panel.build_stock_features("sh.600001", raw, cal, cal.days[380], None, tb2, groups=("Z_O",))
        pd.testing.assert_frame_equal(a, b)


if __name__ == "__main__":
    unittest.main()

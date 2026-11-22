"""Unit tests of the new pieces of the confirmatory code (synthetic data only; no raw file is read).

    experiments/.venv/Scripts/python.exe -X utf8 -m unittest experiments/src/confirm/tests/test_confirm.py -v
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parents[2]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from confirm import models as M                 # noqa: E402
from confirm import overlap_diagnostic as OD     # noqa: E402
from confirm import strategy as S               # noqa: E402
from confirm import tuning_matrix as TM          # noqa: E402

H = 5


def business_days(y0, y1):
    d, out = date(y0, 1, 1), []
    while d <= date(y1, 12, 31):
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def synthetic(n_names=40, years=(2018, 2020), seed=0, short_day_names=10):
    """Frame, std, cand, noms, ktr, colsets for a small synthetic market."""
    rng = np.random.default_rng(seed)
    days = business_days(*years)
    codes = [f"c{k:03d}" for k in range(n_names)]
    yb = S.year_bounds(days, sorted({d.year for d in days}))
    cand = {i: list(codes) for i in range(len(days))}
    short_day = yb[2020][0] + 7                     # a day with fewer than 15 eligible names
    cand[short_day] = codes[:short_day_names]
    di, cc = [], []
    for i, cs in cand.items():
        for c in cs:
            di.append(i)
            cc.append(c)
    di, cc = np.array(di), np.array(cc, dtype=object)
    cols = ["f1", "f2", "f3", "zh1", "zo_lhb_a", "zo_blk_b", "zo_ins_c"]
    X = rng.random((len(di), len(cols))).astype(np.float32)
    fr = S.Frame(di, cc, X, cols, {(int(i), c): k for k, (i, c) in enumerate(zip(di, cc))})
    rank = pd.Series(rng.random(len(di))).groupby(di).rank(pct=True).to_numpy()
    noms, ktr = {}, {}
    for i in cand:
        rows = [fr.row[(i, c)] for c in cand[i]]
        order = sorted(rows, key=lambda r: (-rank[r], fr.code[r]))
        noms[i] = [fr.code[r] for r in order[:30]]
        ktr[i] = [fr.code[r] for r in order[:90]]
    std = {}
    for r in range(len(di)):
        i, c = int(di[r]), cc[r]
        exit_i = i + H + 1 + (30 if rng.random() < 0.05 else 0)      # 5% delayed exits
        std[(i, c)] = {"filled": bool(rng.random() > 0.02), "rho": float(rng.normal(0, 0.02)),
                       "o1": float(rng.random() < 0.5), "exit_i": exit_i, "unresolved": bool(rng.random() < 0.01),
                       "reason": "ok"}
    colsets = {"-Z": ["f1", "f2", "f3"], "Z_H": ["zh1"], "Z_O": ["zo_lhb_a", "zo_blk_b", "zo_ins_c"]}
    colsets["Z_O*"] = S.zo_star_columns(colsets["Z_O"])
    return SimpleNamespace(days=days, codes=codes, yb=yb, cand=cand, fr=fr, rank=rank, noms=noms, ktr=ktr, std=std,
                           colsets=colsets, short_day=short_day)


def cfg_stub(**kw):
    d = dict(H=H, c=0.5, K=30, base_deploy_start=2018, gate_rule="fixed_count", gate_window="y1", lgbm_threads=1,
             failed_score="exclude", netu15_base_rank_input=False, target_count=15, n_configs=2,
             base_tune_years=(2019,), first_feature_year=2018, criterion_resolved_only=True)
    d.update(kw)
    return SimpleNamespace(**d)


class TestSelection(unittest.TestCase):
    def test_select_top_basic_ties_failed(self):
        sc = {"b": 1.0, "a": 1.0, "c": 3.0, "d": np.nan, "e": None}
        s, nbad = S.select_top(list(sc), sc.get, 2, True)
        self.assertEqual(s, {"c", "a"})                      # tie between a and b broken by code
        self.assertEqual(nbad, 2)
        s, _ = S.select_top(list(sc), sc.get, 2, False)
        self.assertEqual(s, {"a", "b"})
        s, _ = S.select_top(list(sc), sc.get, 10, True)       # fewer eligible than k: submit all eligible
        self.assertEqual(s, {"a", "b", "c"})
        s, _ = S.select_top(list(sc), sc.get, 4, True, failed="last")
        self.assertEqual(s, {"a", "b", "c", "d"})
        s, nbad = S.select_top([], sc.get, 15, True)
        self.assertEqual((s, nbad), (set(), 0))

    def test_vectorised_selection_matches(self):
        rng = np.random.default_rng(3)
        n = 3000
        day = rng.integers(0, 40, n)
        code = np.array([f"x{k:04d}" for k in rng.permutation(n)], dtype=object)
        score = np.round(rng.normal(size=n), 1)               # many ties
        score[rng.random(n) < 0.1] = np.nan
        m = S.topk_mask_by_day(day, code, score, 0.5, 30)
        for d_ in range(40):
            ii = np.flatnonzero(day == d_)
            want, _ = S.select_fixed(list(code[ii]), dict(zip(code[ii], score[ii])).get, 0.5, 30, True)
            self.assertEqual(set(code[ii][m[ii]]), want)


class TestV(unittest.TestCase):
    def test_pooled_and_zero(self):
        self.assertEqual(S.pooled_V(0.0, 0), (0.0, True))
        self.assertEqual(S.pooled_V(3.0, 4), (0.75, False))
        # pooled over years differs from the mean of annual ratios when annual counts differ
        n1, d1, n2, d2 = 1.0, 10, 1.0, 30
        self.assertAlmostEqual(S.pooled_V(n1 + n2, d1 + d2)[0], 2 / 40)
        self.assertNotAlmostEqual(S.pooled_V(n1 + n2, d1 + d2)[0], 0.5 * (n1 / d1 + n2 / d2))

    def test_v_parts(self):
        std = {(1, "a"): {"rho": 0.1}, (1, "b"): {"rho": -0.3}, (2, "a"): {"rho": 0.2}}
        sub = {1: ({"a", "b"}, 1.0), 2: (set(), 1.0)}
        self.assertEqual(S.v_parts(sub, std, [1, 2, 3]), (0.1 - 0.3, 2, 2))


class TestWindowAndGates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = synthetic()

    def ctx(self, **kw):
        s = self.s
        return S.GateContext(s.fr, s.rank, s.noms, s.ktr, s.cand, s.std, None, cfg_stub(**kw), s.days, s.colsets,
                             seed=0, perm_seed=1000)

    def test_window_formulae(self):
        yb = self.s.yb
        lo, hi, kb = S.gate_fit_window(yb, 2020, H, 2018, "y1")
        self.assertEqual((lo, hi, kb), (yb[2018][0], yb[2020][0] - 2 * H - 2, yb[2020][0]))
        lo, hi, kb = S.gate_fit_window(yb, 2020, H, 2018, "y2")
        self.assertEqual(hi, min(yb[2018][1], yb[2019][0] - 2 * H - 2))
        self.assertEqual(kb, yb[2019][0])
        lo, hi, kb = S.gate_fit_window(yb, 2019, H, 2018, "y2")       # Y-2 outside the data
        self.assertEqual(hi, yb[2018][0] - 2 * H - 2)
        self.assertLess(hi, lo)
        with self.assertRaises(ValueError):
            S.gate_fit_window(yb, 2020, H, 2018, "y3")

    def test_labels_respect_known_before(self):
        c = self.ctx()
        kb = self.s.yb[2020][0]
        rows = c.rows_for(self.s.ktr, kb - 60, kb - 1)
        ok, _ = c.labels(rows, "rho", kb)
        for r, o in zip(rows, ok):
            rec = self.s.std[(int(self.s.fr.day[r]), self.s.fr.code[r])]
            self.assertEqual(o, rec["filled"] and not rec["unresolved"] and rec["exit_i"] < kb)
        ok, _ = c.labels(rows, "o1", kb)
        for r, o in zip(rows, ok):
            t = int(self.s.fr.day[r])
            rec = self.s.std[(t, self.s.fr.code[r])]
            self.assertEqual(o, rec["filled"] and t + H + 1 < kb)

    def test_fixed_count_gate_y1(self):
        c = self.ctx()
        sub = c.gate_year("LOSS-LR(-Z)", {"C": 1.0}, 2020)
        fi = c.fit_info[("LOSS-LR(-Z)", 2020, S.json_key({"C": 1.0}))]
        lo_Y = self.s.yb[2020][0]
        self.assertEqual(fi["window"], "y1")
        self.assertLessEqual(fi["last_row_day"], lo_Y - 2 * H - 2)
        self.assertGreater(fi["last_row_day"], self.s.yb[2019][0])          # Y-1 rows are used
        self.assertEqual(fi["label_known_before"], lo_Y)
        for i, (names, _sc) in sub.items():
            self.assertEqual(len(names), math.ceil(0.5 * len(self.s.noms[i])))
            self.assertTrue(names <= set(self.s.noms[i]))
        self.assertEqual(len(sub[self.s.short_day][0]), 5)                   # 10 nominations -> 5
        # the y2 sensitivity uses only rows through Y-2
        c2 = self.ctx(gate_window="y2")
        c2.gate_year("LOSS-LR(-Z)", {"C": 1.0}, 2020)
        fi2 = c2.fit_info[("LOSS-LR(-Z)", 2020, S.json_key({"C": 1.0}))]
        self.assertLessEqual(fi2["last_row_day"], self.s.yb[2018][1])

    def test_netu15_is_not_a_gate_any_more(self):
        c = self.ctx()
        with self.assertRaises(ValueError):
            c.gate_year("NET-U15(-Z)", {}, 2020)

    def test_failed_fit_is_logged(self):
        c = self.ctx(gate_window="y2")
        sub = c.gate_year("LOSS-LR(-Z)", {"C": 1.0}, 2019)                   # no usable row
        self.assertTrue(all(len(n) == 0 for n, _ in sub.values()))
        self.assertEqual(len(c.failures), 1)
        self.assertEqual(c.failures[0]["method"], "LOSS-LR(-Z)")
        self.assertTrue(c.fit_info[("LOSS-LR(-Z)", 2019, S.json_key({"C": 1.0}))]["failed"])

    def test_logit_convergence_logged(self):
        c = self.ctx()
        c.gate_year("LOSS-LR(-Z)", {"C": 1.0}, 2020)
        fi = c.fit_info[("LOSS-LR(-Z)", 2020, S.json_key({"C": 1.0}))]
        self.assertIn("logit_converged", fi)
        self.assertEqual(fi["logit_converged"], fi["logit_n_iter"] < fi["logit_max_iter"])

    def test_thr_policy_uses_threshold_and_y2(self):
        c = self.ctx()
        sub = c.gate_year("LOSS-LR(-Z)-thr", {"C": 1.0}, 2020)
        fi = c.fit_info[("LOSS-LR(-Z)-thr", 2020, S.json_key({"C": 1.0}))]
        self.assertEqual(fi["window"], "y2")
        counts = {len(n) for n, _ in sub.values()}
        self.assertGreater(len(counts), 1)                                   # variable count: threshold rule
        self.assertEqual(S.GateContext.parse_method("LOSS(+Z_O)-thr"), ("LOSS", "+Z_O", True, None))
        self.assertEqual(S.GateContext.parse_method("LOSS(+noise Z_H)#7"), ("LOSS", "+noise Z_H", False, 7))

    def test_design_feature_sets(self):
        c = self.ctx()
        rows = np.arange(50)
        self.assertEqual(S.parse_fset("-Z"), ([], None))
        self.assertEqual(S.parse_fset("+Z_H+Z_O*"), (["Z_H", "Z_O*"], None))
        self.assertEqual(S.parse_fset("+perm Z_O*"), (["Z_O*"], "Z_O*"))
        self.assertEqual(S.parse_fset("+noise Z_H"), (["Z_H"], ("noise", "Z_H")))
        self.assertEqual(self.s.colsets["Z_O*"], ["zo_lhb_a", "zo_blk_b"])
        X = c.design(rows, "+Z_H+Z_O*")
        self.assertEqual(X.shape[1], 3 + 1 + 2 + 1)
        np.testing.assert_array_equal(X[:, :6], self.s.fr.X[rows][:, [0, 1, 2, 3, 4, 5]])
        np.testing.assert_array_equal(X[:, 6], self.s.rank[rows].astype(np.float32))
        self.assertEqual(c.design(rows, "-Z", include_rank=False).shape[1], 3)
        for g in ("Z_H", "Z_O", "Z_O*"):
            c._permuted(np.zeros(0, dtype=int), g)
        Xp = c.design(rows, "+perm Z_O*")
        self.assertEqual(Xp.shape[1], 3 + 2 + 1)
        np.testing.assert_array_equal(Xp[:, :3], X[:, :3])
        day0 = rows[self.s.fr.day[rows] == 0]
        real = np.sort(self.s.fr.X[day0][:, 4])
        perm = np.sort(c._permuted(day0, "Z_O*")[:, 0])
        np.testing.assert_array_equal(real, perm)

    def test_follow_up_draws(self):
        """A4.3 item 6: per-draw permutations are within-day rearrangements, differ across draws, are reproducible
        regardless of order; noise draws are standard normal and replace exactly the group's columns."""
        c, c2 = self.ctx(), self.ctx()
        rows = np.array(sorted(c.rows_for(self.s.ktr, 0, 3)))
        a0 = c.design(rows, "+perm Z_O*", True, 0)
        a1 = c.design(rows, "+perm Z_O*", True, 1)
        _ = c2.design(rows, "+perm Z_O*", True, 1)                          # other order in another context
        b0 = c2.design(rows, "+perm Z_O*", True, 0)
        np.testing.assert_array_equal(a0, b0)
        self.assertFalse(np.array_equal(a0, a1))
        for d_ in np.unique(self.s.fr.day[rows]):
            m = self.s.fr.day[rows] == d_
            np.testing.assert_array_equal(np.sort(a0[m, 3]), np.sort(self.s.fr.X[rows[m], 4]))
        n0 = c.design(rows, "+noise Z_H", True, 0)
        np.testing.assert_array_equal(n0[:, :3], self.s.fr.X[rows][:, :3])
        np.testing.assert_array_equal(n0[:, 4], self.s.rank[rows].astype(np.float32))
        self.assertLess(abs(float(np.mean(n0[:, 3]))), 0.2)
        self.assertGreater(float(np.std(n0[:, 3])), 0.8)
        c.drop_draw("Z_H", "noise", 0)
        np.testing.assert_array_equal(n0, c.design(rows, "+noise Z_H", True, 0))   # regenerated identically


def orders_of(s):
    key = [(int(i), c) for i, c in zip(s.fr.day, s.fr.code)]
    return {"rho": np.array([s.std[k]["rho"] for k in key]), "filled": np.array([s.std[k]["filled"] for k in key]),
            "exit_i": np.array([s.std[k]["exit_i"] for k in key]),
            "unresolved": np.array([s.std[k]["unresolved"] for k in key])}


def brute_V(s, p, te, lo_next):
    num = den = 0
    for d_ in np.unique(s.fr.day[te]):
        ii = np.flatnonzero(s.fr.day[te] == d_)
        pick, _ = S.select_fixed(list(s.fr.code[te][ii]), dict(zip(s.fr.code[te][ii], p[ii])).get, 0.5, 30, True)
        for c in pick:
            r = s.std[(int(d_), c)]
            if (not r["filled"]) or (not r["unresolved"] and 0 <= r["exit_i"] < lo_next):
                num += r["rho"]
                den += 1
    return num / den


class TestBaseV(unittest.TestCase):
    def test_criterion_is_pooled_V_of_own_fixed_count(self):
        s = synthetic(n_names=40, years=(2018, 2020), seed=1)
        y = pd.Series(s.fr.X[:, 0] + np.random.default_rng(2).normal(0, 1, len(s.fr.day))).groupby(s.fr.day).rank(pct=True).to_numpy() - 0.5
        cfg = cfg_stub(n_configs=3, base_tune_years=(2019,), base_deploy_start=2020, first_feature_year=2018)
        logs = []
        cols = np.array([0, 1, 2])                                            # the -Z set
        base, bv, rec = S.base_scores(s.fr, y, s.days, cfg, "ridge", (0, 1), logs.append, orders=orders_of(s),
                                      want_basev=True, col_idx=cols, workers=2)
        tun = base[0]["tuning"]
        lo, hi = s.yb[2019]
        tr = (s.fr.day <= lo - 2 * H - 2) & np.isfinite(y) & (s.fr.day >= s.yb[2018][0])
        te = (s.fr.day >= lo) & (s.fr.day <= hi)
        dropped = 0
        for t in tun:
            p = S._fit_predict("linear", s.fr.X[tr][:, cols], y[tr], s.fr.X[te][:, cols], t["config"], 0, 1)
            self.assertAlmostEqual(t["criterion_V"], brute_V(s, p, te, s.yb[2020][0]), places=12)
            self.assertEqual(len(t["folds"]), 1)                              # ridge: one seed
            dropped += t["dropped_unresolved"]
        self.assertGreater(dropped, 0)                                        # D4 removed late exits
        best_v = max(range(len(tun)), key=lambda k: (tun[k]["criterion_V"], -k))
        self.assertEqual(bv[0]["chosen_index"], best_v)
        # load mode: no tuning, same deployment
        base2, bv2, rec2 = S.base_scores(s.fr, y, s.days, cfg, "ridge", (0, 1), logs.append, orders=orders_of(s),
                                         want_basev=True, col_idx=cols, fixed=rec["chosen"])
        self.assertIsNone(rec2["tuning"])
        np.testing.assert_array_equal(bv2[0]["score"], bv[0]["score"])
        np.testing.assert_array_equal(base2[1]["score"], base[1]["score"])
        days20 = [i for i in range(s.yb[2020][0], s.yb[2020][1] + 1)]
        sub, nbad = S.basev_subs(s.fr, bv[0]["score"], s.cand, days20, 0.5, 30)
        self.assertEqual(nbad, 0)
        self.assertEqual(len(sub[s.short_day][0]), 5)                         # Q1: ceil(0.5 min(30, 10))
        self.assertEqual({len(sub[i][0]) for i in days20 if i != s.short_day}, {15})
        rr, _ = S.rerank_subs(s.fr, bv[0]["score"], s.noms, list(sub), 0.5, 30)
        for i, (names, _sc) in rr.items():
            self.assertTrue(names <= set(s.noms[i]))
            self.assertEqual(len(names), math.ceil(0.5 * len(s.noms[i])))

    def test_netu15_end_to_end(self):
        s = synthetic(n_names=40, years=(2018, 2020), seed=4)
        cfg = cfg_stub(n_configs=2, base_tune_years=(2019,), first_feature_year=2018)
        orders = orders_of(s)
        out, rec = S.netu15_scores(s.fr, s.days, cfg, (0,), [].append, orders, np.array([0, 1, 2]), [2020], workers=1)
        f = rec["tuning"][0]["folds"][0]
        lo19 = s.yb[2019][0]
        self.assertLessEqual(f["train_last_day"], lo19 - 2 * H - 2)
        self.assertEqual(f["year"], 2019)
        # training rows: filled, resolved before the validation year; no base input (3 columns)
        tr = (s.fr.day <= lo19 - 2 * H - 2) & (s.fr.day >= s.yb[2018][0]) & orders["filled"] & ~orders["unresolved"] \
            & (orders["exit_i"] >= 0) & (orders["exit_i"] < lo19)
        self.assertEqual(f["train_rows"], int(tr.sum()))
        te = (s.fr.day >= lo19) & (s.fr.day <= s.yb[2019][1])
        conf = rec["confs"][0]
        p = S._fit_predict("lgbm", s.fr.X[tr][:, [0, 1, 2]], np.where(orders["filled"], orders["rho"], np.nan)[tr],
                           s.fr.X[te][:, [0, 1, 2]], conf, 0, 1)
        self.assertAlmostEqual(rec["tuning"][0]["criterion_V"], brute_V(s, p, te, s.yb[2020][0]), places=12)
        sc = out[0]["score"]
        self.assertTrue(np.isfinite(sc[s.fr.day >= s.yb[2020][0]]).all())
        self.assertTrue(np.isnan(sc[s.fr.day < s.yb[2020][0]]).all())


class TestRound2Rules(unittest.TestCase):
    def test_count_for(self):
        self.assertEqual(S.count_for(30, 0.5, 30), 15)
        self.assertEqual(S.count_for(10, 0.5, 30), 5)
        self.assertEqual(S.count_for(295, 0.5, 30), 15)
        self.assertEqual(S.count_for(10, 0.3, 30), 3)                        # math.ceil(0.3 * 10) would be 4
        self.assertEqual(S.count_for(0, 0.5, 30), 0)
        self.assertEqual(S.count_for(7, 0.5, 30), 4)

    def test_select_fixed_counts_eligible(self):
        sc = {f"x{k}": (float(k) if k % 4 else np.nan) for k in range(40)}   # 30 finite, 10 failed
        s_, nbad = S.select_fixed(list(sc), sc.get, 0.5, 30, True)
        self.assertEqual((len(s_), nbad), (15, 10))
        sc2 = {f"x{k}": float(k) for k in range(12)}
        self.assertEqual(len(S.select_fixed(list(sc2), sc2.get, 0.5, 30, True)[0]), 6)

    def test_resolved_mask(self):
        o = {"filled": np.array([False, True, True, True]), "unresolved": np.array([False, False, True, False]),
             "exit_i": np.array([-1, 9, 5, 10])}
        np.testing.assert_array_equal(S.resolved_mask(np.arange(4), o, 10), [True, True, False, False])


class TestArchiveAndGuards(unittest.TestCase):
    def setUp(self):
        import tempfile
        from confirm import run_confirm as RC
        from confirm.config import ConfirmConfig
        self.RC, self.CC = RC, ConfirmConfig
        self.tmp = Path(tempfile.mkdtemp(dir=str(Path(__file__).resolve().parent)))
        self.cfg = ConfirmConfig(data_cutoff="2021-12-31", bases=("lgbm",), seeds=(0,), n_configs=2,
                                 methods=("G0", "SCORE", "LOSS(-Z)", "TREND", "VT"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, cfg):
        RC = self.RC
        recs = {"base|lgbm": {"confs": M.draw_configs("lgbm", 2), "chosen": {"rank_ic": 0}}}
        tl = {("lgbm", "LOSS(-Z)"): {"configs": M.draw_configs("lgbm", 2), "chosen": 1, "criterion": "V"},
              ("lgbm", "TREND"): {"configs": M.draw_configs("trend", 2), "chosen": 0},
              ("lgbm", "follow-up perm Z_H"): {"configs": [{}], "chosen": 0}}
        return RC.write_archive(self.tmp, cfg, recs, tl, {("lgbm", 0): 0.012345678901234567})

    def test_roundtrip_and_checks(self):
        RC = self.RC
        info = self._write(self.cfg)
        self.assertEqual(info["missing_required"], [])
        p = self.tmp / RC.ARCHIVE_NAME
        a = RC.load_archive(p, self.cfg, info["sha256"])
        self.assertEqual(RC.arch_get(a, "gate|lgbm|LOSS(-Z)", M.draw_configs("lgbm", 2), None), 1)
        self.assertEqual(RC.arch_get(a, "base|lgbm", M.draw_configs("lgbm", 2), ("rank_ic",)), {"rank_ic": 0})
        self.assertEqual(RC.arch_get(a, "vt|lgbm|0", None, None), 0.012345678901234567)     # exact float
        with self.assertRaises(RuntimeError):                                # missing unit: refuse to re-tune
            RC.arch_get(a, "gate|lgbm|NET-K(-Z)", None, None)
        with self.assertRaises(RuntimeError):                                # configuration list differs
            RC.arch_get(a, "gate|lgbm|LOSS(-Z)", M.draw_configs("lgbm", 3), None)
        with self.assertRaises(RuntimeError):                                # wrong expected hash
            RC.load_archive(p, self.cfg, "0" * 64)
        from dataclasses import replace
        with self.assertRaises(RuntimeError):                                # other tuning spec (seeds)
            RC.load_archive(p, replace(self.cfg, seeds=(0, 1)), "")
        a2 = RC.load_archive(p, replace(self.cfg, data_cutoff="2026-06-30"), "")    # spec excludes the cut-off
        self.assertEqual(a2["_sha256"], info["sha256"])
        blob = p.read_bytes().replace(b'"chosen": 1', b'"chosen": 0', 1)     # tampering
        p.write_bytes(blob)
        with self.assertRaises(RuntimeError):
            RC.load_archive(p, self.cfg, "")

    def test_incomplete_archive_refused(self):
        RC = self.RC
        self._write(self.cfg)
        p = self.tmp / RC.ARCHIVE_NAME
        obj = json.loads(p.read_text(encoding="utf-8"))
        del obj["entries"]["grid|lgbm|TREND"]
        blob = json.dumps(obj, sort_keys=True, indent=1).encode()
        p.write_bytes(blob)
        (self.tmp / (RC.ARCHIVE_NAME + ".sha256")).write_text(hashlib.sha256(blob).hexdigest(), encoding="utf-8")
        with self.assertRaises(RuntimeError) as cm:
            RC.load_archive(p, self.cfg, "")
        self.assertIn("incomplete", str(cm.exception))

    def test_guards(self):
        RC = self.RC
        out = "experiments/results/confirm/_never"
        self.assertEqual(RC.main(["--data-cutoff", "2022-01-04", "--out", out]), 2)
        self.assertEqual(RC.main(["--data-cutoff", "2022-01-04", "--holdout-approved", "--out", out]), 2)  # no archive
        self.assertEqual(RC.main(["--data-cutoff", "2020-12-31", "--tune-only", "--out", out]), 2)
        self.assertFalse((RC.ROOT / out).exists())

    def test_listing_cut_wrapper(self):
        from confirm import data as Dm
        import engine.io_baostock as eio
        f = self.tmp / "universe"
        f.mkdir()
        pd.DataFrame({"code": ["a", "b", "c"], "ipoDate": ["2010-01-04", "2023-05-05", ""],
                      "outDate": ["2024-01-02", "2015-03-03", None]}).to_parquet(f / "bs_stock_basic.parquet")
        Dm.install_listing_cut(date(2021, 12, 31))
        df = eio._read_parquet(f / "bs_stock_basic.parquet")
        self.assertEqual(list(df["ipoDate"]), ["2010-01-04", "", ""])
        self.assertEqual(list(df["outDate"]), ["", "2015-03-03", ""])
        other = self.tmp / "x.parquet"
        pd.DataFrame({"ipoDate": ["2030-01-01"]}).to_parquet(other)
        self.assertEqual(list(eio._read_parquet(other)["ipoDate"]), ["2030-01-01"])   # other files untouched

    def test_panel_provenance(self):
        from confirm import data as Dm
        calls = []
        orig = Dm.build_panel
        Dm.build_panel = lambda cfg, codes, pdir, raw, overwrite=False: (calls.append(overwrite) or pd.DataFrame({"status": []}))
        try:
            pdir = self.tmp / "panel"
            _, a1 = Dm.build_panel_checked(self.cfg, ["x"], pdir, Path("."), "h1", lambda *_: None)
            _, a2 = Dm.build_panel_checked(self.cfg, ["x"], pdir, Path("."), "h1", lambda *_: None)
            _, a3 = Dm.build_panel_checked(self.cfg, ["x"], pdir, Path("."), "h2", lambda *_: None)   # other raw tree
            from dataclasses import replace
            _, a4 = Dm.build_panel_checked(replace(self.cfg, data_cutoff="2020-12-31"), ["x"], pdir, Path("."), "h2",
                                           lambda *_: None)
        finally:
            Dm.build_panel = orig
        self.assertEqual((a1, a2, a3, a4), ("rebuild", "reuse", "rebuild", "rebuild"))
        self.assertEqual(calls, [True, False, True, True])


class TestDiagnosticIdentity(unittest.TestCase):
    def _dump(self, unequal=False, seed=0):
        rng = np.random.default_rng(seed)
        rows, ddays = [], []
        names = [f"n{k}" for k in range(30)]
        rho = {(i, c): rng.normal(0, 0.03) for i in range(100) for c in names}
        for s in (0, 1, 2):
            for i in range(100):
                for m, k in (("G", 15), ("H", 14 if (unequal and i % 7 == 0) else 15)):
                    if i == 50:
                        k = 0                                              # a decision day with zero submissions
                    for c in rng.choice(names, size=k, replace=False):
                        rows.append(("b", s, m, i, c, rho[(i, c)]))
                    ddays.append(("b", s, m, i, k))
        sub = pd.DataFrame(rows, columns=["base", "seed", "method", "i", "code", "rho"])
        dd = pd.DataFrame(ddays, columns=["base", "seed", "method", "i", "S_day"])
        return sub, dd

    def test_identity_equal_counts(self):
        sub, dd = self._dump()
        parts = OD.contrast_parts(sub, dd, "G", "H", np.arange(100), [0, 1, 2])
        sm = OD.summarise(parts, {i: 2021 for i in range(100)})
        self.assertTrue(sm["identity_applies"])
        self.assertLess(sm["identity_residual"], 1e-10 / OD.BP)
        self.assertLess(sm["daily_identity_max_abs_residual"], 1e-12)
        # brute-force delta
        g = sub[sub["method"] == "G"]
        h = sub[sub["method"] == "H"]
        want = g["rho"].sum() / len(g) - h["rho"].sum() / len(h)
        self.assertAlmostEqual(sm["delta_bp"], want * OD.BP, places=9)
        self.assertEqual(sm["days_seed_pairs"], 300)                          # the zero-submission day is kept

    def test_unequal_counts_flagged(self):
        sub, dd = self._dump(unequal=True)
        sm = OD.summarise(OD.contrast_parts(sub, dd, "G", "H", np.arange(100), [0, 1, 2]), {})
        self.assertFalse(sm["identity_applies"])
        self.assertGreater(sm["days_with_unequal_counts"], 0)
        self.assertLess(sm["daily_identity_max_abs_residual"], 1e-12)


class TestTuningAndConfigs(unittest.TestCase):
    def test_draw_order_same_set_as_pilot(self):
        for kind, n in (("lgbm", 30), ("lgbm", 4), ("linear", 4), ("trend", 4)):
            a = M.draw_configs(kind, n)
            rng = np.random.default_rng(20261115)
            from confirm.models import LGBM_SPACE  # noqa: F401
            self.assertEqual(len(a), min(n, len(a)))
            again = M.draw_configs(kind, n)
            self.assertEqual(a, again)
        # pilot: the same set, sorted by grid index
        import itertools
        keys = list(M.LGBM_SPACE)
        grid = [dict(zip(keys, v)) for v in itertools.product(*[M.LGBM_SPACE[k] for k in keys])]
        pick = np.random.default_rng(20261115).choice(len(grid), size=30, replace=False)
        pilot = [grid[k] for k in sorted(pick)]
        conf = M.draw_configs("lgbm", 30)
        self.assertEqual(sorted(map(str, conf)), sorted(map(str, pilot)))
        self.assertEqual(conf, [grid[k] for k in pick])
        del rng

    def test_best_after(self):
        v = [0.1, np.nan, 0.3, -1.0, 0.2, 0.5] + [0.0] * 24
        ba = TM.best_after(v)
        self.assertEqual(ba[5], 0.3)
        self.assertEqual(ba[10], 0.5)
        self.assertEqual(ba[30], 0.5)
        self.assertIsNone(TM.best_after([0.1, 0.2])[5])


class TestHoldoutGuard(unittest.TestCase):
    def test_refuses_holdout_cutoff(self):
        from confirm import run_confirm as RC
        self.assertEqual(RC.main(["--data-cutoff", "2022-01-04", "--out", "experiments/results/confirm/_never"]), 2)
        self.assertFalse((RC.ROOT / "experiments/results/confirm/_never").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)

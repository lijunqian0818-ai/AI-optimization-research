"""Tests of the v0.8 code changes of the engine (experiments/IMPLEMENTATION_CHANGES_v0.8.md):

  C-1  event table rule 2a "confirmed by the reference price" (PLAN v0.8 H-2), production configuration
  C-3  RC-18 element cum3 in the rule calendar (PLAN v0.8 J-1)
  C-5  counts of sell orders whose commission exceeds their value, negative-cash sleeve-days (H-14)
  C-8  hard data cut-off of the loader (U-PILOT, section 13A)

Expected values are written by hand from the task list and PLAN v0.8 section 3.11.  Constructed data only
(the loader tests write a tiny imitation of experiments/data/raw into a temporary directory)."""
from __future__ import annotations

import tempfile
from dataclasses import replace
from datetime import date
from pathlib import Path

import pandas as pd

from common import T, panel

from engine import datacut as dc
from engine import event_table as et
from engine import io_baostock as io
from engine import rule_calendar as rc
from engine import simulate
from engine.config import EngineConfig, PARAM_STATUS
from engine.synth import weekdays

d = date.fromisoformat
CFG = EngineConfig()
SH = "sh.600001"
START = d("2021-03-01")
DAYS = weekdays(START, 12)


def Sv(p):
    return {"s": "S", "o": p, "c": p, "pc": p, "amt": 0.0, "st": False}


def _ex_rows(ex=5, new=9.5, n=12):
    return [T(10, 10, 10)] * ex + [T(new, new, new)] * (n - ex)


def _src(source, ex, rec, cash=0.5, bonus=0.0, **kw):
    return et.SrcRow(source, SH, DAYS[ex] if ex is not None else None, DAYS[rec] if rec is not None else None, cash,
                     bonus, **kw)


FLAG = "single source / disagreement, confirmed by the reference price"


# ============================================================ C-1
def test_c1a_single_source_confirmed_within_0005_not_beyond():
    """(a) one source; previous close 10.00, cash 0.50 -> implied reference price 9.50.  `preclose` 9.497
    (difference 0.003 <= 0.005): booked with the source's values and flagged.  `preclose` 9.492 (0.008):
    pending rule (forced U), reason 'no matching source'."""
    m = panel(START, {SH: _ex_rows(new=9.497)})
    t = et.build(m, [_src("EV2", 5, 4)], [], CFG)
    ev, = t.events
    assert (ev.forced_class, ev.ex_date, ev.record_date, ev.gross_cash, ev.phi) == (None, DAYS[5], DAYS[4], 0.5, 1.0)
    assert any(f.get("kind", "").startswith(FLAG) for f in t.flags), t.flags
    c = t.counts
    assert (c["confirmed_by_price_single"], c["single_source"], c["booked_dist_events"], c["forced_U_events"]) == (1, 1, 1, 0)
    assert t.hand_check == [] and t.urs == set()
    assert t.by_year["2021"]["confirmed_by_price:listed"] == 1
    m2 = panel(START, {SH: _ex_rows(new=9.492)})
    t2 = et.build(m2, [_src("EV2", 5, 4)], [], CFG)
    assert [e.forced_class for e in t2.events] == ["U"] and t2.counts["rule2a_no_matching_source"] == 1
    assert t2.counts["confirmed_by_price_single"] == 0 and t2.urs == set()
    assert t2.by_year["2021"]["pending:single_source:listed"] == 1
    return {"booked": 1, "pending": 1}


def test_c1b_disagreement_exactly_one_matching_source():
    """(b) EV1 0.50 and EV2 0.40 disagree; the step is to 9.50: EV1 implies 9.50 (match), EV2 9.60 (no) ->
    booked with EV1's values.  Both matching (0.50 and 0.5002: they disagree by more than 0.0001 but both
    imply a price within 0.005) -> pending rule.  Neither matching -> pending rule.  A matching single source
    whose record date is not the trading day before the ex-date -> pending rule."""
    m = panel(START, {SH: _ex_rows()})
    t = et.build(m, [_src("EV1", 5, 4, cash=0.5), _src("EV2", 5, 4, cash=0.4)], [], CFG)
    ev, = t.events
    assert ev.forced_class is None and ev.gross_cash == 0.5 and t.counts["confirmed_by_price_disagreement"] == 1
    t2 = et.build(m, [_src("EV1", 5, 4, cash=0.5), _src("EV2", 5, 4, cash=0.5002)], [], CFG)
    assert t2.counts["disagreement"] == 1 and t2.counts["rule2a_several_matching_sources"] == 1
    assert [e.forced_class for e in t2.events] == ["U"]
    t3 = et.build(m, [_src("EV1", 5, 4, cash=0.4), _src("EV2", 5, 4, cash=0.3)], [], CFG)
    assert t3.counts["rule2a_no_matching_source"] == 1 and [e.forced_class for e in t3.events] == ["U"]
    t4 = et.build(m, [_src("EV2", 5, 3)], [], CFG)
    assert t4.counts["rule2a_record_date_relation"] == 1 and [e.forced_class for e in t4.events] == ["U"]
    return {"cases": 4}


def test_c1c_ex_date_inside_suspension_step_at_resumption():
    """(c) ex-date (day 5) inside a suspension (days 4-5), the reference-price step on the resumption day
    6 (previous close 10.00, `preclose` 9.50); one source with cash 0.50: confirmed by the reference price,
    booked on its ex-date (rule 7); the step is explained once (no URS), and it is NOT counted again as a
    rule 9 (a) match."""
    rows = [T(10, 10, 10)] * 4 + [Sv(10.0), Sv(10.0)] + [T(9.5, 9.5, 9.5)] * 6
    m = panel(START, {SH: rows})
    t = et.build(m, [_src("EV2", 5, 4)], [], CFG)
    ev, = t.events
    assert (ev.forced_class, ev.ex_date, ev.gross_cash) == (None, DAYS[5], 0.5)
    c = t.counts
    assert t.urs == set() and c["steps_total"] == 1 and c["steps_explained_by_event"] == 1 and c["steps_urs"] == 0
    assert c["conflict_a_matched"] == 0 and c["rule2a_step_at_resumption"] == 1 and c["confirmed_by_price_single"] == 1
    assert any("step at the resumption" in f.get("kind", "") for f in t.flags)
    return {"steps_explained_by_event": c["steps_explained_by_event"]}


def test_c1d_duplicate_rows_stay_pending():
    """(d) two rows of one source on one (code, ex-date) - here identical and matching the step - are
    ineligible for rules 2 and 2a: pending rule (H-9)."""
    m = panel(START, {SH: _ex_rows()})
    t = et.build(m, [_src("EV2", 5, 4), _src("EV2", 5, 4)], [], CFG)
    assert [e.forced_class for e in t.events] == ["U"] and t.counts["duplicate_rows_in_one_source"] == 1
    assert t.counts["confirmed_by_price_single"] == 0 and t.counts["confirmed_by_price_disagreement"] == 0


def test_c1e_two_source_events_unchanged_and_rule_2a_switch():
    """(e) events confirmed by two sources are as in v0.7 (the expected tuple of the v0.7 test), and the
    v0.8 table differs from a build without rule 2a (= the v0.7 table) only in the event rule 2a confirms."""
    m = panel(START, {SH: [T(10, 10, 10)] * 5 + [T(9.5, 9.5, 9.5)] * 17 + [T(9.0, 9.0, 9.0)] * 18})
    D = m.days
    rows = [et.SrcRow("EV1", SH, D[5], D[4], 0.5, 0.0), et.SrcRow("EV2", SH, D[5], D[4], 0.50005, 0.0),   # rule 2
            et.SrcRow("EV2", SH, D[22], D[21], 0.5, 0.0)]                                                 # rule 2a
    t8 = et.build(m, rows, [], CFG)
    t7 = et.build(m, rows, [], CFG, rule_2a=False)
    key = lambda e: (e.kind, e.ex_date, e.record_date, e.gross_cash, e.phi, e.forced_class, e.pay_date)   # noqa: E731
    assert [key(e) for e in t8.events if e.ex_date == D[5]] == [key(e) for e in t7.events if e.ex_date == D[5]]         == [("dist", D[5], D[4], 0.5, 1.0, None, None)]
    assert [key(e) for e in t8.events if e.ex_date == D[22]] == [("dist", D[22], D[21], 0.5, 1.0, None, None)]
    assert [key(e) for e in t7.events if e.ex_date == D[22]] == [("dist", D[22], D[21], 0.5, 1.0, "U", None)]
    assert t8.urs == t7.urs == set()
    return {"v08_events": len(t8.events), "v07_events": len(t7.events)}


def test_c1_production_configuration_in_config():
    """H-2: the production configuration is fixed in the engine configuration, and load_market uses it."""
    assert CFG.event_pending == "U" and CFG.event_undated_rights == "exclude"
    assert "H-2" in PARAM_STATUS["event_pending"] and "H-2" in PARAM_STATUS["event_undated_rights"]
    import inspect
    src = inspect.getsource(et)
    assert "never be used for a result" not in src and "pre-declared EXPLORATORY sensitivity" in src


# ============================================================ C-3
def test_c3_cum3_element_and_chinext_boundary():
    """RC-18 rows carry cum3: 0.20 under 'deviation', 0.30 under 'change'; ChiNext switches on
    2020-08-24 (2020-08-23 still 0.20); the status of the element is written in each row's note."""
    assert rc.lhb_thresholds(d("2020-08-23"), "chinext")["cum3"] == 0.20
    assert rc.lhb_thresholds(d("2020-08-24"), "chinext")["cum3"] == 0.30
    for x in ("2008-01-02", "2020-08-24", "2026-06-30"):
        assert rc.lhb_thresholds(d(x), "main")["cum3"] == 0.20 and rc.lhb_thresholds(d(x), "star")["cum3"] == 0.30
    rows = [r for r in rc.RULES if r.key.startswith("lhb_thr:")]
    assert len(rows) == 4 and all("cum3" in r.value and "cum3: unverified, PLAN 3.10 item 22" in r.note for r in rows)
    assert all((r.value["cum3"] == 0.20) == (r.value["kind"] == "deviation") for r in rows)


# ============================================================ C-5
def test_c5_sell_commission_exceeds_value_and_no_cash():
    """H-14: lot-rounding-free configuration with the 5-yuan minimum.  H = 2, K = 1, three sleeves of 5.5
    yuan.  Day 1 (sleeve 1): budget 0.5 yuan -> ~0.045 shares; sold on day 3 for ~0.45 yuan < commission 5:
    the sale is booked, counted once, and the sleeve's cash becomes negative.  Day 4 (sleeve 1 again): the
    nomination gets no order, reason 'no_cash'."""
    rows = [T(10, 10, 10)] * 8
    m = panel(START, {SH: rows})
    cfg = replace(CFG, H=2, K=1, W0=3 * 5.5, min_commission=5.0)
    led, orders = simulate.run(m, cfg, {1: [(SH, 1.0)], 4: [(SH, 1.0)]}, 1, 6)
    sells = [o for o in orders if o["side"] == "sell"]
    assert len(sells) == 1 and sells[0]["filled"] and sells[0]["i"] == 3
    tr = [t for t in led.trades if t["side"] == "sell"][0]
    assert tr["costs"]["commission"] == 5.0 and tr["amount"] < 5.0
    assert led.extra_counts["sell_commission_exceeds_value"] == 1
    assert led.cash[1] < 0 and led.extra_counts["sleeve_days_negative_cash"] >= 1
    b4 = [o for o in orders if o["side"] == "buy" and o["i"] == 4]
    assert [(o["reason"], o["submitted"]) for o in b4] == [("no_cash", False)]
    rec = simulate.result_record(led, orders, 1, 6)
    assert rec["sell_commission_exceeds_value"] == 1 and rec["sleeve_days_negative_cash"] == led.extra_counts["sleeve_days_negative_cash"]
    return {"negative_cash_sleeve_days": led.extra_counts["sleeve_days_negative_cash"]}


# ============================================================ C-8
def _write_raw_late(root: Path):
    """Imitation of data/raw spanning 2008-01-02 .. 2008-03-31 with an event after the cut-off used below."""
    from test_v07_components import _write_raw
    tdays = _write_raw(root)
    return tdays


def test_c8a_rows_after_the_cutoff_never_reach_the_market():
    """(a) cut-off 2008-02-29: the panel ends on the last trading day <= the cut-off; no bar row after it is
    in the container; the Sina 'plan' row (ex-date 2008-03-20) and the rights row (ex-date 2008-03-10,
    record 2008-03-03) are not read; sz.000002's delisting (2008-02-15) is before the cut-off and kept.
    Cut-off 2008-02-10: the delisting date lies after it and is not known (the name is listed through the
    end of the panel); the dividend with ex-date 2008-02-01 is still read.  No data_cutoff -> refused."""
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw"
        tdays = _write_raw_late(raw)
        m, rep = io.load_market(raw, ["sh.600001", "sz.000002"], events="sina", data_cutoff="2008-02-29",
                                dispositions_path=Path(tmp) / "none.csv")
        assert m.days[-1] == d("2008-02-29") and m.days == [x for x in tdays if x <= d("2008-02-29")]
        assert rep["data_cutoff"] == "2008-02-29" and m.data_cutoff == d("2008-02-29")
        assert sorted(e.kind for e in m.events["sh.600001"]) == ["dist"]
        assert rep["events"]["not_in_table"] == [] or all("2008-03" not in s for s in rep["events"]["not_in_table"])
        assert m.secs["sz.000002"].delist_i is not None
        m2, rep2 = io.load_market(raw, ["sh.600001", "sz.000002"], events="sina", data_cutoff="2008-02-10",
                                  dispositions_path=Path(tmp) / "none.csv")
        assert m2.days[-1] <= d("2008-02-10") and m2.secs["sz.000002"].delist_i is None
        assert [e.ex_date for e in m2.events.get("sh.600001", []) if e.kind == "dist"] == [d("2008-02-01")]
        assert [e for e in m2.events.get("sh.600001", []) if e.kind == "rights"] == []
        for bad in (None,):
            try:
                io.load_market(raw, ["sh.600001"], events="none", data_cutoff=bad)
                raise AssertionError("a missing cut-off must be refused")
            except dc.CutoffError:
                pass
        try:
            io.load_market(raw, ["sh.600001"], events="none")          # keyword is required
            raise AssertionError("load_market without data_cutoff must fail")
        except TypeError:
            pass
    return {"panel_end": str(m.days[-1])}


def test_c8a_reader_refuses_late_rows_and_null_dates():
    """read_parquet_cut filters while reading; a frame that still carries a later row is refused; a file
    whose date column is all-null yields no row; period files after the cut-off are not openable."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "x.parquet"
        pd.DataFrame({"date": ["2021-12-30", "2021-12-31", "2022-01-04", "2026-01-05"], "v": [1, 2, 3, 4]}).to_parquet(p)
        df = dc.read_parquet_cut(p, "date", "2021-12-31")
        assert list(df["v"]) == [1, 2]
        try:
            dc.assert_no_row_after(pd.DataFrame({"date": ["2022-01-04"]}), "date", "2021-12-31", "t")
            raise AssertionError("must raise")
        except dc.CutoffError:
            pass
        q = Path(tmp) / "y.parquet"
        pd.DataFrame({"date": [None, None], "v": [1, 2]}).to_parquet(q)
        assert len(dc.read_parquet_cut(q, "date", "2021-12-31")) == 0
    assert dc.period_ok("202112", "2021-12-31") and not dc.period_ok("202201", "2021-12-31")
    assert dc.period_ok("2021", "2021-12-31") and not dc.period_ok("2022", "2021-12-31")
    assert dc.clip_date("2024-05-01", "2021-12-31") is None and dc.clip_date("2020-05-01", "2021-12-31") == d("2020-05-01")


def test_c8c_result_files_carry_the_cutoff():
    """(c) simulate.result_record carries data_cutoff (the market's), write_result refuses a record without it."""
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw"
        _write_raw_late(raw)
        m, _ = io.load_market(raw, ["sh.600001"], events="none", data_cutoff="2008-02-29",
                              dispositions_path=Path(tmp) / "none.csv")
        cfg = replace(CFG, H=2, K=1)
        led, orders = simulate.run(m, cfg, {2: [("sh.600001", 1.0)]}, 1, m.T - 1)
        rec = simulate.result_record(led, orders, 1, m.T - 1)
        assert rec["data_cutoff"] == "2008-02-29"
        simulate.write_result(Path(tmp) / "r.json", rec)
        bad = dict(rec)
        del bad["data_cutoff"]
        try:
            simulate.write_result(Path(tmp) / "bad.json", bad)
            raise AssertionError("must refuse")
        except ValueError:
            pass


def test_c8_factor_directory_never_opened_through_the_cut_reader():
    """FC-A4 together with C-8: every raw file the loader opens goes through datacut or _read_parquet;
    none is in the vendor factor directory (spied on all three readers)."""
    opened = []
    r1, r2, r3 = dc.read_parquet_cut, dc.read_events_cut, io.pd.read_parquet

    def s1(path, *a, **k):
        opened.append(str(path))
        return r1(path, *a, **k)

    def s2(path, *a, **k):
        opened.append(str(path))
        return r2(path, *a, **k)

    def s3(path, *a, **k):
        opened.append(str(path))
        return r3(path, *a, **k)
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw"
        _write_raw_late(raw)
        io.dc.read_parquet_cut, io.dc.read_events_cut, io.pd.read_parquet = s1, s2, s3
        try:
            for mode in ("sina", "merged", "none"):
                io.load_market(raw, ["sh.600001", "sz.000002"], events=mode, data_cutoff="2008-03-31",
                               dispositions_path=Path(tmp) / "none.csv")
        finally:
            io.dc.read_parquet_cut, io.dc.read_events_cut, io.pd.read_parquet = r1, r2, r3
    assert any("bs_daily" in p for p in opened) and any("sina_dividend" in p for p in opened)
    assert not any("adjust_factor" in p for p in opened), opened
    return {"files_opened": len(opened)}


TESTS = [test_c1a_single_source_confirmed_within_0005_not_beyond, test_c1b_disagreement_exactly_one_matching_source,
         test_c1c_ex_date_inside_suspension_step_at_resumption, test_c1d_duplicate_rows_stay_pending,
         test_c1e_two_source_events_unchanged_and_rule_2a_switch, test_c1_production_configuration_in_config,
         test_c3_cum3_element_and_chinext_boundary, test_c5_sell_commission_exceeds_value_and_no_cash,
         test_c8a_rows_after_the_cutoff_never_reach_the_market, test_c8a_reader_refuses_late_rows_and_null_dates,
         test_c8c_result_files_carry_the_cutoff, test_c8_factor_directory_never_opened_through_the_cut_reader]

if __name__ == "__main__":
    from common import run_tests
    run_tests("v08_changes", TESTS, "v08_changes.json")

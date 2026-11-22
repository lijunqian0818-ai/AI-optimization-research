"""Components built for PLAN v0.7: the corporate-event table (PLAN 3.11 rules 1-12; TODO-E1), the
universe and candidate filters (PLAN 2.3, 3.5; TODO-E2), the raw-file loader with its v0.7 filters
(ENG-8, ENG-13 (b)) and the FC-A4 guard (TODO-E12).

Constructed data only.  The loader tests write a tiny imitation of experiments/data/raw into a
temporary directory; nothing under experiments/data is read or written here.  Expected outcomes
are written by hand from the rule texts.
"""
from __future__ import annotations

import dataclasses
import tempfile
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from common import N, S, T, X, close, panel, run_tests

from engine import event_table as et
from engine import io_baostock as io
from engine import universe as uni
from engine.config import EngineConfig
from engine.labels import label_o1
from engine.market import Event, Market, MarketDataError, Sec, Valuer
from engine.synth import make_market, weekdays

d = date.fromisoformat
CFG = EngineConfig()
SH = "sh.600001"
START = d("2021-03-01")
DAYS = weekdays(START, 12)


def Sv(p):
    """Suspended-day row as the bar source writes it: open = close = preclose = carried price."""
    return {"s": "S", "o": p, "c": p, "pc": p, "amt": 0.0, "st": False}


def _ex_rows(ex=5, new=9.5, n=12):
    return [T(10, 10, 10)] * ex + [T(new, new, new)] * (n - ex)


def _src(source, ex, rec, cash=0.5, bonus=0.0, **kw):
    return et.SrcRow(source, SH, DAYS[ex] if ex is not None else None, DAYS[rec] if rec is not None else None, cash, bonus, **kw)


def _kinds(t):
    return sorted(h["kind"] for h in t.hand_check)


def _dist(t):
    return [e for e in t.events if e.kind == "dist"]


# ================================================================== event table
def test_event_two_and_three_source_confirmation():
    """Rule 2: confirmed iff two of EV1-EV3 agree on cash (0.0001), ratio and record date.  The step
    of `preclose` on the ex-date is explained; nothing goes to the hand check or to URS."""
    m = panel(START, {SH: _ex_rows()})
    t = et.build(m, [_src("EV1", 5, 4), _src("EV2", 5, 4, cash=0.50005)], [], CFG)
    ev, = t.events
    assert (ev.kind, ev.ex_date, ev.record_date, ev.gross_cash, ev.phi, ev.forced_class) == ("dist", DAYS[5], DAYS[4], 0.5, 1.0, None)
    assert t.urs == set() and t.hand_check == [] and t.u_spans == {}
    c = t.counts
    assert (c["confirmed_2_sources"], c["confirmed_3_sources"], c["matched_same_day"], c["steps_total"],
            c["steps_explained_by_event"], c["booked_dist_events"], c["steps_urs"]) == (1, 0, 1, 1, 1, 1, 0)
    # v0.8 (C-1): the counts by year also record the confirmation category (PLAN 3.11 "Mechanical rule" item 4)
    assert t.by_year == {"2021": {"booked:listed": 1, "confirmed_2_sources:listed": 1}}
    t3 = et.build(m, [_src("EV1", 5, 4), _src("EV2", 5, 4), _src("EV3", 5, 4, pay_date=DAYS[7])], [], CFG)
    assert t3.counts["confirmed_3_sources"] == 1 and t3.events[0].pay_date == DAYS[7]
    # the third source disagrees: still confirmed by the two that agree
    t2 = et.build(m, [_src("EV1", 5, 4), _src("EV2", 5, 4), _src("EV3", 5, 4, cash=0.3)], [], CFG)
    assert t2.counts["confirmed_2_sources"] == 1 and t2.events[0].gross_cash == 0.5 and t2.hand_check == []
    # same inputs, same hash; different content, different hash
    assert t.content_hash() == et.build(m, [_src("EV1", 5, 4), _src("EV2", 5, 4, cash=0.50005)], [], CFG).content_hash()
    assert t.content_hash() != t3.content_hash()
    # install: the engine books it
    m2 = panel(START, {SH: _ex_rows()})
    t.install(m2)
    assert len(m2.events_on(SH, 5)) == 1 and m2.problems == []


def test_event_single_source_and_disagreement_go_to_hand_check():
    """Rule 3.  Pending rule: not booked, outcome U on the ex-date (forced_class 'U'); the step of that
    day is not a URS step.  A resolution with the announcement's values books the event.
    pending='provisional' (dry runs only) books the first source's values.
    v0.8 (C-1, rule 2a): with the v0.7 panel (step of exactly 0.50 = the announced cash) a single source is
    now CONFIRMED BY THE REFERENCE PRICE, so the pending-rule cases use a step of 0.51: the implied reference
    price lies 0.01 yuan from `preclose` - above the 2a tolerance (0.005), below the hand-check tolerance (0.02).
    Expectation changed by ruling H-2; the confirmation itself is tested in test_v08_changes.py."""
    m = panel(START, {SH: _ex_rows(new=9.49)})
    t = et.build(m, [_src("EV2", 5, 4)], [], CFG)
    assert _kinds(t) == ["single_source"] and t.counts["single_source"] == 1
    assert [(e.forced_class, e.ex_date) for e in t.events] == [("U", DAYS[5])] and t.urs == set()
    m2 = panel(START, {SH: _ex_rows(new=9.49)})
    t.install(m2)
    assert m2.events_on(SH, 5) == [] and label_o1(m2, Valuer(m2), SH, 3, 100.0, 10.0, 0.77, 2, CFG).outcome == "U"
    td = et.build(m, [_src("EV1", 5, 4), _src("EV2", 5, 4, cash=0.4)], [], CFG)
    assert _kinds(td) == ["disagreement"] and td.events[0].forced_class == "U"
    assert et.build(m, [_src("EV1", 5, 4), _src("EV2", 5, 4, cash=0.5002)], [], CFG).counts["disagreement"] == 1   # > 0.0001
    assert et.build(m, [_src("EV1", 5, 4), _src("EV2", 5, 3)], [], CFG).counts["disagreement"] == 1               # record dates
    assert et.build(m, [_src("EV1", 5, 4, bonus=0.1), _src("EV2", 5, 4)], [], CFG).counts["disagreement"] == 1    # ratio
    # two rows of one source on one ex-date (even identical ones): no rule in the plan -> hand check
    tdup = et.build(m, [_src("EV1", 5, 4), _src("EV2", 5, 4), _src("EV3", 5, 4), _src("EV3", 5, 4)], [], CFG)
    assert _kinds(tdup) == ["duplicate_rows_in_one_source"] and tdup.events[0].forced_class == "U"
    key = (SH, DAYS[5].isoformat())
    tr = et.build(m, [_src("EV2", 5, 4)], [], CFG, resolutions={key: {"status": "announcement", "gross_cash": 0.5}})
    assert [(e.forced_class, e.gross_cash) for e in tr.events] == [(None, 0.5)] and tr.counts["resolved_by_announcement"] == 1
    assert et.build(m, [_src("EV2", 5, 4)], [], CFG, resolutions={key: {"status": "reject"}}).events == []
    tp = et.build(m, [_src("EV2", 5, 4)], [], CFG, pending="provisional")
    assert tp.events[0].forced_class is None and _kinds(tp) == ["single_source"]


def test_event_status_filter_implemented_only():
    """Rule 10 (G-2): a row enters only if its status says implemented AND it has an ex-date.  A row
    with an ex-date but another status goes to the hand check; plan-stage rows are dropped."""
    m = panel(START, {SH: _ex_rows()})
    rows = [_src("EV1", 5, 4), _src("EV2", 5, 4),
            _src("EV2", 8, 7, implemented=False, status="plan"),            # ex-date, not implemented
            _src("EV2", None, None, implemented=False, status="plan"),      # plan stage
            _src("EV1", None, None, implemented=True, status="implemented")]
    t = et.build(m, rows, [], CFG)
    assert len(_dist(t)) == 1 and t.events[0].ex_date == DAYS[5]
    assert _kinds(t) == ["ex_date_but_not_implemented", "implemented_without_ex_date"]
    c = t.counts
    assert (c["rows_other_status_with_ex_date"], c["rows_not_implemented_without_ex_date"],
            c["rows_implemented_without_ex_date"]) == (1, 1, 1)


def test_event_step_without_event_goes_to_URS():
    """Rule 4: a reference-price step that no event explains -> hand check; unresolved -> URS (label U).
    Rule 12: a step whose previous row is not the previous market day is listed separately."""
    m = panel(START, {SH: _ex_rows()})
    t = et.build(m, [], [], CFG)
    assert t.urs == {(SH, DAYS[5])} and _kinds(t) == ["step_without_event"] and t.counts["steps_urs"] == 1
    m2 = panel(START, {SH: _ex_rows()})
    t.install(m2)
    assert label_o1(m2, Valuer(m2), SH, 4, 100.0, 10.0, 0.77, 2, CFG).outcome == "U"
    assert et.build(m, [], [], CFG, resolutions={(SH, DAYS[5].isoformat()): {"step": "explained"}}).urs == set()
    rows = [T(10, 10, 10)] * 5 + [X()] + [T(9.8, 9.8, 9.8)] * 6
    mm = panel(START, {SH: rows})
    tm = et.build(mm, [], [], CFG)
    assert tm.urs == {(SH, DAYS[6])} and _kinds(tm) == ["step_after_a_missing_row"]
    assert tm.counts["steps_urs_after_missing_row"] == 1 and tm.counts["steps_urs"] == 0


def test_event_ex_date_inside_suspension_step_at_resumption():
    """Rule 9 (a) with rule 7: ex-date (day 5) inside a suspension (days 4-6); the bar source carries
    10.00 on the suspended rows and shows the step on the first traded day after it (day 7:
    `preclose` 9.50).  Matched mechanically: the event stays on its ex-date, the step is explained,
    no URS.  P1 restates from the ex-date: (10 - 0.5) = 9.5 on days 5 and 6."""
    rows = [T(10, 10, 10)] * 4 + [Sv(10.0)] * 3 + [T(9.5, 9.5, 9.5)] * 5
    m = panel(START, {SH: rows})
    assert et.ev4_steps(m, SH) == {7: {"prev": 6, "prev_close": 10.0, "preclose": 9.5, "after_missing_row": False}}
    t = et.build(m, [_src("EV1", 5, 4), _src("EV2", 5, 4)], [], CFG)
    ev, = t.events
    assert ev.ex_date == DAYS[5] and ev.forced_class is None and t.urs == set() and t.u_spans == {} and t.hand_check == []
    assert t.counts["conflict_a_matched"] == 1 and t.counts["steps_explained_by_event"] == 1
    m2 = panel(START, {SH: rows})
    t.install(m2)
    v = Valuer(m2)
    assert v.ov(SH, 4).value == 10.0 and close(v.ov(SH, 5).value, 9.5, 1e-15) and close(v.ov(SH, 6).value, 9.5, 1e-15)
    # the step does not agree with the event (9.0 instead of 9.5): no match -> rule 9 (c) and URS
    rows_bad = [T(10, 10, 10)] * 4 + [Sv(10.0)] * 3 + [T(9.0, 9.0, 9.0)] * 5
    tb = et.build(panel(START, {SH: rows_bad}), [_src("EV1", 5, 4), _src("EV2", 5, 4)], [], CFG)
    assert tb.counts["conflict_a_matched"] == 0 and tb.events[0].forced_class == "U" and tb.urs == {(SH, DAYS[7])}


def test_event_date_conflict_decidable_and_undecidable():
    """Rule 9 (b): the sources' ex-date (day 3) is a traded day without a step; an unexplained step
    that agrees with the event lies on day 8.
      resolution 'event'     : event kept on day 3; the step -> URS
      resolution 'step'      : event re-dated to day 8 (record date := day 7)
      resolution 'undecided' : event applied on day 8, outcome U for entries whose window contains a
                               day of [day 3, day 8]
      no resolution (pending): as 'undecided', and listed for the hand check."""
    rows = [T(10, 10, 10)] * 8 + [T(9.5, 9.5, 9.5)] * 4
    m = panel(START, {SH: rows})
    src = [_src("EV1", 3, 2), _src("EV2", 3, 2)]
    key = (SH, DAYS[3].isoformat())
    te = et.build(m, src, [], CFG, resolutions={key: {"date": "event"}})
    assert [(e.ex_date, e.forced_class) for e in te.events] == [(DAYS[3], None)] and te.urs == {(SH, DAYS[8])}
    assert te.u_spans == {} and te.counts["conflict_b_event_date"] == 1
    ts = et.build(m, src, [], CFG, resolutions={key: {"date": "step"}})
    assert [(e.ex_date, e.record_date) for e in ts.events] == [(DAYS[8], DAYS[7])] and ts.urs == set() and ts.u_spans == {}
    tu = et.build(m, src, [], CFG, resolutions={key: {"date": "undecided"}})
    tp = et.build(m, src, [], CFG)
    for t in (tu, tp):
        assert [(e.ex_date, e.record_date, e.forced_class) for e in t.events] == [(DAYS[8], DAYS[7], None)]
        assert t.urs == set() and t.u_spans == {SH: [(DAYS[3], DAYS[8], "date conflict between the event source and the bar source")]}
        assert t.counts["conflict_b_pairs"] == 1 and t.counts["conflict_b_undecided_or_pending"] == 1
    assert _kinds(tu) == [] and _kinds(tp) == ["date_conflict"]
    m2 = panel(START, {SH: rows})
    tp.install(m2)
    v = Valuer(m2)
    assert label_o1(m2, v, SH, 1, 100.0, 10.0, 0.77, 2, CFG).outcome == "U"       # window days 2, 3
    assert label_o1(m2, v, SH, 4, 100.0, 10.0, 0.77, 2, CFG).outcome == "U"       # window days 5, 6
    assert label_o1(m2, v, SH, 7, 100.0, 10.0, 0.77, 2, CFG).outcome == "U"       # window days 8, 9
    assert label_o1(m2, v, SH, 9, 100.0, 9.5, 0.7315, 2, CFG).outcome == "value"  # window days 10, 11
    assert label_o1(m2, v, SH, 0, 100.0, 10.0, 0.77, 2, CFG).outcome == "value"   # window days 1, 2


def test_event_without_any_step():
    """Rule 9 (c): amounts imply a step of 0.50 but `preclose` never moves and no announcement
    confirms the event: not booked, outcome U on its ex-date, hand check.  Confirmed by the
    announcement: booked.  An event whose amounts imply a step below 0.005 needs no step."""
    m = panel(START, {SH: [T(10, 10, 10)] * 12})
    src = [_src("EV1", 5, 4), _src("EV2", 5, 4)]
    t = et.build(m, src, [], CFG)
    assert [(e.ex_date, e.forced_class) for e in t.events] == [(DAYS[5], "U")] and _kinds(t) == ["event_without_any_step"]
    assert t.counts["conflict_c_not_booked"] == 1 and t.counts["forced_U_events"] == 1
    tc = et.build(m, src, [], CFG, resolutions={(SH, DAYS[5].isoformat()): {"date": "event"}})
    assert tc.events[0].forced_class is None and tc.counts["conflict_c_confirmed_by_announcement"] == 1
    tiny = [_src("EV1", 5, 4, cash=0.003), _src("EV2", 5, 4, cash=0.003)]
    tt = et.build(m, tiny, [], CFG)
    assert tt.events[0].forced_class is None and tt.hand_check == [] and tt.counts["no_step_expected"] == 1


def test_event_record_date_rule_and_amount_consistency():
    """Rule 10 (E-11): record date must be the trading day before the ex-date; a confirmed event that
    violates it goes to the hand check; if the announcement shows another relation it is
    unclassifiable (U).  Rule 6: |implied reference price - preclose| > 0.005 flagged, > 0.02 hand check."""
    m = panel(START, {SH: _ex_rows()})
    key = (SH, DAYS[5].isoformat())
    src = [_src("EV1", 5, 3), _src("EV2", 5, 3)]                             # record date two days before
    t = et.build(m, src, [], CFG)
    assert _kinds(t) == ["record_date_not_the_trading_day_before_the_ex_date"] and t.events[0].forced_class == "U"
    assert t.counts["record_date_violation"] == 1
    t1 = et.build(m, src, [], CFG, resolutions={key: {"status": "announcement", "record_date": DAYS[4].isoformat()}})
    assert t1.events[0].forced_class is None and t1.events[0].record_date == DAYS[4]
    t2 = et.build(m, src, [], CFG, resolutions={key: {"status": "announcement", "record_date": DAYS[3].isoformat()}})
    assert t2.events[0].forced_class == "U"                                 # the announcement itself shows another relation
    t3 = et.build(m, src, [], CFG, resolutions={key: {"status": "unclassifiable"}})
    assert t3.events[0].forced_class == "U"
    ok = [_src("EV1", 5, 4), _src("EV2", 5, 4)]
    m_flag = panel(START, {SH: _ex_rows(new=9.49)})                         # implied 9.50 vs 9.49: 0.01
    tf = et.build(m_flag, ok, [], CFG)
    assert tf.events[0].forced_class is None and tf.counts["amount_flagged"] == 1 and tf.hand_check == []
    assert [f["kind"] for f in tf.flags] == ["amount_vs_reference_price"]
    m_bad = panel(START, {SH: _ex_rows(new=9.2)})                           # implied 9.50 vs 9.20: 0.30
    tb = et.build(m_bad, ok, [], CFG)
    assert _kinds(tb) == ["amount_inconsistent_with_reference_price"] and tb.events[0].forced_class == "U"
    assert tb.events[0].gross_cash == 0.5                                   # the announced amount is never replaced


def test_event_rights_rows():
    """Rule 5: rights issues from the Sina rights table; each goes to the hand-check list; a dated row
    enters the table and explains the step on its ex-date; a row without any date does not enter
    (default) - with undated_rights='include' it does and gives outcome M (note (10))."""
    rows = [T(10, 10, 10)] * 8 + [T(9.67, 9.67, 9.67)] * 4
    m = panel(START, {SH: rows})
    dated = et.RightsRow(SH, 0.2, 8.0, DAYS[8], DAYS[2], DAYS[0])
    undated = et.RightsRow(SH, 0.3, 7.0, None, None, DAYS[1])
    t = et.build(m, [], [dated, undated], CFG)
    ev, = t.events
    assert (ev.kind, ev.record_date, ev.ex_date, ev.rights_price, ev.rights_ratio) == ("rights", DAYS[2], DAYS[8], 8.0, 0.2)
    assert t.urs == set() and _kinds(t) == ["rights_issue", "rights_without_dates"]
    assert (t.counts["rights_in_table"], t.counts["rights_undated"], t.counts["steps_explained_by_rights"]) == (1, 1, 1)
    ti = et.build(m, [], [undated], CFG, undated_rights="include")
    assert len(ti.events) == 1 and ti.events[0].announce_date == DAYS[1]
    m2 = panel(START, {SH: [T(10, 10, 10)] * 12})
    ti.install(m2)
    assert label_o1(m2, Valuer(m2), SH, 3, 100.0, 10.0, 0.77, 2, CFG).outcome == "M"
    assert label_o1(m2, Valuer(m2), SH, 0, 100.0, 10.0, 0.77, 2, CFG).outcome == "value"
    norec = et.RightsRow(SH, 0.2, 8.0, DAYS[8], None, DAYS[0])
    tn = et.build(m, [], [norec], CFG)
    assert _kinds(tn) == ["rights_without_record_date"] and tn.counts["rights_missing_record_date"] == 1 and len(tn.events) == 1


# ================================================================== loader on an imitation of data/raw
def _write_raw(root: Path, adjustflag="3", extra_col=None):
    days_all = []
    x = d("2007-12-03")
    while x <= d("2008-03-31"):
        days_all.append(x)
        x += timedelta(days=1)
    cal = pd.DataFrame({"calendar_date": [y.isoformat() for y in days_all],
                        "is_trading_day": ["1" if y.weekday() < 5 else "0" for y in days_all]})
    (root / "universe").mkdir(parents=True)
    cal.to_parquet(root / "universe" / "bs_trade_dates.parquet")
    pd.DataFrame({"code": ["sh.600001", "sz.000002"], "code_name": ["a", "b"], "ipoDate": ["2000-01-04", "2008-01-10"],
                  "outDate": ["", "2008-02-15"], "type": ["1", "1"], "status": ["1", "0"]}
                 ).to_parquet(root / "universe" / "bs_stock_basic.parquet")
    tdays = [y for y in days_all if y.weekday() < 5 and y >= d("2008-01-01")]
    (root / "bars" / "bs_daily").mkdir(parents=True)
    ex = d("2008-02-01")
    for code, first, last in (("sh.600001", d("2008-01-01"), d("2008-03-31")), ("sz.000002", d("2008-01-10"), d("2008-02-15"))):
        rows = []
        for y in tdays:
            if not (first <= y <= last):
                continue
            px = 10.0 if (code != "sh.600001" or y < ex) else 9.5
            pc = px
            rows.append({"date": y.isoformat(), "code": code, "open": f"{px:.4f}", "high": f"{px:.4f}", "low": f"{px:.4f}",
                         "close": f"{px:.4f}", "preclose": f"{pc:.4f}", "volume": "100000", "amount": "1000000.00",
                         "adjustflag": adjustflag, "turn": "0.1", "tradestatus": "1", "pctChg": "0", "isST": "0"})
        df = pd.DataFrame(rows)
        if code == "sh.600001":
            df["filled_from_xsrc"] = ["1" if r == "2008-01-15" else "0" for r in df["date"]]
            if extra_col:
                df[extra_col] = "1.0"
        df.to_parquet(root / "bars" / "bs_daily" / f"{code}.parquet")
    fe = root / "factors_events"
    for sub in ("sina_dividend", "sina_rights", "em_fhps", "bs_dividend", "bs_adjust_factor"):
        (fe / sub).mkdir(parents=True)
    impl, plan, none = io.STATUS_IMPLEMENTED_SINA, "预案", "不分配"
    pd.DataFrame([["2008-01-20", 0, 0, 5.0, impl, "2008-02-01", "2008-01-31", None],
                  ["2008-03-01", 0, 0, 2.0, plan, "2008-03-20", "2008-03-19", None],     # ex-date but 'plan'
                  ["2008-03-05", 0, 0, 0.0, none, None, None, None]],
                 columns=[f"c{k}" for k in range(8)]).to_parquet(fe / "sina_dividend" / "sh.600001.parquet")
    pd.DataFrame([["2008-02-10", 2.0, 8.0, 1, "2008-03-10", "2008-03-03", None, "2008-03-07", "2008-03-12", None],
                  ["2008-03-25", 3.0, 7.0, 1, None, None, None, None, None, None]],
                 columns=[f"c{k}" for k in range(10)]).to_parquet(fe / "sina_rights" / "sh.600001.parquet")
    em = [["2007-12-31", "2008-01-20", 0.0, 0.0, 0.0, 5.0, "x", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1, "2008-01-10",
           "2008-01-31", "2008-02-01", io.STATUS_IMPLEMENTED_EM, "2008-01-20"]]
    pd.DataFrame(em, columns=[f"c{k}" for k in range(19)]).to_parquet(fe / "em_fhps" / "sh.600001.parquet")
    pd.DataFrame({"code": ["sh.600001"], "factor": ["1.05"]}).to_parquet(fe / "bs_adjust_factor" / "sh.600001.parquet")
    return tdays


def test_loader_status_filter_delisting_and_flags():
    """ENG-8 (a), G-3, ENG-13 (b), on an imitation of data/raw in a temporary directory.
    Sina: the 'implemented' row with an ex-date enters; the 'plan' row WITH an ex-date and the rights
    row without dates do not enter and are listed; `outDate` = last day with a row, so the name is
    not listed from the next market day; the repair flag column is read and passed through."""
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw"
        tdays = _write_raw(raw)
        m, rep = io.load_market(raw, ["sh.600001", "sz.000002"], events="sina", data_cutoff=io.PANEL_END,
                                dispositions_path=Path(tmp) / "none.csv")
        assert rep["problems"] == [] and m.days == tdays
        evs = m.events["sh.600001"]
        assert sorted(e.kind for e in evs) == ["dist", "rights"]
        dist = [e for e in evs if e.kind == "dist"][0]
        assert (dist.ex_date, dist.record_date, dist.gross_cash, dist.phi) == (d("2008-02-01"), d("2008-01-31"), 0.5, 1.0)
        rights = [e for e in evs if e.kind == "rights"][0]
        assert (rights.record_date, rights.ex_date, rights.rights_ratio, rights.rights_price) == (d("2008-03-03"), d("2008-03-10"), 0.2, 8.0)
        nt = rep["events"]["not_in_table"]
        assert len(nt) == 2 and any("2008-03-20" in s and "hand check" in s for s in nt) and any("rights row without dates" in s for s in nt)
        assert m.events_on("sh.600001", m.idx[d("2008-03-20")]) == []
        s2 = m.secs["sz.000002"]
        last = m.idx[d("2008-02-15")]
        assert s2.delist_i == last + 1 and s2.has_row[last] and m.status("sz.000002", last) == "T" and m.status("sz.000002", last + 1) == "D"
        assert rep["dispositions"]["no_row"] == ["sz.000002"] and rep["dispositions"]["fallback_sentence_required"]
        s1 = m.secs["sh.600001"]
        assert s1.filled_from_xsrc is not None and int(s1.filled_from_xsrc.sum()) == 1 and m.filled_xsrc("sh.600001", m.idx[d("2008-01-15")])
        assert s2.filled_from_xsrc is None and rep["codes"]["sh.600001"]["rows_filled_from_xsrc"] == 1
        # listing age: 21 weekdays of December 2007 precede the panel (the imitation calendar starts 2007-12-03)
        assert s1.listed_days_before_panel == 21 and s2.listed_days_before_panel == 0
        # merged table: Sina and Eastmoney agree -> confirmed, booked; same lists for the hand check
        m2, rep2 = io.load_market(raw, ["sh.600001", "sz.000002"], events="merged", dispositions_path=Path(tmp) / "none.csv", data_cutoff=io.PANEL_END)
        c = rep2["event_table"]["counts"]
        assert (c["confirmed_2_sources"], c["booked_dist_events"], c["rights_in_table"], c["rights_undated"],
                c["rows_other_status_with_ex_date"], c["steps_urs"]) == (1, 1, 1, 1, 1, 0)
        kinds = sorted(h["kind"] for h in rep2["event_table"]["hand_check"])
        assert kinds == ["ex_date_but_not_implemented", "rights_issue", "rights_without_dates"], kinds
        assert len(m2.events_on("sh.600001", m2.idx[d("2008-02-01")])) == 1 and len(rep2["event_table"]["hash"]) == 64
        return {"sina_not_in_table": nt, "merged_counts": {k: c[k] for k in ("confirmed_2_sources", "booked_dist_events", "hand_check_items")}}


def test_FC_A4_no_factor_or_adjusted_price_is_read():
    """FC-A4: labels and ledger never read a vendor adjustment factor or an adjusted price.
    (1) the market container has no field that could hold one;
    (2) the loader never opens a file of the factor table although one exists, and refuses to if asked;
    (3) a bar file that is not unadjusted (adjustflag != '3') is refused;
    (4) a bar file with a factor / adjusted-price column is refused."""
    for cls in (Sec, Event):
        names = [f.name.lower() for f in dataclasses.fields(cls)]
        assert not any(("factor" in n) or ("adj" in n) or ("hfq" in n) or ("qfq" in n) for n in names), names
    opened = []
    real = pd.read_parquet

    def spy(path, *a, **k):
        opened.append(str(path))
        return real(path, *a, **k)
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw"
        _write_raw(raw)
        io.pd.read_parquet = spy
        try:
            for mode in ("sina", "merged", "none"):
                io.load_market(raw, ["sh.600001", "sz.000002"], events=mode, dispositions_path=Path(tmp) / "none.csv", data_cutoff=io.PANEL_END)
        finally:
            io.pd.read_parquet = real
        assert opened and not any("adjust_factor" in p for p in opened), opened
        assert (raw / "factors_events" / "bs_adjust_factor" / "sh.600001.parquet").exists()
        try:
            io._read_parquet(raw / "factors_events" / "bs_adjust_factor" / "sh.600001.parquet")
            raise AssertionError("reading the factor table must be refused")
        except MarketDataError:
            pass
        assert all(c in io.BAR_COLS for c in io.READ_COLS) and "turn" not in io.READ_COLS and "pctChg" not in io.READ_COLS
        for kw in ({"adjustflag": "2"}, {"adjustflag": "1"}, {"extra_col": "adj_factor"}, {"extra_col": "hfq_close"},
                   {"extra_col": "backadjustfactor"}):
            raw2 = Path(tmp) / ("raw_" + "_".join(str(v) for v in kw.values()))
            _write_raw(raw2, **kw)
            try:
                io.load_market(raw2, ["sh.600001"], events="none", dispositions_path=Path(tmp) / "none.csv", data_cutoff=io.PANEL_END)
                raise AssertionError(f"{kw} must be refused")
            except MarketDataError:
                pass
    return {"files_opened": len(opened), "refused_variants": 5}


# ================================================================== universe and candidates
def _uni_market():
    a, b, c, dd, e, f, g, h = "sh.600001", "sh.600002", "sz.000003", "sz.300004", "sh.688005", "sh.900901", "sz.000007", "sz.000008"
    def tr(amt, n=8, st_last=False):
        return [T(10, 10, 10, amt=amt)] * (n - 1) + [T(10, 10, 10, amt=amt, st=st_last)]
    rows = {a: tr(5e6), b: tr(9e6, st_last=True),
            c: [T(10, 10, 10, amt=8e6)] * 3 + [S(10.0)] * 3 + [T(10, 10, 10, amt=8e6)] * 2,
            dd: tr(7e6), e: [X()] * 5 + [T(10, 10, 10, amt=9e9)] * 3, f: tr(1e9),
            g: [T(10, 10, 10, amt=6e6)] * 5 + [N(10.0)] + [T(10, 10, 10, amt=6e6)] * 2, h: tr(5e6)}
    return panel(START, rows), (a, b, c, dd, e, f, g, h)


def test_universe_screen_by_hand():
    """U-LIQ on a screen day (window 5, at least 3 traded days, at least 5 days listed, N_U = 2 / 3):
      a  median 5e6                     eligible
      b  9e6 but ST on the screen day   excluded
      c  traded 2 of the last 5 days    excluded (inactive)
      d  median 7e6                     eligible
      e  listed 3 days                  excluded (listing age)
      f  B share (prefix 900)           excluded (board)
      g  6e6 on 4 days, one no-trade day counted as 0 -> median 6e6   eligible
      h  median 5e6                     eligible; tie with a, broken by code
    Ranking: d (7e6), g (6e6), a, h -> N_U = 2: [d, g]; N_U = 3: [d, g, a]."""
    m, (a, b, c, dd, e, f, g, h) = _uni_market()
    cfg = replace(CFG, universe_window=5, universe_min_traded=3, universe_min_listed=5, universe_size=2)
    p = uni.Panel(m)
    mem, rep = uni.members(p, 7, cfg)
    assert mem == [dd, g], mem
    assert (rep["eligible"], rep["members"], rep["excluded_board"], rep["excluded_listing_age"],
            rep["excluded_inactive"], rep["excluded_st_or_no_row"]) == (4, 2, 1, 1, 1, 1), rep
    assert uni.members(p, 7, replace(cfg, universe_size=3))[0] == [dd, g, a]
    assert uni.members(p, 7, replace(cfg, universe_size=10))[0] == [dd, g, a, h]
    assert uni.members(p, 3, cfg)[0] == []                                  # fewer than 5 panel days before the screen day
    # listing age counts days before the panel when the loader supplies them
    m.secs[e].listed_days_before_panel = 0
    m.secs[a].listed_days_before_panel = 500
    p2 = uni.Panel(m)
    assert p2.listed_days(7)[p2.codes.index(a)] == 508 and p2.listed_days(7)[p2.codes.index(e)] == 3
    assert p2.listed_days(4)[p2.codes.index(e)] == 0
    return {"members_N2": mem, "counts": rep}


def test_screen_days_and_membership_validity():
    """Screen day = last market trading day of a calendar month; its membership is used for the
    decision days of the FOLLOWING calendar month."""
    days = weekdays(d("2021-01-04"), 62)                                    # 2021-01-04 .. 2021-03-30
    rows = {"sh.600001": [T(10, 10, 10, amt=5e6)] * 62, "sh.600002": [T(10, 10, 10, amt=3e6)] * 30 + [S(10.0)] * 32}
    m = panel(d("2021-01-04"), rows)
    sd = uni.screen_days(m.days)
    assert [m.days[i] for i in sd] == [d("2021-01-29"), d("2021-02-26"), d("2021-03-30")]
    cfg = replace(CFG, universe_window=10, universe_min_traded=8, universe_min_listed=10, universe_size=5)
    by, reps = uni.membership_by_month(uni.Panel(m), cfg)
    assert sorted(by) == [(2021, 2), (2021, 3)]
    assert by[(2021, 2)] == ["sh.600001", "sh.600002"]                      # both active through January
    # 600002 is suspended from 2021-02-15 (day 30): on the screen day 2021-02-26 it traded on 0 of the last
    # 10 days -> not a member in March.  It IS a member throughout February, although suspended from the
    # 15th: the membership of a month is fixed on the last trading day of the previous month.
    assert by[(2021, 3)] == ["sh.600001"]
    assert m.days[30] == d("2021-02-15") and m.days[39] == d("2021-02-26")
    assert uni.ever_members(by) == ["sh.600001", "sh.600002"]


def test_candidate_filters_by_hand():
    """C_t = members, listed at least 3 days (U11 scaled down), not suspended on t-1, with a row on
    t-1, ST flag 0 on each of the 4 market days ending t-1 (U55 scaled down).  t = 7."""
    ok, susp, norow, st_recent, st_old, young = ("sh.600001", "sh.600002", "sh.600003", "sh.600004", "sh.600005", "sh.600006")
    base = [T(10, 10, 10)] * 8
    rows = {ok: base, susp: [T(10, 10, 10)] * 6 + [S(10.0), T(10, 10, 10)],
            norow: [T(10, 10, 10)] * 6 + [X(), T(10, 10, 10)],
            st_recent: [T(10, 10, 10)] * 3 + [T(10, 10, 10, st=True)] + [T(10, 10, 10)] * 4,     # ST on day 3: inside days 3..6
            st_old: [T(10, 10, 10)] * 2 + [T(10, 10, 10, st=True)] + [T(10, 10, 10)] * 5,        # ST on day 2: outside
            young: [X()] * 5 + [T(10, 10, 10)] * 3}                                             # listed day 5: 2 days by t-1
    m = panel(START, rows)
    cfg = replace(CFG, candidate_min_listed=3, st_lookback=4)
    cands, cnt = uni.candidates(uni.Panel(m), 7, sorted(rows), cfg)
    assert cands == [ok, st_old], cands
    assert cnt == {"members": 6, "removed_listing_age": 1, "removed_suspended": 1, "removed_no_row": 1,
                   "removed_st_lookback": 1, "candidates": 2}, cnt
    # a name suspended on day t itself stays a candidate (day-t status is not in G_t)
    m.secs[ok].flag_trading[7] = False
    assert uni.candidates(uni.Panel(m), 7, sorted(rows), cfg)[0] == [ok, st_old]
    return cnt


def test_universe_and_candidates_depend_on_past_data_only():
    """Truncation test: every row dated after the screen day s (after t-1 for the candidate set) is
    replaced by random junk, and listing ends dated later are removed; membership and candidates are
    unchanged.  Random synthetic markets, 3 seeds; no price move or outcome is read by the screen."""
    cfg = replace(CFG, universe_window=20, universe_min_traded=12, universe_min_listed=20, universe_size=8,
                  candidate_min_listed=10, st_lookback=10)
    checked = 0
    for seed in (5, 6, 7):
        m = make_market(seed, d("2019-01-02"), 150, 24)
        p = uni.Panel(m)
        rng = np.random.default_rng(seed)
        for s_i in (25, 47, 80, 111, 140):
            mem, _ = uni.members(p, s_i, cfg)
            assert 0 < len(mem) <= 8
            for cut, what in ((s_i, "members"), (s_i + 6, "candidates")):
                secs = {}
                for code, s in m.secs.items():
                    def junk(arr, kind):
                        out = arr.copy()
                        k = len(out) - cut - 1
                        if kind == "bool":
                            out[cut + 1:] = rng.random(k) < 0.5
                        else:
                            out[cut + 1:] = rng.uniform(0.5, 1e9, k)
                        return out
                    secs[code] = Sec(code, junk(s.open, "f"), junk(s.close, "f"), junk(s.preclose, "f"), junk(s.amount, "f"),
                                     junk(s.has_row, "bool"), junk(s.flag_trading, "bool"), junk(s.vol_pos, "bool"),
                                     junk(s.is_st, "bool"), s.delist_i if (s.delist_i is not None and s.delist_i <= cut) else None)
                pt = uni.Panel(Market(m.days, secs))
                if what == "members":
                    assert uni.members(pt, s_i, cfg)[0] == mem, (seed, s_i)
                else:
                    t_i = cut + 1
                    assert uni.candidates(pt, t_i, mem, cfg)[0] == uni.candidates(p, t_i, mem, cfg)[0], (seed, t_i)
                checked += 1
    return {"comparisons": checked}


TESTS = [test_event_two_and_three_source_confirmation, test_event_single_source_and_disagreement_go_to_hand_check,
         test_event_status_filter_implemented_only, test_event_step_without_event_goes_to_URS,
         test_event_ex_date_inside_suspension_step_at_resumption, test_event_date_conflict_decidable_and_undecidable,
         test_event_without_any_step, test_event_record_date_rule_and_amount_consistency, test_event_rights_rows,
         test_loader_status_filter_delisting_and_flags, test_FC_A4_no_factor_or_adjusted_price_is_read,
         test_universe_screen_by_hand, test_screen_days_and_membership_validity, test_candidate_filters_by_hand,
         test_universe_and_candidates_depend_on_past_data_only]

if __name__ == "__main__":
    run_tests("v07_components", TESTS, "v07_components.json")

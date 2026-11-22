"""Unit tests of the rule calendar.  Expected values are typed by hand from PLAN 3.10 / 3.6
and rule_verification.md; they are not produced by the code under test."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal as D

from common import run_tests

from engine import rule_calendar as rc

d = date.fromisoformat


def test_stamp_duty_boundaries():
    """RC-15: 2008-04-24, 2008-09-19, 2023-08-28."""
    exp = {"2008-01-02": (0.003, 0.003), "2008-04-23": (0.003, 0.003), "2008-04-24": (0.001, 0.001),
           "2008-09-18": (0.001, 0.001), "2008-09-19": (0.0, 0.001), "2015-06-15": (0.0, 0.001),
           "2023-08-25": (0.0, 0.001), "2023-08-27": (0.0, 0.001), "2023-08-28": (0.0, 0.0005),
           "2026-06-30": (0.0, 0.0005)}
    for k, v in exp.items():
        assert rc.stamp_duty(d(k)) == v, (k, rc.stamp_duty(d(k)), v)


def test_transfer_fee_boundaries():
    """RC-16: 2015-08-01 (SSE per share -> rate), 2022-04-29, and the 'no 2022 cut' fallback."""
    assert rc.transfer_fee(d("2015-07-31"), "sh") == ("per_share", 0.000375)
    assert rc.transfer_fee(d("2015-07-31"), "sz") == ("rate", 0.0000255)
    assert rc.transfer_fee(d("2010-01-04"), "sh") == ("per_share", 0.000375)
    for ex in ("sh", "sz"):
        assert rc.transfer_fee(d("2015-08-01"), ex) == ("rate", 0.00002)
        assert rc.transfer_fee(d("2022-04-28"), ex) == ("rate", 0.00002)
        assert rc.transfer_fee(d("2022-04-29"), ex) == ("rate", 0.00001)
        assert rc.transfer_fee(d("2022-04-29"), ex, fallback_no_2022_cut=True) == ("rate", 0.00002)
        assert rc.transfer_fee(d("2022-04-28"), ex, fallback_no_2022_cut=True) == ("rate", 0.00002)


def test_dividend_tax_boundaries():
    """RC-14 by record date: 2013-01-01, 2015-09-08, and the 20% fallback before 2013."""
    assert rc.dividend_tax(d("2012-12-31")) == (0.10, 0.10)
    assert rc.dividend_tax(d("2013-01-01")) == (0.20, 0.05)
    assert rc.dividend_tax(d("2015-09-07")) == (0.20, 0.05)
    assert rc.dividend_tax(d("2015-09-08")) == (0.20, 0.0)
    assert rc.dividend_tax(d("2026-06-30")) == (0.20, 0.0)
    assert rc.dividend_tax(d("2012-12-31"), fallback_20_before_2013=True) == (0.20, 0.20)
    assert rc.dividend_tax(d("2013-01-01"), fallback_20_before_2013=True) == (0.20, 0.05)


def test_price_bands():
    """RC-6: main 10% / ST 5%; ChiNext 10% -> 20% and ChiNext ST 5% -> 20% on 2020-08-24; STAR 20%."""
    exp = [("2010-01-04", "main", False, "0.10"), ("2026-06-30", "main", False, "0.10"),
           ("2010-01-04", "main", True, "0.05"), ("2026-06-30", "main", True, "0.05"),
           ("2020-08-21", "chinext", False, "0.10"), ("2020-08-24", "chinext", False, "0.20"),
           ("2020-08-21", "chinext", True, "0.05"), ("2020-08-24", "chinext", True, "0.20"),
           ("2019-07-22", "star", False, "0.20"), ("2024-01-02", "star", True, "0.20")]
    for dt, board, st, band in exp:
        assert rc.price_band(d(dt), board, st) == D(band), (dt, board, st)


def test_limit_price_rounding():
    """RC-5: decimal half-up to 0.01; +-0.01 when the rounded limit is closer than 0.01."""
    exp = [("10.00", "0.10", "11.00", "9.00"),
           ("10.05", "0.10", "11.06", "9.05"),      # 11.055 -> 11.06, 9.045 -> 9.05 (half-up, not half-even)
           ("10.15", "0.10", "11.17", "9.14"),      # 11.165 -> 11.17, 9.135 -> 9.14
           ("9.95", "0.05", "10.45", "9.45"),       # 10.4475 -> 10.45, 9.4525 -> 9.45
           ("1.25", "0.20", "1.50", "1.00"),
           ("23.45", "0.20", "28.14", "18.76"),
           ("0.09", "0.10", "0.10", "0.08"),        # 0.099 -> 0.10, 0.081 -> 0.08
           ("0.05", "0.10", "0.06", "0.04"),        # 0.055 -> 0.06; 0.045 -> 0.05 = preclose -> 0.04
           ("0.04", "0.10", "0.05", "0.03"),        # 0.044 -> 0.04 -> 0.05; 0.036 -> 0.04 -> 0.03
           ("0.07", "0.05", "0.08", "0.06")]        # 0.0735 -> 0.07 -> 0.08; 0.0665 -> 0.07 -> 0.06
    for pc, band, up, dn in exp:
        got = rc.limit_prices(pc, band)
        assert got == (D(up), D(dn)), (pc, band, got)
        got_f = rc.limit_prices(float(pc), D(band))          # float input from the data files
        assert got_f == (D(up), D(dn)), ("float", pc, got_f)


def test_limit_price_full_grid_vs_integer_arithmetic():
    """Every reference price 0.01..300.00 x bands 5/10/20%: engine vs exact integer half-up arithmetic."""
    n, builtin_diff = 0, 0
    for b in (5, 10, 20):
        band = D(b) / D(100)
        for cents in range(1, 30001):
            up_c = (cents * (100 + b) + 50) // 100           # exact half-up in cents
            dn_c = (cents * (100 - b) + 50) // 100
            if up_c - cents < 1:
                up_c = cents + 1
            if cents - dn_c < 1:
                dn_c = cents - 1
            pc = cents / 100.0                                # float, as read from a data file
            up, dn = rc.limit_prices(pc, band)
            assert (up, dn) == (D(up_c) / D(100), D(dn_c) / D(100)), (cents, b, up, dn)
            n += 1
            # information only: how often Python's built-in round on floats would be wrong
            if round(pc * (1 + b / 100), 2) != up_c / 100 and up_c - cents >= 1 and (cents * (100 + b)) % 100 == 50:
                builtin_diff += 1
    return {"cases": n, "upper_limits_where_builtin_float_round_differs": builtin_diff}


def test_limit_prices_for_code_and_date():
    """ChiNext ST name on 2020-08-21 and 2020-08-24 (PLAN R4 rule-calendar case)."""
    up, dn, band = rc.limit_prices_for("sz.300104", d("2020-08-21"), "10.00", True)
    assert (up, dn, band) == (D("10.50"), D("9.50"), D("0.05"))
    up, dn, band = rc.limit_prices_for("sz.300104", d("2020-08-24"), "10.00", True)
    assert (up, dn, band) == (D("12.00"), D("8.00"), D("0.20"))
    up, dn, band = rc.limit_prices_for("sh.688111", d("2021-03-01"), "100.00", False)
    assert (up, dn) == (D("120.00"), D("80.00"))
    up, dn, band = rc.limit_prices_for("sh.600053", d("2021-03-01"), "10.00", True)
    assert (up, dn) == (D("10.50"), D("9.50"))


def test_boards_and_exchanges():
    exp = {"sh.600000": "main", "sh.601318": "main", "sh.603288": "main", "sh.605499": "main",
           "sh.688111": "star", "sh.689009": "star", "sz.000002": "main", "sz.001872": "main",
           "sz.002594": "main", "sz.003816": "main", "sz.300750": "chinext", "sz.301001": "chinext",
           "sz.302132": "chinext"}
    for c, b in exp.items():
        assert rc.board_of(c) == b, c
    assert rc.exchange_of("sh.600000") == "sh" and rc.exchange_of("sz.000002") == "sz"
    for bad in ("bj.430047", "sh.900901", "sz.200002", "sh.000001", "sz.399001"):
        try:
            rc.board_of(bad)
        except rc.CalendarError:
            continue
        raise AssertionError(f"{bad} should be unclassifiable")


def test_lot_rounding():
    """RC-11: main / ChiNext multiples of 100; STAR at least 200, no multiple (150 -> no order, 250 -> 250)."""
    dt = d("2022-01-04")
    assert rc.round_buy_quantity(250.0, dt, "main") == 200.0
    assert rc.round_buy_quantity(99.9, dt, "main") == 0.0
    assert rc.round_buy_quantity(399.0, dt, "chinext") == 300.0
    assert rc.round_buy_quantity(150.0, dt, "star") == 0.0
    assert rc.round_buy_quantity(250.0, dt, "star") == 250.0
    assert rc.round_buy_quantity(250.7, dt, "star") == 250.0
    assert rc.round_buy_quantity(200.0, dt, "star") == 200.0
    assert rc.lot_rule(dt, "main")["max_order"] == 1_000_000


def test_window_and_unique_coverage():
    """Every key has exactly one row on every calendar day of 2008-01-01..2026-06-30; outside raises."""
    keys = sorted({r.key for r in rc.RULES})
    day, n = rc.CAL_START, 0
    while day <= rc.CAL_END:
        for k in keys:
            rc.lookup(k, day)          # raises unless exactly one row applies
        day += timedelta(days=1)
        n += 1
    for bad in (d("2007-12-31"), d("2026-07-01"), d("2026-07-06")):
        try:
            rc.stamp_duty(bad)
        except rc.CalendarError:
            continue
        raise AssertionError(f"{bad} should be outside the calendar")
    return {"days_checked": n, "keys": len(keys)}


def test_every_boundary_changes_value():
    """At each boundary date the value on the day differs from the value on the day before."""
    out = []
    for key, start in rc.boundary_dates():
        before, after = rc.lookup(key, start - timedelta(days=1)), rc.lookup(key, start)
        assert before.value != after.value, (key, start)
        assert before.end == start - timedelta(days=1), (key, start, before.end)
        out.append(f"{key}@{start}")
    exp = {"stamp@2008-04-24", "stamp@2008-09-19", "stamp@2023-08-28", "transfer:sh@2015-08-01",
           "transfer:sz@2015-08-01", "transfer:sh@2022-04-29", "transfer:sz@2022-04-29",
           "divtax@2013-01-01", "divtax@2015-09-08", "band:chinext:0@2020-08-24", "band:chinext:1@2020-08-24",
           "close_auction:sh@2018-08-20", "delist_regime@2020-12-31"}
    # added in v0.7 (task ENG-17 (b)): group (e) disclosure regimes and RC-6 (f)
    exp |= {"ins_regime@2015-07-08", "ins_regime@2016-01-09", "ins_regime@2017-05-27", "ins_regime@2024-05-24",
            "lhb_thr:chinext@2020-08-24", "lhb_topn:sh@2021-09-17", "lhb_topn:sh@2021-10-08",
            "lhb_topn:sz@2013-12-01", "ipo_nolimit5:chinext@2020-08-24", "ipo_nolimit5:main@2023-04-10"}
    assert set(out) == exp, set(out) ^ exp
    return {"boundaries": sorted(out)}


def test_disclosure_regimes_group_e():
    """RC-18 / RC-20 (v0.7, E-20, F-20): values typed by hand from PLAN 3.10 (e) and 5.6.2a."""
    # v0.8 (J-1, task C-3): the rows carry the element cum3 (0.20 / 0.30) - expectation extended
    main = {"kind": "deviation", "price": 0.07, "amplitude": 0.15, "turnover": 0.20, "cum3": 0.20}
    wide = {"kind": "change", "price": 0.15, "amplitude": 0.30, "turnover": 0.30, "cum3": 0.30}
    assert rc.lhb_thresholds(d("2010-01-04"), "main") == main and rc.lhb_thresholds(d("2026-06-30"), "main") == main
    assert rc.lhb_thresholds(d("2020-08-21"), "chinext") == main and rc.lhb_thresholds(d("2020-08-23"), "chinext") == main
    assert rc.lhb_thresholds(d("2020-08-24"), "chinext") == wide
    assert rc.lhb_thresholds(d("2019-07-22"), "star") == wide and rc.lhb_thresholds(d("2024-01-02"), "star") == wide
    # top-3 / top-5: THREE values - 0, 1, None (unknown)
    exp = [("sh", "2008-01-02", 0, 3), ("sh", "2021-09-16", 0, 3), ("sh", "2021-09-17", None, None),
           ("sh", "2021-10-07", None, None), ("sh", "2021-10-08", 1, 5), ("sh", "2026-06-30", 1, 5),
           ("sz", "2008-01-02", None, None), ("sz", "2013-11-30", None, None), ("sz", "2013-12-01", 1, 5),
           ("sz", "2013-12-02", 1, 5), ("sz", "2026-06-30", 1, 5)]
    for ex, day, top5, n in exp:
        assert rc.lhb_top5(d(day), ex) == top5 and rc.lhb_top_n(d(day), ex) == n, (ex, day)
    # five INS regimes
    exp = [("2008-01-02", 0), ("2015-07-07", 0), ("2015-07-08", 1), ("2016-01-08", 1), ("2016-01-09", 2),
           ("2017-05-26", 2), ("2017-05-27", 3), ("2024-05-23", 3), ("2024-05-24", 4), ("2026-06-30", 4)]
    for day, k in exp:
        assert rc.ins_regime(d(day)) == k, day
    # first five trading days without a limit, by board; the main-board date is marked unverified
    assert rc.ipo_no_limit_first5(d("2019-07-22"), "star") is True
    assert rc.ipo_no_limit_first5(d("2020-08-21"), "chinext") is False
    assert rc.ipo_no_limit_first5(d("2020-08-24"), "chinext") is True
    assert rc.ipo_no_limit_first5(d("2023-04-07"), "main") is False and rc.ipo_no_limit_first5(d("2023-04-10"), "main") is True
    r = rc.lookup("ipo_nolimit5:main", d("2023-04-10"))
    assert r.date_status == rc.UNV and r.unverified_item == 21 and "UNVERIFIED" in r.note
    for key, day, item in (("lhb_topn:sh", "2021-10-08", 7), ("lhb_topn:sz", "2013-12-01", 19),
                           ("lhb_thr:chinext", "2020-08-24", 7)):
        r = rc.lookup(key, d(day))
        assert r.date_status == rc.UNV and r.unverified_item == item, key
    # interval accessor used by the feature library
    iv = rc.intervals("ins_regime")
    assert [v for _, _, v in iv] == [0, 1, 2, 3, 4] and iv[0][0] == rc.CAL_START and iv[-1][1] == rc.CAL_END
    assert all(iv[k][1] + timedelta(days=1) == iv[k + 1][0] for k in range(4))
    assert [v[1] for _, _, v in rc.intervals("lhb_topn:sh")] == [0, None, 1]


def test_dividend_tax_boundary_day_two_readings():
    """E-9 (PLAN 3.10 list item 17): record date 2015-09-08 under 'from' and 'after'; tau is the same."""
    assert rc.dividend_tax(d("2015-09-08")) == (0.20, 0.0)
    assert rc.dividend_tax(d("2015-09-08"), reading_2015="after") == (0.20, 0.05)
    for day in ("2015-09-07", "2015-09-09", "2014-01-02", "2012-12-31"):
        assert rc.dividend_tax(d(day)) == rc.dividend_tax(d(day), reading_2015="after"), day
    r = rc.lookup("divtax", d("2015-09-08"))
    assert r.unverified_item == 17 and "2015-09-08" in r.note and r.status == rc.V
    try:
        rc.dividend_tax(d("2015-09-08"), reading_2015="x")
    except rc.CalendarError:
        return
    raise AssertionError("unknown reading must raise")


def test_source_status_transcription():
    """Status fields use the plan's vocabulary; the 'must' items 1-4 of PLAN 3.10 are marked unverified."""
    vocab = (rc.V, rc.OP, rc.IND, rc.UNV, rc.NF)
    for r in rc.RULES:
        assert any(v in r.status for v in vocab), r
        assert r.unverified_item is None or 1 <= r.unverified_item <= 21      # the v0.7 list has 21 entries
    def row(key, day):
        return rc.lookup(key, d(day))
    assert rc.UNV in row("stamp", "2023-08-28").status and row("stamp", "2023-08-28").unverified_item == 1
    assert row("stamp", "2010-01-04").status == rc.OP
    assert rc.UNV in row("transfer:sh", "2022-04-29").status and row("transfer:sh", "2022-04-29").unverified_item == 2
    assert rc.UNV in row("transfer:sh", "2010-01-04").status and row("transfer:sh", "2010-01-04").unverified_item == 3
    assert row("transfer:sz", "2016-01-04").status == rc.OP
    assert rc.UNV in row("divtax", "2012-06-01").status and row("divtax", "2012-06-01").unverified_item == 4
    assert row("divtax", "2014-06-01").status == rc.V and row("divtax", "2016-06-01").status == rc.V
    assert row("band:main:0", "2012-06-01").status == rc.V
    assert row("band:chinext:0", "2021-06-01").date_status == rc.OP
    assert row("band:star:0", "2021-06-01").date_status == rc.UNV
    n_unv = sum(1 for r in rc.RULES if rc.UNV in r.status or rc.UNV in r.date_status)
    return {"rows": len(rc.RULES), "rows_with_unverified_value_or_date": n_unv}


def test_flagged_days_and_info_rows():
    assert rc.flagged_day(d("2016-01-04")) and rc.flagged_day(d("2016-01-07")) and rc.flagged_day(d("2016-01-05")) is None
    assert rc.has_closing_auction(d("2018-08-17"), "sh") is False and rc.has_closing_auction(d("2018-08-20"), "sh") is True
    assert rc.has_closing_auction(d("2010-01-04"), "sz") is True
    assert rc.delisting_regime(d("2020-12-30"))["arrangement_days"] == 30
    assert rc.delisting_regime(d("2020-12-31"))["arrangement_days"] == 15
    assert rc.commission_bounds(d("2015-01-05")) == {"max_rate": 0.003, "min_per_trade": 5.0}


TESTS = [test_stamp_duty_boundaries, test_transfer_fee_boundaries, test_dividend_tax_boundaries,
         test_price_bands, test_limit_price_rounding, test_limit_price_full_grid_vs_integer_arithmetic,
         test_limit_prices_for_code_and_date,
         test_boards_and_exchanges, test_lot_rounding, test_window_and_unique_coverage,
         test_every_boundary_changes_value, test_source_status_transcription, test_flagged_days_and_info_rows,
         test_disclosure_regimes_group_e, test_dividend_tax_boundary_day_two_readings]

if __name__ == "__main__":
    run_tests("rule_calendar", TESTS, "rule_calendar.json")

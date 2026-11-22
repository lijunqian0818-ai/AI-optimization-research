"""Cases added for PLAN v0.7 (rulings E-7 ... E-19, G-1 ... G-3; task list ENG-5 ... ENG-17 and
TODO-E3, TODO-E6).  Ledger, label, attribution and disposition rules on constructed panels.

Every expected number is computed by hand in the comment next to it; none is produced by the
code under test.  Default cost rates: commission 0.00025, slippage 0.0005 per side; 2016 and
later: transfer fee 0.00002 both sides, stamp duty 0.001 on sells -> buy 0.00077, sell 0.00177.
"""
from __future__ import annotations

import csv
import hashlib
import tempfile
from dataclasses import replace
from datetime import date
from pathlib import Path

import numpy as np
from common import N, NAN, S, SRC, T, X, close, panel, run_tests
from test_ledger_r4 import day, led1

from engine import dispositions as disp
from engine import monitor, simulate
from engine.attribution import ReturnTrack, lemma3, periods_from_track, reference_cost
from engine.config import CONVENTION_FILES, EngineConfig, conventions_hash
from engine.labels import deadline_label, label_o1
from engine.ledger import Ledger
from engine.market import Event, Valuer, succ_id

d = date.fromisoformat
CFG = EngineConfig()
SZ, SZ2, SH = "sz.000001", "sz.000002", "sh.600036"
W0 = 100000.0
BASE = [T(10, 10, 10), T(10, 10, 10), T(10, 10.4, 10)]


# ------------------------------------------------------------------ ENG-5 (E-7)
def test_reference_cost_close_instant_component():
    """E-7 (b): a reference path that changes ONLY at a close.
    A: open 10, close 11 on day 1, flat afterwards; C: 20 throughout.  Overnight returns are 0.
    G holds 100 A; B holds 100 A + 100 C (both bought at the open of day 1).
    Auction of day 1: e^G = 1000, w^B = (1/3, 2/3) -> s^E = (33.33.. A, 33.33.. C); implied trade
        1000 -> C_E_open = 1000 x 0.00077 = 0.77.
    Close of day 1 (CV: A 11, C 20): e^G = 1100, w^B = (11/31, 20/31) -> s^E = 35.4838.. of each;
        carried shares 33.33.. of each are worth 1033.33..; all changes are buys:
        amount = 1100 - 1033.33.. = 66.66.. -> C_E_close = (200/3) x 0.00077 = 0.051333..
    Auction of day 2: prices unchanged -> no implied trade."""
    A, C = SZ, SZ2
    rows = {A: [T(10, 10, 10), T(10, 11, 10), T(11, 11, 11)], C: [T(20, 20, 20)] * 3}
    m = panel(d("2016-03-01"), rows)
    val = Valuer(m)
    G, B = led1(m, valuer=val), led1(m, valuer=val)
    day(G, 0); day(G, 1, buys=[(A, 100.0)]); day(G, 2)
    day(B, 0); day(B, 1, buys=[(A, 100.0), (C, 100.0)]); day(B, 2)
    tr = ReturnTrack(m, val, CFG)
    pG, _ = periods_from_track([tr.day(G, i) for i in (1, 2)])
    pB, _ = periods_from_track([tr.day(B, i) for i in (1, 2)])
    rc_ = reference_cost(tr, pG, pB)
    assert close(rc_["C_E_open"], 0.77, 1e-12), rc_["C_E_open"]
    assert close(rc_["C_E_close"], (200.0 / 3.0) * 0.00077, 1e-12), rc_["C_E_close"]
    assert rc_["C_E"] == rc_["C_E_open"] + rc_["C_E_close"] and rc_["C_E_close"] > 0.05
    assert close(rc_["by_instant"][(1, "open")], 1000.0, 1e-12)
    assert close(rc_["by_instant"][(2, "close")], 200.0 / 3.0, 1e-12)      # key (t+1, 'close') = close of day t
    assert rc_["by_instant"].get((2, "open"), 0.0) <= 1e-10 * W0
    # the three terms of the decomposition do not depend on C^E: lemma3 has no such argument
    r = lemma3(pG, pB, 0.77, 2.31)
    assert abs(r["residual"]) <= 1e-10 * W0
    return {"C_E_open": rc_["C_E_open"], "C_E_close": rc_["C_E_close"]}


# ------------------------------------------------------------------ ENG-7 (E-9)
def test_record_date_2015_09_08_two_readings():
    """Record date 2015-09-08 under both readings of the 2015 notice (PLAN 3.10 list item 17).
    Buy 1000 @ 10.00 (cost 7.7); gross dividend 500; tau = 20% under both.
      'from'  (in force): nothing withheld: cash paid 500, liability 100
      'after'           : 5% withheld:     cash paid 475, liability 75
    Identical under both: wealth (W_open on the ex-date = 100000 - 10007.7 + 9500 + 400 = 99892.3),
    cash net of liabilities (89992.3 + 400 = 90392.3), the O1 label (net 9500 - 16.815 + 400 =
    9883.185) and the final wealth after the sale at 9.60 (99975.308)."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), T(9.5, 9.6, 9.5), T(9.6, 9.6, 9.6), T(9.6, 9.6, 9.6)]
    out = {}
    for reading, paid, liab in (("from", 500.0, 100.0), ("after", 475.0, 75.0)):
        cfg = replace(CFG, divtax_2015_reading=reading)
        m = panel(d("2015-09-04"), {SZ: rows}, [Event(SZ, "dist", ex_date=d("2015-09-09"), gross_cash=0.5, phi=1.0)])
        assert m.days[2] == d("2015-09-08") and m.days[3] == d("2015-09-09")
        led = led1(m, cfg=cfg)
        day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2)
        cash_before = led.cash[0]
        led.begin_day(3)
        assert close(led.cash[0], cash_before + paid) and close(lot.tax_liability, liab), (reading, led.cash[0])
        assert close(led.rec[3]["W_open"], 99892.3, 1e-12)
        assert close(led.spendable(0), 90392.3, 1e-12)
        led.end_day(3)
        day(led, 4); day(led, 5, sells=[[lot]])
        assert lot.tax_liability == 0.0 and close(led.rec[5]["W_close"], 99975.308, 1e-12)
        lab = label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 2, cfg)
        assert close(lab.net_proceeds, 9883.185, 1e-12) and lab.label == 1 and close(lab.cash, 400.0)
        out[reading] = {"cash_paid": paid, "liability": liab, "W_open_ex": led.rec[3]["W_open"],
                        "spendable": 90392.3, "label_net": lab.net_proceeds}
    assert out["from"]["W_open_ex"] == out["after"]["W_open_ex"] and out["from"]["label_net"] == out["after"]["label_net"]
    return out


# ------------------------------------------------------------------ ENG-8 (E-11, G-1)
def test_forced_class_U_event_label_U_ledger_as_URS():
    """An event the event table could not classify (forced_class 'U'): the label of every entry whose
    window contains its effective day is U; the ledger books nothing - shares and cash unchanged,
    market valuation - and flags the name (the URS convention of PLAN 3.9)."""
    ev = Event(SZ, "dist", ex_date=d("2016-03-04"), gross_cash=0.5, phi=2.0, forced_class="U")
    m = panel(d("2016-03-01"), {SZ: BASE + [T(12, 12, 10.4), T(12, 12, 12)]}, [ev])
    assert m.events_on(SZ, 3) == [] and m.unclassifiable_on(SZ, 3) is not None
    lab = label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 2, CFG)
    assert (lab.outcome, lab.label) == ("U", 1) and "cannot be classified" in lab.why
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert lot.status == "open" and lot.q == 1000.0 and lot.div_net == 0.0 and led.receivables == []
    assert close(led.rec[3]["W_close"], W0 - 10007.7 + 12000.0) and led.net_traded_amount(3) == 0.0
    assert any(f[0] == 3 and "not booked" in f[2] for f in led.flags)
    assert led.extra_counts["unclassifiable_not_booked"] == 1 and led.counts["S-a"] == 0 and led.counts["S-b"] == 0
    tr = ReturnTrack(m, led.val, CFG)
    assert close(tr.x_on(SZ, 3), 12.0 / 10.4 - 1.0, 1e-15)                 # plain price return, nothing booked
    # outside the window the label is unaffected: entry day 3, H = 1, mark day 4
    lab2 = label_o1(m, Valuer(m), SZ, 3, 1000.0, 12.0, 9.24, 1, CFG)
    assert lab2.outcome == "value"
    # the P1 restatement ignores it as well: suspended on the effective day
    m2 = panel(d("2016-03-01"), {SZ: BASE + [S(5.2)]}, [ev])
    v = Valuer(m2).ov(SZ, 3)
    assert v.branch == "P1" and v.value == 10.4
    # undecided date conflict (Market.u_spans): U for windows that contain a day of the span
    m3 = panel(d("2016-03-01"), {SZ: [T(10, 10, 10)] * 9},
               u_spans={SZ: [(d("2016-03-04"), d("2016-03-08"), "date conflict")]})
    assert label_o1(m3, Valuer(m3), SZ, 1, 1000.0, 10.0, 7.7, 2, CFG).outcome == "U"      # window days 2, 3
    assert label_o1(m3, Valuer(m3), SZ, 4, 1000.0, 10.0, 7.7, 1, CFG).outcome == "U"      # window day 5
    assert label_o1(m3, Valuer(m3), SZ, 5, 1000.0, 10.0, 7.7, 2, CFG).outcome == "value"  # window days 6, 7 (03-09, 03-10)


# ------------------------------------------------------------------ ENG-9 (E-12)
def test_same_day_dividend_and_rights_record_date_in_suspension():
    """PLAN 3.8 (iii) note (7).  Last traded close 10.00 (day 2); suspended days 3..5.
    (i)  dividend ex-date (gross 0.5) and rights record date (rho 0.2, P_r 8) both on day 4:
         dividend first: (10 - 0.5)/1 = 9.5; then P1-R: min(9.5, (9.5 + 1.6)/1.2 = 9.25) = 9.25.
         (The other order would give (10 + 1.6)/1.2 - 0.5 = 9.1667.)
         On day 4 itself only the dividend has taken effect (the rights at the CLOSE of day 4): 9.5.
    (ii) rights record date on day 3, dividend ex-date on day 4: the rights first (close of day 3
         precedes the open of day 4): (10 + 1.6)/1.2 = 9.6667; then - 0.5 = 9.1667."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), S(10.0), S(9.5), S(9.5)]
    m = panel(d("2016-03-01"), {SZ: rows}, [
        Event(SZ, "dist", ex_date=d("2016-03-07"), gross_cash=0.5, phi=1.0),
        Event(SZ, "rights", ex_date=d("2016-03-16"), record_date=d("2016-03-07"), rights_price=8.0, rights_ratio=0.2)])
    assert m.days[4] == d("2016-03-07")
    val = Valuer(m)
    assert val.ov(SZ, 3).value == 10.0 and val.ov(SZ, 3).branch == "P1"
    assert close(val.ov(SZ, 4).value, 9.5, 1e-15) and val.ov(SZ, 4).branch == "P1"
    v5 = val.ov(SZ, 5)
    assert v5.branch == "P1R" and close(v5.value, 9.25, 1e-15), v5
    led = led1(m, valuer=val)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3); day(led, 4); day(led, 5)
    assert close(led.rec[4]["W_open"] - led.rec[3]["W_close"], -500.0 + 400.0, 1e-12)   # price -0.5, net dividend +0.4
    assert close(led.rec[5]["W_open"] - led.rec[4]["W_close"], 1000.0 * (9.25 - 9.5), 1e-12)
    lab = label_o1(m, val, SZ, 1, 1000.0, 10.0, 7.7, 4, CFG)                   # mark day 5
    # net = 9250 - 9250 x 0.00177 (16.3725) + 400 = 9633.6275
    assert lab.events == ["S-a", "S-c"] and lab.price_branch == "P1R" and close(lab.net_proceeds, 9633.6275, 1e-12)
    m2 = panel(d("2016-03-01"), {SZ: rows}, [
        Event(SZ, "dist", ex_date=d("2016-03-07"), gross_cash=0.5, phi=1.0),
        Event(SZ, "rights", ex_date=d("2016-03-16"), record_date=d("2016-03-04"), rights_price=8.0, rights_ratio=0.2)])
    v = Valuer(m2).ov(SZ, 5)
    assert v.branch == "P1R" and close(v.value, 11.6 / 1.2 - 0.5, 1e-15), v
    return {"same_day": v5.value, "rights_first": v.value}


# ------------------------------------------------------------------ ENG-10 (E-13)
def _cash_exit_market():
    rows = {SZ: [T(10, 10, 10), T(10, 10, 10), T(9.5, 9.6, 9.5), X()], SZ2: [T(20, 20, 20)] * 4}
    evs = [Event(SZ, "dist", ex_date=d("2016-03-03"), gross_cash=0.5, phi=1.0),
           Event(SZ, "cashout", ex_date=d("2016-03-04"), cash_per_share=10.5)]
    return panel(d("2016-03-01"), rows, evs, delist={SZ: 3})


def test_cash_exit_no_sell_charge_liability_debited():
    """E-13 (a): buy 1000 @ 10 (7.7); dividend 0.5 gross with record date = entry day (2016: paid 500,
    liability 100); cash exit at 10.50 on day 3.
    Ledger: cash = 100000 - 10007.7 + 500 + 10500 - 100 = 100892.3; no cost on day 3; liability 0.
    Label (H = 2): D = 400 + 10500 = 10900, no sell-side charge -> net 10900 >= 10007.7 -> 0.
    (b) sensitivity cash_exit_explicit_charges: commission 2.625 + stamp 10.5 + transfer 0.21 = 13.335
    on the cash amount (no shortfall): ledger cash 100878.965, label net 10886.665."""
    m = _cash_exit_market()
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2)
    assert close(lot.tax_liability, 100.0)
    day(led, 3)
    assert lot.status == "cashed_out" and lot.tax_liability == 0.0 and led.outstanding_liability() == 0.0
    assert close(led.cash[0], 100892.3, 1e-12) and led.rec[3]["cost"] == 0.0 and lot.sell_cost == 0.0
    assert led.net_traded_amount(3) == 0.0 and led.order_turnover(3) == 0.0 and lot.label_o2 == 0
    lab = label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 2, CFG)
    assert lab.price_branch == "cash" and close(lab.net_proceeds, 10900.0, 1e-12) and lab.label == 0
    assert lab.exit_charges == 0.0 and lab.events == ["S-a", "S-d"]
    # (b) sensitivity
    cfg = replace(CFG, cash_exit_explicit_charges=True)
    m = _cash_exit_market()
    led = led1(m, cfg=cfg)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert close(led.rec[3]["cost"], 13.335, 1e-12) and close(lot.sell_cost, 13.335, 1e-12)
    assert close(led.cash[0], 100892.3 - 13.335, 1e-12) and led.order_turnover(3) == 0.0
    lab = label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 2, cfg)
    assert close(lab.net_proceeds, 10886.665, 1e-12) and close(lab.exit_charges, 13.335, 1e-12)
    tr = ReturnTrack(m, led.val, cfg)                                      # track and ledger still agree
    for i in (1, 2, 3):
        assert abs(tr.day(led, i)["dW_A"] - (led.rec[i]["W_close"] - led.rec[i]["W_prev_close"])) < 1e-9
    # write-off (no S-d record): the liability is debited at the write-off as well
    m = panel(d("2016-03-01"), {SZ: [T(10, 10, 10), T(10, 10, 10), T(9.5, 9.6, 9.5), X()]},
              [Event(SZ, "dist", ex_date=d("2016-03-03"), gross_cash=0.5, phi=1.0)], delist={SZ: 3})
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert lot.status == "written_off" and lot.tax_liability == 0.0
    assert close(led.cash[0], 100000.0 - 10007.7 + 500.0 - 100.0, 1e-12)
    return {"cash_after_exit": 100892.3, "sensitivity_charges": 13.335}


def test_sell_charges_exclude_cash_part():
    """E-13 (c): a lot with a dividend in its holding period: the sell-side charges are computed on the
    security part q x m only (9,600 -> 16.992), never on q x m + D."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), T(9.5, 9.6, 9.5), T(9.6, 9.6, 9.6)]
    m = panel(d("2016-03-01"), {SZ: rows}, [Event(SZ, "dist", ex_date=d("2016-03-04"), gross_cash=0.5, phi=1.0)])
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3); day(led, 4, sells=[[lot]])
    assert led.trades[-1]["amount"] == 9600.0 and close(lot.sell_cost, 9600.0 * 0.00177, 1e-12)
    assert close(lot.sell_cost, 16.992, 1e-12) and close(lot.div_net, 400.0)
    lab = label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 3, CFG)         # mark day 4 at 9.60
    assert close(lab.net_proceeds, 9600.0 - 16.992 + 400.0, 1e-12)
    assert close(lab.net_proceeds, lot.proceeds - lot.sell_cost + lot.div_net, 1e-12)


# ------------------------------------------------------------------ ENG-11 (E-14)
def test_successor_event_on_succession_day_is_U():
    """PLAN 3.8 (iii) note (9).  SZ is exchanged into SZ2 at 0.5 on day 3; SZ2 has a 2-for-1 split with
    ex-date day 3.  Lot by succession: label U; ledger: 500 shares (the split is NOT applied), valued
    at the market open 10.50, flagged.  A directly bought lot of SZ2 gets the split (100 -> 200)."""
    rows = {SZ: BASE + [X(), X()], SZ2: [T(20, 20, 20)] * 3 + [T(10.5, 10.6, 10.0), T(10.6, 10.6, 10.6)]}
    evs = [Event(SZ, "exchange", ex_date=d("2016-03-04"), successor=SZ2, ratio=0.5),
           Event(SZ2, "dist", ex_date=d("2016-03-04"), gross_cash=0.0, phi=2.0)]
    m = panel(d("2016-03-01"), rows, evs, delist={SZ: 3})
    lab = label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 2, CFG)
    assert (lab.outcome, lab.label) == ("U", 1) and "succession day" in lab.why and lab.events == ["S-e"]
    led = led1(m)
    day(led, 0); a, b = day(led, 1, buys=[(SZ, 1000.0), (SZ2, 100.0)]); day(led, 2); day(led, 3)
    assert a.code == SZ2 and a.q == 500.0 and a.track_id == succ_id(SZ2) and b.q == 200.0 and b.track_id == SZ2
    assert led.rec[3]["s_pre"] == {succ_id(SZ2): 500.0, SZ2: 200.0}
    # cash = 100000 - 10007.7 - (2000 + 1.54); holdings 500 x 10.5 + 200 x 10.5
    assert close(led.rec[3]["W_open"], 100000.0 - 10007.7 - 2001.54 + 700.0 * 10.5, 1e-12)
    assert led.extra_counts["successor_event_on_succession_day"] == 1 and led.net_traded_amount(3) == 0.0
    assert any("succession day" in f[2] for f in led.flags)
    day(led, 4)
    tr = ReturnTrack(m, led.val, CFG)
    for i in (1, 2, 3, 4):
        assert abs(tr.day(led, i)["dW_A"] - (led.rec[i]["W_close"] - led.rec[i]["W_prev_close"])) < 1e-9, i


def test_successor_event_after_succession_day_applies():
    """Entitlement by record date >= succession day: SZ -> SZ2 at 0.5 on day 3; SZ2 pays 0.2 gross with
    ex-date day 4 (record date day 3).  The lot by succession holds 500 shares at that record date:
    gross 100, net 80 (2016: tau 20%, nothing withheld -> receivable 100, liability 20).
    Label, H = 3, mark day 4 at 20.80: 500 x 20.8 = 10400 - 18.408 + 80 = 10461.592 -> 0."""
    rows = {SZ: BASE + [X(), X()], SZ2: [T(20, 20, 20)] * 3 + [T(21.0, 21.0, 20.0), T(20.8, 20.8, 20.8)]}
    evs = [Event(SZ, "exchange", ex_date=d("2016-03-04"), successor=SZ2, ratio=0.5),
           Event(SZ2, "dist", ex_date=d("2016-03-07"), gross_cash=0.2, phi=1.0)]
    m = panel(d("2016-03-01"), rows, evs, delist={SZ: 3})
    lab = label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 3, CFG)
    assert lab.outcome == "value" and lab.events == ["S-e", "S-a"] and close(lab.cash, 80.0)
    assert close(lab.net_proceeds, 10461.592, 1e-12) and lab.label == 0
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3); day(led, 4)
    assert close(lot.div_net, 80.0) and close(lot.tax_liability, 20.0) and lot.q == 500.0
    tr = ReturnTrack(m, led.val, CFG)
    assert close(tr.x_on(succ_id(SZ2), 4), (20.8 + 0.16) / 21.0 - 1.0, 1e-15)


def test_lot_by_succession_and_direct_lot_then_cash_out_of_successor():
    """E-14 (b): G holds a lot that arrived by succession (SZ -> SZ2 on day 3; 500 shares) and a directly
    bought lot of SZ2 (100 shares, day 2).  SZ2 is cashed out at 22.00 on day 5.
      lot by succession: a further S-d of the successor is class U -> written off at 0; label U
      direct lot:        S-d -> cash 2,200; label 'value'
    In the track the two are different identifiers with different overnight returns on day 5
    (-1 and 22/21 - 1); Lemma 3 holds; track and ledger agree every day."""
    rows = {SZ: BASE + [X(), X(), X()],
            SZ2: [T(20, 20, 20), T(20, 20.2, 20), T(20.2, 20.4, 20.2), T(21.0, 21.2, 20.4), T(21.2, 21.0, 21.2), X()],
            SH: [T(5, 5, 5), T(5, 5.1, 5), T(5.1, 5.0, 5.1), T(5.0, 5.2, 5.0), T(5.2, 5.2, 5.2), T(5.3, 5.3, 5.2)]}
    evs = [Event(SZ, "exchange", ex_date=d("2016-03-04"), successor=SZ2, ratio=0.5),
           Event(SZ2, "cashout", ex_date=d("2016-03-08"), cash_per_share=22.0)]
    m = panel(d("2016-03-01"), rows, evs, delist={SZ: 3, SZ2: 5})
    assert m.days[5] == d("2016-03-08")
    val = Valuer(m)
    G, B = led1(m, valuer=val, name="G"), led1(m, valuer=val, name="B")
    day(G, 0); a, = day(G, 1, buys=[(SZ, 1000.0)]); b, = day(G, 2, buys=[(SZ2, 100.0)])
    day(B, 0); day(B, 1, buys=[(SZ2, 200.0)]); day(B, 2, buys=[(SH, 1000.0)])
    for i in (3, 4, 5):
        day(G, i); day(B, i)
    assert a.status == "written_off" and a.proceeds == 0.0 and a.label_o2 == 1
    assert b.status == "cashed_out" and b.proceeds == 2200.0
    assert G.counts["S-e"] == 1 and G.counts["S-d"] == 1 and G.counts["U"] == 1
    assert G.rec[5]["s_on"] == {succ_id(SZ2): 500.0, SZ2: 100.0}
    la = label_o1(m, val, SZ, 1, 1000.0, 10.0, a.buy_cost, 4, CFG)          # mark day 5
    lb = label_o1(m, val, SZ2, 2, 100.0, 20.2, b.buy_cost, 3, CFG)          # mark day 5
    assert (la.outcome, la.label) == ("U", 1) and "successor" in la.why
    assert lb.outcome == "value" and lb.price_branch == "cash" and close(lb.net_proceeds, 2200.0)
    tr = ReturnTrack(m, val, CFG)
    assert tr.x_on(succ_id(SZ2), 5) == -1.0 and close(tr.x_on(SZ2, 5), 22.0 / 21.0 - 1.0, 1e-15)
    dG = [tr.day(G, i) for i in range(1, 6)]
    dB = [tr.day(B, i) for i in range(1, 6)]
    r2 = 0.0
    for led, days_ in ((G, dG), (B, dB)):
        for x in days_:
            r = led.rec[x["i"]]
            r2 = max(r2, abs(x["dW_A"] - (r["W_close"] - r["W_prev_close"])) / r["W_prev_close"])
    assert r2 <= CFG.tol_R2_daily, r2
    pG, cG = periods_from_track(dG)
    pB, cB = periods_from_track(dB)
    res = lemma3(pG, pB, cG, cB)
    assert abs(res["residual"]) <= CFG.tol_R1 * W0 and abs(res["residual_alt"]) <= CFG.tol_R1 * W0
    assert res["max_return_mismatch"] == 0.0
    wealth_diff = G.rec[5]["W_close"] - B.rec[5]["W_close"]
    assert abs(res["diff"] - wealth_diff) <= 1e-6
    return {"R2_daily_rel": r2, "lemma3_residual": res["residual"], "terms_minus_wealth_diff": res["sum_terms"] - wealth_diff}


# ------------------------------------------------------------------ ENG-12 (E-15)
def test_rights_issue_with_missing_record_date():
    """PLAN 3.8 (iii) note (10); U58 = 10.  Entry day 1, H = 2, mark day 3.
    (a) ex-date known: M iff it lies in (t, t+H+10] = days 2..13.
    (b) neither date known: M iff the entry day is on or after the record's earliest date
        (announcement); (c) a record without any date: M for every entry."""
    rows = [T(10, 10, 10)] * 16
    whys: dict = {}

    def lab(ev, entry=1):
        m = panel(d("2016-03-01"), {SZ: rows}, [ev])
        r = label_o1(m, Valuer(m), SZ, entry, 1000.0, 10.0, 7.7, 2, CFG)
        if r.outcome != "value":
            whys[r.why] = whys.get(r.why, 0) + 1
        return r.outcome
    days_ = panel(d("2016-03-01"), {SZ: rows}).days
    kw = dict(rights_price=8.0, rights_ratio=0.2)
    assert lab(Event(SZ, "rights", ex_date=days_[9], **kw)) == "M"
    assert lab(Event(SZ, "rights", ex_date=days_[13], **kw)) == "M"          # t + H + 10 = day 13: inside
    assert lab(Event(SZ, "rights", ex_date=days_[14], **kw)) == "value"      # day 14: outside
    assert lab(Event(SZ, "rights", ex_date=days_[2], **kw)) == "M"
    assert lab(Event(SZ, "rights", ex_date=days_[1], **kw)) == "value"       # ex-date on the entry day: not in (t, ...]
    assert lab(Event(SZ, "rights", announce_date=days_[1], **kw)) == "M"     # entry on the announcement day
    assert lab(Event(SZ, "rights", announce_date=days_[0], **kw)) == "M"
    assert lab(Event(SZ, "rights", announce_date=days_[2], **kw)) == "value"  # entry before the earliest date
    assert lab(Event(SZ, "rights", announce_date=days_[2], **kw), entry=5) == "M"
    assert lab(Event(SZ, "rights", **kw)) == "M"                             # no date at all
    assert lab(Event(SZ, "rights", **kw), entry=12) == "M"
    assert whys == {"rights issue without record date (ex-date inside the window)": 3,
                    "rights issue without record date and ex-date": 5}, whys
    return {"M_by_reason": whys}


# ------------------------------------------------------------------ ENG-13 (E-16, F-18)
def test_missing_row_inside_P1_carry_gives_M():
    """PLAN 3.8 (iii) note (11).  Entry day 1; last traded close 10.2 on day 2; day 3 suspended;
    day 4 NO ROW; day 5 suspended (mark day, H = 4): the carry would cross a day without a row -> M.
    Ledger: valued by P1 at 10.2 on days 3-5, flagged.  With a suspended-day row on day 4 instead:
    value (P1).  Mark day itself without a row: M (unchanged)."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10.2, 10), S(10.2), X(), S(10.2), T(10.3, 10.3, 10.2)]
    m = panel(d("2016-03-01"), {SZ: rows})
    val = Valuer(m)
    lab = label_o1(m, val, SZ, 1, 1000.0, 10.0, 7.7, 4, CFG)
    assert (lab.outcome, lab.label) == ("M", 1) and "without a bar row" in lab.why
    assert label_o1(m, val, SZ, 1, 1000.0, 10.0, 7.7, 3, CFG).why == "no bar row on the mark day"
    assert label_o1(m, val, SZ, 1, 1000.0, 10.0, 7.7, 2, CFG).outcome == "value"          # day 3: no missing row yet
    assert label_o1(m, val, SZ, 1, 1000.0, 10.0, 7.7, 5, CFG).outcome == "value"          # day 6: traded
    led = led1(m, valuer=val)
    day(led, 0); day(led, 1, buys=[(SZ, 1000.0)])
    for i in range(2, 7):
        day(led, i)
    assert led.rec[4]["W_open"] == led.rec[2]["W_close"] and led.rec[5]["W_open"] == led.rec[2]["W_close"]
    assert any(f[0] == 4 and "no row" in f[2] for f in led.flags)
    assert any(f[0] == 5 and "carry across a day without a row" in f[2] for f in led.flags)
    rows2 = list(rows)
    rows2[4] = S(10.2)
    m2 = panel(d("2016-03-01"), {SZ: rows2})
    lab2 = label_o1(m2, Valuer(m2), SZ, 1, 1000.0, 10.0, 7.7, 4, CFG)
    assert lab2.outcome == "value" and lab2.price_branch == "P1" and lab2.mark == 10.2 and lab2.spell == 3


def test_filled_from_xsrc_flag_is_carried_through():
    """PLAN 3.11 rule 12 / E-16 (b): a row inserted by the fetch pipeline from the cross-check source is
    an ordinary traded row for fills and labels; the flag appears in the order ledger, the trade
    ledger and the label.  The engine never sets the flag itself."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10.1, 10.2, 10), T(10.5, 10.5, 10.2), T(10.5, 10.5, 10.5)]
    cfg = replace(CFG, H=2, K=1, W0=3.0e5)
    plain = panel(d("2021-03-01"), {SH: rows})
    flagged = panel(d("2021-03-01"), {SH: rows})
    f = np.zeros(5, bool)
    f[2] = True
    flagged.secs[SH].filled_from_xsrc = f
    res = []
    for m in (plain, flagged):
        led, orders = simulate.run(m, cfg, {1: [(SH, 1.0)], 2: [(SH, 1.0)]}, 1, 4)
        res.append((led, orders))
    (l0, o0), (l1, o1) = res
    assert [(o["i"], o["side"], o["filled"], o["q"]) for o in o0] == [(o["i"], o["side"], o["filled"], o["q"]) for o in o1]
    assert l0.rec[4]["W_close"] == l1.rec[4]["W_close"]
    assert not any(o["filled_xsrc"] for o in o0)
    assert [o["filled_xsrc"] for o in o1 if o["i"] == 2] == [True] and sum(o["filled_xsrc"] for o in o1) == 1
    assert [t["filled_xsrc"] for t in l1.trades if t["i"] == 2] == [True]
    labs0, labs1 = [l.label_o1 for l in l0.lots], [l.label_o1 for l in l1.lots]
    assert labs1[0].filled_xsrc is True and labs0[0].filled_xsrc is False    # entry day 1, window days 1..3
    assert (labs0[0].label, labs0[0].net_proceeds) == (labs1[0].label, labs1[0].net_proceeds)
    assert simulate.order_summary(o1)["total"]["orders_on_xsrc_rows"] == 1


# ------------------------------------------------------------------ ENG-15 (E-18, G-3)
def _disp_rows():
    return {SZ: BASE + [X(), X(), X(), X()],
            SZ2: [T(20, 20, 20), T(20, 20, 20), T(20, 20, 20), T(20.5, 20.5, 20), T(20.6, 20.6, 20.5),
                  T(21.0, 21.5, 20.6), T(21.5, 21.5, 21.5)]}


def test_disposition_table_absent_falls_back_to_write_off():
    """E-18 (a): no table, or no row for the name -> class U, written off (the v0.6 behaviour), and the
    name is listed so that the fallback sentence can be printed."""
    table, problems = disp.read_table(Path(tempfile.gettempdir()) / "no_such_dir_engine_test" / "x.csv")
    assert table == {} and len(problems) == 1 and "not found" in problems[0]
    m = panel(d("2016-03-01"), _disp_rows(), delist={SZ: 3})
    rep = disp.apply(m, table)
    assert rep["no_row"] == [SZ] and rep["fallback_sentence_required"] and rep["delisted_names"] == 1
    assert rep["fallback_sentence"] == "delistings are written off, including absorptions by share exchange"
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert lot.status == "written_off" and close(led.rec[3]["W_open"], W0 - 10007.7)      # as in v0.6
    assert label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 2, CFG).outcome == "U"
    assert disp.affected_lots([led], rep) == {"lots_written_off_without_a_row": 1, "by_name": {SZ: 1}}
    # sensitivity "last traded price" (U33)
    led = led1(m, cfg=replace(CFG, terminal_value_U=1.0))
    day(led, 0); day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert close(led.rec[3]["W_open"], W0 - 10007.7 + 10400.0)


def test_disposition_share_exchange_with_carry():
    """E-18 (b): SZ leaves the bar file after day 2 (last close 10.40); the table says: exchanged into
    SZ2 at 0.5, new shares first trade on day 5.  The table is read from a CSV file.
    Ledger: days 3-4 carried at 1000 x 10.40 (flagged, not written off); day 5: 500 shares of SZ2,
    valued at its open 21.00; no trade, no cost on any of these days.
    Label: mark day 3 or 4 (successor's shares not yet listed) -> U; mark day 5 -> value:
    500 x 21 = 10500 - 18.585 = 10481.415 -> 0."""
    m = panel(d("2016-03-01"), _disp_rows(), delist={SZ: 3})
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "dispositions.csv"
        with open(f, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(disp.COLUMNS)
            w.writerow([SZ, "exchange", "", "0.5", SZ2, m.days[2].isoformat(), m.days[5].isoformat(), "", "https://example.invalid/a"])
        table, problems = disp.read_table(f)
    assert problems == [] and table[SZ]["ratio"] == 0.5 and table[SZ]["first_trade_date_new"] == m.days[5]
    rep = disp.apply(m, table)
    assert rep["exchange"] == [SZ] and rep["no_row"] == [] and rep["errors"] == [] and not rep["fallback_sentence_required"]
    assert m.secs[SZ].carry_until_i == 5 and m.in_carry(SZ, 3) and m.in_carry(SZ, 4) and not m.in_carry(SZ, 5)
    val = Valuer(m)
    led = led1(m, valuer=val)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2)
    for i in (3, 4):
        day(led, i)
        assert lot.status == "open" and lot.code == SZ and lot.q == 1000.0
        assert close(led.rec[i]["W_open"], W0 - 10007.7 + 10400.0, 1e-12) and led.rec[i]["W_close"] == led.rec[i]["W_open"]
        assert any(f_[0] == i and "carried" in f_[2] for f_ in led.flags)
    day(led, 5); day(led, 6)
    assert lot.code == SZ2 and lot.q == 500.0 and lot.succession_i == 5 and led.counts["S-e"] == 1 and led.counts["U"] == 0
    assert close(led.rec[5]["W_open"], W0 - 10007.7 + 500.0 * 21.0, 1e-12)
    assert close(led.rec[6]["W_close"], W0 - 10007.7 + 500.0 * 21.5, 1e-12)
    assert all(led.net_traded_amount(i) == 0.0 and led.rec[i]["cost"] == 0.0 for i in range(2, 7))
    assert led.extra_counts["carry_days"] == 2
    for H, exp in ((2, "U"), (3, "U"), (4, "value")):
        lab = label_o1(m, val, SZ, 1, 1000.0, 10.0, 7.7, H, CFG)
        assert lab.outcome == exp, (H, lab)
    assert close(lab.net_proceeds, 10481.415, 1e-12) and lab.label == 0 and lab.events == ["S-e"]
    tr = ReturnTrack(m, val, CFG)
    for i in range(1, 7):
        assert abs(tr.day(led, i)["dW_A"] - (led.rec[i]["W_close"] - led.rec[i]["W_prev_close"])) < 1e-9, i
    return {"carry_value": 10400.0, "value_after_succession": 10500.0}


def test_disposition_cash_other_terminated_and_errors():
    """E-18 (c) cash exit -> S-d; (d) 'other' and 'terminated' -> class U; (e) a row whose successor is
    not in the bar panel, or whose terms are unusable -> class U and listed under errors."""
    def run(row):
        m = panel(d("2016-03-01"), _disp_rows(), delist={SZ: 3})
        rep = disp.apply(m, {SZ: dict({"cash_per_share": None, "ratio": None, "successor": None,
                                       "last_trade_date": None, "first_trade_date_new": None,
                                       "effective_date": None, "url": ""}, **row)})
        led = led1(m)
        day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
        return m, rep, led, lot
    m, rep, led, lot = run({"disposition": "cash", "cash_per_share": 10.5})
    assert rep["cash"] == [SZ] and lot.status == "cashed_out" and close(led.cash[0], W0 - 10007.7 + 10500.0)
    assert label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 2, CFG).price_branch == "cash"
    for dsp in ("other", "terminated"):
        m, rep, led, lot = run({"disposition": dsp})
        assert rep[dsp] == [SZ] and rep["no_row"] == [] and lot.status == "written_off"
        assert close(led.rec[3]["W_open"], W0 - 10007.7)
        assert label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 2, CFG).outcome == "U"
    bad = [{"disposition": "exchange", "ratio": 0.5, "successor": "sh.600999"},        # successor not in the panel
           {"disposition": "exchange", "ratio": None, "successor": SZ2},               # no ratio
           {"disposition": "exchange", "ratio": 0.5, "successor": SZ},                 # itself
           {"disposition": "cash", "cash_per_share": None},                            # no amount
           {"disposition": "exchange", "ratio": 0.5, "successor": SZ2, "first_trade_date_new": d("2016-03-02")}]
    for row in bad:
        m, rep, led, lot = run(row)
        assert rep["other"] == [SZ] and len(rep["errors"]) == 1 and lot.status == "written_off", row
        assert label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 2, CFG).outcome == "U"
    # a successor whose first row lies after the stated first trading day of the new shares
    rows = _disp_rows()
    rows[SZ2] = [X(), X(), X(), X(), X(), T(21.0, 21.5, 21.0), T(21.5, 21.5, 21.5)]
    m = panel(d("2016-03-01"), rows, delist={SZ: 3})
    rep = disp.apply(m, {SZ: {"disposition": "exchange", "cash_per_share": None, "ratio": 0.5, "successor": SZ2,
                              "last_trade_date": None, "first_trade_date_new": m.days[4], "effective_date": None, "url": ""}})
    assert rep["other"] == [SZ] and "not listed" in rep["errors"][0]
    return {"error_rows_tested": len(bad) + 1}


# ------------------------------------------------------------------ ENG-16 (E-19)
def test_cash_return_overnight_only_intraday_zero():
    """E-19: cash return 3.65% p.a. (ACT/365 -> 1e-4 per calendar day), intraday rate 0.
    Thursday -> Friday: 1 day; Friday -> Monday: 3 days.  100 -> 100 x 1.0001 x 1.0003 = 100.040003."""
    m = panel(d("2016-03-03"), {SZ: [T(10, 10, 10)] * 3})
    assert [x.weekday() for x in m.days] == [3, 4, 0]
    cfg = replace(CFG, cash_return=0.0365, W0=100.0, H=2, K=1)
    on, idr = simulate.cash_return_schedule(m, cfg)
    assert close(on[1], 1e-4, 1e-15) and close(on[2], 3e-4, 1e-15) and on[0] == 0.0 and not idr.any()
    led, _ = simulate.run(m, cfg, {}, 1, 2)
    assert close(led.rec[2]["W_close"], 100.0 * 1.0001 * 1.0003, 1e-14), led.rec[2]["W_close"]
    assert led.rec[1]["interest_id"] == 0.0 and led.rec[2]["interest_id"] == 0.0
    assert close(led.rec[1]["interest_on"], 0.01, 1e-12)
    led0, _ = simulate.run(m, replace(cfg, cash_return=0.0), {}, 1, 2)       # primary run: W4
    assert led0.rec[2]["W_close"] == 100.0 and led0.rho_on is None


# ------------------------------------------------------------------ ENG-17 (E-20)
def test_conventions_hash_in_result_records():
    """E-20: the SHA-256 of config.py and rule_calendar.py is in every result record; a record without
    it cannot be written."""
    h = conventions_hash()
    comb = hashlib.sha256()
    for name in CONVENTION_FILES:
        b = (SRC / "engine" / name).read_bytes()
        assert h[name] == hashlib.sha256(b).hexdigest()
        comb.update(b)
    assert h["combined"] == comb.hexdigest() and len(h["combined"]) == 64
    m = panel(d("2021-03-01"), {SH: [T(10, 10, 10)] * 4})
    cfg = replace(CFG, H=2, K=1, W0=3.0e5)
    led, orders = simulate.run(m, cfg, {1: [(SH, 1.0)]}, 1, 3)
    rec = simulate.result_record(led, orders, 1, 3)
    assert rec["conventions_hash"] == h and rec["config_hash"] == cfg.kappa_hash()
    assert replace(cfg, adv_counts_nontraded_days_as_zero=True).kappa_hash() != cfg.kappa_hash()
    # every parameter of the configuration has a recorded status (placeholder / ruling / plan silent)
    import dataclasses
    from engine.config import PARAM_STATUS
    assert set(PARAM_STATUS) == {f.name for f in dataclasses.fields(EngineConfig)}
    with tempfile.TemporaryDirectory() as tmp:
        simulate.write_result(Path(tmp) / "r.json", rec)
        assert "conventions_hash" in (Path(tmp) / "r.json").read_text(encoding="utf-8")
        try:
            simulate.write_result(Path(tmp) / "bad.json", {"x": 1})
        except ValueError:
            return {"combined": h["combined"]}
    raise AssertionError("a record without the conventions hash must be refused")


# ------------------------------------------------------------------ TODO-E3 (Cor. 1.3 labels, monitor counts)
def _deadline_run(end_i=10):
    A, B, C, Dn, E = "sz.000001", "sz.000002", "sz.000004", "sz.000005", "sz.000006"
    flat = [T(10, 10, 10)] * 3
    rows = {A: flat + [T(10.5, 10.5, 10.0)] + [T(10.5, 10.5, 10.5)] * 7,
            B: flat + [S(10.0)] * 6 + [T(10.0, 10.0, 10.0), T(10, 10, 10)],
            C: flat + [T(9.8, 9.8, 10.0)] + [T(9.8, 9.8, 9.8)] * 7,
            Dn: flat + [T(10.5, 10.5, 10.0)] + [T(10.5, 10.5, 10.5)] * 7,
            E: [T(10, 10, 10), T(10, 10, 10)] + [X()] * 9}
    evs = [Event(Dn, "dist", ex_date=d("2016-03-03"), gross_cash=NAN, phi=1.0)]
    m = panel(d("2016-03-01"), rows, evs, delist={E: 2})
    cfg = replace(CFG, H=2, K=5, W0=1.5e6, deadline_extra=3)            # D = 5, d_D = 6
    led, orders = simulate.run(m, cfg, {1: [(A, 1.0), (B, 1.0), (C, 1.0), (Dn, 1.0), (E, 1.0)]}, 1, end_i)
    return m, cfg, led, {l.entry_code: l for l in led.lots}, (A, B, C, Dn, E)


def test_deadline_labels_missing_record_gives_lower_0_upper_1():
    """Cor. 1.3 labels (draft; I-s6.4) with H = 2, D = H + 3 = 5; all entries on day 1; frozen at the
    start of day t + D + 1 = 7.
      A  sold day 3 at a gain                         S=1 V=1 L=0 -> (lo, hi) = (0, 0)
      C  sold day 3 at a loss                         S=1 V=1 L=1 -> (1, 1)
      B  suspended days 3-8, sold day 9 > t+D = 6     S=0 V=0     -> (0, 1)
      Dn sold day 3, but an event of the holding period has no amount (record incomplete)
                                                      S=1 V=0     -> (0, 1)   <- missing record
      E  delisted without a record (class U)          S=0 V=0     -> (0, 1)
    The O1 fallback M is NOT used: for Dn the O1 label is M (label 1) while the bracket is (0, 1)."""
    m, cfg, led, lots, (A, B, C, Dn, E) = _deadline_run()
    exp = {A: (1, 1, 0, 0, 0), C: (1, 1, 1, 1, 1), B: (0, 0, None, 0, 1), Dn: (1, 0, None, 0, 1), E: (0, 0, None, 0, 1)}
    for code, (S_, V_, L_, lo, hi) in exp.items():
        dl = lots[code].deadline
        assert dl is not None and (dl.S, dl.V, dl.L_cert, dl.lo, dl.hi) == (S_, V_, L_, lo, hi), (code, dl)
    assert lots[B].status == "sold" and lots[B].exit_i == 9             # sold after the deadline: label not revised
    assert lots[Dn].deadline.why == "record incomplete" and lots[Dn].incomplete_record
    assert lots[Dn].label_o1.outcome == "M" and lots[Dn].label_o1.label == 1
    assert lots[E].deadline.why == "class-U event before the deadline"
    # not revealed before day t + D + 1
    m2, cfg2, led2, lots2, _ = _deadline_run(end_i=6)
    assert all(l.deadline is None for l in led2.lots)
    # pure function: missing net proceeds -> (0, 1)
    dl = deadline_label("sold", 1, 3, 5, True, float("nan"), 100.0)
    assert (dl.S, dl.V, dl.lo, dl.hi) == (1, 0, 0, 1)
    return {code: (lots[code].deadline.lo, lots[code].deadline.hi) for code in exp}


def test_monitor_counts_and_truncation():
    """K_T, P_T, N_T (O1) and K^lo, K^hi, P^D (deadline labels) from frozen labels only.
    O1 (H = 2, revealed at T >= t + 3 = 4): A 0; C 1; B 1 (P1 mark 10.0 below the cost basis); Dn 1 (M);
    E 1 (U) -> K = 4.  Deadline labels (revealed at T >= 7): K^lo = 1, K^hi = 4.
    Counts at T from a run that stops at T equal the counts at T from the longer run."""
    m, cfg, led, lots, (A, B, C, Dn, E) = _deadline_run()
    assert monitor.o1_counts(led.lots, 0) == {"T": 0, "N_T": 0, "K_T": 0, "P_T": 0, "revealed": 0,
                                              "outcomes": {"value": 0, "U": 0, "M": 0}}
    c3, c4 = monitor.o1_counts(led.lots, 3), monitor.o1_counts(led.lots, 4)
    assert (c3["N_T"], c3["K_T"], c3["P_T"]) == (5, 0, 5)
    assert (c4["N_T"], c4["K_T"], c4["P_T"]) == (5, 4, 0) and c4["outcomes"] == {"value": 3, "U": 1, "M": 1}
    assert [lots[x].label_o1.label for x in (A, C, B, Dn, E)] == [0, 1, 1, 1, 1]
    d6, d7 = monitor.deadline_counts(led.lots, 6, cfg.deadline_extra), monitor.deadline_counts(led.lots, 7, cfg.deadline_extra)
    assert (d6["J_T"], d6["P_D_T"], d6["K_lo_T"], d6["K_hi_T"]) == (0, 5, 0, 0)
    assert (d7["N_T"], d7["J_T"], d7["P_D_T"], d7["K_lo_T"], d7["K_hi_T"]) == (5, 5, 0, 1, 4)
    assert d7["sold_by_deadline"] == 3 and d7["certified"] == 2
    for T_ in (3, 4, 6, 7):
        _, cfg_t, led_t, _, _ = _deadline_run(end_i=T_)
        assert monitor.o1_counts(led_t.lots, T_) == monitor.o1_counts(led.lots, T_), T_
        assert monitor.deadline_counts(led_t.lots, T_, cfg.deadline_extra) == monitor.deadline_counts(led.lots, T_, cfg.deadline_extra)
    assert monitor.lane(13, 3) == 1
    return {"o1_T4": c4, "deadline_T7": d7}


# ------------------------------------------------------------------ TODO-E6 (R3)
def test_R3_days_over_tolerance_are_listed_and_traced():
    """R3 has to be triggered to be tested: the track is fed a market that deliberately differs from
    the ledger's.
    (1) the track's market lacks a cash dividend that the ledger booked: the ex-date exceeds the daily
        tolerance, is LISTED, and is traced to that event -> explained.
    (2) the track's market has a different close on a day without any event: the day (and the next,
        whose overnight return starts from that close) exceed the tolerance with nothing to trace
        them to -> unexplained: R3 fails.
    (3) identical markets: no day over the tolerance."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), T(9.5, 9.6, 9.5), T(9.6, 9.7, 9.6), T(9.7, 9.7, 9.7)]
    ev = Event(SZ, "dist", ex_date=d("2016-03-04"), gross_cash=0.5, phi=1.0)
    m = panel(d("2016-03-01"), {SZ: rows}, [ev])
    led = led1(m)
    day(led, 0); day(led, 1, buys=[(SZ, 1000.0)])
    for i in range(2, 6):
        day(led, i)
    args = (1, 5, CFG.tol_R2_daily, CFG.tol_R2_cum, W0)
    ok = monitor.r2_report(ReturnTrack(m, Valuer(m), CFG), led, *args)
    assert ok["days_over_tolerance"] == [] and ok["pass_R2"] and ok["pass_R3"] and ok["R2_daily_rel"] < 1e-12
    m_no_ev = panel(d("2016-03-01"), {SZ: rows})
    r1 = monitor.r2_report(ReturnTrack(m_no_ev, Valuer(m_no_ev), CFG), led, *args)
    assert [x["i"] for x in r1["days_over_tolerance"]] == [3] and not r1["pass_R2"]
    assert close(r1["days_over_tolerance"][0]["diff"], -400.0, 1e-9)        # the track misses the net dividend
    assert r1["days_over_tolerance"][0]["explained"] and r1["pass_R3"] and r1["unexplained"] == []
    assert any("dist event" in c for c in r1["days_over_tolerance"][0]["traced_to"])
    rows_bad = list(rows)
    rows_bad[4] = T(9.6, 9.9, 9.6)                                          # a different close on day 4
    m_bad = panel(d("2016-03-01"), {SZ: rows_bad}, [ev])
    r2 = monitor.r2_report(ReturnTrack(m_bad, Valuer(m_bad), CFG), led, *args)
    assert [x["i"] for x in r2["days_over_tolerance"]] == [4, 5] and not r2["pass_R3"]
    assert [x["i"] for x in r2["unexplained"]] == [4, 5] and all(x["traced_to"] == [] for x in r2["unexplained"])
    return {"explained_day": r1["days_over_tolerance"][0]["date"], "explained_by": r1["days_over_tolerance"][0]["traced_to"],
            "unexplained_days": [x["date"] for x in r2["unexplained"]]}


TESTS = [test_reference_cost_close_instant_component, test_record_date_2015_09_08_two_readings,
         test_forced_class_U_event_label_U_ledger_as_URS,
         test_same_day_dividend_and_rights_record_date_in_suspension,
         test_cash_exit_no_sell_charge_liability_debited, test_sell_charges_exclude_cash_part,
         test_successor_event_on_succession_day_is_U, test_successor_event_after_succession_day_applies,
         test_lot_by_succession_and_direct_lot_then_cash_out_of_successor,
         test_rights_issue_with_missing_record_date, test_missing_row_inside_P1_carry_gives_M,
         test_filled_from_xsrc_flag_is_carried_through, test_disposition_table_absent_falls_back_to_write_off,
         test_disposition_share_exchange_with_carry, test_disposition_cash_other_terminated_and_errors,
         test_cash_return_overnight_only_intraday_zero, test_conventions_hash_in_result_records,
         test_deadline_labels_missing_record_gives_lower_0_upper_1, test_monitor_counts_and_truncation,
         test_R3_days_over_tolerance_are_listed_and_traced]

if __name__ == "__main__":
    run_tests("v07_rules", TESTS, "v07_rules.json")

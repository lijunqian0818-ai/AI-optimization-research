"""R4 stress cases on constructed panels (PLAN 3.9) plus O1-label cases (I-s3).

Every expected number is computed by hand in the comment next to it; none is produced by
the code under test.  Default cost rates: commission 0.00025, slippage 0.0005 per side.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date

import numpy as np
from common import N, NAN, S, T, X, close, panel, run_tests

from engine import simulate
from engine.attribution import ReturnTrack, lemma3, periods_from_track, reference_cost
from engine.config import EngineConfig
from engine.costs import trade_costs
from engine.labels import label_o1
from engine.ledger import Ledger
from engine.market import Event, Valuer

d = date.fromisoformat
CFG = EngineConfig()
SZ, SZ2, SH = "sz.000001", "sz.000002", "sh.600036"
W0 = 100000.0


def led1(m, cfg=CFG, **kw):
    return Ledger(m, cfg, n_sleeves=1, W0=kw.pop("W0", W0), **kw)


def day(led, i, buys=(), sells=()):
    led.begin_day(i)
    for lots in sells:
        led.book_sell(i, lots)
    out = [led.book_buy(i, c, 0, q) for c, q in buys]
    led.end_day(i)
    return out


def _div_rows():
    return [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), T(9.5, 9.6, 9.5), T(9.6, 9.6, 9.6), T(9.6, 9.6, 9.6)]


def _run_dividend(start, pay_offset=None):
    m = panel(d(start), {SZ: _div_rows()})
    m.add_event(Event(SZ, "dist", ex_date=m.days[3], gross_cash=0.5, phi=1.0,
                      pay_date=m.days[3 + pay_offset] if pay_offset else None))
    led = led1(m)
    day(led, 0)
    lot, = day(led, 1, buys=[(SZ, 1000.0)])
    day(led, 2)
    return m, led, lot


def test_dividend_no_trade_three_tax_regimes():
    """R4(a) + rule-calendar case: record date before 2013, 2013-2015-09-07, from 2015-09-08."""
    # buy 1000 @ 10.00: commission 2.5 + slippage 5 + transfer (SZ: 0.0255 per mille = 0.255 before
    # 2015-08-01; 0.02 per mille = 0.2 after) -> 7.755 / 7.7.   gross dividend 1000 x 0.5 = 500.
    # sale 1000 @ 9.60 = 9600: commission 2.4 + stamp 9.6 + slippage 4.8 + transfer 0.2448 / 0.192.
    cases = [  # start, record date, cash paid, liability, W_open(ex-date), final wealth
        ("2012-12-26", "2012-12-28", 450.0, 0.0, 99942.245, 100025.2002),    # tau 10%, withheld 10%
        ("2014-06-06", "2014-06-10", 475.0, 75.0, 99892.245, 99975.2002),    # tau 20%, withheld 5%
        ("2016-03-01", "2016-03-03", 500.0, 100.0, 99892.3, 99975.308),      # tau 20%, withheld 0
    ]
    out = {}
    for start, rec, paid, liab, w_open, w_final in cases:
        m, led, lot = _run_dividend(start)
        assert m.days[2] == d(rec)
        cash_before = led.cash[0]
        w2 = led.rec[2]["W_close"]
        led.begin_day(3)
        net = 500.0 - (500.0 - paid) - liab                                  # = q g (1 - tau)
        assert close(led.cash[0], cash_before + paid) and close(lot.tax_liability, liab)
        assert close(led.rec[3]["W_open"], w_open, 1e-12), (start, led.rec[3]["W_open"])
        # wealth identical to "net amount at the ex-date": W_open - W_close(2) = 1000*(9.5-10) + net
        assert close(led.rec[3]["W_open"] - w2, -500.0 + net, 1e-12)
        assert close(led.spendable(0), cash_before + paid - liab)
        led.end_day(3)
        assert led.rec[3]["trade"][SZ] == 0.0 and led.traded_amount(3) == 0.0 and led.rec[3]["cost"] == 0.0
        assert lot.q == 1000.0
        day(led, 4)
        day(led, 5, sells=[[lot]])
        assert lot.tax_liability == 0.0 and led.outstanding_liability() == 0.0
        assert close(led.rec[5]["W_close"], w_final, 1e-12), (start, led.rec[5]["W_close"])
        assert close(led.cash[0], w_final, 1e-12)
        out[rec] = {"W_open_ex": led.rec[3]["W_open"], "W_final": led.rec[5]["W_close"]}
    return out


def test_dividend_pay_date_after_ex_date():
    """Receivable until the pay date: wealth moves at the ex-date, spendable cash at the pay date."""
    m, led, lot = _run_dividend("2016-03-01", pay_offset=1)
    cash_before = led.cash[0]
    day(led, 3)
    assert close(led.cash[0], cash_before) and close(sum(r["amount"] for r in led.receivables), 500.0)
    assert close(led.rec[3]["W_open"], 99892.3, 1e-12)
    day(led, 4)
    assert close(led.cash[0], cash_before + 500.0) and led.receivables == []


def test_split_two_for_one_no_trade():
    """R4(b): share multiplier 2, price halves: q doubles, wealth unchanged, traded amount exactly 0."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), T(5.0, 5.1, 5.0), T(5.1, 5.1, 5.1)]
    m = panel(d("2016-03-01"), {SZ: rows}, [Event(SZ, "dist", ex_date=d("2016-03-04"), gross_cash=0.0, phi=2.0)])
    assert m.days[3] == d("2016-03-04")
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert lot.q == 2000.0
    assert led.rec[3]["W_open"] == led.rec[2]["W_close"]
    assert led.rec[3]["trade"][SZ] == 0.0 and led.rec[3]["cost"] == 0.0 and led.cash[0] == W0 - 10000.0 - 7.7


def test_pure_price_move_no_trade():
    """R4(c): unchanged position through a price move: traded amount 0 (not h_t - h_{t-1})."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10.5, 11.0, 10.0), T(11.0, 11.0, 11.0)]
    m = panel(d("2016-03-01"), {SZ: rows})
    led = led1(m)
    day(led, 0); day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert led.traded_amount(2) == 0.0 and led.traded_amount(3) == 0.0
    assert led.traded_amount(1) == 10000.0
    assert close(led.rec[3]["W_close"], W0 - 7.7 + 1000.0, 1e-12)


def test_every_cost_once():
    """Buy 1000 @ 10.00, sell @ 11.00 with non-zero slippage: wealth change = 1000 - 7.7 - 19.47."""
    # sell 11000: commission 2.75 + stamp 11 + transfer 0.22 + slippage 5.5 = 19.47
    rows = [T(10, 10, 10), T(10, 10, 10), T(10.5, 10.5, 10.0), T(11.0, 11.2, 10.5)]
    m = panel(d("2016-03-01"), {SZ: rows})
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3, sells=[[lot]])
    assert lot.entry_price == 10.0 and lot.exit_price == 11.0          # slippage never applied to a price
    assert close(lot.buy_cost, 7.7) and close(lot.sell_cost, 19.47)
    assert close(led.rec[3]["W_close"] - W0, 972.83, 1e-12), led.rec[3]["W_close"] - W0
    assert close(lot.realised_pnl, 972.83, 1e-12) and close(led.total_cost(), 27.17)
    slip = sum(t["costs"]["slippage"] for t in led.trades)
    assert close(slip, 5.0 + 5.5)


def test_cash_return_cost_debited_at_trade():
    """Lemma 3 round-3 counterexample: cash 100, cost 1 at the start, cash return 10% -> 108.9, not 109."""
    m = panel(d("2016-03-01"), {SZ: [T(10, 10, 10)]})
    led = led1(m, W0=100.0, rho_on=[0.0], rho_id=[0.10])
    led.begin_day(0); led.debit_cost(0, 0, 1.0); led.end_day(0)
    assert close(led.rec[0]["W_close"], 108.9, 1e-13), led.rec[0]["W_close"]
    # recursion: W_end - W_start = Pi + rho (W - c) = -1 + 0.1 * 99
    assert close(led.rec[0]["W_close"] - 100.0, -1.0 + 0.10 * (100.0 - 1.0), 1e-13)


def test_transfer_fee_sse_per_share_vs_szse():
    """Buy 1000 @ 10.00 on 2015-07-30: SSE 1000 x 0.000375 = 0.375; SZSE 10000 x 0.0000255 = 0.255."""
    assert close(trade_costs(d("2015-07-30"), SH, "buy", 1000.0, 10000.0, CFG)["transfer"], 0.375)
    assert close(trade_costs(d("2015-07-30"), SZ, "buy", 1000.0, 10000.0, CFG)["transfer"], 0.255)
    assert close(trade_costs(d("2015-08-03"), SH, "buy", 1000.0, 10000.0, CFG)["transfer"], 0.2)
    m = panel(d("2015-07-29"), {SH: [T(10, 10, 10)] * 3, SZ: [T(10, 10, 10)] * 3})
    assert m.days[1] == d("2015-07-30")
    led = led1(m)
    day(led, 0); a, b = day(led, 1, buys=[(SH, 1000.0), (SZ, 1000.0)])
    assert close(a.buy_cost, 2.5 + 5.0 + 0.375) and close(b.buy_cost, 2.5 + 5.0 + 0.255)


def test_stamp_duty_2023_08_25_vs_28():
    """Sell 1000 @ 10.00: stamp 10.00 on 2023-08-25, 5.00 on 2023-08-28."""
    out = []
    for start, sell_day, stamp in (("2023-08-23", "2023-08-25", 10.0), ("2023-08-24", "2023-08-28", 5.0)):
        m = panel(d(start), {SZ: [T(10, 10, 10)] * 3})
        assert m.days[2] == d(sell_day)
        led = led1(m)
        day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2, sells=[[lot]])
        got = led.trades[-1]["costs"]["stamp"]
        assert close(got, stamp), (sell_day, got)
        assert led.trades[0]["costs"]["stamp"] == 0.0
        out.append(got)
    return {"stamp": out}


def test_K2_no_trade_day_and_K3_missing_close():
    """K2: suspended day -> intraday return exactly 0, next overnight carries the move.
    K3: traded day with a missing close -> CV := OV, flagged and counted."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10.2, 10), S(10.2), T(10.8, 10.9, 10.2), T(10.9, NAN, 10.9), T(11, 11, 10.9)]
    m = panel(d("2016-03-01"), {SZ: rows})
    val = Valuer(m)
    led = led1(m, valuer=val)
    day(led, 0); day(led, 1, buys=[(SZ, 1000.0)])
    for i in range(2, 7):
        day(led, i)
    tr = ReturnTrack(m, val, CFG)
    assert tr.x_id(SZ, 3) == 0.0 and tr.x_on(SZ, 3) == 0.0             # P1 = last traded close 10.2
    assert close(tr.x_on(SZ, 4), 10.8 / 10.2 - 1.0, 1e-15)
    assert led.rec[3]["W_close"] == led.rec[2]["W_close"]
    assert val.cv(SZ, 5).branch == "K3" and val.cv(SZ, 5).value == 10.9 and val.counts["K3"] == 1
    assert tr.x_id(SZ, 5) == 0.0
    assert any(f[0] == 5 and "close missing" in f[2] for f in led.flags)
    assert val.ov(SZ, 3).branch == "P1" and val.cv(SZ, 3).branch == "K2"


def test_split_effective_on_a_suspended_day():
    """2-for-1 with ex-date inside a suspension: q doubles on the ex-date, P1 value halves, no trade."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), S(5.0), S(5.0), T(5.2, 5.2, 5.0)]
    m = panel(d("2016-03-01"), {SZ: rows}, [Event(SZ, "dist", ex_date=d("2016-03-04"), gross_cash=0.0, phi=2.0)])
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert lot.q == 2000.0 and led.val.ov(SZ, 3).value == 5.0 and led.val.ov(SZ, 3).branch == "P1"
    assert led.rec[3]["W_open"] == led.rec[2]["W_close"] and led.traded_amount(3) == 0.0
    day(led, 4); day(led, 5)
    assert close(led.rec[5]["W_open"] - led.rec[4]["W_close"], 2000.0 * (5.2 - 5.0))


def test_cv_is_immaterial_for_open_to_open_position():
    """Replacing every CV by an arbitrary positive number leaves the P&L of a position held from
    one open to a later open unchanged (ledger wealth after the sale and the track's total)."""
    rows = [T(10, 10, 10), T(10, 10.3, 10), T(10.1, 9.9, 10.3), T(4.9, 5.2, 4.95), T(5.3, 5.0, 5.2), T(5.1, 5.1, 5.0)]
    ev = [Event(SZ, "dist", ex_date=d("2016-03-04"), gross_cash=0.1, phi=2.0)]
    res = []
    for seed in (None, 1, 2, 3):
        m = panel(d("2016-03-01"), {SZ: rows}, ev)
        rng = np.random.default_rng(seed) if seed is not None else None
        cache = {}
        def ovr(code, i):
            return cache.setdefault((code, i), float(rng.uniform(0.5, 50.0)))
        val = Valuer(m, cv_override=ovr if rng is not None else None)
        led = led1(m, valuer=val)
        day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3); day(led, 4, sells=[[lot]]); day(led, 5)
        tr = ReturnTrack(m, val, CFG)
        tot = sum(tr.day(led, i)["dW_A"] for i in range(1, 6))
        res.append((led.rec[5]["W_close"], tot, led.rec[2]["W_close"]))
    base = res[0]
    for w, tot, mid in res[1:]:
        assert close(w, base[0], 1e-13) and close(tot, base[1], 1e-9), (w, tot, base)
        assert not close(mid, base[2], 1e-6)                  # daily marks do differ
    assert close(base[1], base[0] - W0, 1e-9)
    return {"pnl": base[0] - W0, "max_abs_diff_track_total": max(abs(t - base[1]) for _, t, _ in res)}


def _rights_market(p_r=9.29, missing=False):
    rows = [T(10.5, 10.56, 10.5), T(10.60, 10.70, 10.56), T(10.60, 10.66, 10.70)] + [S(10.66)] * 6 + \
           [T(10.70, 10.66, 10.46), T(10.63, 10.89, 10.66)]
    m = panel(d("2013-08-23"), {SH: rows})
    m.add_event(Event(SH, "rights", ex_date=m.days[9], record_date=m.days[2],
                      rights_price=None if missing else p_r, rights_ratio=0.174))
    return m


def test_rights_issue_P1R_ledger_and_label():
    """Mark day inside the payment-period suspension: convention P1-R of instantiation_ashare.md.
    m = min(10.66, (10.66 + 0.174 x 9.29) / 1.174) = 12.27646 / 1.174 = 10.456950596...
    (PLAN 3.9 R4 still says 'cum-rights P1'; the lead's instruction is that P1-R governs.)"""
    exp = (10.66 + 0.174 * 9.29) / 1.174
    assert abs(exp - 10.4569505963) < 1e-9
    m = _rights_market()
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SH, 1000.0)]); day(led, 2)
    cash = led.cash[0]
    for i in range(3, 11):
        day(led, i)
    for i in range(3, 9):
        v = led.val.ov(SH, i)
        assert v.branch == "P1R" and close(v.value, exp, 1e-14), (i, v)
        assert led.traded_amount(i) == 0.0
    assert lot.q == 1000.0 and led.cash[0] == cash and led.counts["S-c"] == 1      # not subscribed: nothing booked
    assert close(led.rec[3]["W_open"] - led.rec[2]["W_close"], 1000.0 * (exp - 10.66), 1e-12)
    assert led.val.ov(SH, 9).branch == "P23" and led.val.ov(SH, 9).value == 10.70   # after resumption: actual price
    lab = label_o1(m, Valuer(m), SH, 1, 1000.0, 10.60, lot.buy_cost, 4, CFG)        # mark day 5
    assert lab.outcome == "value" and lab.price_branch == "P1R" and close(lab.mark, exp, 1e-14)
    assert lab.events == ["S-c"] and lab.spell == 3 and lab.label == 1
    # subscription price at or above the carried close: the min keeps the close
    m2 = _rights_market(p_r=11.0)
    v = Valuer(m2).ov(SH, 5)
    assert v.branch == "P1R" and v.value == 10.66
    # terms missing from the snapshot: outcome M (label 1); the ledger carries the last value, flagged
    m3 = _rights_market(missing=True)
    lab3 = label_o1(m3, Valuer(m3), SH, 1, 1000.0, 10.60, lot.buy_cost, 4, CFG)
    assert (lab3.label, lab3.outcome) == (1, "M")
    led3 = led1(m3)
    day(led3, 0); day(led3, 1, buys=[(SH, 1000.0)]); day(led3, 2); day(led3, 3)
    assert led3.rec[3]["W_open"] == led3.rec[2]["W_close"] and any("missing" in f[2] for f in led3.flags)
    return {"P1R_mark": exp, "cum_rights_close": 10.66}


def test_P1_restatement_uses_gross_dividend():
    """Suspended across an ex-date: m = (10 - 0.5 gross) / 1.25 = 7.6; cash D gets the NET amount."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), S(7.6), S(7.6)]
    m = panel(d("2016-03-01"), {SZ: rows}, [Event(SZ, "dist", ex_date=d("2016-03-04"), gross_cash=0.5, phi=1.25)])
    v = Valuer(m).ov(SZ, 3)
    assert v.branch == "P1" and close(v.value, 7.6, 1e-15)
    lab = label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 2, CFG)
    assert lab.price_branch == "P1" and close(lab.cash, 400.0) and close(lab.shares, 1250.0) and lab.spell == 1
    assert lab.events == ["S-a", "S-b"]
    # net = 1250 x 7.6 + 400 - sell cost(9500: 2.375 + 9.5 + 0.19 + 4.75 = 16.815) = 9883.185 < 10007.7
    assert close(lab.net_proceeds, 9883.185, 1e-12) and lab.label == 1


def test_label_values_by_hand():
    """Buy 1000 @ 10.00 (basis 10007.7), H = 2, mark at the open of day 3."""
    def lab(open3, events=()):
        m = panel(d("2016-03-01"), {SZ: [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), T(open3, open3, 10.0)]}, events)
        return label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 2, CFG)
    a = lab(10.05)      # 10050 - (2.5125 + 10.05 + 0.201 + 5.025 = 17.7885) = 10032.2115 >= basis -> 0
    assert close(a.net_proceeds, 10032.2115, 1e-12) and close(a.cost_basis, 10007.7) and a.label == 0
    b = lab(10.02)      # 10020 - (2.505 + 10.02 + 0.2004 + 5.01 = 17.7354) = 10002.2646 < basis -> 1
    assert close(b.net_proceeds, 10002.2646, 1e-12) and b.label == 1 and b.price_branch == "P23"
    ev = [Event(SZ, "dist", ex_date=d("2016-03-04"), gross_cash=0.5, phi=1.0)]
    c = lab(9.55, ev)   # 9550 - (2.3875 + 9.55 + 0.191 + 4.775 = 16.9035) + 400 = 9933.0965 -> 1
    assert close(c.net_proceeds, 9933.0965, 1e-12) and c.label == 1 and c.events == ["S-a"]
    e = lab(9.65, ev)   # 9650 - (2.4125 + 9.65 + 0.193 + 4.825 = 17.0805) + 400 = 10032.9195 -> 0
    assert close(e.net_proceeds, 10032.9195, 1e-12) and e.label == 0


def test_label_branches_P4_U_M_Sd_Se():
    base = [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10)]
    def lab(rows, events=(), H=2, **kw):
        m = panel(d("2016-03-01"), rows, events, **kw)
        return label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, H, CFG)
    p4 = lab({SZ: base + [N(9.9)]})
    assert p4.price_branch == "P4" and p4.mark == 9.9 and p4.outcome == "value" and p4.label == 1
    assert (lab({SZ: base + [X()]}).outcome, lab({SZ: base + [X()]}).label) == ("M", 1)
    u = lab({SZ: base + [X()]}, delist={SZ: 3})
    assert (u.outcome, u.label) == ("U", 1)
    u2 = lab({SZ: base + [T(12, 12, 10)]}, [Event(SZ, "unsupported", ex_date=d("2016-03-04"))])
    assert (u2.outcome, u2.label) == ("U", 1)                           # price rose, still a recorded loss
    u3 = lab({SZ: base + [T(12, 12, 10)]}, urs={(SZ, d("2016-03-03"))})
    assert (u3.outcome, u3.label) == ("U", 1)
    mm = lab({SZ: base + [T(12, 12, 10)]}, [Event(SZ, "dist", ex_date=d("2016-03-04"), gross_cash=NAN, phi=1.0)])
    assert (mm.outcome, mm.label) == ("M", 1)
    sd = lab({SZ: base + [X()]}, [Event(SZ, "cashout", ex_date=d("2016-03-04"), cash_per_share=10.5)], delist={SZ: 3})
    assert sd.outcome == "value" and sd.price_branch == "cash" and close(sd.net_proceeds, 10500.0) and sd.label == 0
    rows = {SZ: base + [X(), X()], SZ2: [T(20, 20, 20)] * 3 + [T(21.0, 21, 20), T(21, 21, 21)]}
    ex1 = Event(SZ, "exchange", ex_date=d("2016-03-04"), successor=SZ2, ratio=0.5)
    se = lab(rows, [ex1], delist={SZ: 3})
    # 500 x 21 = 10500 - (2.625 + 10.5 + 0.21 + 5.25 = 18.585) = 10481.415
    assert se.events == ["S-e"] and se.shares == 500.0 and close(se.net_proceeds, 10481.415, 1e-12) and se.label == 0
    se2 = lab(rows, [ex1, Event(SZ2, "cashout", ex_date=d("2016-03-07"), cash_per_share=30.0)], H=3, delist={SZ: 3})
    assert (se2.outcome, se2.label) == ("U", 1)                         # S-d of a successor is class U


def test_ledger_delisting_U_cashout_exchange():
    """Ledger side of U / S-d / S-e: write-off at the U33 value, cash-out and succession are not trades."""
    base = [T(10, 10, 10), T(10, 10, 10), T(10, 10.4, 10)]
    # (1) delisted on day 3 without S-d / S-e: written off at 0
    m = panel(d("2016-03-01"), {SZ: base + [X()], SZ2: [T(20, 20, 20)] * 4}, delist={SZ: 3})
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert lot.status == "written_off" and lot.label_o2 == 1 and led.counts["U"] == 1
    assert close(led.rec[3]["W_open"], W0 - 10000.0 - 7.7) and led.traded_amount(3) == 0.0 and led.rec[3]["cost"] == 0.0
    # sensitivity: last traded price kept (factor 1.0)
    led = led1(m, cfg=replace(CFG, terminal_value_U=1.0))
    day(led, 0); day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert close(led.rec[3]["W_open"], W0 - 10000.0 - 7.7 + 10400.0)
    # (2) S-d: cash-out at 10.5 per share, no trade, no cost
    m = panel(d("2016-03-01"), {SZ: base + [X()], SZ2: [T(20, 20, 20)] * 4},
              [Event(SZ, "cashout", ex_date=d("2016-03-04"), cash_per_share=10.5)], delist={SZ: 3})
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert lot.status == "cashed_out" and close(led.cash[0], W0 - 10007.7 + 10500.0) and led.rec[3]["cost"] == 0.0
    assert lot.label_o2 == 0 and led.traded_amount(3) == 0.0
    # (3) S-e into SZ2 at 0.5, then a second succession of SZ2 -> class U for that lot
    rows = {SZ: base + [X(), X()], SZ2: [T(20, 20, 20)] * 3 + [T(21.0, 21.5, 20), X()], SH: [T(5, 5, 5)] * 5}
    evs = [Event(SZ, "exchange", ex_date=d("2016-03-04"), successor=SZ2, ratio=0.5),
           Event(SZ2, "exchange", ex_date=d("2016-03-07"), successor=SH, ratio=2.0)]
    m = panel(d("2016-03-01"), rows, evs, delist={SZ: 3, SZ2: 4})
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert lot.code == SZ2 and lot.q == 500.0 and lot.status == "open" and led.traded_amount(3) == 0.0
    assert close(led.rec[3]["W_open"], W0 - 10007.7 + 500.0 * 21.0)
    day(led, 4)
    assert lot.status == "written_off" and led.counts == {"S-a": 0, "S-b": 0, "S-c": 0, "S-d": 0, "S-e": 1, "U": 1}
    # (4) URS name: label U, but the ledger keeps valuing it at market prices
    m = panel(d("2016-03-01"), {SZ: base + [T(12, 12, 10.4)]}, urs={(SZ, d("2016-03-03"))})
    led = led1(m)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert lot.status == "open" and close(led.rec[3]["W_close"], W0 - 10007.7 + 12000.0)


def test_suspension_spanning_exit_and_long_spell():
    """Scheduled exit inside a suspension: O1 marks by P1 (spell length reported), LP retries the sale.

    Capacity cap after a long suspension (PLAN 3.7 / 3.9 R4, v0.7 E-5).
    PRIMARY definition (ADV over the 20 most recent TRADED days): on the resumption day (33) the
    window holds the traded days 0, 1, 2 (1e9 each), the cap is 1e7 and the sale is filled on day 33.
    Sensitivity 'cap-zero' (the v0.6 wording read literally; this was the primary expectation of the
    v0.6 version of this test and is kept as the sensitivity branch): the 20 market days ending t-1
    all lie inside the suspension, ADV = 0, cap = 0, the sale is NOT filled on day 33 (S3) and fills
    on day 34, when the window holds one traded day (cap = 1% x 1e9 / 20 = 5e5)."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 9.9, 10)] + [S(9.9)] * 30 + [T(9.0, 9.0, 9.9), T(9, 9, 9)]
    m = panel(d("2016-03-01"), {SZ: rows})
    cfg = replace(CFG, H=2, K=1, W0=3.0e5)
    led, orders = simulate.run(m, cfg, {1: [(SZ, 1.0)]}, 1, 34)
    lot = led.lots[0]
    sells = [o for o in orders if o["side"] == "sell"]
    assert [o["reason"] for o in sells[:30]] == ["S1"] * 30
    assert [(o["i"], o["filled"], o["reason"]) for o in sells[30:]] == [(33, True, "filled")]
    assert lot.exit_i == 33 and lot.exit_price == 9.0
    assert sells[30]["adv_days"] == 3 and sells[30]["adv_reach"] == 32 and sells[30]["stale_cap"] is False
    cz = replace(cfg, adv_counts_nontraded_days_as_zero=True)
    led_z, orders_z = simulate.run(m, cz, {1: [(SZ, 1.0)]}, 1, 34)
    sells_z = [o for o in orders_z if o["side"] == "sell"]
    assert [(o["i"], o["filled"], o["reason"]) for o in sells_z[30:]] == [(33, False, "S3"), (34, True, "filled")]
    assert led_z.lots[0].exit_i == 34 and led_z.lots[0].exit_price == 9.0
    led_l, orders_l = simulate.run(m, cz, {1: [(SZ, 1.0)]}, 1, 34, rule="SF-loose")
    assert led_l.lots[0].exit_i == 33                              # under cap-zero the cap is what delays the exit
    assert lot.label_o1.price_branch == "P1" and lot.label_o1.mark == 9.9 and lot.label_o1.spell == 1
    assert lot.label_o1.label == 1 and lot.label_o2 == 1
    lab = label_o1(m, Valuer(m), SZ, 1, 1000.0, 10.0, 7.7, 25, CFG)        # mark on day 26: spell of 24 days
    assert lab.price_branch == "P1" and lab.spell == 24 and lab.mark == 9.9


def test_label_frozen_and_reads_nothing_after_mark_day():
    """The label of an entry of day t is set at begin_day(t+H+1), never recomputed, and equals the label
    computed from a panel truncated after day t+H."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), T(10.05, 10.0, 10.0), T(9.0, 9.0, 10.0), T(8, 8, 9), T(8, 8, 8)]
    m = panel(d("2016-03-01"), {SZ: rows})
    cfg = replace(CFG, H=2)
    led = led1(m, cfg=cfg)
    day(led, 0); lot, = day(led, 1, buys=[(SZ, 1000.0)]); day(led, 2); day(led, 3)
    assert lot.label_o1 is None                                   # day t+H: not yet revealed
    day(led, 4)
    first = lot.label_o1
    assert first is not None and first.label == 0
    m.secs[SZ].open[3] = 1.0                                      # a later "revision" of the mark-day open
    led.val._ov.clear()
    day(led, 5); day(led, 6)
    assert lot.label_o1 is first and lot.label_o1.label == 0      # never recomputed
    trunc = panel(d("2016-03-01"), {SZ: rows[:4] + [X(), X(), X()]})
    again = label_o1(trunc, Valuer(trunc), SZ, 1, 1000.0, 10.0, 7.7, 2, cfg)
    assert (again.label, again.net_proceeds, again.price_branch) == (first.label, first.net_proceeds, first.price_branch)


def _two_strategy():
    A, C = SZ, SZ2
    rows = {A: [T(10, 10, 10), T(10, 10.2, 10), T(10.3, 10.1, 10.2), T(10.0, 10.4, 10.1), T(10.5, 10.6, 10.4),
                T(10.6, 10.5, 10.6), T(10.4, 10.4, 10.5)],
            C: [T(20, 20, 20), T(20, 19.8, 20), T(19.9, 20.3, 19.8), T(20.4, 20.2, 20.3), T(20.1, 20.0, 20.2),
                T(20.0, 20.5, 20.0), T(20.6, 20.6, 20.5)]}
    m = panel(d("2016-03-01"), rows)
    cfg = replace(CFG, H=2, K=2, W0=6.0e5)
    # G's second lot is bought on day 5 (due day 7, beyond the window) so that G has a lot open at the end
    G, _ = simulate.run(m, cfg, {1: [(A, 1.0), (C, 0.5)], 5: [(C, 1.0)]}, 1, 6, name="G")
    B, _ = simulate.run(m, cfg, {3: [(A, 1.0)], 5: [(A, 1.0)]}, 1, 6, name="B")
    return m, cfg, G, B, A, C


def test_two_strategies_same_name_entry_exit_same_day_and_zero_baseline():
    """G sells A on day 3 while B buys A on day 3; C is held by G only; B has zero exposure on days 1-2;
    lots open at the window end.  R1 (identity) for three fallback conventions; R2 (track vs ledger)."""
    m, cfg, G, B, A, C = _two_strategy()
    assert any(t["i"] == 3 and t["side"] == "sell" and t["code"] == A for t in G.trades)
    assert any(t["i"] == 3 and t["side"] == "buy" and t["code"] == A for t in B.trades)
    assert G.open_lots() and B.open_lots()
    tr = ReturnTrack(m, G.val, cfg)
    dG = [tr.day(G, i) for i in range(1, 7)]
    dB = [tr.day(B, i) for i in range(1, 7)]
    r2 = 0.0
    for led, days_ in ((G, dG), (B, dB)):
        for x in days_:
            i = x["i"]
            r2 = max(r2, abs(x["dW_A"] - (led.rec[i]["W_close"] - led.rec[i]["W_prev_close"])))
    assert r2 <= 1e-6, r2
    pG, cG = periods_from_track(dG)
    pB, cB = periods_from_track(dB)
    xs = {(k, i): {A: (tr.x_on(A, i) if k == "on" else tr.x_id(A, i)),
                   C: (tr.x_on(C, i) if k == "on" else tr.x_id(C, i))} for k in ("on", "id") for i in range(1, 7)}
    def with_x(periods):                     # give every period the full return vector (for fallback names)
        return [(k, i, h, xs[(k, i)]) for k, i, h, _ in periods]
    pG, pB = with_x(pG), with_x(pB)
    out = {}
    for name, fb in (("zero", None), ("A", lambda k, i: {A: 1.0}), ("A+C", lambda k, i: {A: 0.5, C: 0.5})):
        r = lemma3(pG, pB, cG, cB, fb)
        assert abs(r["residual"]) <= 1e-10 * cfg.W0 and abs(r["residual_alt"]) <= 1e-10 * cfg.W0, (name, r["residual"])
        assert r["zero_baseline_intervals"]["id"] >= 2 and r["max_return_mismatch"] == 0.0
        out[name] = (r["exposure"], r["composition"], r["cost"], r["residual"])
    assert abs(out["zero"][0] - out["A"][0]) > 1e-6          # the split depends on the convention ...
    assert close(out["zero"][0] + out["zero"][1], out["A"][0] + out["A"][1], 1e-9)   # ... the sum does not
    wealth_diff = (G.rec[6]["W_close"] - cfg.W0) - (B.rec[6]["W_close"] - cfg.W0)
    r = lemma3(pG, pB, cG, cB, None)
    assert abs(r["diff"] - wealth_diff) <= 1e-6
    return {"max_R2_daily_abs": r2, "residuals": {k: v[3] for k, v in out.items()},
            "terms_minus_wealth_diff": r["sum_terms"] - wealth_diff}


def test_reference_path_no_trade_on_dividend_and_split():
    """R4 (a), (b) with the tolerances of PLAN 3.9 as amended in v0.7 (E-8):
      * real strategy (shares): traded amount and cost on the no-trade days are BITWISE zero;
      * reference path h^E = e^G w^B (defined in yuan, converted to shares), here with G = B holding
        one unchanged lot across a dividend and a 2-for-1 split: |traded amount| <= 1e-10 x W_0, the
        tolerance of R1 (cfg.tol_R1).
    Also E-7 (a): with identical holdings of G and B the reference path equals the strategy, so after
    the entry both cost components are zero to that tolerance: C_E_close ~ 0 and C_E_open = the cost of
    the entry trade only (10,000 x 0.00077 = 7.7)."""
    REFERENCE_TOL = CFG.tol_R1 * W0            # 1e-10 x W_0 (R1), explicit
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10.2, 10), T(9.8, 9.9, 9.7), T(4.95, 5.0, 4.95), T(5.0, 5.1, 5.0)]
    evs = [Event(SZ, "dist", ex_date=d("2016-03-04"), gross_cash=0.5, phi=1.0),
           Event(SZ, "dist", ex_date=d("2016-03-07"), gross_cash=0.0, phi=2.0)]
    m = panel(d("2016-03-01"), {SZ: rows}, evs)
    led = led1(m)
    day(led, 0); day(led, 1, buys=[(SZ, 1000.0)])
    for i in range(2, 6):
        day(led, i)
    for i in range(2, 6):                      # real strategy: bitwise zero
        assert led.net_traded_amount(i) == 0.0 and led.order_turnover(i) == 0.0 and led.rec[i]["cost"] == 0.0
        assert all(v == 0.0 for v in led.rec[i]["trade"].values())
    tr = ReturnTrack(m, led.val, CFG)
    days_ = [tr.day(led, i) for i in range(1, 6)]
    p, _ = periods_from_track(days_)
    rcost = reference_cost(tr, p, p)
    later = {k: v for k, v in rcost["by_instant"].items() if k != (1, "open")}
    worst = max(later.values(), default=0.0)
    assert close(rcost["by_instant"][(1, "open")], 10000.0, 1e-12)
    assert worst <= REFERENCE_TOL, later       # reference path: <= 1e-10 x W_0
    assert rcost["C_E_close"] <= REFERENCE_TOL and abs(rcost["C_E_open"] - 7.7) <= REFERENCE_TOL
    assert rcost["C_E"] == rcost["C_E_open"] + rcost["C_E_close"]
    return {"max_reference_trade_after_entry": worst, "tolerance": REFERENCE_TOL,
            "C_E_open": rcost["C_E_open"], "C_E_close": rcost["C_E_close"],
            "note": "reference path: zero to 1e-10 x W_0, not bit-exact; real strategy: bitwise zero"}


TESTS = [test_dividend_no_trade_three_tax_regimes, test_dividend_pay_date_after_ex_date,
         test_split_two_for_one_no_trade, test_pure_price_move_no_trade, test_every_cost_once,
         test_cash_return_cost_debited_at_trade, test_transfer_fee_sse_per_share_vs_szse,
         test_stamp_duty_2023_08_25_vs_28, test_K2_no_trade_day_and_K3_missing_close,
         test_split_effective_on_a_suspended_day, test_cv_is_immaterial_for_open_to_open_position,
         test_rights_issue_P1R_ledger_and_label, test_P1_restatement_uses_gross_dividend,
         test_label_values_by_hand, test_label_branches_P4_U_M_Sd_Se, test_ledger_delisting_U_cashout_exchange,
         test_suspension_spanning_exit_and_long_spell, test_label_frozen_and_reads_nothing_after_mark_day,
         test_two_strategies_same_name_entry_exit_same_day_and_zero_baseline,
         test_reference_path_no_trade_on_dividend_and_split]

if __name__ == "__main__":
    run_tests("ledger_r4", TESTS, "ledger_r4.json")

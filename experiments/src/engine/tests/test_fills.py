"""SF / SF-strict / SF-loose on constructed scenarios; unfilled-remainder handling; lots.
Expected outcomes are written by hand from PLAN 3.2 / 3.4 / 3.7."""
from __future__ import annotations

from dataclasses import replace
from datetime import date

import numpy as np
from common import N, NAN, S, T, X, panel, run_tests

from engine import fills, simulate
from engine.config import EngineConfig

d = date.fromisoformat
CFG = EngineConfig()
SH = "sh.600001"


def _one(open_, day_row=None, amt_hist=1e9, code=SH, pc=10.0, start="2021-03-01", st=False):
    """Two-day panel: day 0 history (ADV), day 1 the order day with reference price `pc`."""
    row = day_row if day_row is not None else T(open_, open_, pc, st=st)
    return panel(d(start), {code: [T(pc, pc, pc, amt=amt_hist, st=st), row]})


def _dec(m, side, value, rule, code=SH, i=1, cfg=CFG):
    oi = fills.order_inputs(m, code, i, cfg)
    return fills.decide(m, code, i, side, value, oi, cfg, rule)


def _all(m, side, value, **kw):
    return tuple(_dec(m, side, value, r, **kw) for r in fills.RULES)


F = (True, "filled")


def test_buy_inside_band_filled_by_all():
    assert _all(_one(10.50), "buy", 1000.0) == (F, F, F)


def test_buy_open_at_limit_up():
    """Open = P_up (11.00): SF not filled (S2), SF-strict not filled, SF-loose filled."""
    assert _all(_one(11.00), "buy", 1000.0) == ((False, "S2"), (False, "S2"), F)


def test_buy_strict_band_threshold():
    """SF-strict: open <= ref x (1 + 0.8 x 10%) = 10.80."""
    assert _all(_one(10.80), "buy", 1000.0) == (F, F, F)
    assert _all(_one(10.81), "buy", 1000.0) == (F, (False, "S2"), F)
    assert _all(_one(10.99), "buy", 1000.0) == (F, (False, "S2"), F)


def test_buy_open_above_computed_limit():
    """No-limit day / wrong preclose: open 11.20 > P_up 11.00 -> not filled under all three rules."""
    assert _all(_one(11.20), "buy", 1000.0) == ((False, "S2"), (False, "S2"), (False, "S2"))


def test_s1_cases():
    """Suspended row; flagged trading with zero volume; no row; flagged suspended WITH volume: all S1."""
    for row in (S(10.0), N(10.0), X()):
        assert _all(_one(None, day_row=row), "buy", 1000.0) == ((False, "S1"),) * 3, row
        assert _all(_one(None, day_row=row), "sell", 1000.0) == ((False, "S1"),) * 3, row
    m = _one(10.5)
    m.secs[SH].flag_trading[1] = False          # inconsistent row: suspended flag but volume > 0
    assert _all(m, "buy", 1000.0) == ((False, "S1"),) * 3
    md = _one(10.5)
    md.secs[SH].delist_i = 1
    assert _all(md, "buy", 1000.0) == ((False, "S1"),) * 3


def test_capacity_cap():
    """ADV20 = 1e6 -> cap 1e4 (SF), 1e3 (SF-strict), none (SF-loose)."""
    m = _one(10.5, amt_hist=1e6)
    oi = fills.order_inputs(m, SH, 1, CFG)
    assert abs(oi.cap_value - 1e4) < 1e-9 and oi.adv_days_used == 1
    assert _all(m, "buy", 9000.0) == (F, (False, "S3"), F)
    assert _all(m, "buy", 10000.0) == (F, (False, "S3"), F)          # equal to the cap: allowed
    assert _all(m, "buy", 10000.01) == ((False, "S3"), (False, "S3"), F)
    assert _all(m, "buy", 999.0) == (F, F, F)
    assert _all(m, "sell", 20000.0) == ((False, "S3"), (False, "S3"), F)


def test_adv_window_uses_days_before_t_only():
    """ADV_t (PLAN 3.7, v0.7 E-5): the 20 most recent TRADED days dated <= t-1; days without a trade
    are skipped.  Sensitivity 'cap-zero': the 20 market days ending t-1, non-traded days as zero
    (this was the primary expectation of the v0.6 test; kept as the sensitivity branch)."""
    rows = [T(10, 10, 10, amt=2e6)] * 10 + [S(10.0)] * 10 + [T(10, 10, 10, amt=2e6)] * 5 + [T(10.5, 10.5, 10, amt=7e12)]
    m = panel(d("2021-03-01"), {SH: rows})
    a, n, reach = fills.adv(m, SH, 25, CFG)     # traded days before 25: 0..9 and 20..24 = 15 days (< 20)
    assert n == 15 and abs(a - 2e6) < 1e-6 and reach == 24, (a, n, reach)
    cz = replace(CFG, adv_counts_nontraded_days_as_zero=True)
    a2, n2, reach2 = fills.adv(m, SH, 25, cz)   # days 5..24: 5 traded + 10 suspended + 5 traded
    assert n2 == 20 and abs(a2 - (10 * 2e6) / 20) < 1e-6 and reach2 == 19, (a2, n2, reach2)
    # the day-t amount (7e12) must not enter the day-t cap
    assert abs(fills.order_inputs(m, SH, 25, CFG).cap_value - 0.01 * 2e6) < 1e-6
    assert abs(fills.order_inputs(m, SH, 25, cz).cap_value - 0.01 * 1e6) < 1e-6
    assert CFG.adv_counts_nontraded_days_as_zero is False            # the primary definition is the default


def test_adv_window_with_suspended_days_inside():
    """(b) 5 suspended days inside the window: ADV = mean of the 20 traded days (by hand).
    Traded days before day 35: 0..9 (1e6), 10..21 (3e6), 27..34 (5e6); days 22..26 suspended.
    The 20 most recent: 8 x 5e6 + 12 x 3e6 = 76e6 -> 3.8e6; earliest window day = 10, reach = 34 - 10."""
    rows = ([T(10, 10, 10, amt=1e6)] * 10 + [T(10, 10, 10, amt=3e6)] * 12 + [S(10.0)] * 5
            + [T(10, 10, 10, amt=5e6)] * 8 + [T(10, 10, 10, amt=9e9)])
    m = panel(d("2021-03-01"), {SH: rows})
    a, n, reach = fills.adv(m, SH, 35, CFG)
    assert n == 20 and abs(a - 3.8e6) < 1e-6 and reach == 24, (a, n, reach)
    a2, n2, _ = fills.adv(m, SH, 35, replace(CFG, adv_counts_nontraded_days_as_zero=True))
    assert n2 == 20 and abs(a2 - (8 * 5e6 + 7 * 3e6) / 20) < 1e-6          # days 15..34: 7 + 5 susp + 8


def test_adv_fewer_than_20_traded_days_and_none():
    """(c) listed for 3 traded days: mean of those that exist (2e6, 4e6, 9e6 -> 5e6); none: cap 0."""
    rows = [X(), X(), T(10, 10, 10, amt=2e6), T(10, 10, 10, amt=4e6), N(10.0), T(10, 10, 10, amt=9e6), T(10, 10, 10)]
    m = panel(d("2021-03-01"), {SH: rows})
    a, n, reach = fills.adv(m, SH, 6, CFG)
    assert n == 3 and abs(a - 5e6) < 1e-6 and reach == 3, (a, n, reach)
    assert fills.adv(m, SH, 2, CFG) == (0.0, 0, 0) and fills.adv(m, SH, 0, CFG) == (0.0, 0, 0)
    oi = fills.order_inputs(m, SH, 2, CFG)
    assert oi.cap_value == 0.0
    assert fills.decide(m, SH, 2, "buy", 1.0, oi, CFG, "SF") == (False, "S3")       # no history: cap 0
    assert fills.decide(m, SH, 2, "buy", 1.0, oi, CFG, "SF-loose") == F


def test_sell_order_value_uses_day_t_preclose_on_ex_date():
    """(d) sell on the ex-date of a 2-for-1 split: order value = quantity AFTER the split x the day's
    `preclose` (5.00), not x the previous close (10.00).  q0 = 1e5 / (11 x 1.00077); value = 2 q0 x 5.
    With ADV = 1.2e7 the cap is 1.2e5: the correct value (~9.08e4) passes, the previous-close value
    (~1.82e5) would not."""
    from engine.market import Event
    rows = [T(10, 10, 10, amt=1.2e7)] * 3 + [T(5.0, 5.0, 5.0, amt=1.2e7), T(5, 5, 5, amt=1.2e7)]
    m = panel(d("2021-03-01"), {SH: rows}, [Event(SH, "dist", ex_date=d("2021-03-04"), gross_cash=0.0, phi=2.0)])
    led, orders = simulate.run(m, _sim_cfg(), {1: [(SH, 1.0)]}, 1, 4)
    q0 = 1e5 / (11.0 * 1.00077)
    sell = [o for o in orders if o["side"] == "sell"][0]
    assert sell["i"] == 3 and abs(sell["q"] - 2 * q0) < 1e-6
    assert abs(sell["value"] - 2 * q0 * 5.0) < 1e-6 and sell["value"] < 1.2e5 < 2 * q0 * 10.0
    assert sell["filled"] and led.lots[0].exit_i == 3


def test_stale_cap_fill_is_counted():
    """(e) a fill whose ADV window reaches back more than 60 market days is a 'stale-cap fill' (U59).
    Buy day 1; suspended days 3..72; resumption day 73: traded days before 73 are 0, 1, 2 ->
    reach = 72 - 0 = 72 > 60.  Under 'cap-zero' the cap is 0 on day 73 and the sale waits a day."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10)] + [S(10.0)] * 70 + [T(9.5, 9.5, 10.0), T(9.5, 9.5, 9.5)]
    m = panel(d("2021-03-01"), {SH: rows})
    led, orders = simulate.run(m, _sim_cfg(), {1: [(SH, 1.0)]}, 1, 74)
    filled = [o for o in orders if o["side"] == "sell" and o["filled"]]
    assert len(filled) == 1 and filled[0]["i"] == 73 and filled[0]["adv_reach"] == 72 and filled[0]["stale_cap"] is True
    assert simulate.order_summary(orders)["total"]["stale_cap_fills"] == 1
    buy = [o for o in orders if o["side"] == "buy"][0]
    assert buy["stale_cap"] is False and buy["adv_reach"] == 0
    led2, orders2 = simulate.run(m, _sim_cfg(adv_counts_nontraded_days_as_zero=True), {1: [(SH, 1.0)]}, 1, 74)
    s2 = [(o["i"], o["filled"], o["reason"]) for o in orders2 if o["side"] == "sell"][-2:]
    assert s2 == [(73, False, "S3"), (74, True, "filled")], s2


def test_sf_strict_fills_are_a_subset_of_sf_fills():
    """E-6: property test on random bars (incl. reference prices below 0.10 yuan, opens off the tick
    grid, opens beyond the limits): SF-strict filled  =>  SF filled, for buys and for sells."""
    rng = np.random.default_rng(20261115)
    n_checked = n_strict = n_sf = 0
    for trial in range(400):
        code = ["sh.600001", "sz.300001", "sh.688001", "sz.000002"][trial % 4]
        pc = float(np.round(rng.choice([rng.uniform(0.01, 0.12), rng.uniform(0.1, 3), rng.uniform(3, 200)]), 2))
        pc = max(pc, 0.01)
        st = bool(rng.random() < 0.3) and not code.startswith("sh.688")
        rows = [T(pc, pc, pc, amt=float(10 ** rng.uniform(3, 9)))]
        for _ in range(12):
            o = pc * (1 + rng.uniform(-0.25, 0.25))
            o = float(np.round(o, 2)) if rng.random() < 0.7 else float(o)
            rows.append(T(max(o, 0.001), pc, pc, amt=1e6, st=st))
        m = panel(d("2021-03-01"), {code: rows})
        for i in range(1, 13):
            oi = fills.order_inputs(m, code, i, CFG)
            for side in ("buy", "sell"):
                for value in (10.0, 1e3, 1e5):
                    a = fills.decide(m, code, i, side, value, oi, CFG, "SF")[0]
                    b = fills.decide(m, code, i, side, value, oi, CFG, "SF-strict")[0]
                    n_checked += 1
                    n_sf += a
                    n_strict += b
                    assert (not b) or a, (code, pc, m.secs[code].open[i], side, value)
    assert n_strict > 0 and n_sf > n_strict
    return {"decisions": n_checked, "SF_fills": int(n_sf), "SF_strict_fills": int(n_strict)}


def test_sf_strict_reference_price_below_ten_cents():
    """E-6 boundary: reference 0.05, band 10%: P_up = 0.06, P_down = 0.04 (+-0.01 rule); the strict
    thresholds 0.05 x 1.08 = 0.054 and 0.05 x 0.92 = 0.046 are compared exactly and are not rounded."""
    assert _all(_one(0.05, pc=0.05), "buy", 1.0) == (F, F, F)
    assert _all(_one(0.06, pc=0.05), "buy", 1.0) == ((False, "S2"), (False, "S2"), F)
    assert _all(_one(0.05, pc=0.05), "sell", 1.0) == (F, F, F)
    assert _all(_one(0.04, pc=0.05), "sell", 1.0) == ((False, "S2"), (False, "S2"), F)
    assert _all(_one(0.054, pc=0.05), "buy", 1.0) == (F, F, F)             # exactly at the unrounded threshold
    assert _all(_one(0.0541, pc=0.05), "buy", 1.0) == (F, (False, "S2"), F)
    assert _all(_one(0.046, pc=0.05), "sell", 1.0) == (F, F, F)
    assert _all(_one(0.0459, pc=0.05), "sell", 1.0) == (F, (False, "S2"), F)


def test_no_ref_is_not_part_of_S_t():
    """E-17: no row (or no reference price) on the order day -> no order, reason 'no_ref', outside S_t;
    the slot cash stays in the sleeve."""
    rows = {SH: [T(10, 10, 10), X(), T(10, 10, 10)], "sh.600002": [T(10, 10, 10), T(10.5, 10.5, 10.0), T(10, 10, 10)],
            "sh.600003": [T(10, 10, 10), T(10, 10, NAN), T(10, 10, 10)]}
    m = panel(d("2021-03-01"), rows)
    cfg = replace(CFG, H=2, K=3, W0=9.0e5)                 # 3 sleeves of 3e5, 3 slots of 1e5
    led, orders = simulate.run(m, cfg, {1: [(SH, 1.0), ("sh.600002", 1.0), ("sh.600003", 1.0)]}, 1, 2)
    by = {o["code"]: o for o in orders}
    assert by[SH]["reason"] == "no_ref" and by[SH]["submitted"] is False and by[SH]["q"] == 0.0
    assert by["sh.600003"]["reason"] == "no_ref" and by["sh.600003"]["submitted"] is False
    assert by["sh.600002"]["submitted"] is True and by["sh.600002"]["filled"]
    s = simulate.order_summary(orders)
    assert s["by_day"][1]["S"] == 1 and s["by_day"][1]["n"] == 1 and s["by_day"][1]["unsubmitted"] == {"no_ref": 2}
    assert s["total"]["S"] == 1 and s["total"]["unsubmitted"] == {"no_ref": 2}
    lot = led.lots[0]
    spent = lot.cost_basis
    assert abs(led.cash[1] - (3e5 - spent)) < 1e-9 and spent < 1e5 + 1e-9        # two slots untouched
    assert len(led.lots) == 1


def _mc_cfg(slot, **kw):
    return replace(CFG, H=2, K=1, W0=3.0 * slot, min_commission=5.0, **kw)


def test_min_commission_binding_and_not_binding():
    """E-4: q = (slot - 5) / (P_up (1 + kappa) + f); commission = max(rate x value, 5), once per order.
    P_up = 11.00, kappa = 0.00025 + 0.0005 + 0.00002 = 0.00077, open 10.50.
    (i)  slot 5,005: q = 5000 / 11.00847 = 454.1957...; value = q x 10.5 = 4769.05...;
         0.00025 x value = 1.19 < 5 -> commission 5 (binds).
    (ii) slot 100,005: q = 1e5 / 11.00847; value = 95,381.1...; 0.00025 x value = 23.85 > 5 (does not bind)."""
    out = {}
    for slot, binds in ((5005.0, True), (100005.0, False)):
        m = panel(d("2021-03-01"), {SH: [T(10, 10, 10), T(10.5, 10.5, 10.0), T(10.5, 10.5, 10.5)]})
        led, orders = simulate.run(m, _mc_cfg(slot), {1: [(SH, 1.0)]}, 1, 2)
        lot = led.lots[0]
        q = (slot - 5.0) / (11.0 * 1.00077)
        value = q * 10.5
        assert abs(lot.q0 - q) < 1e-9, (slot, lot.q0, q)
        c = led.trades[0]["costs"]
        if binds:
            assert 0.00025 * value < 5.0 and c["commission"] == 5.0
        else:
            assert 0.00025 * value > 5.0 and abs(c["commission"] - 0.00025 * value) < 1e-9
        exp_cost = max(0.00025 * value, 5.0) + value * 0.0005 + value * 0.00002
        assert abs(lot.buy_cost - exp_cost) < 1e-9
        assert abs(led.cash[lot.sleeve] - (slot - value - exp_cost)) < 1e-9 and led.cash[lot.sleeve] >= 0.0
        out[str(slot)] = {"commission": c["commission"], "binds": binds}
    # at the limit price (SF-loose) the slot is still enough
    m = panel(d("2021-03-01"), {SH: [T(10, 10, 10), T(11.0, 11.0, 10.0), T(11, 11, 11)]})
    led, _ = simulate.run(m, _mc_cfg(5005.0), {1: [(SH, 1.0)]}, 1, 2, rule="SF-loose")
    assert led.cash[led.lots[0].sleeve] >= -1e-9
    return out


def test_min_commission_slot_too_small():
    """E-4: slot cash <= 5 yuan: nothing is left after the reserve -> no order, reason 'min_commission'."""
    for slot in (4.0, 5.0):
        m = panel(d("2021-03-01"), {SH: [T(10, 10, 10), T(10.5, 10.5, 10.0), T(10.5, 10.5, 10.5)]})
        led, orders = simulate.run(m, _mc_cfg(slot), {1: [(SH, 1.0)]}, 1, 2)
        assert [(o["reason"], o["submitted"]) for o in orders] == [("min_commission", False)] and led.lots == []
        assert simulate.order_summary(orders)["total"]["S"] == 0
    m = panel(d("2021-03-01"), {SH: [T(10, 10, 10), T(10.5, 10.5, 10.0), T(10.5, 10.5, 10.5)]})
    led, orders = simulate.run(m, _mc_cfg(5.01), {1: [(SH, 1.0)]}, 1, 2)
    assert orders[0]["submitted"] and orders[0]["filled"] and led.cash[led.lots[0].sleeve] >= 0.0


def test_min_commission_merged_sell_charged_once_pro_rata():
    """E-4 (d): two lots of one name sold in ONE order: one minimum commission, split pro rata to shares.
    Lots of ~454.2 and ~227.1 shares sold at 9.50: value ~6,472 -> 0.00025 x value = 1.62 < 5 -> 5 once."""
    import naive
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), T(9.0, 9.0, 10.0), T(9.5, 9.5, 9.0), T(9.5, 9.5, 9.5)]
    m = panel(d("2021-03-01"), {SH: rows})
    led, orders = simulate.run(m, _mc_cfg(5005.0), {1: [(SH, 1.0)], 2: [(SH, 0.5)]}, 1, 5)
    tr = [t for t in led.trades if t["side"] == "sell"]
    assert len(tr) == 1 and tr[0]["lots"] == [0, 1] and tr[0]["costs"]["commission"] == 5.0
    a, b = led.lots
    qa, qb = 5000.0 / (11.0 * 1.00077), 2500.0 / (11.0 * 1.00077)
    value = (qa + qb) * 9.5
    total = 5.0 + value * (0.001 + 0.00002 + 0.0005)                 # stamp + transfer + slippage (2021)
    assert abs(tr[0]["costs"]["total"] - total) < 1e-9
    assert abs(a.sell_cost - total * qa / (qa + qb)) < 1e-9 and abs(b.sell_cost - total * qb / (qa + qb)) < 1e-9
    assert abs(a.sell_cost + b.sell_cost - total) < 1e-9
    assert abs(naive.terminal_wealth(m, led, 5) - led.rec[5]["W_close"]) < 1e-9
    return {"order_commission": tr[0]["costs"]["commission"], "order_cost": total}


def test_min_commission_cash_never_negative_with_lot_rounding():
    """E-4 (c): lot-rounding robustness configuration with the 5-yuan minimum on random markets: after
    every filled buy the sleeve's cash is non-negative (all three fill rules; 5 seeds)."""
    from engine.synth import make_market, make_plans
    n_buys, worst, binding = 0, float("inf"), 0
    for seed, start in ((11, "2012-10-08"), (23, "2015-06-01"), (37, "2020-06-01"), (41, "2023-06-01"), (53, "2017-03-01")):
        m = make_market(seed, d(start), 150, 24)
        cfg = replace(CFG, H=3, K=6, W0=2.0e5, min_commission=5.0, lot_rounding=True)
        planG, planB, _ = make_plans(m, seed, cfg.K, 21, m.T - 2)
        for rule in fills.RULES:
            led, orders = simulate.run(m, cfg, planB, 21, m.T - 1, rule=rule)
            for t in led.trades:
                if t["side"] == "buy":
                    n_buys += 1
                    worst = min(worst, t["sleeve_cash_after"])
                    binding += t["costs"]["commission"] == 5.0
                    assert t["sleeve_cash_after"] >= -1e-9, (seed, rule, t)
    assert n_buys > 500 and binding > 50, (n_buys, binding)
    return {"buys": n_buys, "buys_with_binding_minimum": int(binding), "min_sleeve_cash_after_buy": worst}


def test_sell_side_mirror():
    """Sell: SF open > P_down (9.00); SF-strict open >= 9.20; SF-loose open >= 9.00; below P_down nobody."""
    assert _all(_one(9.00), "sell", 1000.0) == ((False, "S2"), (False, "S2"), F)
    assert _all(_one(9.01), "sell", 1000.0) == (F, (False, "S2"), F)
    assert _all(_one(9.19), "sell", 1000.0) == (F, (False, "S2"), F)
    assert _all(_one(9.20), "sell", 1000.0) == (F, F, F)
    assert _all(_one(8.50), "sell", 1000.0) == ((False, "S2"),) * 3
    assert _all(_one(11.00), "sell", 1000.0) == (F, F, F)             # limit-up open: a sell fills


def test_rounding_boundary_in_fill():
    """preclose 10.05 -> P_up 11.06 (half-up).  Open 11.05 is strictly below: filled under SF."""
    assert _dec(_one(11.05, pc=10.05), "buy", 1000.0, "SF") == F
    assert _dec(_one(11.06, pc=10.05), "buy", 1000.0, "SF") == (False, "S2")
    assert _dec(_one(9.05, pc=10.05), "sell", 1000.0, "SF") == (False, "S2")      # P_down = 9.05
    assert _dec(_one(9.06, pc=10.05), "sell", 1000.0, "SF") == F


def test_bands_by_board_date_status():
    """ChiNext ST 2020-08-21 (5%) vs 2020-08-24 (20%); STAR 20%; main ST 5%."""
    c = "sz.300001"
    m1 = _one(10.50, code=c, start="2020-08-20", st=True)     # order day = 2020-08-21, P_up 10.50
    assert m1.days[1] == d("2020-08-21")
    assert _dec(m1, "buy", 1000.0, "SF", code=c) == (False, "S2")
    m2 = _one(10.50, code=c, start="2020-08-21", st=True)     # order day = 2020-08-24 (Monday), P_up 12.00
    assert m2.days[1] == d("2020-08-24")
    assert _dec(m2, "buy", 1000.0, "SF", code=c) == F
    assert _dec(_one(11.50, code="sh.688001"), "buy", 1000.0, "SF", code="sh.688001") == F
    assert _dec(_one(12.00, code="sh.688001"), "buy", 1000.0, "SF", code="sh.688001") == (False, "S2")
    assert _dec(_one(10.50, st=True), "buy", 1000.0, "SF") == (False, "S2")          # main-board ST: 10.50
    assert _dec(_one(10.49, st=True), "buy", 1000.0, "SF") == F


def test_only_three_fields_of_day_t_bar_are_read():
    """Changing close / amount of day t and everything after t leaves every decision unchanged;
    changing the open changes it.  (high, low and the volume size are not even stored.)"""
    rng = np.random.default_rng(0)
    rows = [T(10, 10, 10, amt=1e6)] * 25 + [T(10.4, 10.9, 10.0, amt=3e6), T(10.2, 10.1, 10.9, amt=1e6)]
    base = panel(d("2021-03-01"), {SH: rows})
    ref = [_dec(base, s, v, r, i=25) for s in ("buy", "sell") for v in (500.0, 5000.0, 50000.0) for r in fills.RULES]
    for _ in range(20):
        m = panel(d("2021-03-01"), {SH: rows})
        s = m.secs[SH]
        s.close[25:] = rng.uniform(1, 100, size=2)
        s.amount[25:] = rng.uniform(1, 1e12, size=2)
        s.open[26:] = rng.uniform(1, 100)
        s.preclose[26:] = rng.uniform(1, 100)
        got = [_dec(m, sd, v, r, i=25) for sd in ("buy", "sell") for v in (500.0, 5000.0, 50000.0) for r in fills.RULES]
        assert got == ref
    m = panel(d("2021-03-01"), {SH: rows})
    m.secs[SH].open[25] = 11.0
    assert _dec(m, "buy", 500.0, "SF", i=25) == (False, "S2") and ref[0] == F


def _sim_cfg(**kw):
    return replace(CFG, H=2, K=1, W0=3.0e5, **kw)      # 3 sleeves of 1e5; slot = 1e5


def test_unfilled_buy_is_cancelled_not_retried():
    """Limit-up open on the order day: no lot; the cash stays; no order on later days."""
    rows = [T(10, 10, 10), T(11.0, 11.0, 10.0), T(10.5, 10.5, 11.0), T(10.5, 10.5, 10.5)]
    m = panel(d("2021-03-01"), {SH: rows})
    led, orders = simulate.run(m, _sim_cfg(), {1: [(SH, 1.0)]}, 1, 3)
    assert [(o["i"], o["filled"], o["reason"]) for o in orders] == [(1, False, "S2")]
    assert led.lots == [] and led.trades == [] and abs(led.rec[3]["W_close"] - 3.0e5) < 1e-9
    led2, orders2 = simulate.run(m, _sim_cfg(), {1: [(SH, 1.0)]}, 1, 3, rule="SF-loose")
    assert orders2[0]["filled"] and len(led2.lots) == 1 and led2.lots[0].entry_price == 11.0


def test_limit_down_sequence_exit_is_retried():
    """Exit due on day 3; days 3 and 4 open at limit-down (not filled, retried); day 5 fills."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), T(9.0, 9.0, 10.0), T(8.10, 8.10, 9.0), T(8.2, 8.2, 8.1)]
    m = panel(d("2021-03-01"), {SH: rows})
    led, orders = simulate.run(m, _sim_cfg(), {1: [(SH, 1.0)]}, 1, 5)
    sells = [(o["i"], o["filled"], o["reason"], o["retry"]) for o in orders if o["side"] == "sell"]
    assert sells == [(3, False, "S2", False), (4, False, "S2", True), (5, True, "filled", True)], sells
    lot = led.lots[0]
    assert lot.status == "sold" and lot.exit_i == 5 and lot.exit_price == 8.2 and lot.exit_due_i == 3
    assert led.traded_amount(3) == 0.0 and led.traded_amount(4) == 0.0 and led.rec[3]["cost"] == 0.0


def test_two_lots_due_same_day_one_order_cap_on_total():
    """Lot A (entry day 1, due day 3, blocked by limit-down) meets lot B (entry day 2, due day 4):
    one sell order for the total; pro-rata costs.  With a small ADV each lot alone is under the
    cap and the total is over it: not filled (S3), both stay open."""
    rows = [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), T(9.0, 9.0, 10.0), T(9.5, 9.5, 9.0), T(9.5, 9.5, 9.5)]
    m = panel(d("2021-03-01"), {SH: rows})
    plan = {1: [(SH, 1.0)], 2: [(SH, 0.5)]}
    led, orders = simulate.run(m, _sim_cfg(), plan, 1, 5)
    s4 = [o for o in orders if o["side"] == "sell" and o["i"] == 4]
    assert len(s4) == 1 and s4[0]["filled"] and sorted(s4[0]["lots"]) == [0, 1]
    tr = [t for t in led.trades if t["side"] == "sell"]
    assert len(tr) == 1 and tr[0]["lots"] == [0, 1]
    a, b = led.lots
    assert abs(a.sell_cost + b.sell_cost - tr[0]["costs"]["total"]) < 1e-9
    assert abs(a.sell_cost / b.sell_cost - a.q0 / b.q0) < 1e-9          # pro rata to shares sold
    assert a.sleeve != b.sleeve
    # cap on the total: value(A) ~ 0.9e5, value(B) ~ 0.45e5 at the reference price; cap = 1% x ADV
    rows2 = [dict(r, amt=1.0e7) for r in rows]                          # cap = 1e5: A alone ok, A+B over
    m2 = panel(d("2021-03-01"), {SH: rows2})
    led2, orders2 = simulate.run(m2, _sim_cfg(), plan, 1, 5)
    s4 = [o for o in orders2 if o["side"] == "sell" and o["i"] == 4][0]
    assert (s4["filled"], s4["reason"]) == (False, "S3") and len(led2.open_lots()) == 2
    qa, qb = led2.lots[0].q, led2.lots[1].q
    assert qa * 9.0 <= 1e5 and qb * 9.0 <= 1e5 and (qa + qb) * 9.0 > 1e5


def test_buy_and_sell_same_name_same_day_not_netted():
    """E-3: a lot is due for sale on a day on which the same name is bought again: two orders, two
    trades, costs on BOTH; the net traded amount is 0; the non-netting amount is the sum of the two
    order values and the cost on it is the sum of the two orders' costs.
    By hand (2021, SSE): q = 1e5 / (11 x 1.00077) for both lots (same slot cash, same P_up);
    value v = 10 q each.  Buy cost = v x 0.00077; sell cost = v x (0.00025 + 0.0005 + 0.00002 + 0.001)."""
    rows = [T(10, 10, 10)] * 6
    m = panel(d("2021-03-01"), {SH: rows})
    led, orders = simulate.run(m, _sim_cfg(), {1: [(SH, 1.0)], 3: [(SH, 1.0)]}, 1, 5)
    t3 = [t for t in led.trades if t["i"] == 3]
    assert sorted(t["side"] for t in t3) == ["buy", "sell"]
    v = 10.0 * 1e5 / (11.0 * 1.00077)
    c_buy, c_sell = v * 0.00077, v * 0.00177
    rep = led.turnover_report(3)
    assert abs(rep["TO"] - 2 * v) < 1e-6 and rep["net"] == 0.0 and led.net_traded_amount(3) == 0.0
    assert abs(rep["non_netting"] - 2 * v) < 1e-6 and rep["names_bought_and_sold"] == 1
    assert abs(rep["non_netting_cost"] - (c_buy + c_sell)) < 1e-9
    assert abs(led.rec[3]["cost"] - (c_buy + c_sell)) < 1e-9
    assert abs(led.rec[3]["cost"] - sum(t["costs"]["total"] for t in t3)) < 1e-9
    # (b) days without a same-name buy and sell: the non-netting amount is exactly 0 and TO = net
    for i in (1, 2, 4, 5):
        r = led.turnover_report(i)
        assert r["non_netting"] == 0.0 and r["non_netting_cost"] == 0.0 and abs(r["TO"] - r["net"]) <= 1e-9, (i, r)
    assert abs(led.turnover_report(1)["TO"] - v) < 1e-6 and abs(led.turnover_report(5)["TO"] - v) < 1e-6
    # (c) every order's cost is carried by its own lot exactly once
    assert abs(led.total_cost() - led.lot_cost_total()) < 1e-9
    assert abs(led.total_cost() - (2 * c_buy + 2 * c_sell)) < 1e-9
    rec = simulate.result_record(led, orders, 1, 5)
    assert rec["turnover_total"]["non_netting_days"] == 1 and abs(rec["turnover_total"]["non_netting"] - 2 * v) < 1e-6
    return {"order_turnover_day3": rep["TO"], "net_day3": rep["net"], "non_netting_cost_day3": rep["non_netting_cost"]}


def test_non_netting_unequal_buy_and_sell():
    """E-3, unequal sizes: sell v (lot 1), buy v/2 (scale 0.5).  Net = v/2 (a sell); non-netting amount
    = v + v/2 - v/2 = v; cost on it = cost(sell v) + cost(buy v/2) - cost(one sell of v/2)
    = v x 0.00177 + (v/2) x 0.00077 - (v/2) x 0.00177 = (v/2) x (0.00177 + 0.00077)."""
    rows = [T(10, 10, 10)] * 6
    m = panel(d("2021-03-01"), {SH: rows})
    led, _ = simulate.run(m, _sim_cfg(), {1: [(SH, 1.0)], 3: [(SH, 0.5)]}, 1, 5)
    v = 10.0 * 1e5 / (11.0 * 1.00077)
    r = led.turnover_report(3)
    assert abs(r["TO"] - 1.5 * v) < 1e-6 and abs(r["net"] - 0.5 * v) < 1e-6 and abs(r["non_netting"] - v) < 1e-6
    assert abs(r["non_netting_cost"] - 0.5 * v * (0.00177 + 0.00077)) < 1e-9
    assert abs(led.total_cost() - led.lot_cost_total()) < 1e-9


def test_quantity_predetermined_and_affordable():
    """q = slot / (P_up (1 + kappa) + per-share fee): uses P_up, not the open; cash never negative,
    also under SF-loose at the limit price and for an SSE name before 2015-08-01."""
    for start, rule, o in (("2021-03-01", "SF", 10.5), ("2021-03-01", "SF-loose", 11.0), ("2014-03-03", "SF-loose", 11.0)):
        m = panel(d(start), {SH: [T(10, 10, 10), T(o, o, 10.0), T(o, o, o)]})
        cfg = _sim_cfg()
        led, orders = simulate.run(m, cfg, {1: [(SH, 1.0)]}, 1, 2, rule=rule)
        lot = led.lots[0]
        kappa = cfg.commission_rate + cfg.slippage_rate + (0.00002 if start > "2015-08-01" else 0.0)
        per_share = 0.000375 if start < "2015-08-01" else 0.0
        assert abs(lot.q0 - 1e5 / (11.0 * (1 + kappa) + per_share)) < 1e-6, (start, lot.q0)
        assert led.cash[lot.sleeve] >= -1e-9, (start, rule, led.cash[lot.sleeve])
        if o == 11.0:
            assert abs(led.cash[lot.sleeve]) < 1e-6     # at the limit price the slot is spent exactly


def test_lot_rounding_by_board():
    """Lot-rounding run: STAR order of ~150 shares -> no order; ~250 -> 250; main board 250 -> 200."""
    star = "sh.688001"
    def run(code, w0, band_up):
        m = panel(d("2021-03-01"), {code: [T(10, 10, 10), T(10.5, 10.5, 10.0), T(10.5, 10.5, 10.5)]})
        cfg = replace(CFG, H=2, K=1, W0=w0, lot_rounding=True)
        return simulate.run(m, cfg, {1: [(code, 1.0)]}, 1, 2)
    # slot = W0/3; STAR P_up = 12.00: 150 shares need ~1,800 yuan, 250 need ~3,000 yuan
    led, orders = run(star, 3 * 150.5 * 12.0 * 1.00077, 12.0)
    assert orders[0]["reason"] == "below_lot" and led.lots == []
    led, orders = run(star, 3 * 250.5 * 12.0 * 1.00077, 12.0)
    assert orders[0]["filled"] and led.lots[0].q0 == 250.0
    led, orders = run(SH, 3 * 250.5 * 11.0 * 1.00077, 11.0)
    assert orders[0]["filled"] and led.lots[0].q0 == 200.0
    led, orders = run(SH, 3 * 99.0 * 11.0 * 1.00077, 11.0)
    assert orders[0]["reason"] == "below_lot"


def test_circuit_breaker_days_flagged_in_trade_ledger():
    m = panel(d("2016-01-04"), {SH: [T(10, 10, 10), T(10, 10, 10), T(10, 10, 10), T(10, 10, 10)]})
    assert m.days[0] == d("2016-01-04") and m.days[3] == d("2016-01-07")
    led, _ = simulate.run(m, _sim_cfg(), {1: [(SH, 1.0)]}, 1, 3)
    flags = {t["i"]: t["flag"] for t in led.trades}
    assert flags[1] is None and flags[3] is not None


TESTS = [test_buy_inside_band_filled_by_all, test_buy_open_at_limit_up, test_buy_strict_band_threshold,
         test_buy_open_above_computed_limit, test_s1_cases, test_capacity_cap,
         test_adv_window_uses_days_before_t_only, test_adv_window_with_suspended_days_inside,
         test_adv_fewer_than_20_traded_days_and_none, test_sell_order_value_uses_day_t_preclose_on_ex_date,
         test_stale_cap_fill_is_counted, test_sf_strict_fills_are_a_subset_of_sf_fills,
         test_sf_strict_reference_price_below_ten_cents, test_no_ref_is_not_part_of_S_t,
         test_min_commission_binding_and_not_binding, test_min_commission_slot_too_small,
         test_min_commission_merged_sell_charged_once_pro_rata,
         test_min_commission_cash_never_negative_with_lot_rounding, test_non_netting_unequal_buy_and_sell,
         test_sell_side_mirror, test_rounding_boundary_in_fill,
         test_bands_by_board_date_status, test_only_three_fields_of_day_t_bar_are_read,
         test_unfilled_buy_is_cancelled_not_retried, test_limit_down_sequence_exit_is_retried,
         test_two_lots_due_same_day_one_order_cap_on_total, test_buy_and_sell_same_name_same_day_not_netted,
         test_quantity_predetermined_and_affordable, test_lot_rounding_by_board,
         test_circuit_breaker_days_flagged_in_trade_ledger]

if __name__ == "__main__":
    run_tests("fills", TESTS, "fills.json")

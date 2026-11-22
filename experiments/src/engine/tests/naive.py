"""Naive, independent recomputation of terminal wealth and of SF buy decisions.

Deliberately does NOT import engine.ledger, engine.attribution, engine.costs, engine.labels,
engine.fills or engine.market.Valuer.  It shares with the engine only (i) the Market data
container (bars, event list, delisting / carry indices), (ii) the rate look-ups of the rule
calendar (tested separately against hand-typed values) and (iii) the list of fills, which is
its input.  Everything else - costs incl. the minimum commission per order, corporate
actions, successions and their carry period, write-offs incl. the U33 terminal factor, the
terminal mark incl. the P1 / P1-R restatement, limit prices, the capacity cap - is
re-implemented here in plain loops with different arithmetic (integer cents for limits).

Terminal wealth = W0 + sum over lots of that lot's cash flows (+ terminal value if open)
                  - commissions, computed per ORDER (a sell order = all lots of one security
                  sold on one day).
Dividends are counted net of the scheduled tax at the ex-date; cash timing is irrelevant
for wealth.  Not covered (asserted): the cash-exit charge sensitivity, the tax fallbacks,
a non-zero cash return.
"""
from __future__ import annotations

import math

from engine import rule_calendar as rc


def _other_cost(m, i, code, side, shares, amount, slippage):
    """Stamp duty + transfer fee + modelled shortfall (everything except the commission)."""
    dt = m.days[i]
    buy_r, sell_r = rc.stamp_duty(dt)
    mode, x = rc.transfer_fee(dt, "sh" if code.startswith("sh.") else "sz")
    fee = shares * x if mode == "per_share" else amount * x
    return amount * slippage + amount * (buy_r if side == "buy" else sell_r) + fee


def _is_traded(m, code, i):
    s = m.secs[code]
    if s.delist_i is not None and i >= s.delist_i:
        return False
    return bool(s.has_row[i] and s.flag_trading[i] and s.vol_pos[i])


def _gone(m, code, i):
    s = m.secs[code]
    return s.delist_i is not None and i >= s.delist_i


def _carried(m, code, i):
    """Delisted, share exchange pending: carried, not written off."""
    s = m.secs[code]
    cu = getattr(s, "carry_until_i", None)
    return s.delist_i is not None and cu is not None and s.delist_i <= i < cu


def _mark_close(m, code, i):
    """Per-share value at the close of day i, written out independently of the Valuer."""
    s = m.secs[code]
    if _gone(m, code, i):
        return _mark_close(m, code, s.delist_i - 1)        # carry period: last value of the absorbed name
    if _is_traded(m, code, i):
        c = float(s.close[i])
        return c if c > 0 else float(s.open[i])
    if s.has_row[i] and s.flag_trading[i]:                 # flagged trading, no volume
        return float(s.preclose[i])
    j = i - 1                                              # suspended or no row: carry and restate
    while j >= 0 and not _is_traded(m, code, j):
        j -= 1
    v = float(s.close[j])
    todo = []
    for ev in m.events.get(code, []):
        if getattr(ev, "forced_class", None):
            continue
        if ev.kind == "dist" and m.days[j] < ev.ex_date <= m.days[i]:
            todo.append((ev.ex_date, 0, ev))               # effective at the open of the ex-date
        if ev.kind == "rights" and ev.record_date is not None and m.days[j] <= ev.record_date < m.days[i]:
            todo.append((ev.record_date, 1, ev))           # effective at the close of the record date
    for _, _, ev in sorted(todo, key=lambda z: (z[0], z[1])):
        if ev.kind == "dist":
            v = (v - ev.gross_cash) / ev.phi
        else:
            v = min(v, (v + ev.rights_ratio * ev.rights_price) / (1.0 + ev.rights_ratio))
    return v


def lot_walk(m, code, entry_i, q0, exit_i, end_i, slippage, terminal_factor):
    """Cash flows of one lot EXCLUDING commissions.  Returns (cash flow, buy amount,
    sale or None) with sale = (day, security sold, amount)."""
    s = m.secs[code]
    buy_amount = q0 * float(s.open[entry_i])
    cf = -buy_amount - _other_cost(m, entry_i, code, "buy", q0, buy_amount, slippage)
    cur, q, succeeded = code, q0, False
    for i in range(entry_i + 1, end_i + 1):
        done = False
        todays = [e for e in m.events.get(cur, []) if e.kind != "rights" and e.ex_date == m.days[i]
                  and not getattr(e, "forced_class", None)]
        for ev in sorted(todays, key=lambda e: 0 if e.kind == "dist" else 1):
            if ev.kind == "dist":
                tau, _ = rc.dividend_tax(ev.record_date or m.days[i - 1])
                cf += q * ev.gross_cash * (1.0 - tau)
                q *= ev.phi
            elif ev.kind == "cashout" and not succeeded:
                return cf + q * ev.cash_per_share, buy_amount, None
            elif ev.kind == "exchange" and not succeeded:
                cur, q, succeeded = ev.successor, q * ev.ratio, True
                done = True                                 # same-day events of the successor: not applied
                break
            else:                                           # class U: terminal factor x last value
                return cf + terminal_factor * q * _mark_close(m, cur, i - 1), buy_amount, None
        if not done and _gone(m, cur, i) and not _carried(m, cur, i):
            return cf + terminal_factor * q * _mark_close(m, cur, i - 1), buy_amount, None
        if exit_i is not None and i == exit_i:
            amt = q * float(m.secs[cur].open[i])
            return cf + amt - _other_cost(m, i, cur, "sell", q, amt, slippage), buy_amount, (i, cur, amt)
    return cf + q * _mark_close(m, cur, end_i), buy_amount, None


def terminal_wealth(m, ledger, end_i):
    """W0 + sum of lot cash flows - commissions per order, from the ledger's fill list only
    (entry day, name, shares, sale day)."""
    cfg = ledger.cfg
    assert not cfg.cash_exit_explicit_charges and cfg.divtax_2015_reading == "from"
    assert not cfg.dividend_tax_fallback_20_before_2013 and not cfg.transfer_fee_fallback_no_2022_cut
    assert ledger.rho_on is None and ledger.rho_id is None
    rate, minc = cfg.commission_rate, cfg.min_commission
    total = ledger.W0
    sell_orders: dict = {}
    for lot in ledger.lots:
        exit_i = lot.exit_i if lot.status == "sold" else None
        cf, buy_amount, sale = lot_walk(m, lot.entry_code, lot.entry_i, lot.q0, exit_i, end_i,
                                        cfg.slippage_rate, cfg.terminal_value_U)
        total += cf - max(rate * buy_amount, minc)          # one buy order per lot
        if sale is not None:
            sell_orders[(sale[0], sale[1])] = sell_orders.get((sale[0], sale[1]), 0.0) + sale[2]
    for amount in sell_orders.values():                     # one sell order per (day, security)
        total -= max(rate * amount, minc)
    return total


def sf_buy_decision(m, code, i, q, cap_fraction=0.01, window=20, cap_zero=False):
    """SF for a buy, from raw arrays with integer-cent limit arithmetic.  Returns (filled, p_up).
    Capacity cap: the `window` most recent TRADED days before day i (cap_zero: the `window`
    market days before day i with non-traded days as zero)."""
    s = m.secs[code]
    if not s.has_row[i] or not (s.preclose[i] > 0):
        return False, None
    board = "star" if code[:6] in ("sh.688", "sh.689") else ("chinext" if code[:5] == "sz.30" else "main")
    dt = m.days[i]
    if board == "star":
        b = 20
    elif board == "chinext":
        b = 20 if dt.isoformat() >= "2020-08-24" else (5 if s.is_st[i] else 10)
    else:
        b = 5 if s.is_st[i] else 10
    cents = int(round(float(s.preclose[i]) * 100))
    up_c = (cents * (100 + b) + 50) // 100
    if up_c - cents < 1:
        up_c = cents + 1
    p_up = up_c / 100.0
    if not _is_traded(m, code, i):
        return False, p_up
    if int(round(float(s.open[i]) * 100)) >= up_c:
        return False, p_up
    if cap_zero:
        lo = max(0, i - window)
        tot = 0.0
        for j in range(lo, i):
            if _is_traded(m, code, j) and not math.isnan(s.amount[j]):
                tot += float(s.amount[j])
        cap = cap_fraction * tot / (i - lo)
    else:
        vals, j = [], i - 1
        while j >= 0 and len(vals) < window:
            if _is_traded(m, code, j):
                vals.append(0.0 if math.isnan(s.amount[j]) else float(s.amount[j]))
            j -= 1
        cap = cap_fraction * (math.fsum(vals) / len(vals)) if vals else 0.0
    return (q * p_up <= cap), p_up

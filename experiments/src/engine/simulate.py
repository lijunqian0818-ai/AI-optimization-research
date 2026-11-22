"""Day loop that turns a pre-specified nomination plan into orders, synthetic fills and
ledger bookings (PLAN 3.2, 3.4, 3.7, 3.8 (iv)).  It contains no model and no signal.

Order of a day t:
  1. ledger.begin_day(t): corporate actions, receivables, frozen labels;
  2. liquidation policy LP: every open lot with exit_due <= t is offered for sale; lots of one
     name are ONE order (capacity condition on their total, all-or-nothing); a non-filled
     sale is re-submitted on the next day;
  3. buys of the trading sleeve j = t mod (H+1): slot cash = sleeve's spendable cash at the
     close of t-1 / K; quantity q = scale x (slot cash - min_commission) /
     (P_up (1 + kappa_t) + f_t), fixed before the auction (PLAN 3.7, v0.7 E-4); a non-filled
     buy is cancelled, never retried;
  4. ledger.end_day(t).
No purchase is funded by a sale of the same auction: sizing uses cash at the close of t-1.

Order ledger.  Every record carries `submitted`.  A nomination for which no order can be
formed is recorded with submitted = False and one of the reasons
    no_ref          no row or no reference price on the order day (PLAN 3.8 (iii) note (12))
    no_cash         the sleeve has no spendable cash
    min_commission  slot cash does not exceed the minimum commission (v0.7, E-4)
    below_lot       quantity below the board's minimum after lot rounding
and is NOT part of S_t (orders submitted); these are counted separately (order_summary).
The existence of the day-t row, its `preclose` and its ST flag are the only day-t fields
order generation reads.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np

from . import fills
from . import rule_calendar as rc
from .config import EngineConfig, conventions_hash
from .costs import buy_kappa
from .ledger import Ledger
from .market import Market, Valuer

UNSUBMITTED = ("no_ref", "no_cash", "min_commission", "below_lot")


def cash_return_schedule(market: Market, cfg: EngineConfig) -> tuple[np.ndarray, np.ndarray]:
    """(rho_on, rho_id) of the robustness run with a non-zero cash return (PLAN 3.6 item 6,
    v0.7 E-19): one rate on the overnight interval covering the calendar days since the
    previous trading day, rho_on[t] = cash_return x days / cash_return_day_count; the intraday
    rate is cfg.cash_return_intraday (0)."""
    on = np.zeros(market.T)
    for i in range(1, market.T):
        on[i] = cfg.cash_return * (market.days[i] - market.days[i - 1]).days / cfg.cash_return_day_count
    return on, np.full(market.T, cfg.cash_return_intraday)


def run(market: Market, cfg: EngineConfig, plan: dict, start_i: int, end_i: int, rule: str = "SF",
        name: str = "", valuer: Optional[Valuer] = None, rho_on=None, rho_id=None) -> tuple[Ledger, list]:
    """plan[i] = list of (code, scale) nominations of day i (at most K, one per name).
    Returns (ledger, order ledger).  Days start_i .. end_i inclusive; start_i >= 1."""
    if start_i < 1:
        raise ValueError("start_i must be >= 1 (orders of day t need data of day t-1)")
    if rho_on is None and rho_id is None and (cfg.cash_return != 0.0 or cfg.cash_return_intraday != 0.0):
        rho_on, rho_id = cash_return_schedule(market, cfg)
    led = Ledger(market, cfg, valuer=valuer, name=name, rho_on=rho_on, rho_id=rho_id)
    # the ledger must start its day sequence at start_i
    led._day = start_i - 1
    orders: list[dict] = []
    for i in range(start_i, end_i + 1):
        led.begin_day(i)
        dt = market.days[i]
        # ---- sells (LP) ----
        due: dict[str, list] = {}
        for lot in led.open_lots():
            if lot.exit_due_i <= i and lot.entry_i < i:
                due.setdefault(lot.code, []).append(lot)
        for code in sorted(due):
            lots = due[code]
            oi = fills.order_inputs(market, code, i, cfg)
            Q = sum(l.q for l in lots)
            value = Q * float(oi.ref) if oi.ref is not None else 0.0
            ok, why = fills.decide(market, code, i, "sell", value, oi, cfg, rule)
            orders.append({"i": i, "code": code, "side": "sell", "q": Q, "filled": ok, "reason": why,
                           "submitted": True, "lots": [l.lot_id for l in lots],
                           "retry": any(l.exit_due_i < i for l in lots), "value": value,
                           "adv_reach": oi.adv_reach, "adv_days": oi.adv_days_used,
                           "stale_cap": bool(ok and oi.adv_reach > cfg.stale_cap_days),
                           "filled_xsrc": market.filled_xsrc(code, i)})
            if ok:
                led.book_sell(i, lots)
        # ---- buys ----
        sleeve = i % led.n_sleeves
        noms = plan.get(i, [])
        if len(noms) > cfg.K or len({c for c, _ in noms}) != len(noms):
            raise ValueError("at most K orders per day and one order per name")
        slot = led.spendable_prev_close(sleeve) / cfg.K

        def no_order(code, reason):
            orders.append({"i": i, "code": code, "side": "buy", "q": 0.0, "filled": False, "reason": reason,
                           "submitted": False, "sleeve": sleeve})

        for code, scale in noms:
            oi = fills.order_inputs(market, code, i, cfg)
            if oi.p_up is None:
                no_order(code, "no_ref")
                continue
            if slot <= 0:
                no_order(code, "no_cash")
                continue
            budget = slot - cfg.min_commission if cfg.min_commission > 0 else slot
            if budget <= 0:
                no_order(code, "min_commission")
                continue
            kappa, per_share = buy_kappa(dt, code, cfg)
            q = scale * budget / (float(oi.p_up) * (1.0 + kappa) + per_share)
            if cfg.lot_rounding:
                q = rc.round_buy_quantity(q, dt, rc.board_of(code))
                if q <= 0:
                    no_order(code, "below_lot")
                    continue
            value = q * float(oi.p_up)
            ok, why = fills.decide(market, code, i, "buy", value, oi, cfg, rule)
            rec = {"i": i, "code": code, "side": "buy", "q": q, "filled": ok, "reason": why, "submitted": True,
                   "sleeve": sleeve, "p_up": float(oi.p_up), "value": value, "adv_reach": oi.adv_reach,
                   "adv_days": oi.adv_days_used, "stale_cap": bool(ok and oi.adv_reach > cfg.stale_cap_days),
                   "filled_xsrc": market.filled_xsrc(code, i)}
            if ok:
                rec["lot"] = led.book_buy(i, code, sleeve, q).lot_id
            orders.append(rec)
        led.end_day(i)
    return led, orders


def order_summary(orders: list) -> dict:
    """Per day: S_t (buy orders submitted), n_t (synthetic fills), non-fills by reason, and the
    nominations for which no order was submitted (never part of S_t).  Sell orders are
    summarised separately.  Counts only."""
    by_day: dict = {}
    tot = {"S": 0, "n": 0, "buy_nonfill": {}, "unsubmitted": {}, "sell_orders": 0, "sell_fills": 0,
           "sell_nonfill": {}, "stale_cap_fills": 0, "orders_on_xsrc_rows": 0}
    for o in orders:
        d = by_day.setdefault(o["i"], {"S": 0, "n": 0, "buy_nonfill": {}, "unsubmitted": {}})
        if o.get("stale_cap"):
            tot["stale_cap_fills"] += 1
        if o.get("filled_xsrc"):
            tot["orders_on_xsrc_rows"] += 1
        if o["side"] == "sell":
            tot["sell_orders"] += 1
            if o["filled"]:
                tot["sell_fills"] += 1
            else:
                tot["sell_nonfill"][o["reason"]] = tot["sell_nonfill"].get(o["reason"], 0) + 1
            continue
        if not o["submitted"]:
            for t in (d, tot):
                t["unsubmitted"][o["reason"]] = t["unsubmitted"].get(o["reason"], 0) + 1
            continue
        for t in (d, tot):
            t["S"] += 1
            if o["filled"]:
                t["n"] += 1
            else:
                t["buy_nonfill"][o["reason"]] = t["buy_nonfill"].get(o["reason"], 0) + 1
    return {"by_day": by_day, "total": tot}


def result_record(led: Ledger, orders: list, start_i: int, end_i: int, rule: str = "SF") -> dict:
    """What a result file of one run contains besides its own content: the conventions hash
    (PLAN 3 intro, v0.7 E-20), the configuration hash, the daily turnover report (TO_t, net,
    non-netting amount and cost; v0.7 E-3) and the order summary.  No wealth or return figure."""
    daily = [led.turnover_report(i) for i in range(start_i, end_i + 1)]
    dc_ = getattr(led.m, "data_cutoff", None)
    return {"strategy": led.name, "fill_rule": rule,
            "conventions_hash": conventions_hash(), "config_hash": led.cfg.kappa_hash(),
            "data_cutoff": dc_.isoformat() if dc_ is not None else None,      # PLAN v0.8 C-8
            "sell_commission_exceeds_value": led.extra_counts.get("sell_commission_exceeds_value", 0),   # C-5
            "sleeve_days_negative_cash": led.extra_counts.get("sleeve_days_negative_cash", 0),           # C-5
            "days": [led.m.days[start_i].isoformat(), led.m.days[end_i].isoformat()],
            "turnover_daily": daily,
            "turnover_total": {"TO": sum(d["TO"] for d in daily), "net": sum(d["net"] for d in daily),
                               "non_netting": sum(d["non_netting"] for d in daily),
                               "non_netting_cost": sum(d["non_netting_cost"] for d in daily),
                               "non_netting_days": sum(1 for d in daily if d["names_bought_and_sold"] > 0),
                               "cost": sum(d["cost"] for d in daily)},
            "order_summary": order_summary(orders)["total"],
            "ledger_event_counts": dict(led.counts), "ledger_extra_counts": dict(led.extra_counts)}


def write_result(path, record: dict) -> None:
    """Write a result file; refuses a record without the conventions hash."""
    if "conventions_hash" not in record:
        raise ValueError("a result file must carry the conventions hash (PLAN v0.7, E-20)")
    if "data_cutoff" not in record:
        raise ValueError("a result file must carry the data cut-off field (PLAN v0.8, C-8)")
    Path(path).write_text(json.dumps(record, indent=1, ensure_ascii=False, default=str), encoding="utf-8")

"""Trading costs of ONE executed order on its benchmark-price value (PLAN 3.6 item 3, v0.7
E-3; Lemma 3 convention B).

Cost base.  Costs are charged per executed order, on the order's own value
|q_order| x OV_t (ad-valorem rates) plus the per-share transfer fee where one applies.  A buy
order and a sell order of one strategy in one name on one day are separate orders and are
not netted.  Every component is charged once.  Slippage is a cost; it is never applied to a
price.  The tax on distributions is not a trading cost and is not here.

Minimum commission (PLAN 3.7, v0.7 E-4): commission = max(rate x value, min_commission),
once per ORDER.  Several lots sold in one order share one commission pro rata to shares
(ledger.book_sell).
"""
from __future__ import annotations

from datetime import date

from . import rule_calendar as rc
from .config import EngineConfig


def trade_costs(dt: date, code: str, side: str, shares: float, amount: float, cfg: EngineConfig,
                include_slippage: bool = True) -> dict:
    """side: 'buy' | 'sell'; amount = shares x benchmark price (>= 0).
    include_slippage=False gives the explicit charges only (stamp duty, transfer fee,
    commission) - used by the cash-exit sensitivity of E-13."""
    if shares < 0 or amount < 0:
        raise ValueError("shares and amount must be non-negative")
    if shares == 0:
        return {"commission": 0.0, "stamp": 0.0, "transfer": 0.0, "slippage": 0.0, "total": 0.0}
    buy_rate, sell_rate = rc.stamp_duty(dt)
    stamp = amount * (buy_rate if side == "buy" else sell_rate)
    mode, amt = rc.transfer_fee(dt, rc.exchange_of(code), cfg.transfer_fee_fallback_no_2022_cut)
    transfer = shares * amt if mode == "per_share" else amount * amt
    commission = amount * cfg.commission_rate
    if cfg.min_commission > 0:
        commission = max(commission, cfg.min_commission)
    slippage = amount * cfg.slippage_rate if include_slippage else 0.0
    return {"commission": commission, "stamp": stamp, "transfer": transfer, "slippage": slippage,
            "total": commission + stamp + transfer + slippage}


def buy_kappa(dt: date, code: str, cfg: EngineConfig) -> tuple[float, float]:
    """(kappa_t, f_t) for the pre-determined buy quantity (PLAN 3.7, v0.7 E-4)

        q = slot cash / (P_up (1 + kappa_t) + f_t).

    kappa_t = sum of all buy-side ad-valorem rates in force on day t: modelled shortfall,
    commission rate, ad-valorem transfer fee, and stamp duty on days on which the buyer pays
    it (before 2008-09-19).  f_t = per-share transfer fee in yuan (SSE names before
    2015-08-01; otherwise 0).  The minimum commission is not part of kappa: in runs that
    apply it, simulate.run reserves `min_commission` from the slot cash first."""
    buy_rate, _ = rc.stamp_duty(dt)
    mode, amt = rc.transfer_fee(dt, rc.exchange_of(code), cfg.transfer_fee_fallback_no_2022_cut)
    kappa = cfg.commission_rate + cfg.slippage_rate + buy_rate + (amt if mode == "rate" else 0.0)
    return kappa, (amt if mode == "per_share" else 0.0)

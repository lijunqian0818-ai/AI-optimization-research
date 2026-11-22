"""Retrospective synthetic fill rules SF, SF-strict, SF-loose (PLAN 3.2; I-s2.4).

Information discipline
  * The ORDER (name, quantity, limit price, capacity cap) is a function of G_t: data dated
    <= t-1 plus the day-t reference price `preclose` and the day-t ST flag (PLAN 3.4 treats
    both as pre-open public information of day t; PLAN 3.8 (iii) note (12): the existence of
    the day-t row, its `preclose` and its ST flag are the only day-t fields of order
    generation).  `order_inputs` reads nothing else.
  * The FILL decision reads, of the day-t bar, ONLY: the traded flag (row exists, flagged
    trading, parsed volume > 0 - a boolean, never the size of the volume), the suspension
    flag, and the published open.  `bar_fields` is the single accessor and returns exactly
    these three.

All three rules are retrospective; none can tell whether the opening auction matched.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import numpy as np

from . import rule_calendar as rc
from .config import EngineConfig
from .market import Market

RULES = ("SF", "SF-strict", "SF-loose")


@dataclass
class OrderInputs:
    """G_t-measurable inputs of one order."""
    p_up: Optional[Decimal]
    p_down: Optional[Decimal]
    band: Optional[Decimal]
    ref: Optional[Decimal]          # day-t reference price (data `preclose`)
    cap_value: float                # cap_fraction x ADV_t (yuan)
    adv_days_used: int
    adv_reach: int = 0              # market trading days from the earliest window day to t-1


def adv(market: Market, code: str, i: int, cfg: EngineConfig) -> tuple[float, int, int]:
    """ADV_t for t = i.  Reads data dated <= i-1 only.  Returns (ADV, days used, reach).

    Primary definition (PLAN 3.7, v0.7 E-5; cfg.adv_counts_nontraded_days_as_zero = False):
    the mean unadjusted traded amount over the `adv_window` most recent market trading days
    dated <= i-1 on which the name TRADED; days without a trade are skipped, not counted as
    zero; fewer such days in the name's history: the mean of those that exist; none: 0.

    Sensitivity "cap-zero" (the v0.6 wording read literally; flag True): the mean over the
    `adv_window` market trading days ending i-1, days without a trade counted as zero.

    reach = (i-1) - (index of the earliest day of the window): how far back the window goes.
    Fills with reach > cfg.stale_cap_days are counted as "stale-cap fills" (U59)."""
    if i <= 0:
        return 0.0, 0, 0
    if cfg.adv_counts_nontraded_days_as_zero:
        s = market.secs[code]
        lo = max(0, i - cfg.adv_window)
        amt = np.where(s.has_row[lo:i] & s.flag_trading[lo:i] & s.vol_pos[lo:i], np.nan_to_num(s.amount[lo:i]), 0.0)
        return float(amt.sum() / (i - lo)), i - lo, i - 1 - lo
    ix, amounts = market.traded_index(code)
    hi = int(np.searchsorted(ix, i, side="left"))        # traded days with index < i
    lo = max(0, hi - cfg.adv_window)
    n = hi - lo
    if n == 0:
        return 0.0, 0, 0
    return float(amounts[lo:hi].sum() / n), n, int(i - 1 - ix[lo])


def order_inputs(market: Market, code: str, i: int, cfg: EngineConfig) -> OrderInputs:
    s = market.secs[code]
    a, n, reach = adv(market, code, i, cfg)
    cap = a * cfg.cap_fraction
    if (s.delist_i is not None and i >= s.delist_i) or not s.has_row[i] or not (s.preclose[i] > 0):
        return OrderInputs(None, None, None, None, cap, n, reach)
    ref = Decimal(repr(float(s.preclose[i])))
    up, dn, band = rc.limit_prices_for(code, market.days[i], ref, bool(s.is_st[i]))
    return OrderInputs(up, dn, band, ref, cap, n, reach)


def bar_fields(market: Market, code: str, i: int) -> tuple[bool, bool, Optional[float]]:
    """(traded flag, suspension flag, published open) of the day-i bar - the only fields of
    that bar the fill rules may read."""
    s = market.secs[code]
    if s.delist_i is not None and i >= s.delist_i:
        return False, False, None
    if not s.has_row[i]:
        return False, False, None
    suspended = not bool(s.flag_trading[i])
    traded = (not suspended) and bool(s.vol_pos[i])
    op = float(s.open[i]) if traded else None
    return traded, suspended, op


def decide(market: Market, code: str, i: int, side: str, order_value: float, oi: OrderInputs,
           cfg: EngineConfig, rule: str = "SF") -> tuple[bool, str]:
    """Return (filled, reason).  reason in {'filled', 'S1', 'S2', 'S3', 'no_ref'}.

    order_value (PLAN 3.7, v0.7 E-5): buys - quantity x the order's limit price P_up; sells -
    quantity (after the corporate actions effective by day t) x the day-t reference price
    `preclose` (pre-open public information; on ex-entitlement terms on an ex-date).

      SF        (S1) and (S2) and (S3)
      SF-strict (S1) and (S2) and open <= ref x (1 + 0.8 band) [sell: >= ref x (1 - 0.8 band)]
                and order value <= cap / 10.  The threshold is compared in exact decimal
                arithmetic and is not rounded to the tick; (S2) is a conjunct, so every
                SF-strict fill is an SF fill (v0.7, E-6).
      SF-loose  (S1) and open <= P_up [sell: >= P_down], no cap."""
    if rule not in RULES:
        raise ValueError(rule)
    if side not in ("buy", "sell"):
        raise ValueError(side)
    traded, _suspended, op = bar_fields(market, code, i)
    if not traded or op is None or not (op > 0):
        return False, "S1"
    if oi.p_up is None:
        return False, "no_ref"
    o = Decimal(repr(op))
    s2 = (o < oi.p_up) if side == "buy" else (o > oi.p_down)
    if rule == "SF":
        ok2 = s2
        cap = oi.cap_value
    elif rule == "SF-strict":
        f = Decimal(repr(cfg.strict_band_factor))
        band_ok = (o <= oi.ref * (1 + f * oi.band)) if side == "buy" else (o >= oi.ref * (1 - f * oi.band))
        ok2 = s2 and band_ok
        cap = oi.cap_value * cfg.strict_cap_factor
    else:  # SF-loose: fills at the limit credited, fills beyond the order's own limit not; no cap
        ok2 = (o <= oi.p_up) if side == "buy" else (o >= oi.p_down)
        cap = float("inf")
    if not ok2:
        return False, "S2"
    if order_value > cap:
        return False, "S3"
    return True, "filled"

"""Standard counterfactual orders (PLAN 8.3): for every (decision day t, name i) asked for, one order of
the notional slot size W0 / ((H+1) K) placed by the rules of PLAN 3 - quantity fixed from G_t at the
limit-up price, synthetic fill SF, exit by LP at t+H with re-submission, benchmark-price accounting with
the full cost model, entitlement-based distributions.  rho = net P&L per yuan of slot cash (0 if not
filled).  The O1 label of a filled order is the engine's frozen label (training target of LOSS).

Each standard order is its own lot and its own sell order (cap checked per order at the notional slot
size, PLAN 3.7 last paragraph).  Orders never interact, so names can be processed in separate chunks
(processes).  Every quantity comes from the engine (fills, costs, ledger, labels); nothing is re-coded.
An order still open at the last data day is valued at OV of that day, flagged `unresolved` (PLAN 8.3).
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from engine import fills
from engine.costs import buy_kappa
from engine.ledger import Ledger

_W: dict = {}


def run_chunk(market, ecfg, asks: dict, last_i: int) -> pd.DataFrame:
    """asks: {day index i: [codes]}.  Returns one row per (i, code)."""
    if not asks:
        return pd.DataFrame()
    slot = ecfg.W0 / ((ecfg.H + 1) * ecfg.K)
    first = min(asks)
    led = Ledger(market, ecfg, n_sleeves=1, W0=1e18, name="standard_orders")
    led._day = first - 1
    out = {}
    lot_of: dict[int, tuple] = {}
    for i in range(first, last_i + 1):
        led.begin_day(i)
        dt = market.days[i]
        for lot in list(led.open_lots()):
            if lot.exit_due_i <= i and lot.entry_i < i:
                oi = fills.order_inputs(market, lot.code, i, ecfg)
                value = lot.q * float(oi.ref) if oi.ref is not None else 0.0
                ok, _why = fills.decide(market, lot.code, i, "sell", value, oi, ecfg, "SF")
                if ok:
                    led.book_sell(i, [lot])
        for code in asks.get(i, ()):
            oi = fills.order_inputs(market, code, i, ecfg)
            rec = {"i": i, "code": code, "submitted": oi.p_up is not None, "filled": False, "reason": "no_ref",
                   "rho": 0.0, "o1": np.nan, "o1_outcome": "", "o2": np.nan, "exit_i": -1, "unresolved": False,
                   "lot": -1}
            if oi.p_up is not None:
                kappa, per_share = buy_kappa(dt, code, ecfg)
                q = slot / (float(oi.p_up) * (1.0 + kappa) + per_share)
                ok, why = fills.decide(market, code, i, "buy", q * float(oi.p_up), oi, ecfg, "SF")
                rec["reason"] = why
                if ok:
                    lot = led.book_buy(i, code, 0, q)
                    rec["filled"], rec["lot"] = True, lot.lot_id
                    lot_of[lot.lot_id] = (i, code)
            out[(i, code)] = rec
        led.end_day(i)
    # results per lot
    for lot in led.lots:
        r = out[lot_of[lot.lot_id]]
        if lot.status == "open":
            ov = led.val.ov(lot.code, last_i).value
            if ov is None:
                ov = led._last_val.get(lot.code, 0.0)
            pnl = lot.q * ov + lot.div_net - lot.cost_basis          # div_net is net of the full tax
            r["unresolved"] = True
        else:
            pnl = lot.realised_pnl
            r["exit_i"] = -1 if lot.exit_i is None else int(lot.exit_i)
            r["o2"] = lot.label_o2
        r["rho"] = pnl / slot
        if lot.label_o1 is not None:
            r["o1"] = lot.label_o1.label
            r["o1_outcome"] = lot.label_o1.outcome
    return pd.DataFrame(list(out.values()))


def _init(market, ecfg, last_i):
    _W.update(market=market, ecfg=ecfg, last_i=last_i)


def _work(asks):
    return run_chunk(_W["market"], _W["ecfg"], asks, _W["last_i"])


def standard_orders(market, ecfg, asks: dict, last_i: int, n_jobs: int = 1) -> pd.DataFrame:
    """Standard orders for all asked (i, code), chunked by name across processes."""
    codes = sorted({c for v in asks.values() for c in v})
    if n_jobs <= 1 or len(codes) < 2 * n_jobs:
        return run_chunk(market, ecfg, asks, last_i)
    chunks = [codes[k::n_jobs] for k in range(n_jobs)]
    parts = []
    work = []
    for ch in chunks:
        s = set(ch)
        work.append({i: [c for c in v if c in s] for i, v in asks.items() if any(c in s for c in v)})
    with ProcessPoolExecutor(max_workers=n_jobs, initializer=_init, initargs=(market, ecfg, last_i)) as ex:
        for df in ex.map(_work, work):
            parts.append(df)
    out = pd.concat([p for p in parts if len(p)], ignore_index=True)
    return out.sort_values(["i", "code"]).reset_index(drop=True)

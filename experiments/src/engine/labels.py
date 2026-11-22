"""Labels.

(1) Primary label O1: the decision tree of instantiation_ashare.md I-s3, as written there,
    with the plan-level notes (7)-(12) of PLAN v0.7 section 3.8 (iii).

    L = 1{net proceeds at the mark < cost basis}; mark instant = opening auction of day t+H.
    The function reads market data dated <= t+H only (the snapshot of day t + d_label,
    d_label = H + 1, contains exactly that) and is called once per entry by the ledger; the
    stored value is never recomputed.

    Outcomes: 'value' (tentative value accepted), 'U' (unsupported: label 1), 'M' (missing
    input: label 1; overrides a tentative value).

    Plan-level rules implemented here (PLAN 3.8 (iii)):
      note (4)  an unexplained reference-price step (list URS), an event the event table
                could not classify (Event.forced_class = 'U') or an undecided date conflict
                (Market.u_spans) inside (t, t+H]  =>  U;
      note (8)  sell-side charges and shortfall at the mark apply to the security part q*m
                only; the cash part D bears none; after a cash exit (S-d) nothing is sold and
                no sell-side charge is deducted.  Sensitivity (cfg.cash_exit_explicit_charges):
                stamp duty, transfer fee and commission (no shortfall) on the cash amount;
      note (9)  after a succession (S-e) effective on day d the successor's events with
                ex-date > d apply (record date >= d); an event of the successor whose
                effective day is d itself  =>  U; a successor that is not yet listed at the
                mark day  =>  U;
      note (10) a rights issue of the held name without a record date  =>  M if (a) its
                ex-date lies in (t, t+H+rights_missing_R_window market days], or (b) it
                carries neither date and the entry day is on or after the earliest date the
                record carries (`announce_date`; no date at all: every entry);
      note (11) no row on the mark day, or a P1 carry across a day without a row  =>  M.

(2) Deadline (bracket) labels of Corollary 1.3 (status: draft; PLAN 3.8 (iv), I-s6.4):
    `deadline_label`.  A missing or incomplete record gives lower label 0 and upper label 1;
    the O1 fallback M is not used for them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from . import rule_calendar as rc
from .config import EngineConfig
from .costs import trade_costs
from .market import Market, Valuer


@dataclass
class LabelResult:
    label: int
    outcome: str                 # 'value' | 'U' | 'M'
    price_branch: str = ""       # 'P1' | 'P1R' | 'P23' | 'P4' | 'cash' | ''
    spell: int = 0               # suspension-spell length at the mark day (P1 / P1R)
    events: list = field(default_factory=list)   # e.g. ['S-a', 'S-b', 'S-c', 'S-d', 'S-e']
    why: str = ""
    net_proceeds: Optional[float] = None
    cost_basis: Optional[float] = None
    mark: Optional[float] = None
    shares: Optional[float] = None
    cash: Optional[float] = None
    filled_xsrc: bool = False    # a row of the held name in [t, t+H] came from the cross-check source
    exit_charges: float = 0.0    # charges on a cash exit (sensitivity only)


def _bad(x) -> bool:
    return x is None or not np.isfinite(x)


def label_o1(market: Market, valuer: Valuer, code: str, entry_i: int, q0: float, entry_price: float,
             buy_cost: float, H: int, cfg: EngineConfig) -> LabelResult:
    mark_i = entry_i + H
    if mark_i >= market.T:
        raise ValueError("mark day beyond the panel; the label is pending, not computable")
    basis = q0 * entry_price + buy_cost
    j, q, D = code, q0, 0.0
    seen: list[str] = []
    succession = False
    held_from = entry_i
    exit_charges = 0.0
    segs = [[code, entry_i, mark_i]]          # (security, first day, last day) held - for the repair flag

    def filled() -> bool:
        for c, a, b in segs:
            f = market.secs[c].filled_from_xsrc
            if f is not None and bool(f[a:b + 1].any()):
                return True
        return False

    def out(outcome, why, **kw):
        return LabelResult(1, outcome, events=seen, why=why, cost_basis=basis, filled_xsrc=filled(), **kw)

    # ---- Step 1: events and listing status over (t, t+H] ----
    for i in range(entry_i + 1, mark_i + 1):
        if j is None:
            break
        u = market.unclassifiable_on(j, i)
        if u:
            return out("U", u)
        for ev in market.events_on(j, i):
            if ev.kind == "dist":
                if _bad(ev.gross_cash) or _bad(ev.phi) or ev.phi <= 0:
                    return out("M", "distribution amount or multiplier missing")
                rec = ev.record_date or market.days[i - 1]
                tau, _ = rc.dividend_tax(rec, cfg.dividend_tax_fallback_20_before_2013, cfg.divtax_2015_reading)
                if ev.gross_cash != 0:
                    D += q * ev.gross_cash * (1.0 - tau)
                    seen.append("S-a")
                if ev.phi != 1.0:
                    q *= ev.phi
                    seen.append("S-b")
            elif ev.kind == "cashout":
                if succession:
                    return out("U", "S-d event of a successor security")
                if _bad(ev.cash_per_share):
                    return out("M", "cash-out terms missing")
                cash = q * ev.cash_per_share
                if cfg.cash_exit_explicit_charges:
                    exit_charges = trade_costs(market.days[i], j, "sell", q, cash, cfg, include_slippage=False)["total"]
                D += cash - exit_charges
                seen.append("S-d")
                segs[-1][2] = i - 1
                j = None
                break
            elif ev.kind == "exchange":
                if succession:
                    return out("U", "second succession")
                if ev.successor is None or _bad(ev.ratio) or ev.ratio <= 0 or ev.successor not in market.secs:
                    return out("M", "exchange terms missing")
                segs[-1][2] = i - 1
                j, q, succession, held_from = ev.successor, q * ev.ratio, True, i
                segs.append([j, i, mark_i])
                seen.append("S-e")
                # note (9): an event of the successor effective on the succession day itself
                if market.events_on(j, i) or market.unclassifiable_on(j, i):
                    return out("U", "event of the successor on the succession day")
                break
            else:
                return out("U", "unsupported corporate event")

    # rights issues of the security held (S-c): no state change; terms must be in the snapshot
    if j is not None:
        for ev in market.rights_of(j):
            if ev.record_date is None:
                if ev.ex_date is not None:
                    xi = market.day_index_on_or_after(ev.ex_date)
                    hi = mark_i + cfg.rights_missing_R_window
                    beyond = xi is None                    # ex-date after the last panel day
                    if (not beyond and entry_i < xi <= hi) or (beyond and hi >= market.T - 1):
                        return out("M", "rights issue without record date (ex-date inside the window)")
                elif ev.announce_date is None or market.days[entry_i] >= ev.announce_date:
                    return out("M", "rights issue without record date and ex-date")
                continue
            if market.days[held_from] <= ev.record_date < market.days[mark_i]:
                if _bad(ev.rights_price) or _bad(ev.rights_ratio):
                    return out("M", "rights-issue terms missing")
                seen.append("S-c")

    if j is None:
        # holding is cash only (S-d): nothing left to sell, no sell-side charge (note (8))
        net = D
        return LabelResult(int(net < basis), "value", "cash", 0, seen, "", net, basis, None, 0.0, D,
                           filled(), exit_charges)

    # listing status at the mark day
    st = market.status(j, mark_i)
    if st == "D":
        return out("U", "no longer listed at the mark day")
    fr = market.first_row(j)
    if succession and (fr is None or fr > mark_i):
        return out("U", "successor not yet listed at the mark day")
    if st == "X":
        return out("M", "no bar row on the mark day")

    # ---- Step 2: price rule at the opening auction of day t+H ----
    v = valuer.ov(j, mark_i)
    if v.value is None:
        return out("M", v.why or "price input missing")
    if v.carry_missing_row:
        return out("M", "P1 carry across a day without a bar row")
    spell = market.spell_length(j, mark_i) if v.branch in ("P1", "P1R") else 0

    # ---- Step 3: validation and the label ----
    amount = q * v.value                        # security part only; D bears no charge (note (8))
    sell = trade_costs(market.days[mark_i], j, "sell", q, amount, cfg)["total"]
    net = amount + D - sell
    if _bad(net) or _bad(basis):
        return out("M", "non-finite value")
    return LabelResult(int(net < basis), "value", v.branch, spell, seen, "", net, basis, v.value, q, D, filled())


# ------------------------------------------------------------------ deadline labels (Cor. 1.3, draft)
@dataclass
class DeadlineLabel:
    S: int            # whole lot liquidated at or before the opening auction of day t+D
    V: int            # S and the record of that liquidation is complete and final in the snapshot
    L_cert: Optional[int]   # 1{net proceeds < cost basis} from the certified record (None if V = 0)
    lo: int           # V * L_cert
    hi: int           # 1 - V * (1 - L_cert)
    why: str = ""


def deadline_label(status: str, entry_i: int, exit_i: Optional[int], D: int, record_complete: bool,
                   net_proceeds: Optional[float], cost_basis: float) -> DeadlineLabel:
    """Bracket labels of I-s6.4 from the lot's record as it stands in the snapshot of day
    t + D + 1 (d_D = D + 1).

    S = 1 iff the liquidation policy has disposed of the WHOLE lot at or before the opening
    auction of day t+D: a sale ('sold'), or a cash exit S-d after which no security remains
    ('cashed_out' - a reading of I-s6.1, stated in the engine report).  A class-U write-off is
    not a liquidation (V = 0).  V = S and the record is complete (every event booked with its
    amounts, net proceeds finite).  Missing or incomplete record: lo = 0, hi = 1."""
    done = status in ("sold", "cashed_out") and exit_i is not None and exit_i <= entry_i + D
    S = int(done)
    why = ""
    if not done:
        why = "class-U event before the deadline" if (status == "written_off" and exit_i is not None
                                                      and exit_i <= entry_i + D) else "not liquidated by the deadline"
    ok = done and record_complete and net_proceeds is not None and bool(np.isfinite(net_proceeds)) \
        and bool(np.isfinite(cost_basis))
    if done and not ok:
        why = "record incomplete"
    V = int(ok)
    L = int(net_proceeds < cost_basis) if V else None
    lo = V * (L or 0)
    hi = 1 - V * (1 - (L or 0))
    return DeadlineLabel(S, V, L, lo, hi, why)

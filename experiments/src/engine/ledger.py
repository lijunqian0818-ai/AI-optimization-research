"""Share-and-cash ledger by entry lot (PLAN 3.6, 3.7, 3.9 (L), 3.11; Lemma 3 convention B).

One Ledger = one strategy (or comparator).  It does not decide anything: orders and fill
decisions are made outside (simulate.py / fills.py); the ledger books what it is told.

Accounting rules implemented
  * benchmark-price accounting: every trade is booked at OV_t = the published daily open;
    fees and modelled slippage are debited as costs at the trade, each exactly once;
  * cost base (PLAN 3.6 item 3, v0.7 E-3): costs are charged per executed ORDER on the
    order's own benchmark-price value; a buy and a sell of one name on one day are separate
    orders, never netted; several lots sold together are one order whose proceeds and costs
    (including a minimum commission, charged once) are split pro rata to shares sold.
    Reported per day: the order-level turnover TO_t, the net traded amount ||trade_t||_1
    and the "non-netting" amount TO_t - ||trade_t||_1 with the cost charged on it;
  * lots: one entry = one lot (entry day, name, sleeve);
  * corporate actions at the open of the effective day (overnight interval), on the lots
    held at the previous close: S-a/S-b (cash by entitlement, share multiplier), S-c (rights:
    not subscribed, no state change), S-d (cash-out), S-e (one succession), class U and
    delisting without S-d/S-e (write-off at the U33 terminal value);
  * a lot that arrived by succession is carried under the identifier "<successor>#succ" in
    the share vectors (PLAN 3.9, v0.7 E-14); it receives the successor's distributions with
    ex-date after the succession day; an event of the successor effective on the succession
    day itself is not booked and is flagged (label: U); a later S-d / S-e of the successor is
    class U for it;
  * events that could not be classified (URS steps, Event.forced_class = 'U', undecided date
    conflicts): nothing is booked, the name keeps being valued at market prices, flagged
    (PLAN 3.9); the label is U;
  * a delisted name whose share exchange is pending (disposition table, PLAN 3.11 rule 11):
    carried at the last value of the absorbed name until the successor's shares trade,
    flagged; a delisted name without such a record is written off (U33);
  * cash dividends (PLAN 3.11): wealth changes by q*g*(1-tau) at the ex-date; spendable cash
    receives the amount actually paid on the pay date; the remaining tax is a liability of
    the lot, debited from the sleeve's cash when the lot ceases to exist - at its sale, at a
    cash exit or at a write-off (v0.7, E-13).  tau is the schedule by record date (RC-14);
    holding-period brackets are NOT modelled (plan);
  * trade vector per day and name: trade = (s_post - s_pre) * OV with s_pre the shares after
    corporate actions - computed from share counts, independently of the trade records.
    It is the NET change of the share vector, as the theory files define trade_t.

Wealth = sum of sleeve cash + receivables - tax liabilities + sum_lots q * price.

Cash return (robustness run only; PLAN 3.6 item 6, v0.7 E-19).  Interest is credited on
(cash + receivables - liabilities), i.e. on all wealth not held in securities: on the
balance at the previous close for the overnight interval and - only if an intraday rate is
supplied, which the plan sets to 0 - on the balance after the auction trades and costs for
the intraday interval.  That receivables earn the cash return before they are paid is a
small overstatement (stated in the plan).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from . import rule_calendar as rc
from .config import EngineConfig
from .costs import trade_costs
from .labels import DeadlineLabel, LabelResult, deadline_label, label_o1
from .market import Market, Valuer, real_code, succ_id


class LedgerError(RuntimeError):
    pass


@dataclass
class Lot:
    lot_id: int
    code: str                  # security currently held (changes on S-e)
    entry_code: str
    sleeve: int
    entry_i: int
    entry_price: float
    q0: float
    q: float
    buy_cost: float
    cost_basis: float
    H: int
    exit_due_i: int
    status: str = "open"       # open | sold | cashed_out | written_off
    tax_liability: float = 0.0
    div_net: float = 0.0       # net distributions attributed to the lot
    exit_i: Optional[int] = None
    exit_price: Optional[float] = None
    proceeds: float = 0.0      # sale proceeds / cash-out / terminal value, before sell cost
    sell_cost: float = 0.0
    succession_used: bool = False
    succession_i: Optional[int] = None
    incomplete_record: bool = False     # an event of the holding period could not be booked in full
    log: list = field(default_factory=list)
    label_o1: Optional[LabelResult] = None
    label_o2: Optional[int] = None
    deadline: Optional[DeadlineLabel] = None

    @property
    def track_id(self) -> str:
        return succ_id(self.code) if self.succession_used else self.code

    @property
    def realised_pnl(self) -> Optional[float]:
        if self.status == "open":
            return None
        return self.proceeds - self.sell_cost + self.div_net - self.cost_basis


class Ledger:
    def __init__(self, market: Market, cfg: EngineConfig, valuer: Optional[Valuer] = None,
                 n_sleeves: Optional[int] = None, W0: Optional[float] = None, name: str = "",
                 rho_on=None, rho_id=None):
        self.m, self.cfg, self.name = market, cfg, name
        self.val = valuer or Valuer(market)
        self.n_sleeves = n_sleeves if n_sleeves is not None else cfg.H + 1
        self.W0 = cfg.W0 if W0 is None else W0
        self.cash = [self.W0 / self.n_sleeves] * self.n_sleeves
        self.receivables: list[dict] = []
        self.lots: list[Lot] = []
        self.trades: list[dict] = []
        self.flags: list[tuple] = []
        self.rec: dict[int, dict] = {}
        self.rho_on, self.rho_id = rho_on, rho_id
        self._day: Optional[int] = None
        self._phase = "closed"
        self._last_val: dict[str, float] = {}
        self._flagged: set = set()
        self._spendable_prev = [c for c in self.cash]
        self.counts = {"S-a": 0, "S-b": 0, "S-c": 0, "S-d": 0, "S-e": 0, "U": 0}
        self.extra_counts = {"unclassifiable_not_booked": 0, "successor_event_on_succession_day": 0,
                             "carry_days": 0, "dist_with_missing_amount": 0,
                             # PLAN v0.8 H-14 (task C-5): sell orders whose commission (incl. the
                             # minimum) exceeds the order's sale value, and sleeve-days on which
                             # the sleeve's cash net of liabilities is negative at the close
                             "sell_commission_exceeds_value": 0, "sleeve_days_negative_cash": 0}
        # index of open lots (insertion order = lot id order) and of lots whose labels are not
        # frozen yet, so that no daily step scans every lot ever created
        self._open: dict[int, Lot] = {}
        self._unlabelled: list[Lot] = []
        self._undeadlined: list[Lot] = []

    # ------------------------------------------------------------------ helpers
    def open_lots(self) -> list[Lot]:
        return list(self._open.values())

    def _shares(self) -> dict[str, float]:
        """Share vector keyed by track identifier (see market.py)."""
        out: dict[str, float] = {}
        for l in self._open.values():
            k = l.track_id
            out[k] = out.get(k, 0.0) + l.q
        return out

    def _flag(self, i: int, code: str, why: str) -> None:
        if (i, code, why) not in self._flagged:
            self._flagged.add((i, code, why))
            self.flags.append((i, code, why))

    def _price(self, ident: str, i: int, kind: str) -> float:
        code = real_code(ident)
        v = self.val.ov(code, i) if kind == "ov" else self.val.cv(code, i)
        if v.value is None:
            last = self._last_val.get(code)
            self._flag(i, code, f"valuation input missing ({v.branch}: {v.why}); last value carried")
            if last is None:
                raise LedgerError(f"{code} on day {i}: no valuation and nothing to carry forward")
            return last
        if v.why:
            self._flag(i, code, v.why)
        self._last_val[code] = v.value
        return v.value

    def cashlike(self, sleeve: Optional[int] = None) -> float:
        sl = range(self.n_sleeves) if sleeve is None else [sleeve]
        tot = 0.0
        for s in sl:
            tot += self.cash[s]
            tot += sum(r["amount"] for r in self.receivables if r["sleeve"] == s)
            tot -= sum(l.tax_liability for l in self._open.values() if l.sleeve == s)
        return tot

    def spendable(self, sleeve: int) -> float:
        """Sleeve cash net of outstanding tax liabilities (receivables are not spendable)."""
        return self.cash[sleeve] - sum(l.tax_liability for l in self._open.values() if l.sleeve == sleeve)

    def spendable_prev_close(self, sleeve: int) -> float:
        """Spendable cash of the sleeve at the close of the previous day (G_t input of sizing)."""
        return self._spendable_prev[sleeve]

    def wealth(self, i: int, kind: str) -> float:
        w = self.cashlike()
        for ident, q in self._shares().items():
            w += q * self._price(ident, i, kind)
        return w

    # ------------------------------------------------------------------ day cycle
    def begin_day(self, i: int) -> None:
        if self._phase != "closed" or (self._day is not None and i != self._day + 1):
            raise LedgerError("days must be processed in order: begin_day, trades, end_day")
        self._day, self._phase = i, "open"
        r = self.rec[i] = {"s_on": self._shares(), "cost": 0.0, "interest_on": 0.0, "interest_id": 0.0,
                           "order_turnover": 0.0, "orders_by_name": {}, "non_order_cost": 0.0,
                           "W_prev_close": self.rec[i - 1]["W_close"] if (i - 1) in self.rec else self.W0}
        # overnight cash return on the balance carried from the previous close
        if self.rho_on is not None and self.rho_on[i] != 0.0:
            for s in range(self.n_sleeves):
                amt = self.rho_on[i] * self.cashlike(s)
                self.cash[s] += amt
                r["interest_on"] += amt
        # corporate actions effective today, on the lots held at the previous close
        for lot in self.open_lots():
            self._apply_events(lot, i)
        # receivables whose pay date has come
        keep = []
        for rv in self.receivables:
            if rv["pay_i"] <= i:
                self.cash[rv["sleeve"]] += rv["amount"]
            else:
                keep.append(rv)
        self.receivables = keep
        r["s_pre"] = self._shares()
        r["W_open"] = self.wealth(i, "ov")
        # frozen O1 labels: entry of day t is labelled from the snapshot of day t + H + 1
        pending = []
        for lot in self._unlabelled:
            if lot.entry_i + lot.H + 1 <= i:
                lot.label_o1 = label_o1(self.m, self.val, lot.entry_code, lot.entry_i, lot.q0,
                                        lot.entry_price, lot.buy_cost, lot.H, self.cfg)
            else:
                pending.append(lot)
        self._unlabelled = pending
        # frozen deadline labels (Cor. 1.3, draft): from the record as of day t + D + 1, before
        # that day's trades (sales at or before the auction of t + D are in the record)
        pending = []
        for lot in self._undeadlined:
            D = lot.H + self.cfg.deadline_extra
            if lot.entry_i + D + 1 <= i:
                net = None if lot.status == "open" else lot.proceeds - lot.sell_cost + lot.div_net
                lot.deadline = deadline_label(lot.status, lot.entry_i, lot.exit_i, D,
                                              not lot.incomplete_record, net, lot.cost_basis)
            else:
                pending.append(lot)
        self._undeadlined = pending

    def _close_lot(self, lot: Lot, i: int, status: str, proceeds: float, price: Optional[float]) -> None:
        """The lot ceases to exist: proceeds are credited and the recorded dividend-tax
        liability is debited (sale, cash exit or write-off; PLAN 3.11, v0.7 E-13)."""
        self._open.pop(lot.lot_id, None)
        self.cash[lot.sleeve] += proceeds - lot.tax_liability
        lot.tax_liability = 0.0
        lot.status, lot.exit_i, lot.exit_price, lot.proceeds = status, i, price, proceeds
        lot.q = 0.0

    def _apply_events(self, lot: Lot, i: int) -> None:
        m, cfg = self.m, self.cfg
        code = lot.code
        u = m.unclassifiable_on(code, i)
        if u:                                    # URS convention: nothing booked, market valuation, flagged
            self._flag(i, code, "not booked: " + u)
            self.extra_counts["unclassifiable_not_booked"] += 1
            lot.incomplete_record = True
            lot.log.append((i, "U-not-booked", u))
        for ev in m.rights_of(code):
            if ev.record_date is not None and i > 0 and ev.record_date == m.days[i - 1]:
                self.counts["S-c"] += 1          # held at the close of the rights record date:
                lot.log.append((i, "S-c"))       # not subscribed, valued at zero, nothing booked
        for ev in m.events_on(code, i):
            if ev.kind == "dist":
                g, phi = ev.gross_cash, ev.phi
                if g is None or phi is None or not np.isfinite(g) or not np.isfinite(phi) or phi <= 0:
                    self._flag(i, code, "distribution with missing amount or multiplier: not booked")
                    self.extra_counts["dist_with_missing_amount"] += 1
                    lot.incomplete_record = True
                    continue
                rec_date = ev.record_date or m.days[i - 1]
                tau, wh = rc.dividend_tax(rec_date, cfg.dividend_tax_fallback_20_before_2013, cfg.divtax_2015_reading)
                gross = lot.q * g
                if gross != 0.0:
                    pay_i = i
                    if ev.pay_date is not None:
                        pj = m.day_index_on_or_after(ev.pay_date)
                        pay_i = max(i, pj) if pj is not None else m.T   # beyond the panel: stays a receivable
                    self.receivables.append({"pay_i": pay_i, "sleeve": lot.sleeve, "amount": gross * (1.0 - wh),
                                             "lot_id": lot.lot_id})
                    lot.tax_liability += gross * (tau - wh)
                    lot.div_net += gross * (1.0 - tau)
                    self.counts["S-a"] += 1
                    lot.log.append((i, "S-a", gross, tau, wh))
                if phi != 1.0:
                    lot.q *= phi
                    self.counts["S-b"] += 1
                    lot.log.append((i, "S-b", phi))
            elif ev.kind == "cashout" and not lot.succession_used:
                self.counts["S-d"] += 1
                lot.log.append((i, "S-d", ev.cash_per_share))
                cash = lot.q * ev.cash_per_share
                if cfg.cash_exit_explicit_charges:      # E-13 sensitivity: explicit charges, no shortfall
                    c = trade_costs(m.days[i], code, "sell", lot.q, cash, cfg, include_slippage=False)["total"]
                    lot.sell_cost = c
                    self.cash[lot.sleeve] -= c
                    self.rec[i]["cost"] += c
                    self.rec[i]["non_order_cost"] += c
                self._close_lot(lot, i, "cashed_out", cash, ev.cash_per_share)
                lot.label_o2 = int(lot.proceeds - lot.sell_cost + lot.div_net < lot.cost_basis)
                return
            elif ev.kind == "exchange" and not lot.succession_used:
                self.counts["S-e"] += 1
                lot.log.append((i, "S-e", ev.successor, ev.ratio))
                lot.code, lot.q, lot.succession_used, lot.succession_i = ev.successor, lot.q * ev.ratio, True, i
                # PLAN 3.8 (iii) note (9): an event of the successor effective on the succession day
                # cannot be classified safely - label U; here: not booked, flagged (URS convention)
                if m.events_on(lot.code, i) or m.unclassifiable_on(lot.code, i):
                    self._flag(i, lot.code, "event of the successor on the succession day: not booked for lots by succession")
                    self.extra_counts["successor_event_on_succession_day"] += 1
                    lot.incomplete_record = True
                return
            else:                            # class U (incl. S-d / S-e of a successor)
                self._write_off(lot, i, "class-U event")
                return
        if m.status(lot.code, i) == "D":
            if m.in_carry(lot.code, i):
                self.extra_counts["carry_days"] += 1
                return
            self._write_off(lot, i, "no longer listed")

    def _write_off(self, lot: Lot, i: int, why: str) -> None:
        """U33: valued at the last valuation until the event date and at
        terminal_value_U x that value thereafter (0 = conservative default)."""
        last = self._last_val.get(lot.code)
        if last is None:
            v = self.val.cv(lot.code, i - 1) if i > 0 else None
            last = v.value if (v is not None and v.value is not None) else 0.0
        self.counts["U"] += 1
        lot.log.append((i, "U", why))
        self._close_lot(lot, i, "written_off", lot.q * last * self.cfg.terminal_value_U, None)
        lot.label_o2 = 1

    # ------------------------------------------------------------------ trades (at OV = published open)
    def _need_open(self, code: str, i: int) -> float:
        if self._phase != "open" or i != self._day:
            raise LedgerError("trades are booked between begin_day and end_day of the same day")
        if not self.m.traded(code, i):
            raise LedgerError(f"{code} did not trade on day {i}: no synthetic fill can exist")
        return self._price(code, i, "ov")

    def _record_order(self, i: int, code: str, side: str, shares: float, amount: float, cost: float) -> None:
        r = self.rec[i]
        r["order_turnover"] += amount
        o = r["orders_by_name"].setdefault(code, {"buy": 0.0, "sell": 0.0, "buy_shares": 0.0, "sell_shares": 0.0, "cost": 0.0})
        o[side] += amount
        o[side + "_shares"] += shares
        o["cost"] += cost

    def book_buy(self, i: int, code: str, sleeve: int, q: float, H: Optional[int] = None) -> Lot:
        p = self._need_open(code, i)
        if not (q > 0):
            raise LedgerError("buy quantity must be positive")
        H = self.cfg.H if H is None else H
        amount = q * p
        c = trade_costs(self.m.days[i], code, "buy", q, amount, self.cfg)
        self.cash[sleeve] -= amount + c["total"]
        self.rec[i]["cost"] += c["total"]
        self._record_order(i, code, "buy", q, amount, c["total"])
        lot = Lot(len(self.lots), code, code, sleeve, i, p, q, q, c["total"], amount + c["total"], H, i + H)
        self.lots.append(lot)
        self._open[lot.lot_id] = lot
        self._unlabelled.append(lot)
        self._undeadlined.append(lot)
        self.trades.append({"i": i, "code": code, "side": "buy", "shares": q, "price": p, "amount": amount,
                            "costs": c, "lots": [lot.lot_id], "flag": rc.flagged_day(self.m.days[i]),
                            "filled_xsrc": self.m.filled_xsrc(code, i), "sleeve_cash_after": self.cash[sleeve]})
        return lot

    def book_sell(self, i: int, lots: list[Lot]) -> None:
        """One sell order for the whole remaining quantity of one or several lots of one name.
        The order's cost - including a minimum commission, charged once - is allocated to the
        lots pro rata to shares sold."""
        codes = {l.code for l in lots}
        if len(codes) != 1 or any(l.status != "open" for l in lots):
            raise LedgerError("a sell order covers open lots of exactly one security")
        code = codes.pop()
        if any(l.entry_i >= i for l in lots):
            raise LedgerError("T+1: a lot cannot be sold on its entry day")
        p = self._need_open(code, i)
        Q = sum(l.q for l in lots)
        amount = Q * p
        c = trade_costs(self.m.days[i], code, "sell", Q, amount, self.cfg)
        if c["commission"] > amount:                        # C-5 (H-14): counted, still booked
            self.extra_counts["sell_commission_exceeds_value"] += 1
        self.rec[i]["cost"] += c["total"]
        self._record_order(i, code, "sell", Q, amount, c["total"])
        for l in lots:
            share = l.q / Q
            l.sell_cost = c["total"] * share
            self.cash[l.sleeve] -= l.sell_cost
            self._close_lot(l, i, "sold", l.q * p, p)
            l.label_o2 = int(l.proceeds - l.sell_cost + l.div_net < l.cost_basis)
        self.trades.append({"i": i, "code": code, "side": "sell", "shares": Q, "price": p, "amount": amount,
                            "costs": c, "lots": [l.lot_id for l in lots], "flag": rc.flagged_day(self.m.days[i]),
                            "filled_xsrc": self.m.filled_xsrc(code, i)})

    def debit_cost(self, i: int, sleeve: int, amount: float) -> None:
        """A cost debited at the trade instant without a share trade (used by the Lemma 3 case
        'cash 100, cost 1, cash return 10%')."""
        if self._phase != "open" or i != self._day:
            raise LedgerError("costs are debited between begin_day and end_day")
        self.cash[sleeve] -= amount
        self.rec[i]["cost"] += amount
        self.rec[i]["non_order_cost"] += amount

    def end_day(self, i: int) -> None:
        if self._phase != "open" or i != self._day:
            raise LedgerError("end_day without begin_day")
        r = self.rec[i]
        r["s_post"] = self._shares()
        idents = set(r["s_pre"]) | set(r["s_post"])
        r["ov"] = {c: self._price(c, i, "ov") for c in sorted(idents)}   # sorted: deterministic order (v0.8)
        # net trade vector by SECURITY: lots by succession and directly bought lots of one
        # security are the same security for an order
        pre, post = {}, {}
        for c, q in r["s_pre"].items():
            pre[real_code(c)] = pre.get(real_code(c), 0.0) + q
        for c, q in r["s_post"].items():
            post[real_code(c)] = post.get(real_code(c), 0.0) + q
        r["trade"] = {c: (post.get(c, 0.0) - pre.get(c, 0.0)) * self._price(c, i, "ov") for c in sorted(set(pre) | set(post))}
        if self.rho_id is not None and self.rho_id[i] != 0.0:
            for s in range(self.n_sleeves):
                amt = self.rho_id[i] * self.cashlike(s)
                self.cash[s] += amt
                r["interest_id"] += amt
        r["W_close"] = self.wealth(i, "cv")
        self._spendable_prev = [self.spendable(s) for s in range(self.n_sleeves)]
        self.extra_counts["sleeve_days_negative_cash"] += sum(1 for v in self._spendable_prev if v < 0.0)
        self._phase = "closed"

    # ------------------------------------------------------------------ summaries
    def net_traded_amount(self, i: int) -> float:
        """||trade_t||_1: the NET change of the share vector valued at OV_t (theory definition
        of trade_t; a buy and a sell of one name on one day cancel in it)."""
        return sum(abs(v) for v in self.rec[i]["trade"].values())

    def traded_amount(self, i: int) -> float:
        """Alias of net_traded_amount (the NET amount).  For the order-level amount on which
        costs are charged use order_turnover."""
        return self.net_traded_amount(i)

    def order_turnover(self, i: int) -> float:
        """TO_t = sum over executed orders of |q_order| x OV_t - the cost base (v0.7, E-3)."""
        return self.rec[i]["order_turnover"]

    def non_netting(self, i: int) -> dict:
        """TO_t - ||trade_t||_1 and the cost charged on it.

        Amount, per name with a filled buy (value b) and a filled sell (value s) on the day:
        b + s - |b - s|.  Cost on it, per such name: the cost of the two orders minus the cost
        that ONE order for the net quantity |q_b - q_s| on the side of the larger would have
        borne (0 if the two cancel).  The plan states the reported quantity but not this
        formula; it is the engine's reading (listed in the engine report)."""
        r = self.rec[i]
        amount, cost, names = 0.0, 0.0, 0
        for code, o in r["orders_by_name"].items():
            if o["buy"] > 0.0 and o["sell"] > 0.0:
                names += 1
                amount += o["buy"] + o["sell"] - abs(o["buy"] - o["sell"])
                dq = o["buy_shares"] - o["sell_shares"]
                net_cost = 0.0
                if dq != 0.0:
                    net_cost = trade_costs(self.m.days[i], code, "buy" if dq > 0 else "sell", abs(dq),
                                           abs(o["buy"] - o["sell"]), self.cfg)["total"]
                cost += o["cost"] - net_cost
        return {"amount": amount, "cost": cost, "names": names}

    def turnover_report(self, i: int) -> dict:
        nn = self.non_netting(i)
        return {"i": i, "TO": self.order_turnover(i), "net": self.net_traded_amount(i),
                "non_netting": nn["amount"], "non_netting_cost": nn["cost"], "names_bought_and_sold": nn["names"],
                "cost": self.rec[i]["cost"]}

    def total_cost(self) -> float:
        return sum(r["cost"] for r in self.rec.values())

    def lot_cost_total(self) -> float:
        """Sum of the costs carried by the lots (buy cost + sell / exit cost)."""
        return sum(l.buy_cost + l.sell_cost for l in self.lots)

    def outstanding_liability(self) -> float:
        return sum(l.tax_liability for l in self._open.values())

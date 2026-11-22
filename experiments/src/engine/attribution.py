"""Return-based attribution track (A) and the Lemma 3 identity on two intervals per day.

(A) is the second computation of PLAN 3.9: it rebuilds the two return vectors of each day
from unadjusted prices and the event table (formulas below) and never touches the ledger's
lot bookkeeping.  It takes from the ledger only the share counts held in each interval and
the day's cost.

  overnight  x_on[t]: total return from CV_{t-1} to OV_t of one share held at the close of
             t-1, including share multipliers effective on t and entitled cash net of the
             tax of the schedule by record date; S-d, S-e and write-offs enter here.
  intraday   x_id[t] = CV_t / OV_t - 1.

Lemma 3 (theorems.md) is applied to each interval separately and the terms are summed.
Fixed conventions (PLAN 8.2): interaction booked under composition (reference
h^E = e^G w^B); when e^B = 0 in an interval, w^B is supplied by the caller through
`fallback_wB(kind, i)` (plan: equal weight on the baseline's nominated lists of the cohorts
it would hold; if there is none, 0); when e^G = 0, w^G is irrelevant and set to 0.

Identifiers (PLAN 3.9, v0.7 E-14).  Holdings are keyed by track identifier: a lot that
arrived by succession is "<successor>#succ".  Such an identifier has the successor's prices
and distributions, but a further S-d / S-e of the successor is class U for it (terminal
value U33), while a directly bought lot of the same security follows S-d / S-e.  The
identifier is the same for every strategy and reference path, so Lemma 3 applies unchanged.

The three terms of the decomposition do not depend on the reference cost C^E.
"""
from __future__ import annotations

from typing import Callable, Optional

from . import rule_calendar as rc
from .config import EngineConfig
from .costs import trade_costs
from .market import Market, Valuer, is_succ, real_code, succ_id


class AttributionError(RuntimeError):
    pass


class ReturnTrack:
    def __init__(self, market: Market, valuer: Valuer, cfg: EngineConfig):
        self.m, self.val, self.cfg = market, valuer, cfg
        self._last: dict[str, float] = {}

    def _p(self, ident: str, i: int, kind: str) -> float:
        code = real_code(ident)
        v = self.val.ov(code, i) if kind == "ov" else self.val.cv(code, i)
        if v.value is None:
            # carry the last valid valuation, exactly as a data defect is handled in the ledger
            for j in range(i - 1, -1, -1):
                w = self.val.cv(code, j)
                if w.value is not None:
                    return w.value
            raise AttributionError(f"no valuation for {code} up to day {i}")
        return v.value

    def share_map(self, ident: str, i: int) -> tuple[Optional[str], float, float]:
        """Effect of the events of day i on ONE share of `ident` held at the close of i-1:
        (identifier held afterwards or None, number of shares of it, cash received net of tax
        and before any cost).

        Events with forced_class 'U', URS steps and undecided date conflicts are not booked
        (Market.events_on does not return them).  For an identifier "<Y>#succ" a cash-out or
        exchange of Y is class U.  On the day of a succession X -> Y the events of Y effective
        that day are not applied to the arriving shares (PLAN 3.8 (iii) note (9))."""
        m = self.m
        code, succ = real_code(ident), is_succ(ident)
        cur, mult, cash = ident, 1.0, 0.0
        for ev in m.events_on(code, i):
            if ev.kind == "dist":
                g, phi = ev.gross_cash, ev.phi
                if g is None or phi is None or not (g == g) or not (phi == phi) or phi <= 0:
                    continue                                   # not booked by the ledger either
                rec_date = ev.record_date or m.days[i - 1]
                tau, _ = rc.dividend_tax(rec_date, self.cfg.dividend_tax_fallback_20_before_2013,
                                         self.cfg.divtax_2015_reading)
                cash += mult * g * (1.0 - tau)
                mult *= phi
            elif ev.kind == "cashout" and not succ:
                return None, 0.0, cash + mult * ev.cash_per_share
            elif ev.kind == "exchange" and not succ:
                return succ_id(ev.successor), mult * ev.ratio, cash
            else:
                return None, 0.0, cash + mult * self._p(code, i - 1, "cv") * self.cfg.terminal_value_U
        if m.status(code, i) == "D" and not m.in_carry(code, i):
            return None, 0.0, cash + mult * self._p(code, i - 1, "cv") * self.cfg.terminal_value_U
        return cur, mult, cash

    def x_on(self, code: str, i: int) -> float:
        base = self._p(code, i - 1, "cv")
        cur, mult, cash = self.share_map(code, i)
        end = cash + (mult * self._p(cur, i, "ov") if cur is not None else 0.0)
        return end / base - 1.0

    def x_id(self, code: str, i: int) -> float:
        return self._p(code, i, "cv") / self._p(code, i, "ov") - 1.0

    def day(self, ledger, i: int) -> dict:
        """Holdings (yuan), returns and the wealth change of track (A) for one ledger day."""
        r = ledger.rec[i]
        h_on = {c: q * self._p(c, i - 1, "cv") for c, q in r["s_on"].items()}
        x_on = {c: self.x_on(c, i) for c in h_on}
        h_id = {c: q * self._p(c, i, "ov") for c, q in r["s_post"].items()}
        x_id = {c: self.x_id(c, i) for c in h_id}
        pnl_on = sum(h_on[c] * x_on[c] for c in h_on)
        pnl_id = sum(h_id[c] * x_id[c] for c in h_id)
        return {"i": i, "h_on": h_on, "x_on": x_on, "h_id": h_id, "x_id": x_id, "cost": r["cost"],
                "pnl_on": pnl_on, "pnl_id": pnl_id, "dW_A": pnl_on + pnl_id - r["cost"]}


def periods_from_track(days: list[dict], scale: Optional[dict] = None) -> tuple[list, float]:
    """Flatten track days into Lemma 3 periods [(kind, i, h, x)], and the total cost.
    scale[i] divides holdings and cost of day i (wealth normalisation by W_{t-1}, PLAN 8.2)."""
    periods, C = [], 0.0
    for d in days:
        s = 1.0 if scale is None else scale[d["i"]]
        periods.append(("on", d["i"], {c: v / s for c, v in d["h_on"].items()}, d["x_on"]))
        periods.append(("id", d["i"], {c: v / s for c, v in d["h_id"].items()}, d["x_id"]))
        C += d["cost"] / s
    return periods, C


def lemma3(periods_G: list, periods_B: list, C_G: float, C_B: float,
           fallback_wB: Optional[Callable[[str, int], dict]] = None) -> dict:
    """Identity (2) of Lemma 3 over a common list of periods.

    periods_a: [(kind, i, h: {code: holding}, x: {code: return})], same (kind, i) order for
    G and B; where both carry a return for a name the two must agree (one return vector).
    Returns the three terms split by interval kind, their total, Pi^G - Pi^B and the residual."""
    if len(periods_G) != len(periods_B):
        raise AttributionError("G and B must cover the same periods")
    out = {k: {"exposure": 0.0, "composition": 0.0, "exposure_alt": 0.0, "composition_alt": 0.0,
               "interaction": 0.0, "gross_G": 0.0, "gross_B": 0.0}
           for k in ("on", "id")}
    zero_B = {"on": 0, "id": 0}
    zero_B_no_fallback = 0
    max_x_mismatch = 0.0
    for (kg, ig, hG, xG), (kb, ib, hB, xB) in zip(periods_G, periods_B):
        if (kg, ig) != (kb, ib):
            raise AttributionError("period mismatch")
        x = dict(xB)
        for c, v in xG.items():
            if c in x:
                max_x_mismatch = max(max_x_mismatch, abs(x[c] - v))
            x[c] = v
        eG, eB = sum(hG.values()), sum(hB.values())
        if eG < 0 or eB < 0:
            raise AttributionError("negative exposure: long-only convention violated")
        if eB > 0:
            wB = {c: v / eB for c, v in hB.items()}
        else:
            zero_B[kg] += 1
            wB = dict(fallback_wB(kg, ig) or {}) if fallback_wB is not None else {}
            if not wB:
                zero_B_no_fallback += 1
            for c in wB:
                if c not in x:
                    raise AttributionError(f"fallback weight on {c} without a return in period {(kg, ig)}")
        wG = {c: v / eG for c, v in hG.items()} if eG > 0 else {}
        rB = sum(w * x[c] for c, w in wB.items())          # (w^B)'x
        rG = sum(w * x[c] for c, w in wG.items())          # (w^G)'x
        o = out[kg]
        o["exposure"] += (eG - eB) * rB
        o["composition"] += eG * (rG - rB)
        o["exposure_alt"] += (eG - eB) * rG                # other ordering (reference e^B w^G)
        o["composition_alt"] += eB * (rG - rB)
        o["interaction"] += (eG - eB) * (rG - rB)
        o["gross_G"] += sum(v * x[c] for c, v in hG.items())
        o["gross_B"] += sum(v * x[c] for c, v in hB.items())
    exposure = out["on"]["exposure"] + out["id"]["exposure"]
    composition = out["on"]["composition"] + out["id"]["composition"]
    cost = -(C_G - C_B)
    pi_G = out["on"]["gross_G"] + out["id"]["gross_G"] - C_G
    pi_B = out["on"]["gross_B"] + out["id"]["gross_B"] - C_B
    return {"by_interval": out, "exposure": exposure, "composition": composition, "cost": cost,
            "sum_terms": exposure + composition + cost, "Pi_G": pi_G, "Pi_B": pi_B,
            "diff": pi_G - pi_B, "residual": (pi_G - pi_B) - (exposure + composition + cost),
            "residual_alt": (pi_G - pi_B) - (out["on"]["exposure_alt"] + out["id"]["exposure_alt"]
                                             + out["on"]["composition_alt"] + out["id"]["composition_alt"] + cost),
            "zero_baseline_intervals": zero_B, "zero_baseline_without_fallback": zero_B_no_fallback,
            "max_return_mismatch": max_x_mismatch}


def reference_cost(track: ReturnTrack, periods_G: list, periods_B: list,
                   fallback_wB: Optional[Callable[[str, int], dict]] = None) -> dict:
    """Notional cost C^E of the exposure-schedule reference h^E = e^G w^B (PLAN 8.2), from
    share-based trades: s^E = h^E / p; trade = (s_t - s_{t-}) * p with s_{t-} the shares after
    the corporate actions effective by that instant; cash distributions are not trades.

    The reference has no orders; it is costed on its NET implied trades, at the same rates as
    the real strategies (PLAN 3.6 item 3).  It changes at BOTH instants of a day, and both
    implied trades are costed (PLAN 8.2, v0.7 E-7, following theorems.md: C^E from the share
    changes at the start of every period; the periods are the 2T intervals):

        C_E_open   implied trades at the auction instant, valued at OV_t
        C_E_close  implied rebalancing at the close, valued at CV_t (booked under the date of
                   that close; by_instant key (t+1, 'close') = close of day t)
        C_E        = C_E_open + C_E_close

    The three terms of the decomposition (exposure, composition, cost difference C^G - C^B)
    do not depend on C^E; it only splits the cost term when a net reference P&L is shown."""
    m, cfg = track.m, track.cfg
    comp = {"open": {"amount": 0.0, "cost": 0.0}, "close": {"amount": 0.0, "cost": 0.0}}
    prev_shares: dict[str, float] = {}      # shares of the reference carried into the instant
    by_instant: dict = {}                   # (day index, 'open' | 'close') -> traded amount
    for (kind, i, hG, _), (_, _, hB, _) in zip(periods_G, periods_B):
        eG, eB = sum(hG.values()), sum(hB.values())
        if eB > 0:
            wB = {c: v / eB for c, v in hB.items()}
        else:
            wB = dict(fallback_wB(kind, i) or {}) if fallback_wB is not None else {}
        if kind == "on":       # instant = close of day i-1; prices CV_{i-1}; no corporate action
            price = {c: track._p(c, i - 1, "cv") for c in set(wB) | set(prev_shares)}
            pre = dict(prev_shares)
            dt, where = m.days[i - 1], "close"
        else:                  # instant = auction of day i; prices OV_i; actions of day i applied
            pre = {}
            for c, s in prev_shares.items():
                cur, mult, _cash = track.share_map(c, i)
                if cur is not None:
                    pre[cur] = pre.get(cur, 0.0) + s * mult
            price = {c: track._p(c, i, "ov") for c in set(wB) | set(pre)}
            dt, where = m.days[i], "open"
        post = {c: eG * w / price[c] for c, w in wB.items()}
        for c in sorted(set(pre) | set(post)):         # sorted: summation order independent of hashing
            ds = post.get(c, 0.0) - pre.get(c, 0.0)
            amt = abs(ds) * price[c]
            if amt > 0:
                comp[where]["amount"] += amt
                by_instant[(i, where)] = by_instant.get((i, where), 0.0) + amt
                comp[where]["cost"] += trade_costs(dt, real_code(c), "buy" if ds > 0 else "sell", abs(ds), amt, cfg)["total"]
        prev_shares = post
    comp["total_cost"] = comp["open"]["cost"] + comp["close"]["cost"]
    comp["C_E_open"] = comp["open"]["cost"]
    comp["C_E_close"] = comp["close"]["cost"]
    comp["C_E"] = comp["C_E_open"] + comp["C_E_close"]
    comp["by_instant"] = by_instant
    return comp

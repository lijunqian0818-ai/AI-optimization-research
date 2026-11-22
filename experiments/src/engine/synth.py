"""Random synthetic market for the engine tests.  NOT a model of A-share prices and never
used for any result: its only purpose is to exercise every branch of the accounting
(limit opens, suspensions, no-trade days, missing rows, missing closes, dividends, bonus
issues, consolidations, rights issues with payment-period suspension, cash-outs,
successions - three absorbed names per market, two into one successor, one with a carry
period before the successor's new shares trade and a later cash-out of that successor -
class-U events, delistings) on reproducible seeds.

v0.7: the succession roles were added (task ENG-11 (c)), so the random stream - and with it
every random panel - differs from the v0.6 panels of the same seeds.

Suspended-day rows carry open = close = 999.0 on purpose: any code path that read them
as a value would break the reconciliation.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from . import rule_calendar as rc
from .market import Event, Market, Sec


def weekdays(start: date, n: int) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def _r2(x: float) -> float:
    return float(np.round(x + 1e-9, 2))


def make_market(seed: int, start: date, T: int = 150, n: int = 24, special: bool = True) -> Market:
    rng = np.random.default_rng(seed)
    days = weekdays(start, T)
    prefixes = ["sh.6000", "sz.0000", "sz.3000", "sh.6880", "sh.6010", "sz.0020"]
    codes = [f"{prefixes[k % len(prefixes)]}{k:02d}" for k in range(n)]
    secs: dict[str, Sec] = {}
    events: list[Event] = []

    # ---- special roles (disjoint names) ----
    role: dict[str, tuple] = {}
    if special:
        pool = list(rng.permutation(n))
        def take():
            return codes[pool.pop()]
        for _ in range(3):
            role[take()] = ("rights", int(rng.integers(25, T - 40)))
        role[take()] = ("cashout", int(rng.integers(60, T - 20)))
        succ = take()
        role[succ] = ("successor", None)
        role[take()] = ("exchange", int(rng.integers(60, T - 20)), succ, 0)
        role[take()] = ("exchange", int(rng.integers(40, T - 20)), succ, 0)
        succ2 = take()
        d3 = int(rng.integers(45, T - 50))
        carry = int(rng.integers(2, 5))
        role[take()] = ("exchange", d3, succ2, carry)          # carried `carry` days before the new shares trade
        role[succ2] = ("successor_cashout", int(rng.integers(d3 + carry + 6, T - 12)))
        role[take()] = ("unsupported", int(rng.integers(60, T - 20)))
        role[take()] = ("delist", int(rng.integers(70, T - 15)))
        role[take()] = ("delist", int(rng.integers(70, T - 15)))
        role[take()] = ("longsusp", int(rng.integers(30, T - 60)))

    for k, code in enumerate(codes):
        board = rc.board_of(code)
        st_from = int(rng.integers(20, T)) if (board != "star" and rng.random() < 0.25) else None
        op = np.full(T, np.nan); cl = np.full(T, np.nan); pc = np.full(T, np.nan); am = np.zeros(T)
        has = np.zeros(T, bool); ft = np.zeros(T, bool); vp = np.zeros(T, bool); st = np.zeros(T, bool)
        last_close = float(np.round(rng.uniform(3, 80), 2))
        ref = last_close
        adv_scale = float(np.exp(rng.uniform(np.log(2e6), np.log(5e8))))
        r = role.get(code, (None,))
        delist_i = r[1] if r[0] in ("cashout", "exchange", "delist", "successor_cashout") else None

        # scheduled suspensions
        susp = np.zeros(T, bool)
        i = 5
        while i < T:
            if rng.random() < 0.015:
                L = int(rng.integers(1, 9)); susp[i:i + L] = True; i += L
            i += 1
        if r[0] == "longsusp":
            susp[r[1]:r[1] + 35] = True
        if r[0] == "delist":
            susp[max(0, r[1] - int(rng.integers(0, 12))):r[1]] = True
        rights = None
        if r[0] == "rights":
            R = r[1]
            susp[R - 1:R + 1] = False          # trades on the record date
            susp[R + 1:R + 7] = True           # payment period and settlement: suspended
            susp[R + 7] = False
            rights = {"R": R, "ex": R + 7, "rho": float(rng.choice([0.2, 0.3])), "disc": float(rng.uniform(0.6, 0.85))}

        # distributions: ex-days
        dist_days = {}
        if r[0] != "successor" or True:
            for _ in range(int(rng.integers(1, 4))):
                e = int(rng.integers(8, T - 3))
                if rights and rights["R"] < e <= rights["ex"]:
                    continue
                if delist_i is not None and e >= delist_i:
                    continue
                dist_days[e] = (float(rng.choice([0.0, 0.01, 0.02, 0.03])),
                                float(rng.choice([1.0, 1.0, 1.3, 2.0, 0.5, 1.05])))

        for i in range(T):
            if delist_i is not None and i >= delist_i:
                break
            st[i] = st_from is not None and i >= st_from
            # corporate actions effective today change the reference price (exchange formula)
            if i in dist_days:
                gfrac, phi = dist_days[i]
                g = _r2(gfrac * ref)
                if g == 0.0 and phi == 1.0:
                    g = 0.01
                if ref - g <= 0.02:
                    g = 0.0
                    if phi == 1.0:
                        phi = 1.3
                pay = days[min(T - 1, i + int(rng.integers(0, 4)))] if rng.random() < 0.6 else None
                events.append(Event(code, "dist", ex_date=days[i],
                                    record_date=days[i - 1] if rng.random() < 0.5 else None,
                                    gross_cash=g, phi=phi, pay_date=pay))
                ref = max(0.01, _r2((ref - g) / phi))
            if rights and i == rights["ex"]:
                ref = max(0.01, _r2((ref + rights["rho"] * rights["P_r"]) / (1 + rights["rho"])))
            if r[0] == "unsupported" and i == r[1]:
                events.append(Event(code, "unsupported", ex_date=days[i]))
            roll = rng.random()
            if roll < 0.003 and i > 3 and not (rights and i == rights["R"]):
                continue                                   # 'X': no row at all
            has[i] = True
            pc[i] = ref
            if susp[i]:
                ft[i] = False; op[i] = cl[i] = 999.0       # vendor carry-forward row: never a value
                continue
            ft[i] = True
            if roll < 0.008 and i > 3 and not (rights and i == rights["R"]):
                op[i] = cl[i] = ref                        # 'N': flagged trading, zero volume
                continue
            vp[i] = True
            up, dn = rc.limit_prices(repr(ref), rc.price_band(days[i], board, bool(st[i])))
            up, dn = float(up), float(dn)
            u = rng.random()
            band = float(rc.price_band(days[i], board, bool(st[i])))
            if u < 0.05:
                o = up
            elif u < 0.10:
                o = dn
            else:
                o = min(up, max(dn, _r2(ref * (1 + rng.normal(0, band / 4)))))
            o = max(o, 0.01)
            c = min(up, max(dn, _r2(o * (1 + rng.normal(0, band / 4)))))
            c = max(c, 0.01)
            op[i] = o
            am[i] = adv_scale * float(np.exp(rng.normal(0, 0.4)))
            if rng.random() < 0.004:
                cl[i] = np.nan                             # K3: close missing on a traded day
                last_close = o
            else:
                cl[i] = c
                last_close = c
            ref = last_close
            if rights and i == rights["R"]:
                rights["P_r"] = _r2(max(0.01, rights["disc"] * last_close))
                events.append(Event(code, "rights", ex_date=days[rights["ex"]], record_date=days[i],
                                    rights_price=rights["P_r"], rights_ratio=rights["rho"]))
        if r[0] in ("cashout", "successor_cashout"):
            events.append(Event(code, "cashout", ex_date=days[r[1]], cash_per_share=_r2(max(0.01, last_close * 1.05))))
        carry_until = None
        if r[0] == "exchange":
            events.append(Event(code, "exchange", ex_date=days[r[1] + r[3]], successor=r[2], ratio=0.8))
            carry_until = r[1] + r[3] if r[3] > 0 else None
        secs[code] = Sec(code, op, cl, pc, am, has, ft, vp, st, delist_i, carry_until_i=carry_until)
    mk = Market(days, secs, events)
    mk.synth_roles = role
    return mk


def make_plans(market: Market, seed: int, K: int, start_i: int, end_i: int, late_start_B: int = 6):
    """Random nomination plans for a baseline B and a gated strategy G on one market.
    G's list is a random thinning of B's plus a few other names, with scales in {0.5, 1};
    G skips some days; B starts `late_start_B` days after G so that there are intervals with
    zero baseline exposure and positive gated exposure.  Nominations use day t-1 status only."""
    rng = np.random.default_rng(seed + 7919)
    codes = sorted(market.secs)
    planB, planG, nomB = {}, {}, {}
    # names about to be absorbed are nominated on the three days before they leave the bar
    # file, so that lots are held across the succession (coverage of task ENG-11 (c))
    boost: dict = {}
    for c, r in getattr(market, "synth_roles", {}).items():
        if r[0] == "exchange":
            for i in range(r[1] - 3, r[1]):
                boost.setdefault(i, []).append(c)
    for i in range(start_i, end_i + 1):
        cand = [c for c in codes if market.status(c, i - 1) == "T"]
        if len(cand) == 0:
            continue
        b = list(rng.choice(cand, size=min(K, len(cand)), replace=False))
        forced = [c for c in boost.get(i, []) if c in cand]
        for c in forced:
            if c not in b:
                b = [c] + b[:max(0, K - 1)]
        nomB[i] = b
        if i >= start_i + late_start_B and rng.random() > 0.05:
            planB[i] = [(c, 1.0) for c in b]
        if rng.random() > 0.15:
            g = [c for c in b if rng.random() < 0.6 or c in forced]
            extra = [c for c in cand if c not in b]
            if extra and rng.random() < 0.5:
                g += list(rng.choice(extra, size=min(2, len(extra)), replace=False))
            g = g[:K]
            planG[i] = [(c, float(rng.choice([0.5, 1.0]))) for c in g]
    return planG, planB, nomB

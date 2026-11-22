"""Deployment backtests of the pilot: each method's daily plan through the engine (simulate.run: H+1
sleeves, quantities fixed at the limit-up price, synthetic fill SF, LP exits, benchmark-price ledger),
then the return-based track (A) for the reconciliation R2 and for the Lemma 3 attribution, and the
monitoring counts.  Every number comes from the engine; nothing about fills or costs is re-coded here.

Reconciliations computed for every run (PLAN 3.9): R2 (track (A) against the ledger, daily and
cumulative; monitor.r2_report), cost total against the sum of lot costs, the turnover identity
TO - net - non-netting = 0, and an independent terminal-wealth recomputation from the trade records
(engine/tests/naive.py).  Lemma 3 (R1) residuals are computed by the caller (attribution of G vs G0).
"""
from __future__ import annotations

import importlib.util
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from engine import monitor, simulate
from engine.attribution import ReturnTrack, periods_from_track

_NAIVE = None


def _naive():
    global _NAIVE
    if _NAIVE is None:
        p = Path(__file__).resolve().parents[1] / "engine" / "tests" / "naive.py"
        sys.path.insert(0, str(p.parent))
        spec = importlib.util.spec_from_file_location("naive_recon", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _NAIVE = mod
    return _NAIVE


def theorem1(n_by_day: dict, K_T: int, P_T: int, N_T: int, d: int, delta: float) -> dict:
    """Theorem 1 (theorems.md) at the end of the window: radii B_T (a) and B*_T (b), intervals.
    Lanes are residue classes mod d of the market trading-day index (PLAN 3.3)."""
    c0 = math.pi ** 2 / 6

    def L(k):
        return math.log(2 * d * c0 * (k + 1) ** 2 / delta)

    def b(qv):
        if qv == 0:
            return 0.0
        k = int(math.floor(math.log2(qv)))
        return math.sqrt(2 ** k * L(k))

    def bstar(qv):
        if qv == 0:
            return 0.0
        best, k = math.inf, 0
        while True:
            g = 0.5 * math.sqrt(2 ** k * L(k)) * (1 + qv / 2 ** (k + 1))
            best = min(best, g)
            if 2 ** k > 4 * qv + 4 and k > 3:
                break
            k += 1
        return best
    Q = [0] * d
    for i, n in n_by_day.items():
        Q[i % d] += int(n) ** 2
    B = sum(b(x) for x in Q)
    Bs = sum(bstar(x) for x in Q)
    if N_T == 0:
        return {"N_T": 0, "interval_a": [0.0, 1.0], "interval_b": [0.0, 1.0]}
    return {"N_T": N_T, "K_T": K_T, "P_T": P_T, "B_T": B, "B_star_T": Bs,
            "interval_a": [max(0.0, (K_T - B) / N_T), min(1.0, (K_T + P_T + B) / N_T)],
            "interval_b": [max(0.0, (K_T - Bs) / N_T), min(1.0, (K_T + P_T + Bs) / N_T)],
            "half_width_b": Bs / N_T, "half_width_a": B / N_T, "d": d, "delta": delta}


def run_one(market, ecfg, plan: dict, start_i: int, end_i: int, eval_lo: int, eval_hi: int, name: str,
            delta: float, keep_track: bool = True) -> dict:
    t0 = time.time()
    led, orders = simulate.run(market, ecfg, plan, start_i, end_i, name=name)
    sim_s = time.time() - t0
    rec = simulate.result_record(led, orders, start_i, end_i)
    rec.pop("turnover_daily", None)
    days = list(range(start_i, end_i + 1))
    W = np.array([led.rec[i]["W_close"] for i in days])
    Wp = np.array([led.rec[i]["W_prev_close"] for i in days])
    cost = np.array([led.rec[i]["cost"] for i in days])
    track = ReturnTrack(market, led.val, ecfg)
    tall = [track.day(led, i) for i in days]
    # invested fraction at the close (securities at CV / wealth at the close), every simulated day
    expo = np.array([sum(q * track._p(c, d["i"], "cv") for c, q in led.rec[d["i"]]["s_post"].items())
                     for d in tall]) / W
    tdays = [d for d in tall if eval_lo <= d["i"] <= eval_hi]
    # reconciliations (whole simulated range)
    r2 = monitor.r2_report(track, led, start_i, end_i, ecfg.tol_R2_daily, ecfg.tol_R2_cum, ecfg.W0)
    turnover_id = max((abs(t["TO"] - t["net"] - t["non_netting"]) / ecfg.W0
                       for t in (led.turnover_report(i) for i in days)), default=0.0)
    try:
        naive_rel = abs(_naive().terminal_wealth(market, led, end_i) - led.rec[end_i]["W_close"]) / ecfg.W0
    except AssertionError as e:                 # the naive implementation does not cover every path
        naive_rel = f"not covered: {e}"
    recon = {"R2_daily_rel": r2["R2_daily_rel"], "R2_cum_rel": r2["R2_cum_rel"],
             "R2_days_over_tolerance": len(r2["days_over_tolerance"]), "R3_unexplained": len(r2["unexplained"]),
             "cost_total_vs_lot_costs_rel": abs(led.total_cost() - led.lot_cost_total()) / ecfg.W0,
             "turnover_identity_rel": turnover_id, "naive_vs_ledger_rel": naive_rel}
    # entries and labels by entry day (synthetic fills)
    n_by_day, x1_by_day, x2_by_day = {}, {}, {}
    lots = []
    for l in led.lots:
        n_by_day[l.entry_i] = n_by_day.get(l.entry_i, 0) + 1
        lab = l.label_o1.label if l.label_o1 is not None else None
        if lab is not None:
            x1_by_day[l.entry_i] = x1_by_day.get(l.entry_i, 0) + lab
        if l.label_o2 is not None:
            x2_by_day[l.entry_i] = x2_by_day.get(l.entry_i, 0) + l.label_o2
        net = (l.realised_pnl / l.cost_basis) if (l.realised_pnl is not None and l.cost_basis) else None
        lots.append((l.entry_i, l.code, lab, l.label_o1.outcome if l.label_o1 is not None else "",
                     l.label_o2, net, l.status))
    c1 = monitor.o1_counts([l for l in led.lots if eval_lo <= l.entry_i <= eval_hi], eval_hi)
    thm = theorem1({i: n for i, n in n_by_day.items() if eval_lo <= i <= eval_hi}, c1["K_T"], c1["P_T"], c1["N_T"],
                   ecfg.H + 1, delta)
    out = {"name": name, "start_i": start_i, "end_i": end_i, "W_close": W, "W_prev": Wp, "cost": cost,
           "exposure": expo, "orders_by_day": simulate.order_summary(orders)["by_day"],
           "order_totals": simulate.order_summary(orders)["total"], "n_by_day": n_by_day, "x1_by_day": x1_by_day,
           "x2_by_day": x2_by_day, "lots": lots, "monitor": c1, "theorem1": thm, "recon": recon,
           "result_record": rec, "sim_seconds": round(sim_s, 2), "total_seconds": round(time.time() - t0, 2)}
    if keep_track:
        scale = {d["i"]: led.rec[d["i"]]["W_prev_close"] for d in tdays}
        periods, C = periods_from_track(tdays, scale)
        out["periods"], out["C_norm"] = compact_periods(periods), C
    return out


def compact_periods(periods: list) -> list:
    """Lemma 3 periods as arrays (kind, i, codes, h, x, in_h, in_x) - memory-light; `expand_periods`
    restores the dict form of engine.attribution exactly (same floats)."""
    out = []
    for kind, i, h, x in periods:
        codes = sorted(set(h) | set(x))
        out.append((kind, i, codes, np.array([h.get(c, np.nan) for c in codes]),
                    np.array([x.get(c, np.nan) for c in codes]), [c in h for c in codes], [c in x for c in codes]))
    return out


def expand_periods(cp: list) -> list:
    out = []
    for kind, i, codes, h, x, inh, inx in cp:
        out.append((kind, i, {c: float(v) for c, v, f in zip(codes, h, inh) if f},
                    {c: float(v) for c, v, f in zip(codes, x, inx) if f}))
    return out


_W: dict = {}


def _init(market, ecfg):
    _W.update(market=market, ecfg=ecfg)


def _work(job):
    plan, start_i, end_i, eval_lo, eval_hi, name, delta = job[:7]
    keep = job[7] if len(job) > 7 else True
    return run_one(_W["market"], _W["ecfg"], plan, start_i, end_i, eval_lo, eval_hi, name, delta, keep)


def run_many(market, ecfg, jobs: list, n_jobs: int) -> list:
    """Jobs: (plan, start_i, end_i, eval_lo, eval_hi, name, delta[, keep_track])."""
    if n_jobs <= 1 or len(jobs) <= 1:
        return [run_one(market, ecfg, *j) for j in jobs]
    with ProcessPoolExecutor(max_workers=min(n_jobs, len(jobs)), initializer=_init, initargs=(market, ecfg)) as ex:
        return list(ex.map(_work, jobs))

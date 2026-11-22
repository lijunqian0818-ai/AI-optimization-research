"""Monitoring counts (PLAN 3.8 (vi); setup A4, A5; I-s8.10) and the R3 listing of PLAN 3.9.

Counts only.  No interval is computed here: the radius of Theorem 1 / Corollary 1.3 is
defined in theory/theorems.md, which governs, and belongs to the analysis layer.

  N_T  executed entries (synthetic fills) with entry day <= T
  O1:  an entry of day t is REVEALED at T iff t + H + 1 <= T - the frozen final value,
       computed from the snapshot of day t + d_label (d_label = H + 1), is recorded in the
       ledger at the start of day t + H + 1; provisional marks are never used and a recorded
       label is never corrected.
       K_T = revealed entries with label 1;  P_T = N_T - revealed.
  Deadline labels (Cor. 1.3, draft): common revealed set J_T = entries with t + D + 1 <= T,
       D = H + deadline_extra;  K^lo_T, K^hi_T over J_T;  P^D_T = N_T - |J_T|.

Every count at T uses only lots with entry day <= T and labels frozen by day T, so a ledger
run through T and a longer run give the same counts (tested by truncation).

The matured-only rate K_T / (N_T - P_T) is covered by no statement of the theory files and
is not computed here.
"""
from __future__ import annotations

from typing import Optional


def o1_counts(lots: list, T: int) -> dict:
    N = K = revealed = 0
    outcome = {"value": 0, "U": 0, "M": 0}
    for lot in lots:
        if lot.entry_i > T:
            continue
        N += 1
        if lot.entry_i + lot.H + 1 <= T:
            if lot.label_o1 is None:
                raise RuntimeError(f"lot {lot.lot_id}: label due at day {lot.entry_i + lot.H + 1} is not recorded")
            revealed += 1
            K += lot.label_o1.label
            outcome[lot.label_o1.outcome] += 1
    return {"T": T, "N_T": N, "K_T": K, "P_T": N - revealed, "revealed": revealed, "outcomes": outcome}


def deadline_counts(lots: list, T: int, deadline_extra: int) -> dict:
    N = J = K_lo = K_hi = S = V = 0
    for lot in lots:
        if lot.entry_i > T:
            continue
        N += 1
        D = lot.H + deadline_extra
        if lot.entry_i + D + 1 <= T:
            if lot.deadline is None:
                raise RuntimeError(f"lot {lot.lot_id}: deadline label due is not recorded")
            J += 1
            K_lo += lot.deadline.lo
            K_hi += lot.deadline.hi
            S += lot.deadline.S
            V += lot.deadline.V
    return {"T": T, "N_T": N, "J_T": J, "K_lo_T": K_lo, "K_hi_T": K_hi, "P_D_T": N - J,
            "sold_by_deadline": S, "certified": V}


def lane(entry_i: int, d: int) -> int:
    """Lane of an entry: residue class mod d of the market trading-day index (PLAN 3.3)."""
    return entry_i % d


def r2_report(track, ledger, start_i: int, end_i: int, tol_daily: float, tol_cum: float, W0: float,
              explain_market=None) -> dict:
    """R2 and R3 of PLAN 3.9 for one strategy.

    R2: |dW^(A)_t - dW^(L)_t| <= tol_daily x W_{t-1} every day; cumulated <= tol_cum x W0.
    R3: every day above the daily tolerance is LISTED and traced to the events of that day on
    the names held overnight or traded (booked events, rights record dates, URS / forced-U /
    date-conflict days, missing rows, delistings, ledger flags).  A day above the tolerance
    with nothing to trace it to is `unexplained`: a failure.  `explain_market` is the market
    whose event table is searched (default: the ledger's)."""
    m = explain_market or ledger.m
    from .market import real_code
    worst, cum, over = 0.0, 0.0, []
    for i in range(start_i, end_i + 1):
        x, r = track.day(ledger, i), ledger.rec[i]
        diff = x["dW_A"] - (r["W_close"] - r["W_prev_close"])
        cum += diff
        rel = abs(diff) / r["W_prev_close"]
        worst = max(worst, rel)
        if rel > tol_daily:
            causes = []
            names = sorted({real_code(c) for c in list(r["s_on"]) + list(r["s_post"])})
            for c in names:
                for ev in m.events_on(c, i):
                    causes.append(f"{c}: {ev.kind} event effective {m.days[i]}")
                for ev in m.rights_of(c):
                    if ev.record_date is not None and i > 0 and ev.record_date == m.days[i - 1]:
                        causes.append(f"{c}: rights record date {ev.record_date}")
                u = m.unclassifiable_on(c, i)
                if u:
                    causes.append(f"{c}: {u}")
                st = m.status(c, i)
                if st in ("X", "D"):
                    causes.append(f"{c}: {'no row' if st == 'X' else 'not listed'} on {m.days[i]}")
            for fi, fc, why in ledger.flags:
                if fi == i:
                    causes.append(f"{fc}: ledger flag: {why}")
            over.append({"i": i, "date": m.days[i].isoformat(), "diff": diff, "rel": rel,
                         "traced_to": causes, "explained": bool(causes)})
    return {"R2_daily_rel": worst, "R2_cum_rel": abs(cum) / W0, "days_over_tolerance": over,
            "unexplained": [d for d in over if not d["explained"]],
            "pass_R2": worst <= tol_daily and abs(cum) / W0 <= tol_cum,
            "pass_R3": all(d["explained"] for d in over)}

"""Independent reconciliation on random synthetic markets (fixed seeds; see SEEDS).

Per seed, two strategies G and B with interleaved entries / holdings / exits in the same
names are run on one market containing suspensions, limit opens, no-trade days, missing
rows, missing closes, dividends, bonus issues, consolidations, rights issues, a cash-out,
a succession, a class-U event and delistings.  Checked:

  naive   terminal wealth from per-lot cash flows (tests/naive.py)  vs  ledger
  R2      return-based track (A) vs share ledger (L), daily and cumulated
  R1      Lemma 3 residual, in yuan and wealth-normalised; three terms vs wealth difference
  trade   share-vector traded amount vs trade records; exactly 0 on days without an order
  fills   SF buy decisions vs an integer-arithmetic re-derivation
  rho     W_end - W_start = Pi + sum rho (W - c) with a non-zero cash return

Added for PLAN v0.7 (task list ENG-1 ... ENG-11, TODO-E6, TODO-E7):
  naive   also under the lot-rounding configuration with the 5-yuan minimum commission, under
          the U33 sensitivity "last traded price" (terminal factor 1) and under 'cap-zero'
  R3      the listing of days over the daily tolerance must be empty
  TO      order-level turnover vs net traded amount vs the non-netting amount; every order's
          cost carried by its lot exactly once
  fills   buy decisions re-derived under the primary cap (20 most recent traded days) and
          under the sensitivity 'cap-zero'
  succ    lots that arrive by succession: at least 5 per seed in at least 3 seeds
The succession roles added to engine/synth.py change the random stream, so the panels of
the five seeds are not the v0.6 panels.

Synthetic markets are not a model of anything; no number here is a performance result.
The test configuration (H=3, K=6) is a test choice, not the plan's H=5, K=30.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date

import numpy as np
from common import run_tests

import naive
from engine import monitor, simulate
from engine.attribution import ReturnTrack, lemma3, periods_from_track
from engine.config import EngineConfig
from engine.market import real_code
from engine.synth import make_market, make_plans

d = date.fromisoformat
CFG = replace(EngineConfig(), H=3, K=6, W0=1.0e7)
T_DAYS, N_NAMES, START_I = 150, 24, 21
# seed, first day of the panel (chosen so that the panels straddle rule boundaries:
# 2013-01-01 dividend tax; 2015-08-01 transfer fee and 2015-09-08 tax timing; 2020-08-24 ChiNext band;
# 2023-08-28 stamp duty; one panel without a boundary)
SEEDS = [(11, "2012-10-08"), (23, "2015-06-01"), (37, "2020-06-01"), (41, "2023-06-01"), (53, "2017-03-01")]
TOL_NAIVE = 1e-9          # relative to W0: numerical error only
_CACHE: dict = {}


def _one_seed(seed: int, start: str) -> dict:
    m = make_market(seed, d(start), T_DAYS, N_NAMES)
    assert m.problems == [], m.problems
    end_i = m.T - 1
    planG, planB, nomB = make_plans(m, seed, CFG.K, START_I, end_i - 1)
    G, oG = simulate.run(m, CFG, planG, START_I, end_i, name="G")
    B, oB = simulate.run(m, CFG, planB, START_I, end_i, name="B")
    out = {"seed": seed, "start": start, "lots_G": len(G.lots), "lots_B": len(B.lots)}

    # ---- naive terminal wealth (also for the two sensitivity fill rules) ----
    worst_naive = 0.0
    for led in (G, B, simulate.run(m, CFG, planG, START_I, end_i, rule="SF-strict")[0],
                simulate.run(m, CFG, planG, START_I, end_i, rule="SF-loose")[0]):
        w_naive = naive.terminal_wealth(m, led, end_i)
        worst_naive = max(worst_naive, abs(w_naive - led.rec[end_i]["W_close"]) / CFG.W0)
    out["naive_vs_ledger_rel"] = worst_naive

    # ---- naive terminal wealth under the v0.7 configurations (ENG-3 (e), TODO-E7, ENG-1) ----
    variants = {"min_commission_lot_rounding": replace(CFG, W0=2.0e5, min_commission=5.0, lot_rounding=True),
                "terminal_factor_1": replace(CFG, terminal_value_U=1.0),
                "cap_zero": replace(CFG, adv_counts_nontraded_days_as_zero=True)}
    out["naive_variants_rel"] = {}
    for vname, vcfg in variants.items():
        worst = 0.0
        for plan in (planG, planB):
            led, _ = simulate.run(m, vcfg, plan, START_I, end_i)
            worst = max(worst, abs(naive.terminal_wealth(m, led, end_i) - led.rec[end_i]["W_close"]) / vcfg.W0)
            if vname == "min_commission_lot_rounding":
                out["min_commission_binding_orders"] = out.get("min_commission_binding_orders", 0) + sum(
                    t["costs"]["commission"] == 5.0 for t in led.trades)
            if vname == "terminal_factor_1":
                out["write_offs_with_value"] = out.get("write_offs_with_value", 0) + sum(
                    l.status == "written_off" and l.proceeds > 0 for l in led.lots)
        out["naive_variants_rel"][vname] = worst
    out["naive_variants_max_rel"] = max(out["naive_variants_rel"].values())

    # ---- R2: track (A) vs ledger (L) ----
    tr = ReturnTrack(m, G.val, CFG)
    days = {"G": [tr.day(G, i) for i in range(START_I, end_i + 1)],
            "B": [tr.day(B, i) for i in range(START_I, end_i + 1)]}
    r2_daily, r2_cum = 0.0, 0.0
    for name, led in (("G", G), ("B", B)):
        cum = 0.0
        for x in days[name]:
            r = led.rec[x["i"]]
            diff = x["dW_A"] - (r["W_close"] - r["W_prev_close"])
            r2_daily = max(r2_daily, abs(diff) / r["W_prev_close"])
            cum += diff
        r2_cum = max(r2_cum, abs(cum) / CFG.W0)
    out["R2_daily_rel"], out["R2_cum_rel"] = r2_daily, r2_cum
    # R3: the listing of days over the tolerance (must be empty here; the path itself is tested
    # in test_v07_rules.test_R3_days_over_tolerance_are_listed_and_traced)
    r3 = [monitor.r2_report(tr, led, START_I, end_i, CFG.tol_R2_daily, CFG.tol_R2_cum, CFG.W0) for led in (G, B)]
    out["R3_days_over_tolerance"] = sum(len(x["days_over_tolerance"]) for x in r3)
    assert all(x["pass_R2"] and x["pass_R3"] for x in r3)

    # ---- R1: Lemma 3 on the two intervals, yuan and wealth-normalised ----
    def fallback(kind, i):
        names = [c for c in nomB.get(i, []) if m.status(c, i) == "T" and m.status(c, i - 1) == "T"
                 and not m.events_on(c, i)]
        return {c: 1.0 / len(names) for c in names} if names else {}
    def full_x(periods):
        res = []
        for kind, i, h, x in periods:
            x = dict(x)
            for c in fallback(kind, i):
                if c not in x:
                    x[c] = tr.x_on(c, i) if kind == "on" else tr.x_id(c, i)
            res.append((kind, i, h, x))
        return res
    pG, cG = periods_from_track(days["G"])
    pB, cB = periods_from_track(days["B"])
    pG, pB = full_x(pG), full_x(pB)
    res = lemma3(pG, pB, cG, cB, fallback)
    wealth_diff = (G.rec[end_i]["W_close"] - CFG.W0) - (B.rec[end_i]["W_close"] - CFG.W0)
    out["R1_residual_rel"] = abs(res["residual"]) / CFG.W0
    out["R1_residual_alt_rel"] = abs(res["residual_alt"]) / CFG.W0
    out["terms_vs_wealth_diff_rel"] = abs(res["sum_terms"] - wealth_diff) / CFG.W0
    out["return_vector_mismatch"] = res["max_return_mismatch"]
    out["zero_baseline_intervals"] = res["zero_baseline_intervals"]
    out["zero_baseline_without_fallback"] = res["zero_baseline_without_fallback"]
    by = res["by_interval"]
    out["interval_sum_check"] = abs((by["on"]["exposure"] + by["id"]["exposure"]) - res["exposure"])
    sG = {i: G.rec[i]["W_prev_close"] for i in range(START_I, end_i + 1)}
    sB = {i: B.rec[i]["W_prev_close"] for i in range(START_I, end_i + 1)}
    nG, ncG = periods_from_track(days["G"], sG)
    nB, ncB = periods_from_track(days["B"], sB)
    resn = lemma3(full_x(nG), full_x(nB), ncG, ncB, fallback)
    ret_diff = sum(G.rec[i]["W_close"] / G.rec[i]["W_prev_close"] - B.rec[i]["W_close"] / B.rec[i]["W_prev_close"]
                   for i in range(START_I, end_i + 1))
    out["R1_normalised_residual_abs"] = abs(resn["residual"])
    out["normalised_terms_vs_return_diff_abs"] = abs(resn["sum_terms"] - ret_diff)

    # ---- trade vector vs trade records; no order => exactly zero ----
    worst_trade, zero_days, ca_zero_days = 0.0, 0, 0
    for led in (G, B):
        recs: dict = {}
        for t in led.trades:
            recs.setdefault(t["i"], {}).setdefault(t["code"], 0.0)
            recs[t["i"]][t["code"]] += t["amount"] if t["side"] == "buy" else -t["amount"]
        for i in range(START_I, end_i + 1):
            r = led.rec[i]
            if i not in recs:
                assert led.traded_amount(i) == 0.0 and r["cost"] == 0.0, (led.name, i, r["trade"])
                zero_days += 1
                if any(m.events_on(real_code(c), i) for c in r["s_on"]):
                    ca_zero_days += 1
                continue
            for c in set(r["trade"]) | set(recs[i]):
                worst_trade = max(worst_trade, abs(r["trade"].get(c, 0.0) - recs[i].get(c, 0.0)) / CFG.W0)
    out["trade_vector_vs_records_rel"] = worst_trade
    out["days_without_order_exact_zero"] = zero_days
    out["of_which_with_corporate_action_on_a_held_name"] = ca_zero_days

    # ---- order-level turnover, net amount, non-netting (v0.7, E-3) ----
    worst_to, nn_days, worst_cost = 0.0, 0, 0.0
    for led in (G, B):
        for i in range(START_I, end_i + 1):
            r = led.turnover_report(i)
            worst_to = max(worst_to, abs(r["TO"] - r["net"] - r["non_netting"]) / CFG.W0)
            assert r["non_netting"] >= 0.0 and r["non_netting_cost"] >= -1e-12
            if r["names_bought_and_sold"] == 0:
                assert r["non_netting"] == 0.0 and r["non_netting_cost"] == 0.0
            else:
                nn_days += 1
        worst_cost = max(worst_cost, abs(led.total_cost() - led.lot_cost_total()) / CFG.W0)
    out["turnover_identity_rel"] = worst_to          # TO - net - non-netting
    out["non_netting_days"] = nn_days
    out["cost_total_vs_lot_costs_rel"] = worst_cost

    # ---- SF buy decisions vs integer-arithmetic re-derivation ----
    n_buy = mism = 0
    for o in oG + oB:
        if o["side"] != "buy" or not o["submitted"]:
            continue
        ok, p_up = naive.sf_buy_decision(m, o["code"], o["i"], o["q"], CFG.cap_fraction, CFG.adv_window)
        n_buy += 1
        if ok != o["filled"] or abs(p_up - o["p_up"]) > 1e-9:
            mism += 1
    out["buy_orders_checked"], out["fill_decision_mismatches"] = n_buy, mism
    cz = replace(CFG, adv_counts_nontraded_days_as_zero=True)
    n_cz = mism_cz = differ = 0
    for plan, base_orders in ((planG, oG), (planB, oB)):
        _, o_cz = simulate.run(m, cz, plan, START_I, end_i)
        for o in o_cz:
            if o["side"] != "buy" or not o["submitted"]:
                continue
            ok, _p = naive.sf_buy_decision(m, o["code"], o["i"], o["q"], CFG.cap_fraction, CFG.adv_window, cap_zero=True)
            n_cz += 1
            mism_cz += ok != o["filled"]
        differ += sum(1 for o in o_cz if o["reason"] == "S3") - sum(1 for o in base_orders if o["reason"] == "S3")
    out["buy_orders_checked_cap_zero"], out["fill_decision_mismatches_cap_zero"] = n_cz, int(mism_cz)
    out["extra_S3_under_cap_zero"] = differ
    summ = {k: simulate.order_summary(o)["total"] for k, o in (("G", oG), ("B", oB))}
    out["order_summary"] = summ
    reasons: dict = {}
    for o in oG + oB:
        key = f'{o["side"]}:{o["reason"]}'
        reasons[key] = reasons.get(key, 0) + 1
    out["order_outcomes"] = reasons

    # ---- non-zero cash return: W_end - W_start = Pi + sum rho (W - c) ----
    rng = np.random.default_rng(seed + 1)
    rho_on, rho_id = rng.uniform(0, 2e-4, m.T), rng.uniform(0, 2e-4, m.T)
    R, _ = simulate.run(m, CFG, planG, START_I, end_i, name="G-rho", rho_on=rho_on, rho_id=rho_id)
    pi, extra = 0.0, 0.0
    for i in range(START_I, end_i + 1):
        x, r = tr.day(R, i), R.rec[i]
        pi += sum(h * (x["x_on"][c] - rho_on[i]) for c, h in x["h_on"].items())
        pi += sum(h * (x["x_id"][c] - rho_id[i]) for c, h in x["h_id"].items()) - r["cost"]
        extra += rho_on[i] * r["W_prev_close"] + rho_id[i] * (r["W_open"] - r["cost"])
    lhs = R.rec[end_i]["W_close"] - CFG.W0
    out["cash_return_recursion_rel"] = abs(lhs - (pi + extra)) / CFG.W0
    # the wrong formula (costs treated as debited at the END of the period) must NOT reconcile as well
    wrong = pi + sum(rho_on[i] * R.rec[i]["W_prev_close"] + rho_id[i] * R.rec[i]["W_open"] for i in range(START_I, end_i + 1))
    out["wrong_formula_gap_rel"] = abs(lhs - wrong) / CFG.W0

    # ---- coverage of branches (counts only) ----
    labs = [l.label_o1 for l in G.lots + B.lots if l.label_o1 is not None]
    out["coverage"] = {"ledger_counts_G": G.counts, "ledger_counts_B": B.counts,
                       "labels": len(labs), "labels_pending": sum(l.label_o1 is None for l in G.lots + B.lots),
                       "label_outcomes": {k: sum(x.outcome == k for x in labs) for k in ("value", "U", "M")},
                       "label_price_branches": {k: sum(x.price_branch == k for x in labs) for k in ("P23", "P4", "P1", "P1R", "cash")},
                       "K3_closes": G.val.counts["K3"], "ledger_flags": len(G.flags) + len(B.flags),
                       "open_at_end": len(G.open_lots()) + len(B.open_lots()),
                       "lot_status": {k: sum(l.status == k for l in G.lots + B.lots)
                                      for k in ("open", "sold", "cashed_out", "written_off")},
                       "ledger_extra_counts_G": G.extra_counts, "ledger_extra_counts_B": B.extra_counts,
                       "lots_by_succession": sum(l.succession_used for l in G.lots + B.lots),
                       "lots_by_succession_then_written_off": sum(l.succession_used and l.status == "written_off"
                                                                 for l in G.lots + B.lots),
                       "deadline_labels": sum(l.deadline is not None for l in G.lots + B.lots),
                       "deadline_certified": sum(l.deadline is not None and l.deadline.V for l in G.lots + B.lots)}
    # labels due must all be frozen
    for l in G.lots + B.lots:
        assert (l.label_o1 is not None) == (l.entry_i + l.H + 1 <= end_i), l.lot_id
        assert (l.deadline is not None) == (l.entry_i + l.H + CFG.deadline_extra + 1 <= end_i), l.lot_id
    for led in (G, B):
        c1 = monitor.o1_counts(led.lots, end_i)
        assert c1["N_T"] == len(led.lots) and c1["P_T"] == sum(l.label_o1 is None for l in led.lots)
        c2 = monitor.deadline_counts(led.lots, end_i, CFG.deadline_extra)
        assert c2["K_lo_T"] <= c2["K_hi_T"] and c2["P_D_T"] == sum(l.deadline is None for l in led.lots)

    # ---- acceptance ----
    assert out["naive_vs_ledger_rel"] <= TOL_NAIVE, out["naive_vs_ledger_rel"]
    assert out["R1_residual_rel"] <= CFG.tol_R1 and out["R1_residual_alt_rel"] <= CFG.tol_R1, out
    assert out["R2_daily_rel"] <= CFG.tol_R2_daily and out["R2_cum_rel"] <= CFG.tol_R2_cum, out
    assert out["terms_vs_wealth_diff_rel"] <= TOL_NAIVE and out["R1_normalised_residual_abs"] <= 1e-10, out
    assert out["normalised_terms_vs_return_diff_abs"] <= 1e-9 and out["return_vector_mismatch"] == 0.0, out
    assert out["trade_vector_vs_records_rel"] <= 1e-12 and out["fill_decision_mismatches"] == 0, out
    assert out["cash_return_recursion_rel"] <= TOL_NAIVE, out["cash_return_recursion_rel"]
    assert out["naive_variants_max_rel"] <= TOL_NAIVE, out["naive_variants_rel"]
    assert out["turnover_identity_rel"] <= 1e-12 and out["cost_total_vs_lot_costs_rel"] <= 1e-12, out
    assert out["fill_decision_mismatches_cap_zero"] == 0 and out["R3_days_over_tolerance"] == 0, out
    _CACHE[seed] = out
    return out


def test_succession_coverage_across_seeds():
    """Task ENG-11 (c): lots that arrive by succession - at least 5 in each of at least 3 seeds."""
    for s, st in SEEDS:
        if s not in _CACHE:
            _one_seed(s, st)
    per = {s: _CACHE[s]["coverage"]["lots_by_succession"] for s, _ in SEEDS}
    wo = {s: _CACHE[s]["coverage"]["lots_by_succession_then_written_off"] for s, _ in SEEDS}
    assert sum(v >= 5 for v in per.values()) >= 3, per
    return {"lots_by_succession_per_seed": per, "of_which_later_written_off_(S-d_of_the_successor)": wo,
            "seeds_with_at_least_5": sum(v >= 5 for v in per.values())}


def _mk(seed, start):
    def t():
        return _one_seed(seed, start)
    t.__name__ = f"test_seed_{seed}_{start}"
    t.__doc__ = f"random market, seed {seed}, panel from {start}"
    return t


TESTS = [_mk(s, st) for s, st in SEEDS] + [test_succession_coverage_across_seeds]

if __name__ == "__main__":
    run_tests("reconcile_random", TESTS, "reconcile_random.json")

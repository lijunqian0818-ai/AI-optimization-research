"""Pipeline-only dry run on the raw files that have landed (v0.7).

READ-ONLY: opens Parquet files under experiments/data/raw; contacts no data source; writes only
its own JSON under results/engine_tests.  The full pull is still running: bar files modified
within the last FRESH_MINUTES minutes are not opened (the fetch process may be writing them),
and a file that cannot be read is listed and skipped.

Part A - the 20 trial names (the only names with event files): load, rule-calendar coverage,
  the event table of PLAN 3.11 (EV1-EV3 + EV4) and the v0.6 single-source events, the
  candidate filters, the engine end to end, reconciliation, labels, deadline labels, counts.
  The orders come from a mechanical rotation with NO signal (name k is nominated on day i iff
  (k + i) % 4 == 0 and it is in the candidate set C_i).
Part B - every bar file that has landed: load (bars only), loader checks, the universe screen
  U-LIQ by month, candidate counts, a truncation check of the screen on real data.  The
  landed files are a PART of the market (the pull goes through the work list in code order),
  so the membership counts describe that part only.

NO performance figure is written or printed: only field checks, counts and reconciliation
residuals.  No return, label rate or wealth figure leaves this module.
"""
from __future__ import annotations

import json
import time
import traceback
from datetime import date
from decimal import Decimal

import numpy as np

from common import OUT, ROOT

import naive
from engine import dispositions as disp
from engine import event_table as et
from engine import fills, monitor, simulate
from engine import rule_calendar as rc
from engine import universe as uni
from engine.attribution import ReturnTrack
from engine.config import EngineConfig, conventions_hash
from engine.io_baostock import load_market
from engine.market import Market, Sec

RAW = ROOT / "experiments" / "data" / "raw"
TRIAL = ROOT / "experiments" / "results" / "data_fetch" / "trial_codes.txt"
CFG = EngineConfig()
# PLAN v0.8 C-8 and the lead's constraint for the pilot round: no raw row after 2021-12-31 is read,
# also in this dry run (v0.8 rerun; the v0.7 run read the whole landed window)
from engine.datacut import PILOT_CUTOFF as DATA_CUTOFF  # noqa: E402
FRESH_MINUTES = 15


def trial_codes() -> list[str]:
    out = []
    for line in TRIAL.read_text(encoding="utf-8").splitlines():
        s = line.split("#")[0].strip()
        if s:
            out.append(("sh." if s.startswith("6") else "sz.") + s)
    return out


def calendar_coverage(m) -> dict:
    rep = {"boards": {}, "unclassifiable_codes": [], "calendar_errors": [], "rows_checked": 0,
           "open_above_P_up": [], "open_below_P_down": [], "open_equal_P_up": 0, "open_equal_P_down": 0,
           "open_not_on_cent_grid": 0, "preclose_not_on_cent_grid": 0, "st_rows_by_board": {}}
    for dt in m.days:                                   # cost / tax look-ups on every panel day
        try:
            rc.stamp_duty(dt); rc.transfer_fee(dt, "sh"); rc.transfer_fee(dt, "sz"); rc.dividend_tax(dt)
            rc.commission_bounds(dt)
        except rc.CalendarError as e:
            rep["calendar_errors"].append(f"{dt}: {e}")
    for code, s in m.secs.items():
        try:
            board = rc.board_of(code); rc.exchange_of(code)
        except rc.CalendarError as e:
            rep["unclassifiable_codes"].append(f"{code}: {e}")
            continue
        rep["boards"][code] = board + (" (prefix classification unverified)" if code[:6] in rc.BOARD_PREFIX_UNVERIFIED else "")
        for i in range(m.T):
            if not s.has_row[i] or not (s.preclose[i] > 0):
                continue
            pc = Decimal(repr(float(s.preclose[i])))
            if pc != pc.quantize(Decimal("0.01")):
                rep["preclose_not_on_cent_grid"] += 1
            try:
                up, dn, band = rc.limit_prices_for(code, m.days[i], pc, bool(s.is_st[i]))
            except rc.CalendarError as e:
                rep["calendar_errors"].append(f"{code} {m.days[i]}: {e}")
                continue
            rep["rows_checked"] += 1
            if s.is_st[i]:
                rep["st_rows_by_board"][board] = rep["st_rows_by_board"].get(board, 0) + 1
            if not m.traded(code, i):
                continue
            o = Decimal(repr(float(s.open[i])))
            if o != o.quantize(Decimal("0.01")):
                rep["open_not_on_cent_grid"] += 1
            row = {"code": code, "date": m.days[i].isoformat(), "open": str(o), "preclose": str(pc), "band": str(band)}
            if o > up:
                rep["open_above_P_up"].append(row)
            elif o < dn:
                rep["open_below_P_down"].append(row)
            elif o == up:
                rep["open_equal_P_up"] += 1
            elif o == dn:
                rep["open_equal_P_down"] += 1
    return rep


def ev4_backstop(m) -> dict:
    """Rows whose `preclose` differs from the close of the name's previous row, against the
    single-source (Sina) events.  The plan's rule needs the merged table; this is a pipeline check."""
    steps, matched, unmatched, no_step = 0, 0, [], []
    for code, s in m.secs.items():
        ex_dist = {e.ex_date for e in m.events.get(code, []) if e.kind == "dist"}
        ex_rights = {e.ex_date for e in m.events.get(code, []) if e.kind == "rights" and e.ex_date}
        prev = None
        for i in range(m.T):
            if not s.has_row[i]:
                continue
            if prev is not None:
                step = abs(float(s.preclose[i]) - float(s.close[prev])) > 0.0005
                dt = m.days[i]
                if step:
                    steps += 1
                    if dt in ex_dist or dt in ex_rights:
                        matched += 1
                    else:
                        unmatched.append({"code": code, "date": dt.isoformat(), "prev_close": float(s.close[prev]),
                                          "preclose": float(s.preclose[i]), "prev_row": m.days[prev].isoformat()})
                elif dt in ex_dist:
                    no_step.append({"code": code, "date": dt.isoformat()})
            prev = i
    return {"reference_price_steps": steps, "matched_to_a_sina_event_on_the_same_day": matched,
            "unmatched": unmatched, "dist_events_without_a_step": no_step}


def candidate_plan(m, codes, start_i, end_i):
    """Signal-free rotation restricted to the candidate set C_i (PLAN 2.3; data dated <= i-1)."""
    panel = uni.Panel(m, codes)
    by_month, screens = uni.membership_by_month(panel, CFG)
    order = sorted(codes)
    plan, cnt = {}, {"decision_days": 0, "days_without_membership": 0, "members_sum": 0, "candidates_sum": 0,
                     "removed_listing_age": 0, "removed_suspended": 0, "removed_no_row": 0, "removed_st_lookback": 0,
                     "nominations_before_filter": 0, "nominations": 0}
    for i in range(start_i, end_i):
        dt = m.days[i]
        cnt["decision_days"] += 1
        mem = by_month.get((dt.year, dt.month))
        rot = [c for k, c in enumerate(order) if (k + i) % 4 == 0]
        cnt["nominations_before_filter"] += len(rot)
        if mem is None:
            cnt["days_without_membership"] += 1
            continue
        cands, c = uni.candidates(panel, i, mem, CFG)
        cnt["members_sum"] += c["members"]
        cnt["candidates_sum"] += c["candidates"]
        for k in ("removed_listing_age", "removed_suspended", "removed_no_row", "removed_st_lookback"):
            cnt[k] += c[k]
        cs = set(cands)
        noms = [(c_, 1.0) for c_ in rot if c_ in cs]
        if noms:
            plan[i] = noms
            cnt["nominations"] += len(noms)
    cnt["screen_days"] = len(screens)
    cnt["ever_members"] = len(uni.ever_members(by_month))
    return plan, cnt


def pipeline(m, codes) -> dict:
    rep: dict = {}
    start_i = next(i for i, x in enumerate(m.days) if x >= date(2010, 1, 4))
    end_i = m.T - 1
    plan, crep = candidate_plan(m, codes, start_i, end_i)
    rep["candidate_filter"] = crep
    rep["days"] = end_i - start_i + 1
    rep["nominations"] = sum(len(v) for v in plan.values())
    led, orders = simulate.run(m, CFG, plan, start_i, end_i, name="dryrun")
    reasons: dict = {}
    for o in orders:
        key = f'{o["side"]}:{o["reason"]}'
        reasons[key] = reasons.get(key, 0) + 1
    rep["order_outcomes"] = reasons
    rep["order_summary"] = simulate.order_summary(orders)["total"]
    rep["lots_by_status"] = {k: sum(l.status == k for l in led.lots) for k in ("open", "sold", "cashed_out", "written_off")}
    rep["ledger_event_counts"] = led.counts
    rep["ledger_extra_counts"] = led.extra_counts
    labs = [l.label_o1 for l in led.lots if l.label_o1 is not None]
    rep["labels"] = {"frozen": len(labs), "pending_at_panel_end": sum(l.label_o1 is None for l in led.lots),
                     "outcome": {k: sum(x.outcome == k for x in labs) for k in ("value", "U", "M")},
                     "price_branch": {k: sum(x.price_branch == k for x in labs) for k in ("P23", "P4", "P1", "P1R", "cash")},
                     "P1_by_spell": {"<=20": sum(x.price_branch in ("P1", "P1R") and x.spell <= 20 for x in labs),
                                     "21-60": sum(x.price_branch in ("P1", "P1R") and 20 < x.spell <= 60 for x in labs),
                                     ">60": sum(x.price_branch in ("P1", "P1R") and x.spell > 60 for x in labs)},
                     "why_U_or_M": {}, "on_rows_filled_from_xsrc": sum(x.filled_xsrc for x in labs)}
    for x in labs:
        if x.outcome != "value":
            rep["labels"]["why_U_or_M"][x.why] = rep["labels"]["why_U_or_M"].get(x.why, 0) + 1
    rep["labels"]["M_from_missing_rows"] = sum(v for k, v in rep["labels"]["why_U_or_M"].items() if "bar row" in k)
    # deadline labels and monitoring counts (counts of labels, not rates)
    dls = [l.deadline for l in led.lots if l.deadline is not None]
    rep["deadline_labels"] = {"frozen": len(dls), "pending_at_panel_end": sum(l.deadline is None for l in led.lots),
                              "sold_by_deadline": sum(x.S for x in dls), "certified": sum(x.V for x in dls),
                              "bracket_open_(lo0_hi1)": sum(x.lo == 0 and x.hi == 1 for x in dls),
                              "why_not_certified": {}}
    for x in dls:
        if not x.V:
            rep["deadline_labels"]["why_not_certified"][x.why] = rep["deadline_labels"]["why_not_certified"].get(x.why, 0) + 1
    c1 = monitor.o1_counts(led.lots, end_i)
    c2 = monitor.deadline_counts(led.lots, end_i, CFG.deadline_extra)
    rep["monitor_counts_consistent"] = bool(c1["N_T"] == len(led.lots) and c1["P_T"] == rep["labels"]["pending_at_panel_end"]
                                            and c2["P_D_T"] == rep["deadline_labels"]["pending_at_panel_end"]
                                            and c2["K_lo_T"] <= c2["K_hi_T"])
    rep["ledger_flags"] = {"n": len(led.flags), "by_kind": {},
                           "first": [(m.days[i].isoformat(), c, w) for i, c, w in led.flags[:15]]}
    for _i, _c, w in led.flags:
        k = w.split(":")[0][:60]
        rep["ledger_flags"]["by_kind"][k] = rep["ledger_flags"]["by_kind"].get(k, 0) + 1
    rep["trades_on_flagged_days"] = sum(1 for t in led.trades if t["flag"])
    rep["K3_closes"] = led.val.counts["K3"]

    # --- counts asked for by the v0.7 task list (counts only) ---
    sells = [o for o in orders if o["side"] == "sell"]
    rep["v07_counts"] = {
        "stale_cap_fills": sum(1 for o in orders if o.get("stale_cap")),
        "fills_with_fewer_than_20_traded_days_in_the_cap_window": sum(1 for o in orders if o["filled"] and o["adv_days"] < CFG.adv_window),
        "sell_orders_not_filled_by_the_cap": sum(1 for o in sells if o["reason"] == "S3"),
        "no_ref": rep["order_summary"]["unsubmitted"].get("no_ref", 0),
        "unsubmitted_by_reason": rep["order_summary"]["unsubmitted"],
        "labels_M_from_missing_rows": rep["labels"]["M_from_missing_rows"],
        "orders_on_rows_filled_from_xsrc": rep["order_summary"]["orders_on_xsrc_rows"]}
    # sensitivity 'cap-zero': how many sell orders the literal v0.6 cap would block (a count of orders)
    led_z, orders_z = simulate.run(m, EngineConfig(adv_counts_nontraded_days_as_zero=True), plan, start_i, end_i)
    rep["v07_counts"]["cap_zero_sell_orders_not_filled_by_the_cap"] = sum(
        1 for o in orders_z if o["side"] == "sell" and o["reason"] == "S3")
    rep["v07_counts"]["cap_zero_sell_orders_with_cap_exactly_zero"] = sum(
        1 for o in orders_z if o["side"] == "sell" and o["reason"] == "S3" and o["adv_days"] > 0
        and fills.adv(m, o["code"], o["i"], EngineConfig(adv_counts_nontraded_days_as_zero=True))[0] == 0.0)
    rep["v07_counts"]["cap_zero_naive_vs_ledger_rel"] = abs(naive.terminal_wealth(m, led_z, end_i) - led_z.rec[end_i]["W_close"]) / CFG.W0

    # --- order-level turnover vs net amount (v0.7, E-3): days and residuals only ---
    nn_days, worst_to = 0, 0.0
    for i in range(start_i, end_i + 1):
        r = led.turnover_report(i)
        nn_days += r["names_bought_and_sold"] > 0
        worst_to = max(worst_to, abs(r["TO"] - r["net"] - r["non_netting"]) / CFG.W0)
    rep["v07_counts"]["non_netting_days"] = int(nn_days)
    rep["turnover_identity_rel"] = worst_to
    rep["cost_total_vs_lot_costs_rel"] = abs(led.total_cost() - led.lot_cost_total()) / CFG.W0

    # --- reconciliation residuals (no wealth figure leaves this function) ---
    w_naive = naive.terminal_wealth(m, led, end_i)
    rep["naive_vs_ledger_rel"] = abs(w_naive - led.rec[end_i]["W_close"]) / CFG.W0
    tr = ReturnTrack(m, led.val, CFG)
    r3 = monitor.r2_report(tr, led, start_i, end_i, CFG.tol_R2_daily, CFG.tol_R2_cum, CFG.W0)
    rep["R2_daily_rel"], rep["R2_cum_rel"] = r3["R2_daily_rel"], r3["R2_cum_rel"]
    rep["R3_days_over_tolerance"] = [{k: x[k] for k in ("date", "rel", "traced_to", "explained")} for x in r3["days_over_tolerance"]]
    rep["R2_pass"], rep["R3_pass"] = r3["pass_R2"], r3["pass_R3"]
    recs: dict = {}
    for t in led.trades:
        recs.setdefault(t["i"], {}).setdefault(t["code"], 0.0)
        recs[t["i"]][t["code"]] += t["amount"] if t["side"] == "buy" else -t["amount"]
    worst_trade, zero_days, nonzero_no_order = 0.0, 0, 0
    for i in range(start_i, end_i + 1):
        r = led.rec[i]
        if i not in recs:
            zero_days += 1
            if led.traded_amount(i) != 0.0 or r["cost"] != 0.0:
                nonzero_no_order += 1
            continue
        for c in set(r["trade"]) | set(recs[i]):
            worst_trade = max(worst_trade, abs(r["trade"].get(c, 0.0) - recs[i].get(c, 0.0)) / CFG.W0)
    rep["trade_vector_vs_records_rel"] = worst_trade
    rep["days_without_order"] = zero_days
    rep["days_without_order_but_nonzero_trade_or_cost"] = nonzero_no_order
    n_buy = mism = 0
    examples = []
    for o in orders:
        if o["side"] != "buy" or not o["submitted"]:
            continue
        ok, p_up = naive.sf_buy_decision(m, o["code"], o["i"], o["q"], CFG.cap_fraction, CFG.adv_window)
        n_buy += 1
        if ok != o["filled"] or abs(p_up - o["p_up"]) > 1e-9:
            mism += 1
            if len(examples) < 10:
                examples.append({"code": o["code"], "date": m.days[o["i"]].isoformat(), "engine": o["reason"],
                                 "engine_p_up": o["p_up"], "naive_filled": ok, "naive_p_up": p_up})
    rep["buy_orders_rechecked"], rep["fill_decision_mismatches"], rep["mismatch_examples"] = n_buy, mism, examples
    rep["orders_above_exchange_max_size"] = sum(
        1 for o in orders if o["q"] > rc.lot_rule(m.days[o["i"]], rc.board_of(o["code"]))["max_order"])
    # delistings without a row in the disposition table (PLAN 3.11 rule 11)
    return rep, led


def landed_bar_codes() -> tuple[list, dict]:
    """Codes whose bar file has landed and is not being written (mtime older than FRESH_MINUTES)."""
    now = time.time()
    codes, fresh = [], []
    for f in sorted((RAW / "bars" / "bs_daily").glob("*.parquet")):
        if now - f.stat().st_mtime < FRESH_MINUTES * 60:
            fresh.append(f.stem)
        else:
            codes.append(f.stem)
    return codes, {"bar_files_found": len(codes) + len(fresh), "skipped_recently_modified": fresh,
                   "fresh_minutes": FRESH_MINUTES}


def part_b() -> dict:
    """All landed bar files: loader checks, universe screen, candidate counts, truncation check."""
    codes, info = landed_bar_codes()
    out: dict = {"files": info}
    t0 = time.time()
    m, rep = load_market(RAW, codes, events="none", data_cutoff=DATA_CUTOFF)
    out["load_seconds"] = round(time.time() - t0, 1)
    cr = rep["codes"]
    loaded = [c for c in codes if c in m.secs]

    def tot(key):
        return int(sum(cr[c].get(key, 0) for c in loaded))
    out["load"] = {
        "names_loaded": len(loaded), "problems": rep["problems"][:20], "n_problems": len(rep["problems"]),
        "rows": tot("rows"), "traded_days": tot("traded_days"), "suspended_flag_days": tot("suspended_flag_days"),
        "empty_volume_rows": tot("empty_volume_rows"), "st_days": tot("st_days"),
        "flag_suspended_with_volume": tot("flag_suspended_with_volume"),
        "flag_trading_zero_volume": tot("flag_trading_zero_volume"),
        "traded_open_missing_or_nonpositive": tot("traded_open_missing_or_nonpositive"),
        "traded_close_missing_or_nonpositive": tot("traded_close_missing_or_nonpositive"),
        "row_preclose_missing_or_nonpositive": tot("row_preclose_missing_or_nonpositive"),
        "duplicate_dates": tot("duplicate_dates"), "rows_filled_from_xsrc": tot("rows_filled_from_xsrc"),
        "names_with_rows_off_calendar": sum(1 for c in loaded if cr[c]["rows_off_calendar"]),
        "names_with_missing_days_inside_span": sum(1 for c in loaded if cr[c]["missing_days_inside_span"]),
        "missing_days_inside_span": int(sum(len(cr[c]["missing_days_inside_span"]) for c in loaded)),
        "missing_days_examples": [(c, cr[c]["missing_days_inside_span"][:3]) for c in loaded if cr[c]["missing_days_inside_span"]][:10],
        "adjustflag_values": sorted({v for c in loaded for v in cr[c]["adjustflag_values"]}),
        "tradestatus_values": sorted({v for c in loaded for v in cr[c]["tradestatus_values"]}),
        "isST_values": sorted({v for c in loaded for v in cr[c]["isST_values"]}),
        "delisted_names": sum(1 for c in loaded if m.secs[c].delist_i is not None),
        "names_with_rows_on_or_after_outDate": sum(1 for c in loaded if cr[c].get("rows_on_or_after_outDate")),
        "names_by_board": {}, "unclassifiable_codes": []}
    for c in loaded:
        try:
            b = rc.board_of(c)
            out["load"]["names_by_board"][b] = out["load"]["names_by_board"].get(b, 0) + 1
        except rc.CalendarError:
            out["load"]["unclassifiable_codes"].append(c)
    # EV4 backstop on bars alone: number of reference-price steps (no event file exists for these names)
    steps = after_gap = 0
    for c in loaded:
        st = et.ev4_steps(m, c)
        steps += len(st)
        after_gap += sum(1 for v in st.values() if v["after_missing_row"])
    out["ev4"] = {"reference_price_steps": steps, "of_which_after_a_missing_row": after_gap}
    # delisting dispositions: no table -> every delisting falls back to class U
    out["dispositions"] = {k: (len(v) if isinstance(v, list) else v) for k, v in rep["dispositions"].items()
                           if k in ("delisted_names", "no_row", "errors", "fallback_sentence_required")}
    out["dispositions"]["table_problems"] = rep["dispositions"]["table_problems"]

    # ---- universe screen (PLAN 2.3) ----
    t0 = time.time()
    panel = uni.Panel(m, loaded)
    out["universe"] = {}
    for n_u in (CFG.universe_size, 300):
        cfg = EngineConfig(universe_size=n_u)
        by_month, screens = uni.membership_by_month(panel, cfg)
        sizes = [len(v) for v in by_month.values()]
        elig = [r["eligible"] for r in screens if "note" not in r]
        key = f"N_U={n_u}"
        out["universe"][key] = {
            "screen_days": len(screens), "months_with_membership": len(by_month),
            "members_min_median_max": [int(np.min(sizes)), float(np.median(sizes)), int(np.max(sizes))] if sizes else None,
            "eligible_min_median_max": [int(np.min(elig)), float(np.median(elig)), int(np.max(elig))] if elig else None,
            "ever_members": len(uni.ever_members(by_month)),
            "first_and_last_screen": [screens[0], screens[-1]] if screens else None}
        if n_u == 300:
            # candidate counts on the first decision day of each month
            cc = {"decision_days_sampled": 0, "members": 0, "candidates": 0, "removed_listing_age": 0,
                  "removed_suspended": 0, "removed_no_row": 0, "removed_st_lookback": 0}
            seen = set()
            for i, dt in enumerate(m.days):
                if i < 1 or (dt.year, dt.month) in seen or (dt.year, dt.month) not in by_month:
                    continue
                seen.add((dt.year, dt.month))
                _c, c = uni.candidates(panel, i, by_month[(dt.year, dt.month)], cfg)
                cc["decision_days_sampled"] += 1
                for k in ("members", "candidates", "removed_listing_age", "removed_suspended", "removed_no_row", "removed_st_lookback"):
                    cc[k] += c[k]
            out["universe"][key]["candidate_counts_first_day_of_month"] = cc
            # truncation on real data: junk after the screen day must not change the membership
            rng = np.random.default_rng(0)
            sd = [s for s in uni.screen_days(m.days) if s >= 400]
            checks = 0
            for s_i in (sd[10], sd[len(sd) // 2], sd[-3]):
                secs = {}
                for c in loaded:
                    s_ = m.secs[c]

                    def junk(arr, is_bool):
                        o = arr.copy()
                        k = len(o) - s_i - 1
                        o[s_i + 1:] = (rng.random(k) < 0.5) if is_bool else rng.uniform(0.5, 1e9, k)
                        return o
                    secs[c] = Sec(c, junk(s_.open, False), junk(s_.close, False), junk(s_.preclose, False),
                                  junk(s_.amount, False), junk(s_.has_row, True), junk(s_.flag_trading, True),
                                  junk(s_.vol_pos, True), junk(s_.is_st, True),
                                  s_.delist_i if (s_.delist_i is not None and s_.delist_i <= s_i) else None,
                                  listed_days_before_panel=s_.listed_days_before_panel)
                same = uni.members(uni.Panel(Market(m.days, secs), loaded), s_i, cfg)[0] == uni.members(panel, s_i, cfg)[0]
                checks += 1
                if not same:
                    out["universe"].setdefault("truncation_failures", []).append(m.days[s_i].isoformat())
            out["universe"]["truncation_checks"] = checks
            out["universe"]["truncation_failures"] = out["universe"].get("truncation_failures", [])
    out["universe_seconds"] = round(time.time() - t0, 1)
    out["note"] = ("the landed bar files are a part of the market in work-list order; membership counts describe "
                   "that part only and are not the universe of the plan")
    return out


def main() -> dict:
    t0 = time.time()
    out: dict = {"what": "pipeline-only dry run on landed raw files; no performance figure is reported",
                 "config": "EngineConfig defaults (plan placeholders)", "conventions_hash": conventions_hash(),
                 "config_hash": CFG.kappa_hash()}
    codes = trial_codes()
    out["codes"] = codes
    # ---------------- Part A: the 20 trial names ----------------
    try:
        m, load_rep = load_market(RAW, codes, events="merged", pending="U", data_cutoff=DATA_CUTOFF)
        out["load"] = load_rep
        out["calendar"] = calendar_coverage(m)
        tab = load_rep["event_table"]
        out["event_table_summary"] = {"hash": tab["hash"], "counts": tab["counts"], "by_year_keys": len(tab["by_year"]),
                                      "hand_check_by_kind": {}, "urs": len(tab["urs"]),
                                      "u_spans": sum(len(v) for v in tab["u_spans"].values())}
        for h in tab["hand_check"]:
            k = h["kind"]
            out["event_table_summary"]["hand_check_by_kind"][k] = out["event_table_summary"]["hand_check_by_kind"].get(k, 0) + 1
    except Exception:
        out["load_error"] = traceback.format_exc()
        m = None
    if m is not None:
        try:
            have = [c for c in codes if c in m.secs]
            rep_m, led_m = pipeline(m, have)
            rep_m["dispositions_affected"] = disp.affected_lots([led_m], out["load"]["dispositions"])
            out["pipeline"] = rep_m                              # event table of PLAN 3.11, pending rule 'U'
            # the same pipeline with the v0.6 single-source events (Sina), with the v0.7 status filter
            m_s, rep_s = load_market(RAW, codes, events="sina", data_cutoff=DATA_CUTOFF)
            out["sina_single_source"] = {"events": rep_s["events"], "event_problems": rep_s["event_problems"],
                                         "ev4": ev4_backstop(m_s)}
            rep_p, led_p = pipeline(m_s, have)
            out["pipeline_sina_single_source"] = rep_p
            # the event table with provisional booking of unconfirmed events (dry-run only)
            m_p, rep_pp = load_market(RAW, codes, events="merged", pending="provisional", data_cutoff=DATA_CUTOFF)
            rep_v, _ = pipeline(m_p, have)
            out["pipeline_merged_provisional"] = rep_v
            out["event_table_provisional_counts"] = rep_pp["event_table"]["counts"]
        except Exception:
            out["pipeline_error"] = traceback.format_exc()
    # ---------------- Part B: every landed bar file ----------------
    try:
        out["all_landed_bars"] = part_b()
    except Exception:
        out["part_b_error"] = traceback.format_exc()
    out["seconds"] = round(time.time() - t0, 1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "dryrun_real_data.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    return out


if __name__ == "__main__":
    o = main()
    print("codes:", len(o["codes"]), "seconds:", o["seconds"])
    for k in ("load_error", "pipeline_error", "part_b_error"):
        if k in o:
            print(k.upper())
            print(o[k])
    if "event_table_summary" in o:
        print("event table:", json.dumps(o["event_table_summary"], ensure_ascii=True)[:3000])
    for key in ("pipeline", "pipeline_sina_single_source", "pipeline_merged_provisional"):
        if key in o:
            p = o[key]
            print("==", key)
            for k in ("days", "nominations", "candidate_filter", "order_outcomes", "lots_by_status", "ledger_event_counts",
                      "ledger_extra_counts", "v07_counts", "naive_vs_ledger_rel", "R2_daily_rel", "R2_cum_rel", "R2_pass",
                      "R3_pass", "turnover_identity_rel", "cost_total_vs_lot_costs_rel", "trade_vector_vs_records_rel",
                      "days_without_order_but_nonzero_trade_or_cost", "buy_orders_rechecked", "fill_decision_mismatches",
                      "K3_closes", "trades_on_flagged_days", "orders_above_exchange_max_size", "monitor_counts_consistent"):
                print(f"  {k}: {p[k]}")
            print("  labels:", json.dumps(p["labels"], ensure_ascii=True))
            print("  deadline labels:", json.dumps(p["deadline_labels"], ensure_ascii=True))
            print("  ledger flags:", p["ledger_flags"]["n"], p["ledger_flags"]["by_kind"])
    if "all_landed_bars" in o:
        print("== all landed bars")
        print(json.dumps(o["all_landed_bars"], ensure_ascii=True, default=str)[:6000])
    print("->", OUT / "dryrun_real_data.json")

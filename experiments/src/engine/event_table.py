"""Corporate-event table: merge of the sources EV1-EV3 with the backstop EV4 (PLAN 3.11,
rules 1-12; v0.7 G-1, G-2, E-11; tolerances U56, U61).

This module is mechanical.  It decides nothing case by case: whatever the rules send to
the hand check is LISTED (`hand_check`) and, until a resolution is supplied, treated by the
conservative pending rule stated below.  It reads no price move other than the reference
price step (previous row's close vs `preclose`), and no return.

Sources (per-share units, converted by the readers in io_baostock.py):
  EV1 Eastmoney  EV2 Sina dividend table  EV3 BaoStock dividend table
  EV4 computed here: every row of the bar file whose `preclose` differs from the close of
      the name's previous row.
Rights issues come from the Sina rights table only (rule 5).

Rules implemented (numbers of PLAN 3.11)
  1  key (code, ex-date).  The code-change table (OA9) does not exist yet: codes are NOT
     mapped; the names concerned are those of the bar file.
  2  confirmed  <=> at least two of EV1-EV3 agree on cash per share (ev_tol_cash), share
     ratio (ev_tol_ratio) and record date.
  2a (PLAN v0.8 ruling H-2, task C-1) confirmed by the reference price: a (code, ex-date)
     not confirmed under rule 2 and without duplicate rows of one source is confirmed if
     EXACTLY ONE source value implies, by RC-5 (dividend and share ratio, no rights term),
     a reference price (prev_close - g) / (1 + bonus) within ev_tol_flag (0.005 yuan) of the
     `preclose` of the reference step, and that source's record date is the trading day
     before the ex-date.  Reference step: the EV4 step on the ex-date row; for an ex-date
     without a trade, the first unexplained step at or after it if it lies on the name's
     first traded day after the ex-date (the rule 9 (a) choice).  Booked with that source's
     values, flagged "single source / disagreement, confirmed by the reference price"; the
     reference step is explained by it (once; it is not counted again under rule 9 (a)).
     0 or >= 2 matching sources, no reference step, or a failed record-date relation ->
     pending rule (counted by reason).
  3  one source only, or disagreement, not confirmed by 2a -> pending rule (diagnostic
     hand-check list only, PLAN v0.8).  Two rows of ONE source on the same
     ex-date (the trial files have an exact duplicate row in EV3) are neither merged nor
     de-duplicated: the plan has no rule for them; they go to the hand check as
     "duplicate_rows_in_one_source" (listed in the engine report).
  4  every EV4 step without a matching event -> hand check; unresolved -> list URS.
  5  rights issues: every one goes to the hand-check list (A16).  Rows with a record date or
     an ex-date enter the table; a row without any date does not (rule 10) unless
     `undated_rights="include"` (then PLAN 3.8 (iii) note (10) (b) gives outcome M).
  6  consistency of the amounts with the reference price: |implied reference price -
     `preclose`| above ev_tol_flag is flagged, above ev_tol_hand goes to the hand check.  The
     announced amount is never replaced by a value backed out of `preclose`.
  7  an event whose ex-date lies inside a suspension takes effect on its ex-date.
  8  counts by year and by listed / delisted status; content hash.
  9  date conflicts (G-1): the bar source governs the day on which prices change, the
     announcement governs amounts, ratios and the record date.
       (a) ex-date e on a day without a trade, the first unexplained step at or after e lies
           on the name's first traded day after e and agrees with the event (ev_tol_hand):
           matched; the event stays on e (rule 7), the step is explained.
       (b) any other pair - an event without a step on its ex-date and an unexplained step of
           the same name within ev_pair_window market trading days that agrees with it:
           hand check.  Resolution "event": event kept, step -> URS.  "step": event re-dated
           to the step date.  "undecided": event applied on the step date (record date := the
           trading day before), flagged, outcome U for every entry whose window contains a
           day between the two dates (Market.u_spans).
       (c) an event with no step anywhere and no confirming announcement: not booked; outcome
           U for entries whose window contains its ex-date (Event.forced_class = "U").
     An event whose amounts imply a step smaller than ev_tol_flag needs no step.
 10  implemented events only: status "implemented" AND an ex-date; rows with an ex-date but
     another status go to the hand check.  For S-a / S-b the record date must be the trading
     day before the ex-date; a confirmed event that violates it goes to the hand check and,
     if the announcement shows another relation, is unclassifiable (resolution
     "unclassifiable": outcome U, ledger as for URS).
 11  delisting dispositions: dispositions.py (applied by the caller).
 12  missing rows are repaired by the fetch pipeline, never here; a step whose previous row
     is not the previous market trading day is listed separately ("after a missing row").

PENDING RULE (what the table contains before the hand check is done; conservative, fixed in
advance; the plan prescribes the outcome of the hand check, not the interim state - listed
in the engine report):
  * unconfirmed event (rules 3, 6, 10)      -> forced_class "U" on its ex-date (not booked)
  * date-conflict pair of rule 9 (b)        -> as "undecided"
  * event without any step, rule 9 (c)      -> forced_class "U" (as the rule says)
  * unexplained step, rule 4                -> list URS
`pending="provisional"` books unconfirmed events with the values of the first source in the
order EV1, EV2, EV3 instead; it is the pre-declared EXPLORATORY sensitivity "provisional
booking" (PLAN v0.8 H-2) and never the primary table.  The production configuration is
fixed in config.EngineConfig (event_pending = "U", event_undated_rights = "exclude") and
takes no resolution input (resolutions=None).

Resolutions (the outcome of the hand check), keyed by (code, ex-date ISO string):
  {"status": "announcement", "gross_cash": .., "bonus": .., "record_date": .., "url": ..}
  {"status": "unclassifiable"} | {"status": "reject"}
  {"date": "event" | "step" | "undecided"}
and for a step, keyed by (code, step date ISO string): {"step": "explained"}.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import numpy as np

from .config import EngineConfig
from .market import Event, Market

SOURCES = ("EV1", "EV2", "EV3")


@dataclass
class SrcRow:
    source: str
    code: str
    ex_date: Optional[date]
    record_date: Optional[date]
    gross_cash: float            # yuan per share, before tax
    bonus: float                 # new shares per existing share (phi = 1 + bonus)
    implemented: bool = True
    status: str = ""
    pay_date: Optional[date] = None
    announce_date: Optional[date] = None


@dataclass
class RightsRow:
    code: str
    ratio: Optional[float]       # announced new shares per existing share
    price: Optional[float]
    ex_date: Optional[date]
    record_date: Optional[date]
    announce_date: Optional[date] = None


@dataclass
class EventTable:
    events: list = field(default_factory=list)
    urs: set = field(default_factory=set)
    u_spans: dict = field(default_factory=dict)
    hand_check: list = field(default_factory=list)
    flags: list = field(default_factory=list)
    counts: dict = field(default_factory=dict)
    by_year: dict = field(default_factory=dict)
    steps: dict = field(default_factory=dict)

    def content_hash(self) -> str:
        rows = sorted((e.code, e.kind, str(e.ex_date), str(e.record_date), repr(e.gross_cash), repr(e.phi),
                       str(e.pay_date), repr(e.rights_price), repr(e.rights_ratio), str(e.forced_class),
                       str(e.announce_date)) for e in self.events)
        blob = json.dumps({"events": rows, "urs": sorted((c, str(d)) for c, d in self.urs),
                           "u_spans": {c: [(str(a), str(b), w) for a, b, w in v] for c, v in sorted(self.u_spans.items())}})
        return hashlib.sha256(blob.encode()).hexdigest()

    def install(self, market: Market) -> None:
        """Add the table to a market (events, URS list, undecided date-conflict spans)."""
        for ev in self.events:
            market.add_event(ev)
        market.urs |= set(self.urs)
        for c, v in self.u_spans.items():
            market.u_spans.setdefault(c, []).extend(v)


def ev4_steps(market: Market, code: str, tol: float = 0.0005) -> dict:
    """{row index: {"prev": index of the previous row, "prev_close", "preclose",
    "after_missing_row": bool}} for every row whose `preclose` differs from the close of the
    name's previous row."""
    s = market.secs[code]
    out, prev = {}, None
    last = s.delist_i if s.delist_i is not None else market.T
    for i in range(last):
        if not s.has_row[i]:
            continue
        if prev is not None:
            pc, c = float(s.preclose[i]), float(s.close[prev])
            if np.isfinite(pc) and np.isfinite(c) and abs(pc - c) > tol:
                out[i] = {"prev": prev, "prev_close": c, "preclose": pc, "after_missing_row": prev != i - 1}
        prev = i
    return out


def _prev_row(market: Market, code: str, i: int) -> Optional[int]:
    s = market.secs[code]
    j = i - 1
    while j >= 0:
        if s.has_row[j]:
            return j
        j -= 1
    return None


def _agree(a: SrcRow, b: SrcRow, cfg: EngineConfig) -> bool:
    return (abs(a.gross_cash - b.gross_cash) <= cfg.ev_tol_cash and abs(a.bonus - b.bonus) <= cfg.ev_tol_ratio
            and a.record_date is not None and a.record_date == b.record_date)


def _reference_step(market: Market, code: str, i: int, steps_c: dict, un_c: dict):
    """(index, step) of the reference step of rule 2a, or (None, None): the EV4 step on the
    ex-date row; for an ex-date without a trade, the first unexplained step at or after it if
    that is on the name's first traded day after the ex-date (as in rule 9 (a))."""
    st = steps_c.get(i)
    if st is not None:
        return i, st
    if not market.traded(code, i):
        nxt = next((k for k in range(i + 1, market.T) if market.traded(code, k)), None)
        later = sorted(k for k in un_c if k >= i)
        if nxt is not None and later and later[0] == nxt:
            return nxt, un_c[nxt]
    return None, None


def _rule_2a(market: Market, code: str, i: int, rows: list, steps_c: dict, un_c: dict, cfg: EngineConfig):
    """Rule 2a (PLAN v0.8 H-2).  Returns ((source row, reference step index), "") or
    (None, reason) with reason in {no_reference_step, no_matching_source,
    several_matching_sources, record_date_relation}."""
    k, st = _reference_step(market, code, i, steps_c, un_c)
    if st is None:
        return None, "no_reference_step"
    match = [r for r in rows
             if np.isfinite(r.gross_cash) and np.isfinite(r.bonus) and (1.0 + r.bonus) > 0
             and abs((st["prev_close"] - r.gross_cash) / (1.0 + r.bonus) - st["preclose"]) <= cfg.ev_tol_flag]
    if not match:
        return None, "no_matching_source"
    if len(match) > 1:
        return None, "several_matching_sources"
    r = match[0]
    if i < 1 or r.record_date is None or r.record_date != market.days[i - 1]:
        return None, "record_date_relation"
    return (r, k), ""


def build(market: Market, rows: list, rights: list, cfg: EngineConfig, resolutions: Optional[dict] = None,
          pending: str = "U", undated_rights: str = "exclude", rule_2a: bool = True) -> EventTable:
    """The event table.  `rule_2a=False` reproduces the v0.7 table (tests only: it shows that rule 2a
    changes nothing but the events it confirms); production always uses rule 2a (PLAN v0.8 H-2)."""
    if pending not in ("U", "provisional"):
        raise ValueError(pending)
    if undated_rights not in ("exclude", "include"):
        raise ValueError(undated_rights)
    res = resolutions or {}
    t = EventTable()
    cnt = {"source_rows": len(rows), "rows_not_implemented_without_ex_date": 0, "rows_empty_amounts": 0,
           "rows_other_status_with_ex_date": 0, "rows_implemented_without_ex_date": 0,
           "rows_outside_panel_or_listing": 0, "groups": 0, "confirmed_3_sources": 0, "confirmed_2_sources": 0,
           "single_source": 0, "disagreement": 0, "duplicate_rows_in_one_source": 0,
           "confirmed_by_price_single": 0, "confirmed_by_price_disagreement": 0,
           "rule2a_no_reference_step": 0, "rule2a_no_matching_source": 0, "rule2a_several_matching_sources": 0,
           "rule2a_record_date_relation": 0, "rule2a_step_at_resumption": 0,
           "resolved_by_announcement": 0, "rejected": 0,
           "record_date_violation": 0, "amount_flagged": 0, "amount_hand_check": 0, "no_step_expected": 0,
           "matched_same_day": 0, "conflict_a_matched": 0, "conflict_b_pairs": 0, "conflict_b_event_date": 0,
           "conflict_b_step_date": 0, "conflict_b_undecided_or_pending": 0, "conflict_c_not_booked": 0,
           "conflict_c_confirmed_by_announcement": 0, "booked_dist_events": 0, "forced_U_events": 0,
           "rights_rows": len(rights), "rights_in_table": 0, "rights_undated": 0, "rights_missing_record_date": 0,
           "steps_total": 0, "steps_explained_by_event": 0, "steps_explained_by_rights": 0,
           "steps_urs": 0, "steps_urs_after_missing_row": 0, "steps_resolved_explained": 0,
           "code_change_mapping": "not applied (OA9 table does not exist)"}
    by_year: dict = {}

    def year_count(d: Optional[date], code: str, key: str):
        if d is None:
            return
        delisted = market.secs[code].delist_i is not None
        y = by_year.setdefault(d.year, {})
        k = f"{key}:{'delisted' if delisted else 'listed'}"
        y[k] = y.get(k, 0) + 1

    def hand(code, d, kind, detail):
        t.hand_check.append({"code": code, "date": d.isoformat() if d else None, "kind": kind, "detail": detail})

    # ---------------- rule 10: implemented events only ----------------
    groups: dict = {}
    for r in rows:
        if r.code not in market.secs:
            cnt["rows_outside_panel_or_listing"] += 1
            continue
        if r.ex_date is None:
            if r.implemented:
                cnt["rows_implemented_without_ex_date"] += 1
                hand(r.code, r.announce_date, "implemented_without_ex_date", f"{r.source}: status {r.status!r}")
            else:
                cnt["rows_not_implemented_without_ex_date"] += 1
            continue
        if not r.implemented:
            cnt["rows_other_status_with_ex_date"] += 1
            hand(r.code, r.ex_date, "ex_date_but_not_implemented", f"{r.source}: status {r.status!r}")
            continue
        if not (np.isfinite(r.gross_cash) and np.isfinite(r.bonus)) or (r.gross_cash == 0 and r.bonus == 0):
            cnt["rows_empty_amounts"] += 1
            continue
        i = market.idx.get(r.ex_date)
        s = market.secs[r.code]
        fr = market.first_row(r.code)
        if i is None or fr is None or i <= fr or (s.delist_i is not None and i >= s.delist_i) or not s.has_row[i]:
            cnt["rows_outside_panel_or_listing"] += 1
            if i is not None and fr is not None and fr < i and (s.delist_i is None or i < s.delist_i):
                hand(r.code, r.ex_date, "ex_date_without_bar_row", r.source)
            continue
        groups.setdefault((r.code, r.ex_date), []).append(r)

    # ---------------- EV4 ----------------
    steps = {c: ev4_steps(market, c) for c in market.secs}
    unexplained = {c: dict(v) for c, v in steps.items()}
    cnt["steps_total"] = sum(len(v) for v in steps.values())
    t.steps = steps

    # ---------------- rule 5: rights issues ----------------
    for r in rights:
        if r.code not in market.secs:
            continue
        if r.record_date is None and r.ex_date is None:
            cnt["rights_undated"] += 1
            hand(r.code, r.announce_date, "rights_without_dates", "not in the table" if undated_rights == "exclude"
                 else "in the table: outcome M for entries on or after the announcement date")
            if undated_rights == "exclude":
                continue
        elif r.record_date is None:
            cnt["rights_missing_record_date"] += 1
            hand(r.code, r.ex_date, "rights_without_record_date", "in the table: outcome M inside the window of note (10)")
        else:
            hand(r.code, r.record_date, "rights_issue", "every rights issue is hand-checked (A16)")
        t.events.append(Event(r.code, "rights", ex_date=r.ex_date, record_date=r.record_date, rights_price=r.price,
                              rights_ratio=r.ratio, announce_date=r.announce_date))
        cnt["rights_in_table"] += 1
        year_count(r.record_date or r.ex_date or r.announce_date, r.code, "rights")
        xi = market.idx.get(r.ex_date) if r.ex_date else None
        if xi is not None and xi in unexplained[r.code]:
            del unexplained[r.code][xi]
            cnt["steps_explained_by_rights"] += 1

    # ---------------- rules 2, 3, 6, 10: one candidate per (code, ex-date) ----------------
    cands = []
    for (code, ex), g in sorted(groups.items(), key=lambda z: (z[0][0], z[0][1])):
        cnt["groups"] += 1
        key = (code, ex.isoformat())
        r_ = res.get(key, {})
        by_src: dict = {}
        dup = False
        for r in g:
            if r.source in by_src:
                dup = True
            by_src.setdefault(r.source, r)
        srcs = [s for s in SOURCES if s in by_src]
        pair = None
        if not dup:
            for a in range(len(srcs)):
                for b in range(a + 1, len(srcs)):
                    if _agree(by_src[srcs[a]], by_src[srcs[b]], cfg):
                        pair = pair or (srcs[a], srcs[b])
        all3 = (len(srcs) == 3 and not dup and all(_agree(by_src[srcs[a]], by_src[srcs[b]], cfg)
                                                   for a in range(3) for b in range(a + 1, 3)))
        base = by_src[pair[0]] if pair else by_src[srcs[0]]
        pay = by_src["EV3"].pay_date if "EV3" in by_src else None
        c = {"code": code, "ex": ex, "i": market.idx[ex], "g": base.gross_cash, "bonus": base.bonus,
             "record": base.record_date, "pay": pay, "state": "confirmed", "why": [], "sources": srcs}
        if pair:
            cnt["confirmed_3_sources" if all3 else "confirmed_2_sources"] += 1
            year_count(ex, code, "confirmed_3_sources" if all3 else "confirmed_2_sources")
        else:
            # several rows of ONE source on one ex-date (identical or not) are not merged or
            # de-duplicated here: the plan has no rule for them; they are ineligible for rules
            # 2 and 2a and fall to the pending rule (PLAN v0.8 H-9)
            kind = "duplicate_rows_in_one_source" if dup else ("disagreement" if len(srcs) > 1 else "single_source")
            cnt[kind] += 1
            matched = None
            if not dup and rule_2a:
                matched, why2a = _rule_2a(market, code, c["i"], [by_src[s] for s in srcs], steps[code],
                                          unexplained[code], cfg)
                if matched is None:
                    cnt["rule2a_" + why2a] += 1
            if matched is not None:
                src_row, k_ref = matched
                c.update(g=src_row.gross_cash, bonus=src_row.bonus, record=src_row.record_date,
                         by_price=True, ref_k=k_ref, src_2a=src_row.source,
                         flag="single source / disagreement, confirmed by the reference price")
                key2a = "confirmed_by_price_single" if kind == "single_source" else "confirmed_by_price_disagreement"
                cnt[key2a] += 1
                year_count(ex, code, "confirmed_by_price")
                if k_ref != c["i"]:
                    cnt["rule2a_step_at_resumption"] += 1
            else:
                c["state"] = "unconfirmed"
                c["why"].append(kind)
                hand(code, ex, kind, {s: (by_src[s].gross_cash, by_src[s].bonus, str(by_src[s].record_date)) for s in srcs})
        # rule 10: record date = the trading day before the ex-date
        i = c["i"]
        if c["state"] == "confirmed" and (i < 1 or c["record"] != market.days[i - 1]):
            cnt["record_date_violation"] += 1
            c["state"] = "unconfirmed"
            c["why"].append("record_date_relation")
            hand(code, ex, "record_date_not_the_trading_day_before_the_ex_date", str(c["record"]))
        # rule 6: amounts against the reference price (only where a step exists on the ex-date)
        st = steps[code].get(i)
        if st is not None:
            implied = (st["prev_close"] - c["g"]) / (1.0 + c["bonus"])
            diff = abs(implied - st["preclose"])
            if diff > cfg.ev_tol_hand:
                cnt["amount_hand_check"] += 1
                hand(code, ex, "amount_inconsistent_with_reference_price", round(diff, 4))
                if c["state"] == "confirmed":
                    c["state"] = "unconfirmed"
                c["why"].append("amount_vs_reference_price")
            elif diff > cfg.ev_tol_flag:
                cnt["amount_flagged"] += 1
                t.flags.append({"code": code, "date": ex.isoformat(), "kind": "amount_vs_reference_price", "diff": round(diff, 4)})
        # resolutions of the hand check
        stt = r_.get("status")
        if stt == "announcement":
            c["g"] = float(r_.get("gross_cash", c["g"]))
            c["bonus"] = float(r_.get("bonus", c["bonus"]))
            rd = r_.get("record_date", c["record"])
            c["record"] = date.fromisoformat(rd) if isinstance(rd, str) else rd
            c["state"] = "confirmed"
            cnt["resolved_by_announcement"] += 1
            if i >= 1 and c["record"] != market.days[i - 1]:
                c["state"] = "unclassifiable"       # the announcement itself shows another relation (rule 10)
        elif stt == "unclassifiable":
            c["state"] = "unclassifiable"
        elif stt == "reject":
            cnt["rejected"] += 1
            continue
        cands.append(c)

    # ---------------- same-day steps ----------------
    for c in cands:
        if c["i"] in steps[c["code"]]:
            c["step"] = "same_day"
            cnt["matched_same_day"] += 1
            if c["i"] in unexplained[c["code"]]:        # not already explained by a rights ex-date
                del unexplained[c["code"]][c["i"]]
                cnt["steps_explained_by_event"] += 1

    def book(c, i, record, forced=None, flag=None):
        ev = Event(c["code"], "dist", ex_date=market.days[i], record_date=record, gross_cash=c["g"],
                   phi=1.0 + c["bonus"], pay_date=c["pay"], forced_class=forced)
        t.events.append(ev)
        if forced:
            cnt["forced_U_events"] += 1
            year_count(market.days[i], c["code"], "forced_U")
        else:
            cnt["booked_dist_events"] += 1
            year_count(market.days[i], c["code"], "booked")
        if flag:
            t.flags.append({"code": c["code"], "date": market.days[i].isoformat(), "kind": flag})

    def agrees(c, st) -> bool:
        return abs((st["prev_close"] - c["g"]) / (1.0 + c["bonus"]) - st["preclose"]) <= cfg.ev_tol_hand

    # ---------------- rule 9 and the pending rule ----------------
    for c in cands:
        code, i, ex = c["code"], c["i"], c["ex"]
        key = (code, ex.isoformat())
        r_ = res.get(key, {})
        if c["state"] == "unclassifiable":
            book(c, i, c["record"], forced="U", flag="unclassifiable (hand check)")
            continue
        if c["state"] == "unconfirmed":
            if pending == "U":
                book(c, i, c["record"], forced="U", flag="pending rule: " + ",".join(c["why"]))
                year_count(ex, code, "pending:" + "+".join(c["why"]))
                continue
            c["record"] = market.days[i - 1] if "record_date_relation" in c["why"] else c["record"]
        if c.get("step") == "same_day":
            book(c, i, c["record"], flag=c.get("flag"))
            continue
        if c.get("by_price"):
            # rule 2a with the reference step on the first traded day after an ex-date inside a
            # suspension: the event stays on its ex-date (rule 7) and the step is explained once
            k = c["ref_k"]
            if k in unexplained[code]:
                del unexplained[code][k]
                cnt["steps_explained_by_event"] += 1
            book(c, i, c["record"], flag=c["flag"] + " (step at the resumption)")
            continue
        # no step on the ex-date
        pr = _prev_row(market, code, i)
        prev_close = float(market.secs[code].close[pr]) if pr is not None else float("nan")
        expected = abs(prev_close - (prev_close - c["g"]) / (1.0 + c["bonus"]))
        if np.isfinite(expected) and expected < cfg.ev_tol_flag:
            cnt["no_step_expected"] += 1
            book(c, i, c["record"])
            continue
        un = unexplained[code]
        # (a) ex-date on a day without a trade; step on the first traded day after it
        if not market.traded(code, i):
            later = sorted(k for k in un if k >= i)
            nxt = next((k for k in range(i + 1, market.T) if market.traded(code, k)), None)
            if later and nxt is not None and later[0] == nxt and agrees(c, un[nxt]):
                del un[nxt]
                cnt["conflict_a_matched"] += 1
                cnt["steps_explained_by_event"] += 1
                book(c, i, c["record"], flag="ex-date inside a suspension; reference-price step at the resumption")
                continue
        # (b) another unexplained step of the name within the pairing window that agrees
        near = sorted((abs(k - i), -k, k) for k in un if abs(k - i) <= cfg.ev_pair_window and agrees(c, un[k]))
        if near:
            k = near[0][2]
            cnt["conflict_b_pairs"] += 1
            choice = r_.get("date")
            if choice == "event":
                cnt["conflict_b_event_date"] += 1
                book(c, i, c["record"], flag="date conflict: announcement confirms the event date; step -> URS")
                continue                                   # the step stays unexplained -> URS below
            del un[k]
            cnt["steps_explained_by_event"] += 1
            rec = market.days[k - 1] if k >= 1 else None
            if choice == "step":
                cnt["conflict_b_step_date"] += 1
                book(c, k, rec, flag="date conflict: event re-dated to the step date")
            else:
                cnt["conflict_b_undecided_or_pending"] += 1
                book(c, k, rec, flag="date conflict: applied on the step date"
                     + ("" if choice == "undecided" else " (pending hand check)"))
                lo, hi = (market.days[min(i, k)], market.days[max(i, k)])
                t.u_spans.setdefault(code, []).append((lo, hi, "date conflict between the event source and the bar source"))
                if choice != "undecided":
                    hand(code, ex, "date_conflict", {"step_date": market.days[k].isoformat()})
            continue
        # (c) no step anywhere
        if r_.get("date") == "event" or r_.get("status") == "announcement":
            cnt["conflict_c_confirmed_by_announcement"] += 1
            book(c, i, c["record"], flag="no reference-price step; confirmed by the announcement")
        else:
            cnt["conflict_c_not_booked"] += 1
            hand(code, ex, "event_without_any_step", {"expected_step": round(expected, 4)})
            book(c, i, c["record"], forced="U", flag="no reference-price step and no confirming announcement: not booked")
            year_count(ex, code, "pending:no_step")

    # ---------------- rule 4: what is left of EV4 ----------------
    for code, un in unexplained.items():
        for k, st in sorted(un.items()):
            d = market.days[k]
            if res.get((code, d.isoformat()), {}).get("step") == "explained":
                cnt["steps_resolved_explained"] += 1
                continue
            t.urs.add((code, d))
            if st["after_missing_row"]:
                cnt["steps_urs_after_missing_row"] += 1
                hand(code, d, "step_after_a_missing_row", {"prev_row": market.days[st["prev"]].isoformat()})
            else:
                cnt["steps_urs"] += 1
                hand(code, d, "step_without_event", {"prev_close": st["prev_close"], "preclose": st["preclose"]})
            year_count(d, code, "urs")
    cnt["hand_check_items"] = len(t.hand_check)
    cnt["pending_policy"] = pending
    t.counts, t.by_year = cnt, {str(y): v for y, v in sorted(by_year.items())}
    return t

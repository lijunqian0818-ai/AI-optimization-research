"""Delisting disposition table (PLAN 3.9 "Delisting versus merger"; 3.11 rule 11; v0.7 E-18,
G-3; U62).

A name is "no longer listed" from the market trading day after its last row in the bar file
(Sec.delist_i; the bar source's delisting date is the last day with a row).  What then
happens to a holding is read from a hand-built table, one row per delisted name:

    code, disposition, cash_per_share, ratio, successor, last_trade_date,
    first_trade_date_new, effective_date, url

    disposition in {terminated, cash, exchange, other}

      terminated  termination of listing            -> class U (label 1; ledger value 0, U33)
      cash        cash-only exit on published terms -> S-d (cash_per_share; effective on
                  `effective_date` if given, else on the first day the name is not listed)
      exchange    absorption by share exchange into exactly ONE SSE / SZSE A-share at a
                  published ratio -> S-e, effective on `first_trade_date_new` (the first
                  trading day of the new shares); if that field is empty: on the first day
                  the name is not listed.  The holder is assumed not to exercise a cash
                  option.  Between the delisting and that day the ledger carries the holding at
                  the last value of the absorbed name (flagged); the label follows I-s3: a
                  successor not listed at day t+H gives U.
      other       anything else                     -> class U

FALLBACK, fixed in advance: the table does not exist, or a delisted name has no row ->
class U, written off; the names are listed in the report, and every table that uses the
ledger or O1 must carry the sentence "delistings are written off, including absorptions by
share exchange".  A row that cannot be applied (cash amount or ratio missing or
non-positive, successor not in the bar panel, successor equal to the name itself, dates
before the delisting) is treated as 'other' (class U) and listed under `errors`.

The table is collected by hand (referred to the user, PLAN 17.4 item 1); this module only
reads it.  It contacts no data source.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Optional

from .market import Event, Market

DISPOSITIONS = ("terminated", "cash", "exchange", "other")
COLUMNS = ("code", "disposition", "cash_per_share", "ratio", "successor", "last_trade_date",
           "first_trade_date_new", "effective_date", "url")
# default location (does not exist unless the user decides to collect the table)
DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "manual" / "delisting_dispositions.csv"
SENTENCE = "delistings are written off, including absorptions by share exchange"


def _f(x) -> Optional[float]:
    try:
        s = str(x).strip()
        return float(s) if s else None
    except (TypeError, ValueError):
        return None


def _d(x) -> Optional[date]:
    try:
        s = str(x).strip()
        return date.fromisoformat(s[:10]) if s else None
    except (TypeError, ValueError):
        return None


def read_table(path=None) -> tuple[dict, list]:
    """Returns ({code: row dict}, problems).  A missing file is not an error: ({}, [note])."""
    path = Path(path) if path is not None else DEFAULT_PATH
    if not path.exists():
        return {}, [f"disposition table not found at {path}: every delisting falls back to class U"]
    rows, problems = {}, []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for k, r in enumerate(csv.DictReader(fh), start=2):
            code = (r.get("code") or "").strip()
            disp = (r.get("disposition") or "").strip().lower()
            if not code:
                problems.append(f"line {k}: no code")
                continue
            if disp not in DISPOSITIONS:
                problems.append(f"line {k} ({code}): unknown disposition {disp!r} -> treated as 'other'")
                disp = "other"
            if code in rows:
                problems.append(f"line {k} ({code}): duplicate row -> treated as 'other'")
                rows[code]["disposition"] = "other"
                continue
            rows[code] = {"code": code, "disposition": disp, "cash_per_share": _f(r.get("cash_per_share")),
                          "ratio": _f(r.get("ratio")), "successor": (r.get("successor") or "").strip() or None,
                          "last_trade_date": _d(r.get("last_trade_date")),
                          "first_trade_date_new": _d(r.get("first_trade_date_new")),
                          "effective_date": _d(r.get("effective_date")), "url": (r.get("url") or "").strip()}
    return rows, problems


def apply(market: Market, table: Optional[dict]) -> dict:
    """Turn the table into S-d / S-e events of `market` (in place) and report.

    Returns {"no_row": [...], "terminated": [...], "cash": [...], "exchange": [...],
    "other": [...], "errors": [...], "fallback_sentence_required": bool}."""
    table = table or {}
    rep = {"delisted_names": 0, "no_row": [], "terminated": [], "cash": [], "exchange": [], "other": [],
           "errors": [], "rows_for_names_not_delisted_in_panel": []}
    for code, row in table.items():
        s = market.secs.get(code)
        if s is None or s.delist_i is None:
            rep["rows_for_names_not_delisted_in_panel"].append(code)
    for code in sorted(market.secs):
        s = market.secs[code]
        if s.delist_i is None:
            continue
        rep["delisted_names"] += 1
        d0 = s.delist_i
        row = table.get(code)
        if row is None:
            rep["no_row"].append(code)
            continue
        disp = row["disposition"]
        if disp == "cash":
            cps, eff = row["cash_per_share"], row["effective_date"]
            ei = d0 if eff is None else market.day_index_on_or_after(eff)
            if cps is None or not (cps > 0):
                rep["errors"].append(f"{code}: cash exit without a positive cash amount -> class U")
                rep["other"].append(code)
                continue
            if ei is None or ei < d0:
                rep["errors"].append(f"{code}: cash exit effective {eff} is before the delisting or outside the panel -> class U")
                rep["other"].append(code)
                continue
            if ei > d0:
                s.carry_until_i = ei
            market.add_event(Event(code, "cashout", ex_date=market.days[ei], cash_per_share=cps))
            rep["cash"].append(code)
        elif disp == "exchange":
            succ, ratio, first = row["successor"], row["ratio"], row["first_trade_date_new"]
            if succ is None or succ == code or succ not in market.secs:
                rep["errors"].append(f"{code}: successor {succ!r} is not in the bar panel -> class U")
                rep["other"].append(code)
                continue
            if ratio is None or not (ratio > 0):
                rep["errors"].append(f"{code}: share exchange without a positive ratio -> class U")
                rep["other"].append(code)
                continue
            fi = d0 if first is None else market.day_index_on_or_after(first)
            if fi is None or fi < d0:
                rep["errors"].append(f"{code}: first trading day of the new shares {first} is before the "
                                     f"delisting or outside the panel -> class U")
                rep["other"].append(code)
                continue
            fr = market.first_row(succ)
            sd = market.secs[succ].delist_i
            if fr is None or fr > fi or (sd is not None and sd <= fi):
                rep["errors"].append(f"{code}: successor {succ} is not listed in the bar panel on the first "
                                     f"trading day of the new shares ({market.days[fi]}) -> class U")
                rep["other"].append(code)
                continue
            if fi > d0:
                s.carry_until_i = fi
            market.add_event(Event(code, "exchange", ex_date=market.days[fi], successor=succ, ratio=ratio))
            rep["exchange"].append(code)
        elif disp == "terminated":
            rep["terminated"].append(code)
        else:
            rep["other"].append(code)
    rep["fallback_sentence_required"] = bool(rep["no_row"])
    rep["fallback_sentence"] = SENTENCE
    return rep


def affected_lots(ledgers, report: dict) -> dict:
    """Numbers of lots written off because the name left the bar file without a row in the
    table (to be printed with every table that uses the ledger or O1)."""
    no_row = set(report["no_row"])
    out: dict = {}
    for led in ledgers:
        for lot in led.lots:
            if lot.status == "written_off" and lot.code in no_row and any(
                    e[1] == "U" and e[2] == "no longer listed" for e in lot.log if len(e) >= 3):
                out[lot.code] = out.get(lot.code, 0) + 1
    return {"lots_written_off_without_a_row": sum(out.values()), "by_name": out}

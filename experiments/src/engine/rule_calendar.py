"""Rule calendar (PLAN v0.7 section 3.10), as data rows plus query functions.

ONE calendar for the engine and the feature library (v0.7, E-20, F-20): a second copy of a
band, threshold or regime date anywhere in the code is a defect.

EVERY value and EVERY source status below is transcribed from experiments/PLAN.md
section 3.10 / 3.6 and experiments/rule_verification.md.  The author of this module
opened no rule text and made no judgement about verification.  Status vocabulary
(PLAN 3.10): "verified", "official page", "indirect", "unverified against official
text", "not found".  A row whose value is used inside the sample although part of
its basis is unverified carries the number of the corresponding entry of the PLAN's
list of unverified items (21 entries in v0.7) in `unverified_item`.

Validity window: 2008-01-01 .. 2026-06-30 (raw-data period of the plan).  Queries
outside it raise CalendarError: the 2026 revisions of the Trading Rules (effective
2026-07-06) are not transcribed here except the one row the plan states (RC-6 (b)).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

CAL_START = date(2008, 1, 1)
CAL_END = date(2026, 6, 30)

V = "verified"
OP = "official page"
IND = "indirect"
UNV = "unverified against official text"
NF = "not found"


class CalendarError(ValueError):
    pass


@dataclass(frozen=True)
class Rule:
    rc: str                 # PLAN id, e.g. "RC-15"
    key: str                # lookup key
    start: date             # first day in force (inclusive)
    end: Optional[date]     # last day in force (inclusive); None = through CAL_END
    value: Any
    status: str             # status of the VALUE as used here
    date_status: str        # status of the interval boundary dates
    unverified_item: Optional[int] = None   # index in PLAN 3.10 list (1..21 in v0.7)
    note: str = ""


def _d(s: str) -> date:
    return date.fromisoformat(s)


RULES: list[Rule] = [
    # ---------------- price-limit bands, RC-6 ----------------
    Rule("RC-6(a)", "band:main:0", _d("2008-01-01"), None, "0.10", V, V),
    Rule("RC-6(b)", "band:main:1", _d("2008-01-01"), None, "0.05", V, V,
         note="5% through the end of the sample; 10% from 2026-07-06 (outside the calendar window)"),
    Rule("RC-6(c)", "band:chinext:0", _d("2008-01-01"), _d("2020-08-23"), "0.10", V, OP,
         note="last trading day with 10% is 2020-08-21"),
    Rule("RC-6(c)", "band:chinext:0", _d("2020-08-24"), None, "0.20", V, OP,
         note="date from an official press Q&A"),
    Rule("RC-6(d)", "band:chinext:1", _d("2008-01-01"), _d("2020-08-23"), "0.05", V, OP),
    Rule("RC-6(d)", "band:chinext:1", _d("2020-08-24"), None, "0.20", V, OP,
         note="no separate ST band on ChiNext afterwards"),
    Rule("RC-6(e)", "band:star:0", _d("2008-01-01"), None, "0.20", V, UNV, 9,
         note="launch date 2019-07-22 unverified; STAR names enter with their first bar"),
    Rule("RC-6(e)", "band:star:1", _d("2008-01-01"), None, "0.20", V, UNV, 9,
         note="no 5% band for risk-warning stocks on STAR"),
    # ---------------- stamp duty, RC-15: value = (buy rate, sell rate) ----------------
    Rule("RC-15", "stamp", _d("2008-01-01"), _d("2008-04-23"), (0.003, 0.003), OP, OP,
         note="both sides; precedes the first simulated trade (2010-01-01)"),
    Rule("RC-15", "stamp", _d("2008-04-24"), _d("2008-09-18"), (0.001, 0.001), OP, OP,
         note="both sides"),
    Rule("RC-15", "stamp", _d("2008-09-19"), _d("2023-08-27"), (0.0, 0.001), OP, OP,
         note="seller only"),
    Rule("RC-15", "stamp", _d("2023-08-28"), None, (0.0, 0.0005), UNV, UNV, 1,
         note="read on an official repost only; no later change found (search not exhaustive)"),
    # ---------------- transfer fee, RC-16: value = (mode, amount), both sides ----------------
    Rule("RC-16", "transfer:sh", _d("2008-01-01"), _d("2015-07-31"), ("per_share", 0.000375), UNV, OP, 3,
         note="0.375 per mille of a par value of 1 yuan = highest rate found for the period; "
              "par value 1 yuan for every name is unverified"),
    Rule("RC-16", "transfer:sz", _d("2008-01-01"), _d("2015-07-31"), ("rate", 0.0000255), UNV, OP, 3,
         note="0.0255 per mille of traded value as of 2015; earlier rates unknown"),
    Rule("RC-16", "transfer:sh", _d("2015-08-01"), _d("2022-04-28"), ("rate", 0.00002), OP, OP),
    Rule("RC-16", "transfer:sz", _d("2015-08-01"), _d("2022-04-28"), ("rate", 0.00002), OP, OP),
    Rule("RC-16", "transfer:sh", _d("2022-04-29"), None, ("rate", 0.00001), UNV, UNV, 2,
         note="search summary only; plan fallback: 0.02 per mille throughout"),
    Rule("RC-16", "transfer:sz", _d("2022-04-29"), None, ("rate", 0.00001), UNV, UNV, 2,
         note="search summary only; plan fallback: 0.02 per mille throughout"),
    # ---------------- dividend tax, RC-14: by RECORD date; value = (tau, withheld at payment) ----
    Rule("RC-14", "divtax", _d("2008-01-01"), _d("2012-12-31"), (0.10, 0.10), IND + " - " + UNV, V, 4,
         note="10% flat known only through the repeal clause of the 2012 notice; that it was "
              "withheld at payment is assumed, not checked; plan fallback: 20% throughout"),
    Rule("RC-14", "divtax", _d("2013-01-01"), _d("2015-09-07"), (0.20, 0.05), V, V,
         note="20% = rate for holdings of one month or less; 5% withheld at payment, rest at the sale; "
              "holding-period brackets NOT modelled (plan)"),
    Rule("RC-14", "divtax", _d("2015-09-08"), None, (0.20, 0.0), V, V, 17,
         note="nothing withheld at payment; collected at the sale; whether the notice applies to a "
              "record date of 2015-09-08 itself was not checked (PLAN 3.10 list item 17; v0.7 E-9: "
              "kept as 'from 2015-09-08'; only the split cash paid / liability of that one record "
              "date depends on it)"),
    # ---------------- commission bounds, RC-17 (rate itself is a config placeholder) ----------
    Rule("RC-17", "commission_bounds", _d("2008-01-01"), None, {"max_rate": 0.003, "min_per_trade": 5.0}, V, V,
         note="includes exchange handling fee and regulatory fee; in force since 2002-05-01"),
    # ---------------- lot rules, RC-11 ----------------
    Rule("RC-11", "lot:main", _d("2008-01-01"), None, {"mode": "multiple", "unit": 100, "max_order": 1_000_000}, V, V),
    Rule("RC-11", "lot:chinext", _d("2008-01-01"), None, {"mode": "multiple", "unit": 100, "max_order": 300_000}, V, V,
         note="max limit-order size from the 2020 special provisions"),
    Rule("RC-11", "lot:star", _d("2008-01-01"), None, {"mode": "minimum", "unit": 200, "max_order": 100_000}, V, V,
         note="at least 200 shares, no multiple required; 2019 STAR provisions not opened"),
    # ---------------- closing call auction, RC-8 (information only; CV) ----------------
    Rule("RC-8", "close_auction:sz", _d("2008-01-01"), None, True, V, V),
    Rule("RC-8", "close_auction:sh", _d("2008-01-01"), _d("2018-08-19"), False, V, V,
         note="close = VWAP of the last minute; the pre-2018 clause itself was not opened"),
    Rule("RC-8", "close_auction:sh", _d("2018-08-20"), None, True, V, V),
    # ---------------- delisting regime, RC-10 (information only) ----------------
    Rule("RC-10", "delist_regime", _d("2008-01-01"), _d("2020-12-30"),
         {"suspension_of_listing_exists": True, "arrangement_days": 30, "first_day_no_limit": False,
          "trading_type_has_arrangement": True}, UNV, OP, 10,
         note="2012 and 2014 texts not opened; before 2012 no arrangement period"),
    Rule("RC-10", "delist_regime", _d("2020-12-31"), None,
         {"suspension_of_listing_exists": False, "arrangement_days": 15, "first_day_no_limit": True,
          "trading_type_has_arrangement": False}, V, OP,
         note="current SSE Listing Rules verified; date from the SSE press Q&A; SZSE chapter not opened"),
    # ================= (e) disclosure rules behind Z_O (v0.7, E-20 / F-20) =================
    # ---- RC-18 Dragon-Tiger thresholds.  kind 'deviation': closing-price deviation +-7%,
    #      amplitude 15%, turnover 20%; kind 'change': closing-price change +-15%, amplitude 30%,
    #      turnover 30%.
    #      (v0.8, J-1; task C-3) element "cum3": threshold of the three-day cumulative criterion
    #      used by the trigger proxy ro_trig_cum3_* (0.20 under 'deviation', 0.30 under 'change');
    #      the values of the v0.7 feature code.  One status per row: the status of cum3 is
    #      stated in the note of each row ("cum3: unverified, PLAN 3.10 item 22").
    Rule("RC-18", "lhb_thr:main", _d("2008-01-01"), None,
         {"kind": "deviation", "price": 0.07, "amplitude": 0.15, "turnover": 0.20, "cum3": 0.20}, V, V,
         note="cum3: unverified, PLAN 3.10 item 22"),
    Rule("RC-18", "lhb_thr:chinext", _d("2008-01-01"), _d("2020-08-23"),
         {"kind": "deviation", "price": 0.07, "amplitude": 0.15, "turnover": 0.20, "cum3": 0.20}, V, UNV, 7,
         note="main-board criteria until the 2020 reform; cum3: unverified, PLAN 3.10 item 22"),
    Rule("RC-18", "lhb_thr:chinext", _d("2020-08-24"), None,
         {"kind": "change", "price": 0.15, "amplitude": 0.30, "turnover": 0.30, "cum3": 0.30}, UNV, UNV, 7,
         note="with the 2020 reform; the implementing document was not opened; cum3: unverified, PLAN 3.10 item 22"),
    Rule("RC-18", "lhb_thr:star", _d("2008-01-01"), None,
         {"kind": "change", "price": 0.15, "amplitude": 0.30, "turnover": 0.30, "cum3": 0.30}, V, UNV, 9,
         note="since launch (2019; launch date unverified); STAR names enter with their first bar; "
              "cum3: unverified, PLAN 3.10 item 22"),
    # ---- RC-18 number of names listed per criterion: value = (N, top-5 indicator); both None
    #      where unknown (three-valued indicator 0 / 1 / unknown; PLAN 5.6.2a, v0.7 F-13).
    Rule("RC-18", "lhb_topn:sh", _d("2008-01-01"), _d("2021-09-16"), (3, 0), V, UNV, 7,
         note="top 3 until the 2021 notice"),
    Rule("RC-18", "lhb_topn:sh", _d("2021-09-17"), _d("2021-10-07"), (None, None), UNV, UNV, 7,
         note="UNKNOWN: between the date of the SSE notice (2021-09-17) and the effective date "
              "known from media only (2021-10-08)"),
    Rule("RC-18", "lhb_topn:sh", _d("2021-10-08"), None, (5, 1), V, UNV, 7,
         note="effective date from media only"),
    Rule("RC-18", "lhb_topn:sz", _d("2008-01-01"), _d("2013-11-30"), (None, None), UNV, UNV, 19,
         note="UNKNOWN: 3 in the 2006 text, 5 in the November 2013 text; which revision in between "
              "changed it is unknown"),
    Rule("RC-18", "lhb_topn:sz", _d("2013-12-01"), None, (5, 1), V, UNV, 19,
         note="5 in the November 2013 text; its effective date is unverified (item 19); the boundary "
              "2013-12-01 is the one fixed in PLAN 5.6.2a / task FEA-7"),
    # ---- RC-20 pre-disclosure of share reductions: regime index 0..4 ----
    Rule("RC-20", "ins_regime", _d("2008-01-01"), _d("2015-07-07"), 0, V, V, 15,
         note="no general requirement; disclosure before 2015-07-08 not opened (item 15)"),
    Rule("RC-20", "ins_regime", _d("2015-07-08"), _d("2016-01-08"), 1, V, V,
         note="large shareholders and insiders may not sell through the secondary market"),
    Rule("RC-20", "ins_regime", _d("2016-01-09"), _d("2017-05-26"), 2, V, V,
         note="large shareholders disclose a plan 15 trading days before the first sale by centralised bidding"),
    Rule("RC-20", "ins_regime", _d("2017-05-27"), _d("2024-05-23"), 3, V, V,
         note="extended to directors, supervisors and senior managers; exchanges' 2017 rules not opened"),
    Rule("RC-20", "ins_regime", _d("2024-05-24"), None, 4, V, V,
         note="large shareholders' block-trade sales also covered"),
    # ---- RC-6 (f): new listings trade without a price limit on their first 5 trading days ----
    Rule("RC-6(f)", "ipo_nolimit5:star", _d("2008-01-01"), None, True, V, UNV, 9,
         note="since launch"),
    Rule("RC-6(f)", "ipo_nolimit5:chinext", _d("2008-01-01"), _d("2020-08-23"), False, V, OP,
         note="first listing day only"),
    Rule("RC-6(f)", "ipo_nolimit5:chinext", _d("2020-08-24"), None, True, V, OP),
    Rule("RC-6(f)", "ipo_nolimit5:main", _d("2008-01-01"), _d("2023-04-09"), False, V, UNV, 21,
         note="first listing day only"),
    Rule("RC-6(f)", "ipo_nolimit5:main", _d("2023-04-10"), None, True, V, UNV, 21,
         note="DATE UNVERIFIED AGAINST OFFICIAL TEXT (PLAN 3.10 list items 8 and 21): 2023-04-10 was "
              "carried by the feature library, written from memory.  No computation may depend on it: "
              "limit-count controls are NaN while their window contains any of a name's first 5 "
              "trading days (v0.7, F-20); SF needs no calendar of no-limit days (PLAN 3.4)"),
]

# Rules with no interval structure, kept for the status report only.
STATIC_RULES = [
    ("RC-1", "T+1 for A-shares, whole period", V),
    ("RC-2", "Opening call auction 09:15-09:25, no cancellation 09:20-09:25", V),
    ("RC-3", "Call-auction pricing: orders priced better than the match price filled in full", V),
    ("RC-4", "Published open = first trade of the day (early routine one-hour suspensions: unverified, item 11)", V),
    ("RC-5", "Ex-reference price uses pre-tax dividend; limit price rounded half-up to 0.01; +-0.01 floor", V),
    ("RC-6(g)", "Days without a limit for seasoned stocks - not needed by SF; (5) unverified, item 14", V),
    ("RC-6(h)", "Arrangement period after first day: 10% main board (verified); ChiNext/STAR unverified, item 10", UNV),
    ("RC-12", "Ex-date = trading day after the record date for dividends/bonus/capitalisation "
              "(SSE R+2 -> R+1 change date unverified, item 13)", V),
    ("RC-13", "Rights issues: suspension in payment period, ex-date timing, non-transferability", UNV),
    ("RC-22", "Same-auction funding of a purchase by sale proceeds - not relied on", NF),
]

# Days flagged in the trade ledger (index circuit breaker; auction ran normally), RC-7.
FLAGGED_DAYS = {_d("2016-01-04"): "index circuit breaker (RC-7; 2016 notices not opened)",
                _d("2016-01-07"): "index circuit breaker (RC-7; 2016 notices not opened)"}

_TICK = Decimal("0.01")


def _check(dt: date) -> None:
    if not (CAL_START <= dt <= CAL_END):
        raise CalendarError(f"{dt} is outside the rule calendar window {CAL_START}..{CAL_END}")


def lookup(key: str, dt: date) -> Rule:
    _check(dt)
    hits = [r for r in RULES if r.key == key and r.start <= dt and (r.end is None or dt <= r.end)]
    if len(hits) != 1:
        raise CalendarError(f"{len(hits)} rule rows for key={key!r} on {dt}")
    return hits[0]


# ---------------- board / exchange classification ----------------
# Prefix table. "302 -> ChiNext" is the fetch task's own judgement and is unverified
# (FETCH_README 6-11).  sz.002 (former SME board) had main-board bands throughout.
_BOARD_PREFIX = [
    ("sh.600", "main"), ("sh.601", "main"), ("sh.603", "main"), ("sh.605", "main"),
    ("sh.688", "star"), ("sh.689", "star"),
    ("sz.000", "main"), ("sz.001", "main"), ("sz.002", "main"), ("sz.003", "main"),
    ("sz.300", "chinext"), ("sz.301", "chinext"), ("sz.302", "chinext"),
]
BOARD_PREFIX_UNVERIFIED = {"sz.302"}


def board_of(code: str) -> str:
    """'main' | 'chinext' | 'star'.  Raises CalendarError for anything else (B shares, BSE, ...)."""
    for p, b in _BOARD_PREFIX:
        if code.startswith(p):
            return b
    raise CalendarError(f"cannot classify code {code!r} into a board")


def exchange_of(code: str) -> str:
    if code.startswith("sh."):
        return "sh"
    if code.startswith("sz."):
        return "sz"
    raise CalendarError(f"cannot classify code {code!r} into an exchange")


# ---------------- price limits ----------------
def price_band(dt: date, board: str, is_st: bool) -> Decimal:
    return Decimal(lookup(f"band:{board}:{int(bool(is_st))}", dt).value)


def _dec(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    if isinstance(x, str):
        return Decimal(x.strip())
    # floats: shortest repr round-trips the decimal the data source printed
    return Decimal(repr(float(x)))


def limit_prices(preclose, band) -> tuple[Decimal, Decimal]:
    """(P_up, P_down) per RC-5 (verified): preclose x (1 +- band), rounded half-up to 0.01 yuan
    in decimal arithmetic; a rounded limit less than 0.01 away from preclose is set to
    preclose +- 0.01."""
    pc, r = _dec(preclose), _dec(band)
    if pc <= 0:
        raise CalendarError(f"non-positive reference price {preclose!r}")
    up = (pc * (1 + r)).quantize(_TICK, rounding=ROUND_HALF_UP)
    dn = (pc * (1 - r)).quantize(_TICK, rounding=ROUND_HALF_UP)
    if up - pc < _TICK:
        up = pc + _TICK
    if pc - dn < _TICK:
        dn = pc - _TICK
    return up, dn


def limit_prices_for(code: str, dt: date, preclose, is_st: bool) -> tuple[Decimal, Decimal, Decimal]:
    band = price_band(dt, board_of(code), is_st)
    up, dn = limit_prices(preclose, band)
    return up, dn, band


# ---------------- costs ----------------
def stamp_duty(dt: date) -> tuple[float, float]:
    """(buy-side rate, sell-side rate) on the trade date."""
    return lookup("stamp", dt).value


def transfer_fee(dt: date, exchange: str, fallback_no_2022_cut: bool = False) -> tuple[str, float]:
    """('per_share', yuan per share) or ('rate', fraction of traded value); charged on both sides."""
    mode, amt = lookup(f"transfer:{exchange}", dt).value
    if fallback_no_2022_cut and dt >= date(2022, 4, 29):
        return ("rate", 0.00002)
    return mode, amt


def commission_bounds(dt: date) -> dict:
    return lookup("commission_bounds", dt).value


DIVTAX_2015_BOUNDARY = date(2015, 9, 8)


def dividend_tax(record_date: date, fallback_20_before_2013: bool = False,
                 reading_2015: str = "from") -> tuple[float, float]:
    """(tau, rate withheld at payment) by RECORD date.  tau is the total tax used by every
    label and by wealth; the withheld part only moves spendable cash (PLAN 3.11).

    reading_2015 (v0.7, E-9; PLAN 3.10 list item 17): 'from' = the 2015 notice applies to record
    dates >= 2015-09-08 (in force); 'after' = to record dates > 2015-09-08, i.e. the boundary
    day itself is still under the 2013 arrangement.  tau is the same under both readings."""
    if reading_2015 not in ("from", "after"):
        raise CalendarError(f"unknown reading {reading_2015!r}")
    q = record_date
    if reading_2015 == "after" and record_date == DIVTAX_2015_BOUNDARY:
        q = date(2015, 9, 7)
    tau, wh = lookup("divtax", q).value
    if fallback_20_before_2013 and record_date < date(2013, 1, 1):
        return 0.20, 0.20
    return tau, wh


# ---------------- lots ----------------
def lot_rule(dt: date, board: str) -> dict:
    return lookup(f"lot:{board}", dt).value


def round_buy_quantity(q: float, dt: date, board: str) -> float:
    """Lot-rounding robustness run (RC-11).  Main board / ChiNext: floor to a multiple of 100.
    STAR: no order below 200 shares, otherwise floor to whole shares.  Returns 0.0 for 'no order'."""
    import math
    rule = lot_rule(dt, board)
    if rule["mode"] == "multiple":
        return float(math.floor(q / rule["unit"] + 1e-12) * rule["unit"])
    if q < rule["unit"]:
        return 0.0
    return float(math.floor(q + 1e-12))


# ---------------- information-only lookups ----------------
def has_closing_auction(dt: date, exchange: str) -> bool:
    return lookup(f"close_auction:{exchange}", dt).value


def delisting_regime(dt: date) -> dict:
    return lookup("delist_regime", dt).value


# ---------------- (e) disclosure regimes (read by the feature library) ----------------
def lhb_thresholds(dt: date, board: str) -> dict:
    """Dragon-Tiger criteria in force for a board on a day (RC-18)."""
    return lookup(f"lhb_thr:{board}", dt).value


def lhb_top5(dt: date, exchange: str) -> Optional[int]:
    """Three-valued indicator of 'five names per criterion' (RC-18): 0, 1, or None = unknown."""
    return lookup(f"lhb_topn:{exchange}", dt).value[1]


def lhb_top_n(dt: date, exchange: str) -> Optional[int]:
    """Number of names listed per criterion (3 or 5), None = unknown."""
    return lookup(f"lhb_topn:{exchange}", dt).value[0]


def ins_regime(dt: date) -> int:
    """Index 0..4 of the share-reduction disclosure regime (RC-20)."""
    return lookup("ins_regime", dt).value


def ipo_no_limit_first5(dt: date, board: str) -> bool:
    """Whether a stock first listed on `dt` trades without a price limit on its first five
    trading days (RC-6 (f)).  The main-board date is unverified - see the row's note."""
    return lookup(f"ipo_nolimit5:{board}", dt).value


def intervals(key: str) -> list[tuple[date, date, Any]]:
    """All rows of a key as (start, end, value), ascending - for vectorised use by callers."""
    rows = sorted((r for r in RULES if r.key == key), key=lambda r: r.start)
    if not rows:
        raise CalendarError(f"no rule rows for key={key!r}")
    return [(r.start, r.end if r.end is not None else CAL_END, r.value) for r in rows]


def flagged_day(dt: date) -> Optional[str]:
    return FLAGGED_DAYS.get(dt)


def boundary_dates() -> list[tuple[str, date]]:
    """Every (key, start date) at which a value changes inside the window (for the tests)."""
    out = []
    for r in RULES:
        if r.start > CAL_START:
            out.append((r.key, r.start))
    return sorted(set(out), key=lambda z: (z[1], z[0]))


def status_table() -> list[dict]:
    rows = []
    for r in RULES:
        rows.append({"rc": r.rc, "key": r.key, "start": r.start.isoformat(),
                     "end": r.end.isoformat() if r.end else CAL_END.isoformat(),
                     "value": r.value if not isinstance(r.value, (tuple, dict)) else str(r.value),
                     "status": r.status, "date_status": r.date_status,
                     "unverified_item": r.unverified_item, "note": r.note})
    for rc, text, st in STATIC_RULES:
        rows.append({"rc": rc, "key": "static", "start": CAL_START.isoformat(), "end": CAL_END.isoformat(),
                     "value": text, "status": st, "date_status": "", "unverified_item": None, "note": ""})
    return rows

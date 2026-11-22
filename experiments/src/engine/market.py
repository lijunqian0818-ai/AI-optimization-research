"""Market container, corporate-event records and the two valuation rules OV / CV.

OV (open valuation)  = price rule of instantiation_ashare.md I-s3 Step 2 applied on every
                       day (PLAN 3.9): P1 (suspended: last traded close restated by rule
                       R-P1, incl. convention P1-R for rights issues), P2/P3 merged (traded:
                       published daily open), P4 (not suspended, no trade: data `preclose`).
CV (closing valuation) = PLAN 3.9 K1-K3 (K4 is handled by the ledger's write-off).

No vendor adjustment factor and no vendor-adjusted price is read anywhere: the container
has no field for one (FC-A4; tests/test_v07_components.py checks it).  The `open`, `close`
and `preclose` of a suspended-day row are never used as a value.

Track identifiers (PLAN 3.9, v0.7 E-14).  A lot that arrived by succession (S-e) is carried
in the ledger's share vectors and in the attribution track under the identifier
"<successor code>#succ": it has the successor's prices and distributions, but a further
S-d / S-e of the successor is class U for it.  `real_code` maps an identifier to the
security whose bars and orders it refers to.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional

import numpy as np

SUCC_MARK = "#succ"


def real_code(ident: str) -> str:
    return ident[:-len(SUCC_MARK)] if ident.endswith(SUCC_MARK) else ident


def is_succ(ident: str) -> bool:
    return ident.endswith(SUCC_MARK)


def succ_id(code: str) -> str:
    return real_code(code) + SUCC_MARK


class MarketDataError(ValueError):
    pass


@dataclass
class Event:
    """One corporate event of one security.

    kind:
      'dist'        S-a / S-b: cash dividend (gross per share `gross_cash`) and/or share
                    multiplier `phi`, effective on `ex_date`; record date = previous market
                    trading day (RC-12) - a different stated record date is a data error.
      'rights'      S-c: rights issue; `record_date`, `rights_price`, `rights_ratio`
                    (announced new shares per existing share) are read from the record;
                    `announce_date` = the earliest date the record carries (E-15).
      'cashout'     S-d: removal against cash only, `cash_per_share`, effective `ex_date`.
      'exchange'    S-e: exchange for `successor` at `ratio`, effective `ex_date`.
      'unsupported' class U, effective `ex_date`.

    forced_class = "U" (v0.7, E-11 / G-1; PLAN 3.11 rules 9 (c) and 10): the event table could
    not classify the event even after the hand check.  Such an event is NOT booked anywhere
    (ledger, valuation, attribution track: shares and cash unchanged, market valuation,
    flagged - the URS convention of PLAN 3.9) and gives outcome U to every entry whose window
    (t, t+H] contains its effective day.
    """
    code: str
    kind: str
    ex_date: Optional[date] = None
    record_date: Optional[date] = None
    gross_cash: Optional[float] = 0.0
    phi: Optional[float] = 1.0
    pay_date: Optional[date] = None
    rights_price: Optional[float] = None
    rights_ratio: Optional[float] = None
    cash_per_share: Optional[float] = None
    successor: Optional[str] = None
    ratio: Optional[float] = None
    forced_class: Optional[str] = None
    announce_date: Optional[date] = None


@dataclass
class Sec:
    code: str
    open: np.ndarray        # float, nan where no row
    close: np.ndarray
    preclose: np.ndarray
    amount: np.ndarray      # traded amount in yuan (G_{t+1} information; used for ADV only)
    has_row: np.ndarray     # bool
    flag_trading: np.ndarray  # bool: vendor status flag == trading (False = whole-day suspension)
    vol_pos: np.ndarray     # bool: parsed volume > 0 (empty string counts as zero)
    is_st: np.ndarray       # bool
    # first market-day index on which the name is no longer listed = the market trading day
    # after its last row in the bar file (PLAN 3.9, v0.7 G-3)
    delist_i: Optional[int] = None
    # rows inserted by the fetch pipeline from the cross-check source (PLAN 3.11 rule 12);
    # the engine itself never fills a row
    filled_from_xsrc: Optional[np.ndarray] = None
    # share exchange (disposition table, PLAN 3.11 rule 11): first market-day index on which
    # the successor's new shares trade.  On delist_i <= i < carry_until_i the holding is
    # carried at the last value of the absorbed name (flagged), not written off.
    carry_until_i: Optional[int] = None
    # market trading days between the listing day and the first panel day (0 if listed inside
    # the panel); None = unknown (then only rows inside the panel count)
    listed_days_before_panel: Optional[int] = None


class Market:
    def __init__(self, days: list[date], secs: dict[str, Sec], events: list[Event] | None = None,
                 urs: set | None = None, u_spans: dict | None = None):
        self.days = list(days)
        self.T = len(days)
        self.idx = {d: i for i, d in enumerate(self.days)}
        self.secs = secs
        self.urs = set(urs or ())           # {(code, date)}: unexplained reference-price steps
        # {code: [(first date, last date, reason)]}: date conflicts between an event source and
        # the bar source that the hand check could not decide (PLAN 3.11 rule 9 (b)): outcome U
        # for every entry whose window (t, t+H] contains a day of the span
        self.u_spans: dict[str, list[tuple]] = {k: list(v) for k, v in (u_spans or {}).items()}
        self.events: dict[str, list[Event]] = {}
        self._by_day: dict[tuple[str, int], list[Event]] = {}
        self.forced_u: dict[tuple[str, int], list[Event]] = {}
        self.problems: list[str] = []
        self.data_cutoff = None             # set by io_baostock.load_market (PLAN v0.8 C-8)
        self._tr_cache: dict[str, tuple] = {}
        self._first_row: dict[str, Optional[int]] = {}
        for ev in (events or []):
            self.add_event(ev)

    # ---------- events ----------
    def day_index_on_or_after(self, d: date) -> Optional[int]:
        lo, hi = 0, self.T
        while lo < hi:
            mid = (lo + hi) // 2
            if self.days[mid] < d:
                lo = mid + 1
            else:
                hi = mid
        return lo if lo < self.T else None

    def add_event(self, ev: Event) -> None:
        if ev.kind not in ("dist", "rights", "cashout", "exchange", "unsupported"):
            raise MarketDataError(f"unknown event kind {ev.kind!r}")
        if ev.forced_class not in (None, "U"):
            raise MarketDataError(f"unknown forced class {ev.forced_class!r}")
        self.events.setdefault(ev.code, []).append(ev)
        if ev.kind == "rights" and ev.forced_class is None:
            return
        if ev.ex_date is None:
            raise MarketDataError(f"{ev.kind} event of {ev.code} without effective date")
        i = self.idx.get(ev.ex_date)
        if i is None:
            self.problems.append(f"{ev.code}: {ev.kind} effective {ev.ex_date} is not a market trading day in the panel")
            return
        if ev.forced_class == "U":
            self.forced_u.setdefault((ev.code, i), []).append(ev)
            return
        if ev.kind == "dist" and ev.record_date is not None and i > 0 and ev.record_date != self.days[i - 1]:
            # RC-12 says record date = trading day before the ex-date.  A record that says
            # otherwise must be resolved by hand (PLAN 3.11 rules 3, 10); the engine does not guess.
            self.problems.append(f"{ev.code}: dist record date {ev.record_date} is not the trading day "
                                 f"before ex-date {ev.ex_date}")
        self._by_day.setdefault((ev.code, i), []).append(ev)

    def events_on(self, code: str, i: int) -> list[Event]:
        """Booked non-rights events of `code` effective on market day i (order: dist, then
        others).  Events with forced_class 'U' are not returned (see Event)."""
        evs = self._by_day.get((code, i), [])
        return sorted(evs, key=lambda e: 0 if e.kind == "dist" else 1)

    def rights_of(self, code: str) -> list[Event]:
        return [e for e in self.events.get(code, []) if e.kind == "rights" and e.forced_class is None]

    def unclassifiable_on(self, code: str, i: int) -> Optional[str]:
        """Reason why day i is a class-U day for holders of `code` although nothing is booked
        (URS step, forced-U event, undecided date conflict), or None."""
        d = self.days[i]
        if (code, d) in self.urs:
            return f"unexplained reference-price step on {d}"
        if (code, i) in self.forced_u:
            return f"event that cannot be classified, effective {d}"
        for lo, hi, why in self.u_spans.get(code, ()):
            if lo <= d <= hi:
                return f"{why} ({lo}..{hi})"
        return None

    # ---------- row status ----------
    def status(self, code: str, i: int) -> str:
        """'T' traded (S1 holds) | 'S' flagged whole-day suspension | 'N' flagged trading, no
        volume | 'X' no row | 'D' no longer listed."""
        s = self.secs[code]
        if s.delist_i is not None and i >= s.delist_i:
            return "D"
        if not s.has_row[i]:
            return "X"
        if not s.flag_trading[i]:
            return "S"
        return "T" if s.vol_pos[i] else "N"

    def traded(self, code: str, i: int) -> bool:
        return self.status(code, i) == "T"

    def in_carry(self, code: str, i: int) -> bool:
        s = self.secs[code]
        return (s.delist_i is not None and s.carry_until_i is not None
                and s.delist_i <= i < s.carry_until_i)

    def filled_xsrc(self, code: str, i: int) -> bool:
        f = self.secs[code].filled_from_xsrc
        return bool(f is not None and f[i])

    def first_row(self, code: str) -> Optional[int]:
        if code not in self._first_row:
            r = np.flatnonzero(self.secs[code].has_row)
            self._first_row[code] = int(r[0]) if len(r) else None
        return self._first_row[code]

    def traded_index(self, code: str) -> tuple:
        """(sorted indices of traded days, their traded amounts) - cached; rows only change
        in tests that build a fresh Market."""
        c = self._tr_cache.get(code)
        if c is None:
            s = self.secs[code]
            tr = s.has_row & s.flag_trading & s.vol_pos
            if s.delist_i is not None:
                tr = tr.copy()
                tr[s.delist_i:] = False
            ix = np.flatnonzero(tr)
            c = self._tr_cache[code] = (ix, np.nan_to_num(s.amount[ix]))
        return c

    def last_traded_before(self, code: str, i: int) -> Optional[int]:
        s = self.secs[code]
        j = i - 1
        while j >= 0:
            if s.has_row[j] and s.flag_trading[j] and s.vol_pos[j]:
                return j
            j -= 1
        return None

    def spell_length(self, code: str, i: int) -> int:
        """Number of market days since the last traded day (0 if traded on i)."""
        if self.traded(code, i):
            return 0
        c = self.last_traded_before(code, i)
        return i - (c if c is not None else -1)


@dataclass
class Val:
    value: Optional[float]      # per-share value; None = missing input
    branch: str                 # 'P23' | 'P4' | 'P1' | 'P1R' | 'CARRY' | 'D' | 'MISSING'
    why: str = ""
    carry_missing_row: bool = False   # P1 carried a close across a day without a row (E-16)


class Valuer:
    """OV / CV for a market.  `cv_override(code, i) -> float` replaces every CV (used only by
    the R4 test 'CV is immaterial for an open-to-open position')."""

    def __init__(self, market: Market, cv_override: Optional[Callable[[str, int], float]] = None):
        self.m = market
        self.cv_override = cv_override
        self.counts = {"K3": 0}
        self._ov: dict[tuple[str, int], Val] = {}
        self._cv: dict[tuple[str, int], Val] = {}

    def ov(self, code: str, i: int) -> Val:
        key = (code, i)
        v = self._ov.get(key)
        if v is None:
            v = self._ov[key] = self._ov_compute(code, i)
        return v

    def _ov_compute(self, code: str, i: int) -> Val:
        m = self.m
        s = m.secs[code]
        st = m.status(code, i)
        if st == "D":
            if m.in_carry(code, i):
                # share exchange pending (PLAN 3.9, v0.7 E-18): last value of the absorbed name
                last = self.cv(code, s.delist_i - 1) if s.delist_i > 0 else Val(None, "MISSING")
                if last.value is None:
                    return Val(None, "MISSING", "no last value of the absorbed name to carry")
                return Val(last.value, "CARRY", "delisted; carried at the last value until the successor's shares trade")
            return Val(None, "D", "not listed")
        if st == "T":
            p = float(s.open[i])
            if not (p > 0):
                return Val(None, "MISSING", "open missing or non-positive on a traded day")
            return Val(p, "P23")
        if st == "N":
            p = float(s.preclose[i])
            if not (p > 0):
                return Val(None, "MISSING", "reference price missing on a no-trade day")
            return Val(p, "P4")
        # 'S' (flagged suspended) and 'X' (no row; treated as suspended, reported by callers)
        return self._p1(code, i, missing_row=(st == "X"))

    def _p1(self, code: str, i: int, missing_row: bool) -> Val:
        """Rule R-P1 (I-s3): the last close c at which the name traded, restated in
        chronological order of the instants at which the events take effect:

          * S-a / S-b with ex-date e, c < e <= i: m := (m - gross) / phi, effective at the
            OPEN of e;
          * S-c with record date R, c <= R <= i-1: convention P1-R,
            m := min(m, (m + rho P_r) / (1 + rho)), effective at the CLOSE of R.

        Same-day order (PLAN 3.8 (iii) note (7), v0.7 E-12): when an S-a / S-b ex-date and an
        S-c record date fall on the same day, the dividend / bonus restatement is applied
        first and P1-R second (open before close).  An S-c record date on the day before an
        S-a / S-b ex-date is applied first, for the same reason.

        `carry_missing_row`: some day in (c, i] has no row in the bar file, so it cannot be
        established that c is the last traded close (E-16) - the label turns this into M, the
        ledger keeps the value and flags it."""
        m = self.m
        c = m.last_traded_before(code, i)
        if c is None:
            return Val(None, "MISSING", "no traded day before the suspension")
        val = float(m.secs[code].close[c])
        if not (val > 0):
            return Val(None, "MISSING", "last traded close missing")
        s = m.secs[code]
        gap = bool((~s.has_row[c + 1:i + 1]).any())
        steps = []   # (date of the instant, 0 = open / 1 = close, event)
        for j in range(c + 1, i + 1):
            for ev in m.events_on(code, j):
                if ev.kind == "dist":
                    steps.append((m.days[j], 0, ev))
        used_rights = False
        for ev in m.rights_of(code):
            if ev.record_date is None:
                continue
            if m.days[c] <= ev.record_date < m.days[i]:
                steps.append((ev.record_date, 1, ev))
        steps.sort(key=lambda z: (z[0], z[1]))
        for _, _, ev in steps:
            if ev.kind == "dist":
                g, phi = ev.gross_cash, ev.phi
                if g is None or phi is None or not np.isfinite(g) or not np.isfinite(phi) or phi <= 0:
                    return Val(None, "MISSING", "dist event with missing amount in P1 restatement")
                val = (val - g) / phi
            else:
                pr, rho = ev.rights_price, ev.rights_ratio
                if pr is None or rho is None or not np.isfinite(pr) or not np.isfinite(rho) or rho < 0:
                    return Val(None, "MISSING", "rights terms missing in P1-R")
                val = min(val, (val + rho * pr) / (1.0 + rho))
                used_rights = True
        if not (val > 0):
            return Val(None, "MISSING", "restated P1 value not positive")
        why = ""
        if missing_row:
            why = "no row (treated as suspended)"
        elif gap:
            why = "P1 carry across a day without a row"
        return Val(val, "P1R" if used_rights else "P1", why, carry_missing_row=gap)

    def cv(self, code: str, i: int) -> Val:
        key = (code, i)
        v = self._cv.get(key)
        if v is None:
            v = self._cv[key] = self._cv_compute(code, i)
        return v

    def _cv_compute(self, code: str, i: int) -> Val:
        ov = self.ov(code, i)
        if ov.value is None:
            return ov
        if self.cv_override is not None:
            return Val(float(self.cv_override(code, i)), "CVX")
        if self.m.status(code, i) == "T":
            c = float(self.m.secs[code].close[i])
            if c > 0:
                return Val(c, "K1")
            self.counts["K3"] += 1
            return Val(ov.value, "K3", "close missing on a traded day")
        return Val(ov.value, "K2", ov.why if ov.branch == "CARRY" else "")

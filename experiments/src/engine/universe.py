"""Universe U-LIQ and the candidate set C_t (PLAN 2.3, 3.5; U54, U11, U55).

Everything here is a function of G_t: membership of the month uses data dated <= s, the last
market trading day of the previous calendar month; the candidate filter uses data dated
<= t-1.  `tests/test_v07_components.py` checks this by truncation.

Universe (screen date s):
  eligible  board classifiable as SSE / SZSE main board, ChiNext or STAR (rule calendar
            prefix table: no B shares, no BSE); at least `universe_min_listed` market trading
            days since listing; traded on at least `universe_min_traded` of the
            `universe_window` market trading days ending s; a row on s with ST flag 0;
  ranking   median daily traded amount over the `universe_window` market trading days ending
            s (a day without a trade counts as 0); the `universe_size` highest are members;
            ties are broken by code (ascending) - the plan does not say, any fixed rule is
            G_t-measurable;
  validity  the membership of screen date s is used for all decision days of the following
            calendar month.

Candidate set C_t = members
  and listed at least `candidate_min_listed` market trading days before t (U11),
  and not suspended on t-1: the day t-1 row exists and is not flagged as a whole-day
      suspension (a name without a row on t-1 is removed and counted - plan silent),
  and ST flag 0 on every one of the `st_lookback` market trading days ending t-1 (U55; a day
      without a row carries no flag and does not exclude).

"Days since listing" = market trading days from the listing day (inclusive) to the day in
question.  For a name listed before the first panel day the loader supplies
Sec.listed_days_before_panel (from the full exchange calendar); if it is unknown only the
days inside the panel are counted (conservative: later eligibility).

No return, price change or outcome is read here.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

import numpy as np

from . import rule_calendar as rc
from .config import EngineConfig
from .market import Market


def screen_days(days: list[date]) -> list[int]:
    """Indices of the last market trading day of each calendar month (the last panel day is a
    screen day only if the next panel day would be in another month - it is included, and
    its membership is simply never used if the panel ends there)."""
    out = []
    for i, d in enumerate(days):
        if i == len(days) - 1 or (days[i + 1].year, days[i + 1].month) != (d.year, d.month):
            out.append(i)
    return out


class Panel:
    """Dense arrays (T x n) of the fields the screen reads.  Built once."""

    def __init__(self, market: Market, codes: Optional[list[str]] = None):
        self.m = market
        self.codes = sorted(codes if codes is not None else market.secs)
        T, n = market.T, len(self.codes)
        self.traded = np.zeros((T, n), bool)
        self.amount = np.zeros((T, n))
        self.has_row = np.zeros((T, n), bool)
        self.susp = np.zeros((T, n), bool)
        self.st = np.zeros((T, n), bool)
        self.first = np.full(n, T, int)          # index of the listing day inside the panel (first row)
        self.before = np.zeros(n, int)           # listed days before the panel
        self.board_ok = np.zeros(n, bool)
        for k, c in enumerate(self.codes):
            s = market.secs[c]
            listed = np.ones(T, bool)
            if s.delist_i is not None:
                listed[s.delist_i:] = False
            tr = s.has_row & s.flag_trading & s.vol_pos & listed
            self.traded[:, k] = tr
            self.amount[:, k] = np.where(tr, np.nan_to_num(s.amount), 0.0)
            self.has_row[:, k] = s.has_row & listed
            self.susp[:, k] = s.has_row & ~s.flag_trading & listed
            self.st[:, k] = s.has_row & s.is_st & listed
            fr = market.first_row(c)
            self.first[k] = T if fr is None else fr
            self.before[k] = s.listed_days_before_panel or 0
            try:
                rc.board_of(c)
                self.board_ok[k] = True
            except rc.CalendarError:
                self.board_ok[k] = False

    def listed_days(self, i: int) -> np.ndarray:
        """Market trading days since listing, counted through day i (0 if not yet listed)."""
        inside = np.maximum(0, i - self.first + 1)
        return np.where(inside > 0, inside + self.before, 0)


def members(panel: Panel, s_i: int, cfg: EngineConfig) -> tuple[list[str], dict]:
    """Members for the month after screen day s_i, and counts."""
    w = cfg.universe_window
    lo = s_i - w + 1
    n = len(panel.codes)
    if lo < 0:
        return [], {"screen_day": panel.m.days[s_i].isoformat(), "eligible": 0, "members": 0,
                    "note": "fewer than universe_window panel days before the screen day"}
    listed = panel.listed_days(s_i) >= cfg.universe_min_listed
    n_traded = panel.traded[lo:s_i + 1].sum(axis=0)
    active = n_traded >= cfg.universe_min_traded
    not_st = panel.has_row[s_i] & ~panel.st[s_i]
    elig = panel.board_ok & listed & active & not_st
    med = np.median(panel.amount[lo:s_i + 1], axis=0)
    idx = [k for k in range(n) if elig[k]]
    idx.sort(key=lambda k: (-med[k], panel.codes[k]))
    chosen = idx[:cfg.universe_size]
    return [panel.codes[k] for k in chosen], {
        "screen_day": panel.m.days[s_i].isoformat(), "names_with_a_row": int(panel.has_row[s_i].sum()),
        "eligible": len(idx), "members": len(chosen),
        "excluded_board": int((~panel.board_ok).sum()),
        "excluded_listing_age": int((panel.board_ok & ~listed & panel.has_row[s_i]).sum()),
        "excluded_inactive": int((panel.board_ok & listed & ~active & panel.has_row[s_i]).sum()),
        "excluded_st_or_no_row": int((panel.board_ok & listed & active & ~not_st).sum())}


def membership_by_month(panel: Panel, cfg: EngineConfig) -> tuple[dict, list]:
    """{(year, month): members valid for the decision days of that month}, and the per-screen
    counts.  The membership of month (y, m) comes from the last trading day of the previous
    calendar month."""
    out, reports = {}, []
    days = panel.m.days
    for s_i in screen_days(days):
        if s_i + 1 >= len(days):
            continue
        nxt = days[s_i + 1]
        mem, rep = members(panel, s_i, cfg)
        out[(nxt.year, nxt.month)] = mem
        reports.append(rep)
    return out, reports


def candidates(panel: Panel, t_i: int, member_codes: list[str], cfg: EngineConfig) -> tuple[list[str], dict]:
    """C_t from the month's members and data dated <= t-1."""
    if t_i < 1:
        return [], {"note": "no day t-1"}
    pos = {c: k for k, c in enumerate(panel.codes)}
    p = t_i - 1
    lo = max(0, p - cfg.st_lookback + 1)
    listed_days = panel.listed_days(p)
    st_any = panel.st[lo:p + 1].any(axis=0)
    out, cnt = [], {"members": len(member_codes), "removed_listing_age": 0, "removed_suspended": 0,
                    "removed_no_row": 0, "removed_st_lookback": 0}
    for c in member_codes:
        k = pos[c]
        if listed_days[k] < cfg.candidate_min_listed:
            cnt["removed_listing_age"] += 1
        elif not panel.has_row[p, k]:
            cnt["removed_no_row"] += 1
        elif panel.susp[p, k]:
            cnt["removed_suspended"] += 1
        elif st_any[k]:
            cnt["removed_st_lookback"] += 1
        else:
            out.append(c)
    cnt["candidates"] = len(out)
    return out, cnt


def ever_members(by_month: dict) -> list[str]:
    s: set = set()
    for v in by_month.values():
        s.update(v)
    return sorted(s)

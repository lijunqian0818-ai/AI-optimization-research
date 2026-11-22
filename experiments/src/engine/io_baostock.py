"""Read-only loader for the raw BaoStock daily bars and the event tables written by
experiments/src/data_fetch (Parquet under experiments/data/raw).

It never contacts a data source and never writes under data/raw.  It parses, aligns the
rows of each name on the market trading calendar and LISTS every irregularity it meets;
it repairs nothing and fills no row (PLAN 3.11 rule 12: missing rows are repaired by the
fetch pipeline; a row it inserted carries the column `filled_from_xsrc`, which is read
here and passed through).

No adjustment factor, no adjusted price (FC-A4).  The loader
  * never opens a file of a vendor factor table (FORBIDDEN_DIRS);
  * refuses a bar file whose `adjustflag` is not "3" (unadjusted) on every row;
  * refuses a bar file that has a column whose name looks like a factor or an adjusted price
    (FORBIDDEN_COLUMN_PARTS);
and reads from a bar file only the columns of READ_COLS.

"No longer listed" (PLAN 3.9, v0.7 G-3): a name is not listed from the market trading day
after its last row in the bar file.  The bar source's `outDate` is the last day with a row
for most delisted names and the day after it for others (landed files, 2026-11-15: 89 and
11 of 100); the loader keeps every row and gives the same answer in both cases.

Events.  `events="sina"`: ONE source (the Sina dividend and rights tables) - the v0.6
pipeline exercise, kept with the v0.7 filter (G-2): a dividend row enters only if its status
is "implemented" AND it has an ex-date; rows with an ex-date but another status and rights
rows without dates go to the problem list and not into the event table.  Reference-price
steps without an event and events without a step are only LISTED here (ENG-18); pairing
them is the event table's job.  `events="merged"`: the event table of PLAN 3.11
(event_table.build) from EV1-EV3 and EV4.  `events="none"`: bars only.

The Sina and Eastmoney tables have Chinese column names; columns are addressed by position
after the column count has been checked, and the names found are returned for inspection.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from . import datacut as dc
from . import dispositions as disp
from . import event_table as et
from .config import DEFAULT, EngineConfig
from .market import Event, Market, MarketDataError, Sec

BAR_COLS = ["date", "code", "open", "high", "low", "close", "preclose", "volume", "amount",
            "adjustflag", "turn", "tradestatus", "pctChg", "isST"]
# the only columns of a bar file whose VALUES the engine reads
READ_COLS = ["date", "open", "close", "preclose", "volume", "amount", "adjustflag", "tradestatus", "isST"]
OPTIONAL_COLS = ["filled_from_xsrc"]
FORBIDDEN_COLUMN_PARTS = ("factor", "adj_", "_adj", "adjclose", "adjopen", "hfq", "qfq", "foreadjust", "backadjust")
FORBIDDEN_DIRS = ("bs_adjust_factor",)
PANEL_START, PANEL_END = date(2008, 1, 1), date(2026, 6, 30)
# PANEL_END is the end of the raw window, NOT a default cut-off: every load needs an explicit
# data_cutoff (PLAN v0.8 C-8); the pilot passes datacut.PILOT_CUTOFF = 2021-12-31.

STATUS_IMPLEMENTED_SINA = "实施"                 # Sina: "implemented"
STATUS_IMPLEMENTED_EM = "实施分配"       # Eastmoney: "distribution implemented"


def _read_parquet(path: Path, columns=None) -> pd.DataFrame:
    """Single entry point for reading raw files: refuses vendor factor tables (FC-A4)."""
    p = Path(path)
    if any(part in FORBIDDEN_DIRS for part in p.parts):
        raise MarketDataError(f"the engine does not read vendor adjustment factors: {p}")
    return pd.read_parquet(p, columns=columns)


def _to_date(x):
    if x is None or (isinstance(x, float) and np.isnan(x)) or x is pd.NaT:
        return None
    if isinstance(x, date) and not isinstance(x, pd.Timestamp):
        return x
    try:
        s = str(x).strip()
        if not s or s in ("None", "NaT", "nan"):
            return None
        return date.fromisoformat(s[:10])
    except Exception:
        return None


def _num(series: pd.Series) -> np.ndarray:
    return pd.to_numeric(series.astype(str).str.strip().replace("", np.nan), errors="coerce").to_numpy(float)


def _fl(x) -> float:
    """Amount field of an event source: an empty or missing field means 'none of this component'
    (0); text that is not a number gives nan, which the event table drops and counts."""
    try:
        if x is None:
            return 0.0
        v = float(str(x).strip() or 0)
        return 0.0 if v != v else v
    except (TypeError, ValueError):
        return float("nan")


def _guard_path(p) -> None:
    if any(part in FORBIDDEN_DIRS for part in Path(p).parts):
        raise MarketDataError(f"the engine does not read vendor adjustment factors: {p}")


def all_trading_days(raw: Path, data_cutoff) -> list[date]:
    """Market trading days up to the data cut-off (C-8: the calendar is cut as well)."""
    p = Path(raw) / "universe" / "bs_trade_dates.parquet"
    _guard_path(p)
    df = dc.read_parquet_cut(p, "calendar_date", data_cutoff)
    return [date.fromisoformat(s) for s, f in zip(df["calendar_date"], df["is_trading_day"]) if str(f) == "1"]


def trading_days(raw: Path, data_cutoff) -> list[date]:
    cut = dc.require_cutoff(data_cutoff)
    return [x for x in all_trading_days(raw, cut) if PANEL_START <= x <= min(PANEL_END, cut)]


def load_bars(raw: Path, codes: list[str], days: list[date], rep: dict, full_calendar: Optional[list] = None,
              data_cutoff=None) -> dict:
    """Bars of `codes` on `days`.  `data_cutoff` (required, C-8): rows dated after it are
    dropped while the file is read (datacut.read_parquet_cut) and never reach the container;
    the delisting and listing dates of the snapshot table are used only if not after it."""
    cut = dc.require_cutoff(data_cutoff)
    if days and days[-1] > cut:
        raise dc.CutoffError("panel days extend beyond the data cut-off")
    idx = {x: i for i, x in enumerate(days)}
    T = len(days)
    basic = _read_parquet(raw / "universe" / "bs_stock_basic.parquet").set_index("code")
    before = [x for x in (full_calendar or []) if x < days[0]]
    secs: dict[str, Sec] = {}
    for code in codes:
        f = raw / "bars" / "bs_daily" / f"{code}.parquet"
        cr: dict = {}
        rep["codes"][code] = cr
        if not f.exists():
            rep["problems"].append(f"{code}: bar file missing")
            continue
        try:
            _guard_path(f)
            df = dc.read_parquet_cut(f, "date", cut)
        except dc.CutoffError:
            raise
        except Exception as e:                       # unreadable file (e.g. being written): listed, skipped
            rep["problems"].append(f"{code}: bar file unreadable ({type(e).__name__})")
            continue
        bad = [c for c in df.columns if any(p in str(c).lower() for p in FORBIDDEN_COLUMN_PARTS)]
        if bad:
            raise MarketDataError(f"{code}: bar file carries factor / adjusted-price columns {bad}; refused (FC-A4)")
        missing_cols = [c for c in BAR_COLS if c not in df.columns]
        if missing_cols:
            rep["problems"].append(f"{code}: missing columns {missing_cols}")
            continue
        opt = [c for c in OPTIONAL_COLS if c in df.columns]
        df = df[READ_COLS + opt]
        cr["rows"] = len(df)
        adj = sorted(set(df["adjustflag"].astype(str).str.strip()))
        cr["adjustflag_values"] = adj
        if adj != ["3"] and len(df):
            raise MarketDataError(f"{code}: adjustflag values {adj}; only unadjusted bars ('3') are accepted (FC-A4)")
        dts = [_to_date(s) for s in df["date"]]
        op, cl, pc = _num(df["open"]), _num(df["close"]), _num(df["preclose"])
        vol, amt = _num(df["volume"]), _num(df["amount"])
        ts = df["tradestatus"].astype(str).str.strip().to_numpy()
        st = df["isST"].astype(str).str.strip().to_numpy()
        fx = (df["filled_from_xsrc"].astype(str).str.strip().str.lower().isin(("1", "true")).to_numpy()
              if "filled_from_xsrc" in df.columns else None)
        cr["tradestatus_values"] = sorted(set(ts))
        cr["isST_values"] = sorted(set(st))
        cr["empty_volume_rows"] = int((df["volume"].astype(str).str.strip() == "").sum())
        o = np.full(T, np.nan); c = np.full(T, np.nan); p = np.full(T, np.nan); a = np.zeros(T)
        has = np.zeros(T, bool); ft = np.zeros(T, bool); vp = np.zeros(T, bool); s_ = np.zeros(T, bool)
        filled = np.zeros(T, bool)
        off_cal, dup = [], 0
        for k, dt in enumerate(dts):
            i = idx.get(dt)
            if i is None:
                off_cal.append(str(df["date"].iloc[k]))
                continue
            if has[i]:
                dup += 1
                continue
            has[i] = True
            o[i], c[i], p[i] = op[k], cl[k], pc[k]
            a[i] = amt[k] if np.isfinite(amt[k]) else 0.0
            ft[i] = ts[k] == "1"
            vp[i] = bool(np.isfinite(vol[k]) and vol[k] > 0)
            s_[i] = st[k] == "1"
            if fx is not None:
                filled[i] = bool(fx[k])
        rows_i = np.flatnonzero(has)
        first, last = (int(rows_i[0]), int(rows_i[-1])) if len(rows_i) else (None, None)
        gaps = [days[i].isoformat() for i in range(first, last + 1) if not has[i]] if first is not None else []
        traded = has & ft & vp
        # snapshot fields: a date after the data cut-off is a fact the run may not know (C-8)
        out_date = dc.clip_date(_to_date(basic.loc[code, "outDate"]), cut) if code in basic.index else None
        ipo = dc.clip_date(_to_date(basic.loc[code, "ipoDate"]), cut) if code in basic.index else None
        delist_i = None
        if out_date is not None:
            later = [i for i, x in enumerate(days) if x >= out_date]
            delist_i = later[0] if later else None
            if delist_i is not None and last is not None and last >= delist_i:
                cr["rows_on_or_after_outDate"] = int(has[delist_i:].sum())
                delist_i = last + 1 if last + 1 < T else None      # keep every row; listed until its last row
        lb = None
        if ipo is not None and full_calendar is not None:
            lb = sum(1 for x in before if x >= ipo) if ipo < days[0] else 0
            if ipo < days[0] and before and ipo < before[0]:
                lb = len(before)        # listed before the calendar file starts: at least this many days
        cr.update({
            "first_row": days[first].isoformat() if first is not None else None,
            "last_row": days[last].isoformat() if last is not None else None,
            "outDate": out_date.isoformat() if out_date else None, "ipoDate": ipo.isoformat() if ipo else None,
            "rows_off_calendar": off_cal, "duplicate_dates": dup, "missing_days_inside_span": gaps,
            "traded_days": int(traded.sum()), "suspended_flag_days": int((has & ~ft).sum()),
            "flag_suspended_with_volume": int((has & ~ft & vp).sum()),
            "flag_trading_zero_volume": int((has & ft & ~vp).sum()),
            "traded_open_missing_or_nonpositive": int((traded & ~(o > 0)).sum()),
            "traded_close_missing_or_nonpositive": int((traded & ~(c > 0)).sum()),
            "row_preclose_missing_or_nonpositive": int((has & ~(p > 0)).sum()),
            "st_days": int((has & s_).sum()), "rows_filled_from_xsrc": int(filled.sum()),
        })
        secs[code] = Sec(code, o, c, p, a, has, ft, vp, s_, delist_i,
                         filled_from_xsrc=filled if fx is not None else None, listed_days_before_panel=lb)
    return secs


# ------------------------------------------------------------------ event sources
def read_event_sources(raw: Path, codes: list[str], days: list[date], rep: dict, data_cutoff=None,
                       sources=("EV1", "EV2", "EV3", "rights")) -> tuple[list, list]:
    """(dividend rows of EV1-EV3 as event_table.SrcRow, rights rows as event_table.RightsRow),
    in per-share units.  EV3 (BaoStock, queried by ex-date year) has no status field: a row
    with an ex-date counts as implemented.

    Data cut-off (C-8, required): a row enters only if its ex-date is <= the cut-off, or it
    has no ex-date and its announcement date is <= the cut-off (datacut.read_events_cut); other
    date fields after the cut-off are set to missing.  `sources` restricts the sources read
    (the pilot reads EV1, EV2 and the Sina rights table, PLAN 13A)."""
    cut = dc.require_cutoff(data_cutoff)
    rows, rights = [], []
    info = rep.setdefault("event_sources", {"EV1_files": 0, "EV2_files": 0, "EV3_files": 0, "rights_files": 0,
                                            "EV1_rows": 0, "EV2_rows": 0, "EV3_rows": 0, "rights_rows": 0,
                                            "column_names": {}, "sources_read": list(sources)})
    for code in codes:
        f = raw / "factors_events" / "em_fhps" / f"{code}.parquet"
        if "EV1" in sources and f.exists():
            df = dc.read_events_cut(f, 16, 14, cut, other_date_cols=(15, 18, 0, 1), counts=info, by_position=True)
            if df.shape[1] != 19:
                rep["problems"].append(f"{code}: em_fhps has {df.shape[1]} columns, expected 19")
            else:
                info["EV1_files"] += 1
                info["column_names"]["EV1"] = [str(x) for x in df.columns]
                for _, r in df.iterrows():
                    st = str(r.iloc[17]).strip()
                    rows.append(et.SrcRow("EV1", code, _to_date(r.iloc[16]), _to_date(r.iloc[15]),
                                          _fl(r.iloc[5]) / 10.0, _fl(r.iloc[2]) / 10.0,
                                          implemented=(st == STATUS_IMPLEMENTED_EM), status=st,
                                          announce_date=_to_date(r.iloc[14]) or _to_date(r.iloc[18])))
                    info["EV1_rows"] += 1
        f = raw / "factors_events" / "sina_dividend" / f"{code}.parquet"
        if "EV2" in sources and f.exists():
            df = dc.read_events_cut(f, 5, 0, cut, other_date_cols=(6, 7), counts=info, by_position=True)
            if df.shape[1] != 8:
                rep["problems"].append(f"{code}: sina_dividend has {df.shape[1]} columns, expected 8")
            else:
                info["EV2_files"] += 1
                info["column_names"]["EV2"] = [str(x) for x in df.columns]
                for _, r in df.iterrows():
                    st = str(r.iloc[4]).strip()
                    rows.append(et.SrcRow("EV2", code, _to_date(r.iloc[5]), _to_date(r.iloc[6]),
                                          _fl(r.iloc[3]) / 10.0, (_fl(r.iloc[1]) + _fl(r.iloc[2])) / 10.0,
                                          implemented=(st == STATUS_IMPLEMENTED_SINA), status=st,
                                          announce_date=_to_date(r.iloc[0])))
                    info["EV2_rows"] += 1
        f = raw / "factors_events" / "bs_dividend" / f"{code}.parquet"
        if "EV3" in sources and f.exists():
            df = dc.read_events_cut(f, "dividOperateDate", "dividPlanAnnounceDate", cut,
                                    other_date_cols=("dividRegistDate", "dividPayDate"), counts=info)
            need = ["dividRegistDate", "dividOperateDate", "dividPayDate", "dividCashPsBeforeTax", "dividStocksPs",
                    "dividReserveToStockPs", "dividPlanAnnounceDate"]
            if any(c not in df.columns for c in need):
                if len(df):
                    rep["problems"].append(f"{code}: bs_dividend lacks expected columns")
            else:
                info["EV3_files"] += 1
                for _, r in df.iterrows():
                    ex = _to_date(r["dividOperateDate"])
                    rows.append(et.SrcRow("EV3", code, ex, _to_date(r["dividRegistDate"]),
                                          _fl(r["dividCashPsBeforeTax"]),
                                          _fl(r["dividStocksPs"]) + _fl(r["dividReserveToStockPs"]),
                                          implemented=ex is not None, status="has ex-date" if ex else "no ex-date",
                                          pay_date=_to_date(r["dividPayDate"]),
                                          announce_date=_to_date(r["dividPlanAnnounceDate"])))
                    info["EV3_rows"] += 1
        f = raw / "factors_events" / "sina_rights" / f"{code}.parquet"
        if "rights" in sources and f.exists():
            # keyed by the ex-rights date (col 4), else by the announcement date (col 0); the
            # record date (col 5) and the other dates are cleared if they lie after the cut-off
            df = dc.read_events_cut(f, 4, 0, cut, other_date_cols=(5, 6, 7, 8), counts=info, by_position=True)
            if len(df) and df.shape[1] != 10:
                rep["problems"].append(f"{code}: sina_rights has {df.shape[1]} columns, expected 10")
            elif len(df):
                info["rights_files"] += 1
                info["column_names"]["rights"] = [str(x) for x in df.columns]
                for _, r in df.iterrows():
                    ratio, price = _fl(r.iloc[1]) / 10.0, _fl(r.iloc[2])
                    rights.append(et.RightsRow(code, ratio if np.isfinite(ratio) else None,
                                               price if np.isfinite(price) else None,
                                               _to_date(r.iloc[4]), _to_date(r.iloc[5]), _to_date(r.iloc[0])))
                    info["rights_rows"] += 1
    return rows, rights


def _sina_single_source(rows: list, rights: list, days: list[date], rep: dict) -> list[Event]:
    """v0.6 pipeline exercise with the v0.7 filter (G-2): Sina only."""
    events: list[Event] = []
    ev_rep = {"dist_events": 0, "rights_events": 0, "skipped": [], "not_in_table": []}
    for r in rows:
        if r.source != "EV2":
            continue
        if r.ex_date is None:
            if r.implemented:
                ev_rep["not_in_table"].append(f"{r.code} announced {r.announce_date}: status implemented but no ex-date")
            continue
        if not r.implemented:
            ev_rep["not_in_table"].append(f"{r.code} {r.ex_date}: ex-date present but status {r.status!r} (hand check)")
            continue
        if not (days[0] < r.ex_date <= days[-1]):
            continue
        if not np.isfinite(r.bonus) or not np.isfinite(r.gross_cash) or (r.bonus == 0 and r.gross_cash == 0):
            ev_rep["skipped"].append(f"{r.code} {r.ex_date}: empty or non-finite amounts")
            continue
        events.append(Event(r.code, "dist", ex_date=r.ex_date, record_date=r.record_date, gross_cash=r.gross_cash,
                            phi=1.0 + r.bonus))
        ev_rep["dist_events"] += 1
    for r in rights:
        if r.record_date is None and r.ex_date is None:
            ev_rep["not_in_table"].append(f"{r.code} announced {r.announce_date}: rights row without dates (hand check)")
            continue
        if (r.record_date or r.ex_date) < days[0] or (r.record_date or r.ex_date) > days[-1]:
            continue
        events.append(Event(r.code, "rights", ex_date=r.ex_date, record_date=r.record_date, rights_price=r.price,
                            rights_ratio=r.ratio, announce_date=r.announce_date))
        ev_rep["rights_events"] += 1
    rep["events"] = ev_rep
    return events


def load_market(raw: Path, codes: list[str], events: str = "sina", cfg: EngineConfig = DEFAULT,
                pending: Optional[str] = None, resolutions: Optional[dict] = None, dispositions_path=None,
                apply_dispositions: bool = True, *, data_cutoff, event_sources=("EV1", "EV2", "EV3", "rights"),
                undated_rights: Optional[str] = None) -> tuple[Market, dict]:
    """Returns (market, report).  `report` lists what was found; nothing is repaired.

    `data_cutoff` (keyword, REQUIRED; PLAN v0.8 C-8): no bar, calendar day, event or snapshot
    date after it is read; the panel ends on the last market trading day <= the cut-off.
    `pending` / `undated_rights` default to the production configuration of PLAN v0.8 H-2
    (cfg.event_pending = "U", cfg.event_undated_rights = "exclude", no resolutions)."""
    if events not in ("sina", "merged", "none"):
        raise ValueError(events)
    cut = dc.require_cutoff(data_cutoff)
    pending = cfg.event_pending if pending is None else pending
    undated_rights = cfg.event_undated_rights if undated_rights is None else undated_rights
    raw = Path(raw)
    full = all_trading_days(raw, cut)
    days = [x for x in full if PANEL_START <= x <= min(PANEL_END, cut)]
    rep: dict = {"n_days": len(days), "first_day": days[0].isoformat(), "last_day": days[-1].isoformat(),
                 "data_cutoff": cut.isoformat(), "codes": {}, "problems": [], "events_mode": events}
    secs = load_bars(raw, codes, days, rep, full, data_cutoff=cut)
    market = Market(days, secs)
    market.data_cutoff = cut
    have = [c for c in codes if c in secs]
    if events != "none":
        rows, rights = read_event_sources(raw, have, days, rep, data_cutoff=cut, sources=event_sources)
        if events == "sina":
            for ev in _sina_single_source(rows, rights, days, rep):
                market.add_event(ev)
        else:
            table = et.build(market, rows, rights, cfg, resolutions=resolutions, pending=pending,
                             undated_rights=undated_rights)
            table.install(market)
            rep["event_table"] = {"counts": table.counts, "by_year": table.by_year, "hash": table.content_hash(),
                                  "hand_check": table.hand_check, "flags": table.flags,
                                  "urs": sorted((c, d.isoformat()) for c, d in table.urs),
                                  "u_spans": {c: [(a.isoformat(), b.isoformat(), w) for a, b, w in v]
                                              for c, v in table.u_spans.items()}}
    if apply_dispositions:
        table_d, probs = disp.read_table(dispositions_path)
        drep = disp.apply(market, table_d)
        drep["table_problems"] = probs
        rep["dispositions"] = drep
    rep["event_problems"] = list(market.problems)
    return market, rep

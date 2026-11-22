"""Data layer of the pilot: list, readiness, market (engine), feature panel (feature library), and the
derived arrays every later step uses.  Every raw read goes through the two libraries' cut-off loaders
(engine.io_baostock.load_market and features.store.RawStore), which refuse rows after the data cut-off
(PLAN v0.8 C-8).  This module opens no raw file itself except the pilot list and the fetch manifest
(experiments/results/data_fetch/manifest.jsonl, read only to see which names have their event files).
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

from engine import datacut as dc
from engine import io_baostock as eio
from engine import universe as uni
from engine.config import EngineConfig
from features import market_panel, registry
from features.bars import own_adjust_factor

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "experiments" / "data" / "raw"
FETCH_MANIFEST = ROOT / "experiments" / "results" / "data_fetch" / "manifest.jsonl"


def sha256_file(p) -> str:
    return dc.file_sha256(p)


# ------------------------------------------------------------------ list and readiness
def pilot_list(cfg) -> tuple[list[str], dict]:
    p = ROOT / cfg.universe_csv
    h = sha256_file(p)
    if h != cfg.universe_sha256:
        raise RuntimeError(f"pilot list hash {h} differs from the hash recorded in PLAN 13A ({cfg.universe_sha256})")
    df = pd.read_csv(p, dtype=str)
    codes = list(df["code"])
    if cfg.codes_subset:
        bad = [c for c in cfg.codes_subset if c not in set(codes)]
        if bad:
            raise ValueError(f"subset codes not in the pilot list: {bad[:5]}")
        codes = [c for c in codes if c in set(cfg.codes_subset)]
    return codes, {"list_file": str(p), "list_sha256": h, "n_list": len(df), "n_used": len(codes),
                   "board_counts": df[df["code"].isin(codes)]["board"].value_counts().to_dict()}


def fetch_status() -> dict:
    """{(source, code): status} of the factors_events stage from the fetch manifest (last record wins)."""
    out = {}
    if not FETCH_MANIFEST.exists():
        return out
    with open(FETCH_MANIFEST, encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:            # a line being written
                continue
            if r.get("stage") == "factors_events":
                out[(r.get("source"), r.get("unit"))] = r.get("status")
    return out


EVENT_SOURCES_PILOT = ("em_fhps", "sina_dividend", "sina_rights")    # EV1, EV2 and the Sina rights table (13A)


def readiness(codes: list[str], fresh_minutes: float = 15.0) -> pd.DataFrame:
    """Per name: bar file present (and not modified in the last minutes), and for each pilot event source
    whether the fetch has finished it (manifest status ok or empty).  The vendor factor table is NOT
    needed (FC-A4: no vendor factor is read anywhere) and is reported only as information."""
    st = fetch_status()
    now = time.time()
    rows = []
    for c in codes:
        f = RAW / "bars" / "bs_daily" / f"{c}.parquet"
        bar_ok = f.exists() and (now - f.stat().st_mtime) > fresh_minutes * 60
        r = {"code": c, "bars": bar_ok}
        for s in EVENT_SOURCES_PILOT:
            r[s] = st.get((s, c)) in ("ok", "empty")
        r["bs_factor_info_only"] = st.get(("bs_factor", c)) in ("ok", "empty")
        r["ready"] = bar_ok and all(r[s] for s in EVENT_SOURCES_PILOT)
        rows.append(r)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ market
def engine_config(cfg) -> EngineConfig:
    return EngineConfig(H=cfg.H, K=cfg.K, W0=cfg.W0, universe_size=cfg.N_U)


def load_market(cfg, codes: list[str], raw: Path = RAW):
    """Engine market with the event table of PLAN 3.11 / 13A: EV1 + EV2 (+ Sina rights), rule 2a, pending
    rule 'U', no resolution input; dispositions table absent -> write-off (U33)."""
    ecfg = engine_config(cfg)
    m, rep = eio.load_market(raw, codes, events="merged", cfg=ecfg, data_cutoff=cfg.cut(),
                             event_sources=("EV1", "EV2", "rights"))
    return m, rep


# ------------------------------------------------------------------ feature panel
def build_panel(cfg, codes: list[str], panel_dir: Path, raw: Path = RAW, overwrite: bool = False) -> pd.DataFrame:
    dcut = cfg.decision_cutoff or None
    man = market_panel.build_market_panel(codes, str(panel_dir), cutoff=dcut, root=str(raw), n_jobs=cfg.n_jobs,
                                          overwrite=overwrite, progress_every=100, data_cutoff=cfg.cut(),
                                          zo_codes=codes)
    return man


def feature_columns() -> dict:
    cat = registry.catalogue()
    g = lambda grp, role=None: [n for n, gg, rr in zip(cat["name"], cat["group"], cat["role"])   # noqa: E731
                                if gg == grp and (role is None or rr == role)]
    minus_z = g("B0", "primary") + g("R_H-sum") + g("R_H-hist") + g("R_O")
    return {"-Z": minus_z, "Z_H": g("Z_H", "primary"), "Z_O": g("Z_O", "primary")}


# ------------------------------------------------------------------ derived arrays
class Derived:
    """Dense day x name arrays from the engine market (no raw file is opened here)."""

    def __init__(self, market, codes: list[str], cfg):
        self.m = market
        self.codes = [c for c in codes if c in market.secs]
        self.k = {c: j for j, c in enumerate(self.codes)}
        T, n = market.T, len(self.codes)
        self.T, self.n = T, n
        self.aopen = np.full((T, n), np.nan)
        self.aclose = np.full((T, n), np.nan)
        self.traded = np.zeros((T, n), bool)
        self.adv = np.full((T, n), np.nan)       # ADV_t (engine definition, data <= t-1)
        self.vol20 = np.full((T, n), np.nan)     # std of daily adjusted close returns, 20 rows ending t-1
        for c, j in self.k.items():
            s = market.secs[c]
            rows = np.flatnonzero(s.has_row)
            if len(rows) == 0:
                continue
            F = own_adjust_factor(s.close[rows].astype(float), s.preclose[rows].astype(float))
            tr = s.has_row & s.flag_trading & s.vol_pos
            if s.delist_i is not None:
                tr[s.delist_i:] = False
            self.traded[:, j] = tr
            ac = np.full(T, np.nan)
            ac[rows] = s.close[rows] * F
            ao = np.full(T, np.nan)
            ao[rows] = s.open[rows] * F
            ao[~tr] = np.nan
            self.aclose[:, j] = ac
            self.aopen[:, j] = ao
            # 20-row volatility of the name's rows, valid for the decision day after the last row
            r = pd.Series(ac[rows]).pct_change()
            v = r.rolling(20, min_periods=20).std().to_numpy()
            nxt = np.minimum(rows + 1, T - 1)
            ok = rows + 1 < T
            self.vol20[nxt[ok], j] = v[ok]
            # ADV: mean amount of the 20 most recent traded days dated <= t-1 (engine.fills.adv, primary)
            ix = np.flatnonzero(tr)
            if len(ix):
                cs = np.r_[0.0, np.cumsum(np.nan_to_num(s.amount[ix]))]
                hi = np.searchsorted(ix, np.arange(T), side="left")
                lo = np.maximum(0, hi - 20)
                cnt = hi - lo
                with np.errstate(all="ignore"):
                    a = (cs[hi] - cs[lo]) / cnt
                self.adv[:, j] = np.where(cnt > 0, a, np.nan)
        # forward H-day open-to-open total return (base target)
        H = cfg.H
        self.fwd = np.full((T, n), np.nan)
        with np.errstate(all="ignore"):
            self.fwd[:T - H] = self.aopen[H:] / self.aopen[:T - H] - 1.0
        # daily close-to-close adjusted return (for TREND's equal-weight index)
        with np.errstate(all="ignore"):
            self.ret1 = np.vstack([np.full((1, n), np.nan), self.aclose[1:] / self.aclose[:-1] - 1.0])


def universe_and_candidates(market, codes: list[str], cfg, first_i: int, last_i: int) -> tuple[dict, dict, dict]:
    """Membership by month (U-LIQ-P, N_U = 300) and candidate sets C_t for decision days first_i..last_i."""
    ecfg = engine_config(cfg)
    pan = uni.Panel(market, codes=[c for c in codes if c in market.secs])
    by_month, reports = uni.membership_by_month(pan, ecfg)
    cand, crep = {}, {}
    for i in range(first_i, last_i + 1):
        d = market.days[i]
        mem = by_month.get((d.year, d.month), [])
        c, r = uni.candidates(pan, i, mem, ecfg)
        cand[i] = c
        crep[i] = r
    return by_month, cand, {"screens": reports, "candidate_counts": crep}


def load_feature_rows(panel_dir: Path, market, cand: dict, cols: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Long matrix of feature rows for (decision day i, code) in the candidate sets.
    Returns (day index array, code array (object), float32 matrix rows x cols)."""
    need: dict[str, set] = {}
    for i, cs in cand.items():
        for c in cs:
            need.setdefault(c, set()).add(i)
    di, cc, mats = [], [], []
    for c in sorted(need):
        p = panel_dir / "features" / f"{c}.parquet"
        if not p.exists():
            continue
        f = pd.read_parquet(p, columns=[x for x in cols])
        idx = np.array([market.idx.get(d.date(), -1) for d in f.index])
        keep = np.isin(idx, np.fromiter(need[c], int))
        if not keep.any():
            continue
        di.append(idx[keep])
        cc.append(np.full(int(keep.sum()), c, dtype=object))
        mats.append(f.values[keep].astype(np.float32))
    if not mats:
        return np.zeros(0, int), np.zeros(0, object), np.zeros((0, len(cols)), np.float32)
    return np.concatenate(di), np.concatenate(cc), np.vstack(mats)

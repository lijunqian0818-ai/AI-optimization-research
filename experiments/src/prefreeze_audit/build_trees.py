"""Pre-freeze point-in-time audit: build the two raw trees of the in-development perturbation test.

Source: the cut tree A of the pilot's cut-off invariance test (built on 2026-11-16 by
pilot/cutoff_invariance.py from the loaders' own cut readers; it holds no row dated after 2021-12-31).
Every file of tree A is read here again through the cut readers of engine.datacut with cut-off
2021-12-31, so that no row dated after 2021-12-31 can be loaded even if one were present.

  tree_R   reference: tree A as read (bit-identical content for rows <= 2021-12-31)
  tree_P   perturbed: every datum dated in (C, 2021-12-31] (C = in-development cut-off, default
           2019-12-31) is altered; rows dated <= C are untouched:
             bars          prices x exp(N(0, 0.2)), volume / amount / turn x exp(N(0, 0.5)), pctChg noise,
                           tradestatus flipped with p = 0.05, isST flipped with p = 0.03, 2 % of rows deleted
             index bars    prices x exp(N(0, 0.2))
             events        amounts of rows with ex-date (or, without ex-date, announcement date) > C
                           x U(0.2, 3); one fabricated event per name (copy of its last row, all dates set
                           to a random trading day in (C, 2021-12-31])
             Z_O tables    rows dated > C: numeric columns x exp(N(0, 0.7)), the code column permuted
                           among those rows; up to 100 fabricated rows per period file (copies of random
                           rows dated > C, code set to a random smoke name, date to a random trading day of
                           the file's period inside (C, 2021-12-31])
             listing table outDate of ~25 % of the smoke names set to a random trading day in
                           (C, 2021-12-31] (existing outDates in that range moved within it)
           The trading calendar is not altered (it is pre-announced information; altering it would
           move every day index).

No pipeline output, return, label or feature is computed here.

    experiments/.venv/Scripts/python.exe -X utf8 experiments/src/prefreeze_audit/build_trees.py \
        --source <tree_A> --work <dir> --codes-file <smoke_codes.txt> [--inner-cutoff 2019-12-31]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import numpy as np          # noqa: E402
import pandas as pd         # noqa: E402

from engine import datacut as dc     # noqa: E402

DATA_CUT = "2021-12-31"
EVENT_KEYS = {"em_fhps": (16, 14, (15, 18, 0, 1)), "sina_dividend": (5, 0, (6, 7)), "sina_rights": (4, 0, (5, 6, 7, 8))}
ZO = {"lhb_detail": ("上榜日", "代码"), "lhb_jgmmtj": ("上榜日期", "代码"), "dzjy_mrmx": ("交易日期", "证券代码"),
      "ins_raw": ("NOTICE_DATE", "SECURITY_CODE")}
INDEXES = ("sh.000001", "sz.399001", "sz.399006")


def _dates(s) -> pd.Series:
    return pd.to_datetime(pd.Series(s).astype(str).str.slice(0, 10), errors="coerce")


def _fmt_like(orig: pd.Series, vals: np.ndarray) -> list:
    return [f"{v:.6f}" if np.isfinite(v) else "" for v in vals]


def build(src: Path, work: Path, codes: list, C: str, seed: int = 20261117) -> dict:
    Ct = pd.Timestamp(C)
    R, P = work / "tree_R", work / "tree_P"
    for t in (R, P):
        if t.exists():
            shutil.rmtree(t)
    rng = np.random.default_rng(seed)
    info = {"source": str(src), "inner_cutoff": C, "data_cutoff": DATA_CUT, "seed": seed, "counts": {}}
    cnt = info["counts"]

    def put(rel: str, dfR: pd.DataFrame, dfP: pd.DataFrame):
        for root, df in ((R, dfR), (P, dfP)):
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(p, index=False)

    # calendar (unchanged) and listing table
    cal = dc.read_parquet_cut(src / "universe" / "bs_trade_dates.parquet", "calendar_date", DATA_CUT)
    put("universe/bs_trade_dates.parquet", cal, cal)
    tdays = pd.to_datetime(cal.loc[cal["is_trading_day"].astype(str) == "1", "calendar_date"])
    late = tdays[(tdays > Ct) & (tdays <= pd.Timestamp(DATA_CUT))].reset_index(drop=True)
    basic = pd.read_parquet(src / "universe" / "bs_stock_basic.parquet")
    for c in ("ipoDate", "outDate"):           # tree A blanked dates after 2021-12-31; check it again
        bad = [x for x in basic[c] if str(x).strip() and dc.clip_date(x, DATA_CUT) is None]
        if bad:
            raise RuntimeError(f"listing table carries {c} after {DATA_CUT}")
    bP = basic.copy()
    sm = bP["code"].isin(codes).to_numpy()
    od = _dates(bP["outDate"])
    pick = sm & (rng.random(len(bP)) < 0.25) & (od.isna() | (od > Ct)).to_numpy()
    bP.loc[pick, "outDate"] = [str(pd.Timestamp(d).date()) for d in rng.choice(late.to_numpy(), int(pick.sum()))]
    cnt["listing_outDate_set_in_(C,2021]"] = int(pick.sum())
    put("universe/bs_stock_basic.parquet", basic, bP)

    # bars
    nb = nd = 0
    for c in codes:
        f = src / "bars" / "bs_daily" / f"{c}.parquet"
        df = dc.read_parquet_cut(f, "date", DATA_CUT)
        dP = df.copy()
        m = (_dates(dP["date"]) > Ct).to_numpy()
        k = int(m.sum())
        if k:
            for col in ("open", "high", "low", "close", "preclose"):
                v = pd.to_numeric(dP.loc[m, col], errors="coerce").to_numpy(float) * np.exp(rng.normal(0, 0.2, k))
                dP.loc[m, col] = _fmt_like(dP[col], v)
            for col in ("volume", "amount", "turn"):
                v = pd.to_numeric(dP.loc[m, col], errors="coerce").to_numpy(float) * np.exp(rng.normal(0, 0.5, k))
                dP.loc[m, col] = [str(int(x)) if (col == "volume" and np.isfinite(x)) else (f"{x:.6f}" if np.isfinite(x) else "")
                                  for x in v]
            dP.loc[m, "pctChg"] = [f"{x:.4f}" for x in rng.normal(0, 5, k)]
            ts = dP.loc[m, "tradestatus"].astype(str).to_numpy()
            flip = rng.random(k) < 0.05
            dP.loc[m, "tradestatus"] = np.where(flip, np.where(ts == "1", "0", "1"), ts)
            st = dP.loc[m, "isST"].astype(str).to_numpy()
            flip = rng.random(k) < 0.03
            dP.loc[m, "isST"] = np.where(flip, np.where(st == "1", "0", "1"), st)
            drop = np.zeros(len(dP), bool)
            drop[np.flatnonzero(m)] = rng.random(k) < 0.02
            nd += int(drop.sum())
            dP = dP.loc[~drop].reset_index(drop=True)
            nb += k
        put(f"bars/bs_daily/{c}.parquet", df, dP)
    cnt["bar_rows_perturbed"] = nb
    cnt["bar_rows_deleted"] = nd

    for ix in INDEXES:
        f = src / "index" / "bs_index_daily" / f"{ix}.parquet"
        df = dc.read_parquet_cut(f, "date", DATA_CUT)
        dP = df.copy()
        m = (_dates(dP["date"]) > Ct).to_numpy()
        k = int(m.sum())
        for col in ("open", "high", "low", "close", "preclose"):
            v = pd.to_numeric(dP.loc[m, col], errors="coerce").to_numpy(float) * np.exp(rng.normal(0, 0.2, k))
            dP.loc[m, col] = _fmt_like(dP[col], v)
        put(f"index/bs_index_daily/{ix}.parquet", df, dP)

    # corporate-action events
    ne = nf = 0
    for sub, (ex, ann, other) in EVENT_KEYS.items():
        for c in codes:
            f = src / "factors_events" / sub / f"{c}.parquet"
            if not f.exists():
                continue
            df = dc.read_events_cut(f, ex, ann, DATA_CUT, other_date_cols=other, by_position=True)
            dP = df.copy()
            cols = list(dP.columns)
            exd, annd = _dates(dP[cols[ex]]), _dates(dP[cols[ann]])
            m = ((exd > Ct) | (exd.isna() & (annd > Ct))).to_numpy()
            datecols = {cols[ex], cols[ann]} | {cols[o] for o in other}
            if m.any():
                for col in cols:
                    if col in datecols:
                        continue
                    if pd.api.types.is_float_dtype(dP[col]):
                        dP.loc[m, col] = dP.loc[m, col].to_numpy(float) * rng.uniform(0.2, 3.0, int(m.sum()))
                    elif pd.api.types.is_integer_dtype(dP[col]):
                        dP.loc[m, col] = (dP.loc[m, col].to_numpy() * rng.integers(1, 4, int(m.sum()))).astype(dP[col].dtype)
                ne += int(m.sum())
            if len(dP):
                g = dP.iloc[[-1]].copy().reset_index(drop=True)
                d = pd.Timestamp(rng.choice(late.to_numpy()))
                for k_ in [ex, ann] + list(other):
                    col = cols[k_]
                    if pd.api.types.is_datetime64_any_dtype(dP[col]):
                        g[col] = pd.Series([d], dtype=dP[col].dtype)
                    else:
                        g[col] = [d.date()]
                try:
                    dP = pd.concat([dP, g], ignore_index=True)
                    dP.to_parquet(work / "_probe.parquet", index=False)
                    nf += 1
                except Exception:                   # a dtype that cannot hold the value: no fabricated row
                    dP = dP.iloc[:-1] if len(dP) > len(df) else dP
            put(f"factors_events/{sub}/{c}.parquet", df, dP)
    (work / "_probe.parquet").unlink(missing_ok=True)
    cnt["event_rows_perturbed"] = ne
    cnt["event_rows_fabricated"] = nf

    # Z_O tables
    six = [c.split(".")[1] for c in codes]
    for sub, (dcol, ccol) in ZO.items():
        nz = nzf = 0
        for f in sorted((src / "zo" / sub).glob("*.parquet")):
            if not (f.stem.isdigit() and dc.period_ok(f.stem, DATA_CUT)):
                continue
            df = dc.read_parquet_cut(f, dcol, DATA_CUT)
            dP = df.copy()
            m = (_dates(dP[dcol]) > Ct).to_numpy()
            k = int(m.sum())
            if k:
                for col in dP.columns:
                    if col == dcol:
                        continue
                    if pd.api.types.is_float_dtype(dP[col]):
                        dP.loc[m, col] = dP.loc[m, col].to_numpy(float) * np.exp(rng.normal(0, 0.7, k))
                    elif pd.api.types.is_integer_dtype(dP[col]) and col != "序号":
                        dP.loc[m, col] = np.round(dP.loc[m, col].to_numpy(float) * np.exp(rng.normal(0, 0.7, k))).astype(dP[col].dtype)
                idx = np.flatnonzero(m)
                dP.loc[m, ccol] = dP.loc[m, ccol].to_numpy()[rng.permutation(k)]
                nz += k
                nfab = min(100, k)          # per period file (monthly: up to 24 x 100; yearly: 2 x 100)
                g = dP.iloc[rng.choice(idx, nfab)].copy().reset_index(drop=True)
                g[ccol] = rng.choice(six, nfab)
                ds = pd.to_datetime(rng.choice(late.to_numpy(), nfab))
                per = f.stem
                if len(per) == 6:     # monthly file: keep the fabricated date inside the file's month
                    inm = late[(late.dt.year == int(per[:4])) & (late.dt.month == int(per[4:]))]
                    ds = pd.to_datetime(rng.choice(inm.to_numpy(), nfab)) if len(inm) else ds
                else:
                    iny = late[late.dt.year == int(per)]
                    ds = pd.to_datetime(rng.choice(iny.to_numpy(), nfab)) if len(iny) else ds
                if isinstance(dP[dcol].iloc[0], str):
                    g[dcol] = [d.strftime("%Y-%m-%d") + (" 00:00:00" if len(str(dP[dcol].iloc[0])) > 10 else "") for d in ds]
                else:
                    g[dcol] = [d.date() for d in ds]
                dP = pd.concat([dP, g], ignore_index=True)
                nzf += nfab
            put(f"zo/{sub}/{f.name}", df, dP)
        cnt[f"zo_{sub}_rows_perturbed"] = nz
        cnt[f"zo_{sub}_rows_fabricated"] = nzf
    return info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--codes-file", required=True)
    ap.add_argument("--inner-cutoff", default="2019-12-31")
    a = ap.parse_args()
    codes = [l.strip() for l in open(a.codes_file, encoding="utf-8") if l.strip()]
    info = build(Path(a.source), Path(a.work), codes, a.inner_cutoff)
    print(json.dumps(info, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

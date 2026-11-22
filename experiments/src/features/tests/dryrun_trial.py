"""Dry run on the trial stocks already on disk (read-only; no request is sent).

Checks only: can every feature be computed, missing rates, value ranges,
warm-up, the look-ahead test on real rows, and descriptive diagnostics of the
inputs. NOTHING here relates a feature to a later return; no label, forward
return, IC or performance number is computed or read.

v0.7: the Z_O tables are complete on disk, so the run uses the production
setting (strict coverage); the look-ahead days of each stock include one day
on which an event of EACH class (LHB, BLK, INS) has just become usable; the
ADV denominator is compared with `engine.fills.adv` day by day; the panel of
the trial names is assembled with market_panel (written to a temporary
folder, only its report is kept).

Usage (project root):
  experiments/.venv/Scripts/python.exe -X utf8 experiments/src/features/tests/dryrun_trial.py [--lookahead-days 2]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from features import panel, registry, store, lookahead, zo, zh, market_panel   # noqa: E402
from features.bars import prepare_bars                                         # noqa: E402
from engine import datacut as dc                                               # noqa: E402

DATA_CUTOFF = dc.PILOT_CUTOFF       # v0.8 rerun: the lead's constraint (no data after 2021-12-31)


def _far(cal, raw):
    last = pd.to_datetime(raw["date"]).max()
    try:
        return cal.next(last)
    except KeyError:                  # the calendar ends at the data cut-off
        return cal.days[-1]
from features.config import ZO_LAG                                             # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(ROOT, "experiments", "results", "feature_tests")
EVAL_START = pd.Timestamp("2010-01-01")


def trial_codes():
    p = os.path.join(ROOT, "experiments", "results", "data_fetch", "trial_codes.txt")
    codes = []
    for line in open(p, encoding="utf-8"):
        s = line.split("#")[0].strip()
        if not s:
            continue
        c = s.split(".")[-1]
        codes.append(("sh." if c.startswith(("6",)) else "sz.") + c)
    return codes


def build(code, raw_bars, cal, cutoff, raw_index, tables, ipo=None):
    return panel.build_stock_features(code, raw_bars, cal, cutoff, raw_index, tables, ipo_date=ipo)


def bounds_check(f: pd.DataFrame) -> list[dict]:
    """Logical bounds every value must satisfy (no statistics involved)."""
    out = []

    def chk(cols, lo, hi, what):
        for c in cols:
            x = f[c].dropna()
            bad = int(((x < lo - 1e-9) | (x > hi + 1e-9)).sum())
            out.append({"feature": c, "rule": what, "n": int(len(x)), "violations": bad})
    cols = list(f.columns)
    chk([c for c in cols if "_ind_" in c or c.endswith(("_has_prior", "_data")) or c.startswith("ro_ins_regime")
         or c.startswith(("zo_lhb_multi_", "diag_")) or c in ("ro_lhb_thr15", "ro_lhb_top5", "ro_exch_sse")], 0, 1,
        "in {0,1}")
    chk([c for c in cols if c.endswith("days_since")], 0, 60, "in [0,60]")
    for w in (1, 5, 20):
        chk([c for c in cols if c.endswith(f"_cnt_{w}")], 0, w, f"in [0,{w}]")
    chk(["zh_chip_pr", "zh_chip_overhead"], 0, 1, "in [0,1]")
    chk(["zh_chip_band90", "zh_chip_band70"], 0, np.inf, ">= 0")
    chk([c for c in cols if c.startswith(("b0_RSQR", "b0_RANK", "b0_RSV", "b0_CNTP", "b0_CNTN", "b0_SUMP", "b0_SUMN",
                                           "b0_VSUMP", "b0_VSUMN", "b0_IMAX", "b0_IMIN"))], 0, 1, "in [0,1]")
    chk([c for c in cols if c.startswith(("b0_CORR", "b0_CORD", "b0_CNTD", "b0_SUMD", "b0_VSUMD", "b0_IMXD"))], -1, 1,
        "in [-1,1]")
    chk([c for c in cols if c.startswith(("rh_pos_",))], 0, 1, "in [0,1]")
    chk([c for c in cols if c.startswith(("rh_turn_", "ro_turn_max", "ro_amp_"))], 0, np.inf, ">= 0")
    chk([c for c in cols if c.startswith("zo_ins_buy_") and c[-1].isdigit() and "_ind_" not in c], 0, np.inf, ">= 0")
    chk([c for c in cols if c.startswith("zo_ins_sell_") and c[-1].isdigit() and "_ind_" not in c], -np.inf, 0, "<= 0")
    chk([c for c in cols if c.startswith("zo_blk_amt_")], 0, np.inf, ">= 0")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lookahead-days", type=int, default=2, help="random decision days per stock (event days are added)")
    ap.add_argument("--skip-panel", action="store_true")
    ap.add_argument("--codes", default="")
    ap.add_argument("--skip-lookahead", action="store_true")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    st = store.RawStore(data_cutoff=DATA_CUTOFF)      # PLAN v0.8 C-8: no raw row after 2021-12-31
    cal = st.calendar()
    tables = st.zo_tables()
    cat = registry.catalogue().set_index("name")
    codes = [c for c in (args.codes.split(",") if args.codes else trial_codes()) if c in set(st.bar_codes())]
    summary = {"run_at": time.strftime("%Y-%m-%d %H:%M:%S"), "data_cutoff": str(DATA_CUTOFF), "n_codes": len(codes), "codes": codes,
               "zo_coverage": {k: sorted(v) for k, v in tables.coverage.items()},
               "zo_rows": {"lhb": len(tables.lhb), "jg": len(tables.jg), "blk": len(tables.blk), "ins": len(tables.ins)}}
    per_stock, feats, la_records, bound_rows, warm_rows, adj_rows = [], {}, [], [], [], []
    la_event_days = []
    summary["zo_strict_coverage"] = True          # production setting; raises zo.MissingRawFile if a raw file is absent
    tp_all = {}
    rng = np.random.default_rng(20261115)
    # Event tables used by the look-ahead test: the records of the trial stocks only. The feature code filters
    # the tables by code, so the reference rows are unchanged; destroying 100,000-row tables record by record
    # for every check would only add run time.
    c6 = [c.split(".")[1] for c in codes]
    la_tables = zo.ZOTables(tables.lhb[tables.lhb["代码"].isin(c6)].reset_index(drop=True),
                            tables.jg[tables.jg["代码"].isin(c6)].reset_index(drop=True),
                            tables.blk[tables.blk["证券代码"].isin(c6)].reset_index(drop=True),
                            tables.ins[tables.ins["SECURITY_CODE"].isin(c6)].reset_index(drop=True), tables.coverage,
                            data_cutoff=tables.data_cutoff)
    for code in codes:
        raw = st.raw_bars(code)
        idx_code = panel.proxy_index_code(code)
        raw_idx = st.raw_index(idx_code)
        ipo = st.ipo_date(code)
        far = _far(cal, raw)
        t0 = time.time()
        f = build(code, raw, cal, far, raw_idx, tables, ipo)
        el = time.time() - t0
        feats[code] = f
        bars = prepare_bars(raw, cal)
        traded_prev = bars["traded"].loc[bars.index < cal.days[-1]].copy()    # v0.8: calendar ends at the cut-off
        traded_prev.index = cal.next_index(traded_prev.index)
        tp_all[code] = traded_prev.reindex(f.index).fillna(False).values
        per_stock.append({"code": code, "rows": len(f), "first_decision_day": f.index.min().date(),
                          "last_decision_day": f.index.max().date(), "build_seconds": round(el, 2),
                          "n_features": f.shape[1], "n_inf": int(np.isinf(f.values).sum()),
                          "proxy_index": idx_code, "proxy_index_on_disk": raw_idx is not None, **bars.attrs,
                          "n_not_traded_rows": int((~bars["traded"]).sum())})
        for r in bounds_check(f):
            bound_rows.append({"code": code, **r})
        # warm-up: rows of history before the first non-NaN value, against the catalogue
        first_valid = f.notna().values.argmax(axis=0)
        has = f.notna().any(axis=0).values
        for c, fv, h in zip(f.columns, first_valid, has):
            warm_rows.append({"code": code, "feature": c, "group": cat.loc[c, "group"],
                              "declared_warmup_rows": int(cat.loc[c, "warmup"]),
                              "first_valid_row": int(fv) + 1 if h else np.nan,
                              "first_valid_day": f.index[fv].date() if h else None})
        # own factor against the vendor factor table (descriptive)
        pf = os.path.join(st.root, "factors_events", "bs_adjust_factor", code + ".parquet")
        if os.path.exists(pf):
            vf = dc.read_parquet_cut(pf, "dividOperateDate", DATA_CUTOFF)    # descriptive comparison only
            vf["d"] = pd.to_datetime(vf["dividOperateDate"])
            vf = vf[vf["d"].isin(bars.index)].sort_values("d")
            back = pd.to_numeric(vf["backAdjustFactor"], errors="coerce").values
            own = bars["F"].reindex(vf["d"]).values
            step_own = bars["F"].values[1:] / bars["F"].values[:-1]
            own_steps = pd.Series(step_own, index=bars.index[1:])
            n_own_steps = int((np.abs(own_steps - 1) > 1e-9).sum())
            if len(vf) >= 2:
                rel = (own[1:] / own[:-1]) / (back[1:] / back[:-1]) - 1
                adj_rows.append({"code": code, "vendor_factor_rows": len(vf), "own_factor_steps": n_own_steps,
                                 "vendor_steps_compared": len(rel),
                                 "n_within_1e-3": int((np.abs(rel) < 1e-3).sum()),
                                 "max_abs_rel_diff": float(np.nanmax(np.abs(rel)))})
            else:
                adj_rows.append({"code": code, "vendor_factor_rows": len(vf), "own_factor_steps": n_own_steps,
                                 "vendor_steps_compared": 0, "n_within_1e-3": 0, "max_abs_rel_diff": np.nan})
        # look-ahead on real rows
        if not args.skip_lookahead:
            cand = f.index[(f.index >= EVAL_START) & (f.notna().sum(axis=1) > 150)]
            days = []
            if len(cand):
                days = list(cand[rng.choice(len(cand), size=min(args.lookahead_days, len(cand)), replace=False)])
            # for EACH class: one decision day on which an event of the stock has just become usable (if any)
            tb = tables.for_code(code)
            ev_cls = {"lhb": [], "blk": [], "ins": []}
            if len(tb.lhb):
                ev_cls["lhb"] = list(cal.pos_array(pd.to_datetime(tb.lhb["上榜日"])) + ZO_LAG["lhb"])
            if len(tb.blk):
                ev_cls["blk"] = list(cal.pos_array(pd.to_datetime(tb.blk["交易日期"])) + ZO_LAG["blk"])
            if len(tb.ins):
                xi, _ = zo.clean_ins(tb.ins)
                ev_cls["ins"] = list(cal.roll_forward_pos(xi["notice"]) + ZO_LAG["ins"]) if len(xi) else []
            for k in ("lhb", "blk", "ins"):
                ev = [cal.days[p] for p in ev_cls[k] if ZO_LAG[k] <= p < len(cal) and cal.days[p] in f.index
                      and cal.days[p] >= EVAL_START]
                if ev:
                    d_ev = ev[int(rng.integers(len(ev)))]
                    days.append(d_ev)
                    la_event_days.append({"code": code, "class": k, "decision_day": d_ev})
            days = sorted(set(days))
            t1 = time.time()
            recs = lookahead.check_lookahead(lambda c, rb, cl, co, ri, tb_: build(c, rb, cl, co, ri, tb_, ipo), code, raw,
                                             cal, days, raw_idx, la_tables, far_cutoff=far, reference=f,
                                             scopes=("availability",),
                                             seed=int(rng.integers(1 << 30)))
            la_records += recs
            print(f"[{code}] rows={len(f)} build={el:.1f}s lookahead {len(recs)} checks "
                  f"({sum(r['equal'] for r in recs)} equal) in {time.time() - t1:.0f}s", flush=True)
        else:
            print(f"[{code}] rows={len(f)} build={el:.1f}s", flush=True)

    # ---------------------------------------------------------------- tables
    pd.DataFrame(per_stock).to_csv(os.path.join(OUT, "dryrun_per_stock.csv"), index=False)
    pd.DataFrame(bound_rows).to_csv(os.path.join(OUT, "dryrun_bounds.csv"), index=False)
    warm = pd.DataFrame(warm_rows)
    warm.to_csv(os.path.join(OUT, "dryrun_warmup.csv"), index=False)
    pd.DataFrame(adj_rows).to_csv(os.path.join(OUT, "dryrun_adjust_vs_vendor.csv"), index=False)
    pooled = pd.concat([f.assign(code=c, _tp=tp_all[c]) for c, f in feats.items()])
    ev = pooled[pooled.index >= EVAL_START]
    evt = ev[ev["_tp"].astype(bool)]
    rows = []
    for c in cat.index:
        x_all, x = pooled[c], ev[c]
        xv = x.dropna()
        q = xv.quantile([0, 0.01, 0.5, 0.99, 1]).values if len(xv) else [np.nan] * 5
        rows.append({"feature": c, "group": cat.loc[c, "group"], "role": cat.loc[c, "role"],
                     "nan_share_all_rows": float(x_all.isna().mean()),
                     "nan_share_from_2010": float(x.isna().mean()) if len(x) else np.nan,
                     "nan_share_from_2010_prev_day_traded": float(evt[c].isna().mean()) if len(evt) else np.nan,
                     "n_from_2010": int(len(xv)), "min": q[0], "p01": q[1], "median": q[2], "p99": q[3], "max": q[4],
                     "share_zero": float((xv == 0).mean()) if len(xv) else np.nan,
                     "n_distinct": int(xv.nunique())})
    stats = pd.DataFrame(rows)
    stats.to_csv(os.path.join(OUT, "dryrun_feature_stats.csv"), index=False)
    la = pd.DataFrame(la_records)
    if len(la):
        la.to_csv(os.path.join(OUT, "lookahead_real.csv"), index=False)

    # ---------------------------------------------------------------- Z_O input diagnostics (descriptive)
    diag = {}
    lhb = tables.lhb
    mapped = lhb["代码"].map(zo.to_bs_code)
    diag["lhb_rows"] = int(len(lhb))
    diag["lhb_rows_outside_universe_codes"] = int(mapped.isna().sum())
    sd = zo.lhb_stock_day(lhb, tables.jg)
    diag["lhb_stock_days"] = int(len(sd))
    diag["lhb_stock_days_with_more_than_one_row"] = int((sd["n_rows"] > 1).sum())
    diag["lhb_stock_days_only_multi_day_reason"] = int((sd["multi"] & ~sd["has_single"]).sum())
    diag["lhb_rows_unclassified_reason"] = int(sd["n_unclassified"].sum())
    d = pd.to_datetime(lhb["上榜日"])
    diag["lhb_rows_on_non_trading_days"] = int((cal.pos_array(d) < 0).sum())
    five = lhb["上榜原因"].str.contains("前五只|前5只", regex=True)
    three = lhb["上榜原因"].str.contains("前三只|前3只", regex=True)
    exch = lhb["代码"].str[0].map({"6": "sse", "9": "sse", "0": "szse", "3": "szse", "2": "szse"})
    for e in ("sse", "szse"):
        m = exch == e
        diag[f"lhb_{e}_first_day_reason_says_top5"] = str(d[m & five].min().date()) if (m & five).any() else None
        diag[f"lhb_{e}_last_day_reason_says_top3"] = str(d[m & three].max().date()) if (m & three).any() else None
    blk = tables.blk
    diag["blk_rows"] = int(len(blk))
    diag["blk_rows_outside_universe_codes"] = int(blk["证券代码"].map(zo.to_bs_code).isna().sum())
    diag["blk_rows_on_non_trading_days"] = int((cal.pos_array(pd.to_datetime(blk["交易日期"])) < 0).sum())
    ins, ins_stats = zo.clean_ins(tables.ins)
    diag["ins"] = ins_stats
    diag["ins_rows_outside_universe_codes"] = int(tables.ins["SECURITY_CODE"].map(zo.to_bs_code).isna().sum())
    diag["ins_notice_on_non_trading_day_share"] = float((cal.pos_array(ins["notice"]) < 0).mean()) if len(ins) else None
    # block trades of the trial stocks: vendor premium vs own (trade price / bar close - 1); vendor ratio vs own
    chk = []
    for code in codes:
        tb = tables.for_code(code).blk
        if not len(tb):
            continue
        b = prepare_bars(st.raw_bars(code), cal)
        dd = pd.to_datetime(tb["交易日期"])
        close = b["close"].reindex(dd).values
        fmv = panel.float_market_value(b).reindex(dd).values
        chk.append(pd.DataFrame({"code": code, "date": dd.values,
                                 "prem_vendor": tb["折溢率"].values, "prem_own": tb["成交价"].values / close - 1,
                                 "ratio_vendor_pct": tb["成交额/流通市值"].values,
                                 "ratio_own_pct": tb["成交额"].values / fmv * 100}))
    # PLAN v0.8 C-4 (c): premium recomputed with the plausibility rule vs the vendor column (descriptive only)
    v8 = []
    for code in codes:
        tb = tables.for_code(code).blk
        if not len(tb):
            continue
        b8 = prepare_bars(st.raw_bars(code), cal)
        dd = pd.DatetimeIndex(pd.to_datetime(tb["交易日期"]))
        prem8, ok8 = zo.blk_plausibility(code, dd, pd.to_numeric(tb["成交价"], errors="coerce").to_numpy(float), b8)
        v8.append(pd.DataFrame({"code": code, "date": dd.values, "year": dd.year, "plausible": ok8, "prem_own_v08": prem8,
                                "prem_vendor": pd.to_numeric(tb["折溢率"], errors="coerce").to_numpy(float)}))
    if v8:
        x8 = pd.concat(v8)
        x8.to_csv(os.path.join(OUT, "v08_blk_premium_recomputed_vs_vendor.csv"), index=False)
        ok = x8[x8["plausible"]]
        dv = (ok["prem_own_v08"] - ok["prem_vendor"]).abs()
        diag["blk_v08_recomputed_vs_vendor"] = {
            "n_trades": int(len(x8)), "n_implausible": int((~x8["plausible"]).sum()),
            "implausible_by_year": {int(k): int(v) for k, v in (~x8["plausible"]).groupby(x8["year"]).sum().items()},
            "implausible_by_exchange": {e: int((~x8["plausible"] & x8["code"].str.startswith(e)).sum()) for e in ("sh.", "sz.")},
            "plausible_rows_vendor_missing": int(ok["prem_vendor"].isna().sum()),
            "plausible_abs_diff_lt_1e-4": int((dv < 1e-4).sum()), "plausible_abs_diff_median": float(dv.median()) if len(dv) else None,
            "plausible_abs_diff_p99": float(dv.quantile(0.99)) if len(dv) else None,
            "plausible_abs_diff_max": float(dv.max()) if len(dv) else None}
    if chk:
        ck = pd.concat(chk)
        ck.to_csv(os.path.join(OUT, "dryrun_blk_crosscheck.csv"), index=False)
        dp = (ck["prem_vendor"] - ck["prem_own"]).abs()
        rr = (ck["ratio_own_pct"] / ck["ratio_vendor_pct"])
        diag["blk_crosscheck"] = {"n_trades": int(len(ck)), "n_bar_close_missing": int(ck["prem_own"].isna().sum()),
                                  "premium_abs_diff_lt_1e-4": int((dp < 1e-4).sum()),
                                  "premium_abs_diff_max": float(dp.max()),
                                  "own_to_vendor_ratio_median": float(rr.median()),
                                  "own_to_vendor_ratio_p05": float(rr.quantile(0.05)),
                                  "own_to_vendor_ratio_p95": float(rr.quantile(0.95))}
    # chip variants and the CGO / cost-gap relation (feature against feature only)
    var = []
    for code in codes[:8]:
        b = prepare_bars(st.raw_bars(code), cal)
        a = zh.chip_stats(b, init="uniform_first_day")      # pre-declared sensitivity
        r = zh.chip_stats(b, init="renormalise")            # primary (PLAN v0.7 F-3)
        var.append((a - r).abs().assign(code=code))         # feature-against-feature difference only
    if var:
        v = pd.concat(var)
        diag["chip_init_uniform_minus_renormalise_abs_diff"] = {
            k: {"median": float(v[k].median()), "p99": float(v[k].quantile(0.99)), "max": float(v[k].max())}
            for k in ("pr", "cost_gap", "band90", "band70", "overhead")}
    both = ev[["zh_cgo_250", "zh_chip_cost_gap"]].dropna()
    diag["corr_cgo250_vs_chip_cost_gap_pooled"] = float(both.corr().iloc[0, 1]) if len(both) > 10 else None
    two = ev[["zh_cgo_250", "zh_cgo_250_nolag"]].dropna()
    diag["cgo250_primary_minus_nolag_abs_diff"] = {
        "median": float((two.iloc[:, 0] - two.iloc[:, 1]).abs().median()),
        "p99": float((two.iloc[:, 0] - two.iloc[:, 1]).abs().quantile(0.99))} if len(two) else None

    # ---------------------------------------------------------------- ADV against the engine (FEA-8; same definition)
    try:
        from engine import fills as efills, io_baostock as eio
        from engine.config import EngineConfig
        cfg = EngineConfig()
        market, _ = eio.load_market(Path(st.root), codes, events="none", apply_dispositions=False,
                                    data_cutoff=DATA_CUTOFF)
        pos_of = {pd.Timestamp(x): i for i, x in enumerate(market.days)}
        n_cmp = n_both_none = n_only_one = 0
        worst = 0.0
        for code in codes:
            if code not in market.secs:
                continue
            b = prepare_bars(st.raw_bars(code), cal)
            mine = panel.adv_on_data_dates(b)
            for s, v in mine.items():
                if s >= cal.days[-1]:                # no decision day after the cut-off (v0.8)
                    continue
                i = pos_of.get(cal.next(s))
                if i is None:
                    continue
                e = efills.adv(market, code, i, cfg)[0]
                if np.isnan(v) and e == 0.0:
                    n_both_none += 1
                elif np.isnan(v) or e == 0.0:
                    n_only_one += 1
                else:
                    n_cmp += 1
                    worst = max(worst, abs(v / e - 1.0))
        diag["adv_vs_engine"] = {"engine_flag_adv_counts_nontraded_days_as_zero": bool(cfg.adv_counts_nontraded_days_as_zero),
                                 "engine_adv_window": int(cfg.adv_window), "stock_days_compared": n_cmp,
                                 "stock_days_both_without_adv": n_both_none,
                                 "stock_days_only_one_has_adv": n_only_one, "max_abs_relative_diff": worst,
                                 "within_1e-9": bool(worst <= 1e-9 and n_only_one == 0)}
    except Exception as e:                                               # noqa: BLE001 - the engine is another task's code
        diag["adv_vs_engine"] = {"error": f"{type(e).__name__}: {e}"}

    # ---------------------------------------------------------------- panel assembly of the trial names (TODO-F1)
    if not args.skip_panel:
        with tempfile.TemporaryDirectory() as tmp:
            man = market_panel.build_market_panel(codes, tmp, progress_every=0, data_cutoff=DATA_CUTOFF)
            prep = market_panel.panel_report(tmp, OUT, prefix="panel_trial_")
            man.drop(columns=[c for c in ("traceback",) if c in man.columns]).to_csv(
                os.path.join(OUT, "panel_trial_manifest.csv"), index=False)
            # the stored files must equal the frames built above, bit for bit
            n_same = 0
            for code in codes:
                stored = pd.read_parquet(os.path.join(tmp, "features", code + ".parquet"))
                a, b_ = feats[code][stored.columns].values.astype(np.float64), stored.values
                n_same += int(a.shape == b_.shape and bool(((np.isnan(a) & np.isnan(b_)) | (a.view(np.uint64) == b_.view(np.uint64))).all()))
            prep["stored_files_bit_identical_to_direct_build"] = n_same
            prep["bytes_on_disk"] = int(sum(os.path.getsize(os.path.join(tmp, "features", f))
                                            for f in os.listdir(os.path.join(tmp, "features"))))
        summary["panel_trial"] = prep
    diag["n_V_gt_1_stock_days"] = int(sum(p["n_V_gt_1"] for p in per_stock))

    summary["lookahead"] = ({"n_checks": int(len(la)), "n_equal": int(la["equal"].sum()),
                             "n_stocks": int(la["code"].nunique()),
                             "n_stock_days": int(la.groupby(["code", "decision_day"]).ngroups),
                             "min_nonnan_cols_compared": int(la["n_nonnan"].min()),
                             "by_check": la.groupby("check")["equal"].agg(["size", "sum"]).rename(
                                 columns={"size": "n", "sum": "equal"}).to_dict("index"),
                             "failures": la.loc[~la["equal"], ["code", "decision_day", "check", "diff_cols"]]
                             .astype(str).to_dict("records")}
                            if len(la) else "skipped")
    b = pd.DataFrame(bound_rows)
    summary["lookahead_event_days"] = pd.DataFrame(la_event_days).astype(str).to_dict("records")
    summary["lookahead_event_days_by_class"] = (pd.DataFrame(la_event_days)["class"].value_counts().to_dict()
                                                if la_event_days else {})
    zo_cols = [c for c in cat.index if cat.loc[c, "group"] == "Z_O"]
    summary["zo_nonmissing_from_2010"] = {c: int(ev[c].notna().sum()) for c in zo_cols}
    summary["zo_share_nonzero_from_2010"] = {c: float((ev[c].dropna() != 0).mean()) for c in zo_cols}
    summary["bounds"] = {"n_feature_stock_checks": int(len(b)), "total_violations": int(b["violations"].sum()),
                         "violating": b[b["violations"] > 0].groupby("feature")["violations"].sum().to_dict()}
    summary["n_inf_total"] = int(sum(p["n_inf"] for p in per_stock))
    summary["build_seconds_total"] = float(sum(p["build_seconds"] for p in per_stock))
    summary["rows_total"] = int(sum(p["rows"] for p in per_stock))
    g = stats.groupby("group")
    summary["nan_share_from_2010_by_group"] = {k: {"median": float(x["nan_share_from_2010"].median()),
                                                   "max": float(x["nan_share_from_2010"].max())} for k, x in g}
    summary["nan_share_from_2010_prev_day_traded_by_group"] = {
        k: {"median": float(x["nan_share_from_2010_prev_day_traded"].median()),
            "max": float(x["nan_share_from_2010_prev_day_traded"].max())} for k, x in g}
    summary["rows_from_2010"] = int(len(ev))
    summary["rows_from_2010_prev_day_traded"] = int(len(evt))
    w = warm.dropna(subset=["first_valid_row"])
    w = w[w["group"].isin(["B0", "Z_H", "R_H-sum", "R_H-hist"]) & (w["feature"] != "zh_cgo_w260")]
    summary["warmup_first_valid_row_minus_declared"] = {
        "min": float((w["first_valid_row"] - w["declared_warmup_rows"]).min()),
        "n_earlier_than_declared": int((w["first_valid_row"] < w["declared_warmup_rows"]).sum())}
    summary["zo_input_diagnostics"] = diag
    with open(os.path.join(OUT, "dryrun_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: summary.get(k) for k in ("lookahead", "lookahead_event_days_by_class", "bounds", "n_inf_total",
                                                   "build_seconds_total", "rows_total", "nan_share_from_2010_by_group",
                                                   "nan_share_from_2010_prev_day_traded_by_group",
                                                   "warmup_first_valid_row_minus_declared", "panel_trial")},
                     ensure_ascii=False, indent=1, default=str))
    print(json.dumps({"adv_vs_engine": diag.get("adv_vs_engine")}, ensure_ascii=False, default=str))
    bad = (len(la) and not bool(la["equal"].all())) or summary["bounds"]["total_violations"] or summary["n_inf_total"]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

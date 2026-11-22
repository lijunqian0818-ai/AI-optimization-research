"""Full-market feature panel: loop over names, storage, report
(task list TODO-F1; freeze item FC-A16).

    build_market_panel(codes, out_dir, ...)   one parquet file per name + manifest.csv
    panel_report(out_dir, report_dir)         missing rates by year, warm-up, value ranges,
                                              names affected by missing / repaired rows

Storage format
    <out_dir>/features/<code>.parquet   index `decision_day`; float64 columns in
                                        catalogue order (369 model features + the
                                        diagnostic column); no compression of values
                                        other than parquet's own (lossless)
    <out_dir>/manifest.csv              one row per name: status, rows, columns, first /
                                        last decision day, seconds, counts from the bar
                                        frame (missing rows, repaired rows, V > 1), Z_O
                                        counts, sha256 of the file
    <out_dir>/panel_meta.json           cut-off, groups, strict flag, catalogue hash,
                                        hash of the reason table, config constants
A cross-section for one decision day is read by loading the files of the
names wanted; a by-date consolidation is left to the strategy layer.

Rules
  * Row t of every file depends on G_t only (panel.build_stock_features with
    an explicit cut-off; the look-ahead test covers that function).
  * Read-only on the raw data; no request is sent; nothing is imputed.
  * Z_O coverage is strict by default (ruling F-14): a raw file missing from
    the snapshot inside the analysis period stops the run before any name is
    built.
  * Nothing here computes a label, a forward return or any relation between
    a feature and a return. The report contains only: computable or not,
    missing rates, value ranges, warm-up rows, counts.

Command line (project root; read-only on experiments/data/raw):
  experiments/.venv/Scripts/python.exe -X utf8 experiments/src/features/market_panel.py \
      --codes-file <file> --out <dir> [--jobs N] [--report-dir <dir>] [--non-strict] [--cutoff YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

if __package__ in (None, ""):                      # run as a script
    sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
    __package__ = "features"

from . import config, panel, registry, zo            # noqa: E402
from .store import RawStore                          # noqa: E402

EVAL_START = pd.Timestamp("2010-01-01")
_W: dict = {}                                        # per-process state of the workers


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def catalogue_hash() -> str:
    cat = registry.catalogue()
    return hashlib.sha256(cat.to_csv(index=False).encode("utf-8")).hexdigest()


def _init(root: str, cutoff, groups, zo_strict, out_dir: str, data_cutoff, zo_codes=None):
    st = RawStore(root, data_cutoff=data_cutoff)
    cal = st.calendar()
    tables = st.zo_tables() if "Z_O" in groups else None
    if tables is not None and zo_codes is not None:
        tables = tables.restrict(zo_codes)          # Z_O filtered to the list in use (PLAN 13A)
    _W.update(store=st, cal=cal, tables=tables, basic=st.stock_basic(),
              cutoff=cutoff, groups=tuple(groups), zo_strict=zo_strict, out_dir=out_dir, index_cache={},
              data_cutoff=st.data_cutoff)


def _build_one(code: str) -> dict:
    st, cal = _W["store"], _W["cal"]
    rec = {"code": code, "status": "ok", "error": ""}
    t0 = time.time()
    try:
        raw = st.raw_bars(code)
        if not len(raw):
            raise ValueError("empty bar file")
        idx_code = panel.proxy_index_code(code)
        if idx_code not in _W["index_cache"]:
            _W["index_cache"][idx_code] = st.raw_index(idx_code)
        raw_idx = _W["index_cache"][idx_code]
        b = _W["basic"]
        r = b.loc[b["code"] == code, "ipoDate"]
        ipo = pd.Timestamp(r.iloc[0]) if len(r) and r.iloc[0] else None
        cutoff = _W["cutoff"]
        last = pd.to_datetime(raw["date"]).max()
        try:
            far = cal.next(last)
        except KeyError:                              # the calendar ends at the data cut-off (C-8)
            far = cal.days[-1]
        t = far if cutoff is None else min(pd.Timestamp(cutoff), far)
        f = panel.build_stock_features(code, raw, cal, t, raw_idx, _W["tables"], ipo_date=ipo, groups=_W["groups"],
                                       zo_strict=_W["zo_strict"])
        order = [c for c in registry.catalogue()["name"] if c in f.columns]
        if set(order) != set(f.columns):
            raise ValueError("columns outside the catalogue: " + str(sorted(set(f.columns) - set(order))[:5]))
        attrs = dict(f.attrs)
        f = f[order].astype(np.float64)
        path = os.path.join(_W["out_dir"], "features", code + ".parquet")
        tmp = path + ".tmp"
        f.to_parquet(tmp)
        os.replace(tmp, path)
        lhb = attrs.get("zo_lhb_stats", {})
        ins = attrs.get("zo_ins_stats", {})
        blk = attrs.get("zo_blk_stats", {})
        rec.update(rows=len(f), n_cols=f.shape[1], first_decision_day=str(f.index.min().date()),
                   last_decision_day=str(f.index.max().date()), cutoff=str(t.date()),
                   n_inf=int(np.isinf(f.values).sum()), proxy_index=idx_code, proxy_index_on_disk=raw_idx is not None,
                   ipo_date=str(ipo.date()) if ipo is not None else "",
                   **{k: attrs.get(k, 0) for k in ("n_duplicate_dates", "n_rows_off_calendar", "n_missing_rows",
                                                   "n_filled_xsrc_rows", "n_V_gt_1", "n_V_lt_0", "n_traded_V_nan")},
                   lhb_unclassified_rows=lhb.get("n_unclassified_rows", 0),
                   lhb_stock_days_multi_only=lhb.get("n_stock_days_multi_only", 0),
                   ins_rows=ins.get("rows", 0), ins_rows_kept=ins.get("kept", 0),
                   blk_trades=blk.get("trades", 0), blk_implausible=blk.get("implausible", 0),
                   blk_by_year=json.dumps(blk.get("by_year", {})), data_cutoff=str(_W["data_cutoff"]),
                   sha256=_sha256(path))
    except zo.MissingRawFile:
        raise                                         # a snapshot defect: stop, do not record and continue
    except Exception as e:                            # noqa: BLE001 - recorded per name, reported, never hidden
        rec.update(status="error", error=f"{type(e).__name__}: {e}", traceback=traceback.format_exc()[-1500:])
    rec["build_seconds"] = round(time.time() - t0, 2)
    return rec


def build_market_panel(codes, out_dir: str, cutoff=None, root: str | None = None, n_jobs: int = 1,
                       zo_strict: bool | None = None, groups=panel.GROUPS, overwrite: bool = False,
                       progress_every: int = 50, *, data_cutoff, zo_codes=None) -> pd.DataFrame:
    """Build and store the feature frame of every name in `codes`.

    `cutoff` (a decision day; default: for each name the trading day after
    its last bar, or the last calendar day). `data_cutoff` (REQUIRED, PLAN
    v0.8 C-8): no raw row dated after it is read; it is written to
    panel_meta.json and to every manifest row. Names whose file is already in
    the manifest with status ok are skipped unless `overwrite` (resume).
    Returns the manifest."""
    st = RawStore(data_cutoff=data_cutoff) if root is None else RawStore(root, data_cutoff=data_cutoff)
    root = st.root
    os.makedirs(os.path.join(out_dir, "features"), exist_ok=True)
    strict = config.ZO_STRICT_COVERAGE if zo_strict is None else zo_strict
    if "Z_O" in groups:
        # fail before building anything if the snapshot lacks a file of the analysis period (F-14)
        covered = st.check_zo_coverage(strict=strict)
    else:
        covered = {}
    meta = {"created": time.strftime("%Y-%m-%d %H:%M:%S"), "cutoff": None if cutoff is None else str(pd.Timestamp(cutoff).date()),
            "data_cutoff": str(st.data_cutoff),
            "groups": list(groups), "zo_strict": bool(strict), "zo_covered_trading_days": covered,
            "catalogue_sha256": catalogue_hash(),
            "lhb_reason_map_sha256": _sha256(zo.REASON_MAP_FILE),
            "n_columns": int(len(registry.catalogue())), "zo_lag": dict(config.ZO_LAG),
            "chip_init": config.CHIP_INIT_PRIMARY, "cgo_skip": config.CGO_SKIP,
            "ins_intensity_enabled": bool(config.INS_INTENSITY_ENABLED), "raw_root": root}
    with open(os.path.join(out_dir, "panel_meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)
    man_path = os.path.join(out_dir, "manifest.csv")
    done = {}
    if os.path.exists(man_path) and not overwrite:
        old = pd.read_csv(man_path, dtype={"code": str})
        for r in old.to_dict("records"):
            if r.get("status") == "ok" and os.path.exists(os.path.join(out_dir, "features", r["code"] + ".parquet")):
                done[r["code"]] = r
    have = set(st.bar_codes())
    todo = [c for c in codes if c not in done and c in have]
    recs = list(done.values()) + [{"code": c, "status": "no_bar_file", "error": ""} for c in codes if c not in have]
    args = (root, cutoff, tuple(groups), strict, out_dir, st.data_cutoff, None if zo_codes is None else tuple(zo_codes))
    t0 = time.time()

    def note(k):
        if progress_every and k % progress_every == 0:
            print(f"[panel] {k}/{len(todo)} names built, {time.time() - t0:.0f}s", flush=True)

    if n_jobs <= 1:
        _init(*args)
        for k, c in enumerate(todo, 1):
            recs.append(_build_one(c))
            note(k)
    else:
        with ProcessPoolExecutor(max_workers=n_jobs, initializer=_init, initargs=args) as ex:
            for k, r in enumerate(ex.map(_build_one, todo, chunksize=4), 1):
                recs.append(r)
                note(k)
    man = pd.DataFrame(recs)
    order = {c: i for i, c in enumerate(codes)}
    man = man.sort_values("code", key=lambda s: s.map(lambda c: order.get(c, 1 << 30))).reset_index(drop=True)
    man.to_csv(man_path, index=False)
    return man


def panel_report(out_dir: str, report_dir: str | None = None, prefix: str = "panel_") -> dict:
    """Missing-rate, warm-up and range report of a stored panel. Reads one
    name at a time. Only counts, missing rates, ranges and warm-up rows are
    computed -- nothing relates a feature to a return."""
    report_dir = out_dir if report_dir is None else report_dir
    os.makedirs(report_dir, exist_ok=True)
    man = pd.read_csv(os.path.join(out_dir, "manifest.csv"), dtype={"code": str})
    cat = registry.catalogue().set_index("name")
    ok = man[man["status"] == "ok"]
    by_year: dict = {}
    warm_rows = []
    rng = {c: [np.inf, -np.inf, 0, 0, 0] for c in cat.index}       # min, max, n, n_nan, n_inf
    n_rows = 0
    for code in ok["code"]:
        f = pd.read_parquet(os.path.join(out_dir, "features", code + ".parquet"))
        n_rows += len(f)
        cols = [c for c in cat.index if c in f.columns]
        v = f[cols].values
        isn = np.isnan(v)
        years = f.index.year.values
        for y in np.unique(years):
            m = years == y
            acc = by_year.setdefault(int(y), {"n": 0, "nan": np.zeros(len(cat), dtype=np.int64)})
            acc["n"] += int(m.sum())
            acc["nan"][[cat.index.get_loc(c) for c in cols]] += isn[m].sum(axis=0)
        fin = np.where(np.isfinite(v), v, np.nan)
        with np.errstate(all="ignore"):
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mn, mx = np.nanmin(fin, axis=0), np.nanmax(fin, axis=0)
        first_valid = (~isn).argmax(axis=0)
        has = (~isn).any(axis=0)
        for j, c in enumerate(cols):
            r = rng[c]
            if has[j]:
                r[0], r[1] = min(r[0], mn[j]), max(r[1], mx[j])
            r[2] += len(f)
            r[3] += int(isn[:, j].sum())
            r[4] += int(np.isinf(v[:, j]).sum())
            warm_rows.append((code, c, int(first_valid[j]) + 1 if has[j] else np.nan))
    # ---- missing rates by year
    recs = []
    for y in sorted(by_year):
        acc = by_year[y]
        for j, c in enumerate(cat.index):
            recs.append({"year": y, "feature": c, "group": cat.at[c, "group"], "role": cat.at[c, "role"],
                         "n_rows": acc["n"], "n_nan": int(acc["nan"][j]),
                         "nan_share": acc["nan"][j] / acc["n"] if acc["n"] else np.nan})
    miss = pd.DataFrame(recs)
    miss.to_csv(os.path.join(report_dir, prefix + "missing_by_year_feature.csv"), index=False)
    if len(miss):
        g = miss.groupby(["year", "group", "role"])["nan_share"].agg(["median", "max", "size"]).reset_index()
        g = g.rename(columns={"median": "nan_share_median_over_features", "max": "nan_share_max_over_features",
                              "size": "n_features"})
        g = g.merge(miss.groupby("year")["n_rows"].first().rename("n_rows").reset_index(), on="year")
    else:
        g = pd.DataFrame()
    g.to_csv(os.path.join(report_dir, prefix + "missing_by_year_group.csv"), index=False)
    # ---- ranges
    r = pd.DataFrame([{"feature": c, "group": cat.at[c, "group"], "role": cat.at[c, "role"],
                       "min": v[0] if np.isfinite(v[0]) else np.nan, "max": v[1] if np.isfinite(v[1]) else np.nan,
                       "n_rows": v[2], "n_nan": v[3], "n_inf": v[4]} for c, v in rng.items()])
    r.to_csv(os.path.join(report_dir, prefix + "feature_ranges.csv"), index=False)
    # ---- warm-up
    w = pd.DataFrame(warm_rows, columns=["code", "feature", "first_valid_row"])
    if len(w):
        w["declared"] = w["feature"].map(cat["warmup"])
        w["excess"] = w["first_valid_row"] - w["declared"]
        ws = w.groupby("feature").agg(n_names=("code", "size"), n_never_valid=("first_valid_row", lambda s: int(s.isna().sum())),
                                      excess_min=("excess", "min"), excess_median=("excess", "median"),
                                      excess_max=("excess", "max"),
                                      n_earlier_than_declared=("excess", lambda s: int((s < 0).sum()))).reset_index()
        ws.insert(1, "group", ws["feature"].map(cat["group"]))
        ws.insert(2, "declared_warmup_rows", ws["feature"].map(cat["warmup"]))
    else:
        ws = pd.DataFrame()
    ws.to_csv(os.path.join(report_dir, prefix + "warmup_by_feature.csv"), index=False)
    num = lambda c: pd.to_numeric(ok[c], errors="coerce").fillna(0) if c in ok.columns else pd.Series(0, index=ok.index)  # noqa: E731
    summary = {
        "n_names_requested": int(len(man)), "n_names_ok": int(len(ok)),
        "n_names_error": int((man["status"] == "error").sum()),
        "n_names_no_bar_file": int((man["status"] == "no_bar_file").sum()),
        "errors": man.loc[man["status"] == "error", ["code", "error"]].to_dict("records")[:50],
        "rows_total": int(n_rows), "n_columns": int(len(cat)),
        "n_inf_total": int(r["n_inf"].sum()) if len(r) else 0,
        "n_features_never_computed": int((r["n_nan"] == r["n_rows"]).sum()) if len(r) else 0,
        "features_never_computed": r.loc[r["n_nan"] == r["n_rows"], "feature"].tolist()[:50] if len(r) else [],
        "names_with_missing_rows": int((num("n_missing_rows") > 0).sum()),
        "missing_rows_total": int(num("n_missing_rows").sum()),
        "names_with_rows_filled_from_xsrc": int((num("n_filled_xsrc_rows") > 0).sum()),
        "rows_filled_from_xsrc_total": int(num("n_filled_xsrc_rows").sum()),
        "stock_days_V_gt_1": int(num("n_V_gt_1").sum()),
        "lhb_unclassified_rows": int(num("lhb_unclassified_rows").sum()),
        "lhb_stock_days_multi_only": int(num("lhb_stock_days_multi_only").sum()),
        "build_seconds_total": float(num("build_seconds").sum()),
        "warmup_n_feature_name_pairs_earlier_than_declared":
            int((w["excess"] < 0).sum()) if len(w) else 0,
    }
    with open(os.path.join(report_dir, prefix + "report_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1, default=str)
    return summary


def _read_codes(path: str) -> list[str]:
    out = []
    for line in open(path, encoding="utf-8"):
        s = line.split("#")[0].strip()
        if not s:
            continue
        c = s.split(".")[-1]
        bs = zo.to_bs_code(c)
        if bs:
            out.append(bs)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--codes-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report-dir", default=None)
    ap.add_argument("--report-prefix", default="panel_")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--cutoff", default=None)
    ap.add_argument("--data-cutoff", required=True, help="no raw row after this date is read (PLAN v0.8 C-8)")
    ap.add_argument("--non-strict", action="store_true", help="tests only: tolerate missing Z_O files (NaN)")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    man = build_market_panel(_read_codes(a.codes_file), a.out, cutoff=a.cutoff, n_jobs=a.jobs,
                             zo_strict=False if a.non_strict else None, overwrite=a.overwrite,
                             data_cutoff=a.data_cutoff)
    s = panel_report(a.out, a.report_dir, a.report_prefix)
    print(json.dumps({k: s[k] for k in ("n_names_ok", "n_names_error", "rows_total", "n_columns", "n_inf_total",
                                        "n_features_never_computed", "names_with_missing_rows",
                                        "build_seconds_total")}, ensure_ascii=False))
    return 0 if (man["status"] != "error").all() else 1


if __name__ == "__main__":
    sys.exit(main())

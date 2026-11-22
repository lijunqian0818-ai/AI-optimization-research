"""OA10 / SD-O signed date audit -- step 1: draw the sample (OFFLINE).

PLAN v0.7 section 2.4 "Signed date audits", SD-O; rulings F-9, G-4; U47, U57.
This script ONLY builds the list of table rows to be checked against the
official originals. It opens no original, sends no request, and computes
nothing about returns. It reads the raw Z_O files (whitelisted columns only)
and the trading calendar, read-only.

Scheme (as in the plan)
  * one audit per class: LHB (table lhb_detail), BLK (table dzjy_mrmx, one
    row per trade), INS (table ins_raw, rows that pass the feature library's
    cleaning rule -- the rows the pipeline can use);
  * sampling unit = a row of the table (G-4);
  * frame = rows of in-universe codes (SSE / SZSE A-shares; if a file of
    ever-members of the universe is given, restricted to it) whose table date
    lies between the class's analysis start and 2026-06-30;
  * strata = calendar year of the table date (INS: year x direction);
    allocation proportional to the number of rows, at least 5 rows per
    stratum, n = 300 per class;
  * INS additionally: inside each (year, direction) stratum the allocation is
    split proportionally between rows entered by the vendor more than 30 days
    after the announcement date and the rest (see NOTE below);
  * 30 of the 300 rows of LHB and of BLK are marked for the hand re-check,
    drawn at random from the 300 (U57);
  * the seed and the list are written to disk before any original is opened;
    no row is replaced after the draw.
  * d_tab = the date the pipeline uses: LHB / BLK the listing / trade day;
    INS the announcement date ROLLED FORWARD to the next market trading day
    (F-9). `first_usable_decision_day` = d_tab + lag trading days, lag from
    config.ZO_LAG -- the same number the features use.

NOTE (a point the plan leaves open; reported to the lead). The plan asks for
at least 5 rows per stratum and, for INS, for strata by year, by direction
AND by back-fill status. With 19 years x 2 directions x 2 back-fill classes
= 76 strata the minimum alone would be 380 > 300. Here the minimum of 5
applies to year x direction (38 strata) and the back-fill split inside a
stratum is proportional without a minimum.

Usage (project root; writes only under experiments/results/feature_tests/):
  experiments/.venv/Scripts/python.exe -X utf8 experiments/src/features/audit/oa10_sample.py \
      [--members-file FILE] [--out experiments/results/feature_tests/oa10_sample.csv]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", ".."))
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from features import config, zo                       # noqa: E402
from features.store import RawStore, read_whitelisted  # noqa: E402

N_PER_CLASS = 300          # PLAN U47 (PLACEHOLDER confirmed at Gate 2)
MIN_PER_STRATUM = 5        # PLAN 2.4
N_HAND_RECHECK = 30        # PLAN U57 (LHB and BLK)
BACKFILL_DAYS = 30         # PLAN 2.4, additional stratum for INS
SEED = 20261115            # fixed here, written to the meta file; never changed after a draw
AUDIT_END = config.ZO_RAW_END
CLASSES = ("lhb", "blk", "ins")
TABLE = {"lhb": ("lhb_detail", "lhb_detail", "代码", "上榜日"),
         "blk": ("dzjy_mrmx", "dzjy_mrmx", "证券代码", "交易日期"),
         "ins": ("ins_raw", "ins_raw", "SECURITY_CODE", "NOTICE_DATE")}
ROOT = os.path.normpath(os.path.join(SRC, "..", ".."))
DEFAULT_OUT = os.path.join(ROOT, "experiments", "results", "feature_tests", "oa10_sample.csv")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_class_table(store: RawStore, cls: str) -> tuple[pd.DataFrame, dict]:
    """All rows of the class table (whitelisted columns) with their identity
    in the raw files: `source_file` (relative to the raw root) and
    `row_in_file` (0-based). Returns the table and a fingerprint of the files."""
    sub, table, _, _ = TABLE[cls]
    files = sorted(f for f in glob.glob(os.path.join(store.root, "zo", sub, "*.parquet"))
                   if os.path.basename(f)[:-8].isdigit())
    frames, digest = [], hashlib.sha256()
    for f in files:
        df = read_whitelisted(f, table)
        rel = "zo/" + sub + "/" + os.path.basename(f)
        df.insert(0, "row_in_file", np.arange(len(df)))
        df.insert(0, "source_file", rel)
        digest.update((rel + ":" + _sha256_file(f) + "\n").encode())
        if len(df):
            frames.append(df)
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return out, {"n_files": len(files), "files_sha256": digest.hexdigest()}


def build_frame(cls: str, tab: pd.DataFrame, cal, members: set | None = None) -> tuple[pd.DataFrame, dict]:
    """Sampling frame of one class with d_tab and the strata."""
    _, _, code_col, date_col = TABLE[cls]
    counts = {"rows_in_table": int(len(tab))}
    x = tab.copy()
    if cls == "ins":
        x, st = zo.clean_ins(x)                       # the rows the pipeline can use (F-9)
        counts["ins_cleaning"] = st
        x = x.drop(columns=["end"])
        x["table_date"] = x.pop("notice")
    else:
        x["table_date"] = pd.to_datetime(x[date_col], errors="coerce")
        counts["rows_without_date"] = int(x["table_date"].isna().sum())
        x = x[x["table_date"].notna()]
    x["code6"] = x[code_col].astype(str)
    x["bs_code"] = x["code6"].map(zo.to_bs_code)
    counts["rows_outside_universe_codes"] = int(x["bs_code"].isna().sum())
    x = x[x["bs_code"].notna()]
    if members is not None:
        counts["rows_not_ever_members"] = int((~x["bs_code"].isin(members)).sum())
        x = x[x["bs_code"].isin(members)]
    start = config.ZO_CLASS_START[cls]
    inside = (x["table_date"] >= start) & (x["table_date"] <= AUDIT_END)
    counts["rows_outside_audit_period"] = int((~inside).sum())
    x = x[inside].copy()
    pos = cal.roll_forward_pos(x["table_date"])       # LHB / BLK: the day itself if it is a trading day
    on_cal = cal.pos_array(x["table_date"]) >= 0
    counts["rows_dated_on_non_trading_day"] = int((~on_cal).sum())
    lag = config.ZO_LAG[cls]
    ok = pos + lag < len(cal)
    counts["rows_whose_usable_day_is_beyond_the_calendar"] = int((~ok).sum())
    x, pos, on_cal = x[ok].copy(), pos[ok], on_cal[ok]
    x["d_tab"] = cal.days[pos].values
    x["d_tab_rolled"] = (~on_cal).astype(int)
    x["lag"] = lag
    x["first_usable_decision_day"] = cal.days[pos + lag].values
    x["exchange"] = np.where(x["bs_code"].str.startswith("sh."), "SSE", "SZSE")
    x["year"] = x["table_date"].dt.year.astype(int)
    if cls == "ins":
        ei = pd.to_datetime(x["EITIME"], errors="coerce")
        x["backfilled"] = ((ei - x["table_date"]).dt.days > BACKFILL_DAYS).astype(int)
        x["direction"] = x["DIRECTION"].map({"增持": "buy", "减持": "sell"})
        x["stratum"] = x["year"].astype(str) + "/" + x["direction"]
        x["substratum"] = x["stratum"] + "/" + np.where(x["backfilled"] == 1, "backfilled", "not_backfilled")
    else:
        x["stratum"] = x["year"].astype(str)
        x["substratum"] = x["stratum"]
    counts["frame_rows"] = int(len(x))
    return x.sort_values(["source_file", "row_in_file"], kind="mergesort").reset_index(drop=True), counts


def allocate(sizes: dict, n: int, minimum: int) -> dict:
    """Allocation of n rows proportional to the stratum sizes, with at least
    `minimum` rows per stratum (the whole stratum if it is smaller) and never
    more than a stratum holds. Strata whose proportional share falls below
    the minimum are set to the minimum and the rest is re-allocated
    proportionally among the others; fractions are settled by largest
    remainders (ties by stratum name). Deterministic."""
    keys = sorted(sizes)
    n = min(n, sum(sizes.values()))
    floor_of = {k: min(minimum, sizes[k]) for k in keys}
    if sum(floor_of.values()) > n:
        raise ValueError(f"the minimum of {minimum} per stratum needs {sum(floor_of.values())} > n = {n} rows")
    fixed: dict = {}
    free = list(keys)
    quota: dict = {}
    while True:
        rest = n - sum(fixed.values())
        tot = sum(sizes[k] for k in free)
        quota = {k: rest * sizes[k] / tot for k in free} if tot else {}
        low = [k for k in free if quota[k] < floor_of[k]]
        high = [k for k in free if quota[k] > sizes[k]]
        if not low and not high:
            break
        for k in low:
            fixed[k] = floor_of[k]
        for k in high:
            if k not in fixed:
                fixed[k] = sizes[k]
        free = [k for k in free if k not in fixed]
    alloc = dict(fixed)
    base = {k: int(np.floor(quota[k] + 1e-9)) for k in free}
    left = n - sum(fixed.values()) - sum(base.values())
    order = sorted(free, key=lambda k: (-(quota[k] - base[k]), k))
    i = 0
    while left > 0 and order:
        k = order[i % len(order)]
        if base[k] < sizes[k]:
            base[k] += 1
            left -= 1
        i += 1
        if i > 10 * len(order) + n:
            raise RuntimeError("allocation did not converge")
    alloc.update(base)
    return {k: alloc[k] for k in keys}


def draw(frame: pd.DataFrame, cls: str, seed: int = SEED, n: int = N_PER_CLASS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Stratified random sample without replacement. Returns (sample, table
    of strata with frame sizes and allocations)."""
    rng = np.random.default_rng([seed, CLASSES.index(cls)])
    sizes = frame.groupby("stratum").size().to_dict()
    alloc = allocate(sizes, min(n, len(frame)), MIN_PER_STRATUM)
    picks, rows = [], []
    for s in sorted(sizes):
        g = frame.index[frame["stratum"] == s].values
        sub_sizes = frame.loc[g, "substratum"].value_counts().to_dict()
        sub_alloc = allocate(sub_sizes, alloc[s], 0)
        for ss in sorted(sub_sizes):
            gi = frame.index[(frame["stratum"] == s) & (frame["substratum"] == ss)].values
            k = sub_alloc[ss]
            chosen = np.sort(rng.choice(gi, size=k, replace=False)) if k else np.zeros(0, dtype=np.int64)
            picks.append(chosen)
            rows.append({"class": cls, "stratum": s, "substratum": ss, "frame_rows": int(len(gi)), "sampled": int(k)})
    idx = np.concatenate(picks) if picks else np.zeros(0, dtype=np.int64)
    sample = frame.loc[np.sort(idx)].copy()
    sample.insert(0, "sample_id", [f"{cls.upper()}-{i + 1:03d}" for i in range(len(sample))])
    sample["hand_recheck"] = 0
    if cls in ("lhb", "blk") and len(sample):
        h = rng.choice(len(sample), size=min(N_HAND_RECHECK, len(sample)), replace=False)
        sample.iloc[h, sample.columns.get_loc("hand_recheck")] = 1
    return sample, pd.DataFrame(rows)


ID_COLS = {"lhb": ["上榜原因", "龙虎榜净买额", "龙虎榜成交额"],
           "blk": ["成交价", "成交量", "成交额"],
           "ins": ["DIRECTION", "CHANGE_NUM", "END_DATE", "backfilled"]}
OUT_COLS = ["sample_id", "class", "stratum", "substratum", "exchange", "code6", "bs_code", "table_date", "d_tab",
            "d_tab_rolled", "lag", "first_usable_decision_day", "hand_recheck", "source_file", "row_in_file",
            "row_key_1", "row_key_2", "row_key_3", "row_key_4"]


def to_output(sample: pd.DataFrame, cls: str) -> pd.DataFrame:
    out = pd.DataFrame({"sample_id": sample["sample_id"].values, "class": cls.upper()})
    for c in ("stratum", "substratum", "exchange", "code6", "bs_code"):
        out[c] = sample[c].values
    out["table_date"] = pd.to_datetime(sample["table_date"]).dt.strftime("%Y-%m-%d").values
    out["d_tab"] = pd.to_datetime(sample["d_tab"]).dt.strftime("%Y-%m-%d").values
    out["d_tab_rolled"] = sample["d_tab_rolled"].values
    out["lag"] = sample["lag"].values
    out["first_usable_decision_day"] = pd.to_datetime(sample["first_usable_decision_day"]).dt.strftime("%Y-%m-%d").values
    out["hand_recheck"] = sample["hand_recheck"].values
    out["source_file"] = sample["source_file"].values
    out["row_in_file"] = sample["row_in_file"].values
    for j in range(4):
        col = ID_COLS[cls][j] if j < len(ID_COLS[cls]) else None
        out[f"row_key_{j + 1}"] = "" if col is None else [f"{col}={v}" for v in sample[col].values]
    return out[OUT_COLS]


def read_members(path: str | None) -> set | None:
    if not path:
        return None
    out = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            s = line.split("#")[0].strip()
            if s:
                c = zo.to_bs_code(s.split(".")[-1])
                if c:
                    out.add(c)
    return out


def run(out_path: str = DEFAULT_OUT, members_file: str | None = None, root: str | None = None,
        seed: int = SEED, n: int = N_PER_CLASS) -> dict:
    # explicit cut-off (PLAN v0.8 C-8): the audit frame of OA10 is the whole raw window; not run in the pilot round
    store = RawStore(data_cutoff=AUDIT_END) if root is None else RawStore(root, data_cutoff=AUDIT_END)
    cal = store.calendar()
    members = read_members(members_file)
    parts, strata, meta_cls = [], [], {}
    for cls in CLASSES:
        tab, fp = load_class_table(store, cls)
        frame, counts = build_frame(cls, tab, cal, members)
        sample, st = draw(frame, cls, seed, n)
        parts.append(to_output(sample, cls))
        strata.append(st)
        meta_cls[cls] = {"table": TABLE[cls][0], **fp, **counts, "n_strata": int(st["stratum"].nunique()),
                         "sampled": int(len(sample)), "hand_recheck": int(sample["hand_recheck"].sum()),
                         "lag": int(config.ZO_LAG[cls]), "analysis_start": str(config.ZO_CLASS_START[cls].date()),
                         "sampled_by_exchange": sample["exchange"].value_counts().to_dict(),
                         "sampled_d_tab_rolled": int(sample["d_tab_rolled"].sum())}
        if cls == "ins":
            meta_cls[cls]["sampled_backfilled"] = int(sample["backfilled"].sum())
            meta_cls[cls]["frame_backfilled_share"] = float(frame["backfilled"].mean()) if len(frame) else None
    out = pd.concat(parts, ignore_index=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out.to_csv(out_path, index=False, encoding="utf-8-sig")
    base = os.path.splitext(out_path)[0]
    pd.concat(strata, ignore_index=True).to_csv(base + "_strata.csv", index=False)
    meta = {
        "drawn_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": ("PROVISIONAL DRAW. The plan's frame is the FROZEN first snapshot (FC-A1) restricted to ever-members "
                   "of the universe; neither exists yet. This list was drawn from the raw files on disk"
                   + (" restricted to the members file given" if members is not None else
                      " for all SSE / SZSE A-share codes")
                   + ". It must be re-drawn with this script and this seed once the snapshot is frozen and the "
                     "ever-member list exists, and before any original document is opened. No original has been "
                     "opened and no request has been sent."),
        "seed": seed, "rng": "numpy.random.default_rng([seed, class index]); class index: lhb 0, blk 1, ins 2",
        "n_per_class": n, "min_per_stratum": MIN_PER_STRATUM, "n_hand_recheck": N_HAND_RECHECK,
        "backfill_threshold_days": BACKFILL_DAYS, "audit_end": str(AUDIT_END.date()),
        "members_file": members_file, "n_members": None if members is None else len(members),
        "sampling_unit": "row of the table (PLAN v0.7 G-4)",
        "d_tab": "LHB / BLK: listing / trade day; INS: announcement date rolled forward to a trading day (F-9)",
        "strata": "LHB, BLK: calendar year; INS: year x direction, split inside proportionally by back-fill status",
        "classes": meta_cls,
        "sample_file": os.path.basename(out_path), "sample_sha256": _sha256_file(out_path),
        "strata_file": os.path.basename(base + "_strata.csv"),
        "numpy": np.__version__, "pandas": pd.__version__,
    }
    with open(base + "_meta.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1, default=str)
    return meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--members-file", default=None, help="ever-members of the universe, one code per line")
    a = ap.parse_args()
    meta = run(a.out, a.members_file)
    print(json.dumps({c: {k: v[k] for k in ("frame_rows", "n_strata", "sampled", "hand_recheck")}
                      for c, v in meta["classes"].items()}, ensure_ascii=False))
    print("sample sha256", meta["sample_sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

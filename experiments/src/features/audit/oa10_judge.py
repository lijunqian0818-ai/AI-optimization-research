"""OA10 / SD-O signed date audit -- step 3: verdict (OFFLINE).

Input: the pre-drawn sample (`oa10_sample.csv`, never edited) and a results
file filled in by the audit, one row per sampled row:

    sample_id, status, d_orig[, note]

    status   found          the record was located in the official original
             not_found      LHB / BLK only: the official disclosure of the day the
                            table assigns was archived and the record is not in it
             unverifiable   no original could be retrieved
    d_orig   publication date of the original (YYYY-MM-DD). LHB / BLK: the
             trading day of the official disclosure that contains the record.
             INS: the date of the announcement on the statutory platform.

Definitions (PLAN v0.7 section 2.4), in trading days. d_tab is the date the
pipeline uses (INS: rolled forward, F-9; taken from the sample file). A
document without a time stamp is treated as published after the close of
d_orig, so it is public for the decision of the first trading day AFTER
d_orig at the earliest; the pipeline uses the record from d_tab + lag.

    early         d_tab < d_orig                 (reported)
    leak          d_tab + lag < d_orig + 1       (the criterion)
    late          d_tab > d_orig                 (reported)
    LHB / BLK not_found  ->  leak (conservative)
    unverifiable  counted separately, never a match

Criterion SD-O: (i) exact one-sided 95% Clopper-Pearson upper limit of the
leak share among verified rows <= 2%; (ii) unverifiable rows <= 10% of the
sample overall and <= 25% in every calendar year.

This script retrieves nothing and sends no request. Retrieval of originals
needs approval and is not part of it.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", ".."))
if SRC not in sys.path:
    sys.path.insert(0, SRC)

P_MAX = 0.02                 # PLAN U47
CONF = 0.95
UNVERIFIABLE_MAX_OVERALL = 0.10
UNVERIFIABLE_MAX_YEAR = 0.25
STATUSES = ("found", "not_found", "unverifiable")


def clopper_pearson_upper(k: int, n: int, conf: float = CONF) -> float:
    """Exact one-sided upper confidence limit for a binomial proportion."""
    if n <= 0:
        return float("nan")
    if k >= n:
        return 1.0
    return float(stats.beta.ppf(conf, k + 1, n - k))


def classify(sample: pd.DataFrame, results: pd.DataFrame, cal) -> pd.DataFrame:
    """One row per sampled row with the signed quantities and the verdict."""
    if results["sample_id"].duplicated().any():
        raise ValueError("duplicate sample_id in the results file")
    unknown = set(results["sample_id"]) - set(sample["sample_id"])
    if unknown:
        raise ValueError(f"results for rows that are not in the pre-drawn sample: {sorted(unknown)[:5]}")
    bad = set(results["status"].dropna()) - set(STATUSES)
    if bad:
        raise ValueError(f"unknown status values: {sorted(bad)}")
    x = sample.merge(results[["sample_id", "status", "d_orig"]], on="sample_id", how="left")
    x["status"] = x["status"].fillna("pending")
    d_tab = pd.to_datetime(x["d_tab"])
    d_orig = pd.to_datetime(x["d_orig"], errors="coerce")
    p_tab = cal.pos_array(d_tab)
    if (p_tab < 0).any():
        raise ValueError("d_tab of the sample is not a trading day")
    found = (x["status"] == "found").values
    if (found & d_orig.isna().values).any():
        raise ValueError("status 'found' without d_orig")
    cls = x["class"].str.lower().values
    if ((x["status"] == "not_found").values & (cls == "ins")).any():
        raise ValueError("'not_found' is defined for LHB / BLK only; an INS row without an original is 'unverifiable'")
    fill = d_orig.fillna(pd.Timestamp("1970-01-01"))
    p_orig_roll = cal.roll_forward_pos(fill)                         # first trading day >= d_orig
    v = pd.DatetimeIndex(fill).values
    p_public = np.searchsorted(cal.days.values, v, side="right")     # first trading day strictly after d_orig
    usable = p_tab + x["lag"].values.astype(int)
    x["d_tab_minus_d_orig_trading_days"] = np.where(found, p_tab - p_orig_roll, np.nan)
    x["early"] = np.where(found, p_tab < p_orig_roll, False)
    x["late"] = np.where(found, p_tab > p_orig_roll, False)
    leak = np.where(found, usable < p_public, False)
    leak = leak | (x["status"] == "not_found").values                 # conservative rule for LHB / BLK
    x["leak"] = leak
    x["verified"] = found | (x["status"] == "not_found").values
    x["year"] = pd.to_datetime(x["table_date"]).dt.year
    return x


def summarise(x: pd.DataFrame) -> dict:
    out = {}
    for cls, g in x.groupby("class"):
        n = len(g)
        pending = int((g["status"] == "pending").sum())
        ver = g[g["verified"]]
        k = int(ver["leak"].sum())
        ucl = clopper_pearson_upper(k, len(ver))
        unv = int((g["status"] == "unverifiable").sum())
        by_year = g.groupby("year").apply(lambda d: pd.Series({
            "sampled": len(d), "verified": int(d["verified"].sum()), "leak": int(d["leak"].sum()),
            "early": int(d["early"].sum()), "late": int(d["late"].sum()),
            "unverifiable": int((d["status"] == "unverifiable").sum())}), include_groups=False)
        unv_year_max = float((by_year["unverifiable"] / by_year["sampled"]).max()) if len(by_year) else float("nan")
        crit_i = bool(len(ver) > 0 and ucl <= P_MAX)
        crit_ii = bool(unv / n <= UNVERIFIABLE_MAX_OVERALL and unv_year_max <= UNVERIFIABLE_MAX_YEAR) if n else False
        out[cls] = {
            "sampled": n, "pending": pending, "verified": int(len(ver)), "unverifiable": unv,
            "leak": k, "early": int(ver["early"].sum()), "late": int(ver["late"].sum()),
            "not_found_counted_as_leak": int((g["status"] == "not_found").sum()),
            "leak_share_among_verified": k / len(ver) if len(ver) else None,
            "leak_upper_limit_one_sided_95": ucl,
            "unverifiable_share": unv / n if n else None, "unverifiable_share_max_year": unv_year_max,
            "criterion_i_leak": crit_i, "criterion_ii_unverifiable": crit_ii,
            "complete": pending == 0,
            "pass": bool(crit_i and crit_ii and pending == 0),
            "d_tab_minus_d_orig_distribution": ver.loc[ver["status"] == "found", "d_tab_minus_d_orig_trading_days"]
            .value_counts().sort_index().to_dict(),
            "by_year": by_year.reset_index().to_dict("records"),
        }
    return out


def main() -> int:
    from features.store import RawStore
    from features import config
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sample = pd.read_csv(a.sample, dtype={"code6": str})
    results = pd.read_csv(a.results)
    x = classify(sample, results, RawStore(data_cutoff=config.ZO_RAW_END).calendar())   # explicit cut-off (C-8)
    s = summarise(x)
    x.to_csv(os.path.splitext(a.out)[0] + "_rows.csv", index=False, encoding="utf-8-sig")
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(s, fh, ensure_ascii=False, indent=1, default=str)
    print(json.dumps({c: {k: v[k] for k in ("sampled", "verified", "leak", "leak_upper_limit_one_sided_95", "pass")}
                      for c, v in s.items()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

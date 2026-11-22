"""Build `lhb_reason_map.csv`: Dragon-Tiger listing-reason string ->
{single, multi, unclassified} (PLAN v0.7 section 5.6.3, ruling F-6).

The table is built FROM THE STRINGS ALONE. The only column read from the raw
files is the reason string (`上榜原因`) of `lhb_detail` and `lhb_jgmmtj`; no
amount, date, code or count enters the table, and no relation of anything to
returns is computed. The classification is mechanical:

  multi         the string names a multi-day criterion: it contains one of
                连续 / 累计 / [2二两3三]个交易日 / 异常期间 /
                最近<N>个有成交的交易日   (its seat amounts are cumulative
                over the days of the criterion);
  single        not multi, and the string carries a one-day marker:
                it starts with 日, or contains 当日 / 的日 / 首日 / 盘中;
  unclassified  neither (e.g. 无价格涨跌幅限制的证券, 退市整理期): the string
                does not say over which days the amounts are taken. Such rows
                count for the listing indicator only.

Read-only on experiments/data/raw; sends no request. Usage (project root):

  experiments/.venv/Scripts/python.exe -X utf8 experiments/src/features/build_lhb_reason_map.py

The output is frozen and hashed with the first snapshot (FC-A1); at run time a
string that is not in the table is 'unclassified' and counted.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import os
import re
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.normpath(os.path.join(HERE, "..", "..", "data", "raw", "zo"))
OUT = os.path.join(HERE, "lhb_reason_map.csv")

MULTI = re.compile(r"连续|累计|[2二两3三]个交易日|异常期间|最近\d+个有成交的交易日")
SINGLE = re.compile(r"^日|当日|的日|首日|盘中")


def classify(reason: str) -> tuple[str, str]:
    """(class, rule that fired) from the string alone."""
    m = MULTI.search(reason)
    if m:
        return "multi", "multi-day marker '" + m.group(0) + "'"
    m = SINGLE.search(reason)
    if m:
        return "single", "one-day marker '" + m.group(0) + "'"
    return "unclassified", "no marker"


def distinct_reasons(raw: str = RAW) -> list[str]:
    seen = set()
    for sub in ("lhb_detail", "lhb_jgmmtj"):
        for f in sorted(glob.glob(os.path.join(raw, sub, "*.parquet"))):
            if not os.path.basename(f)[:-8].isdigit():
                continue
            s = pd.read_parquet(f, columns=["上榜原因"])["上榜原因"].dropna()
            seen.update(str(x) for x in s.unique())
    return sorted(seen)


def main() -> int:
    reasons = distinct_reasons()
    rows = [(r, *classify(r)) for r in reasons]
    with open(OUT, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["reason", "class", "rule"])
        w.writerows(rows)
    n = {c: sum(1 for _, k, _ in rows if k == c) for c in ("single", "multi", "unclassified")}
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    print(f"{len(rows)} distinct reason strings -> {n}; written to {OUT}; sha256 {sha}")
    for r, k, _ in rows:
        if k == "unclassified":
            print("  unclassified:", r)
    return 0


if __name__ == "__main__":
    sys.exit(main())

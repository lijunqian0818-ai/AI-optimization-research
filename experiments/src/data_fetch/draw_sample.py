"""Draw the study population: a seeded, stratified random sample of the A-share work list.

Decided by the user on 2026-11-15 (option B): the study population is a random sample of
1,000 names instead of the whole market. The rule is fixed here BEFORE any model, backtest
or outcome exists. Names already downloaded get no preference.

Strata: board x listing-year bucket x delisted flag. Proportional allocation by largest
remainder; simple random sampling without replacement inside each stratum.
Outputs: experiments/data/universe_sample_v1.csv (with stratum and draw metadata) and
experiments/data/universe_sample_v1_codes.txt (one code per line, for --codes-file).
"""
import hashlib
import os
import sys

import numpy as np
import pandas as pd

SEED = 20261115
N = 1000
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC = os.path.join(ROOT, "experiments", "data", "raw", "universe", "a_share_worklist.csv")
OUT = os.path.join(ROOT, "experiments", "data", "universe_sample_v1.csv")
OUT_CODES = os.path.join(ROOT, "experiments", "data", "universe_sample_v1_codes.txt")


def board(code: str) -> str:
    num = code.split(".")[-1]
    if num.startswith("688") or num.startswith("689"):
        return "STAR"
    if num.startswith("30"):
        return "ChiNext"
    if num.startswith("6"):
        return "SH_main"
    return "SZ_main"


def year_bucket(y: int) -> str:
    for hi, name in ((2007, "<=2007"), (2012, "2008-2012"), (2017, "2013-2017"), (2021, "2018-2021")):
        if y <= hi:
            return name
    return "2022-2026"


def main() -> None:
    if os.path.exists(OUT):
        sys.exit(f"{OUT} already exists: the sample is drawn once and never redrawn.")
    df = pd.read_csv(SRC, dtype=str)
    code_col = [c for c in df.columns if c.lower() in ("code", "bs_code")][0]
    ipo_col = [c for c in df.columns if "ipo" in c.lower() or "list" in c.lower()][0]
    out_col = [c for c in df.columns if "out" in c.lower() or "delist" in c.lower()][0]
    df = df.sort_values(code_col).reset_index(drop=True)
    df["board"] = df[code_col].map(board)
    df["ipo_bucket"] = pd.to_datetime(df[ipo_col]).dt.year.map(year_bucket)
    df["delisted"] = df[out_col].fillna("").astype(str).str.strip().ne("")
    df["stratum"] = df["board"] + "|" + df["ipo_bucket"] + "|" + df["delisted"].map({True: "delisted", False: "listed"})
    sizes = df.groupby("stratum").size()
    quota = sizes * N / len(df)
    alloc = np.floor(quota).astype(int)
    rem = (quota - alloc).sort_values(ascending=False)
    for s in rem.index[: N - int(alloc.sum())]:
        alloc[s] += 1
    rng = np.random.default_rng(SEED)
    picked = []
    for s in sorted(sizes.index):
        idx = df.index[df["stratum"] == s].to_numpy()
        picked.extend(rng.choice(idx, size=int(alloc[s]), replace=False).tolist())
    sample = df.loc[sorted(picked)].copy()
    sample["seed"] = SEED
    sample.to_csv(OUT, index=False, encoding="utf-8")
    with open(OUT_CODES, "w", encoding="utf-8") as f:
        f.write("\n".join(sample[code_col]) + "\n")
    digest = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    print(f"work list {len(df)} names, {len(sizes)} strata; drew {len(sample)}; seed {SEED}")
    print("by board:", sample["board"].value_counts().to_dict())
    print("delisted in sample:", int(sample["delisted"].sum()), "of", int(df["delisted"].sum()), "in the work list")
    print("sha256", digest)


if __name__ == "__main__":
    main()

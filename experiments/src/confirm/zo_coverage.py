"""Prevalence of usable Z_O events among the NOMINATED orders (exploratory diagnostic, 2026-11-17).

Reads nominations.parquet of a `--dump-decisions` run and the feature panel; reports, for the
evaluation years, the share of nominated orders whose Z_O indicator is 1 (per class and look-back),
the share with any event, and the mean number of such nominations per day.  No outcome is read.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

CLASSES = ("lhb", "blk", "ins_buy", "ins_sell")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--panel", required=True)
    ap.add_argument("--eval-years", default="2017,2018,2019,2020,2021")
    a = ap.parse_args(argv)
    years = [int(x) for x in a.eval_years.split(",")]
    nom = pd.read_parquet(Path(a.dump) / "nominations.parquet")
    nom["date"] = pd.to_datetime(nom["date"])
    nom = nom[nom["date"].dt.year.isin(years)]
    cols = [f"zo_{c}_ind_{w}" for c in CLASSES for w in (1, 5, 20)] + [f"zo_{c}_has_prior" for c in CLASSES]
    parts = []
    for code, g in nom.groupby("code"):
        f = Path(a.panel) / "features" / f"{code}.parquet"
        p = pd.read_parquet(f, columns=cols)
        p.index = pd.to_datetime(p.index)
        parts.append(g.join(p, on="date"))
    j = pd.concat(parts, ignore_index=True)
    out = {"note": "share of nominated orders (evaluation years); no outcome read", "n_rows": int(len(j))}
    for b, gb in j.groupby("base"):
        ob = out.setdefault(b, {})
        for c in cols:
            ob[c] = {"share_one": float((gb[c] == 1).mean()), "share_nan": float(gb[c].isna().mean())}
        for w in (1, 5, 20):
            anyc = (gb[[f"zo_{c}_ind_{w}" for c in CLASSES]] == 1).any(axis=1)
            ob[f"any_class_ind_{w}"] = {"share_one": float(anyc.mean()),
                                        "mean_nominations_per_day": float(anyc.groupby([gb["seed"], gb["i"]]).sum().mean())}
        anyc = (gb[[f"zo_{c}_ind_20" for c in CLASSES]] == 1).any(axis=1)
        ob["any_class_ind_20_by_year"] = {str(int(y)): float(v) for y, v in anyc.groupby(gb["date"].dt.year).mean().items()}
    (Path(a.dump) / "zo_coverage_nominations.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1)[:6000])
    return 0


if __name__ == "__main__":
    sys.exit(main())

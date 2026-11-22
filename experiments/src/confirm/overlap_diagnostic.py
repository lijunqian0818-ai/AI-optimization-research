"""Overlap / swap diagnostic for the contrasts of amendment v0.9.3 A4.1 (plan_review_5, GPT bullet).

Reads a decision dump of `run_confirm.py --dump-decisions` (submissions.parquet, decision_days.parquet,
dump_meta.json) and writes overlap_diagnostic.json (+ a markdown table) next to it.  For every base and
every primary (and secondary) contrast delta(g, h) = V^g - V^h on the evaluation window:

  * daily overlap of the submitted sets |Sub^g_t intersect Sub^h_t| (and as a share of S^g_t);
  * the names ADDED (in g, not in h) and REMOVED (in h, not in g): counts and mean realised rho;
  * the identity, exact whenever the seed-averaged total counts are equal,
        delta(g, h) = [ sum rho over g\\h  -  sum rho over h\\g ] / sum S,
    verified numerically (|residual| <= 1e-10 required; the run fails loudly otherwise).  Day by day,
    N^g_t - N^h_t = A_t - R_t holds for any counts and is checked as well.

Seed averaging as in A2.3 / A8 (c): daily numerators and counts are averaged over seeds before the ratio.
A day on which a policy has a decision but submits nothing contributes zero to its numerator and count.
Nothing here reads data after the dump's cut-off; nothing is a confirmatory statistic.

    experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/overlap_diagnostic.py --dump DIR [--years 2021]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BP = 1e4
TOL = 1e-10


def contrast_parts(sub: pd.DataFrame, ddays: pd.DataFrame, g: str, h: str, days: np.ndarray, seeds: list) -> dict:
    """sub: rows (seed, method, i, code, rho) of ONE base; ddays: (seed, method, i) decision days.
    Returns the per-(seed, day) table and the seed-averaged totals."""
    keep = ["seed", "i", "code", "rho"]
    a = sub[(sub["method"] == g) & sub["i"].isin(days)][keep]
    b = sub[(sub["method"] == h) & sub["i"].isin(days)][keep]
    m = a.merge(b, on=["seed", "i", "code"], how="outer", suffixes=("_g", "_h"), indicator=True)
    # rho is a property of (i, code): take it from whichever side has it
    m["rho"] = m["rho_g"].where(m["rho_g"].notna(), m["rho_h"])
    m["in_g"] = m["_merge"].isin(["both", "left_only"])
    m["in_h"] = m["_merge"].isin(["both", "right_only"])
    m = m.sort_values(["seed", "i", "code"], kind="mergesort")
    m["rg"] = np.where(m["in_g"], m["rho"], 0.0)
    m["rh"] = np.where(m["in_h"], m["rho"], 0.0)
    m["ra"] = np.where(m["in_g"] & ~m["in_h"], m["rho"], 0.0)
    m["rr"] = np.where(m["in_h"] & ~m["in_g"], m["rho"], 0.0)
    m["both"] = (m["in_g"] & m["in_h"]).astype(int)
    m["add"] = (m["in_g"] & ~m["in_h"]).astype(int)
    m["rem"] = (m["in_h"] & ~m["in_g"]).astype(int)
    m["sg"] = m["in_g"].astype(int)
    m["sh"] = m["in_h"].astype(int)
    per = m.groupby(["seed", "i"]).agg(Ng=("rg", "sum"), Nh=("rh", "sum"), A=("ra", "sum"), R=("rr", "sum"),
                                         Sg=("sg", "sum"), Sh=("sh", "sum"), overlap=("both", "sum"),
                                         n_add=("add", "sum"), n_rem=("rem", "sum"))
    # every decision day of either policy in the window, also those with zero submissions
    dd = ddays[ddays["method"].isin([g, h]) & ddays["i"].isin(days)][["seed", "i"]].drop_duplicates()
    full = pd.MultiIndex.from_frame(dd.sort_values(["seed", "i"]))
    per = per.reindex(per.index.union(full)).fillna(0.0)
    per = per[per.index.get_level_values("seed").isin(seeds)]
    ns = len(seeds)
    tot = {k: float(per[k].sum()) / ns for k in ("Ng", "Nh", "A", "R", "Sg", "Sh", "overlap", "n_add", "n_rem")}
    return {"per": per, "tot": tot}


def summarise(parts: dict, year_of: dict) -> dict:
    per, t = parts["per"], parts["tot"]
    out = {"days_seed_pairs": int(len(per))}
    if t["Sg"] <= 0 or t["Sh"] <= 0:
        out["flag"] = "zero submissions on one side: V set to 0 by convention (A2.2)"
    Vg = t["Ng"] / t["Sg"] if t["Sg"] > 0 else 0.0
    Vh = t["Nh"] / t["Sh"] if t["Sh"] > 0 else 0.0
    delta = Vg - Vh
    out.update({"V_g_bp": Vg * BP, "V_h_bp": Vh * BP, "delta_bp": delta * BP,
                "S_g_seedavg": t["Sg"], "S_h_seedavg": t["Sh"],
                "days_with_unequal_counts": int(((per["Sg"] - per["Sh"]).abs() > 0).sum()),
                "mean_daily_overlap_names": float(per["overlap"].mean()) if len(per) else None,
                "mean_daily_overlap_share_of_Sg": float((per["overlap"] / per["Sg"].where(per["Sg"] > 0)).mean())
                if len(per) else None,
                "n_added_seedavg": t["n_add"], "n_removed_seedavg": t["n_rem"],
                "mean_rho_added_bp": t["A"] / t["n_add"] * BP if t["n_add"] > 0 else None,
                "mean_rho_removed_bp": t["R"] / t["n_rem"] * BP if t["n_rem"] > 0 else None,
                "daily_identity_max_abs_residual": float(((per["Ng"] - per["Nh"]) - (per["A"] - per["R"])).abs().max())
                if len(per) else 0.0})
    if abs(t["Sg"] - t["Sh"]) <= 1e-9 * max(1.0, t["Sg"]):
        ident = (t["A"] - t["R"]) / t["Sg"] if t["Sg"] > 0 else 0.0
        out["identity_delta_bp"] = ident * BP
        out["identity_residual"] = abs(delta - ident)
        out["identity_applies"] = True
    else:
        out["identity_applies"] = False
        out["identity_note"] = "total counts differ: delta is a difference of two ratios, the swap identity does not apply"
    # by calendar year
    yr = np.array([year_of.get(int(i)) for i in per.index.get_level_values("i")])
    by = {}
    for y in sorted({v for v in yr if v is not None}):
        p = per[yr == y]
        sg, sh = p["Sg"].sum(), p["Sh"].sum()
        by[str(y)] = {"delta_bp": ((p["Ng"].sum() / sg if sg else 0.0) - (p["Nh"].sum() / sh if sh else 0.0)) * BP,
                      "mean_daily_overlap_share_of_Sg": float((p["overlap"] / p["Sg"].where(p["Sg"] > 0)).mean()),
                      "mean_rho_added_bp": float(p["A"].sum() / p["n_add"].sum() * BP) if p["n_add"].sum() else None,
                      "mean_rho_removed_bp": float(p["R"].sum() / p["n_rem"].sum() * BP) if p["n_rem"].sum() else None}
    out["by_year"] = by
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--years", default="", help="evaluation years (default: those of dump_meta.json)")
    a = ap.parse_args(argv)
    d = Path(a.dump)
    meta = json.loads((d / "dump_meta.json").read_text(encoding="utf-8"))
    years = [int(x) for x in a.years.split(",")] if a.years else meta["eval_years"]
    yfl = {int(k): v for k, v in meta["year_first_last_i"].items()}
    last = int(meta["last_decision_i"])
    days = np.array([i for y in years for i in range(yfl[y][0], min(yfl[y][1], last) + 1)])
    year_of = {int(i): y for y in yfl for i in range(yfl[y][0], yfl[y][1] + 1)}
    sub = pd.read_parquet(d / "submissions.parquet")
    ddays = pd.read_parquet(d / "decision_days.parquet")
    seeds = list(meta["seeds"])
    contrasts = [tuple(x) for x in meta["primary_contrasts"]] + [tuple(x) for x in meta["secondary_contrasts"]]
    out = {"note": "diagnostic on development data; not a confirmatory statistic", "dump": str(d), "years": years,
           "tolerance": TOL}
    worst, lines = 0.0, ["| base | contrast | delta bp | identity bp | residual | overlap share | mean rho added bp | "
                         "mean rho removed bp | unequal-count days |", "|---|---|---|---|---|---|---|---|---|"]
    for b in meta["bases"]:
        sb = sub[sub["base"] == b]
        db = ddays[ddays["base"] == b]
        ob = out.setdefault(b, {})
        have = set(sb["method"]) | set(db["method"])
        for cid, g, h in contrasts:
            if g not in have or h not in have:
                ob[f"{cid}: {g} - {h}"] = {"skipped": "policy not in the dump"}
                continue
            sm = summarise(contrast_parts(sb, db, g, h, days, seeds), year_of)
            ob[f"{cid}: {g} - {h}"] = sm
            r = sm.get("identity_residual")
            worst = max(worst, r if r is not None else 0.0, sm["daily_identity_max_abs_residual"])
            f = lambda x: "n/a" if x is None else f"{x:.3f}"            # noqa: E731
            lines.append(f"| {b} | {cid} {g} - {h} | {sm['delta_bp']:.3f} | {f(sm.get('identity_delta_bp'))} | "
                         f"{'n/a' if r is None else f'{r:.1e}'} | {f(sm['mean_daily_overlap_share_of_Sg'])} | "
                         f"{f(sm['mean_rho_added_bp'])} | {f(sm['mean_rho_removed_bp'])} | {sm['days_with_unequal_counts']} |")
    out["max_identity_residual"] = worst
    out["identity_check_passed"] = bool(worst <= TOL)
    (d / "overlap_diagnostic.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    (d / "overlap_diagnostic.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written {d / 'overlap_diagnostic.json'}; max identity residual {worst:.2e} "
          f"({'pass' if worst <= TOL else 'FAIL'} at {TOL})")
    return 0 if worst <= TOL else 1


if __name__ == "__main__":
    sys.exit(main())

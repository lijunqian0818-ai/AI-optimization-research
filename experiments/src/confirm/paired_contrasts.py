"""Post-hoc diagnostics on the daily decisions dumped by `run_pilot.py --dump-decisions` (exploratory).

Added 2026-11-17 after discussion round 2 with GPT (thread `pilot-direction`).  Reads
nominations.parquet / submissions.parquet / base_ic.parquet / standard_orders.parquet of a dump
directory and writes paired_contrasts.json next to them.  Nothing here is confirmatory; the hold-out
is not read (the dump is produced under the same data cut-off as the pilot).

  A  reproduces theta_sel of every within-batch gate and compares with a reference results.json
  B  paired per-order contrasts on the evaluation days (same resampled dates for both arms):
       V_g - V_SCORE                mean rho of the submitted orders of g minus that of SCORE
       theta_sel(g) - theta_sel(h)  stratified statistic, e.g. real Z minus permuted Z
       theta_uns(g)                 count-matched UNSTRATIFIED random abstention (secondary)
  C  variance audit of theta_sel: by-year contributions, HAC vs bootstrap SE, block-length sensitivity
  D  base RankIC by year on the candidate sets; mean rho of nominations vs all candidates by year
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from confirm import estimands as E                         # noqa: E402

BP = 1e4


def hac_se_ratio(u: np.ndarray, s: np.ndarray, lags: int) -> float:
    """Newey-West SE of sum(u)/sum(s) through the influence series u - theta * s."""
    th = u.sum() / s.sum()
    x = u - th * s
    x = x - x.mean()
    n = len(x)
    lrv = (x @ x) / n
    for L in range(1, lags + 1):
        w = 1.0 - L / (lags + 1.0)
        lrv += 2.0 * w * (x[L:] @ x[:-L]) / n
    return float(np.sqrt(max(lrv, 0.0) * n) / s.sum())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--reference", default="", help="results.json of the full run with the same gate rule")
    ap.add_argument("--eval-years", default="2017,2018,2019,2020,2021")
    ap.add_argument("--B", type=int, default=2000)
    a = ap.parse_args(argv)
    d = Path(a.dump)
    years = [int(x) for x in a.eval_years.split(",")]
    nom = pd.read_parquet(d / "nominations.parquet")
    sub = pd.read_parquet(d / "submissions.parquet")
    ic = pd.read_parquet(d / "base_ic.parquet")
    so = pd.read_parquet(d / "standard_orders.parquet")
    nom["year"] = pd.to_datetime(nom["date"]).dt.year
    ev = nom[nom["year"].isin(years)]
    lo, hi = int(ev["i"].min()), int(ev["i"].max())
    eval_days = np.arange(lo, hi + 1)
    n = len(eval_days)
    year_of = pd.to_datetime(ic.drop_duplicates("i").set_index("i")["date"]).dt.year
    yr = np.array([year_of.get(int(i), np.nan) for i in eval_days])
    idx = E.stationary_indices(n, a.B, 24, seed=20261115)
    out = {"note": "exploratory post-hoc diagnostics; not confirmatory", "dump": str(d), "n_eval_days": int(n),
           "eval_first_i": lo, "eval_last_i": hi}
    seeds = sorted(nom["seed"].unique())
    ref = json.load(open(a.reference, encoding="utf-8"))["estimates"] if a.reference else None

    for b in sorted(nom["base"].unique()):
        ob = out.setdefault(b, {})
        nb = ev[ev["base"] == b].copy()
        nb["cell_mean"] = nb.groupby(["seed", "i", "cell"])["rho"].transform("mean")
        nb["day_mean"] = nb.groupby(["seed", "i"])["rho"].transform("mean")
        sb = sub[(sub["base"] == b) & (sub["i"] >= lo) & (sub["i"] <= hi)]
        methods = [m for m in sorted(sb["method"].unique()) if not m.startswith("NET-U")]
        ser = {}
        for m in methods:
            mm = sb[sb["method"] == m][["seed", "i", "code"]].assign(sel=1)
            j = nb.merge(mm, on=["seed", "i", "code"], how="left")
            j = j[j["sel"] == 1]
            g = j.groupby("i").agg(v=("rho", "sum"), s=("rho", "size"), cm=("cell_mean", "sum"), dm=("day_mean", "sum"))
            g = g.reindex(eval_days).fillna(0.0) / len(seeds)
            ser[m] = {"V": g["v"].to_numpy(), "S": g["s"].to_numpy(), "U": (g["v"] - g["cm"]).to_numpy(),
                      "Uuns": (g["v"] - g["dm"]).to_numpy()}
        # A: reproduction
        rep = {}
        for m, x in ser.items():
            th = E.ratio_boot(x["U"], x["S"], idx)
            ent = {"theta_sel": th}
            if ref is not None and m in ref[b]["theta_sel"]:
                r0 = ref[b]["theta_sel"][m]["theta_sel_seedavg"]["estimate"]
                ent["reference_estimate"] = r0
                ent["abs_diff_vs_reference_bp"] = abs(th["estimate"] - r0) * BP
            ent["theta_unstratified"] = E.ratio_boot(x["Uuns"], x["S"], idx)
            ent["mean_rho_submitted"] = E.ratio_boot(x["V"], x["S"], idx)
            # C: variance audit
            byy = {}
            for y in years:
                k = yr == y
                byy[str(y)] = {"theta_sel": float(x["U"][k].sum() / x["S"][k].sum()) if x["S"][k].sum() else None,
                               "share_of_numerator": float(x["U"][k].sum() / x["U"].sum()) if x["U"].sum() else None,
                               "orders": float(x["S"][k].sum())}
            ent["by_year"] = byy
            ent["se_hac"] = {str(L): hac_se_ratio(x["U"], x["S"], L) for L in (0, 5, 12, 24, 48)}
            infl = x["U"] - th["estimate"] * x["S"]
            top = np.argsort(-np.abs(infl))[:10]
            ent["top10_days_share_of_abs_influence"] = float(np.abs(infl[top]).sum() / np.abs(infl).sum())
            ent["influence_lag1_autocorr"] = float(np.corrcoef(infl[1:], infl[:-1])[0, 1])
            rep[m] = ent
        ob["per_method"] = rep
        # block-length sensitivity for a few gates
        sens = {}
        for mb in (6, 12, 24, 48):
            ix = E.stationary_indices(n, a.B, mb, seed=20261115 + mb)
            for m in ("SCORE", "LOSS(-Z)", "LOSS(+Z_H)", "NET-K(-Z)"):
                if m in ser:
                    sens.setdefault(m, {})[str(mb)] = E.ratio_boot(ser[m]["U"], ser[m]["S"], ix)["se"]
        ob["bootstrap_se_by_mean_block"] = sens
        # B: paired contrasts
        pc = {}

        def dV(g, h):
            return E.diff_ratio_boot(ser[g]["V"], ser[g]["S"], ser[h]["V"], ser[h]["S"], idx)

        def dT(g, h, key="U"):
            return E.diff_ratio_boot(ser[g][key], ser[g]["S"], ser[h][key], ser[h]["S"], idx)

        for g in methods:
            if g in ("SCORE", "G0") or "SCORE" not in ser:
                continue
            pc[f"V[{g}] - V[SCORE]"] = dV(g, "SCORE")
            pc[f"theta_sel[{g}] - theta_sel[SCORE]"] = dT(g, "SCORE")
        for g, h in (("LOSS(+Z_H)", "LOSS(+perm Z_H)"), ("LOSS(+Z_O)", "LOSS(+perm Z_O)"),
                     ("LOSS(+Z_H)", "LOSS(-Z)"), ("LOSS(+Z_O)", "LOSS(-Z)"), ("LOSS(+Z_H+Z_O)", "LOSS(-Z)"),
                     ("NET-K(+Z_H)", "NET-K(-Z)"), ("NET-K(+Z_O)", "NET-K(-Z)")):
            if g in ser and h in ser:
                pc[f"theta_sel[{g}] - theta_sel[{h}]"] = dT(g, h)
                pc[f"V[{g}] - V[{h}]"] = dV(g, h)
        for k_, v in pc.items():
            v["p_two_sided"] = E.two_sided_p(v["estimate"], v["se"])
        ob["paired"] = pc
        # overlap of submissions with SCORE
        ov = {}
        if "SCORE" in ser:
            sc = sb[sb["method"] == "SCORE"][["seed", "i", "code"]].assign(a=1)
            for g in methods:
                if g in ("SCORE", "G0"):
                    continue
                gg = sb[sb["method"] == g][["seed", "i", "code"]].merge(sc, on=["seed", "i", "code"], how="left")
                ov[g] = float(gg["a"].notna().mean()) if len(gg) else None
        ob["share_of_submissions_also_in_SCORE"] = ov
        # D: base RankIC by year, nominations vs candidates
        icb = ic[ic["base"] == b].copy()
        icb["year"] = pd.to_datetime(icb["date"]).dt.year
        ob["base_rank_ic_by_year"] = {str(int(y)): {"mean": float(g["rank_ic"].mean()),
                                                     "t": float(g["rank_ic"].mean() / g["rank_ic"].std(ddof=1) * np.sqrt(len(g)))}
                                      for y, g in icb.groupby("year") if g["rank_ic"].notna().sum() > 20}
        e_ = icb[icb["year"].isin(years)]["rank_ic"].dropna()
        ob["base_rank_ic_eval"] = {"mean": float(e_.mean()), "sd": float(e_.std(ddof=1)), "n_days": int(len(e_)),
                                   "share_positive": float((e_ > 0).mean())}
        allnb = nom[nom["base"] == b]
        ob["mean_rho_nominations_by_year_bp"] = {str(int(y)): float(g["rho"].mean() * BP) for y, g in allnb.groupby("year")}
        top10 = allnb[allnb["pos"] < 10]
        ob["mean_rho_top10_by_year_bp"] = {str(int(y)): float(g["rho"].mean() * BP) for y, g in top10.groupby("year")}
    so["year"] = so["i"].map(year_of)
    out["mean_rho_all_candidates_by_year_bp"] = {str(int(y)): float(g["rho"].mean() * BP)
                                                 for y, g in so.dropna(subset=["year"]).groupby("year")}
    (d / "paired_contrasts.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    print("written", d / "paired_contrasts.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

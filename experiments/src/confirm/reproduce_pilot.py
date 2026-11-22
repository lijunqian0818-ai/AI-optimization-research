"""Reproduction check: a --pilot-compat smoke run of run_confirm.py against the pilot's smoke outputs.

    experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/reproduce_pilot.py \\
        --confirm experiments/results/confirm/smoke_pilotcompat \\
        --pilot experiments/results/pilot/smoke_fixedcount --pilot-dump experiments/results/pilot/smoke_dump

Compares (read-only on the pilot directories): pipeline counts, standard orders (pilot range), base tuning
values and chosen configurations, gate chosen configurations and criterion values, every submission
(base, seed, method, day, code), theta_sel / deployed metrics per method, reconciliation maxima.
Writes <confirm>/reproduction_check.json.  Numbers compared are copied, never interpreted.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def flat(x, prefix=""):
    out = {}
    if isinstance(x, dict):
        for k, v in x.items():
            out.update(flat(v, f"{prefix}/{k}"))
    elif isinstance(x, list):
        for k, v in enumerate(x):
            out.update(flat(v, f"{prefix}[{k}]"))
    else:
        out[prefix] = x
    return out


def cmp_tree(a, b, tol=0.0):
    fa, fb = flat(a), flat(b)
    keys = sorted(set(fa) | set(fb))
    diffs, maxabs = [], 0.0
    for k in keys:
        x, y = fa.get(k, "<missing>"), fb.get(k, "<missing>")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
            if x is None or y is None:
                continue
            if np.isfinite(x) and np.isfinite(y):
                d = abs(x - y)
                maxabs = max(maxabs, d)
                if d > tol:
                    diffs.append((k, x, y))
            elif not (np.isnan(x) and np.isnan(y)) and x != y:
                diffs.append((k, x, y))
        elif x != y:
            diffs.append((k, x, y))
    return {"n_keys": len(keys), "n_diff": len(diffs), "max_abs_numeric_diff": maxabs, "first_diffs": diffs[:15]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", required=True)
    ap.add_argument("--pilot", required=True)
    ap.add_argument("--pilot-dump", default="")
    a = ap.parse_args(argv)
    c, p = Path(a.confirm), Path(a.pilot)
    rc = json.loads((c / "results.json").read_text(encoding="utf-8"))
    rp = json.loads((p / "results.json").read_text(encoding="utf-8"))
    out = {}
    for k in ("market", "universe", "features", "readiness"):
        out[k] = cmp_tree(rc.get(k), rp.get(k))
    sc = {k: v for k, v in rc["standard_orders"].items() if k != "base_tuning_range_n"}
    out["standard_orders_counts"] = cmp_tree(sc, rp["standard_orders"])
    so_c = pd.read_parquet(c / "standard_orders.parquet")
    so_c = so_c[so_c["range"] == "deploy"].drop(columns=["range"]).reset_index(drop=True)
    so_p = pd.read_parquet(p / "standard_orders.parquet").reset_index(drop=True)
    same_shape = so_c.shape == so_p.shape
    eq = bool(same_shape and so_c.equals(so_p[so_c.columns]))
    out["standard_orders_table_identical"] = eq
    if same_shape and not eq:
        out["standard_orders_max_abs_rho_diff"] = float(np.abs(so_c["rho"].to_numpy() - so_p["rho"].to_numpy()).max())
    # base
    bb = {}
    for b in rp["base"]:
        tp, tc = rp["base"][b]["tuning"], rc["base"][b]["tuning"]
        mp = {json.dumps(t["config"], sort_keys=True): t["mean_rank_ic"] for t in tp}
        mc = {json.dumps(t["config"], sort_keys=True): t["mean_rank_ic"] for t in tc}
        bb[b] = {"chosen_same": rp["base"][b]["chosen"] == rc["base"][b]["chosen"],
                 "same_config_set": set(mp) == set(mc),
                 "max_abs_rank_ic_diff": max(abs(mp[k] - mc[k]) for k in mp if k in mc)}
    out["base"] = bb
    # gates: chosen configurations and criterion values
    gt = {}
    for key, tp in rp["tuning"].items():
        tc = rc["tuning"].get(key)
        if tc is None:
            gt[key] = "missing in confirm run"
            continue
        crit_p = tp.get("criterion_mean_theta_sel") or tp.get("criterion_mean_AR")
        cp = {json.dumps(x, sort_keys=True): v for x, v in zip(tp["configs"], crit_p)}
        cc = {json.dumps(x, sort_keys=True): v for x, v in zip(tc["configs"], tc["criterion_values"])}
        d = [abs(cp[k] - cc[k]) for k in cp if k in cc and np.isfinite(cp[k]) and np.isfinite(cc[k])]
        gt[key] = {"chosen_same": tp["configs"][tp["chosen"]] == tc["configs"][tc["chosen"]],
                   "same_config_set": set(cp) == set(cc), "max_abs_criterion_diff": max(d) if d else None}
    out["tuning"] = gt
    # estimates per method
    est = {}
    for b in ("lgbm", "ridge"):
        for part in ("theta_sel", "deployed", "psi", "cards_exploratory", "attribution_vs_G0"):
            A_ = rc["estimates"].get(b, {}).get(part, {})
            B_ = rp["estimates"].get(b, {}).get(part, {})
            for m in sorted(set(B_)):
                est[f"{b}|{part}|{m}"] = cmp_tree(A_.get(m), B_.get(m)) if m in A_ else "missing in confirm run"
    out["estimates"] = est
    out["estimates_methods_with_differences"] = sorted(k for k, v in est.items() if not isinstance(v, dict) or v["n_diff"])
    out["recon_max"] = {"confirm": rc.get("recon_max"), "pilot": rp.get("recon_max")}
    if a.pilot_dump:
        pd_ = Path(a.pilot_dump)
        sp = pd.read_parquet(pd_ / "submissions.parquet")[["base", "seed", "method", "i", "code"]]
        scf = pd.read_parquet(c / "submissions.parquet")[["base", "seed", "method", "i", "code"]]
        res = {}
        for m in sorted(sp["method"].unique()):
            x = sp[sp["method"] == m]
            y = scf[scf["method"] == m]
            kx = set(map(tuple, x.to_numpy().tolist()))
            ky = set(map(tuple, y.to_numpy().tolist()))
            res[m] = {"pilot_rows": len(kx), "confirm_rows": len(ky), "only_pilot": len(kx - ky), "only_confirm": len(ky - kx)}
        out["submissions"] = res
        out["submissions_methods_differing"] = sorted(m for m, v in res.items() if v["only_pilot"] or v["only_confirm"])
        np_ = pd.read_parquet(pd_ / "nominations.parquet")
        nc = pd.read_parquet(c / "nominations.parquet")
        cols = ["base", "seed", "i", "code", "pos", "score", "rho", "filled", "cell"]
        np_ = np_[cols].sort_values(["base", "seed", "i", "pos"]).reset_index(drop=True)
        nc = nc[cols].sort_values(["base", "seed", "i", "pos"]).reset_index(drop=True)
        out["nominations_identical"] = bool(np_.shape == nc.shape and np_.equals(nc))
        if np_.shape == nc.shape and not out["nominations_identical"]:
            out["nominations_max_abs_score_diff"] = float(np.abs(np_["score"] - nc["score"]).max())
            out["nominations_codes_identical"] = bool((np_["code"] == nc["code"]).all())
    (c / "reproduction_check.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("standard_orders_table_identical", "base", "estimates_methods_with_differences")
                      }, indent=1, default=str))
    if "submissions_methods_differing" in out:
        print("submissions differing:", out["submissions_methods_differing"], "nominations identical:",
              out.get("nominations_identical"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

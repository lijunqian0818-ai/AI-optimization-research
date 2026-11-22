"""Compare the records of run_pit.py on tree_R (reference) and tree_P (data dated after the inner cut-off
C perturbed).  Every object that, by the pipeline's own timing rules, may use only data dated <= C must be
bit-identical; objects that may use later data are counted as 'differ' only to show the perturbation
reached the pipeline (a test whose perturbation changes nothing would be vacuous).  No value of a
return, label, score or criterion is written; only equality counts and the keys of mismatches.

    experiments/.venv/Scripts/python.exe -X utf8 experiments/src/prefreeze_audit/compare_pit.py \
        --ref <run_R> --pert <run_P> --inner-cutoff 2019-12-31 --report <json>
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


def bits_equal(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = np.asarray(a, np.float64)
    b = np.asarray(b, np.float64)
    na, nb = np.isnan(a), np.isnan(b)
    return (na & nb) | (~na & ~nb & (a.view(np.uint64) == b.view(np.uint64)))


def tally(out, name, same: bool, key, expect_same: bool):
    e = out.setdefault(name, {"expected_identical": {"n": 0, "identical": 0, "mismatch_keys": []},
                              "allowed_to_differ": {"n": 0, "identical": 0}})
    part = e["expected_identical"] if expect_same else e["allowed_to_differ"]
    part["n"] += 1
    part["identical"] += int(same)
    if expect_same and not same and len(part["mismatch_keys"]) < 25:
        part["mismatch_keys"].append(str(key))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--pert", required=True)
    ap.add_argument("--inner-cutoff", default="2019-12-31")
    ap.add_argument("--report", required=True)
    a = ap.parse_args()
    R = pickle.load(open(Path(a.ref) / "pit_record.pkl", "rb"))
    P = pickle.load(open(Path(a.pert) / "pit_record.pkl", "rb"))
    C = date.fromisoformat(a.inner_cutoff)
    days = [date.fromisoformat(x) for x in R["days"]]
    assert days == [date.fromisoformat(x) for x in P["days"]], "calendars differ"
    iC = max(i for i, d in enumerate(days) if d <= C)            # last trading day <= C
    i1 = iC + 1                                                   # first decision day after C (uses data <= C)
    out: dict = {"inner_cutoff": str(C), "last_day_le_C": days[iC].isoformat(), "first_decision_day_after_C": days[i1].isoformat()}
    T = {}

    # 1 monthly screen: membership of month (y, m) comes from the last trading day of the previous month
    first_after = (days[i1].year, days[i1].month)
    for k in sorted(set(R["by_month"]) | set(P["by_month"])):
        tally(T, "monthly_screen_membership", R["by_month"].get(k) == P["by_month"].get(k), k, tuple(k) <= first_after)
    # 2 candidate sets (data <= t-1)
    for i in sorted(set(R["cand"]) | set(P["cand"])):
        tally(T, "candidate_sets", R["cand"].get(i) == P["cand"].get(i), days[i], i <= i1)
    # 3 rank-transformed feature rows per decision day
    hR, hP = R["frame"]["day_hash"], P["frame"]["day_hash"]
    for i in sorted(set(hR) | set(hP)):
        tally(T, "ranked_feature_rows_per_day", hR.get(i) == hP.get(i), days[i], i <= i1)
    # 4 feature panel files (raw feature values), rows <= first decision day after C
    pr, pp = Path(a.ref) / "feature_panel" / "features", Path(a.pert) / "feature_panel" / "features"
    lim = pd.Timestamp(days[i1])
    nfile = nrow_bad = nrow = 0
    bad_cols: dict = {}
    post_diff_rows = post_rows = 0
    for f in sorted(pr.glob("*.parquet")):
        g = pp / f.name
        if not g.exists():
            tally(T, "feature_panel_files", False, f.name, True)
            continue
        x, y = pd.read_parquet(f), pd.read_parquet(g)
        xe, ye = x.loc[x.index <= lim], y.loc[y.index <= lim]
        same_shape = list(xe.columns) == list(ye.columns) and list(xe.index) == list(ye.index)
        ok = same_shape
        if same_shape:
            eq = bits_equal(xe.values, ye.values)
            rb = ~eq.all(axis=1)
            nrow_bad += int(rb.sum())
            for j in np.flatnonzero(~eq.all(axis=0)):
                bad_cols[xe.columns[j]] = bad_cols.get(xe.columns[j], 0) + 1
            ok = bool(eq.all())
        nrow += len(xe)
        nfile += 1
        tally(T, "feature_panel_files", ok, f.name, True)
        xl, yl = x.loc[x.index > lim], y.loc[y.index > lim]
        common = xl.index.intersection(yl.index)
        if len(common):
            post_rows += len(common)
            post_diff_rows += int((~bits_equal(xl.loc[common].values, yl.loc[common, xl.columns].values).all(axis=1)).sum())
    out["feature_panel"] = {"files": nfile, "rows_le_first_decision_day_after_C": nrow, "rows_not_identical": nrow_bad,
                            "columns_with_mismatch": dict(sorted(bad_cols.items())[:40]),
                            "rows_after": post_rows, "rows_after_that_differ": post_diff_rows}
    # 5 base scores per (base, seed), rows of decision days <= C
    # rows are aligned by (day, code): the two runs have different candidate rows after C
    dR, dP = R["frame"]["day"], P["frame"]["day"]
    kR = {(int(i), str(c)): r for r, (i, c) in enumerate(zip(dR, R["frame"]["code"]))}
    kP = {(int(i), str(c)): r for r, (i, c) in enumerate(zip(dP, P["frame"]["code"]))}
    pre_keys_R = {k for k in kR if k[0] <= iC}
    pre_keys_P = {k for k in kP if k[0] <= iC}
    same_rows = pre_keys_R == pre_keys_P
    out["frame_rows_le_C_same_keys"] = same_rows
    out["frame_rows"] = {"ref": len(kR), "pert": len(kP), "le_C": len(pre_keys_R)}
    for b in R["bases"]:
        tally(T, "base_tuning_record", R["bases"][b]["tuning_hash"] == P["bases"][b]["tuning_hash"], b, True)
        tally(T, "base_chosen_config", R["bases"][b]["chosen_index"] == P["bases"][b]["chosen_index"], b, True)
        for s in R["bases"][b]["score"]:
            for score_kind in ("score", "rank"):
                xr, xp = R["bases"][b][score_kind][s], P["bases"][b][score_kind][s]
                by_day: dict = {}
                for k, r in kR.items():
                    p = kP.get(k)
                    ok = p is not None and bool(bits_equal(np.array([xr[r]]), np.array([xp[p]]))[0])
                    by_day.setdefault(k[0], []).append(ok)
                for k in kP:
                    if k not in kR:
                        by_day.setdefault(k[0], []).append(False)
                for i, v in sorted(by_day.items()):
                    tally(T, f"base_{score_kind}_per_day", all(v), (b, s, days[i]), i <= iC)
    # 6 nominations (top-K and top-K_tr)
    for nm in ("noms", "ktr"):
        for key in R[nm]:
            for i in sorted(set(R[nm][key]) | set(P[nm].get(key, {}))):
                tally(T, f"nominations_{nm}", R[nm][key].get(i) == P[nm].get(key, {}).get(i), (key, days[i]), i <= iC)
    # 7 training sets of every fit
    def fit_key(r):
        return (r["ctx"], r["seq"] if r["ctx"][0] == "base" else 0, r["kind"], r["conf"], r["seed"], r["objective"])
    fR = {fit_key(r): r for r in R["fits"]}
    fP = {fit_key(r): r for r in P["fits"]}
    cfg = R["config"]
    years = sorted({d.year for d in days})
    dep = [y for y in years if y >= cfg["base_deploy_start"]]
    for k in sorted(set(fR) | set(fP), key=str):
        r, p = fR.get(k), fP.get(k)
        same = r is not None and p is not None and r["train_hash"] == p["train_hash"]
        ctx = k[0]
        if ctx[0] == "base":
            b = ctx[1]
            ntune = cfg["n_configs"] * (len(cfg["seeds"]) if b == "lgbm" else 1) * len(cfg["base_tune_years"])
            seq = k[1]
            if seq < ntune:
                label, Y = "base_tuning_fit", cfg["base_tune_years"][seq % len(cfg["base_tune_years"])]
            else:
                Y = dep[(seq - ntune) % len(dep)]
                label = "base_deployment_fit"
            # base fit for year Y: rows with day <= first day of Y - 2H - 2 (labels resolved before Y)
            tally(T, f"{label}_training_set", same, (ctx, seq, Y), Y <= C.year + 1)
        elif ctx[0] == "gate":
            _g, b, s, method, conf, Y = ctx
            if k[2] == "isotonic":
                # CONF: isotonic map fitted on Y-1 nominations with labels known before Y
                tally(T, "gate_CONF_isotonic_training_set", same, (b, s, method, Y), Y - 1 <= C.year)
            else:
                # learned gates (pilot window Y-2): rows through Y-2, labels known before Y-1
                tally(T, "gate_learned_training_set", same, (b, s, method, conf, Y), Y - 1 <= C.year + 1)
    # 8 gate decisions (every configuration) on decision days <= C
    for key in sorted(set(R["gates"]) | set(P["gates"]), key=str):
        g1, g2 = R["gates"].get(key, {}), P["gates"].get(key, {})
        for i in sorted(set(g1) | set(g2)):
            tally(T, "gate_decisions_per_day_all_configs", g1.get(i) == g2.get(i), (key, days[i]), i <= iC)
    # 9 gate tuning: chosen configuration (criterion over the gate tuning year)
    for key in R["gate_tuning"]:
        r, p = R["gate_tuning"][key], P["gate_tuning"].get(key)
        tally(T, "gate_chosen_config", p is not None and r["chosen"] == p["chosen"], key, False)
        tally(T, "gate_tuning_criterion_values", p is not None and r["criterion_hash"] == p["criterion_hash"], key, False)
    # 10 standard orders: resolved by C (exit <= C) must be identical; resolved later may differ
    n_late_tune = {}
    for k, (ex, unres, h) in R["std"].items():
        i = k[0]
        if i > iC:
            continue
        q = P["std"].get(k)
        resolved_by_C = (not unres) and 0 <= ex <= iC
        tally(T, "standard_orders_decided_le_C", q is not None and q[2] == h, (days[i], k[1]), resolved_by_C)
    gy = cfg["gate_tune_years"][-1]
    for key, nm in R["noms"].items():
        tot = late = unfilled = still_open = 0
        for i, v in nm.items():
            if days[i].year != gy:
                continue
            for c in v:
                ex, unres, _ = R["std"][(i, c)]
                tot += 1
                still_open += int(unres)
                unfilled += int((not unres) and ex < 0)
                late += int((not unres) and ex > iC)
        n_late_tune[str(key)] = {"nominations_in_last_gate_tuning_year": tot, "exit_after_C": late,
                                 "open_at_data_end": still_open, "not_filled_rho_0": unfilled}
    out["gate_tuning_year_orders_resolving_after_C"] = n_late_tune
    out["tests"] = T
    viol = {k: v["expected_identical"]["n"] - v["expected_identical"]["identical"] for k, v in T.items()}
    out["violations"] = viol
    out["pass"] = all(v == 0 for v in viol.values()) and nrow_bad == 0 and same_rows
    out["non_vacuous"] = {k: v["allowed_to_differ"]["n"] - v["allowed_to_differ"]["identical"] for k, v in T.items()}
    Path(a.report).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({"pass": out["pass"], "violations": viol, "non_vacuous_differences": out["non_vacuous"],
                      "feature_panel": out["feature_panel"]}, indent=1, ensure_ascii=False, default=str))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

"""Tuning matrix and tuning curves (amendment v0.9.3 A7 / A8 item 5), from a run of run_confirm.py.

    experiments/.venv/Scripts/python.exe -X utf8 experiments/src/confirm/tuning_matrix.py --run DIR [--out FILE.md]

Prints, for every (base, method) that was tuned: inputs (including whether the base score / rank is an
input), model class, training loss, training rows and years, validation years, selection criterion,
early stopping and the data it uses, budget, compute (wall time of the trials and of the deployment
fits); then the best criterion value after 5, 10, 20, 30 trials (in the order the trials were drawn).
The static columns are derived from the code paths of strategy.py / run_confirm.py for the run's
configuration; the measured columns (rows, seconds, criterion values) are read from results.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

CURVE_AT = (5, 10, 20, 30)


def best_after(values: list, ns=CURVE_AT) -> dict:
    """Best (max) criterion value among the first n trials, in trial order; None if fewer than n trials.
    Non-finite values never win (treated as -inf)."""
    v = np.array([x if (x is not None and np.isfinite(x)) else -np.inf for x in values], dtype=float)
    out = {}
    for n in ns:
        out[n] = float(np.max(v[:n])) if len(v) >= n and np.isfinite(np.max(v[:n])) else None
    out["T"] = float(np.max(v)) if len(v) and np.isfinite(np.max(v)) else None
    return out


def spec(base: str, method: str, cfg: dict) -> dict:
    """Static description of one tuned method under the run's configuration."""
    thr = method.endswith("-thr")
    m0 = method[:-4] if thr else method
    fam = m0.split("(")[0]
    fset = m0[len(fam):].strip("()") if "(" in m0 else ""
    base_cls = "LightGBM regression" if base == "lgbm" else "ridge / elastic net (LINEAR_SPACE)"
    win = cfg.get("gate_window", "y2")
    fixed = cfg.get("gate_rule") == "fixed_count"
    btv = ",".join(map(str, cfg["base_tune_years"]))
    gtv = ",".join(map(str, cfg["gate_tune_years"]))
    seeds = len(cfg["seeds"])
    if method in ("BASE", "BASE-V"):
        return {"inputs": "B0+R (-Z set), rank-transformed; base score: no", "model": base_cls,
                "loss": "squared error on within-day rank of fwd H-day open-to-open return",
                "rows": f"all candidate rows from {cfg['first_feature_year']} with label window ending before the "
                        f"validation / deployment year (day <= first day - 2H - 2)",
                "validation": btv,
                "criterion": "mean daily RankIC over (seed, year) folds" if method == "BASE" else
                             f"pooled V of own top {int(np.ceil(cfg['c'] * cfg['K']))} eligible names / day, "
                             "pooled over validation days per seed, mean over seeds",
                "early_stopping": "none (n_estimators is a hyper-parameter)" if base == "lgbm" else "n/a",
                "seeds": seeds if base == "lgbm" else "1 (deterministic)"}
    if method == "NET-U15(-Z)":
        return {"inputs": "-Z set only (no base score / rank; round 2, Q5); population all candidates C_t",
                "model": "LightGBM regression", "loss": "squared error on rho (filled orders, label known before the target year)",
                "rows": f"all candidate rows from {cfg['first_feature_year']} with day <= first day - 2H - 2 and exit before it",
                "validation": btv,
                "criterion": "pooled V of own fixed-count names (orders resolved before v+1 only), mean over seeds",
                "early_stopping": "none (n_estimators is a hyper-parameter)", "seeds": seeds}
    if method in ("TREND", "PERF"):
        return {"inputs": "equal-weight index of the universe" if method == "TREND" else "lagged base RankIC series",
                "model": "rule (grid)", "loss": "n/a", "rows": "n/a", "validation": gtv,
                "criterion": "mean AR over tuning years x seeds (deployment backtest)", "early_stopping": "n/a",
                "seeds": seeds}
    pop = "all candidates C_t" if fam == "NET-U" else f"top-K_tr = {cfg['K_tr_mult'] * cfg['K']} of the base"
    fixed_fam = fixed and not thr and fam in ("LOSS", "LOSS-LR", "NET-K")
    w = win if fixed_fam else "y2"
    wtxt = ("base out-of-sample rows from %d through the purge point before Y (labels known before Y)" if w == "y1"
            else "base out-of-sample rows from %d through Y-2 (purged before Y-1; labels known before Y-1)") % cfg["base_deploy_start"]
    rank_in = "yes"
    model = "logistic regression (LOGIT_SPACE)" if fam == "LOSS-LR" else (
        "LightGBM binary" if fam == "LOSS" else "LightGBM regression")
    loss = "log loss on O1 loss label (filled orders)" if fam in ("LOSS", "LOSS-LR") else "squared error on rho (filled orders)"
    crit = ("pooled V of submitted orders over tuning days per seed, mean over seeds"
            if (fixed_fam and cfg.get("gate_criterion") == "V") else "mean theta_sel over (seed, year) folds")
    if cfg.get("criterion_resolved_only", False):
        crit += "; only orders resolved before v+1 (D4); -inf if a fit failed or no submission (Q3)"
    if thr:
        model += " (threshold rule of v0.8, -thr)"
    return {"inputs": f"-Z{'' if fset in ('-Z', '') else ' ' + fset} + base rank: {rank_in}; population {pop}",
            "model": model, "loss": loss, "rows": wtxt, "validation": gtv, "criterion": crit,
            "early_stopping": "none (n_estimators is a hyper-parameter)" if fam != "LOSS-LR" else "n/a",
            "seeds": seeds}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    d = Path(a.run)
    res = json.loads((d / "results.json").read_text(encoding="utf-8"))
    cfg = json.loads((d / "run_manifest.json").read_text(encoding="utf-8"))["config"]
    tun = res.get("tuning", {})
    L = ["# Tuning matrix", "", f"Run `{d}`; budget T = {cfg['n_configs']}, seeds {cfg['seeds']}, gate window "
         f"{cfg.get('gate_window')}, gate criterion {cfg.get('gate_criterion')}. Development data only.", "",
         "| base | method | inputs | model | training loss | training rows / years | validation years | criterion | "
         "early stopping | trials | seeds | mean train rows (tuning folds) | trial s | deploy s |",
         "|" + "---|" * 14]
    curves = ["", "## Best criterion value after n trials (trial order = draw order)", "",
              "| base | method | criterion | " + " | ".join(f"n={n}" for n in CURVE_AT) + " | n=T | chosen trial |",
              "|" + "---|" * (len(CURVE_AT) + 5)]
    for key in sorted(tun):
        b, m = key.split("|", 1)
        if m.startswith("follow-up"):
            continue
        t = tun[key]
        sp = spec(b, m, cfg)
        trials = t.get("trials") or []
        tsec = sum(x.get("seconds") or 0.0 for x in trials) if trials else t.get("batch_seconds")
        rows = [f.get("train_rows") for x in trials for f in x.get("folds", []) if f.get("train_rows") is not None]
        dsec = t.get("deploy_seconds")
        if isinstance(dsec, list):
            dsec = sum(x or 0.0 for x in dsec)
        L.append(f"| {b} | {m} | {sp['inputs']} | {sp['model']} | {sp['loss']} | {sp['rows']} | {sp['validation']} | "
                 f"{sp['criterion']} | {sp['early_stopping']} | {len(t.get('configs', []))} | {sp['seeds']} | "
                 f"{int(np.mean(rows)) if rows else 'n/a'} | {tsec if tsec is not None else 'n/a'} | "
                 f"{dsec if dsec is not None else 'n/a'} |")
        vals = t.get("criterion_values") or []
        ba = best_after(vals)
        fmt = lambda x: "n/a" if x is None else f"{x:.6g}"          # noqa: E731
        curves.append(f"| {b} | {m} | {t.get('criterion')} | " + " | ".join(fmt(ba[n]) for n in CURVE_AT)
                      + f" | {fmt(ba['T'])} | {t.get('chosen')} |")
    text = "\n".join(L + curves) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

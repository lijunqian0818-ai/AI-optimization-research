"""Base predictor, nominations, gates and the amendment policies (copied from pilot/strategy.py 2026-11-17;
PLAN 4.2, 4.3, 6.1, 6.3, 7, 8.3; amendment v0.9.3 A2.1, A2.2, A7).

Changes against the pilot (each marked "confirm:" at its place):
  * gate_fit_window(): fixed-count gates of deployment year Y are fitted through Y-1 ("y1", A2.1 primary);
    "y2" keeps the v0.8 / pilot window (sensitivity; threshold policies always use it);
  * select_top() / topk_mask_by_day(): the fixed-count selection with explicit rules for fewer eligible
    names than the count and for non-finite (failed) scores;
  * base_scores() also computes, from the SAME validation fits, the pooled-V criterion of the model's own
    top-ceil(cK) eligible names per day and deploys BASE-V (A7);
  * NET-U15(-Z): the all-candidate net-return gate with a fixed count of ceil(cK) (plan_review_5 row 2);
  * feature sets parsed generically, Z_O* (LHB + BLK classes) added (A4.1 P3);
  * failures (too few rows, one class, fit error, non-finite scores) are logged, not silent.

Original header of the pilot module:

Frozen annual deployment algorithm (PLAN 4.3):
  base   tuning years v: fit on rows with label windows ending before v (purge + embargo H+1), score v,
         choose the configuration with the best mean validation RankIC over tuning years x seeds;
         deployment year Y >= base_deploy_start: fit through Y-1 (purged), predict Y.  Scores are
         turned into within-day ranks before a gate uses them.
  gates  deployment year Y: fit on base out-of-sample rows through Y-2 (purged at the start of Y-1),
         calibrate and set thresholds on Y-1, deploy over Y.  Tuning years: the same with Y = v.
         Thresholds: quantile of the deployed gate model's scores on the nominated names of Y-1 (no
         labels).  Rows whose standard order is not filled are dropped from every learned gate's
         training and calibration (PLAN 4.3, M-S13).
Selection criterion (PLAN 6.3 item 3): mean theta_sel over tuning years x seeds for within-batch
methods; AR over tuning years x seeds for TREND / PERF (computed by the caller, which simulates).
"""
from __future__ import annotations

import json
import math
import threading
from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import models as M


@dataclass
class Frame:
    """Feature rows of the candidate sets: day index, code, ranked features, column names, row lookup."""
    day: np.ndarray
    code: np.ndarray
    X: np.ndarray                  # rank-transformed within day (float32, NaN kept)
    cols: list
    row: dict                      # (day, code) -> row


def year_bounds(days, years) -> dict:
    out = {}
    for y in years:
        idx = [i for i, d in enumerate(days) if d.year == y]
        if idx:
            out[y] = (idx[0], idx[-1])
    return out


# ------------------------------------------------------------------ confirm: chronology and fixed-count rules
def gate_fit_window(yb: dict, Y: int, H: int, base_deploy_start: int, window: str) -> tuple[int, int, int]:
    """(first fit row day, last fit row day, label-known-before day) of a gate deployed (or tuned) in year Y.

    "y1" (amendment A2.1 primary): rows of decision days t <= lo_Y - 2H - 2, i.e. the purge + embargo rule
         of the base predictor (train_mask in base_scores) applied at the first decision day lo_Y of Y,
         and the label must be known before lo_Y (labels(): O1 needs t + H + 1 < lo_Y; rho needs the actual
         exit day < lo_Y, which removes orders whose exit was delayed by suspension / limit-down).
    "y2" (v0.8 / pilot): rows through the end of Y-2 and t <= lo_{Y-1} - 2H - 2, labels known before lo_{Y-1}.
    The first fit row is the first base out-of-sample day (base_deploy_start), in both windows."""
    lo_fit = yb[base_deploy_start][0]
    lo_Y = yb[Y][0]
    if window == "y1":
        return lo_fit, lo_Y - 2 * H - 2, lo_Y
    if window == "y2":
        lo_1 = yb[Y - 1][0]
        hi = min(yb[Y - 2][1], lo_1 - 2 * H - 2) if (Y - 2) in yb else lo_1 - 2 * H - 2
        return lo_fit, hi, lo_1
    raise ValueError(window)


def count_for(n: int, c: float, K: int) -> int:
    """Round 2, Q1: the daily count of EVERY fixed-count policy, ceil(c * min(K, n)) with n the number of
    eligible names.  The product is rounded to 9 decimals before the ceiling, so that e.g. c = 0.3, n = 10
    gives 3 (plain math.ceil(0.3 * 10) = 4, a floating-point artefact the pilot code had for c != 0.5)."""
    if n <= 0:
        return 0
    return int(math.ceil(round(c * min(K, n), 9)))


def select_top(names, score_of, k: int, higher_better: bool, failed: str = "exclude") -> tuple[set, int]:
    """The k names with the best finite score, ties by code (primitive; the count is set by the caller).

    * fewer eligible names than k: all eligible names are submitted;
    * a name whose score is missing or non-finite is a FAILED score: with failed="exclude" it is not
      eligible that day; with failed="last" it is ranked after every finite score (ties by code).
    Returns (set of names, number of failed scores among `names`)."""
    fin, bad = [], []
    for x in names:
        v = score_of(x)
        if v is None or not np.isfinite(v):
            bad.append(x)
        else:
            fin.append((-v if higher_better else v, x))
    fin.sort()
    pick = [x for _, x in fin[:k]]
    if failed == "last" and len(pick) < k:
        pick += sorted(bad)[:k - len(pick)]
    elif failed not in ("exclude", "last"):
        raise ValueError(failed)
    return set(pick), len(bad)


def select_fixed(names, score_of, c: float, K: int, higher_better: bool, failed: str = "exclude") -> tuple[set, int]:
    """Round 2, Q1: fixed-count selection with count ceil(c * min(K, eligible)); eligible = names with a
    finite score ("exclude") or all names ("last")."""
    names = list(names)
    n_fin = sum(1 for x in names if (lambda v: v is not None and np.isfinite(v))(score_of(x)))
    n_el = n_fin if failed == "exclude" else len(names)
    return select_top(names, score_of, count_for(n_el, c, K), higher_better, failed)


def topk_mask_by_day(day: np.ndarray, code: np.ndarray, score: np.ndarray, c: float, K: int) -> np.ndarray:
    """Vectorised select_fixed(higher_better=True, failed='exclude') for every day of a long table: boolean
    mask of the rows selected (per day the count_for(n_finite) best finite scores, ties by code)."""
    df = pd.DataFrame({"d": day, "c": code, "s": score, "r": np.arange(len(day))})
    df = df[np.isfinite(df["s"].to_numpy(dtype=float))]
    df = df.sort_values(["d", "s", "c"], ascending=[True, False, True], kind="mergesort")
    pos = df.groupby("d", sort=False).cumcount().to_numpy()
    n = df.groupby("d", sort=False)["r"].transform("size").to_numpy()
    k = np.array([count_for(int(x), c, K) for x in n], dtype=int) if len(n) else np.zeros(0, int)
    pick = df["r"].to_numpy()[pos < k]
    m = np.zeros(len(day), bool)
    m[pick] = True
    return m


def resolved_mask(rows: np.ndarray, orders: dict, lo_next: int) -> np.ndarray:
    """Round 2, D4: True for orders whose outcome is known before day lo_next (unfilled orders: rho = 0, known
    at entry; filled orders: not unresolved and actual exit day < lo_next)."""
    f = orders["filled"][rows]
    return (~f) | ((~orders["unresolved"][rows]) & (orders["exit_i"][rows] >= 0) & (orders["exit_i"][rows] < lo_next))


def pooled_V(num: float, den: float) -> tuple[float, bool]:
    """V = sum rho / sum S (A2.2, A3.1).  Zero submissions overall: V = 0 and the flag is set."""
    if den <= 0:
        return 0.0, True
    return float(num / den), False


def v_parts(sub_by_day: dict, std: dict, days_range) -> tuple[float, int, int]:
    """(sum of rho over submitted orders, number of submitted orders, days with a decision) over days_range.
    rho of an unfilled standard order is 0 and counts in the denominator (A3.1)."""
    num, den, nd = 0.0, 0, 0
    for i in days_range:
        if i not in sub_by_day:
            continue
        names, _scale = sub_by_day[i]
        nd += 1
        for c in sorted(names):
            num += std[(i, c)]["rho"]
            den += 1
    return num, den, nd


def json_key(conf: dict) -> str:
    return json.dumps(conf, sort_keys=True, default=str)


def parse_fset(fset: str) -> tuple[list, str | None]:
    """'-Z' -> ([], None); '+Z_H+Z_O*' -> (['Z_H', 'Z_O*'], None); '+perm Z_O*' -> (['Z_O*'], 'Z_O*')."""
    if fset.startswith("+perm "):
        g = fset[len("+perm "):]
        return [g], g
    if fset.startswith("+noise "):                 # round 2: Gaussian noise control (A4.3 item 6)
        g = fset[len("+noise "):]
        return [g], ("noise", g)
    return [t for t in fset.split("+") if t and t != "-Z"], None


def zo_star_columns(zo_cols: list) -> list:
    """Z_O* = the Z_O columns of the LHB and BLK classes (amendment A4.1 P3, D3: INS excluded)."""
    return [c for c in zo_cols if c.startswith("zo_lhb") or c.startswith("zo_blk")]


# ------------------------------------------------------------------ base predictor
def base_target(fr: Frame, der) -> np.ndarray:
    """Within-day rank of the forward H-day open-to-open total return, demeaned (PLAN 4.2)."""
    y = np.array([der.fwd[i, der.k[c]] if c in der.k else np.nan for i, c in zip(fr.day, fr.code)], dtype=float)
    out = np.full(len(y), np.nan)
    df = pd.DataFrame({"d": fr.day, "y": y})
    r = df.groupby("d")["y"].rank(pct=True)
    ok = r.notna().to_numpy()
    out[ok] = r.to_numpy()[ok] - 0.5
    return out


def _fit_predict(kind, Xtr, ytr, Xte, conf, seed, threads, objective="regression", info: dict | None = None):
    if kind == "lgbm":
        mdl = M.fit_lgbm(Xtr, ytr, conf, seed, objective, threads)
        if objective == "binary":
            return mdl.predict_proba(Xte)[:, 1]
        return mdl.predict(Xte)
    if kind == "linear":
        return M.predict_linear(M.fit_linear(Xtr, ytr, conf), Xte)
    if kind == "logit":
        mdl = M.fit_logit(Xtr, ytr, conf)
        if info is not None:                      # round 2, Q6: convergence log of the logistic gate
            n_it = int(np.max(mdl[1].n_iter_))
            info["logit_n_iter"] = n_it
            info["logit_max_iter"] = int(mdl[1].max_iter)
            info["logit_converged"] = bool(n_it < mdl[1].max_iter)
        return M.predict_logit(mdl, Xte)
    raise ValueError(kind)


def _pmap(fn, items, workers: int):
    """Ordered parallel map in threads (LightGBM and BLAS release the GIL).  Every fit has a fixed thread count,
    so the results do not depend on the number of workers or on scheduling."""
    items = list(items)
    if workers <= 1 or len(items) <= 1:
        return [fn(x) for x in items]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, items))


def annual_model(fr: Frame, days, cfg, *, label: str, kind: str, col_idx, target: np.ndarray, label_ok, seeds,
                 tune_years, deploy_years, criteria: tuple, orders: dict | None, log, fixed: dict | None = None,
                 workers: int = 1, objective: str = "regression") -> dict:
    """Tuned annual model on the candidate rows (round 2; used by the base predictor, BASE-V and NET-U15).

    Training rows for a target year with first decision day lo: candidate rows from the first feature year
    with day <= lo - 2H - 2 (purge + embargo), a finite target and label_ok(rows, lo) (label known before lo).
    Tuning: cfg.n_configs configurations (models.draw_configs, draw order), every (seed, validation year) fold.
    Criteria: "rank_ic" = mean daily RankIC of the prediction against `target` (the base's criterion);
    "V" = for each seed the pooled V of the model's own ceil(c * min(K, eligible)) best names per validation
    day, counting only orders resolved before the first decision day of v + 1 (D4; dropped orders counted),
    mean over seeds; -inf if any seed has zero counted submissions (Q3).
    fixed: {criterion: chosen index} in --load-tuning mode -> no tuning fit at all (D1).
    Returns {"confs", "tuning" (list per trial or None), "chosen" {criterion: k}, "deploy" {k: {seed: out}}}."""
    import time as _time
    H = cfg.H
    yb = year_bounds(days, sorted({d.year for d in days}))
    confs = M.draw_configs(kind, cfg.n_configs)
    seeds = list(seeds)
    seeds_eff = seeds if kind == "lgbm" else [seeds[0]]                  # linear models are deterministic
    first_row = yb[cfg.first_feature_year][0]
    col_idx = np.asarray(col_idx)
    all_cols = len(col_idx) == fr.X.shape[1] and np.array_equal(col_idx, np.arange(fr.X.shape[1]))

    def Xof(mask):
        ii = np.flatnonzero(mask)
        return fr.X[ii] if all_cols else fr.X[np.ix_(ii, col_idx)]

    def train_mask(lo):
        m = (fr.day <= lo - 2 * H - 2) & (fr.day >= first_row) & np.isfinite(target)
        return m & label_ok(lo)

    tuning = None
    if fixed is None:
        tasks = [(ci, s, v) for ci in range(len(confs)) for s in seeds_eff for v in tune_years]

        def fold(t):
            ci, s, v = t
            t0 = _time.time()
            tr = train_mask(yb[v][0])
            te = (fr.day >= yb[v][0]) & (fr.day <= yb[v][1])
            p = np.asarray(_fit_predict(kind, Xof(tr), target[tr], Xof(te), confs[ci], s, cfg.lgbm_threads, objective),
                           dtype=float)
            f = {"seed": s, "year": v, "train_rows": int(tr.sum()),
                 "train_last_day": int(fr.day[tr].max()) if tr.any() else None}
            if "rank_ic" in criteria:
                f["rank_ic"] = float(M.spearman_by_day(fr.day[te], p, target[te]).mean())
            if "V" in criteria:
                te_i = np.flatnonzero(te)
                sel = topk_mask_by_day(fr.day[te], fr.code[te], p, cfg.c, cfg.K)
                rows = te_i[sel]
                rows = rows[np.lexsort((fr.code[rows], fr.day[rows]))]            # fixed summation order
                rr = orders["rho"][rows]
                if not np.all(np.isfinite(rr)):
                    raise RuntimeError(f"{label}: validation rows of {v} without a standard order")
                lo_next = yb[v + 1][0] if (v + 1) in yb else len(days)
                keep = resolved_mask(rows, orders, lo_next) if cfg.criterion_resolved_only else np.ones(len(rows), bool)
                f.update({"V_num": float(np.sum(rr[keep])), "V_den": int(keep.sum()),
                          "dropped_unresolved": int((~keep).sum()), "selected": int(len(rows))})
                f["V"] = pooled_V(f["V_num"], f["V_den"])[0]
            f["seconds"] = round(_time.time() - t0, 2)
            return f
        res = dict(zip(tasks, _pmap(fold, tasks, workers)))
        tuning = []
        for ci, conf in enumerate(confs):
            folds = [res[(ci, s, v)] for s in seeds_eff for v in tune_years]
            ent = {"config": conf, "folds": folds, "seconds": round(sum(f["seconds"] for f in folds), 2)}
            if "rank_ic" in criteria:
                vals = [f["rank_ic"] for f in folds]
                ent["values"] = vals
                ent["mean_rank_ic"] = float(np.nanmean(vals)) if np.isfinite(vals).any() else float("nan")
            if "V" in criteria:
                pv = {s: pooled_V(sum(f["V_num"] for f in folds if f["seed"] == s),
                                  sum(f["V_den"] for f in folds if f["seed"] == s)) for s in seeds_eff}
                ent["V_pooled_by_seed"] = {str(s): v_[0] for s, v_ in pv.items()}
                ent["V_zero_submission_flag"] = any(fl for _, fl in pv.values())
                ent["criterion_V_reported"] = float(np.mean([v_[0] for v_ in pv.values()]))
                ent["criterion_V"] = -np.inf if ent["V_zero_submission_flag"] else ent["criterion_V_reported"]
                ent["dropped_unresolved"] = int(sum(f["dropped_unresolved"] for f in folds))
            tuning.append(ent)
            log(f"[{label}] config {ci + 1}/{len(confs)} validation criteria computed ({ent['seconds']} s fit time)")
        chosen = {}
        if "rank_ic" in criteria:
            chosen["rank_ic"] = max(range(len(confs)), key=lambda k: (
                tuning[k]["mean_rank_ic"] if np.isfinite(tuning[k]["mean_rank_ic"]) else -9, -k))
        if "V" in criteria:
            chosen["V"] = max(range(len(confs)), key=lambda k: (tuning[k]["criterion_V"], -k))
    else:
        chosen = {k: int(v) for k, v in fixed.items()}
        log(f"[{label}] configurations loaded from the tuning archive: {chosen} (no tuning fit)")

    deploy = {}
    for k in sorted(set(chosen.values())):
        tasks = [(s, Y) for s in seeds_eff for Y in deploy_years if Y in yb]

        def dep(t):
            s, Y = t
            t0 = _time.time()
            tr = train_mask(yb[Y][0])
            te = (fr.day >= yb[Y][0]) & (fr.day <= yb[Y][1])
            if not te.any():
                return None
            p = _fit_predict(kind, Xof(tr), target[tr], Xof(te), confs[k], s, cfg.lgbm_threads, objective)
            return te, p, {"seed": s, "year": Y, "train_rows": int(tr.sum()), "train_last_day": int(fr.day[tr].max()),
                           "seconds": round(_time.time() - t0, 2)}
        got = dict(zip(tasks, _pmap(dep, tasks, workers)))
        out = {}
        for s in seeds:
            s_fit = s if kind == "lgbm" else seeds[0]
            if s_fit != s:
                out[s] = out[s_fit]
                continue
            score = np.full(len(fr.day), np.nan)
            fits = []
            for Y in deploy_years:
                g = got.get((s, Y))
                if g is None:
                    continue
                score[g[0]] = g[1]
                fits.append(g[2])
            rank = pd.Series(score).groupby(fr.day).rank(pct=True).to_numpy()
            out[s] = {"score": score, "rank": rank, "config": confs[k], "deploy_fits": fits,
                      "deploy_seconds": round(sum(f["seconds"] for f in fits), 1), "chosen_index": k}
            log(f"[{label}] configuration {k}, seed {s}: deployment fits done")
        deploy[k] = out
    return {"confs": confs, "tuning": tuning, "chosen": chosen, "deploy": deploy}


def base_scores(fr: Frame, y: np.ndarray, days, cfg, base: str, seeds, log, orders: dict | None = None,
                want_basev: bool = False, col_idx=None, fixed: dict | None = None, workers: int = 1
                ) -> tuple[dict, dict | None, dict]:
    """Base predictor (RankIC-tuned) and BASE-V (A7), from the SAME validation fits (round 2: via annual_model).
    BASE-V differs from the base only in the selection criterion: pooled V of its own fixed-count names
    (Q1 count, D4 resolved orders, Q3 -inf).  col_idx: feature columns (round 2: the -Z set, see report).
    Returns (base {seed: ...}, basev {seed: ...} or None, model record)."""
    kind = "lgbm" if base == "lgbm" else "linear"
    crit = ("rank_ic", "V") if want_basev else ("rank_ic",)
    years = [y_ for y_ in sorted({d.year for d in days}) if y_ >= cfg.base_deploy_start]
    if col_idx is None:
        col_idx = np.arange(fr.X.shape[1])
    rec = annual_model(fr, days, cfg, label=f"base {base}", kind=kind, col_idx=col_idx, target=y,
                       label_ok=lambda lo: np.ones(len(fr.day), bool), seeds=seeds, tune_years=cfg.base_tune_years,
                       deploy_years=years, criteria=crit, orders=orders, log=log, fixed=fixed, workers=workers)
    kb = rec["chosen"]["rank_ic"]
    out = {s: dict(v, tuning=rec["tuning"], chosen_index=kb) for s, v in rec["deploy"][kb].items()}
    outv = None
    if want_basev:
        kv = rec["chosen"]["V"]
        outv = {s: dict(v, tuning=rec["tuning"], chosen_index=kv, reused_base_fits=(kv == kb))
                for s, v in rec["deploy"][kv].items()}
    return out, outv, rec


def netu15_scores(fr: Frame, days, cfg, seeds, log, orders: dict, col_idx, deploy_years, fixed: dict | None = None,
                  workers: int = 1) -> tuple[dict, dict]:
    """NET-U15(-Z), round 2 (Q4, Q5): a pure end-to-end LightGBM regression of the standard-order net return rho
    on the -Z features of all candidates (no base score or rank), trained on filled orders whose label is known
    before the target year (purge + embargo as the base), tuned on the base validation years (2011-2012) by
    pooled V of its own fixed-count names (D4, Q3), refitted annually.  It does not depend on the base, so one
    model serves both bases."""
    H = cfg.H
    tgt = np.where(orders["filled"], orders["rho"], np.nan)

    def label_ok(lo):
        return orders["filled"] & ~orders["unresolved"] & (orders["exit_i"] >= 0) & (orders["exit_i"] < lo)
    rec = annual_model(fr, days, cfg, label="NET-U15", kind="lgbm", col_idx=col_idx, target=tgt, label_ok=label_ok,
                       seeds=seeds, tune_years=cfg.base_tune_years, deploy_years=deploy_years, criteria=("V",),
                       orders=orders, log=log, fixed=fixed, workers=workers)
    k = rec["chosen"]["V"]
    return {s: dict(v, tuning=rec["tuning"], chosen_index=k) for s, v in rec["deploy"][k].items()}, rec


def nominations(fr: Frame, rank: np.ndarray, cand: dict, K: int, first_i: int) -> dict:
    """{i: list of codes} = top-K by base score among C_t (ties by code), days >= first_i."""
    df = pd.DataFrame({"d": fr.day, "c": fr.code, "r": rank})
    df = df[(df["d"] >= first_i) & df["r"].notna()]
    out = {}
    for i, g in df.groupby("d"):
        g = g.sort_values(["r", "c"], ascending=[False, True])
        out[int(i)] = list(g["c"].iloc[:K])
    return out


# ------------------------------------------------------------------ strata and theta_sel
def strata(codes: list, i: int, der) -> dict:
    """Liquidity tercile x volatility tercile within the list (data through t-1; PLAN 8.3).  NaN sorts
    last (highest tercile); ties by code."""
    n = len(codes)
    if n == 0:
        return {}

    def terc(vals):
        order = sorted(range(n), key=lambda k: (np.inf if not np.isfinite(vals[k]) else vals[k], codes[k]))
        t = {}
        for r, k in enumerate(order):
            t[codes[k]] = min(2, (3 * r) // n)
        return t
    liq = terc([der.adv[i, der.k[c]] for c in codes])
    vol = terc([der.vol20[i, der.k[c]] for c in codes])
    return {c: 3 * liq[c] + vol[c] for c in codes}


def u_and_S(sub: set, noms: list, rho: dict, cell: dict) -> tuple[float, int, dict]:
    """u_t^g = sum_{i in Sub} rho - sum_s S_{t,s} rhobar_{t,s}; also per-cell counts (PLAN 8.3)."""
    by_cell: dict = {}
    for c in noms:
        by_cell.setdefault(cell[c], []).append(c)
    u, S, info = 0.0, 0, {"choice": 0, "pf": 0.0, "wf": 0.0}
    for s, names in by_cell.items():
        vals = np.array([rho[(c)] for c in names], dtype=float)
        k = sum(1 for c in names if c in sub)
        if k == 0:
            continue
        mean = vals.mean()
        u += sum(rho[c] for c in names if c in sub) - k * mean
        S += k
        if 0 < k < len(names):
            info["choice"] += k
        srt = np.sort(vals)
        info["pf"] += srt[-k:].sum() - k * mean
        info["wf"] += srt[:k].sum() - k * mean
    return u, S, info


# ------------------------------------------------------------------ gate fits
def _isotonic(x, y):
    from sklearn.isotonic import IsotonicRegression
    m = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    m.fit(x, y)
    return m


def q(x, p):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(np.quantile(x, p)) if len(x) else np.nan


class GateContext:
    """Everything a gate needs for one (base, seed)."""

    def __init__(self, fr: Frame, base_rank: np.ndarray, noms: dict, ktr: dict, cand: dict, std: dict, der, cfg,
                 days, colsets: dict, seed: int, perm_seed: int):
        self.fr, self.rank, self.noms, self.ktr, self.cand, self.std, self.der = fr, base_rank, noms, ktr, cand, std, der
        self.cfg, self.days, self.colsets, self.seed = cfg, days, colsets, seed
        self.yb = year_bounds(days, sorted({d.year for d in days}))
        self.col_idx = {c: j for j, c in enumerate(fr.cols)}
        self.rng_perm = np.random.default_rng(perm_seed)
        self.perm_seed = int(perm_seed)
        self._perm_cache: dict = {}
        self.failures: list = []          # confirm: (method, year, reason) of every gate fit that produced no score
        self.failed_scores: dict = {}     # confirm: method -> number of (day, name) with a non-finite score
        self.fit_info: dict = {}          # confirm: (method, year, conf json) -> training rows / window
        self._lock = threading.Lock()

    # ---- design matrices
    def rows_for(self, pop: dict, lo: int, hi: int) -> np.ndarray:
        rr = []
        for i in range(lo, hi + 1):
            for c in pop.get(i, ()):
                r = self.fr.row.get((i, c))
                if r is not None:
                    rr.append(r)
        return np.array(rr, dtype=int)

    def design(self, rows: np.ndarray, fset: str, include_rank: bool = True, draw: int | None = None) -> np.ndarray:
        """-Z columns, then the groups of fset in order (pilot order: Z_H before Z_O), then the base rank.
        '+perm G' replaces the group's columns by a permutation; '+noise G' (round 2, A4.3 item 6) by as many
        independent standard-normal columns.  draw = index of the follow-up draw (None: the pilot's single
        cached draw)."""
        groups, perm = parse_fset(fset)
        cols = list(self.colsets["-Z"])
        for g in groups:
            cols += self.colsets[g]
        X = self.fr.X[rows][:, [self.col_idx[c] for c in cols]]
        if include_rank:
            X = np.hstack([X, self.rank[rows].reshape(-1, 1).astype(np.float32)])
        if perm is not None:
            X = X.copy()
            kind_, grp = perm if isinstance(perm, tuple) else ("perm", perm)
            a, b = len(self.colsets["-Z"]), len(self.colsets["-Z"]) + len(self.colsets[grp])
            if draw is None and kind_ == "perm":
                X[:, a:b] = self._permuted(rows, grp)
            else:
                X[:, a:b] = self._draw_matrix(rows, grp, kind_, 0 if draw is None else draw)
        return X

    GROUP_ID = {"Z_H": 1, "Z_O": 2, "Z_O*": 3}

    def _draw_matrix(self, rows, grp, kind_: str, draw: int) -> np.ndarray:
        """Round 2, A4.3 item 6: draw `draw` of the permuted ('perm') or Gaussian-noise ('noise') columns of a
        group on the top-K_tr rows of every day.  The random stream is keyed by (perm seed, group, kind, draw),
        so a draw does not depend on scheduling or on other draws.  Cached until drop_draw()."""
        key = (grp, kind_, draw)
        with self._lock:
            got = self._perm_cache.get(key)
        if got is None:
            allrows = np.sort(self.rows_for(self.ktr, min(self.ktr), max(self.ktr)))
            cols = self.colsets[grp]
            gid = self.GROUP_ID[grp]
            rng = np.random.default_rng([self.perm_seed, gid, 0 if kind_ == "perm" else 1, int(draw)])
            if kind_ == "noise":
                M_ = rng.standard_normal((len(allrows), len(cols))).astype(np.float32)
            else:
                Z = self.fr.X[np.ix_(allrows, [self.col_idx[c] for c in cols])]
                M_ = Z.copy()
                classes = [cols] if grp == "Z_H" else [[c for c in cols if c.startswith(f"zo_{k}")] for k in ("lhb", "blk", "ins")]
                classes = [cl for cl in classes if cl]
                pos = {c: j for j, c in enumerate(cols)}
                d = self.fr.day[allrows]
                for day in np.unique(d):
                    ii = np.flatnonzero(d == day)
                    for cl in classes:
                        jj = [pos[c] for c in cl]
                        pr = rng.permutation(len(ii))
                        M_[np.ix_(ii, jj)] = Z[np.ix_(ii[pr], jj)]
            got = (allrows, M_)
            with self._lock:
                self._perm_cache[key] = got
        allrows, M_ = got
        k = np.searchsorted(allrows, rows)
        ok = (k < len(allrows)) & (allrows[np.minimum(k, len(allrows) - 1)] == rows)
        out = np.full((len(rows), M_.shape[1]), np.nan, np.float32)
        out[ok] = M_[k[ok]]
        return out

    def drop_draw(self, grp, kind_, draw):
        with self._lock:
            self._perm_cache.pop((grp, kind_, draw), None)

    def _permuted(self, rows, grp):
        """Z columns permuted across the top-K_tr population within each day (PLAN 7.3 c); for Z_O / Z_O*
        within day and class (columns of one class move together).  One draw per seed, cached by row."""
        key = grp
        if key not in self._perm_cache:
            allrows = self.rows_for(self.ktr, min(self.ktr), max(self.ktr))
            cols = self.colsets[grp]
            Z = self.fr.X[:, [self.col_idx[c] for c in cols]]
            out = {}
            classes = [cols] if grp == "Z_H" else [[c for c in cols if c.startswith(f"zo_{k}")] for k in ("lhb", "blk", "ins")]
            classes = [cl for cl in classes if cl]          # confirm: Z_O* has no INS class
            pos = {c: j for j, c in enumerate(cols)}
            d = self.fr.day[allrows]
            for day in np.unique(d):
                rr = allrows[d == day]
                block = Z[rr].copy()
                for cl in classes:
                    jj = [pos[c] for c in cl]
                    perm = self.rng_perm.permutation(len(rr))
                    block[:, jj] = Z[rr][perm][:, jj]
                for r, v in zip(rr, block):
                    out[int(r)] = v
            self._perm_cache[key] = out
        cache = self._perm_cache[key]
        n = len(self.colsets[grp])
        return np.array([cache.get(int(r), np.full(n, np.nan, np.float32)) for r in rows], dtype=np.float32)

    def labels(self, rows: np.ndarray, target: str, known_before: int) -> tuple[np.ndarray, np.ndarray]:
        """(mask of usable rows, target) - filled standard orders only; the label must be known before
        day `known_before` (O1: frozen at t+H+1; rho: exit day)."""
        H = self.cfg.H
        ok = np.zeros(len(rows), bool)
        yv = np.full(len(rows), np.nan)
        for k, r in enumerate(rows):
            rec = self.std.get((int(self.fr.day[r]), self.fr.code[r]))
            if rec is None or not rec["filled"]:
                continue
            t = int(self.fr.day[r])
            if target == "o1":
                if not np.isfinite(rec["o1"]) or t + H + 1 >= known_before:
                    continue
                yv[k] = rec["o1"]
            elif target == "rho":
                if rec["unresolved"] or rec["exit_i"] < 0 or rec["exit_i"] >= known_before:
                    continue
                yv[k] = rec["rho"]
            elif target == "pos":
                if rec["unresolved"] or rec["exit_i"] < 0 or rec["exit_i"] >= known_before:
                    continue
                yv[k] = float(rec["rho"] > 0)
            ok[k] = True
        return ok, yv

    # ---- one gate for one deployment (or tuning) year
    @staticmethod
    def parse_method(method: str) -> tuple[str, str, bool, int | None]:
        """'LOSS(+perm Z_H)#3' -> ('LOSS', '+perm Z_H', False, 3); 'LOSS(-Z)-thr' -> ('LOSS', '-Z', True, None)."""
        draw = None
        if "#" in method:
            method, d = method.rsplit("#", 1)
            draw = int(d)
        thr = method.endswith("-thr")
        if thr:
            method = method[:-4]
        fam = method.split("(")[0]
        fset = method[method.index("(") + 1:method.rindex(")")] if "(" in method else ""
        return fam, fset, thr, draw

    def gate_year(self, method: str, conf: dict, Y: int) -> dict:
        """{day: (set of submitted codes, scale)} for decision days of year Y."""
        cfg, H, c = self.cfg, self.cfg.H, self.cfg.c
        lo_Y, hi_Y = self.yb[Y]
        lo_1, hi_1 = self.yb[Y - 1]
        noms_Y = {i: self.noms[i] for i in range(lo_Y, hi_Y + 1) if i in self.noms}
        out = {}
        fixed = getattr(cfg, "gate_rule", "threshold") == "fixed_count"
        rule = getattr(cfg, "failed_score", "exclude")

        def top_k(v, key):
            """fixed_count rule: the count_for(len(v)) nominations with the smallest key (ties by code)."""
            k = count_for(len(v), c, cfg.K)
            return set(sorted(v, key=lambda x: (key(x), x))[:k])
        if method == "G0":
            return {i: (set(v), 1.0) for i, v in noms_Y.items()}
        if method == "SCORE":
            # round 2, Q1: count_for(n_t) = ceil(c min(K, n_t)) (the pilot: ceil(c K); identical when n_t = K)
            return {i: (set(v[:count_for(len(v), c, cfg.K)]), 1.0) for i, v in noms_Y.items()}
        if method in ("VOL", "LIQ"):
            arr = self.der.vol20 if method == "VOL" else self.der.adv
            cal = [arr[i, self.der.k[x]] for i in range(lo_1, hi_1 + 1) for x in self.noms.get(i, ())]
            thr_ = q(cal, c if method == "VOL" else 1 - c)
            for i, v in noms_Y.items():
                vals = {x: arr[i, self.der.k[x]] for x in v}
                if fixed:   # lowest volatility / highest liquidity first; a missing value is kept first, as under the threshold rule
                    sgn = 1.0 if method == "VOL" else -1.0
                    out[i] = (top_k(v, lambda x: sgn * vals[x] if np.isfinite(vals[x]) else -np.inf), 1.0)
                    continue
                if method == "VOL":
                    out[i] = ({x for x in v if not (np.isfinite(vals[x]) and vals[x] > thr_)}, 1.0)
                else:
                    out[i] = ({x for x in v if not (np.isfinite(vals[x]) and vals[x] < thr_)}, 1.0)
            return out
        if method == "CONF":
            rows = self.rows_for(self.noms, lo_1, hi_1)
            ok, yv = self.labels(rows, "pos", lo_Y)
            if ok.sum() < 10:
                return {i: (set(), 1.0) for i in noms_Y}
            iso = _isotonic(self.rank[rows][ok], yv[ok])
            thr_ = q(iso.predict(self.rank[rows]), 1 - c)
            for i, v in noms_Y.items():
                rr = [self.fr.row[(i, x)] for x in v]
                p = iso.predict(self.rank[rr])
                out[i] = ({x for x, pp in zip(v, p) if pp >= thr_}, 1.0)
            return out
        # learned gates on the top-K_tr population (NET-U: all of C_t)
        fam, fset, thr_policy, draw = self.parse_method(method)
        if fam == "NET-U15":
            raise ValueError("NET-U15 is an end-to-end model since round 2 (strategy.netu15_scores)")
        # which gates use the fixed-count rule and the configurable window.  NET-U (threshold, unchanged), the
        # -thr secondary policies (round 2) and every threshold-rule run keep the v0.8 window through Y-2.
        fixed_g = fixed and not thr_policy
        fixed_fam = fixed_g and fam in ("LOSS", "LOSS-LR", "NET-K")
        window = getattr(cfg, "gate_window", "y2") if fixed_fam else "y2"
        all_pop = fam == "NET-U"
        pop = self.cand if all_pop else self.ktr
        lo_fit, hi_fit, known_before = gate_fit_window(self.yb, Y, H, cfg.base_deploy_start, window)
        rows_fit = self.rows_for(pop, lo_fit, hi_fit)
        target = "o1" if fam in ("LOSS", "LOSS-LR") else "rho"
        ok, yv = self.labels(rows_fit, target, known_before)
        rows_fit, yv = rows_fit[ok], yv[ok]
        info_key = (method, Y, json_key(conf))
        info = {"window": window, "fit_first_day": int(lo_fit), "fit_last_day_rule": int(hi_fit),
                "label_known_before": int(known_before), "rows": int(len(rows_fit)),
                "last_row_day": int(self.fr.day[rows_fit].max()) if len(rows_fit) else None, "failed": False}
        self.fit_info[info_key] = info
        if len(rows_fit) < 50 or (target == "o1" and len(np.unique(yv)) < 2):
            info["failed"] = True
            self.failures.append({"method": method, "year": Y, "reason": "too few usable rows or one class",
                                  "rows": int(len(rows_fit))})
            return {i: (set(), 1.0) for i in noms_Y}
        Xf = self.design(rows_fit, fset, True, draw)
        kind = {"LOSS": "lgbm", "NET-K": "lgbm", "NET-U": "lgbm", "LOSS-LR": "logit"}[fam]
        obj = "binary" if fam == "LOSS" else "regression"
        pop_dep = self.cand if all_pop else self.noms
        rows_dep = self.rows_for(pop_dep, lo_Y, hi_Y)
        # a fixed-count gate needs no calibration year, so Y-1 rows are not scored (row-wise predictions)
        rows_cal = np.zeros(0, dtype=int) if fixed_fam else self.rows_for(pop_dep, lo_1, hi_1)
        both = np.r_[rows_cal, rows_dep]
        try:
            pred = _fit_predict(kind, Xf, yv, self.design(both, fset, True, draw), conf, self.seed,
                                cfg.lgbm_threads, obj, info)
        except Exception as e:                      # logged and flagged; the year submits nothing
            info["failed"] = True
            self.failures.append({"method": method, "year": Y, "reason": f"fit/predict error: {type(e).__name__}: {e}",
                                  "rows": int(len(rows_fit))})
            return {i: (set(), 1.0) for i in noms_Y}
        p_cal, p_dep = pred[:len(rows_cal)], pred[len(rows_cal):]
        score = {(int(self.fr.day[r]), self.fr.code[r]): float(p) for r, p in zip(rows_dep, p_dep)}

        def fixed_pick(i, names, higher):
            s_, nbad = select_fixed(names, lambda x: score.get((i, x)), c, cfg.K, higher, rule)
            if nbad:
                with self._lock:
                    self.failed_scores[method] = self.failed_scores.get(method, 0) + nbad
            return s_
        if fam in ("LOSS", "LOSS-LR"):
            if fixed_g:
                for i, v in noms_Y.items():
                    out[i] = (fixed_pick(i, v, False), 1.0)
                return out
            thr_ = q(p_cal, c)
            for i, v in noms_Y.items():
                out[i] = ({x for x in v if score.get((i, x), np.inf) <= thr_}, 1.0)
            return out
        if fam == "NET-K":
            if fixed_g:
                for i, v in noms_Y.items():
                    out[i] = (fixed_pick(i, v, True), 1.0)
                return out
            thr_ = q(p_cal, 1 - c)
            for i, v in noms_Y.items():
                out[i] = ({x for x in v if score.get((i, x), -np.inf) >= thr_}, 1.0)
            return out
        # NET-U: threshold so that the mean number of orders per day on Y-1 is c K (at most K per day)
        cal_by_day: dict = {}
        for r, p in zip(rows_cal, p_cal):
            cal_by_day.setdefault(int(self.fr.day[r]), []).append(p)
        grid = np.unique(np.quantile(p_cal, np.linspace(0, 1, 401))) if len(p_cal) else np.array([np.inf])
        target_n = c * cfg.K
        best, gap = grid[-1], np.inf
        for t in grid:
            mean_n = np.mean([min(cfg.K, int(np.sum(np.asarray(v) >= t))) for v in cal_by_day.values()]) if cal_by_day else 0
            if abs(mean_n - target_n) < gap:
                best, gap = t, abs(mean_n - target_n)
        for i in range(lo_Y, hi_Y + 1):
            cs = [(score[(i, x)], x) for x in self.cand.get(i, ()) if (i, x) in score]
            cs = sorted([z for z in cs if z[0] >= best], key=lambda z: (-z[0], z[1]))[:cfg.K]
            out[i] = ({x for _, x in cs}, 1.0)
        return out


def basev_subs(fr: Frame, score: np.ndarray, cand: dict, days_list, c: float, K: int,
               failed: str = "exclude") -> tuple[dict, int]:
    """BASE-V (and, round 2, NET-U15) policy: its own count_for(eligible) best eligible candidates by its score
    on each decision day (Q1).  Eligible = in C_t with a finite score."""
    out, nbad = {}, 0
    for i in days_list:
        names = list(cand.get(i, ()))
        s_, b_ = select_fixed(names, lambda x: _score_at(fr, score, i, x), c, K, True, failed)
        out[i] = (s_, 1.0)
        nbad += b_
    return out, nbad


def rerank_subs(fr: Frame, score: np.ndarray, noms: dict, days_list, c: float, K: int,
                failed: str = "exclude") -> tuple[dict, int]:
    """BASEV-RERANK: the BASE-V score picks count_for(n_t) of the RankIC base's n_t nominations (Q1)."""
    out, nbad = {}, 0
    for i in days_list:
        v = noms.get(i)
        if v is None:
            continue
        s_, b_ = select_fixed(v, lambda x: _score_at(fr, score, i, x), c, K, True, failed)
        out[i] = (s_, 1.0)
        nbad += b_
    return out, nbad


def _score_at(fr: Frame, score: np.ndarray, i: int, x: str):
    r = fr.row.get((int(i), x))
    return None if r is None else float(score[r])


def theta_sel(sub_by_day: dict, noms: dict, std: dict, der, days_range) -> dict:
    """theta_sel and its reporting items over decision days in days_range (PLAN 8.3)."""
    rows = []
    for i in days_range:
        v = noms.get(i)
        if not v:
            continue
        sub, _scale = sub_by_day.get(i, (set(), 1.0))
        rho = {c: std[(i, c)]["rho"] for c in v}
        cell = strata(v, i, der)
        u, S, info = u_and_S(sub & set(v), v, rho, cell)
        abst = [rho[c] for c in v if c not in sub]
        rows.append({"i": i, "u": u, "S": S, "choice": info["choice"], "pf": info["pf"], "wf": info["wf"],
                     "n_nom": len(v), "abst_sum": float(np.sum(abst)) if abst else 0.0, "abst_n": len(abst)})
    df = pd.DataFrame(rows)
    if not len(df):
        return {"days": 0}
    St = df["S"].sum()
    return {"days": int(len(df)), "theta_sel": float(df["u"].sum() / St) if St else np.nan,
            "S_total": int(St), "iota": float(df["choice"].sum() / St) if St else np.nan,
            "theta_PF": float(df["pf"].sum() / St) if St else np.nan,
            "theta_WF": float(df["wf"].sum() / St) if St else np.nan,
            "share_days_S_0_or_K": float(((df["S"] == 0) | (df["S"] == df["n_nom"])).mean()),
            "submission_coverage": float(St / df["n_nom"].sum()),
            "abstained_mean_rho": float(df["abst_sum"].sum() / df["abst_n"].sum()) if df["abst_n"].sum() else np.nan,
            "series": df[["i", "u", "S"]]}


def theta_sel_pool(sub_by_day: dict, cand: dict, std: dict, der, days_range) -> dict:
    """NET-U: the same statistic on its own pool C_t, strata within C_t (PLAN 6.1)."""
    return theta_sel(sub_by_day, {i: list(cand.get(i, ())) for i in days_range}, std, der, days_range)

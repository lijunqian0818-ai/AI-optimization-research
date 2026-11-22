"""Base predictor, nominations and gates of the pilot (PLAN 4.2, 4.3, 6.1, 6.3, 7, 8.3).

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

import math
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


def _fit_predict(kind, Xtr, ytr, Xte, conf, seed, threads, objective="regression"):
    if kind == "lgbm":
        mdl = M.fit_lgbm(Xtr, ytr, conf, seed, objective, threads)
        if objective == "binary":
            return mdl.predict_proba(Xte)[:, 1]
        return mdl.predict(Xte)
    if kind == "linear":
        return M.predict_linear(M.fit_linear(Xtr, ytr, conf), Xte)
    if kind == "logit":
        return M.predict_logit(M.fit_logit(Xtr, ytr, conf), Xte)
    raise ValueError(kind)


def base_scores(fr: Frame, y: np.ndarray, days, cfg, base: str, seeds, log) -> dict:
    """Returns {seed: {"score": array over rows (NaN outside deployment years), "rank": within-day rank,
    "config": chosen, "tuning": [...]}}."""
    kind = "lgbm" if base == "lgbm" else "linear"
    H = cfg.H
    yb = year_bounds(days, sorted({d.year for d in days}))
    cols = fr.cols
    confs = M.draw_configs(kind, cfg.n_configs)
    seeds_eff = list(seeds) if kind == "lgbm" else [seeds[0]]            # ridge / enet are deterministic

    def train_mask(first_i_target):
        return (fr.day <= first_i_target - 2 * H - 2) & np.isfinite(y) & (fr.day >= yb[cfg.first_feature_year][0])

    tuning = []
    for ci, conf in enumerate(confs):
        vals = []
        for s in seeds_eff:
            for v in cfg.base_tune_years:
                tr = train_mask(yb[v][0])
                te = (fr.day >= yb[v][0]) & (fr.day <= yb[v][1])
                p = _fit_predict(kind, fr.X[tr], y[tr], fr.X[te], conf, s, cfg.lgbm_threads)
                ic = M.spearman_by_day(fr.day[te], p, y[te]).mean()
                vals.append(float(ic))
        tuning.append({"config": conf, "mean_rank_ic": float(np.nanmean(vals)), "values": vals})
        log(f"[base {base}] config {ci + 1}/{len(confs)} mean validation RankIC computed")
    best = max(range(len(confs)), key=lambda k: (tuning[k]["mean_rank_ic"] if np.isfinite(tuning[k]["mean_rank_ic"]) else -9, -k))
    conf = confs[best]
    out = {}
    years = [y_ for y_ in sorted(yb) if y_ >= cfg.base_deploy_start]
    for s in seeds:
        s_fit = s if kind == "lgbm" else seeds[0]
        if kind != "lgbm" and seeds[0] in out:
            out[s] = out[seeds[0]]
            continue
        score = np.full(len(y), np.nan)
        for Y in years:
            tr = train_mask(yb[Y][0])
            te = (fr.day >= yb[Y][0]) & (fr.day <= yb[Y][1])
            if not te.any():
                continue
            score[te] = _fit_predict(kind, fr.X[tr], y[tr], fr.X[te], conf, s_fit, cfg.lgbm_threads)
        rank = pd.Series(score).groupby(fr.day).rank(pct=True).to_numpy()
        out[s] = {"score": score, "rank": rank, "config": conf}
        log(f"[base {base}] seed {s}: deployment fits done")
    for s in out:
        out[s]["tuning"] = tuning
        out[s]["chosen_index"] = best
    return out


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
        self._perm_cache: dict = {}

    # ---- design matrices
    def rows_for(self, pop: dict, lo: int, hi: int) -> np.ndarray:
        rr = []
        for i in range(lo, hi + 1):
            for c in pop.get(i, ()):
                r = self.fr.row.get((i, c))
                if r is not None:
                    rr.append(r)
        return np.array(rr, dtype=int)

    def design(self, rows: np.ndarray, fset: str) -> np.ndarray:
        cols = list(self.colsets["-Z"])
        if fset in ("+Z_H", "+Z_H+Z_O", "+perm Z_H"):
            cols += self.colsets["Z_H"]
        if fset in ("+Z_O", "+Z_H+Z_O", "+perm Z_O"):
            cols += self.colsets["Z_O"]
        X = self.fr.X[rows][:, [self.col_idx[c] for c in cols]]
        X = np.hstack([X, self.rank[rows].reshape(-1, 1).astype(np.float32)])
        if fset.startswith("+perm"):
            X = X.copy()
            grp = "Z_H" if "Z_H" in fset else "Z_O"
            X[:, len(self.colsets["-Z"]):len(self.colsets["-Z"]) + len(self.colsets[grp])] = self._permuted(rows, grp)
        return X

    def _permuted(self, rows, grp):
        """Z columns permuted across the top-K_tr population within each day (PLAN 7.3 c); for Z_O within
        day and class (columns of one class move together).  One draw per seed, cached by row."""
        key = grp
        if key not in self._perm_cache:
            allrows = self.rows_for(self.ktr, min(self.ktr), max(self.ktr))
            cols = self.colsets[grp]
            Z = self.fr.X[:, [self.col_idx[c] for c in cols]]
            out = {}
            classes = [cols] if grp == "Z_H" else [[c for c in cols if c.startswith(f"zo_{k}")] for k in ("lhb", "blk", "ins")]
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
    def gate_year(self, method: str, conf: dict, Y: int) -> dict:
        """{day: (set of submitted codes, scale)} for decision days of year Y."""
        cfg, H, c = self.cfg, self.cfg.H, self.cfg.c
        lo_Y, hi_Y = self.yb[Y]
        lo_1, hi_1 = self.yb[Y - 1]
        noms_Y = {i: self.noms[i] for i in range(lo_Y, hi_Y + 1) if i in self.noms}
        out = {}
        fixed = getattr(cfg, "gate_rule", "threshold") == "fixed_count"

        def top_k(v, key):
            """fixed_count rule: the ceil(c * len(v)) nominations with the smallest key (ties by code)."""
            k = math.ceil(c * len(v))
            return set(sorted(v, key=lambda x: (key(x), x))[:k])
        if method == "G0":
            return {i: (set(v), 1.0) for i, v in noms_Y.items()}
        if method == "SCORE":
            k = math.ceil(c * cfg.K)
            return {i: (set(v[:k]), 1.0) for i, v in noms_Y.items()}
        if method in ("VOL", "LIQ"):
            arr = self.der.vol20 if method == "VOL" else self.der.adv
            cal = [arr[i, self.der.k[x]] for i in range(lo_1, hi_1 + 1) for x in self.noms.get(i, ())]
            thr = q(cal, c if method == "VOL" else 1 - c)
            for i, v in noms_Y.items():
                vals = {x: arr[i, self.der.k[x]] for x in v}
                if fixed:   # lowest volatility / highest liquidity first; a missing value is kept first, as under the threshold rule
                    sgn = 1.0 if method == "VOL" else -1.0
                    out[i] = (top_k(v, lambda x: sgn * vals[x] if np.isfinite(vals[x]) else -np.inf), 1.0)
                    continue
                if method == "VOL":
                    out[i] = ({x for x in v if not (np.isfinite(vals[x]) and vals[x] > thr)}, 1.0)
                else:
                    out[i] = ({x for x in v if not (np.isfinite(vals[x]) and vals[x] < thr)}, 1.0)
            return out
        if method == "CONF":
            rows = self.rows_for(self.noms, lo_1, hi_1)
            ok, yv = self.labels(rows, "pos", lo_Y)
            if ok.sum() < 10:
                return {i: (set(), 1.0) for i in noms_Y}
            iso = _isotonic(self.rank[rows][ok], yv[ok])
            thr = q(iso.predict(self.rank[rows]), 1 - c)
            for i, v in noms_Y.items():
                rr = [self.fr.row[(i, x)] for x in v]
                p = iso.predict(self.rank[rr])
                out[i] = ({x for x, pp in zip(v, p) if pp >= thr}, 1.0)
            return out
        # learned gates on the top-K_tr population (NET-U: all of C_t)
        fam, fset = method.split("(")[0], "(" + method.split("(", 1)[1]
        fset = fset.strip("()")
        fset = "-Z" if fset == "-Z" else fset
        pop = self.cand if fam == "NET-U" else self.ktr
        lo_fit = self.yb[cfg.base_deploy_start][0]
        hi_fit = min(self.yb[Y - 2][1], lo_1 - 2 * H - 2) if (Y - 2) in self.yb else lo_1 - 2 * H - 2
        rows_fit = self.rows_for(pop, lo_fit, hi_fit)
        target = "o1" if fam in ("LOSS", "LOSS-LR") else "rho"
        ok, yv = self.labels(rows_fit, target, lo_1)
        rows_fit, yv = rows_fit[ok], yv[ok]
        if len(rows_fit) < 50 or (target == "o1" and len(np.unique(yv)) < 2):
            return {i: (set(), 1.0) for i in noms_Y}
        Xf = self.design(rows_fit, fset)
        kind = {"LOSS": "lgbm", "NET-K": "lgbm", "NET-U": "lgbm", "LOSS-LR": "logit"}[fam]
        obj = "binary" if fam == "LOSS" else "regression"
        pop_cal = self.cand if fam == "NET-U" else self.noms
        rows_cal = self.rows_for(pop_cal, lo_1, hi_1)
        pop_dep = self.cand if fam == "NET-U" else self.noms
        rows_dep = self.rows_for(pop_dep, lo_Y, hi_Y)
        both = np.r_[rows_cal, rows_dep]
        pred = _fit_predict(kind, Xf, yv, self.design(both, fset), conf, self.seed, cfg.lgbm_threads, obj)
        p_cal, p_dep = pred[:len(rows_cal)], pred[len(rows_cal):]
        score = {(int(self.fr.day[r]), self.fr.code[r]): float(p) for r, p in zip(rows_dep, p_dep)}
        if fam in ("LOSS", "LOSS-LR"):
            thr = q(p_cal, c)
            for i, v in noms_Y.items():
                if fixed:
                    out[i] = (top_k(v, lambda x: score.get((i, x), np.inf)), 1.0)
                    continue
                out[i] = ({x for x in v if score.get((i, x), np.inf) <= thr}, 1.0)
            return out
        if fam == "NET-K":
            thr = q(p_cal, 1 - c)
            for i, v in noms_Y.items():
                if fixed:
                    out[i] = (top_k(v, lambda x: -score.get((i, x), -np.inf)), 1.0)
                    continue
                out[i] = ({x for x in v if score.get((i, x), -np.inf) >= thr}, 1.0)
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

"""Learners and search spaces of the pilot (PLAN 4.2, 6.1, 6.3).

The search spaces below are fixed in this file before the first trial (PLAN 6.3 item 2) and are hashed
into every run manifest.  Every learned method draws the same number of configurations (cfg.n_configs,
a PILOT-REDUCTION of T = 30) from its space with the same procedure.  Minimum-leaf sizes are frozen as a
FRACTION of the training rows (PLAN 4.3, M-S11); every other hyper-parameter at its absolute value.
No early stopping: the number of boosting rounds is a hyper-parameter.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import warnings

import numpy as np
import pandas as pd

LGBM_SPACE = {"num_leaves": [15, 31, 63], "learning_rate": [0.03, 0.05, 0.1], "n_estimators": [100, 200, 400],
              "min_child_frac": [0.0005, 0.002, 0.01], "feature_fraction": [0.5, 0.8], "lambda_l2": [0.0, 1.0, 10.0]}
LINEAR_SPACE = {"model": ["ridge"] * 5 + ["enet"] * 3,
                "alpha": [1.0, 10.0, 100.0, 1000.0, 10000.0, 1e-5, 1e-4, 1e-3]}      # paired by position
LOGIT_SPACE = {"C": [0.001, 0.01, 0.1, 1.0, 10.0]}
TREND_GRID = [{"L": L, "thr": t} for L in (20, 60, 120) for t in (-0.05, 0.0, 0.05)]
PERF_GRID = [{"halflife": h, "thr": t} for h in (10, 20, 60) for t in (0.0, 0.02, 0.05)]
VT_GRID = [{"window": 60}]                 # sigma* is set by the coverage rule (PLAN 6.1), not searched


def spaces_hash() -> str:
    blob = json.dumps({"lgbm": LGBM_SPACE, "linear": LINEAR_SPACE, "logit": LOGIT_SPACE, "trend": TREND_GRID,
                       "perf": PERF_GRID, "vt": VT_GRID}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def draw_configs(kind: str, n: int, seed: int = 20261115) -> list[dict]:
    """n configurations of a method kind; random search without replacement over the grid (same seed and
    procedure for every method of a kind)."""
    rng = np.random.default_rng(seed)
    if kind == "lgbm":
        keys = list(LGBM_SPACE)
        grid = [dict(zip(keys, v)) for v in itertools.product(*[LGBM_SPACE[k] for k in keys])]
    elif kind == "linear":
        grid = [{"model": m, "alpha": a} for m, a in zip(LINEAR_SPACE["model"], LINEAR_SPACE["alpha"])]
    elif kind == "logit":
        grid = [{"C": c} for c in LOGIT_SPACE["C"]]
    elif kind == "trend":
        grid = list(TREND_GRID)
    elif kind == "perf":
        grid = list(PERF_GRID)
    elif kind == "vt":
        grid = list(VT_GRID)
    else:
        raise ValueError(kind)
    if n >= len(grid):
        return grid
    pick = rng.choice(len(grid), size=n, replace=False)
    return [grid[k] for k in sorted(pick)]


# ------------------------------------------------------------------ preprocessing
def rank_within_days(day: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Cross-sectional rank transform per decision day to (0, 1] (pct ranks, average ties); NaN kept.
    PLAN 4.1: one preprocessing choice fixed before training (rank transform; it makes winsorising moot)."""
    out = np.full(X.shape, np.nan, dtype=np.float32)
    order = np.argsort(day, kind="stable")
    d = day[order]
    bounds = np.flatnonzero(np.r_[True, d[1:] != d[:-1], True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        rows = order[a:b]
        blk = pd.DataFrame(X[rows].astype(np.float64)).rank(pct=True, method="average")
        out[rows] = blk.to_numpy(dtype=np.float32)
    return out


class LinearPrep:
    """Median imputation (training medians) plus missing indicators for columns with missing values in
    training (PLAN 4.1: 'median-imputed plus a missing indicator for the linear model')."""

    def fit(self, X):
        self.med = np.nanmedian(X, axis=0)
        self.med = np.where(np.isfinite(self.med), self.med, 0.5)
        self.ind = np.flatnonzero(np.isnan(X).any(axis=0))
        return self

    def transform(self, X):
        Z = np.where(np.isnan(X), self.med, X)
        if len(self.ind):
            Z = np.hstack([Z, np.isnan(X[:, self.ind]).astype(np.float32)])
        return Z.astype(np.float64)


# ------------------------------------------------------------------ learners
def fit_lgbm(X, y, conf: dict, seed: int, objective: str, threads: int):
    import lightgbm as lgb
    n = len(y)
    params = dict(objective=objective, num_leaves=conf["num_leaves"], learning_rate=conf["learning_rate"],
                  n_estimators=conf["n_estimators"], min_child_samples=max(5, int(round(conf["min_child_frac"] * n))),
                  colsample_bytree=conf["feature_fraction"], subsample=0.8, subsample_freq=1,
                  reg_lambda=conf["lambda_l2"], random_state=seed, n_jobs=threads, verbose=-1,
                  deterministic=True, force_row_wise=True)
    model = lgb.LGBMClassifier(**params) if objective == "binary" else lgb.LGBMRegressor(**params)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(X, y)
    return model


def predict_lgbm(model, X):
    if hasattr(model, "predict_proba") and getattr(model, "objective", None) == "binary":
        return model.predict_proba(X)[:, 1]
    return model.predict(X)


def fit_linear(X, y, conf: dict):
    from sklearn.linear_model import ElasticNet, Ridge
    prep = LinearPrep().fit(X)
    Z = prep.transform(X)
    if conf["model"] == "ridge":
        m = Ridge(alpha=conf["alpha"])
    else:
        m = ElasticNet(alpha=conf["alpha"], l1_ratio=0.5, max_iter=2000)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m.fit(Z, y)
    return (prep, m)


def predict_linear(model, X):
    prep, m = model
    return m.predict(prep.transform(X))


def fit_logit(X, y, conf: dict):
    from sklearn.linear_model import LogisticRegression
    prep = LinearPrep().fit(X)
    m = LogisticRegression(C=conf["C"], max_iter=300)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m.fit(prep.transform(X), y)
    return (prep, m)


def predict_logit(model, X):
    prep, m = model
    return m.predict_proba(prep.transform(X))[:, 1]


def spearman_by_day(day: np.ndarray, a: np.ndarray, b: np.ndarray) -> pd.Series:
    """Spearman correlation of a and b within each day (rows with both finite; days with < 3 rows: NaN)."""
    df = pd.DataFrame({"d": day, "a": a, "b": b}).dropna()
    if not len(df):
        return pd.Series(dtype=float)
    g = df.groupby("d")
    ra = g["a"].rank().to_numpy()
    rb = g["b"].rank().to_numpy()
    t = pd.DataFrame({"d": df["d"].to_numpy(), "a": ra, "b": rb, "ab": ra * rb, "aa": ra * ra, "bb": rb * rb})
    s = t.groupby("d").agg(n=("a", "size"), a=("a", "sum"), b=("b", "sum"), ab=("ab", "sum"), aa=("aa", "sum"),
                           bb=("bb", "sum"))
    n = s["n"].astype(float)
    cov = s["ab"] - s["a"] * s["b"] / n
    va = s["aa"] - s["a"] ** 2 / n
    vb = s["bb"] - s["b"] ** 2 / n
    with np.errstate(all="ignore"):
        r = cov / np.sqrt(va * vb)
    r[(n < 3) | ~np.isfinite(r)] = np.nan
    r.index = r.index.astype(int)
    return r

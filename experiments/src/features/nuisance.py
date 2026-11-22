"""Capacity-matched nuisance features and cross-sectional preprocessing.

permute_within_day (PLAN 7.3 (c), null worlds W-Zperm-H / W-Zperm-O of 10.2):
the Z columns are permuted across the population within each day, so that the
number of features, their marginal distribution on each day and their
missingness are those of Z, with no stock-specific content. For Z_O the
permutation is drawn separately for each class (all columns of a class move
together), which preserves the number of events per day and class.

Both functions use same-day rows only; neither reads an outcome.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def permute_within_day(panel: pd.DataFrame, blocks: dict[str, list[str]], seed: int,
                       population: pd.Series | None = None) -> pd.DataFrame:
    """Return a copy of `panel` (MultiIndex (day, code)) in which, for every
    day and every block of columns, the rows of the block are permuted among
    the population of that day.

    blocks: name -> columns that move together (Z_H: one block with all
    columns; Z_O: one block per class). population: boolean Series on the
    panel index (e.g. the nominated-training population); rows outside it are
    left unchanged and take no part. The permutation of (day, block) is drawn
    from a generator seeded with (seed, block number, day ordinal), with rows
    taken in code order, so the result does not depend on the row order of the
    input or on which other days are in the panel.
    """
    if not isinstance(panel.index, pd.MultiIndex) or panel.index.nlevels != 2:
        raise ValueError("panel must be indexed by (day, code)")
    out = panel.copy()
    days = panel.index.get_level_values(0)
    codes = panel.index.get_level_values(1)
    pop = np.ones(len(panel), dtype=bool) if population is None else population.reindex(panel.index).fillna(False).values
    code_rank = pd.factorize(codes, sort=True)[0]
    day_vals = pd.DatetimeIndex(days).values
    order = np.lexsort((code_rank, day_vals))
    day_sorted = day_vals[order]
    bounds = np.r_[0, np.nonzero(day_sorted[1:] != day_sorted[:-1])[0] + 1, len(order)]
    for bi, (bname, cols) in enumerate(sorted(blocks.items())):
        vals = panel[cols].values
        new = vals.copy()
        for a, b in zip(bounds[:-1], bounds[1:]):
            rows = order[a:b]
            rows = rows[pop[rows]]
            if len(rows) < 2:
                continue
            ordinal = int(pd.Timestamp(day_sorted[a]).toordinal())
            rng = np.random.default_rng([int(seed), bi, ordinal])
            new[rows] = vals[rows[rng.permutation(len(rows))]]
        out[cols] = new
    return out


def zo_blocks(columns) -> dict[str, list[str]]:
    """One block per Z_O class (lhb, blk, ins) from column names zo_<class>_..."""
    blocks: dict[str, list[str]] = {}
    for c in columns:
        if c.startswith("zo_"):
            blocks.setdefault(c.split("_")[1], []).append(c)
    return blocks


def cs_preprocess(panel: pd.DataFrame, method: str = "rank", lower: float = 0.01, upper: float = 0.99) -> pd.DataFrame:
    """Per-day cross-sectional preprocessing of PLAN 4.1: winsorise at the
    1st / 99th percentile of the day, then rank-transform to (0, 1) ('rank')
    or z-score ('zscore'). NaN stays NaN. Each day uses its own rows only."""
    def one_day(g: pd.DataFrame) -> pd.DataFrame:
        lo, hi = g.quantile(lower), g.quantile(upper)
        w = g.clip(lower=lo, upper=hi, axis=1)
        if method == "rank":
            return w.rank(pct=True)
        if method == "zscore":
            return (w - w.mean()) / w.std(ddof=1)
        raise ValueError(method)
    return panel.groupby(level=0, group_keys=False).apply(one_day)

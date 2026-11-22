"""Configuration of the exploratory pilot round (PLAN v0.8 section 13A).

Every value is taken from PLAN v0.8 (section given per field) or is a declared pilot reduction
(marked PILOT-REDUCTION; the same reduction applies to every method).  The data cut-off has NO
default: a configuration is only valid with data_cutoff given explicitly (2021-12-31 for the pilot).
Nothing here was chosen after looking at any pilot outcome.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date

from engine import datacut as dc


@dataclass(frozen=True)
class PilotConfig:
    data_cutoff: str                                   # REQUIRED (C-8); the pilot: "2021-12-31"
    name: str = "pilot"
    universe_csv: str = "experiments/data/universe_pilot_v1.csv"
    universe_sha256: str = "10abefede7b7c6facebf3f3f9adf71e757f3abd02860f037ee30855bade28fdd"   # PLAN 13A
    codes_subset: tuple = ()                           # smoke test only: restrict the list (documented)
    # ---- universe U-LIQ-P (PLAN 13A, U66) and portfolio (PLAN 3.3, 3.7, 6.1)
    N_U: int = 300
    K: int = 30
    H: int = 5
    c: float = 0.5                                     # target coverage (U-placeholder, PLAN 6.1)
    # "threshold": PLAN 6.1 (one threshold per year from Y-1).  "fixed_count": pilot revision of 2026-11-16,
    # made AFTER seeing the first pilot run: LOSS / LOSS-LR / NET-K / VOL / LIQ submit the ceil(c * |nominations|)
    # best-ranked nominations every day.  CONF and NET-U keep the threshold rule (under a fixed count CONF
    # coincides with SCORE, because the isotonic map is monotone in the base rank).
    gate_rule: str = "threshold"
    K_tr_mult: int = 3                                 # K_tr = 3K (PLAN 4.3)
    W0: float = 1.0e7
    # ---- schedule (PLAN 4.3 / 13A: base tuning 2011-2012, gate tuning 2015-2016, evaluation 2017-2021)
    base_tune_years: tuple = (2011, 2012)
    base_deploy_start: int = 2013
    gate_tune_years: tuple = (2015, 2016)
    eval_years: tuple = (2017, 2018, 2019, 2020, 2021)
    first_feature_year: int = 2009                     # first year with complete 250-day windows (PLAN 2.3)
    # ---- methods (PLAN 6.1 round 1; 7.1 cells)
    bases: tuple = ("lgbm", "ridge")                   # PLAN 4.2: Model 1 and Model 2
    methods: tuple = ("G0", "SCORE", "CONF", "LOSS-LR(-Z)", "LOSS(-Z)", "LOSS(+Z_H)", "LOSS(+Z_O)",
                      "LOSS(+Z_H+Z_O)", "LOSS(+perm Z_H)", "LOSS(+perm Z_O)", "NET-K(-Z)", "NET-K(+Z_H)",
                      "NET-K(+Z_O)", "NET-U(-Z)", "VOL", "LIQ", "TREND", "PERF", "VT")
    e_const_dev_for: tuple = ("SCORE", "CONF", "LOSS(-Z)", "LOSS(+Z_H)", "LOSS(+Z_O)")
    rnd_for: tuple = ("CONF", "LOSS(-Z)", "LOSS(+Z_H)", "LOSS(+Z_O)")
    # ---- budget (PLAN 6.3: T = 30 configurations, seeds 0..4) -- PILOT-REDUCTION, same for every method
    n_configs: int = 4                                 # PILOT-REDUCTION of T = 30
    seeds: tuple = (0, 1, 2)                           # PILOT-REDUCTION of 5 seeds (>= 3 required)
    rnd_reps: int = 5                                  # PILOT-REDUCTION of 200 (PLAN 6.1 RND)
    bootstrap_B: int = 2000                            # PILOT-REDUCTION of 10,000 (PLAN 10)
    block_mean: int = 24                               # 4 (H + 1), PLAN 10
    delta_mon: float = 0.10                            # Theorem 1 delta (PLAN 9.2)
    # ---- compute
    n_jobs: int = 8
    lgbm_threads: int = 8
    # ---- outputs
    out_dir: str = "experiments/results/pilot/run"
    panel_dir: str = "experiments/data/derived/feature_panel_pilot"
    decision_cutoff: str = ""                          # last decision day of the feature panel ("" = data cut-off)

    def cut(self) -> date:
        return dc.require_cutoff(self.data_cutoff)

    @property
    def K_tr(self) -> int:
        return self.K_tr_mult * self.K

    def to_json(self) -> dict:
        return asdict(self)

    def hash(self) -> str:
        return hashlib.sha256(json.dumps(self.to_json(), sort_keys=True).encode()).hexdigest()


# Pilot reductions and simplifications are written into every run manifest (PLAN 13A: "any reduction of
# budget or seeds applies to every method and is logged").
REDUCTIONS = {
    "n_configs": "T reduced from 30 to n_configs random-search configurations for every learned method "
                 "(base LightGBM, base ridge, LOSS, LOSS-LR, NET-K, NET-U); grid methods (TREND, PERF, VT) "
                 "searched over at most n_configs grid points",
    "seeds": "seeds {0,1,2} instead of {0,...,4} for every stochastic component",
    "rnd_reps": "RND Monte-Carlo repetitions reduced from 200",
    "bootstrap_B": "bootstrap resamples reduced from 10,000",
}


def smoke_config(data_cutoff: str, codes: tuple, out_dir: str, panel_dir: str) -> PilotConfig:
    """Smoke slice: small list, short schedule, minimal models / bootstrap (pipeline check only)."""
    # the slice ends at the data cut-off, so that the end-of-window rule and the cut-off are exercised:
    # base fit 2015-2016, base validation 2017, base out-of-sample from 2018, gate fit 2018, gate calibration
    # 2019, gate tuning year 2020, evaluation year 2021
    return PilotConfig(data_cutoff=data_cutoff, name="smoke", codes_subset=tuple(codes),
                       base_tune_years=(2017,), base_deploy_start=2018, gate_tune_years=(2020,), eval_years=(2021,),
                       first_feature_year=2015, n_configs=2, seeds=(0, 1, 2), rnd_reps=2, bootstrap_B=200,
                       out_dir=out_dir, panel_dir=panel_dir, n_jobs=8, lgbm_threads=8)

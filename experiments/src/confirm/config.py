"""Configuration of the confirmatory code base (PLAN v0.9.3 amendment, DRAFT; development period only).

Copied from `pilot/config.py` (2026-11-17) and extended for the amendment:
  * fixed-count gate rule is the default (A2.1);
  * gate training window: "y1" = through Y-1 (A2.1 primary) or "y2" = through Y-2 (v0.8 / pilot;
    sensitivity);
  * gate tuning criterion: "V" = pooled V (A2.2) or "theta_sel" (v0.8 6.3 item 3; pilot);
  * budget T = 30 trials and five seeds as configuration values (A2.2, A2.3, A7);
  * new policies BASE-V, NET-U15(-Z), BASEV-RERANK and the Z_O* feature set (A4.1, A7,
    reviews/plan_review_5.md row 2).
The data cut-off has NO default.  Nothing here was chosen after looking at any development outcome of
the new policies (none had been computed when this file was written).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date

from engine import datacut as dc

# Methods of the pilot (kept for the reproduction / pilot-compatibility mode)
PILOT_METHODS = ("G0", "SCORE", "CONF", "LOSS-LR(-Z)", "LOSS(-Z)", "LOSS(+Z_H)", "LOSS(+Z_O)",
                 "LOSS(+Z_H+Z_O)", "LOSS(+perm Z_H)", "LOSS(+perm Z_O)", "NET-K(-Z)", "NET-K(+Z_H)",
                 "NET-K(+Z_O)", "NET-U(-Z)", "VOL", "LIQ", "TREND", "PERF", "VT")

# Methods of the confirmatory configuration (amendment v0.9.3).  Primary family per base:
#   P1 LOSS(-Z) vs SCORE; P2 LOSS(+Z_H) vs LOSS(-Z); P3 LOSS(+Z_O*) vs LOSS(-Z); P4 NET-K(-Z) vs SCORE;
#   P5 LOSS(-Z) vs BASE-V; P6 NET-K(-Z) vs BASE-V.
# Secondary (A4.3 item 2, A4.3 item 6, plan_review_5 row 2): LOSS(+Z_O) (INS included), LOSS(+Z_H+Z_O*),
#   permuted-Z controls, NET-K(+Z_x), NET-U15(-Z), BASEV-RERANK, VOL, LIQ, CONF, LOSS-LR(-Z), NET-U(-Z)
#   (threshold, unchanged), TREND, PERF, VT.
# Round 2 (2026-11-17, PI rulings): the tuned permuted-Z gates are replaced by the A4.3 item 6 follow-up
# (perm_draws permuted and noise draws per seed, refitted at the configuration chosen for the real group; not
# listed here, generated from perm_groups); the -thr secondary policies (v0.8 threshold rule) are added.
CONFIRM_METHODS = ("G0", "SCORE", "CONF", "LOSS-LR(-Z)", "LOSS(-Z)", "LOSS(+Z_H)", "LOSS(+Z_O*)", "LOSS(+Z_O)",
                   "LOSS(+Z_H+Z_O*)", "NET-K(-Z)", "NET-K(+Z_H)",
                   "NET-K(+Z_O*)", "NET-U(-Z)", "NET-U15(-Z)", "BASE-V", "BASEV-RERANK", "VOL", "LIQ",
                   "LOSS(-Z)-thr", "LOSS(+Z_H)-thr", "LOSS(+Z_O)-thr",
                   "TREND", "PERF", "VT")

PRIMARY_CONTRASTS = (("P1", "LOSS(-Z)", "SCORE"), ("P2", "LOSS(+Z_H)", "LOSS(-Z)"),
                     ("P3", "LOSS(+Z_O*)", "LOSS(-Z)"), ("P4", "NET-K(-Z)", "SCORE"),
                     ("P5", "LOSS(-Z)", "BASE-V"), ("P6", "NET-K(-Z)", "BASE-V"))
SECONDARY_CONTRASTS = (("S-BASEV", "BASE-V", "SCORE"), ("S-NETU15", "NET-U15(-Z)", "BASE-V"),
                       ("S-NETU15-SCORE", "NET-U15(-Z)", "SCORE"), ("S-RERANK", "BASEV-RERANK", "SCORE"),
                       ("S-OBJ", "NET-K(-Z)", "LOSS(-Z)"), ("S-HO", "LOSS(+Z_H+Z_O*)", "LOSS(-Z)"),
                       ("S-INS", "LOSS(+Z_O)", "LOSS(-Z)"))

# Policies whose pool is the whole candidate set C_t (they make their own nominations)
POOL_METHODS = ("NET-U(-Z)", "NET-U15(-Z)", "BASE-V")


@dataclass(frozen=True)
class ConfirmConfig:
    data_cutoff: str                                   # REQUIRED; development runs: "2021-12-31"
    name: str = "confirm"
    universe_csv: str = "experiments/data/universe_pilot_v1.csv"
    universe_sha256: str = "10abefede7b7c6facebf3f3f9adf71e757f3abd02860f037ee30855bade28fdd"   # PLAN 13A, A8
    codes_subset: tuple = ()                           # smoke test only
    # ---- universe U-LIQ-P and portfolio (A8: unchanged)
    N_U: int = 300
    K: int = 30
    H: int = 5
    c: float = 0.5
    gate_rule: str = "fixed_count"                     # A2.1 (threshold kept for -thr / pilot mode)
    gate_window: str = "y1"                            # A2.1 primary "y1"; sensitivity "y2"
    gate_criterion: str = "V"                          # A2.2 "V"; pilot / threshold policies "theta_sel"
    failed_score: str = "exclude"                      # non-finite score: name not eligible that day
    K_tr_mult: int = 3
    W0: float = 1.0e7
    # ---- schedule (development period; PLAN 4.3 / 13A)
    base_tune_years: tuple = (2011, 2012)
    base_deploy_start: int = 2013
    gate_tune_years: tuple = (2015, 2016)
    eval_years: tuple = (2017, 2018, 2019, 2020, 2021)
    first_feature_year: int = 2009
    # ---- methods
    bases: tuple = ("lgbm", "ridge")
    methods: tuple = CONFIRM_METHODS
    netu15_base_rank_input: bool = False               # round 2, Q5: NET-U15 is a pure end-to-end model
    base_features: str = "-Z"                          # round 2: base, BASE-V, NET-U15 on the -Z set (B0+R, A7); the
                                                       # pilot's base used ALL columns incl. Z_H and Z_O ("all" = pilot)
    perm_groups: tuple = ("Z_H", "Z_O*")               # A4.3 item 6: groups of the permutation follow-up (LOSS gate)
    perm_draws: int = 20                               # A4.3 item 6 / O6: draws per seed (permuted and noise each)
    criterion_resolved_only: bool = True               # round 2, D4: tuning criteria count orders resolved before v+1
    e_const_dev_for: tuple = ("SCORE", "CONF", "LOSS(-Z)", "LOSS(+Z_H)", "LOSS(+Z_O*)")
    rnd_for: tuple = ("CONF", "LOSS(-Z)", "LOSS(+Z_H)", "LOSS(+Z_O*)")
    # ---- budget (A2.2, A2.3, A7: T = 30, five seeds)
    n_configs: int = 30
    seeds: tuple = (0, 1, 2, 3, 4)
    rnd_reps: int = 200
    bootstrap_B: int = 10000
    block_mean: int = 24
    delta_mon: float = 0.10
    # ---- compute
    n_jobs: int = 5                                    # parallel workers; changes no number (only internal lot ids)
    lgbm_threads: int = 2                              # round 2, Q6 / D6: FIXED; part of the configuration hash
    blas_threads: int = 2                              # round 2, Q6 / D6: FIXED; part of the configuration hash
    base_workers: int = 2                              # parallel base / NET-U15 fits (memory: one full-size training
                                                       # matrix per worker); changes no number
    # ---- outputs
    out_dir: str = "experiments/results/confirm/run"
    panel_dir: str = "experiments/data/derived/feature_panel"
    decision_cutoff: str = ""

    def cut(self) -> date:
        return dc.require_cutoff(self.data_cutoff)

    @property
    def K_tr(self) -> int:
        return self.K_tr_mult * self.K

    @property
    def target_count(self) -> int:
        """ceil(c K) = 15: the daily count of policies that pick from the whole candidate set."""
        import math
        return math.ceil(self.c * self.K)

    def to_json(self) -> dict:
        return asdict(self)

    def hash(self) -> str:
        return hashlib.sha256(json.dumps(self.to_json(), sort_keys=True).encode()).hexdigest()

    def hash_without_compute(self) -> str:
        """Hash of everything that can change a number (the number of workers and paths excluded; the thread
        counts are INCLUDED since round 2, D6); keys the checkpoints used by --resume."""
        d = self.to_json()
        for k in ("n_jobs", "base_workers", "out_dir"):
            d.pop(k, None)
        return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()

    def tuning_spec(self) -> dict:
        """Everything a hyperparameter search depends on except the data cut-off (D1): a hold-out run with a
        later cut-off must present the same spec as the archive it loads."""
        d = self.to_json()
        for k in ("data_cutoff", "out_dir", "panel_dir", "n_jobs", "base_workers", "rnd_reps", "bootstrap_B", "delta_mon",
                  "name"):
            d.pop(k, None)
        return d

    def tuning_spec_hash(self) -> str:
        return hashlib.sha256(json.dumps(self.tuning_spec(), sort_keys=True).encode()).hexdigest()


PilotConfig = ConfirmConfig      # name used by the copied modules

REDUCTIONS = {
    "note": "a run is reduced if n_configs < 30, fewer than five seeds, rnd_reps < 200 or bootstrap_B < 10,000; "
            "the values actually used are in the configuration of the run manifest and apply to every method",
}


def smoke_config(data_cutoff: str, codes: tuple, out_dir: str, panel_dir: str) -> ConfirmConfig:
    """Smoke slice (as in the pilot): base fit 2015-2016, base validation 2017, base out-of-sample from 2018,
    gate tuning year 2020, evaluation year 2021.  Budget and seeds are set by the caller (CLI)."""
    return ConfirmConfig(data_cutoff=data_cutoff, name="smoke", codes_subset=tuple(codes),
                         base_tune_years=(2017,), base_deploy_start=2018, gate_tune_years=(2020,), eval_years=(2021,),
                         first_feature_year=2015, n_configs=2, seeds=(0, 1, 2), rnd_reps=2, bootstrap_B=200, perm_draws=2,
                         out_dir=out_dir, panel_dir=panel_dir)

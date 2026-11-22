"""Pre-freeze point-in-time audit: run the pilot pipeline (stages 1-8, no backtests) on one raw tree and
record, without saving any performance number, the objects whose dependence on later data is tested.

The pilot code is imported unchanged; recording is done by wrapping (in this process only) the functions
the pipeline already calls:
  D.universe_and_candidates   monthly membership and candidate sets
  S.base_scores               base scores per (base, seed); hash of the tuning record and the chosen index
  S._fit_predict, S._isotonic SHA-256 of every training set (X, y) a learner is fitted on, keyed by context
  S.GateContext.gate_year     every gate decision {day: submitted set} per (base, seed, method, config, year)
  ThreadPoolExecutor.map      the chosen gate configuration per (base, method) and a hash of the criterion
  frames                      per-day SHA-256 of the rank-transformed feature rows (GateContext.fr)
  standard orders             per (day, code): exit day and a SHA-256 of the record (no value is stored)

Configuration (declared before running; data cut-off 2021-12-31, smoke list of 100 names):
  smoke_config with first_feature_year 2014, base tuning year 2016, base deployment from 2017, gate tuning
  year 2019, evaluation years 2020-2021, gate_rule fixed_count, seeds (0, 1), n_configs 2, methods
  G0 SCORE CONF VOL LIQ LOSS-LR(-Z) LOSS(-Z) LOSS(+Z_H) LOSS(+Z_O) NET-K(-Z) NET-U(-Z).
  The schedule is shifted one year earlier than the pilot's smoke schedule so that a whole gate
  deployment year (2019, the gate tuning year) and the gate fits for 2019-2021 lie at or before the
  in-development cut-off 2019-12-31 whose later data the test perturbs.

    experiments/.venv/Scripts/python.exe -X utf8 experiments/src/prefreeze_audit/run_pit.py \
        --raw-root <tree> --out <dir> --codes-file <smoke_codes.txt> --jobs 4 --threads 1
"""
from __future__ import annotations

import argparse
import os
import sys

_a = sys.argv
_thr = _a[_a.index("--threads") + 1] if "--threads" in _a else "1"
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, _thr)

import concurrent.futures as cf      # noqa: E402
import hashlib                        # noqa: E402
import json                           # noqa: E402
import pickle                         # noqa: E402
import threading                      # noqa: E402
import time                           # noqa: E402
from dataclasses import replace       # noqa: E402
from pathlib import Path              # noqa: E402

HERE = Path(__file__).resolve().parent
SRC = HERE.parent
sys.path.insert(0, str(SRC))

import numpy as np                    # noqa: E402

from pilot import data as D           # noqa: E402
from pilot import run_pilot as RP     # noqa: E402
from pilot import strategy as S       # noqa: E402
from pilot.config import smoke_config  # noqa: E402

METHODS = ("G0", "SCORE", "CONF", "VOL", "LIQ", "LOSS-LR(-Z)", "LOSS(-Z)", "LOSS(+Z_H)", "LOSS(+Z_O)",
           "NET-K(-Z)", "NET-U(-Z)")

REC: dict = {"fits": [], "gates": {}, "bases": {}, "ctx_order": [], "gate_tuning": {}}
_TL = threading.local()
_LOCK = threading.Lock()


def _h(*arrs) -> str:
    h = hashlib.sha256()
    for a in arrs:
        a = np.ascontiguousarray(a)
        h.update(str(a.dtype).encode() + str(a.shape).encode())
        h.update(a.tobytes())
    return h.hexdigest()


def _ck(conf) -> str:
    return json.dumps(conf, sort_keys=True, default=str)


def install(cfg):
    orig_uc = D.universe_and_candidates

    def uc(*a, **k):
        by_month, cand, rep = orig_uc(*a, **k)
        REC["by_month"] = {k_: list(v) for k_, v in by_month.items()}
        REC["cand"] = {int(i): list(v) for i, v in cand.items()}
        return by_month, cand, rep
    D.universe_and_candidates = uc

    orig_fp = S._fit_predict

    def fp(kind, Xtr, ytr, Xte, conf, seed, threads, objective="regression"):
        ctx = getattr(_TL, "ctx", ("?",))
        with _LOCK:
            seq = getattr(_TL, "seq", 0)
            _TL.seq = seq + 1
        rec = {"ctx": ctx, "seq": seq, "kind": kind, "conf": _ck(conf), "seed": int(seed), "objective": objective,
               "n_train": int(len(ytr)), "train_hash": _h(Xtr, np.asarray(ytr, float))}
        with _LOCK:
            REC["fits"].append(rec)
        return orig_fp(kind, Xtr, ytr, Xte, conf, seed, threads, objective)
    S._fit_predict = fp

    orig_iso = S._isotonic

    def iso(x, y):
        ctx = getattr(_TL, "ctx", ("?",))
        with _LOCK:
            REC["fits"].append({"ctx": ctx, "seq": -1, "kind": "isotonic", "conf": "", "seed": -1, "objective": "",
                                "n_train": int(len(y)), "train_hash": _h(np.asarray(x, float), np.asarray(y, float))})
        return orig_iso(x, y)
    S._isotonic = iso

    orig_bs = S.base_scores

    def bs(fr, y, days, cfg_, base, seeds, log):
        _TL.ctx, _TL.seq = ("base", base), 0
        out = orig_bs(fr, y, days, cfg_, base, seeds, log)
        _TL.ctx = ("?",)
        tun = out[seeds[0]]["tuning"]
        REC["bases"][base] = {
            "chosen_index": int(out[seeds[0]]["chosen_index"]),
            "tuning_hash": hashlib.sha256(json.dumps([t["values"] for t in tun]).encode()).hexdigest(),
            "score": {int(s): np.asarray(out[s]["score"], np.float64).copy() for s in out},
            "rank": {int(s): np.asarray(out[s]["rank"], np.float64).copy() for s in out}}
        return out
    S.base_scores = bs

    orig_init = S.GateContext.__init__

    def ginit(self, *a, **k):
        orig_init(self, *a, **k)
        with _LOCK:
            n = len(REC["ctx_order"])
            b = cfg.bases[n // len(cfg.seeds)]
            self._audit_key = (b, int(self.seed))
            REC["ctx_order"].append(self._audit_key)
            if "frame" not in REC:
                REC["frame"] = {"day": self.fr.day.copy(), "code": self.fr.code.copy(), "cols": list(self.fr.cols),
                                "day_hash": _day_hashes(self.fr)}
                REC["days"] = [d.isoformat() for d in self.days]
                REC["std"] = {k_: (int(v["exit_i"]), bool(v["unresolved"]),
                                   hashlib.sha256(repr((v["filled"], v["rho"], v["o1"], v["exit_i"], v["unresolved"],
                                                        v["reason"])).encode()).hexdigest())
                              for k_, v in self.std.items()}
            REC.setdefault("noms", {})[self._audit_key] = {int(i): list(v) for i, v in self.noms.items()}
            REC.setdefault("ktr", {})[self._audit_key] = {int(i): list(v) for i, v in self.ktr.items()}
    S.GateContext.__init__ = ginit

    orig_gy = S.GateContext.gate_year

    def gy(self, method, conf, Y):
        prev = getattr(_TL, "ctx", ("?",))
        _TL.ctx = ("gate",) + tuple(self._audit_key) + (method, _ck(conf), int(Y))
        try:
            out = orig_gy(self, method, conf, Y)
        finally:
            _TL.ctx = prev
        with _LOCK:
            REC["gates"][_TL_key(self, method, conf, Y)] = {int(i): tuple(sorted(v[0])) for i, v in out.items()}
        return out
    S.GateContext.gate_year = gy

    class TPE(cf.ThreadPoolExecutor):
        def map(self, fn, *its, **kw):
            for r in super().map(fn, *its, **kw):
                b, m, tl, _out = r
                REC["gate_tuning"][(b, m)] = {
                    "chosen": int(tl["chosen"]), "configs": [_ck(c) for c in tl["configs"]],
                    "criterion_hash": hashlib.sha256(json.dumps(tl.get("criterion_mean_theta_sel"), default=str).encode()).hexdigest()}
                yield r
    cf.ThreadPoolExecutor = TPE


def _TL_key(ctx, method, conf, Y):
    return tuple(ctx._audit_key) + (method, _ck(conf), int(Y))


def _day_hashes(fr) -> dict:
    out = {}
    order = np.lexsort((fr.code.astype(str), fr.day))
    d = fr.day[order]
    bounds = np.flatnonzero(np.r_[True, d[1:] != d[:-1], True])
    for a, b in zip(bounds[:-1], bounds[1:]):
        rows = order[a:b]
        out[int(d[a])] = _h(np.array([str(c) for c in fr.code[rows]]).astype("U12"), fr.X[rows])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--codes-file", required=True)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--threads", type=int, default=1)
    a = ap.parse_args()
    codes = tuple(l.strip() for l in open(a.codes_file, encoding="utf-8") if l.strip())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = smoke_config("2021-12-31", codes, str(out), str(out / "feature_panel"))
    cfg = replace(cfg, first_feature_year=2014, base_tune_years=(2016,), base_deploy_start=2017,
                  gate_tune_years=(2019,), eval_years=(2020, 2021), gate_rule="fixed_count", seeds=(0, 1),
                  n_configs=2, methods=METHODS, n_jobs=a.jobs, lgbm_threads=a.threads)
    install(cfg)
    log = RP.Log(out / "logs" / "run.log")
    log(f"PIT audit run; raw root {a.raw_root}; data cut-off {cfg.data_cutoff}; config hash {cfg.hash()}")
    t0 = time.time()
    res = RP.run(cfg, log, out, raw=Path(a.raw_root), stop_after="8")
    REC["config"] = cfg.to_json()
    REC["seconds"] = round(time.time() - t0, 1)
    REC["res_counts"] = {k: res.get(k) for k in ("readiness", "universe", "features", "standard_orders")}
    with open(out / "pit_record.pkl", "wb") as fh:
        pickle.dump(REC, fh)
    log(f"record written ({len(REC['fits'])} fits, {len(REC['gates'])} gate-year decisions); {REC['seconds']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())

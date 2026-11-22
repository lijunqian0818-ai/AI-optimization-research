"""Phase D driver (REVISION_PROTOCOL.md): exploratory grid for the paired bootstrap-t rule.

python run_phaseD.py --scenario F1 --mode cov --n 1000 --procs 8 --out <dir> [--types stat circ]
Seeds: hold_seed = 10,000,000 + 100,000 * (10 * code + mode) + rep  (all in [10M, 20M)).
F2c: one fixed development history, dev_seed = 10,261,117.
"""
import os

for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import argparse
import json
import time
from multiprocessing import Pool

import numpy as np

CODE = {"S0": 1, "S1": 2, "S2": 3, "F1": 4, "F2": 5, "F2c": 6, "F3a": 7, "F3b": 8}
MODE = {"cov": 0, "truth": 1}
F2C_DEV_SEED = 10_261_117
LS = (10, 24, 48)
BANDS = (5, 10, 20)
B_BT = 999
B_OLD = 2000


def seeds_for(scen, mode, rep):
    hold = 10_000_000 + 100_000 * (10 * CODE[scen] + MODE[mode]) + rep
    assert 10_000_000 <= hold < 20_000_000
    dev = F2C_DEV_SEED if scen == "F2c" else hold
    return dev, hold


def get_series(scen, dev, hold):
    from pipeline import Params
    from pipeline2 import policy_level_series, run_history2, scenario_params2
    if scen in ("S0", "S1", "S2"):
        p = Params()
        N, S = policy_level_series(scen, hold, p.holdout_days)
    else:
        p = scenario_params2(scen)
        N, S = run_history2(p, dev, hold)
    return p, N, S


def one_rep(scen, mode, rep, types):
    from bootstrap_t import bt_rule
    from intervals import Contrast, simultaneous_intervals
    from pipeline2 import CONTRASTS2, POLICIES2, masks2
    dev, hold = seeds_for(scen, mode, rep)
    t0 = time.time()
    p, N, S = get_series(scen, dev, hold)
    t_gen = time.time() - t0
    Nbar, Sbar = N.mean(1), S.mean(1)
    masks = masks2(p)
    late = masks[2]
    row = {"rep": rep, "dev_seed": dev, "hold_seed": hold, "t_gen": t_gen}
    for g, nm in enumerate(POLICIES2):
        row[f"sumN_{nm}"] = float(Nbar[g].sum())
        row[f"sumS_{nm}"] = float(Sbar[g].sum())
        row[f"sumNlate_{nm}"] = float((Nbar[g] * late).sum())
        row[f"sumSlate_{nm}"] = float((Sbar[g] * late).sum())
    if mode == "truth":
        return row
    names = [c[0] for c in CONTRASTS2]
    configs = [(t, L) for t in types for L in LS]
    t1 = time.time()
    r = bt_rule(N, S, CONTRASTS2, masks, configs, list(BANDS), B_BT,
                rng_for=lambda ci: np.random.default_rng([hold, 600 + 10 * ("stat", "circ").index(configs[ci][0]) + LS.index(configs[ci][1])]))
    row["t_bt"] = time.time() - t1
    for j, n in enumerate(names):
        row[f"th_{n}"] = r["theta"][j]
        for b in BANDS:
            row[f"hse{b}_{n}"] = r["se"][b][j]
    for (typ, L, b), q in r["q"].items():
        row[f"q_{typ}{L}_b{b}"] = q
        row[f"app_{typ}{L}_b{b}"] = r["applicable"][(typ, L, b)]
        row[f"void_{typ}{L}_b{b}"] = r["void"][(typ, L, b)]
    row["zero_den_any"] = bool(r["zero_den"].any())
    row["zero_hse_any"] = bool(any(v.any() for v in r["zero_se"].values()))
    cs = [Contrast(n, g, h, masks[j] if late_ else None) for j, (n, g, h, late_) in enumerate(CONTRASTS2)]
    t2 = time.time()
    for L in (24, 10):
        o = simultaneous_intervals(N, S, cs, B=B_OLD, mean_block=L,
                                   rng=np.random.default_rng([hold, 4300 + L]))
        row[f"oldq_L{L}"] = o.q
        row[f"oldapp_L{L}"] = o.primary_applicable
        for j, n in enumerate(names):
            row[f"oldse{L}_{n}"] = o.se[j]
            if abs(o.theta_hat[j] - r["theta"][j]) > 1e-12 + 1e-9 * abs(r["theta"][j]):
                raise RuntimeError("theta mismatch between rules")
    row["t_old"] = time.time() - t2
    return row


def run_chunk(args):
    scen, mode, start, stop, out, types = args
    fn = os.path.join(out, f"{scen}_{mode}_{start:06d}_{stop:06d}.json")
    if os.path.exists(fn):
        return fn, 0.0
    t0 = time.time()
    rows = [one_rep(scen, mode, rep, types) for rep in range(start, stop)]
    tmp = fn + ".tmp"
    with open(tmp, "w") as f:
        json.dump(rows, f)
    os.replace(tmp, fn)
    return fn, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--mode", required=True, choices=["cov", "truth"])
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--chunk", type=int, default=10)
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--types", nargs="+", default=["stat", "circ"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    assert a.procs <= 10
    os.makedirs(a.out, exist_ok=True)
    jobs = [(a.scenario, a.mode, s, min(s + a.chunk, a.start + a.n), a.out, tuple(a.types))
            for s in range(a.start, a.start + a.n, a.chunk)]
    t0 = time.time()
    with Pool(a.procs) as pool:
        for k, (fn, dt) in enumerate(pool.imap_unordered(run_chunk, jobs)):
            print(f"[{time.time() - t0:8.1f}s] {k + 1}/{len(jobs)} {os.path.basename(fn)} {dt:.1f}s", flush=True)
    print("done", a.scenario, a.mode, a.n, f"{time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()

"""Phase E driver: literature methods on the Phase D histories (same seeds -> paired with Phase D).

python run_phaseE.py --prep                     # simulate critical values and joint panels (cached)
python run_phaseE.py --scenario F1 --n 1000 --procs 8
"""
import os

for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import argparse
import json
import time
from multiprocessing import Pool

import numpy as np

OUT_DEFAULT = "C:/Users/lijun/Desktop/AI-Optimization-Research/experiments/results/precision_v9/phaseE"
CRIT_PATH = os.path.join(OUT_DEFAULT, "crit_values.npz")
PANEL_PATH = os.path.join(OUT_DEFAULT, "joint_panels.npz")
M3_L = (48, 100)
M3_B = (43, 100, 200)
B_BT = 999
_CACHE = {}


def resources():
    if "crit" not in _CACHE:
        d = np.load(CRIT_PATH)
        _CACHE["crit"] = {k: float(d[k]) for k in d.files}
        p = np.load(PANEL_PATH)
        _CACHE["panels"] = {k: (p[k] if p[k].ndim else int(p[k])) for k in p.files}
    return _CACHE["crit"], _CACHE["panels"]


def one_rep(scen, rep):
    from intervals import Contrast, simultaneous_intervals, stationary_bootstrap_indices
    from methods_lit import bt_fast_q, lit_methods, nw_lrv
    from pipeline2 import CONTRASTS2, masks2
    from run_phaseD import LS, get_series, seeds_for
    from bootstrap_t import ratio_parts
    crit, panels = resources()
    dev, hold = seeds_for(scen, "cov", rep)
    t0 = time.time()
    p, N, S = get_series(scen, dev, hold)
    row = {"rep": rep, "dev_seed": dev, "hold_seed": hold, "t_gen": time.time() - t0}
    Nbar, Sbar = N.mean(1), S.mean(1)
    masks = masks2(p)
    names = [c[0] for c in CONTRASTS2]
    T = Nbar.shape[1]
    t1 = time.time()
    th, meth, info = lit_methods(Nbar, Sbar, CONTRASTS2, masks, crit, panels)
    row["t_lit"] = time.time() - t1
    row["q_maxt"] = info["q_maxt"]
    row["rho_pw"] = info["rho_pw"]
    row["th"] = th.tolist()
    for m, (hw, se) in meth.items():
        row[f"hw_{m}"] = hw.tolist()
        if se is not None:
            row[f"se_{m}"] = se.tolist()
    _, psi, _ = ratio_parts(Nbar, Sbar, CONTRASTS2, masks)
    # M3 and the bootstrap-t benchmark; the benchmark reuses Phase D's bootstrap stream exactly
    t2 = time.time()
    for L in M3_L:
        idx = stationary_bootstrap_indices(T, B_BT, L, np.random.default_rng([hold, 700 + L]))
        q, _ = bt_fast_q(Nbar, Sbar, CONTRASTS2, masks, idx, th, list(M3_B))
        for b in M3_B:
            row[f"q_M3_L{L}_b{b}"] = q[b][0]
            row[f"void_M3_L{L}_b{b}"] = q[b][1]
    for b in M3_B + (20,):
        row[f"se_bt_b{b}"] = (np.sqrt(nw_lrv(psi, b + 1) / T)).tolist()
    idx = stationary_bootstrap_indices(T, B_BT, 24, np.random.default_rng([hold, 600 + LS.index(24)]))
    q, _ = bt_fast_q(Nbar, Sbar, CONTRASTS2, masks, idx, th, [20])
    row["q_bench_bt_L24_b20"] = q[20][0]
    row["t_bt"] = time.time() - t2
    t3 = time.time()
    cs = [Contrast(n, g, h, masks[j] if late else None) for j, (n, g, h, late) in enumerate(CONTRASTS2)]
    o = simultaneous_intervals(N, S, cs, B=2000, mean_block=24, rng=np.random.default_rng([hold, 4300 + 24]))
    row["q_bench_old_L24"] = o.q
    row["se_bench_old_L24"] = o.se.tolist()
    row["t_old"] = time.time() - t3
    return row


def run_chunk(a):
    scen, start, stop, out = a
    fn = os.path.join(out, f"{scen}_{start:06d}_{stop:06d}.json")
    if os.path.exists(fn):
        return fn, 0.0
    t0 = time.time()
    rows = [one_rep(scen, r) for r in range(start, stop)]
    with open(fn + ".tmp", "w") as f:
        json.dump(rows, f)
    os.replace(fn + ".tmp", fn)
    return fn, time.time() - t0


def prep():
    from methods_lit import critical_values, simulate_joint_panels
    os.makedirs(OUT_DEFAULT, exist_ok=True)
    t0 = time.time()
    crit = critical_values(cache_path=CRIT_PATH)
    print("crit", crit, f"{time.time() - t0:.1f}s", flush=True)
    if not os.path.exists(PANEL_PATH):
        pn = simulate_joint_panels(1075, 775, 12, K=20_000)
        np.savez(PANEL_PATH, **pn)
    print("panels done", f"{time.time() - t0:.1f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prep", action="store_true")
    ap.add_argument("--scenario")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--chunk", type=int, default=10)
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--out", default=os.path.join(OUT_DEFAULT, "raw"))
    a = ap.parse_args()
    if a.prep:
        prep()
        return
    assert a.procs <= 8
    if a.scenario.startswith("F"):
        a.procs = min(a.procs, 6)   # memory cap: pipeline + bootstrap ~0.45 GB per worker, limit 3 GB
    os.makedirs(a.out, exist_ok=True)
    jobs = [(a.scenario, s, min(s + a.chunk, a.n), a.out) for s in range(0, a.n, a.chunk)]
    t0 = time.time()
    with Pool(a.procs) as pool:
        for k, (fn, dt) in enumerate(pool.imap_unordered(run_chunk, jobs)):
            print(f"[{time.time() - t0:8.1f}s] {a.scenario} {k + 1}/{len(jobs)} {os.path.basename(fn)} {dt:.1f}s", flush=True)
    print("done", a.scenario, a.n, f"{time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()

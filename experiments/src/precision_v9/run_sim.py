"""Driver for precision_v9 coverage and truth simulations.

Usage:
  python run_sim.py --scenario F1 --mode cov   --n 3000 --procs 10 --out <dir>
  python run_sim.py --scenario F1 --mode truth --n 4000 --procs 10 --out <dir>
Scenarios: S0 (iid Gaussian daily totals), F1, F2, F3a, F3b (unconditional), F1c, F2c
(conditional on one fixed development history). Work is split into chunks of --chunk reps;
existing chunk files are skipped (resumable). Each worker uses one BLAS thread.
"""
import os

for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import argparse
import json
import time
from multiprocessing import Pool

import numpy as np

SCEN_CODE = {"S0": 9, "F1": 1, "F2": 2, "F3a": 3, "F3b": 4, "F1c": 5, "F2c": 6}
MODE_CODE = {"cov": 0, "truth": 1}
COND_DEV_SEED = 20261117          # the one fixed development history of F1c / F2c
B_PRIMARY = 2000
BLOCK_PRIMARY = 24.0
SERIES_KEEP = 1000                # daily series stored for reps < 1000 (block sensitivity)


def seeds_for(scen, mode, rep):
    hold = 1_000_000 * (10 * SCEN_CODE[scen] + MODE_CODE[mode]) + rep
    dev = COND_DEV_SEED if scen.endswith("c") else hold
    return dev, hold


def base_name(scen):
    return scen[:-1] if scen.endswith("c") else scen


def s0_series(hold_seed, T=1075):
    """Sanity scenario: iid Gaussian daily totals with varying counts; truth exact."""
    rng = np.random.default_rng([hold_seed, 3])
    mu = np.array([30.0, 29.0, 28.0, 31.0, 27.0, 26.0]) * 1e-4
    short = rng.random(T) < 0.05
    n_t = np.where(short, rng.integers(10, 30, size=T), 30)
    S1 = np.ceil(0.5 * n_t)
    common = rng.standard_normal(T)
    idio = rng.standard_normal((6, T))
    N = S1[None, :] * (mu[:, None] + 0.01 * (np.sqrt(0.8) * common[None, :] + np.sqrt(0.2) * idio))
    S = np.repeat(S1[None, :], 6, axis=0)
    return N[:, None, :], S[:, None, :]


def s0_truth():
    from pipeline import CONTRASTS
    mu = np.array([30.0, 29.0, 28.0, 31.0, 27.0, 26.0]) * 1e-4
    return np.array([mu[g] - mu[h] for _, g, h, _ in CONTRASTS])


def one_rep(scen, mode, rep):
    from intervals import simultaneous_intervals
    from pipeline import POLICIES, contrast_list, run_history, scenario_params, Params
    dev, hold = seeds_for(scen, mode, rep)
    if scen == "S0":
        p = Params()
        N, S = s0_series(hold, p.holdout_days)
    else:
        p = scenario_params(base_name(scen))
        N, S = run_history(p, dev, hold)
    Nbar, Sbar = N.mean(axis=1), S.mean(axis=1)
    cs = contrast_list(p)
    late = cs[2].mask
    row = {"rep": rep, "dev_seed": dev, "hold_seed": hold}
    for g, nm in enumerate(POLICIES):
        row[f"sumN_{nm}"] = float(Nbar[g].sum())
        row[f"sumS_{nm}"] = float(Sbar[g].sum())
        row[f"sumNlate_{nm}"] = float((Nbar[g] * late).sum())
        row[f"sumSlate_{nm}"] = float((Sbar[g] * late).sum())
    if mode == "truth":
        return row, None
    r = simultaneous_intervals(N, S, cs, B=B_PRIMARY, mean_block=BLOCK_PRIMARY,
                               rng=np.random.default_rng([hold, 4242]))
    row.update({"q": r.q, "z_bonf": r.z_bonf, "primary_applicable": r.primary_applicable})
    for j, c in enumerate(cs):
        row[f"th_{c.name}"] = r.theta_hat[j]
        row[f"se_{c.name}"] = r.se[j]
        row[f"void_{c.name}"] = int(r.void_counts[j])
        row[f"zse_{c.name}"] = bool(r.zero_se[j])
    for (cn, g), flag in r.zero_policy_flags.items():
        if flag:
            row[f"zeropol_{cn}_{g}"] = True
    return row, (Nbar.astype(np.float32), Sbar.astype(np.float32))


def run_chunk(args):
    scen, mode, start, stop, out = args
    fn = os.path.join(out, f"{scen}_{mode}_{start:06d}_{stop:06d}.json")
    if os.path.exists(fn):
        return fn, 0.0
    t0 = time.time()
    rows, Ns, Ss = [], [], []
    for rep in range(start, stop):
        row, ser = one_rep(scen, mode, rep)
        rows.append(row)
        if ser is not None and rep < SERIES_KEEP:
            Ns.append(ser[0])
            Ss.append(ser[1])
    if Ns:
        np.savez_compressed(os.path.join(out, f"{scen}_{mode}_{start:06d}_{stop:06d}_series.npz"),
                            N=np.stack(Ns), S=np.stack(Ss), reps=np.arange(start, start + len(Ns)))
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
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--procs", type=int, default=10)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    assert a.procs <= 10
    os.makedirs(a.out, exist_ok=True)
    jobs = [(a.scenario, a.mode, s, min(s + a.chunk, a.start + a.n), a.out)
            for s in range(a.start, a.start + a.n, a.chunk)]
    t0 = time.time()
    with Pool(a.procs) as pool:
        for k, (fn, dt) in enumerate(pool.imap_unordered(run_chunk, jobs)):
            print(f"[{time.time() - t0:8.1f}s] {k + 1}/{len(jobs)} {os.path.basename(fn)} {dt:.1f}s",
                  flush=True)
    print("done", a.scenario, a.mode, a.n, f"{time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()

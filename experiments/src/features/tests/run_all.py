"""Run every feature test and save the outputs (project root):

  experiments/.venv/Scripts/python.exe -X utf8 experiments/src/features/tests/run_all.py [--skip-dryrun]

Writes to experiments/results/feature_tests/:
  unit_tests.log            unittest output (hand-computed examples, property tests, negative controls)
  feature_catalog.csv       the catalogue (name, group, role = primary / variant / control / diagnostic,
                            formula, window, fields, warm-up, timing, source)
  lookahead_synthetic.csv   look-ahead test on synthetic stocks
  dryrun_*.csv / .json, lookahead_real.csv, panel_trial_*   dry run on the trial stocks (dryrun_trial.py)
Separate scripts: tests/zo_real_validation.py (structure of the Z_O raw tables) and
audit/oa10_sample.py (sample list of the signed date audit).
No label, forward return or performance number is computed anywhere.
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys
import time
import unittest

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, SRC)

from features import panel, registry, lookahead      # noqa: E402
from features.config import ZO_LAG                    # noqa: E402
from features.tests import synth                      # noqa: E402

OUT = os.path.normpath(os.path.join(SRC, "..", "results", "feature_tests"))


def run_unit_tests() -> bool:
    buf = io.StringIO()
    suite = unittest.defaultTestLoader.discover(HERE, top_level_dir=SRC)
    res = unittest.TextTestRunner(stream=buf, verbosity=2).run(suite)
    head = (f"run at {time.strftime('%Y-%m-%d %H:%M:%S')}; python {sys.version.split()[0]}; numpy {np.__version__}; "
            f"pandas {pd.__version__}\n")
    with open(os.path.join(OUT, "unit_tests.log"), "w", encoding="utf-8") as fh:
        fh.write(head + buf.getvalue())
    line = (f"unit tests: run={res.testsRun} failures={len(res.failures)} errors={len(res.errors)} "
            f"skipped={len(res.skipped)}")
    with open(os.path.join(OUT, "unit_tests.log"), "a", encoding="utf-8") as fh:
        fh.write("\n" + line + "\n")
    print(line, flush=True)
    return res.wasSuccessful()


def synthetic_lookahead(n_stocks: int = 5, n_days: int = 6) -> pd.DataFrame:
    cal = synth.make_calendar()
    codes = ["sh.600001", "sz.000002", "sz.300003", "sh.688004", "sh.600005"][:n_stocks]
    tables = synth.make_zo_tables(codes, cal, seed=21, n_per_code=120, last_pos=1290)
    idx = synth.make_raw_index(cal)
    rng = np.random.default_rng(7)
    recs = []
    for k, code in enumerate(codes):
        raw = synth.make_raw_bars(code, cal, seed=100 + k, n_rows=1300, missing_row=650 if k == 1 else None,
                                  long_suspension=(k == 2))
        if k == 3:                 # rows repaired by the fetch pipeline (PLAN 3.11 rule 12): exercises the flag column
            raw["filled_from_xsrc"] = "0"
            raw.loc[[300, 900], "filled_from_xsrc"] = "1"
        far = cal.next(pd.to_datetime(raw["date"]).max())

        def build(c, rb, cl, co, ri, tb):
            return panel.build_stock_features(c, rb, cl, co, ri, tb)
        ref = build(code, raw, cal, far, idx, tables)
        days = list(ref.index[rng.choice(np.arange(280, len(ref) - 5), size=n_days - 2, replace=False)])
        ev = cal.pos_array(pd.to_datetime(tables.for_code(code).blk["交易日期"]))
        p = int(ev[(ev > 400) & (ev < 1200)][0])
        days += [cal.days[p + ZO_LAG["blk"]], cal.days[p + ZO_LAG["blk"] - 1]]
        recs += lookahead.check_lookahead(build, code, raw, cal, sorted(set(days)), idx, tables, far_cutoff=far,
                                          reference=ref, seed=k)
    df = pd.DataFrame(recs)
    df.to_csv(os.path.join(OUT, "lookahead_synthetic.csv"), index=False)
    print(f"synthetic look-ahead: {len(df)} checks on {df.groupby(['code', 'decision_day']).ngroups} stock-days, "
          f"{int(df['equal'].sum())} bit-identical; non-NaN columns compared per row: "
          f"{int(df['n_nonnan'].min())}-{int(df['n_nonnan'].max())} of {int(df['n_cols'].max())}", flush=True)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-dryrun", action="store_true")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    registry.catalogue().to_csv(os.path.join(OUT, "feature_catalog.csv"), index=False, encoding="utf-8-sig")
    ok = run_unit_tests()
    la = synthetic_lookahead()
    ok = ok and bool(la["equal"].all())
    if not args.skip_dryrun:
        r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "dryrun_trial.py")])
        ok = ok and r.returncode == 0
    print("ALL PASSED" if ok else "FAILURES - see the logs")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

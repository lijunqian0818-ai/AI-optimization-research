"""v0.8 checks on the landed trial files (read-only; data cut-off 2021-12-31, PLAN v0.8 C-8).

  C-3  ro_trig_cum3_* of the 20 trial names are bit-identical to the values computed by the v0.7 code
       before the change (v08_cum3_before_change.parquet, written by v08_cum3_before_change_script.py with
       the same cut-off immediately before the threshold was moved into the rule calendar).

Run: experiments/.venv/Scripts/python.exe -X utf8 experiments/src/features/tests/v08_real_checks.py
Writes experiments/results/feature_tests/v08_real_checks.json. No return, label or outcome is computed.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from engine import datacut as dc          # noqa: E402
from features import panel, store         # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(ROOT, "experiments", "results", "feature_tests")


def main() -> int:
    before = pd.read_parquet(os.path.join(OUT, "v08_cum3_before_change.parquet"))
    st = store.RawStore(data_cutoff=dc.PILOT_CUTOFF)
    cal = st.calendar()
    res = {"data_cutoff": str(dc.PILOT_CUTOFF), "names": 0, "rows": 0, "columns": [], "bit_identical": True,
           "mismatching_names": []}
    for code, g in before.groupby("code", sort=True):
        raw = st.raw_bars(code)
        ri = st.raw_index(panel.proxy_index_code(code))
        f = panel.build_stock_features(code, raw, cal, cal.days[-1], ri, None, groups=("R_O",))
        cols = [c for c in f.columns if c.startswith("ro_trig_cum3")]
        g = g.set_index("decision_day")[cols]
        new = f[cols]
        same = g.index.equals(new.index) and list(g.columns) == cols
        if same:
            a, b = g.values.astype(np.float64), new.values.astype(np.float64)
            same = bool(((np.isnan(a) & np.isnan(b)) | (a.view(np.uint64) == b.view(np.uint64))).all())
        res["names"] += 1
        res["rows"] += len(new)
        res["columns"] = cols
        if not same:
            res["bit_identical"] = False
            res["mismatching_names"].append(code)
    with open(os.path.join(OUT, "v08_real_checks.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res))
    return 0 if res["bit_identical"] else 1


if __name__ == "__main__":
    sys.exit(main())

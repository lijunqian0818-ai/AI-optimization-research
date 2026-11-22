"""Test helpers: path set-up, tiny hand-built panels, and a minimal runner (pytest is not
installed in experiments/.venv and no package may be added)."""
from __future__ import annotations

import json
import sys
import time
import traceback
from datetime import date
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[2]            # experiments/src
ROOT = SRC.parents[1]                                # project root
OUT = ROOT / "experiments" / "results" / "engine_tests"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from engine.market import Event, Market, Sec          # noqa: E402
from engine.synth import weekdays                     # noqa: E402

NAN = float("nan")


def T(o, c, pc, amt=1e9, st=False):
    return {"s": "T", "o": o, "c": c, "pc": pc, "amt": amt, "st": st}


def S(pc=NAN, st=False):          # whole-day suspension row; vendor carry-forward values are junk on purpose
    return {"s": "S", "o": 999.0, "c": 999.0, "pc": pc, "amt": 0.0, "st": st}


def N(pc, st=False):              # flagged trading, zero volume
    return {"s": "N", "o": pc, "c": pc, "pc": pc, "amt": 0.0, "st": st}


def X():                          # no row
    return {"s": "X"}


def panel(start: date, rows: dict, events=(), delist: dict | None = None, urs=None, days=None,
          u_spans=None) -> Market:
    n = max(len(v) for v in rows.values())
    days = days or weekdays(start, n)
    secs = {}
    for code, rr in rows.items():
        o = np.full(n, np.nan); c = np.full(n, np.nan); pc = np.full(n, np.nan); am = np.zeros(n)
        has = np.zeros(n, bool); ft = np.zeros(n, bool); vp = np.zeros(n, bool); st = np.zeros(n, bool)
        for i, r in enumerate(rr):
            if r["s"] == "X":
                continue
            has[i] = True
            o[i], c[i], pc[i], am[i], st[i] = r["o"], r["c"], r["pc"], r["amt"], r["st"]
            ft[i] = r["s"] in ("T", "N")
            vp[i] = r["s"] == "T"
        secs[code] = Sec(code, o, c, pc, am, has, ft, vp, st, (delist or {}).get(code))
    return Market(days, secs, list(events), urs, u_spans)


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def run_tests(module_name: str, tests: list, out_name: str) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    results, t0 = [], time.time()
    for fn in tests:
        rec = {"test": fn.__name__, "doc": (fn.__doc__ or "").strip().split("\n")[0]}
        try:
            info = fn()
            rec["status"] = "pass"
            if info is not None:
                rec["info"] = info
        except Exception as e:                       # a failing test is recorded, never hidden
            rec["status"] = "FAIL"
            rec["error"] = f"{type(e).__name__}: {e}"
            rec["traceback"] = traceback.format_exc()
        results.append(rec)
        print(f"[{rec['status']}] {module_name}.{rec['test']}" + (f"  -> {rec.get('error')}" if rec["status"] == "FAIL" else ""))
    from engine.config import conventions_hash       # every result file carries it (PLAN v0.7, E-20)
    summary = {"module": module_name, "conventions_hash": conventions_hash(),
               "n": len(results), "passed": sum(r["status"] == "pass" for r in results),
               "failed": sum(r["status"] == "FAIL" for r in results), "seconds": round(time.time() - t0, 2),
               "results": results}
    (OUT / out_name).write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"== {module_name}: {summary['passed']}/{summary['n']} passed ({summary['seconds']} s) -> {OUT / out_name}")
    return summary

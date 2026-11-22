"""Offline self-test of the runner (no network request): retry / back-off, failure records, pause after consecutive
failures, stop after the pause budget, resume skipping verified units, re-fetch when a stored file was altered.
Uses a temporary directory; the real manifest and data are not touched.

  experiments/.venv/Scripts/python.exe experiments/src/data_fetch/selftest_offline.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd

import core
from core import CFG, Unit, StopRun, NoData

tmp = Path(tempfile.mkdtemp(prefix="fetch_selftest_"))
core.RAW, core.OUT, core.STATE, core.LOGS = tmp / "raw", tmp / "out", tmp / "out" / "state", tmp / "out" / "logs"
core.MANIFEST = core.OUT / "manifest.jsonl"
CFG.backoff, CFG.pause_seconds, CFG.max_consec_fail, CFG.max_pauses = (0.01, 0.01, 0.01), 0.05, 3, 1
CFG.progress_units = 1000

calls = {}


def mk(key, behaviour):
    def fetch():
        calls[key] = calls.get(key, 0) + 1
        if behaviour == "ok":
            return pd.DataFrame({"date": ["2020-01-02", "2020-01-03"], "v": [1, 2]})
        if behaviour == "flaky" and calls[key] >= 3:
            return pd.DataFrame({"date": ["2021-05-06"], "v": [3]})
        if behaviour == "nodata":
            raise NoData("upstream says no record")
        raise ConnectionError("simulated network failure")
    return Unit("selftest", "fake", key, f"selftest/{key}.parquet", fetch, {"p": 1}, ("date",), host="fake")


units = [mk("a", "ok"), mk("b", "flaky"), mk("c", "nodata"), mk("d", "ok")]
c = core.run_units(units, "selftest-1")
assert (c["ok"], c["empty"], c["failed"]) == (3, 1, 0), c
assert calls == {"a": 1, "b": 3, "c": 1, "d": 1}, calls
m = core.load_manifest()
assert m[("selftest", "fake", "b")]["attempts"] == 3 and "simulated network failure" in m[("selftest", "fake", "b")]["error"]
assert m[("selftest", "fake", "a")]["date_min"] == "2020-01-02" and m[("selftest", "fake", "a")]["rows"] == 2

# resume: nothing is requested again
c = core.run_units(units, "selftest-2")
assert c["skipped"] == 4 and calls == {"a": 1, "b": 3, "c": 1, "d": 1}, (c, calls)

# a stored file that no longer matches its hash is fetched again
p = core.RAW / "selftest" / "a.parquet"
p.write_bytes(p.read_bytes() + b"x")
c = core.run_units(units, "selftest-3")
assert c["skipped"] == 3 and calls["a"] == 2, (c, calls)

# persistent failures: each unit recorded as failed after 1 + 3 attempts; pause after 3 in a row; stop after the pause budget
bad = [mk(f"bad{i}", "fail") for i in range(8)]
try:
    core.run_units(bad, "selftest-4")
    raise AssertionError("expected StopRun")
except StopRun as e:
    assert e.code == 4
m = core.load_manifest()
failed = [k for k, r in m.items() if r["status"] == "failed"]
assert len(failed) == 6 and all(m[k]["attempts"] == 4 for k in failed), failed     # 3 -> pause -> 3 -> stop
assert all(calls[f"bad{i}"] == 4 for i in range(6)) and "bad6" not in calls

# failed units are tried again by the next run
calls.clear()
CFG.max_pauses = 5
c = core.run_units(bad[:2], "selftest-5")
assert c["failed"] == 2 and calls == {"bad0": 4, "bad1": 4}
print("offline self-test passed; temp dir:", tmp)

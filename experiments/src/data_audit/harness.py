"""Shared call harness for the data-audit smoke test.

- every data call goes through `call()`: cached to disk, logged to JSONL, counted against a hard budget
- >= MIN_GAP seconds between any two HTTP requests (patched at requests / curl_cffi Session level,
  so the multi-page AKShare functions are throttled too) and >= CALL_GAP seconds between calls
- on error: back-off retries (5 / 20 / 60 s, at most 3), then the call is recorded as failed and skipped
- an empty upstream answer (AKShare raises TypeError / KeyError / returns empty) is recorded, not hidden
Nothing here trains a model or runs a backtest.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261115
random.seed(SEED)
np.random.seed(SEED)

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "experiments" / "results" / "data_audit"
CACHE = OUT / "cache"
LOGS = OUT / "logs"
CACHE.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
CALL_LOG = LOGS / "call_log.jsonl"
COUNTER = LOGS / "call_counter.json"

BUDGET = 590          # hard cap on logical calls (function calls / BaoStock queries), incl. retries
MIN_GAP = 0.6         # seconds between two HTTP requests
CALL_GAP = 1.0        # seconds between two logical calls
BACKOFF = (5, 20, 60)

_last_http = [0.0]
_http_count = [0]


def _throttle():
    dt = time.time() - _last_http[0]
    if dt < MIN_GAP:
        time.sleep(MIN_GAP - dt)
    _last_http[0] = time.time()
    _http_count[0] += 1


def _patch_http():
    import requests
    orig = requests.Session.request

    def patched(self, method, url, *a, **k):
        _throttle()
        return orig(self, method, url, *a, **k)

    requests.Session.request = patched
    try:
        from curl_cffi import requests as cr
        corig = cr.Session.request

        def cpatched(self, method, url, *a, **k):
            _throttle()
            return corig(self, method, url, *a, **k)

        cr.Session.request = cpatched
    except Exception:  # pragma: no cover
        pass


_patch_http()


def _load_counter() -> dict:
    """Budget counter derived from the append-only call log (safe when two stages on different hosts run side by side)."""
    n = h = 0
    if CALL_LOG.exists():
        for line in CALL_LOG.read_text(encoding="utf-8").splitlines():
            if '"attempt"' in line:
                n += 1
                try:
                    h += json.loads(line).get("http_requests", 0) or 0
                except Exception:
                    pass
    return {"calls": n + 1 if False else n, "http": h}


def _save_counter(c: dict):
    return None


def calls_used() -> int:
    return _load_counter()["calls"]


class BudgetExceeded(RuntimeError):
    pass


def _key(name: str, args: tuple, kwargs: dict) -> str:
    raw = json.dumps([name, list(args), kwargs], ensure_ascii=False, sort_keys=True, default=str)
    h = hashlib.md5(raw.encode("utf-8")).hexdigest()[:10]
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in "_".join(str(a) for a in args))[:60]
    return f"{name}__{safe}__{h}"


def _log(rec: dict):
    with open(CALL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def _store(df: pd.DataFrame, path_base: Path) -> str:
    try:
        df.to_parquet(str(path_base) + ".parquet", index=False)
        return path_base.name + ".parquet"
    except Exception:
        df.to_csv(str(path_base) + ".csv", index=False, encoding="utf-8-sig")
        return path_base.name + ".csv"


def _read(path_base: Path):
    p = Path(str(path_base) + ".parquet")
    if p.exists():
        return pd.read_parquet(p)
    c = Path(str(path_base) + ".csv")
    if c.exists():
        return pd.read_csv(c, dtype=str)
    return None


def call(name: str, fn, *args, group: str = "", _net_retries: int | None = None, **kwargs):
    """Returns DataFrame (possibly empty) or None on failure. Cached results cost no request."""
    key = _key(name, args, kwargs)
    base = CACHE / key
    cached = _read(base)
    if cached is not None:
        return cached
    fail_marker = Path(str(base) + ".FAILED.json")
    if fail_marker.exists():
        return None
    last_err = None
    for attempt in range(0, len(BACKOFF) + 1):
        c = _load_counter()
        if c["calls"] >= BUDGET:
            raise BudgetExceeded(f"budget of {BUDGET} calls used")
        c["calls"] += 1
        _save_counter(c)
        h0 = _http_count[0]
        t0 = time.time()
        status, rows, err, df = "ok", None, None, None
        try:
            df = fn(*args, **kwargs)
            if df is None:
                df = pd.DataFrame()
            rows = int(len(df))
            if rows == 0:
                status = "empty"
        except (TypeError, KeyError, IndexError, ValueError) as e:
            # AKShare raises these on an empty / malformed upstream answer: recorded, retried once
            status, err = "error_parse", f"{type(e).__name__}: {e}"
            last_err = traceback.format_exc(limit=3)
        except Exception as e:  # network, rate limit, ...
            status, err = "error_net", f"{type(e).__name__}: {e}"
            last_err = traceback.format_exc(limit=3)
        el = time.time() - t0
        c = _load_counter()
        c["http"] += _http_count[0] - h0
        _save_counter(c)
        rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "group": group, "name": name, "args": list(args),
               "kwargs": kwargs, "attempt": attempt, "status": status, "rows": rows,
               "elapsed_s": round(el, 3), "http_requests": _http_count[0] - h0, "error": (err or "")[:300],
               "cache": None}
        if status in ("ok", "empty"):
            rec["cache"] = _store(df, base)
            _log(rec)
            time.sleep(CALL_GAP)
            return df
        _log(rec)
        # parse errors: one retry only (most are "no data upstream"); network errors: full back-off
        max_retry = 1 if status == "error_parse" else (len(BACKOFF) if _net_retries is None else _net_retries)
        if attempt >= max_retry:
            break
        time.sleep(BACKOFF[attempt])
    fail_marker.write_text(json.dumps({"name": name, "args": list(args), "kwargs": kwargs, "error": last_err},
                                      ensure_ascii=False, default=str), encoding="utf-8")
    time.sleep(CALL_GAP)
    return None


# ---------------------------------------------------------------- BaoStock helpers
_bs_logged_in = [False]


def bs_login():
    import baostock as bs
    if not _bs_logged_in[0]:
        lg = bs.login()
        _bs_logged_in[0] = True
        _log({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "group": "baostock", "name": "login",
              "status": lg.error_code, "error": lg.error_msg})
    return bs


def bs_logout():
    import baostock as bs
    if _bs_logged_in[0]:
        bs.logout()
        _bs_logged_in[0] = False


def bs_query(method: str, *args, **kwargs) -> pd.DataFrame:
    """Run a baostock query_* method and return all rows as a DataFrame of strings."""
    bs = bs_login()
    rs = getattr(bs, method)(*args, **kwargs)
    if rs.error_code != "0":
        raise ConnectionError(f"baostock {method} error {rs.error_code}: {rs.error_msg}")
    rows = []
    while rs.next():
        rows.append(rs.get_row_data())
    return pd.DataFrame(rows, columns=rs.fields)


def bs_call(method: str, *args, group: str = "baostock", **kwargs):
    return call("bs_" + method, lambda *a, **k: bs_query(method, *a, **k), *args, group=group, **kwargs)


def bs_code(code: str) -> str:
    return ("sh." if code.startswith(("6", "9")) else "sz.") + code


def sina_code(code: str) -> str:
    return ("sh" if code.startswith(("6", "9")) else "sz") + code


def clear_failed(name: str, *args, **kwargs):
    """Remove the failure marker of a call so that it may be tried again later (the earlier attempts stay in the log)."""
    m = Path(str(CACHE / _key(name, args, kwargs)) + ".FAILED.json")
    if m.exists():
        m.unlink()


def last_error() -> str:
    try:
        return json.loads(CALL_LOG.read_text(encoding="utf-8").strip().splitlines()[-1]).get("error", "")
    except Exception:
        return ""


class Push2Breaker:
    """Eastmoney push2 quote host: on a rate-limit disconnect do not hammer. Wait once (cooldown), try again;
    after `max_trips` trips the remaining calls of the group are skipped and recorded as not attempted."""

    def __init__(self, cooldown=330, max_trips=3, gap=3.0):
        self.cooldown, self.max_trips, self.gap = cooldown, max_trips, gap
        self.trips, self.dead, self.skipped = 0, False, []

    def call(self, name, fn, *args, group="", **kwargs):
        if self.dead:
            self.skipped.append([name, list(args)])
            return None
        clear_failed(name, *args, **kwargs)
        df = call(name, fn, *args, group=group, _net_retries=0, **kwargs)
        time.sleep(self.gap)
        if df is None and "RateLimit" in last_error():
            self.trips += 1
            if self.trips >= self.max_trips:
                self.dead = True
                self.skipped.append([name, list(args)])
                return None
            time.sleep(self.cooldown)
            clear_failed(name, *args, **kwargs)
            df = call(name, fn, *args, group=group, _net_retries=0, **kwargs)
            if df is None and "RateLimit" in last_error():
                self.trips += 1
                self.dead = self.trips >= self.max_trips
        return df

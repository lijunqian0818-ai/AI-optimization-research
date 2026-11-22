"""Core of the full-pull fetcher: rate limits, BaoStock session, manifest, resumable unit runner.

Design rules (PLAN v0.6 section 2.5; AUDIT_REPORT section 5):
- single thread, strictly sequential; one process per upstream host (host lock files)
- every (stage, source, unit) ends in exactly one manifest record per run attempt: success, empty or failure
- nothing is cleaned, merged or computed here: what the upstream / library returned is stored as Parquet,
  with fetch metadata in the Parquet schema metadata and in the manifest
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import socket
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "experiments" / "data" / "raw"
OUT = ROOT / "experiments" / "results" / "data_fetch"
STATE = OUT / "state"
LOGS = OUT / "logs"
MANIFEST = OUT / "manifest.jsonl"


class NoData(Exception):
    """The upstream answered and said there is no record (not a failure)."""


class PermanentError(Exception):
    """A request that cannot succeed by retrying (e.g. a malformed code): recorded as failed after one attempt."""


class StopRun(Exception):
    def __init__(self, msg, code):
        super().__init__(msg)
        self.code = code


# ------------------------------------------------------------------ configuration (filled by run_fetch.py)
@dataclass
class Cfg:
    bs_gap: float = 1.0            # s between two BaoStock queries (PLAN 2.5: at least 1 s)
    bs_timeout: float = 180.0      # socket timeout for BaoStock (the library sets none: a dead link would hang forever)
    bs_relogin_every: int = 400    # proactive re-login after this many queries
    bs_relogin_minutes: float = 25.0
    http_gap: float = 1.5          # s between two HTTP requests to the same host (PLAN 2.5, Gate-2 value)
    http_daily_cap: int = 3000     # requests per HTTP host per local calendar day (PLAN 2.5)
    backoff: tuple = (5, 20, 60)   # retry waits; at most len(backoff) retries
    max_consec_fail: int = 5       # consecutive failed units before a pause
    pause_seconds: float = 1800.0
    max_pauses: int = 6            # after this many pauses the run stops (exit code 4)
    ratelimit_wait: float = 330.0  # wait after an explicit rate-limit error (PLAN 2.5)
    daily_unit_cap: int = 0        # units per local day for this run's stage (0 = none); Sina bars: 1000
    max_requests: int = 0          # stop after this many requests in this run (0 = none); used for trial runs
    progress_units: int = 20
    progress_seconds: float = 300.0
    resume: bool = True
    retry_empty: bool = False
    run_id: str = ""


CFG = Cfg()

# ------------------------------------------------------------------ logging
_log_file = [None]


def open_log(stage: str):
    LOGS.mkdir(parents=True, exist_ok=True)
    p = LOGS / f"{stage}_{time.strftime('%Y%m%d_%H%M%S')}.log"
    _log_file[0] = open(p, "a", encoding="utf-8")
    return p


def log(msg: str):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    try:
        print(line, flush=True)
    except Exception:
        pass
    if _log_file[0] is not None:
        _log_file[0].write(line + "\n")
        _log_file[0].flush()


# ------------------------------------------------------------------ host locks (one process per upstream host)
_locks = []


def acquire_host_lock(host: str) -> bool:
    STATE.mkdir(parents=True, exist_ok=True)
    f = open(STATE / f"{host}.lock", "a+")
    try:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:  # pragma: no cover
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return False
    _locks.append(f)   # released by the OS when the process ends, however it ends
    return True


# ------------------------------------------------------------------ HTTP layer (requests / curl_cffi patched at Session level)
def host_group(url: str) -> str:
    h = (urlsplit(url).hostname or "").lower()
    for key in ("sina", "eastmoney", "sse.com.cn", "szse", "cninfo", "qq.com"):
        if key in h:
            return key.replace(".com.cn", "").replace(".com", "")
    return h or "unknown"


class Http:
    count = 0                 # requests actually sent by this process
    last_time: dict = {}      # host -> time of the last request
    memo: dict = {}           # identical GETs inside one memo group are sent once (AKShare re-requests page 1)
    last_resp: dict = {}      # status / url / head of the last response (evidence for "empty" versus "error")

    @staticmethod
    def _counter_path(host):
        return STATE / f"http_count_{host}.json"

    @classmethod
    def _today_count(cls, host):
        p = cls._counter_path(host)
        today = time.strftime("%Y-%m-%d")
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            d = {}
        return d, today, int(d.get(today, 0))

    @classmethod
    def before(cls, host):
        d, today, n = cls._today_count(host)
        if CFG.http_daily_cap and n >= CFG.http_daily_cap:
            now = dt.datetime.now()
            nxt = (now + dt.timedelta(days=1)).replace(hour=0, minute=1, second=0, microsecond=0)
            wait = (nxt - now).total_seconds()
            log(f"[cap] host={host} reached the daily cap of {CFG.http_daily_cap} requests; sleeping {wait/3600:.2f} h until {nxt}")
            time.sleep(wait)
        gap = time.time() - cls.last_time.get(host, 0.0)
        if gap < CFG.http_gap:
            time.sleep(CFG.http_gap - gap)

    @classmethod
    def after(cls, host):
        cls.last_time[host] = time.time()
        cls.count += 1
        d, today, n = cls._today_count(host)
        d = {today: n + 1}     # only today's count is kept
        STATE.mkdir(parents=True, exist_ok=True)
        cls._counter_path(host).write_text(json.dumps(d), encoding="utf-8")


def _wrap(orig):
    def request(self, method, url, *a, **k):
        host = host_group(str(url))
        key = None
        if str(method).upper() == "GET":
            prm = k.get("params")
            if isinstance(prm, dict):      # "1" and 1 are the same request (AKShare re-requests page 1 as an int)
                prm = {str(x): str(y) for x, y in prm.items()}
            key = (str(url), json.dumps(prm, sort_keys=True, default=str))
            if key in Http.memo:
                return Http.memo[key]
        Http.before(host)
        try:
            resp = orig(self, method, url, *a, **k)
        finally:
            Http.after(host)
        try:
            Http.last_resp = {"status": resp.status_code, "url": str(resp.url)[:200], "len": len(resp.content),
                              "head": resp.text[:200]}
        except Exception:
            Http.last_resp = {"status": getattr(resp, "status_code", None)}
        if key is not None and getattr(resp, "status_code", None) == 200:
            Http.memo[key] = resp
        return resp
    return request


def patch_http():
    import requests
    requests.Session.request = _wrap(requests.Session.request)
    try:
        from curl_cffi import requests as cr
        cr.Session.request = _wrap(cr.Session.request)
    except Exception:  # pragma: no cover
        pass


# ------------------------------------------------------------------ BaoStock session
class BS:
    logged = False
    n = 0                # queries sent by this process (login not counted)
    since_login = 0
    t_login = 0.0
    t_last = 0.0
    logins = 0

    @classmethod
    def login(cls):
        import baostock as bs
        socket.setdefaulttimeout(CFG.bs_timeout)
        lg = bs.login()
        if lg is None or lg.error_code != "0":
            cls.logged = False
            raise ConnectionError(f"baostock login failed: {getattr(lg, 'error_code', None)} {getattr(lg, 'error_msg', None)}")
        cls.logged, cls.since_login, cls.t_login = True, 0, time.time()
        cls.logins += 1
        log(f"[baostock] login ok (login #{cls.logins})")

    @classmethod
    def logout(cls):
        if cls.logged:
            try:
                import baostock as bs
                bs.logout()
            except Exception:
                pass
        cls.logged = False

    @classmethod
    def query(cls, method: str, *args, **kwargs) -> pd.DataFrame:
        """One BaoStock query; all rows as strings, exactly as returned. Any error forces a re-login before the next query."""
        import baostock as bs
        if cls.logged and (cls.since_login >= CFG.bs_relogin_every
                           or time.time() - cls.t_login > CFG.bs_relogin_minutes * 60):
            cls.logout()
        if not cls.logged:
            cls.login()
        gap = time.time() - cls.t_last
        if gap < CFG.bs_gap:
            time.sleep(CFG.bs_gap - gap)
        cls.n += 1
        cls.since_login += 1
        try:
            rs = getattr(bs, method)(*args, **kwargs)
            if rs is not None and str(rs.error_code).startswith("10004"):     # parameter error: retrying cannot help
                raise PermanentError(f"baostock {method} parameter error {rs.error_code}: {rs.error_msg}")
            if rs is None or rs.error_code != "0":
                raise ConnectionError(f"baostock {method} error {getattr(rs, 'error_code', None)}: {getattr(rs, 'error_msg', None)}")
            rows = []
            while rs.error_code == "0" and rs.next():
                rows.append(rs.get_row_data())
            if rs.error_code != "0":
                raise ConnectionError(f"baostock {method} error while paging {rs.error_code}: {rs.error_msg}")
            return pd.DataFrame(rows, columns=rs.fields)
        except BaseException:
            cls.logout()          # the socket may be in an undefined state: drop the session
            raise
        finally:
            cls.t_last = time.time()


# ------------------------------------------------------------------ storage
def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_parquet(df: pd.DataFrame, path: Path, meta: dict) -> dict:
    """Store the frame as returned. If a column has mixed Python objects that Arrow rejects, object columns are
    stored as strings (None kept) and this is recorded."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(df.index, pd.RangeIndex):
        df = df.reset_index()
    cast = False
    try:
        table = pa.Table.from_pandas(df, preserve_index=False)
    except Exception:
        df = df.copy()
        for c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].map(lambda x: None if x is None or (isinstance(x, float) and x != x) else str(x))
        table = pa.Table.from_pandas(df, preserve_index=False)
        cast = True
    meta = dict(meta, object_columns_cast_to_str=cast)
    md = dict(table.schema.metadata or {})
    md[b"fetch_meta"] = json.dumps(meta, ensure_ascii=False, default=str).encode("utf-8")
    table = table.replace_schema_metadata(md)
    tmp = path.with_suffix(path.suffix + ".tmp")
    pq.write_table(table, tmp, compression="zstd")
    os.replace(tmp, path)
    return {"bytes": path.stat().st_size, "sha256": sha256_file(path), "object_columns_cast_to_str": cast}


# ------------------------------------------------------------------ manifest
def load_manifest() -> dict:
    """Latest record per (stage, source, unit)."""
    latest = {}
    if MANIFEST.exists():
        with open(MANIFEST, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue      # a torn last line after a hard kill
                latest[(r["stage"], r["source"], r["unit"])] = r
    return latest


def all_manifest_records() -> list:
    out = []
    if MANIFEST.exists():
        with open(MANIFEST, encoding="utf-8") as f:
            for line in f:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def append_manifest(rec: dict):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        f.flush()
        os.fsync(f.fileno())


# ------------------------------------------------------------------ units
@dataclass
class Unit:
    stage: str
    source: str
    key: str                       # security code, date, month ...
    relpath: str                   # under RAW
    fetch: Callable                # () -> DataFrame | (DataFrame, dict); raises NoData for "no record"
    params: dict = field(default_factory=dict)
    date_cols: tuple = ()
    host: str = "baostock"
    memo_group: str = ""

    @property
    def id(self):
        return (self.stage, self.source, self.key)

    @property
    def params_hash(self):
        return hashlib.md5(json.dumps(self.params, sort_keys=True, default=str).encode()).hexdigest()[:12]


def record_is_valid(rec: dict, u: Unit, check_hash: bool = True) -> bool:
    if not rec or not rec.get("ok") or rec.get("params_hash") != u.params_hash:
        return False
    if rec.get("status") == "empty" and CFG.retry_empty:
        return False
    if rec.get("file"):
        p = RAW / rec["file"]
        if not p.exists():
            return False
        if check_hash and sha256_file(p) != rec.get("sha256"):
            return False
    elif rec.get("status") != "empty":
        return False
    return True


def _date_range(df, cols):
    for c in cols:
        if c in df.columns and len(df):
            s = df[c].dropna().astype(str).str[:10]
            s = s[s.str.match(r"^\d{4}-?\d{2}-?\d{2}")]
            if len(s):
                return s.min(), s.max()
    return None, None


def _versions():
    from importlib.metadata import version
    out = {}
    for p in ("akshare", "baostock", "pandas", "pyarrow"):
        try:
            out[p] = version(p)
        except Exception:
            out[p] = None
    return out


def _fmt_eta(sec):
    if sec is None:
        return "n/a"
    return f"{sec/3600:.1f}h" if sec >= 3600 else f"{sec/60:.1f}min"


def run_units(units: list, label: str) -> dict:
    """Run the units in order. Returns counters. Raises StopRun when the run has to stop early."""
    man = load_manifest()
    versions = _versions()
    todo, skipped = [], 0
    for u in units:
        if CFG.resume and record_is_valid(man.get(u.id), u):
            skipped += 1
        else:
            todo.append(u)
    total = len(units)
    log(f"[start] {label}: units total={total} already done (verified)={skipped} to fetch={len(todo)}")
    cnt = {"total": total, "skipped": skipped, "ok": 0, "empty": 0, "failed": 0, "bs": 0, "http": 0, "stopped": ""}
    today = time.strftime("%Y-%m-%d")
    done_today = sum(1 for r in man.values() if r["stage"] == (units[0].stage if units else "")
                     and str(r.get("ts", ""))[:10] == today and (r.get("n_http", 0) or r.get("n_bs_queries", 0)))
    consec = pauses = 0
    t_run = time.time()
    t_prog, n_prog = time.time(), 0
    bs0, http0 = BS.n, Http.count
    memo_group = None

    def progress(final=False):
        fetched = cnt["ok"] + cnt["empty"] + cnt["failed"]
        el = time.time() - t_run
        mean = el / fetched if fetched else None
        eta = mean * (len(todo) - fetched) if mean is not None else None
        rate = 100.0 * (cnt["ok"] + cnt["empty"]) / fetched if fetched else float("nan")
        log(f"[{'final' if final else 'progress'}] {label}: done={skipped + fetched}/{total} "
            f"(this run {fetched}: ok={cnt['ok']} empty={cnt['empty']} failed={cnt['failed']}; resumed-skip={skipped}) "
            f"success={rate:.1f}% mean={0 if mean is None else mean:.1f}s/unit ETA={_fmt_eta(eta)} "
            f"requests this run: baostock={BS.n - bs0} http={Http.count - http0} pauses={pauses}")

    try:
        for u in todo:
            if CFG.max_requests and (BS.n - bs0) + (Http.count - http0) >= CFG.max_requests:
                raise StopRun(f"--max-requests {CFG.max_requests} reached", 3)
            if CFG.daily_unit_cap:
                if time.strftime("%Y-%m-%d") != today:
                    today, done_today = time.strftime("%Y-%m-%d"), 0
                if done_today >= CFG.daily_unit_cap:
                    now = dt.datetime.now()
                    nxt = (now + dt.timedelta(days=1)).replace(hour=0, minute=1, second=0, microsecond=0)
                    log(f"[cap] {label}: daily unit cap {CFG.daily_unit_cap} reached; sleeping until {nxt}")
                    time.sleep((nxt - now).total_seconds())
                    today, done_today = time.strftime("%Y-%m-%d"), 0
            if u.memo_group != memo_group or not u.memo_group:
                Http.memo.clear()
                memo_group = u.memo_group
            t0 = time.time()
            b_start, h_start = BS.n, Http.count
            errors, status, df, extra, ratelimited = [], "failed", None, {}, False
            attempts = 0
            for attempt in range(len(CFG.backoff) + 1):
                attempts = attempt + 1
                t_att = time.time()
                try:
                    res = u.fetch()
                    df, extra = res if isinstance(res, tuple) else (res, {})
                    if df is None:
                        df = pd.DataFrame()
                    status = "ok" if len(df) else "empty"
                    break
                except NoData as e:
                    df, status, extra = None, "empty", {"no_data": str(e)[:300]}
                    break
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    Http.memo.clear()
                    msg = f"attempt {attempt}: {type(e).__name__}: {str(e)[:240]}"
                    if u.host != "baostock" and Http.last_resp:
                        msg += f" | last http status={Http.last_resp.get('status')} head={str(Http.last_resp.get('head'))[:80]!r}"
                    errors.append(msg)
                    log(f"[error] {u.stage}/{u.source}/{u.key} {msg}")
                    if "RateLimit" in type(e).__name__:
                        ratelimited = True
                        break
                    if isinstance(e, PermanentError):
                        break
                    if attempt < len(CFG.backoff):
                        time.sleep(CFG.backoff[attempt])
            fetch_s = time.time() - t_att
            rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "run_id": CFG.run_id, "stage": u.stage, "source": u.source,
                   "unit": u.key, "ok": status in ("ok", "empty"), "status": status, "rows": None, "cols": None,
                   "date_min": None, "date_max": None, "elapsed_s": round(time.time() - t0, 3),
                   "fetch_s": round(fetch_s, 3), "attempts": attempts, "n_bs_queries": BS.n - b_start,
                   "n_http": Http.count - h_start, "error": " || ".join(errors), "file": None, "bytes": None,
                   "sha256": None, "params": u.params, "params_hash": u.params_hash, "host": u.host,
                   "versions": versions, "extra": extra}
            if status in ("ok", "empty") and df is not None:
                rec["rows"], rec["cols"] = int(len(df)), int(df.shape[1])
                rec["date_min"], rec["date_max"] = _date_range(df, u.date_cols)
                if df.shape[1] > 0:
                    meta = {"stage": u.stage, "source": u.source, "unit": u.key, "params": u.params,
                            "fetched_at": rec["ts"], "versions": versions, "extra": extra}
                    try:
                        info = write_parquet(df, RAW / u.relpath, meta)
                        rec.update(file=u.relpath, **info)
                    except Exception as e:
                        rec.update(ok=False, status="failed", error=f"write failed: {type(e).__name__}: {str(e)[:240]}")
                        status = "failed"
            elif status == "empty":
                rec["rows"] = 0
            append_manifest(rec)
            cnt[status] += 1
            done_today += 1
            if status == "empty":
                log(f"[empty] {u.stage}/{u.source}/{u.key}: no record returned ({extra.get('no_data', 'zero rows')})")
            if status == "failed":
                consec += 1
                log(f"[failed] {u.stage}/{u.source}/{u.key} after {attempts} attempt(s); consecutive failures={consec}")
                if ratelimited or consec >= CFG.max_consec_fail:
                    pauses += 1
                    if pauses > CFG.max_pauses:
                        raise StopRun(f"{pauses - 1} pauses used and failures continue; stopping (host may be blocking)", 4)
                    wait = CFG.ratelimit_wait if ratelimited and consec < CFG.max_consec_fail else CFG.pause_seconds
                    log(f"[pause] {label}: {'rate-limit error' if ratelimited else str(consec) + ' consecutive failures'}; "
                        f"pause #{pauses} of at most {CFG.max_pauses}, sleeping {wait:.0f}s")
                    time.sleep(wait)
                    consec = 0
            else:
                consec = 0
            n_prog += 1
            if n_prog >= CFG.progress_units or time.time() - t_prog >= CFG.progress_seconds:
                progress()
                t_prog, n_prog = time.time(), 0
    except StopRun as e:
        cnt["stopped"] = str(e)
        progress(final=True)
        raise
    finally:
        cnt["bs"], cnt["http"] = BS.n - bs0, Http.count - http0
    progress(final=True)
    return cnt

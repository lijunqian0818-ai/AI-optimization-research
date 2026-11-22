#!/usr/bin/env python3
"""Download a paper, code repository, model or dataset into the project. Never runs what it downloads.

Usage (run from the project root; identifiers are the ones tools/search_resources.py prints):
    python tools/fetch_resource.py arxiv:2401.01234                 # paper PDF  -> literature/pdfs/
    python tools/fetch_resource.py pdf:https://example.org/x.pdf    # open-access PDF -> literature/pdfs/
    python tools/fetch_resource.py github:owner/repo                # shallow clone -> resources/code/
    python tools/fetch_resource.py hf-model:org/name                # -> resources/hf/model/
    python tools/fetch_resource.py hf-dataset:org/name --include "*.parquet"
    python tools/fetch_resource.py github:owner/repo --info         # show size and license only

Rules built into this script:
  * Papers (arxiv:, pdf:) download straight away (max 50 MB each).
  * Code, models and datasets download ONLY if their identifier is listed in
    resources/approved.txt. The lead adds a line there after the user approves the
    download list at a checkpoint.
  * Size cap per item: 5 GB by default (--max-gb to change, also needs user approval).
  * Every download is logged in resources/MANIFEST.md (source, size, license, where it went).
  * Nothing downloaded is executed or imported here.

Exit codes: 0 = done, 3 = not approved yet, 4 = too large, 1 = error.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "resources"
PDFS = ROOT / "literature" / "pdfs"
APPROVED = RES / "approved.txt"
MANIFEST = RES / "MANIFEST.md"
UA = {"User-Agent": "research-tools/1.0"}
PAPER_CAP_MB = 50
PICKLE_EXT = (".pkl", ".pickle", ".pt", ".pth", ".bin", ".ckpt", ".joblib")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")


def http_json(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return json.loads(r.read())


def approved(identifier: str) -> bool:
    if not APPROVED.is_file():
        return False
    lines = [l.split("#")[0].strip() for l in APPROVED.read_text(encoding="utf-8").splitlines()]
    return identifier in lines


def log(identifier: str, source: str, size_mb: float, license_: str, dest: Path, note: str = "") -> None:
    RES.mkdir(parents=True, exist_ok=True)
    if not MANIFEST.is_file():
        MANIFEST.write_text(
            "# Downloaded resources\n\n"
            "| Date | Identifier | Source | Size | License | Saved to | Notes |\n|---|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    with MANIFEST.open("a", encoding="utf-8") as f:
        f.write(f"| {dt.date.today()} | `{identifier}` | {source} | {size_mb:.1f} MB | {license_} | "
                f"`{dest.relative_to(ROOT).as_posix()}` | {note} |\n")


def fetch_pdf(identifier: str, url: str, name: str, info: bool) -> int:
    if not url.startswith("https://"):
        print("Only https:// links are accepted.", file=sys.stderr)
        return 1
    if info:
        print(f"{identifier}: paper PDF from {url} (papers need no approval, cap {PAPER_CAP_MB} MB)")
        return 0
    PDFS.mkdir(parents=True, exist_ok=True)
    dest = PDFS / (re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:120] + ".pdf")
    cap = PAPER_CAP_MB * 1024 * 1024
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
        data = r.read(cap + 1)
    if len(data) > cap:
        print(f"Larger than {PAPER_CAP_MB} MB; not saved.", file=sys.stderr)
        return 4
    if not data.startswith(b"%PDF"):
        print("The link did not return a PDF (probably a paywall or a web page). Not saved.", file=sys.stderr)
        return 1
    dest.write_bytes(data)
    log(identifier, url, len(data) / 1e6, "see paper", dest)
    print(f"saved {dest.relative_to(ROOT).as_posix()} ({len(data) / 1e6:.1f} MB)")
    return 0


def fetch_github(identifier: str, repo: str, info: bool, max_gb: float) -> int:
    meta = http_json(f"https://api.github.com/repos/{repo}")
    size_mb = meta.get("size", 0) / 1024
    lic = (meta.get("license") or {}).get("spdx_id") or "NO LICENSE"
    print(f"{identifier}: {size_mb:.1f} MB, license {lic}, ★{meta.get('stargazers_count')}, {meta.get('html_url')}")
    if info:
        return 0
    if size_mb > max_gb * 1024:
        print(f"Larger than the {max_gb} GB cap; not downloaded.", file=sys.stderr)
        return 4
    dest = RES / "code" / repo.replace("/", "__")
    if dest.exists():
        print(f"already present: {dest.relative_to(ROOT).as_posix()}")
        return 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(
        ["git", "clone", "--depth", "1", "--no-recurse-submodules", f"https://github.com/{repo}.git", str(dest)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if p.returncode != 0:
        print(p.stderr[-800:], file=sys.stderr)
        return 1
    note = "third-party code: read before running; run only what the user approved"
    if lic == "NO LICENSE":
        note += "; NO LICENSE = may not be reused or redistributed, reference only"
    log(identifier, meta.get("html_url", ""), size_mb, lic, dest, note)
    print(f"cloned to {dest.relative_to(ROOT).as_posix()}")
    return 0


def fetch_hf(identifier: str, kind: str, repo: str, include: list[str], info: bool, max_gb: float) -> int:
    from huggingface_hub import HfApi, snapshot_download

    meta = HfApi().repo_info(repo, repo_type=kind, files_metadata=True)
    files = [s for s in (meta.siblings or []) if not include or any(fnmatch.fnmatch(s.rfilename, p) for p in include)]
    size_mb = sum((s.size or 0) for s in files) / 1e6
    lic = next((t.split(":", 1)[1] for t in (meta.tags or []) if t.startswith("license:")), "NO LICENSE TAG")
    pickles = [s.rfilename for s in files if s.rfilename.lower().endswith(PICKLE_EXT)]
    print(f"{identifier}: {len(files)} files, {size_mb:.1f} MB, license {lic}")
    if pickles:
        print(f"  note: {len(pickles)} pickle-format file(s), e.g. {pickles[0]}")
    if info:
        return 0
    if size_mb > max_gb * 1024:
        print(f"Larger than the {max_gb} GB cap; not downloaded. Narrow it with --include.", file=sys.stderr)
        return 4
    dest = RES / "hf" / kind / repo.replace("/", "__")
    snapshot_download(repo, repo_type=kind, local_dir=str(dest), allow_patterns=include or None)
    note = ""
    if pickles:
        note = "contains pickle-format files: load only with weights_only=True, prefer .safetensors"
    log(identifier, f"https://huggingface.co/{'' if kind == 'model' else 'datasets/'}{repo}", size_mb, lic, dest, note)
    print(f"downloaded to {dest.relative_to(ROOT).as_posix()}")
    return 0


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("identifier", help="arxiv:ID | pdf:URL | github:owner/repo | hf-model:org/name | hf-dataset:org/name")
    ap.add_argument("--include", action="append", default=[], help="Hugging Face only: file pattern to download (repeatable)")
    ap.add_argument("--info", action="store_true", help="show size and license, download nothing")
    ap.add_argument("--max-gb", type=float, default=5.0)
    args = ap.parse_args()

    ident = args.identifier.strip()
    kind, _, rest = ident.partition(":")
    try:
        if kind == "arxiv":
            if not re.fullmatch(r"[A-Za-z0-9./-]+", rest):
                print("Bad arXiv id.", file=sys.stderr)
                return 1
            return fetch_pdf(ident, f"https://arxiv.org/pdf/{rest}", f"arxiv_{rest}", args.info)
        if kind == "pdf":
            return fetch_pdf(ident, rest, rest.split("//", 1)[-1], args.info)
        if kind in ("github", "hf-model", "hf-dataset"):
            if not ID_RE.match(rest):
                print("Identifier must look like owner/name.", file=sys.stderr)
                return 1
            if not args.info and not approved(ident):
                print(f"NOT APPROVED: {ident} is not listed in resources/approved.txt.\n"
                      "Put it on the download list (resources/DOWNLOAD_LIST.md) with its size and license, "
                      "and ask the user at the next checkpoint.", file=sys.stderr)
                return 3
            if kind == "github":
                return fetch_github(ident, rest, args.info, args.max_gb)
            return fetch_hf(ident, kind.split("-")[1], rest, args.include, args.info, args.max_gb)
        print("Unknown identifier type. See --help.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"FETCH FAILED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

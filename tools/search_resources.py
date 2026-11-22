#!/usr/bin/env python3
"""Search papers, code, models and datasets. Read-only: nothing is downloaded.

Usage (run from the project root):
    python tools/search_resources.py arxiv    "adaptive step size nonconvex" --limit 10
    python tools/search_resources.py papers   "learning to optimize convergence" --limit 10
    python tools/search_resources.py github   "learned optimizer pytorch" --limit 10
    python tools/search_resources.py hf-model   "optimization" --limit 10
    python tools/search_resources.py hf-dataset "combinatorial optimization" --limit 10

Sources:
    arxiv      arXiv API (preprints; always free to read)
    papers     OpenAlex (journals and conferences of all publishers, including Elsevier /
               ScienceDirect; shows DOI and a free open-access link when one exists)
    github     GitHub repository search (sorted by stars)
    hf-model / hf-dataset   Hugging Face Hub (sorted by downloads)

Every result prints an identifier that tools/fetch_resource.py accepts.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "research-tools/1.0"}


def get(url: str) -> bytes:
    """Fetch a URL, waiting and retrying when the service says we are asking too fast."""
    import time
    import urllib.error

    req = urllib.request.Request(url, headers=UA)
    for wait in (0, 5, 15, 30):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or wait == 30:
                raise
        except (TimeoutError, urllib.error.URLError):
            if wait == 30:
                raise
    raise RuntimeError("unreachable")


def short(text: str | None, n: int = 320) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def search_arxiv(q: str, limit: int) -> None:
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        # every word must appear; without the explicit AND, arXiv matches any single word
        {"search_query": " AND ".join(f"all:{w}" for w in q.split()), "max_results": limit, "sortBy": "relevance"}
    )
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(get(url))
    for e in root.findall("a:entry", ns):
        arxiv_id = e.findtext("a:id", "", ns).rsplit("/abs/", 1)[-1]
        authors = [a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)]
        print(f"- arxiv:{arxiv_id}  ({e.findtext('a:published', '', ns)[:10]})")
        print(f"  {short(e.findtext('a:title', '', ns), 200)}")
        print(f"  {', '.join(authors[:4])}{' et al.' if len(authors) > 4 else ''}")
        print(f"  {short(e.findtext('a:summary', '', ns))}")
        print(f"  https://arxiv.org/abs/{arxiv_id}\n")


def abstract_from_index(idx: dict | None) -> str:
    if not idx:
        return ""
    words = sorted((pos, w) for w, positions in idx.items() for pos in positions)
    return " ".join(w for _, w in words)


def search_papers(q: str, limit: int) -> None:
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
        {"search": q, "per-page": limit, "sort": "relevance_score:desc"}
    )
    for w in json.loads(get(url)).get("results", []):
        src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or "unknown venue"
        oa = (w.get("open_access") or {}).get("oa_url")
        authors = [a["author"]["display_name"] for a in w.get("authorships", [])]
        print(f"- {short(w.get('title'), 200)}  ({w.get('publication_year')})")
        print(f"  {', '.join(authors[:4])}{' et al.' if len(authors) > 4 else ''} | {src} | cited by {w.get('cited_by_count')}")
        print(f"  doi: {w.get('doi') or 'none'}")
        print(f"  free full text: {oa or 'NOT AVAILABLE (paywalled: ask the user to fetch it through the library)'}")
        print(f"  {short(abstract_from_index(w.get('abstract_inverted_index')))}\n")


def search_github(q: str, limit: int) -> None:
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
        {"q": q, "sort": "stars", "order": "desc", "per_page": limit}
    )
    for r in json.loads(get(url)).get("items", []):
        lic = (r.get("license") or {}).get("spdx_id") or "NO LICENSE"
        print(f"- github:{r['full_name']}  ★{r['stargazers_count']}  {r.get('language') or '?'}  "
              f"license: {lic}  size: {r['size'] / 1024:.1f} MB  updated: {r['pushed_at'][:10]}")
        print(f"  {short(r.get('description'))}")
        print(f"  {r['html_url']}\n")


def search_hf(q: str, limit: int, kind: str) -> None:
    from huggingface_hub import HfApi

    api = HfApi()
    items = (api.list_models if kind == "model" else api.list_datasets)(
        search=q, sort="downloads", limit=limit
    )
    for it in items:
        tags = [t for t in (it.tags or []) if t.startswith(("license:", "arxiv:", "task_categories:"))][:5]
        print(f"- hf-{kind}:{it.id}  downloads: {it.downloads}  likes: {it.likes}")
        print(f"  {' '.join(tags) or 'no license tag'}")
        print(f"  https://huggingface.co/{'' if kind == 'model' else 'datasets/'}{it.id}\n")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", choices=["arxiv", "papers", "github", "hf-model", "hf-dataset"])
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()
    limit = max(1, min(args.limit, 50))
    try:
        if args.source == "arxiv":
            search_arxiv(args.query, limit)
        elif args.source == "papers":
            search_papers(args.query, limit)
        elif args.source == "github":
            search_github(args.query, limit)
        else:
            search_hf(args.query, limit, args.source.split("-")[1])
    except Exception as e:  # network errors, rate limits
        print(f"SEARCH FAILED ({args.source}): {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

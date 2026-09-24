"""
Fetch jobs from the Jooble API for Indonesia, across a list of keywords.

Requires the JOOBLE_API_KEY environment variable (get a free key by
registering at https://id.jooble.org/api/about — free tier is capped
at 500 requests total, and each keyword below costs one request per run).

Usage: python scripts/fetch_jooble.py > data/_jooble_jobs.json
Skips silently (prints an empty list) if JOOBLE_API_KEY isn't set, so
the rest of the pipeline still works without it.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
import yaml

from common import Job, clean_ws, session

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "keywords.yml"


def main() -> None:
    api_key = os.environ.get("JOOBLE_API_KEY", "").strip()
    if not api_key:
        print("JOOBLE_API_KEY not set — skipping Jooble source.", file=sys.stderr)
        print(json.dumps([]))
        return

    cfg = yaml.safe_load(CONFIG.read_text())
    keywords = cfg.get("keywords") or []

    sess = session()
    url = f"https://jooble.org/api/{api_key}"
    jobs: list[Job] = []

    for kw in keywords:
        print(f"Searching Jooble for '{kw}' in Indonesia...", file=sys.stderr)
        try:
            r = sess.post(url, json={"keywords": kw, "location": "Indonesia"}, timeout=20)
        except requests.exceptions.RequestException as e:
            print(f"  [skip] '{kw}': {e}", file=sys.stderr)
            continue
        if r.status_code != 200:
            print(f"  [skip] '{kw}': HTTP {r.status_code}", file=sys.stderr)
            continue
        payload = r.json()
        for raw in payload.get("jobs", []):
            jobs.append(Job(
                title=clean_ws(raw.get("title", "")),
                company=clean_ws(raw.get("company", "") or "Unknown"),
                location=clean_ws(raw.get("location", "") or "Indonesia"),
                url=raw.get("link", ""),
                source="jooble",
                posted_at=(raw.get("updated") or "")[:10] or None,
            ))

    print(f"Matched {len(jobs)} jobs from Jooble across {len(keywords)} keywords.", file=sys.stderr)
    print(json.dumps([j.as_dict() for j in jobs], ensure_ascii=False))


if __name__ == "__main__":
    main()

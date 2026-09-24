"""
Fetch jobs from companies' public Greenhouse / Lever job-board APIs and
keep only postings whose location looks like Indonesia.

Usage: python scripts/fetch_ats.py > data/_ats_jobs.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from common import Job, clean_ws, matches_indonesia, session

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "companies.yml"


def fetch_greenhouse(sess, name: str, slug: str) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    r = sess.get(url, timeout=20)
    if r.status_code != 200:
        print(f"  [skip] greenhouse/{slug}: HTTP {r.status_code}", file=sys.stderr)
        return []
    return r.json().get("jobs", [])


def fetch_lever(sess, name: str, slug: str) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    r = sess.get(url, timeout=20)
    if r.status_code != 200:
        print(f"  [skip] lever/{slug}: HTTP {r.status_code}", file=sys.stderr)
        return []
    return r.json()


def main() -> None:
    cfg = yaml.safe_load(CONFIG.read_text())
    companies = cfg.get("companies") or []
    loc_keywords = cfg.get("location_keywords") or ["indonesia"]
    title_keywords = cfg.get("title_keywords") or []  # empty = keep every title

    def matches_title(title: str) -> bool:
        if not title_keywords:
            return True
        t = (title or "").lower()
        return any(kw.lower().strip() in t for kw in title_keywords)

    sess = session()
    jobs: list[Job] = []

    for c in companies:
        name, ats, slug = c["name"], c["ats"], c["slug"]
        print(f"Fetching {name} ({ats}/{slug})...", file=sys.stderr)

        if ats == "greenhouse":
            for raw in fetch_greenhouse(sess, name, slug):
                loc = clean_ws((raw.get("location") or {}).get("name", ""))
                title = clean_ws(raw.get("title", ""))
                if not matches_indonesia(loc, loc_keywords) or not matches_title(title):
                    continue
                jobs.append(Job(
                    title=title,
                    company=name,
                    location=loc,
                    url=raw.get("absolute_url", ""),
                    source="greenhouse",
                    posted_at=(raw.get("first_published") or raw.get("updated_at") or "")[:10] or None,
                ))

        elif ats == "lever":
            for raw in fetch_lever(sess, name, slug):
                categories = raw.get("categories") or {}
                all_locations = categories.get("allLocations") or []
                loc = clean_ws(categories.get("location") or (all_locations[0] if all_locations else ""))
                title = clean_ws(raw.get("text", ""))
                if not matches_indonesia(loc, loc_keywords) or not matches_title(title):
                    continue
                jobs.append(Job(
                    title=title,
                    company=name,
                    location=loc or "Indonesia",
                    url=raw.get("hostedUrl", ""),
                    source="lever",
                    posted_at=None,
                ))
        else:
            print(f"  [skip] {name}: unknown ats '{ats}'", file=sys.stderr)

    print(f"Matched {len(jobs)} Indonesia-located jobs from {len(companies)} companies.", file=sys.stderr)
    print(json.dumps([j.as_dict() for j in jobs], ensure_ascii=False))


if __name__ == "__main__":
    main()

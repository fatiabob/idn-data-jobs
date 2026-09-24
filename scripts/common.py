"""
Shared helpers: HTTP session, job record shape, dedupe.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

import requests

USER_AGENT = "id-job-radar/1.0 (+https://github.com/; daily job list for Indonesia)"

DEFAULT_TIMEOUT = 20


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return s


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str  # "greenhouse", "lever", "jooble"
    posted_at: Optional[str] = None  # ISO date string, if known
    id: str = field(default="", repr=False)

    def __post_init__(self):
        if not self.id:
            basis = f"{self.company}|{self.title}|{self.url}".lower()
            self.id = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]

    def as_dict(self) -> dict:
        return asdict(self)


def matches_indonesia(location: str, keywords: list[str]) -> bool:
    loc = (location or "").lower()
    return any(kw.lower() in loc for kw in keywords)


def clean_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def dedupe(jobs: list[Job]) -> list[Job]:
    seen: dict[str, Job] = {}
    for j in jobs:
        key = j.url or j.id
        if key not in seen:
            seen[key] = j
    return list(seen.values())

"""
Orchestrates a full refresh:
  1. run fetch_ats.py and fetch_jooble.py
  2. merge + dedupe
  3. write data/jobs.json and data/jobs.csv
  4. rewrite the job table inside README.md (between the
     <!-- JOBS:START --> / <!-- JOBS:END --> markers)

Usage: python scripts/run.py
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
README = ROOT / "README.md"
JOBS_JSON = DATA_DIR / "jobs.json"
JOBS_CSV = DATA_DIR / "jobs.csv"

START_MARK = "<!-- JOBS:START -->"
END_MARK = "<!-- JOBS:END -->"

MAX_ROWS_IN_README = 300  # keep the README readable; full set lives in jobs.json/csv


def run_fetcher(script: str) -> list[dict]:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        capture_output=True, text=True, cwd=ROOT / "scripts",
    )
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    if proc.returncode != 0:
        print(f"[warn] {script} exited {proc.returncode}, treating as 0 jobs", file=sys.stderr)
        return []
    try:
        return json.loads(proc.stdout.strip() or "[]")
    except json.JSONDecodeError:
        print(f"[warn] {script} produced invalid JSON, treating as 0 jobs", file=sys.stderr)
        return []


def dedupe(jobs: list[dict]) -> list[dict]:
    seen = {}
    for j in jobs:
        key = j.get("url") or j.get("id")
        if key and key not in seen:
            seen[key] = j
    return list(seen.values())


def sort_key(j: dict):
    # newest-first; jobs with no known date sink to the bottom but keep company order stable
    return (j.get("posted_at") or "", j.get("company", ""), j.get("title", ""))


def write_json(jobs: list[dict]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    JOBS_JSON.write_text(json.dumps(jobs, ensure_ascii=False, indent=2) + "\n")


def write_csv(jobs: list[dict]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    fields = ["title", "company", "location", "url", "source", "posted_at", "id"]
    with JOBS_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for j in jobs:
            w.writerow({k: j.get(k, "") for k in fields})


def build_table(jobs: list[dict]) -> str:
    if not jobs:
        return "_No matching Indonesia jobs found in the last run — check back tomorrow, or see the workflow logs._\n"

    rows = jobs[:MAX_ROWS_IN_README]
    lines = [
        "| Company | Role | Location | Posted | Source |",
        "|---|---|---|---|---|",
    ]
    for j in rows:
        title = (j.get("title") or "").replace("|", "/")
        company = (j.get("company") or "").replace("|", "/")
        location = (j.get("location") or "").replace("|", "/")
        url = j.get("url") or ""
        posted = j.get("posted_at") or "—"
        source = j.get("source") or ""
        role_cell = f"[{title}]({url})" if url else title
        lines.append(f"| {company} | {role_cell} | {location} | {posted} | {source} |")

    footer = f"\n_Showing {len(rows)} of {len(jobs)} matched roles. Full list: [`data/jobs.json`](data/jobs.json) / [`data/jobs.csv`](data/jobs.csv)._\n"
    return "\n".join(lines) + "\n" + footer


def update_readme(table_md: str) -> None:
    from datetime import datetime, timezone
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    text = README.read_text()
    if START_MARK not in text or END_MARK not in text:
        raise SystemExit(f"README.md is missing {START_MARK} / {END_MARK} markers")

    before, rest = text.split(START_MARK, 1)
    _, after = rest.split(END_MARK, 1)

    new_block = f"{START_MARK}\n_Last refreshed: {stamp}_\n\n{table_md}\n{END_MARK}"
    README.write_text(before + new_block + after)


def main() -> None:
    print("Fetching company career pages (Greenhouse/Lever)...", file=sys.stderr)
    ats_jobs = run_fetcher("fetch_ats.py")

    print("Fetching Jooble...", file=sys.stderr)
    jooble_jobs = run_fetcher("fetch_jooble.py")

    all_jobs = dedupe(ats_jobs + jooble_jobs)
    all_jobs.sort(key=sort_key, reverse=True)

    print(f"Total matched jobs after dedupe: {len(all_jobs)}", file=sys.stderr)

    write_json(all_jobs)
    write_csv(all_jobs)
    update_readme(build_table(all_jobs))

    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()

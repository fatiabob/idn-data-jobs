# id-job-radar 🇮🇩

A daily-refreshing list of job openings in Indonesia, built for friends
back home who are job hunting. Inspired by [SimplifyJobs/New-Grad-Positions](https://github.com/SimplifyJobs/New-Grad-Positions) —
same idea (a GitHub Actions bot that keeps a README table fresh), aimed
at Indonesia instead of US new-grad roles.

Every day a GitHub Actions workflow:
1. Pulls open roles from a curated list of companies' public career-page
   APIs (Greenhouse / Lever), keeping only ones located in Indonesia.
2. Pulls broader results from the [Jooble](https://jooble.org) job
   search API for Indonesia.
3. Dedupes everything, writes the full list to
   [`data/jobs.json`](data/jobs.json) / [`data/jobs.csv`](data/jobs.csv),
   and rewrites the table below.
4. Commits the changes automatically if anything changed.

## Jobs

<!-- JOBS:START -->
_Last refreshed: 2026-09-25 05:42 UTC_

| Company | Role | Location | Posted | Source |
|---|---|---|---|---|
| Xendit | [IT GRC Analyst](https://job-boards.greenhouse.io/xendit/jobs/7731687003) | Jakarta, Indonesia | 2026-06-18 | greenhouse |

_Showing 1 of 1 matched roles. Full list: [`data/jobs.json`](data/jobs.json) / [`data/jobs.csv`](data/jobs.csv)._

<!-- JOBS:END -->

## Getting this running on your own copy

1. **Push this to a new GitHub repo** (public, so the Action can commit
   back to it for free).
2. **(Optional but recommended) Get a free Jooble API key** for
   Indonesia at `https://id.jooble.org/api/about`, then add it as a
   repo secret: **Settings → Secrets and variables → Actions → New
   repository secret**, name it `JOOBLE_API_KEY`. Without this, the
   Jooble source is skipped and you still get the Greenhouse/Lever
   results.
3. **Edit `config/companies.yml`** to add the companies you want
   tracked — see the comments in that file for how to find each
   company's Greenhouse/Lever slug. Only `Xendit` is verified out of
   the box; add more as you confirm them.
4. **Edit `config/keywords.yml`** to change which roles Jooble searches
   for.
5. The workflow (`.github/workflows/refresh.yml`) runs daily at
   **01:00 UTC (08:00 WIB)** and can also be triggered manually from
   the **Actions** tab (**Run workflow**).

## Running it locally

```bash
pip install -r requirements.txt
export JOOBLE_API_KEY=your_key_here   # optional
python scripts/run.py
```

This updates `data/jobs.json`, `data/jobs.csv`, and the table in this
README in place.

## Notes

- Greenhouse/Lever are queried directly against each company's own
  public job-board API — no scraping of rendered HTML, so it's fast
  and stable until a company switches ATS.
- Location matching is a simple keyword filter (`config/companies.yml`
  → `location_keywords`) against whatever location string the ATS
  reports, so a role listed as "Jakarta, Singapore" will still match.
- The Jooble free tier is capped at 500 requests total for the API
  key's lifetime, and this project uses one request per keyword per
  run — trim `config/keywords.yml` or lower the run frequency in the
  workflow if you're worried about hitting that.

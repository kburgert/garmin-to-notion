# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Syncs Garmin Connect data (activities, personal records, daily steps, sleep) to Notion databases. Designed to run as a daily GitHub Actions cron job, but can also be run locally.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run individual scripts (requires .env with credentials)
python garmin-activities.py    # Sync activities to NOTION_DB_ID
python personal-records.py     # Sync PRs to NOTION_PR_DB_ID
python daily-steps.py          # Sync yesterday's steps to NOTION_STEPS_DB_ID
python sleep-data.py           # Sync last night's sleep to NOTION_SLEEP_DB_ID
```

No build step, no test framework, no linter configured. Python 3.11.

## Environment Variables

Required: `GARMIN_EMAIL`, `GARMIN_PASSWORD`, `NOTION_TOKEN`, `NOTION_DB_ID`, `NOTION_PR_DB_ID`

Optional: `NOTION_STEPS_DB_ID`, `NOTION_SLEEP_DB_ID`, `GARMIN_ACTIVITIES_FETCH_LIMIT` (default: 1000)

Copy `.example.env` to `.env` and fill in values for local development.

## Architecture

Four independent scripts sharing the same pattern:
1. Initialize `Garmin` client and login
2. Initialize Notion `Client`
3. Fetch data from Garmin Connect
4. Check if entries already exist in Notion (by date/type/name matching)
5. Create new entries or update existing ones

Each script targets a separate Notion database and is self-contained with its own `main()`.

- **garmin-activities.py** — Fetches all activities (up to fetch limit), deduplicates via time window ±5 min + activity type + name. Handles activity type mapping (e.g., "Treadmill Running" → "Running"), pace formatting, training effect labels.
- **personal-records.py** — Fetches personal records, archives old PRs when new ones are found, creates new entries with emoji icons and Unsplash cover images. Filters out typeId 16 (garbage entries).
- **daily-steps.py** — Fetches yesterday's step count only. Simple create-or-update logic.
- **sleep-data.py** — Fetches last night's sleep. Skips entries with 0 total sleep. Tracks sleep stages (deep, light, REM, awake).

## GitHub Actions

`.github/workflows/sync_garmin_to_notion.yml` runs daily at 1 AM UTC (`cron: '0 1 * * *'`). It executes `garmin-activities.py`, `personal-records.py`, and `daily-steps.py` (not sleep-data.py since commit 032a6ba).

## Key Dependencies

- `garminconnect` — Garmin Connect API wrapper (pinned >=0.2.19,<0.3)
- `notion-client` — Official Notion SDK (==2.2.1)
- `python-dotenv` — Local .env loading

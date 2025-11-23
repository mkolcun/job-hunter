# Scripts Directory

Utility scripts for job scraping project.

## Scripts

- **consolidate_jobs.py** - Consolidates jobs from all sessions into unified database
- **consolidate_sessions.py** - Session consolidation utilities
- **deduplicate_jobs.py** - Removes duplicate jobs from database
- **run_extraction.py** - Job extraction runner

## Usage

These scripts are called by Claude Code skills:
- consolidator skill uses consolidate_jobs.py
- deduplicator skill uses deduplicate_jobs.py

You can also run them directly:
```bash
cd scripts
python3 consolidate_jobs.py
```

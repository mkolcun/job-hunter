---
name: deduplicator
description: Finds and removes duplicate jobs from consolidated database. Works on output/database/jobs_master.json.
allowed-tools: Read, Write, Bash, Grep
restrictions:
  write_allowed_extensions: [".json", ".csv", ".md"]
  write_allowed_directories: ["output/database/", "output/reports/"]
  write_forbidden_extensions: [".py", ".sh", ".js", ".ts"]
---

# Job Deduplicator

## Purpose
Process jobs_master.json and remove duplicates based on URL and fuzzy matching.

## How It Works

### Step 1: Load Master Database

```bash
jq '.jobs | length' output/database/jobs_master.json
```

### Step 2: Find Exact Duplicates (Same URL)

```bash
jq -r '.jobs[].url' output/database/jobs_master.json | sort | uniq -d
```

These are 99% duplicates.

### Step 3: Find Fuzzy Duplicates

Create normalized keys (company|title|location) and find matches:

```bash
jq -r '.jobs[] | "\(.company | ascii_downcase)|\(.title | ascii_downcase)|\(.location | ascii_downcase)"' output/database/jobs_master.json | sort | uniq -d
```

### Step 4: Create Unique Jobs List

Keep first occurrence of each duplicate, mark others.

### Step 5: Save Results

- **jobs_unique.json** - Only unique jobs
- **jobs_duplicates.json** - All duplicates with reasons
- **deduplication_report.md** - Stats and analysis

## Example Execution

```
User: "Remove duplicates from job database"

You:
1. Check if jobs_master.json exists
2. Count total jobs
3. Find URL duplicates
4. Find fuzzy duplicates
5. Create unique list
6. Save files
7. Report: "X jobs → Y unique, Z duplicates (W%)"
```

## Duplicate Detection Logic

**Exact:** Same URL
**High:** Same company.name + title + location.city (normalized)
**Medium:** Similar title + company (80%+ match)

Keep whichever has more fields populated.

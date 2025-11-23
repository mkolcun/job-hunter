---
name: consolidator
description: Consolidates jobs from multiple scraping sessions into unified database. Reads actual session folders and creates master job database.
allowed-tools: Read, Write, Bash, Grep
restrictions:
  write_allowed_extensions: [".json", ".csv", ".md"]
  write_allowed_directories: ["output/database/", "output/reports/"]
  write_forbidden_extensions: [".py", ".sh", ".js", ".ts"]
---

# Job Consolidator

## Purpose
Read all session directories and consolidate jobs into one master database.

## How It Works

When user asks to consolidate jobs, you will:

### Step 1: Find All Sessions

```bash
find output/ -maxdepth 1 -type d -name "*session*" | grep -v database
```

### Step 2: For Each Session, Load Jobs

**Check what files exist:**
```bash
ls output/SESSION_NAME/
```

**Three possible structures:**

1. **api_response_all.json** (like data_analyst_session_scrape_20251120_182316)
   - Read this file, it's array of 2600+ jobs
   - Each job has: id, uid, company.name, location.city, application_url, etc.

2. **jobs_aggregated.json** (like session_scrape_20251120_184825)
   - Has jobs_summary array with processed jobs
   - Each has: id, title, company, location, file

3. **jobs/ directory** (like session_scrape_20251121_181317)
   - Individual JSON files per job
   - Read each one, combine them

### Step 3: Extract Key Fields

From each job, extract:
- id (job.id or job.uid or job.job_id)
- url (job.application_url or job.url)
- title (job.slug or job.title or job.data.title.value)
- company (job.company.name or job.company or job.data.company.value)
- location (job.location.city or job.location or job.data.location.value)

### Step 4: Detect Duplicates

**Exact match:** Same URL = duplicate
**Fuzzy match:** Same company+title+location (normalized) = likely duplicate

Normalize by:
- Lowercase
- Remove "gmbh", "ag", "ltd", "(m/w/d)"
- Trim spaces

### Step 5: Save Outputs

Create in `output/database/`:

1. **jobs_master.json** - All unique jobs
2. **jobs_duplicates.json** - All duplicates found
3. **jobs_unique.csv** - CSV export of unique jobs

## Example Execution

```
User: "Consolidate all job sessions"

You:
1. Find sessions:
   find output/ -maxdepth 1 -type d -name "*session*" | grep -v database

2. For each session found:
   - Check structure: ls output/SESSION_NAME/
   - Read appropriate file(s)
   - Extract jobs

3. Use jq to process JSON and detect duplicates

4. Write consolidated results to output/database/

5. Report to user:
   "Found X sessions, Y total jobs, Z unique jobs, duplicates: W%"
```

## Commands You'll Use

**Count jobs in api_response_all.json:**
```bash
jq 'length' output/SESSION/api_response_all.json
```

**Extract company names:**
```bash
jq -r '.[].company.name' output/SESSION/api_response_all.json
```

**Find duplicates by URL:**
```bash
jq -r '.[].application_url' output/*/api_response_all.json | sort | uniq -d
```

**Combine all jobs:**
```bash
jq -s 'add' output/SESSION1/file.json output/SESSION2/file.json > output/database/jobs_master.json
```

## Important

- Use actual Bash commands with jq
- Read actual files
- Write actual JSON outputs
- No theoretical bullshit, just process the data

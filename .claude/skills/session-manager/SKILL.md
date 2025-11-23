---
name: session-manager
description: Manages scraping sessions, including starting new sessions, resuming interrupted sessions, and handling checkpoints. Use when starting a scrape or recovering from interruptions.
allowed-tools: Read, Write, Bash, Grep
restrictions:
  write_allowed_extensions: [".json", ".txt", ".md"]
  write_allowed_directories: ["output/", "output/session_*/", "output/checkpoints/"]
  write_forbidden_extensions: [".py", ".sh", ".js", ".ts", ".rb", ".php", ".exe", ".bat"]
---

**SECURITY: File Writing Restrictions**
- ✅ Write `.json` (session data), `.txt` (logs), `.md` (reports)
- ✅ Write to `output/` directories only
- ❌ CANNOT create scripts or executable files

# Scraping Session Manager

## Purpose
Manage the full lifecycle of scraping sessions:
- Initialize new sessions with unique IDs
- Resume interrupted sessions from checkpoints
- Manage URL queues and processing status
- Track progress and statistics
- Generate session reports

## When to Use This Skill

Use this skill when:
- Starting a new scraping session
- Resuming an interrupted session
- Checking session status or progress
- Generating completion reports
- Managing multiple concurrent sessions

## Session Management Commands

### 1. Start New Session

**Command**: Start a new scraping session

**Process**:
1. Generate unique session ID: `scrape_YYYYMMDD_HHMMSS`
2. Ask user for:
   - Target website URL
   - Whether to use existing schema or create new one
   - Maximum pages to scrape (optional limit)
3. Create session directory structure:
```
output/
└── session_[SESSION_ID]/
    ├── jobs/              # Individual job JSON files
    ├── jobs.json          # Aggregated jobs file
    ├── url_queue.json     # URL processing queue
    ├── incomplete/        # Jobs with missing required data
    ├── failed/            # Failed URLs with error details
    └── checkpoints/       # Checkpoint files for resume
```

4. Initialize checkpoint file:
```json
{
  "session_id": "scrape_20251119_143000",
  "start_time": "2025-11-19T14:30:00Z",
  "website": "https://example-jobs.com",
  "schema_path": "config/extraction_schema.json",
  "status": "active",
  "stats": {
    "urls_discovered": 0,
    "urls_processed": 0,
    "urls_pending": 0,
    "jobs_extracted": 0,
    "jobs_incomplete": 0,
    "jobs_failed": 0
  },
  "current_url": null,
  "last_update": "2025-11-19T14:30:00Z"
}
```

5. Begin scraping process

**Usage**:
```
Start a new scraping session for https://example.com/jobs
```

### 2. Resume Session

**Command**: Resume an interrupted session

**Process**:
1. Find latest checkpoint: `output/checkpoints/checkpoint_latest.json`
2. Load checkpoint data:
   - Session ID
   - Last processed URL
   - URL queue with status
   - Statistics
3. Verify data integrity:
   - Check if session directory exists
   - Validate checkpoint file
   - Count already processed jobs
4. Ask user for confirmation:
```
📂 Found Session: scrape_20251119_143000
Started: 2025-11-19 14:30
Progress: 87/450 URLs processed (19%)
Last URL: https://example.com/job/12387

Resume this session? (y/n)
```

5. Resume from last checkpoint:
   - Load URL queue
   - Skip processed URLs
   - Continue from last pending URL
   - Update existing checkpoint

**Usage**:
```
Resume the interrupted scraping session
```

**Resume specific session**:
```
Resume session scrape_20251119_143000
```

### 3. Session Status

**Command**: Check current session status

**Process**:
1. Load active checkpoint
2. Calculate statistics:
   - URLs processed vs remaining
   - Jobs extracted vs incomplete
   - Processing speed (jobs/minute)
   - Estimated time remaining
   - Quality metrics (avg confidence, completeness)
3. Display formatted status:

```
📊 Session Status: scrape_20251119_143000
=============================================
Started: 2025-11-19 14:30 (1h 23m ago)
Website: https://example-jobs.com

Progress:
  URLs: 145/450 processed (32%)
  Jobs: 132 extracted | 13 incomplete | 5 failed

Quality:
  Avg Completeness: 76%
  Avg Confidence: 72%
  Grade: B

Speed:
  Current: 1.8 jobs/min
  ETA: ~2h 50m remaining

Latest: Processing job #146
URL: https://example-jobs.com/job/12446
```

**Usage**:
```
Show current scraping session status
```

### 4. List Sessions

**Command**: List all scraping sessions

**Process**:
1. Scan `output/checkpoints/` for checkpoint files
2. Read metadata from each checkpoint
3. Display sessions in table format:

```
📁 Scraping Sessions
===============================================================================
ID                        | Started          | Status    | Progress    | Jobs
--------------------------|------------------|-----------|-------------|------
scrape_20251119_143000   | Nov 19, 14:30   | active    | 145/450 32% | 132
scrape_20251118_093000   | Nov 18, 09:30   | complete  | 850/850 100%| 815
scrape_20251117_161500   | Nov 17, 16:15   | paused    | 67/320 21%  | 58
```

**Usage**:
```
List all scraping sessions
```

### 5. Generate Report

**Command**: Generate completion report for a session

**Process**:
1. Load session checkpoint and all job data
2. Calculate comprehensive statistics:
   - Total jobs extracted
   - Data completeness by field
   - Confidence scores by field
   - Processing time statistics
   - Success/failure rates
   - Quality distribution (A, B, C, D grades)
3. Generate markdown report: `output/reports/report_[SESSION_ID].md`

**Report Structure**:
```markdown
# Scraping Session Report

**Session ID**: scrape_20251119_143000
**Started**: 2025-11-19 14:30
**Completed**: 2025-11-19 18:45
**Duration**: 4h 15m

## Summary

- **Total URLs Processed**: 450
- **Jobs Extracted**: 412 (91.6%)
- **Incomplete Jobs**: 33 (7.3%)
- **Failed Jobs**: 5 (1.1%)
- **Processing Speed**: 1.8 jobs/minute

## Quality Metrics

### Overall Quality
- **Average Completeness**: 78%
- **Average Confidence**: 74%
- **Quality Grade**: B+

### Field Coverage

| Field              | Found  | Avg Confidence | Quality |
|--------------------|--------|----------------|---------|
| title              | 100%   | 95%           | A+      |
| company            | 100%   | 93%           | A+      |
| location           | 98%    | 88%           | A       |
| salary             | 71%    | 73%           | B       |
| description        | 95%    | 91%           | A       |
| requirements       | 82%    | 78%           | B+      |
| contactEmail       | 48%    | 68%           | C+      |
| benefits           | 35%    | 61%           | C       |

### Quality Distribution

- **A Grade** (90-100%): 156 jobs (38%)
- **B Grade** (75-89%): 189 jobs (46%)
- **C Grade** (60-74%): 58 jobs (14%)
- **D Grade** (<60%): 9 jobs (2%)

## Processing Statistics

- **Total Processing Time**: 4h 15m
- **Average Time per Job**: 34.2 seconds
- **Fastest Job**: 8.3 seconds
- **Slowest Job**: 2m 14s

## Issues & Failures

### Failed URLs (5)
1. https://example.com/job/12445 - Timeout
2. https://example.com/job/12489 - CAPTCHA unsolvable
3. https://example.com/job/12501 - Page not found (404)
4. https://example.com/job/12567 - Rate limit exceeded
5. https://example.com/job/12689 - Invalid HTML structure

### Common Missing Fields
1. **contactEmail** (52% missing) - Consider adding more email patterns
2. **benefits** (65% missing) - Consider making optional or improving section detection
3. **salary** (29% missing) - Add more currency format variations

## Recommendations

1. **Improve email extraction**: Only 48% coverage
   - Add more email pattern variations
   - Check for "mailto:" links
   - Look in footer/contact sections

2. **Optimize processing speed**: Current 34s/job average
   - Reduce page load timeouts
   - Implement parallel processing
   - Cache repeated data

3. **Handle rate limiting**: 1 failure due to rate limiting
   - Increase delay between requests
   - Implement better backoff strategy

## Output Files

- **Jobs Data**: `output/session_scrape_20251119_143000/jobs.json`
- **Incomplete Jobs**: `output/session_scrape_20251119_143000/incomplete/`
- **Failed URLs**: `output/session_scrape_20251119_143000/failed/failed_urls.json`
```

**Usage**:
```
Generate report for the current session
```

```
Generate report for session scrape_20251119_143000
```

### 6. Clean Up Session

**Command**: Archive or delete old sessions

**Process**:
1. List sessions older than specified date
2. Ask for confirmation
3. Archive or delete:
   - **Archive**: Move to `output/archive/[SESSION_ID].tar.gz`
   - **Delete**: Remove session directory

**Usage**:
```
Archive sessions older than 30 days
```

```
Delete failed session scrape_20251117_161500
```

## Session File Structure

### Directory Layout
```
output/
├── session_20251119_143000/
│   ├── jobs/
│   │   ├── 12345.json
│   │   ├── 12346.json
│   │   └── ...
│   ├── jobs.json              # Aggregated file
│   ├── url_queue.json         # URL queue with status
│   ├── incomplete/
│   │   ├── 12567.json         # Jobs with missing required fields
│   │   └── ...
│   ├── failed/
│   │   └── failed_urls.json   # URLs that failed processing
│   └── checkpoints/
│       ├── checkpoint_latest.json
│       ├── checkpoint_50.json  # Backup every 50 jobs
│       └── checkpoint_100.json
├── checkpoints/
│   └── checkpoint_latest.json  # Symlink to latest session
└── reports/
    └── report_20251119_143000.md
```

### URL Queue Format
```json
{
  "session_id": "scrape_20251119_143000",
  "source_url": "https://example.com/jobs",
  "total_urls": 450,
  "urls": [
    {
      "url": "https://example.com/job/12345",
      "status": "completed",
      "job_id": "12345",
      "processed_at": "2025-11-19T14:35:23Z",
      "processing_time": 28.5,
      "quality_grade": "B+"
    },
    {
      "url": "https://example.com/job/12346",
      "status": "pending",
      "discovered_at": "2025-11-19T14:30:15Z"
    },
    {
      "url": "https://example.com/job/12347",
      "status": "failed",
      "error": "Timeout after 30 seconds",
      "failed_at": "2025-11-19T14:38:12Z"
    }
  ]
}
```

## Best Practices

1. **Always checkpoint**: Save progress every 10 jobs minimum
2. **Unique session IDs**: Use timestamp-based IDs to avoid conflicts
3. **Preserve failed data**: Keep failed URLs and incomplete jobs for analysis
4. **Regular reports**: Generate reports to track quality trends
5. **Archive old sessions**: Keep output directory clean
6. **Multiple sessions**: Can run multiple sessions in parallel for different sites

## Error Handling

- **Checkpoint corrupted**: Create new checkpoint from job files
- **Session directory missing**: Cannot resume, start new session
- **URL queue lost**: Rebuild from processed job files
- **Duplicate session ID**: Append random suffix to make unique

## Usage Examples

**Start fresh**:
```
Start a new scraping session for https://linkedin.com/jobs/search?keywords=engineer
```

**Resume interrupted**:
```
Resume the scraping session
```

**Check progress**:
```
Show current session status
```

**Generate final report**:
```
Generate report for the completed session
```

**List all**:
```
Show me all scraping sessions
```

**Clean up**:
```
Archive sessions older than 60 days
```

# Job Hunter - System Architecture

Complete technical architecture of the AI-powered job scraping and application automation system.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        JOB HUNTER SYSTEM                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   SCRAPING   │ -> │ CONSOLIDATE  │ -> │  FILTERING   │ -> │ PERSONALIZE  │
│   PIPELINE   │    │  & DEDUPE    │    │   PIPELINE   │    │   PIPELINE   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       │                    │                   │                    │
       ↓                    ↓                   ↓                    ↓
  Session Data        Master Database     Filtered Jobs        Applications
  (per session)       (deduplicated)      (criteria match)     (personalized)
```

## Component Architecture

### 1. Scraping Pipeline

**Command:** `/scrape`
**Skills:** session-manager, page-classifier, url-extractor, data-extractor, antibot-handler

```
User Input (URL) → Session Init → Page Classification
                                         │
                           ┌─────────────┴─────────────┐
                           │                           │
                      Job Detail                  Job List
                           │                           │
                      Extract Job              Extract URLs
                           │                           │
                           └──────────┬────────────────┘
                                      │
                              For Each Job URL:
                                      │
                              ┌───────┴───────┐
                              │               │
                         CAPTCHA Check    HTML Fetch
                              │               │
                         Data Extract    Validation
                              │               │
                         Save to Jobs    Update Checkpoint
                              │
                      Session Complete
```

**Output:**
```
output/session_[ID]/
├── jobs/*.json              # Extracted jobs
├── incomplete/*.json        # Partial extractions
├── failed/failed_urls.json  # Failed URLs
└── checkpoint.json          # Session state
```

### 2. Consolidation Pipeline

**Command:** `/consolidate`
**Skills:** consolidator, deduplicator

```
All Session Dirs → Load All Jobs → Detect Duplicates
                                          │
                                   (URL match OR
                                    Title similarity > 80%)
                                          │
                              Remove Duplicates → Master DB
                                          │
                                   Generate Stats
```

**Algorithm:**
```python
for each job:
    if URL exists in master: skip (duplicate)
    elif title_similarity(job, existing) > 0.8: skip (duplicate)
    else: add to master (unique)

save master database
save duplicates database
save consolidation stats
```

**Output:**
```
output/database/
├── jobs_master.json           # Unique jobs
├── jobs_duplicates.json       # Removed duplicates
└── consolidation_stats.json   # Statistics
```

### 3. Filtering Pipeline

**Command:** `/filter`
**Skills:** job-filter
**Scripts:** `scripts/filter_jobs.py`

```
User Criteria → Load Master DB → Apply Filters
                                       │
                          ┌────────────┼────────────┐
                          │            │            │
                    Deterministic   Fuzzy       AI Class.
                     (exact match)  (pattern)   (ambiguous)
                          │            │            │
                     Job Type       Keywords    Skills
                     Location      Salary Range  Relevance
                     Experience    City Match   Inference
                     Posted Date   Company
                          │            │            │
                          └────────────┼────────────┘
                                       │
                              Calculate Match Scores
                                       │
                              Save Filtered DB + Report
```

**Filter Order (Optimized):**
1. Deterministic (fast elimination)
   - Job type
   - Experience level
   - Location type
   - Posted date
2. Fuzzy (pattern matching)
   - Keywords
   - Salary range
   - Cities
   - Company
3. AI (selective, slow)
   - Required skills
   - Experience inference
   - Relevance scoring

**Output:**
```
output/database/
├── jobs_filtered.json              # Matched jobs
└── reports/filter_results_[ID].json  # Statistics
```

### 4. Personalization Pipeline

**Command:** `/personalize`
**Skills:** application-personalizer
**Scripts:** `scripts/init_tracker.py`

```
Filtered Jobs → For Each Job (Sequential):
                        │
                ┌───────┴───────┐
                │               │
           Company Research  Load Templates
                │               │
         (WebFetch, Search)  (CV, Cover Letter)
                │               │
         Extract: Mission,   Identify EDITABLE
         Values, Products,   Sections
         Tech Stack, News
                │               │
                └───────┬───────┘
                        │
                Personalize Documents
                        │
           ┌────────────┼────────────┐
           │            │            │
    Personalize CV  Personalize   Save Research
    (5 sections)    Cover Letter  Report
                    (6 sections)
           │            │            │
           └────────────┼────────────┘
                        │
                Save Application Package
                        │
                Update Tracker → Next Job
```

**Processing Rules:**
- **Sequential:** One job at a time
- **Fresh Context:** New agent per job
- **No Batching:** Each job independent
- **Full Research:** No cached results
- **Deterministic:** Pre-built tools only

**Output:**
```
applications/[job_id]_[company]/
├── cv.md                    # Personalized CV
├── cover_letter.md          # Personalized cover letter
└── company_research.json    # Research findings

output/database/
└── applications_tracker.json  # Session tracking
```

## Data Flow

### Complete Pipeline Data Flow

```
1. SCRAPING
   Website → HTML → Structured Data → Session Jobs

2. CONSOLIDATION
   Session 1 Jobs ┐
   Session 2 Jobs ├─→ Deduplicate → Master Database
   Session 3 Jobs ┘

3. FILTERING
   Master DB + User Criteria → Matched Jobs → Filtered Database

4. PERSONALIZATION
   Filtered Job + Company Research + Templates → Application Package
```

### Database Schema Evolution

```
SCRAPED JOB (session level):
{
  "job": {
    "id": "12345",
    "url": "...",
    "title": { "value": "...", "confidence": 95 },
    "company": { "value": "...", "confidence": 100 },
    "location": { "city": "...", "country": "...", "type": "..." },
    "salary": { "min": 50000, "max": 70000, "currency": "EUR" },
    "description": { "value": "..." },
    "requirements": [...],
    "responsibilities": [...]
  },
  "extraction": {
    "fieldsFound": 13,
    "dataCompleteness": 87,
    "qualityGrade": "A"
  }
}

CONSOLIDATED JOB (master database):
{
  "id": "12345",
  "url": "...",
  "title": "Senior Backend Developer",
  "company": "TechCorp Solutions Inc.",
  "location": "San Francisco, CA",
  "session": "session_scrape_20251120_140000",
  "raw": { /* complete scraped job */ }
}

FILTERED JOB (after filtering):
{
  "id": "12345",
  "url": "...",
  "title": "Senior Backend Developer",
  "company": "TechCorp Solutions Inc.",
  "location": "San Francisco, CA",
  "session": "session_scrape_20251120_140000",
  "filter_match": {
    "matched_at": "2025-11-22T14:30:00Z",
    "criteria_met": ["job_title", "location_type", "salary_range"],
    "match_score": 100
  },
  "raw": { /* complete scraped job */ }
}

PERSONALIZED JOB (after personalization):
{
  "id": "12345",
  "url": "...",
  "title": "Senior Backend Developer",
  "company": "TechCorp Solutions Inc.",
  "location": "San Francisco, CA",
  "session": "session_scrape_20251120_140000",
  "filter_match": { /* ... */ },
  "application": {
    "personalized": true,
    "created_at": "2025-11-22T15:30:00Z",
    "directory": "applications/12345_TechCorp_Solutions_Inc",
    "files": {
      "cv": "applications/12345_TechCorp_Solutions_Inc/cv.md",
      "cover_letter": "applications/12345_TechCorp_Solutions_Inc/cover_letter.md",
      "research": "applications/12345_TechCorp_Solutions_Inc/company_research.json"
    },
    "status": "ready"
  },
  "raw": { /* complete scraped job */ }
}
```

## Skills & Tools

### Skills (AI Agents)

| Skill | Purpose | Tools Used | Processing |
|-------|---------|------------|------------|
| session-manager | Orchestrates scraping session | All | Autonomous |
| page-classifier | Classifies job pages (detail/list) | WebFetch, Read | Per page |
| url-extractor | Extracts job URLs from listings | WebFetch, Grep | Per page |
| data-extractor | Extracts structured job data | WebFetch, Read | Per job |
| antibot-handler | Detects/handles CAPTCHAs | WebFetch | Per request |
| quality-analyzer | Analyzes scraping quality | Read, Grep, Glob | Per session |
| consolidator | Consolidates multiple sessions | Read, Write, Glob | All sessions |
| deduplicator | Removes duplicate jobs | Read, Write | Master DB |
| schema-builder | Helps build extraction schema | Read, Write | Interactive |
| job-filter | Filters jobs by criteria | Read, Write | Master DB |
| application-personalizer | Personalizes CV/cover letter | WebFetch, WebSearch, Read, Write | Per job |

### Python Scripts

| Script | Purpose | Used By |
|--------|---------|---------|
| `scripts/consolidate_sessions.py` | Merge session data | consolidator skill |
| `scripts/deduplicate_jobs.py` | Remove duplicates | deduplicator skill |
| `scripts/filter_jobs.py` | Filter jobs by criteria | job-filter skill |
| `scripts/init_tracker.py` | Initialize application tracker | personalize command |

### Commands

| Command | Description | Calls |
|---------|-------------|-------|
| `/scrape` | Start scraping session | session-manager skill |
| `/resume` | Resume interrupted session | session-manager skill |
| `/consolidate` | Merge sessions and dedupe | consolidator skill |
| `/dedupe` | Remove duplicates only | deduplicator skill |
| `/analyze` | Analyze scraping quality | quality-analyzer skill |
| `/filter` | Filter jobs by criteria | job-filter skill |
| `/personalize` | Personalize applications | application-personalizer skill (per job) |

## Security Architecture

### Sandboxing & Restrictions

```
┌─────────────────────────────────────┐
│         SECURITY BOUNDARIES         │
└─────────────────────────────────────┘

✅ ALLOWED:
  - Read from config/, user_docs/
  - Read from output/
  - Write to output/ (structured data only)
  - WebFetch public URLs
  - WebSearch for company info
  - Create .json, .md files

❌ FORBIDDEN:
  - Create .py, .sh, .js, executables
  - Modify config files
  - Modify templates in user_docs/
  - Write outside output/ directory
  - Batch process multiple jobs
  - Access user's personal data
  - Execute generated code
```

### Process Integrity

**Scraping:**
- Checkpoint every 10 jobs
- Resume from last checkpoint
- Graceful error handling

**Filtering:**
- Deterministic filters first (fail fast)
- AI classification only when needed
- No modification of master DB

**Personalization:**
- One job at a time (sequential)
- Fresh agent context per job
- No shared state between jobs
- Full audit trail in tracker

## Performance Characteristics

### Scraping
- **Speed:** 2-5 jobs/minute (including delays)
- **Rate Limiting:** 2-5 second delays between requests
- **Checkpoint:** Every 10 jobs
- **Error Rate:** ~5-10% (expected for failed URLs)

### Consolidation
- **Speed:** ~1000 jobs/second
- **Deduplication:** O(n²) similarity check
- **Typical Time:** <1 minute for 1000 jobs

### Filtering
- **Deterministic:** 500-1000 jobs/second
- **Fuzzy:** 200-400 jobs/second
- **AI Classification:** 5-10 jobs/second
- **Typical Time:** 3-5 seconds for 600 jobs

### Personalization
- **Speed:** 1 job per 5-10 minutes
- **Research:** 60% of time (3-5 minutes)
- **Personalization:** 30% of time (2-3 minutes)
- **Save/Track:** 10% of time (30-60 seconds)
- **Typical Time:** 4-8 hours for 50 jobs

## Error Handling Strategy

### Scraping Errors
- **CAPTCHA:** Pause, request user to solve, resume
- **Rate Limit:** Backoff and retry with delays
- **404/403:** Log and skip
- **Timeout:** Retry once, then skip
- **Malformed HTML:** Best-effort extraction, flag as low quality

### Consolidation Errors
- **Missing Session:** Skip and continue
- **Corrupted JSON:** Log error, skip file
- **Duplicate Detection Failure:** Include job (false negative OK)

### Filtering Errors
- **Missing Field:** Include job, flag as missing data
- **Currency Conversion:** Skip currency check
- **AI Classification Timeout:** Default to exclude (conservative)

### Personalization Errors
- **Website Down:** Fallback to web search, mark research_quality=low
- **No Company Info:** Use job posting data only, mark research_quality=low
- **Template Missing:** CRITICAL error, stop processing
- **WebFetch Timeout:** Retry once, then fallback to search

## Scalability Considerations

### Current Limits
- **Jobs per session:** Unlimited (checkpointed every 10)
- **Sessions:** Unlimited (consolidated)
- **Filtered jobs:** Unlimited (processed sequentially for personalization)
- **Personalization:** Sequential (one at a time, no limit)

### Bottlenecks
1. **Scraping:** Rate limiting (intentional)
2. **Deduplication:** O(n²) similarity check (acceptable for <10k jobs)
3. **Personalization:** Sequential processing (intentional, 5-10 min/job)

### Optimization Opportunities
- **Scraping:** Batch HTML fetches (5-10 at a time)
- **Filtering:** Cache AI classification results
- **Personalization:** Pre-fetch company websites in parallel (future)

## Directory Structure

```
job-hunter/
├── .claude/                    # Claude Code configuration
│   ├── commands/               # Slash commands
│   │   ├── scrape.md
│   │   ├── consolidate.md
│   │   ├── filter.md
│   │   └── personalize.md
│   ├── skills/                 # AI agent skills
│   │   ├── session-manager/
│   │   ├── consolidator/
│   │   ├── job-filter/
│   │   └── application-personalizer/
│   ├── hooks/                  # Lifecycle hooks
│   │   ├── validate_extraction.py
│   │   ├── rate_limiter.py
│   │   └── progress_tracker.py
│   └── mcp.json               # MCP server config
├── config/
│   └── extraction_schema.json  # Scraping schema
├── user_docs/                  # User templates
│   ├── cv_template.md
│   └── cover_letter_template.md
├── scripts/                    # Python utilities
│   ├── consolidate_sessions.py
│   ├── deduplicate_jobs.py
│   ├── filter_jobs.py
│   └── init_tracker.py
├── output/                     # All generated data
│   ├── session_[ID]/          # Scraping sessions
│   ├── database/              # Consolidated & filtered
│   ├── reports/               # Analysis reports
│   └── checkpoints/           # Session checkpoints
├── applications/              # Personalized applications
│   └── [job_id]_[company]/
│       ├── cv.md
│       ├── cover_letter.md
│       └── company_research.json
├── README.md                  # Main documentation
├── FILTERING_GUIDE.md         # Filtering system guide
├── PERSONALIZATION_GUIDE.md   # Personalization guide
└── SYSTEM_ARCHITECTURE.md     # This file
```

## Technology Stack

- **Language:** Python 3.8+
- **AI:** Claude (via Claude Code CLI)
- **Browser:** Chrome with remote debugging (Puppeteer MCP)
- **Web Scraping:** WebFetch, WebSearch tools
- **Data Format:** JSON (structured data), Markdown (documents)
- **Version Control:** Git

## Design Principles

1. **Deterministic:** Pre-built tools, no runtime script generation
2. **Bulletproof:** Error recovery, checkpointing, retry logic
3. **Sequential:** One item at a time for personalization (fresh context)
4. **Auditable:** Complete tracking, logs, research reports
5. **Secure:** Sandboxed, limited file access, no code execution
6. **Transparent:** Clear progress reporting, statistics
7. **Quality-First:** Thorough research, quality over speed
8. **User-Centric:** Minimal intervention, walk-away automation

## Future Enhancements

- Email automation (send applications)
- Application status tracking
- Interview scheduling integration
- Response templates
- Cover letter A/B testing
- Multi-language support
- Resume formatting (PDF generation)
- Job board integrations (LinkedIn, Indeed)
- Analytics dashboard

---

**System Status:** Production Ready
**Last Updated:** 2025-11-23

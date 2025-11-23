# Job Filtering System Guide

Complete guide to the intelligent job filtering system built into Job Hunter.

## Overview

The job filtering system allows you to search through your consolidated job database using multiple criteria. It combines:

- **Deterministic filtering** - Fast, exact-match filters (job type, experience level, location type)
- **Fuzzy matching** - Keyword search, salary range overlap, city matching
- **AI classification** - Intelligent matching for required skills and ambiguous cases

## Quick Start

1. Ensure you have a consolidated database:
```bash
/consolidate
```

2. Start filtering:
```bash
/filter
```

3. Answer the filter questions or provide criteria directly

4. Review results in `output/database/jobs_filtered.json`

## Filter Criteria

### Job Title / Keywords

Search for specific roles or keywords in job titles and descriptions.

**Examples:**
- "Data Analyst"
- "Backend Developer"
- "Product Manager"
- "Machine Learning Engineer"

**Matching Strategy:**
- Exact substring match (highest priority)
- Word boundary matching (all words present)
- Fuzzy similarity (>80% match)

**Searches in:**
- Job title
- Job description

### Location Type

Filter by work arrangement.

**Options:**
- Remote only
- Hybrid
- On-site
- Any location

**Note:** Jobs with missing location type will be flagged but included.

### Salary Range

Define minimum and/or maximum salary expectations.

**Specify:**
- Currency (USD, EUR, GBP, etc.)
- Minimum salary
- Maximum salary
- Range (both min and max)

**Normalization:**
- Monthly salaries converted to annual (×12)
- Hourly salaries converted to annual (×2080 hours)
- All comparisons done on annual basis

**Matching:**
- Ranges that overlap are included
- Jobs with missing salary are flagged
- Different currencies can be filtered (conversion TBD)

**Example:**
```
Salary: €40,000 - €80,000 per year

Matches:
  ✓ €50,000 - €70,000 (fully within range)
  ✓ €30,000 - €45,000 (overlaps on low end)
  ✓ €75,000 - €95,000 (overlaps on high end)

Doesn't Match:
  ✗ €20,000 - €35,000 (entirely below)
  ✗ €90,000 - €120,000 (entirely above)
```

### Experience Level

Filter by seniority level.

**Options:**
- Entry Level
- Junior
- Mid-Level
- Senior
- Lead
- Executive

**Multiple Selection:** Can select multiple levels (e.g., Mid-Level AND Senior)

**AI Inference:** If experience level is missing, the system can infer it from:
- Job requirements
- Salary range
- Responsibilities

### Job Type

Employment type filter.

**Options:**
- Full-time
- Part-time
- Contract
- Temporary
- Internship

### City / Location

Target specific cities or regions.

**Examples:**
- "Vienna"
- "San Francisco"
- "Berlin, Munich, Hamburg"

**Matching:**
- Exact city name match
- City name in location string
- Case-insensitive

### Company Name

Filter by company name substring.

**Examples:**
- "Tech" (matches TechCorp, FinTech, Technology Inc.)
- "Bank" (matches Deutsche Bank, Bank of America, etc.)
- "Startup" (matches StartupHub, TechStartup, etc.)

**Matching:**
- Case-insensitive substring match
- Matches anywhere in company name

### Posted Date

Filter by how recently the job was posted.

**Options:**
- Last 7 days
- Last 30 days
- Last 60 days
- Custom number of days

**Note:** Jobs with missing posted date are included but flagged.

### Required Skills (AI-Powered)

Filter by specific technical skills or technologies.

**Examples:**
- "Python, SQL, Power BI"
- "React, TypeScript, Node.js"
- "AWS, Docker, Kubernetes"

**AI Analysis:**
The system uses AI to determine if a job requires these skills by analyzing:
- Job requirements section
- Responsibilities
- Job description
- Related technologies/tools

**Confidence Threshold:** Only matches with ≥70% confidence are included.

## Filtering Process

### 1. Deterministic Filters (Fastest)

Applied first to quickly eliminate non-matches:

```
Job Type: Exact match
  job.jobType.value == "Full-time"

Experience Level: Exact match
  job.experienceLevel.value in ["Mid-Level", "Senior"]

Location Type: Exact match
  job.remotePolicy.value in ["remote", "hybrid"]

Posted Date: Date comparison
  (today - job.postedDate).days <= 30
```

### 2. Fuzzy Filters (Fast)

Pattern matching and range comparisons:

```
Keywords: Substring/similarity match
  "data analyst" in job.title.lower()
  OR similarity(keywords, job.title) > 0.8

Salary Range: Overlap detection
  job_max >= salary_min AND job_min <= salary_max

City: Substring match
  "Vienna" in job.location.city OR "Vienna" in job.location.value

Company: Substring match
  "Tech" in job.company.value.lower()
```

### 3. AI Classification (Slower, Selective)

Only used when deterministic/fuzzy filters can't decide:

```
Required Skills:
  Prompt: "Does this job require: Python, SQL, Power BI?
          Requirements: [...]
          Responsibilities: [...]
          Answer: YES/NO with confidence"

Experience Level Inference (if missing):
  Prompt: "What experience level is this job?
          Requirements: [...]
          Salary: [...]
          Answer: Entry/Junior/Mid/Senior/Lead"

Job Relevance (ambiguous keywords):
  Prompt: "Is this job relevant for: 'data analyst'?
          Title: [...]
          Description: [...]
          Answer: YES/NO with confidence"
```

## Match Scoring

Each job receives a match score (0-100%):

```
match_score = (criteria_met / total_criteria) × 100

Example:
  User specified 5 criteria
  Job matches 5/5 → 100% match
  Job matches 4/5 → 80% match
  Job matches 3/5 → 60% match
```

**Perfect Matches:** 100% score (all criteria met)
**Partial Matches:** 80-99% score (most criteria met)

## Output Files

### jobs_filtered.json

Filtered jobs with match metadata:

```json
{
  "id": "12345",
  "title": "Senior Backend Developer",
  "company": "TechCorp Solutions Inc.",
  "location": "San Francisco, CA",
  "filter_match": {
    "matched_at": "2025-11-22T14:30:00Z",
    "filter_id": "filter_20251122_143000",
    "criteria_met": [
      "job_title",
      "location_type",
      "salary_range",
      "experience_level",
      "job_type"
    ],
    "criteria_failed": [],
    "match_score": 100,
    "ai_classified": false
  },
  "raw": { /* complete job data */ }
}
```

### filter_results_[TIMESTAMP].json

Statistics and breakdown:

```json
{
  "filter_id": "filter_20251122_143000",
  "created_at": "2025-11-22T14:30:00Z",
  "criteria": { /* your filter criteria */ },
  "results": {
    "total_matches": 47,
    "match_rate_percent": 7.57,
    "perfect_matches": 35,
    "partial_matches": 12,
    "ai_classified_count": 5
  },
  "filter_breakdown": {
    "job_title_keyword": { "passed": 156, "failed": 465 },
    "location_type": { "passed": 298, "failed": 312 },
    "salary_range": { "passed": 189, "failed": 367 }
  },
  "top_matches": [ /* top 10 jobs */ ],
  "processing": {
    "duration_seconds": 3.2,
    "jobs_per_second": 194.1
  }
}
```

## Usage Examples

### Example 1: Remote Data Analyst Jobs

```
Filter Criteria:
  Keywords: "data analyst"
  Location Type: Remote
  Salary: €40,000 - €80,000
  Experience: Mid-Level, Senior
  Job Type: Full-time
```

### Example 2: Tech Jobs in Major Cities

```
Filter Criteria:
  Keywords: "software engineer", "developer"
  Cities: San Francisco, New York, Austin
  Salary: $100,000 - $180,000 USD
  Location Type: Hybrid
  Posted: Last 30 days
```

### Example 3: Machine Learning Roles

```
Filter Criteria:
  Keywords: "machine learning", "ML engineer"
  Required Skills: Python, TensorFlow, PyTorch
  Experience: Senior, Lead
  Company: "Tech", "AI"
```

## Performance

### Processing Speed

- **Deterministic filters:** ~500-1000 jobs/second
- **Fuzzy filters:** ~200-400 jobs/second
- **AI classification:** ~5-10 jobs/second (only when needed)

### Optimization

The system processes filters in order of speed:
1. Fast deterministic filters first (fail fast)
2. Fuzzy filters on remaining jobs
3. AI classification only when ambiguous

**Example:**
```
621 total jobs
  → Job Type filter: 587 passed (34 eliminated)
  → Experience filter: 234 passed (353 eliminated)
  → Keywords filter: 89 passed (145 eliminated)
  → Salary filter: 67 passed (22 eliminated)
  → City filter: 47 passed (20 eliminated)
  → AI skills check: 47 jobs (5 needed AI, 42 deterministic)

Final: 47 matches in 3.2 seconds
```

## Tips & Best Practices

### 1. Start Broad, Then Narrow

Start with fewer criteria, see results, then add more filters:

```
Round 1: Just keywords → 200 matches (too many)
Round 2: Add location type → 85 matches (better)
Round 3: Add salary range → 45 matches (good)
```

### 2. Use Multiple Keywords

Instead of one specific term, use variations:

```
❌ "Data Analyst"
✓ "Data Analyst", "Analytics", "BI Analyst"
```

### 3. Account for Missing Data

Some jobs may have incomplete information:
- 10-20% missing salary
- 5-10% missing experience level
- 2-5% missing location type

The system includes these jobs but flags them.

### 4. Salary Ranges

Use overlapping ranges for best results:

```
Want €50,000 salary?
  Set range: €40,000 - €60,000
  (catches €45k-55k, €35k-50k, €50k-65k)

Don't use:
  Exactly €50,000 (too restrictive)
```

### 5. Location Flexibility

If searching multiple cities, include all variations:

```
Vienna → Also search: "Wien" (German name)
Munich → Also search: "München" (German name)
```

### 6. Review Partial Matches

Jobs with 80-99% match score might be good candidates:

```
95% match: Missing only one criterion
  (e.g., salary not specified, but everything else perfect)
```

## Troubleshooting

### No Matches Found

**Problem:** 0 jobs match criteria

**Solutions:**
1. Check if criteria is too restrictive
2. Remove least important filter
3. Broaden salary range
4. Include more experience levels
5. Try different keywords

**Example:**
```
Original: 0 matches
  Keywords: "Senior ML Engineer"
  Salary: €80k-€90k
  Location: Vienna only
  Posted: Last 7 days

Adjusted: 12 matches
  Keywords: "ML Engineer", "Machine Learning"
  Salary: €70k-€100k
  Cities: Vienna, Remote
  Posted: Last 30 days
```

### Too Many Matches

**Problem:** 500+ jobs match (too broad)

**Solutions:**
1. Add more specific keywords
2. Tighten salary range
3. Add experience level filter
4. Add city restriction
5. Use required skills filter

### Slow Filtering

**Problem:** Filtering takes >10 seconds

**Possible Causes:**
- Large database (>1000 jobs)
- Heavy AI classification usage
- Required skills filter on many jobs

**Solutions:**
- Use deterministic filters first
- Limit required skills filter usage
- Check database size

### Missing Expected Jobs

**Problem:** Job you know exists isn't in results

**Checks:**
1. Verify job in master database
2. Check if keywords match exactly
3. Verify salary range includes job's salary
4. Check if location type matches
5. Review filter breakdown stats

## Security & Privacy

The filtering system:

- ✅ **Read-only access** to master database
- ✅ **Cannot modify** original job data
- ✅ **Cannot create** executable scripts
- ✅ **Limited to** `output/` directory
- ✅ **No external** API calls (except AI classification)

All filtering happens locally on your machine.

## Next Steps

After filtering jobs:

1. **Review Results** - Check `jobs_filtered.json`
2. **Export Data** - Convert to CSV/Excel for analysis
3. **Generate Application Tracker** - Create application management system
4. **Refine Filters** - Adjust criteria and re-run
5. **Set Up Alerts** - Get notified of new matching jobs

---

For more information, see:
- Main README: `README.md`
- Filter command: `.claude/commands/filter.md`
- Filter skill: `.claude/skills/job-filter/SKILL.md`
- Filter script: `scripts/filter_jobs.py`

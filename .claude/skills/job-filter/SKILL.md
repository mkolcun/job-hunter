---
name: job-filter
description: Filters jobs from master database using deterministic and AI-based classification. (project)
---

# Job Filter Skill

You are a specialized job filtering agent. Your task is to filter jobs from the master database based on user-defined criteria using a combination of deterministic filtering and AI classification.

## Your Capabilities

You have access to these tools:
- **Read**: Read the master database and job files
- **Write**: Write filtered results to output files
- **Grep**: Search for patterns in job data
- **Glob**: Find job files by pattern

## Your Task

Filter jobs from `output/database/jobs_master.json` based on criteria provided by the user.

## Input Format

You will receive filtering criteria in this format:
```
Filter Criteria:
- Keywords: ["data analyst", "analytics"]
- Location Type: ["remote", "hybrid"]
- Salary Range: €40,000 - €80,000 (annual)
- Experience Levels: ["Mid-Level", "Senior"]
- Job Types: ["Full-time"]
- Cities: ["Vienna", "Berlin", "Munich"]
- Posted Within: 30 days
- Company Contains: null
- Required Skills: ["Python", "SQL"]
```

## Processing Steps

### Step 1: Load Master Database

Read `output/database/jobs_master.json`:
```python
# Expected structure
[
  {
    "id": "12345",
    "url": "...",
    "title": "Senior Data Analyst",
    "company": "TechCorp Inc.",
    "location": "Vienna",
    "session": "...",
    "raw": {
      "job": {
        "title": { "value": "...", "confidence": 95 },
        "company": { "value": "...", "confidence": 100 },
        "location": { "city": "...", "country": "...", "type": "..." },
        "salary": { "min": 50000, "max": 70000, "currency": "EUR", "period": "annual" },
        "experienceLevel": { "value": "Senior" },
        "jobType": { "value": "Full-time" },
        "remotePolicy": { "value": "hybrid" },
        "postedDate": { "value": "2025-11-15" },
        "requirements": [...],
        "responsibilities": [...],
        "description": { "value": "..." }
      }
    }
  }
]
```

### Step 2: Apply Deterministic Filters

Process filters in this order (most restrictive first):

#### 2.1 Job Type Filter
```
If user specified job_types:
  Keep only jobs where: job.raw.job.jobType.value in job_types

Example:
  User wants: ["Full-time"]
  Keep: job.raw.job.jobType.value == "Full-time"
  Reject: job.raw.job.jobType.value == "Part-time"
```

#### 2.2 Experience Level Filter
```
If user specified experience_levels:
  Keep only jobs where: job.raw.job.experienceLevel.value in experience_levels

Special handling:
  - If job missing experienceLevel, use AI to infer (see Step 4)
  - Match case-insensitive

Example:
  User wants: ["Mid-Level", "Senior"]
  Keep: "Mid-Level", "Senior"
  Reject: "Junior", "Entry Level"
```

#### 2.3 Location Type Filter
```
If user specified location_type:
  Keep only jobs where: job.raw.job.remotePolicy.value in location_type

OR if remotePolicy missing:
  Check job.raw.job.location.type

Example:
  User wants: ["remote", "hybrid"]
  Keep: remotePolicy = "remote" or "hybrid"
  Reject: remotePolicy = "on-site"
```

#### 2.4 Posted Date Filter
```
If user specified posted_days:
  today = current date
  Keep only jobs where: (today - job.raw.job.postedDate.value).days <= posted_days

Example:
  User wants: Last 30 days
  Today: 2025-11-22
  Keep: postedDate >= 2025-10-23
  Reject: postedDate < 2025-10-23

Handle missing dates:
  - If postedDate missing, include job but flag it
```

### Step 3: Apply Fuzzy Filters

#### 3.1 Keyword/Title Filter
```
If user specified keywords:
  For each keyword in keywords:
    Check if keyword appears in:
      - job.raw.job.title.value (case-insensitive)
      - job.raw.job.description.value (case-insensitive)

  Matching strategies:
    1. Exact substring match (highest priority)
       "data analyst" in title.lower()

    2. Word boundary match
       All words in keyword appear in title
       "senior analyst" matches "Senior Data Analyst"

    3. Fuzzy similarity (>80%)
       Use word overlap ratio

Example:
  User keyword: "data analyst"
  Match: "Data Analyst", "Senior Data Analyst", "Data Analytics Manager"
  No match: "Business Analyst" (unless user also searches "analyst")
```

#### 3.2 Salary Range Filter
```
If user specified salary_min or salary_max:

  Step 1: Normalize salary to annual
    If job.salary.period == "monthly": annual = monthly * 12
    If job.salary.period == "hourly": annual = hourly * 2080

  Step 2: Currency conversion (if needed)
    If job.salary.currency != user.salary_currency:
      Convert using approximate rates or skip job

  Step 3: Compare ranges
    job_min = job.salary.min or job.salary.max
    job_max = job.salary.max or job.salary.min

    Keep if:
      job_max >= salary_min AND job_min <= salary_max
      (ranges overlap)

Example:
  User range: €40,000 - €80,000
  Keep: €50,000 - €70,000 (overlaps)
  Keep: €30,000 - €45,000 (overlaps)
  Keep: €75,000+ (overlaps)
  Reject: €20,000 - €35,000 (below range)
  Reject: €90,000+ (above range)

Handle missing salary:
  - Flag job as "salary not specified"
  - Ask user if they want to include these
```

#### 3.3 City/Location Filter
```
If user specified cities:
  Keep jobs where ANY city matches:
    - job.raw.job.location.city (exact match)
    - job.raw.job.location.value (contains city name)

  Case-insensitive matching

Example:
  User cities: ["Vienna", "Berlin", "Munich"]
  Keep: location.city = "Vienna"
  Keep: location.value = "Vienna, Austria"
  Keep: location.value = "Berlin or Munich"
  Reject: location.city = "Hamburg"
```

#### 3.4 Company Filter
```
If user specified company_contains:
  Keep jobs where:
    company_contains.lower() in job.raw.job.company.value.lower()

Example:
  User: "Tech"
  Keep: "TechCorp", "FinTech Solutions", "Technology Inc."
  Reject: "Bank of Austria", "Retail Group"
```

### Step 4: AI Classification (Ambiguous Cases)

When deterministic filters cannot decide, use AI classification:

#### 4.1 Required Skills Matching
```
If user specified required_skills and job has requirements/responsibilities:

Prompt:
"Analyze if this job requires the following skills: [required_skills]

Job Requirements:
[job.raw.job.requirements]

Job Responsibilities:
[job.raw.job.responsibilities]

Job Description:
[job.raw.job.description.value]

Question: Does this job require skills in: [required_skills]?

Consider:
- Explicit mentions in requirements
- Implied skills from responsibilities
- Related technologies/tools

Answer with JSON:
{
  "matches": true/false,
  "confidence": 0-100,
  "matched_skills": ["skill1", "skill2"],
  "reasoning": "why it matches or doesn't"
}
"

If matches == true AND confidence >= 70:
  Include job
Else:
  Exclude job
```

#### 4.2 Experience Level Inference
```
If experienceLevel is missing but user filtered by experience:

Prompt:
"Based on the requirements and responsibilities, what experience level is this job?

Requirements:
[job.raw.job.requirements]

Responsibilities:
[job.raw.job.responsibilities]

Salary Range:
[job.raw.job.salary]

Options: Entry Level, Junior, Mid-Level, Senior, Lead, Executive

Answer with JSON:
{
  "level": "Mid-Level",
  "confidence": 0-100,
  "reasoning": "why"
}
"

Assign inferred experience level if confidence >= 60
Then apply experience level filter
```

#### 4.3 Job Title Relevance (Ambiguous Keywords)
```
If keyword matching is uncertain:

Prompt:
"Is this job relevant for someone searching for: [user_keywords]?

Job Title: [job.title]
Job Description: [job.description]
Responsibilities: [job.responsibilities]

Consider:
- Direct title match
- Related roles
- Transferable responsibilities

Answer with JSON:
{
  "relevant": true/false,
  "confidence": 0-100,
  "reasoning": "why"
}
"

If relevant == true AND confidence >= 70:
  Include job
```

### Step 5: Calculate Match Scores

For each job that passes filters:
```
match_score = (criteria_met / total_criteria) * 100

criteria_met = count of filters that matched:
  - job_title_match (keyword found)
  - location_type_match (remote/hybrid/onsite)
  - salary_range_match (within range)
  - experience_level_match (level matches)
  - job_type_match (full-time/part-time)
  - city_match (if specified)
  - company_match (if specified)
  - skills_match (if specified)

Example:
  User specified 5 criteria
  Job matches 5 criteria
  match_score = 100

  User specified 5 criteria
  Job matches 4 criteria (salary missing)
  match_score = 80
```

### Step 6: Save Filtered Results

Create filtered database with match metadata:

```json
[
  {
    "id": "12345",
    "url": "https://example-jobs.com/positions/12345",
    "title": "Senior Data Analyst",
    "company": "TechCorp Inc.",
    "location": "Vienna",
    "session": "session_scrape_20251120_140000",
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
      "ai_classified": false,
      "notes": null
    },
    "raw": {
      // Complete original job object
    }
  }
]
```

Save to: `output/database/jobs_filtered.json`

### Step 7: Generate Statistics Report

Create filter results report:

```json
{
  "filter_id": "filter_20251122_143000",
  "created_at": "2025-11-22T14:30:00Z",
  "source_database": "output/database/jobs_master.json",
  "source_job_count": 579,

  "criteria": {
    "keywords": ["data analyst", "analytics"],
    "location_type": ["remote", "hybrid"],
    "salary_min": 40000,
    "salary_max": 80000,
    "salary_currency": "EUR",
    "experience_levels": ["Mid-Level", "Senior"],
    "job_types": ["Full-time"],
    "cities": ["Vienna", "Berlin", "Munich"],
    "posted_days": 30,
    "company_contains": null,
    "required_skills": ["Python", "SQL"]
  },

  "results": {
    "total_matches": 47,
    "match_rate_percent": 8.12,
    "perfect_matches": 35,
    "partial_matches": 12,
    "ai_classified_count": 8
  },

  "filter_breakdown": {
    "job_title_keyword": {
      "passed": 89,
      "failed": 490,
      "missing_data": 0
    },
    "location_type": {
      "passed": 312,
      "failed": 255,
      "missing_data": 12
    },
    "salary_range": {
      "passed": 156,
      "failed": 298,
      "missing_data": 125
    },
    "experience_level": {
      "passed": 234,
      "failed": 312,
      "missing_data": 33
    },
    "job_type": {
      "passed": 521,
      "failed": 52,
      "missing_data": 6
    },
    "city_location": {
      "passed": 178,
      "failed": 401,
      "missing_data": 0
    },
    "required_skills": {
      "passed": 67,
      "failed": 512,
      "missing_data": 0
    }
  },

  "top_matches": [
    {
      "job_id": "12345",
      "title": "Senior Data Analyst",
      "company": "TechCorp Inc.",
      "location": "Vienna",
      "salary": "€50,000 - €70,000",
      "match_score": 100
    }
  ],

  "processing": {
    "duration_seconds": 4.2,
    "deterministic_filters": 39,
    "ai_classifications": 8,
    "jobs_per_second": 137.9
  }
}
```

Save to: `output/reports/filter_results_[TIMESTAMP].json`

## Output Format

After completing the filtering, report back:

```
✅ Filtering Complete
=====================
Scanned: 579 jobs from master database
Matched: 47 jobs (8.12%)

Perfect Matches: 35 jobs (100% criteria met)
Partial Matches: 12 jobs (80%+ criteria met)

Filter Performance:
  ✓ Job Title/Keywords: 89 passed
  ✓ Location Type: 312 passed
  ✓ Salary Range: 156 passed (125 missing salary data)
  ✓ Experience Level: 234 passed
  ✓ Job Type: 521 passed
  ✓ City: 178 passed
  ✓ Required Skills: 67 passed (8 AI-classified)

Top 5 Matches:
  1. [100%] Senior Data Analyst - TechCorp Inc. - Vienna (€50-70k)
  2. [100%] Data Analytics Lead - DataFlow GmbH - Remote (€55-75k)
  3. [100%] BI Analyst - CloudSystems - Berlin Hybrid (€48-65k)
  4. [100%] Senior Analytics Engineer - Digital Corp - Munich (€60-80k)
  5. [95%] Data Analyst - TechStart - Vienna (salary not specified)

Processing Time: 4.2 seconds
AI Classifications: 8 jobs

Output Files:
  ✓ output/database/jobs_filtered.json
  ✓ output/reports/filter_results_20251122_143000.json
```

## Error Handling

### No Matches Found
```
⚠️  No Jobs Match Criteria
==========================
Scanned: 579 jobs
Matched: 0 jobs

Closest Matches (didn't meet all criteria):
  1. [60%] Data Analyst - Company A (failed: salary too low)
  2. [60%] Senior Analyst - Company B (failed: location on-site)
  3. [40%] Business Analyst - Company C (failed: different role)

Suggestions:
  - Remove salary constraint (currently €40k-€80k)
  - Include "on-site" in location types
  - Broaden keywords to include "Business Analyst"
```

### Missing Data Warning
```
⚠️  Some Jobs Have Incomplete Data
===================================

47 jobs match criteria, but:
  - 12 jobs missing salary information
  - 5 jobs missing experience level (AI-inferred)
  - 3 jobs missing location type

All 47 jobs included in filtered results.
Jobs with missing data flagged in filter_match.notes
```

## Best Practices

1. **Deterministic First**: Always apply exact-match filters before fuzzy/AI
2. **Fast Processing**: Aim for 100+ jobs/second for deterministic filters
3. **Conservative AI**: Only use AI when confidence >= 70%
4. **Transparent Scoring**: Show which criteria each job met/failed
5. **Preserve Original Data**: Keep complete raw job object in filtered results
6. **Report Statistics**: Show how many jobs passed each individual filter
7. **Handle Missing Data**: Don't fail on missing fields, flag them instead
8. **Normalize Data**: Convert salaries to same currency/period before comparing

## Security Constraints

- ✅ Read only from `output/database/jobs_master.json`
- ✅ Write only to `output/database/jobs_filtered.json` and `output/reports/`
- ❌ Do NOT create any scripts (.py, .sh, .js)
- ❌ Do NOT modify the master database
- ❌ Do NOT access files outside `output/` directory

## Notes

- Process jobs in batches of 50 for better performance
- Cache AI classification results to avoid re-processing
- Sort final results by match_score (highest first)
- Include jobs with missing data but flag them appropriately
- All text matching must be case-insensitive
- Use ISO date format for all date comparisons

---
description: Filter jobs from master database based on criteria
---

# Filter Jobs

I need you to filter jobs from the master database based on user-defined criteria. Follow these steps carefully:

## Step 1: Verify Database Exists

Check if the master database exists:
- `output/database/jobs_master.json`

If not found:
```
❌ Master Database Not Found
============================

Cannot find jobs_master.json

Please run /consolidate first to create the master database.
```

## Step 2: Database Summary

Load the database and show summary:
```
📊 Master Database Summary
==========================
Total Jobs: 579
Last Updated: 2025-11-22

Ready to filter!
```

## Step 3: Gather Filter Criteria

Ask the user for their filtering preferences. Use the **AskUserQuestion** tool to collect criteria:

### Question 1: Job Title/Keywords
**Question**: "What job title or keywords are you looking for?"
**Options**:
- Data Analyst
- Software Engineer
- Product Manager
- Designer
- Marketing
- Custom (user specifies)

If "Custom" or user provides text, accept their input as keywords to search in job titles.

### Question 2: Location Preference
**Question**: "What is your location preference?"
**Options**:
- Remote only
- Hybrid
- On-site
- Any location

### Question 3: Salary Range
**Question**: "What is your salary preference?"
**Options**:
- No preference
- Minimum salary (user specifies amount and currency)
- Maximum salary (user specifies amount and currency)
- Range (user specifies min and max)

### Question 4: Experience Level
**Question**: "What experience level are you looking for?"
**Options**:
- Entry Level
- Junior
- Mid-Level
- Senior
- Lead/Executive
- Any level

### Question 5: Job Type
**Question**: "What type of employment?"
**Options**:
- Full-time
- Part-time
- Contract
- Internship
- Any type

### Question 6: Additional Filters (Optional)
Ask if user wants to filter by:
- Company name (contains text)
- Specific location/city
- Posted date (last 7/30/60 days)
- Required skills/technologies

## Step 4: Display Filter Summary

Show what filters will be applied:
```
🔍 Filter Criteria
==================
Job Title: "Data Analyst" (contains)
Location: Remote or Hybrid
Salary: €40,000 - €80,000 per year
Experience: Mid-Level or Senior
Job Type: Full-time
Additional:
  - City: Vienna, Berlin, Munich
  - Posted: Last 30 days

Searching 579 jobs...
```

## Step 5: Invoke Filter Agent

Use the **job-filter** skill to process the filtering.

Pass all criteria to the skill:
```json
{
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
  "required_skills": null
}
```

## Step 6: Processing

The job-filter skill will:
1. Load master database
2. Apply deterministic filters first (exact matches)
3. Apply fuzzy filters (keyword matching, similarity)
4. Use AI classification for ambiguous cases
5. Track filter statistics
6. Save filtered results

## Step 7: Display Results

Show filtering results:
```
✅ Filtering Complete
=====================
Total Jobs Scanned: 579
Jobs Matching Criteria: 47

Filter Breakdown:
  ✓ Job Title Match: 89 jobs
  ✓ Location Match: 312 jobs
  ✓ Salary Range: 156 jobs
  ✓ Experience Level: 234 jobs
  ✓ Job Type: 521 jobs
  ✓ All Criteria: 47 jobs

Top Matches:
  1. Senior Data Analyst - TechCorp Inc. - Vienna (€55,000)
  2. Data Analytics Lead - DataFlow GmbH - Remote (€65,000)
  3. BI Analyst - CloudSystems - Hybrid (€52,000)
  ...

Saved to:
  output/database/jobs_filtered.json
  output/reports/filter_results_20251122_143000.json
```

## Step 8: Offer Next Actions

Ask user what they want to do next:

**Options**:
- View detailed results (show all 47 jobs)
- Refine filters (adjust criteria)
- Export to CSV/Excel
- Generate application tracking list
- Analyze filtered results
- Start new filter

## Filter Processing Rules

### Deterministic Filters (Exact Match)

**Job Type**: Exact match on `jobType` field
```python
job.jobType.value == "Full-time"
```

**Remote Policy**: Exact match on `remotePolicy` field
```python
job.remotePolicy.value in ["remote", "hybrid"]
```

**Experience Level**: Exact match on `experienceLevel` field
```python
job.experienceLevel.value in ["Mid-Level", "Senior"]
```

**Posted Date**: Date comparison
```python
(today - job.postedDate.value).days <= 30
```

### Fuzzy Filters (Pattern Match)

**Job Title Keywords**: Case-insensitive substring or similarity match
```python
# Direct match
"data analyst" in job.title.value.lower()

# OR fuzzy similarity (>80%)
similarity(keywords, job.title.value) > 0.8
```

**Location/City**: Multiple matching strategies
```python
# City name in location string
"Vienna" in job.location.city

# OR city in full location value
"Vienna" in job.location.value
```

**Salary Range**: Normalize and compare
```python
# Convert all to annual salary in same currency
normalized_salary = normalize_salary(job.salary)

# Check if in range
salary_min <= normalized_salary <= salary_max
```

**Company Name**: Substring match
```python
company_filter.lower() in job.company.value.lower()
```

### AI Classification Filters (Ambiguous Cases)

**Skill Matching**: When user specifies required skills
```
Prompt: "Does this job require skills in: Python, SQL, Power BI?
Job Description: [description]
Job Requirements: [requirements]

Answer: YES/NO with confidence score"
```

**Industry/Domain**: When user filters by industry
```
Prompt: "Is this job in the [finance/tech/healthcare] industry?
Company: [company]
Description: [description]

Answer: YES/NO with confidence score"
```

**Seniority Inference**: When experience level is missing
```
Prompt: "Based on requirements and responsibilities, what is the experience level?
Requirements: [requirements]
Responsibilities: [responsibilities]

Answer: Entry/Junior/Mid-Level/Senior/Lead"
```

## Error Handling

### No Matches Found
```
⚠️  No Jobs Match Your Criteria
===============================
Searched: 579 jobs
Matches: 0

Suggestions:
  1. Broaden salary range (current: €40,000 - €50,000)
  2. Include more experience levels
  3. Try different keywords
  4. Remove location restriction

Would you like to:
  - Adjust filters
  - See closest matches (doesn't meet all criteria)
  - Start over
```

### Ambiguous Criteria
```
⚠️  Clarification Needed
========================

Your keyword "analyst" is very broad and matches 234 jobs.

Would you like to:
  - Add more specific keywords (e.g., "data analyst", "business analyst")
  - See all 234 matches
  - Filter further by other criteria
```

### Partial Data
```
⚠️  Some Jobs Missing Data
===========================

47 jobs match your criteria, but:
  - 12 jobs have no salary information
  - 5 jobs have no experience level
  - 3 jobs have no location type

Include jobs with missing data?
  - Yes, include all matches (47 jobs)
  - No, only jobs with complete data (27 jobs)
  - Let me review missing data jobs separately
```

## Output Files

After filtering completes:

### jobs_filtered.json
Full filtered job database (same structure as jobs_master.json)
```json
[
  {
    "id": "12345",
    "url": "...",
    "title": "Senior Data Analyst",
    "company": "TechCorp Inc.",
    "location": "Vienna",
    "session": "session_scrape_20251120_140000",
    "filter_match": {
      "matched_at": "2025-11-22T14:30:00Z",
      "criteria_met": [
        "job_title",
        "location_type",
        "salary_range",
        "experience_level",
        "job_type"
      ],
      "match_score": 100
    },
    "raw": { /* complete job object */ }
  }
]
```

### filter_results_[TIMESTAMP].json
Filter metadata and statistics
```json
{
  "filter_id": "filter_20251122_143000",
  "created_at": "2025-11-22T14:30:00Z",
  "source_database": "output/database/jobs_master.json",
  "criteria": {
    "keywords": ["data analyst"],
    "location_type": ["remote", "hybrid"],
    "salary_min": 40000,
    "salary_max": 80000,
    "salary_currency": "EUR",
    "experience_levels": ["Mid-Level", "Senior"],
    "job_types": ["Full-time"]
  },
  "statistics": {
    "total_jobs_scanned": 579,
    "total_matches": 47,
    "match_rate": 8.12,
    "filter_breakdown": {
      "job_title": 89,
      "location_type": 312,
      "salary_range": 156,
      "experience_level": 234,
      "job_type": 521,
      "all_criteria": 47
    },
    "processing_time_seconds": 4.2
  },
  "matches": [
    {
      "job_id": "12345",
      "match_score": 100,
      "matched_criteria": ["job_title", "location_type", "salary_range", "experience_level", "job_type"]
    }
  ]
}
```

## Best Practices

1. **Be Specific**: Encourage users to provide specific criteria
2. **Normalize Data**: Convert all salaries to same currency/period
3. **Case Insensitive**: All text matching should be case-insensitive
4. **Fuzzy Matching**: Use similarity scores for keyword matching
5. **Report Missing Data**: Inform users about jobs with incomplete information
6. **Track Statistics**: Show how many jobs matched each individual criterion
7. **Save Everything**: Save both filtered database and filter metadata
8. **Reusable Filters**: Allow users to save and reuse filter configurations

## Security

**CRITICAL - No Code Generation**:
- ✅ Agents can ONLY read from `output/database/jobs_master.json`
- ✅ Agents can ONLY write to `output/database/jobs_filtered.json` and `output/reports/`
- ❌ Agents CANNOT create scripts or executable files
- ❌ Agents CANNOT modify the master database
- ❌ Agents CANNOT access files outside `output/` directory

## Example Usage

User: `/filter`

Expected flow:
1. Verify master database exists
2. Show database summary
3. Ask filter questions (use AskUserQuestion tool)
4. Display filter summary
5. Invoke job-filter skill
6. Show results
7. Save filtered database
8. Offer next actions

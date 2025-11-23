---
description: Personalize CV and cover letter for each filtered job
---

# Personalize Applications

I need you to personalize CVs and cover letters for each job in the filtered database. Follow these steps carefully:

## Step 1: Verify Prerequisites

Check that all required files exist:
- ✅ `output/database/jobs_filtered.json` (filtered jobs)
- ✅ `user_docs/cv_template.md` (CV template)
- ✅ `user_docs/cover_letter_template.md` (cover letter template)
- ✅ `applications/` directory (created if missing)

If filtered database doesn't exist:
```
❌ No Filtered Jobs Found
=========================

Please run /filter first to create a filtered job list.
```

## Step 2: Load Filtered Jobs

Read `output/database/jobs_filtered.json` and show summary:
```
📋 Personalization Queue
========================
Total Jobs: 47
Applications to Create: 47

This will create personalized CVs and cover letters for each job.
Each job will be processed individually with fresh context.

Estimated Time: ~5-10 minutes per application
Total Time: ~4-8 hours

Ready to proceed?
```

Ask user for confirmation before starting.

## Step 3: Initialize Tracking Database

Create or load the application tracking database at:
`output/database/applications_tracker.json`

Structure:
```json
{
  "personalization_session": "personalize_20251122_150000",
  "started_at": "2025-11-22T15:00:00Z",
  "source_filter": "filter_20251122_143000",
  "total_jobs": 47,
  "applications": []
}
```

## Step 4: Process Jobs One by One

**CRITICAL:** Process each job individually using the **application-personalizer** skill.

For each job in filtered database:

1. Extract job information:
   ```
   Job ID: 12345
   Company: TechCorp Solutions Inc.
   Title: Senior Backend Developer
   Location: San Francisco, CA
   URL: https://example-jobs.com/positions/12345
   ```

2. Invoke **application-personalizer** skill with:
   ```
   Job Details:
   - ID: 12345
   - Company: TechCorp Solutions Inc.
   - Title: Senior Backend Developer
   - Location: San Francisco, CA
   - URL: https://example-jobs.com/positions/12345
   - Requirements: [from job.raw.job.requirements]
   - Responsibilities: [from job.raw.job.responsibilities]
   - Description: [from job.raw.job.description]

   Output Directory: applications/12345_TechCorp_Solutions_Inc/
   ```

3. Wait for skill to complete

4. Update tracking database with result

5. Report progress:
   ```
   ✅ [3/47] TechCorp Solutions Inc. - Senior Backend Developer
   ```

6. Move to next job

**IMPORTANT:**
- Process jobs sequentially (one at a time)
- Each job gets a fresh agent invocation
- Do NOT batch process
- Do NOT create loops or scripts
- Each skill invocation is independent

## Step 5: Progress Reporting

After every 5 jobs, show progress summary:
```
📊 Progress Update
==================
Completed: 15/47 (32%)
Successful: 14
Failed: 1

Recent:
  ✅ TechCorp Solutions Inc. - Senior Backend Developer
  ✅ Digital Innovations LLC - Frontend Engineer
  ✅ CloudScale Technologies - DevOps Engineer
  ✅ DataFlow Systems - Data Analyst
  ❌ StartupXYZ - Product Manager (company website not accessible)

Continuing...
```

## Step 6: Handle Errors

If a job fails (website down, company info not found, etc.):

1. Log the error in tracking database
2. Mark application as "incomplete"
3. Continue to next job
4. Do NOT stop the entire process

Error handling:
```json
{
  "job_id": "12345",
  "company": "StartupXYZ",
  "status": "failed",
  "error": "Company website not accessible",
  "attempted_at": "2025-11-22T15:45:00Z",
  "retry_possible": true
}
```

## Step 7: Completion Summary

When all jobs processed:
```
✅ Personalization Complete
===========================
Session: personalize_20251122_150000
Duration: 6 hours 23 minutes

Results:
  Total Jobs: 47
  Successful: 44 applications (94%)
  Failed: 3 jobs (6%)

Applications Created:
  ✓ 44 personalized CVs
  ✓ 44 personalized cover letters
  ✓ 44 company research reports

Output:
  applications/[job_id]_[company_name]/
    ├── cv.md
    ├── cover_letter.md
    └── company_research.json

  output/database/applications_tracker.json

Failed Jobs:
  1. StartupXYZ - Company website not accessible
  2. SecretCorp - No company information found
  3. PrivateFirm - Website requires login

Would you like to:
  - Review created applications
  - Retry failed jobs
  - Export application tracker
  - Generate application checklist
```

## Step 8: Update Filtered Database

Add application paths to filtered jobs database:
```json
{
  "id": "12345",
  "company": "TechCorp Solutions Inc.",
  "title": "Senior Backend Developer",
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
  "raw": { /* ... */ }
}
```

Save updated database to `output/database/jobs_filtered.json`

## Processing Rules

### Sequential Processing (CRITICAL)

**MUST:**
- Process one job at a time
- Invoke application-personalizer skill for each job individually
- Wait for completion before moving to next job
- Use fresh context for each job

**MUST NOT:**
- Create batch processing scripts
- Process multiple jobs in parallel
- Create loops in code
- Generate any .py, .sh, or executable files
- Reuse context between jobs

### Skill Invocation Pattern

```
For Job 1:
  → Invoke application-personalizer skill
  → Wait for completion
  → Update tracker
  → Report progress

For Job 2:
  → Invoke application-personalizer skill (fresh context)
  → Wait for completion
  → Update tracker
  → Report progress

[Repeat for each job...]
```

### Error Recovery

If skill fails for a job:
1. Log error details
2. Mark job as failed
3. **Continue to next job** (do not stop)
4. Collect failed jobs for potential retry

### Resource Management

- Each skill invocation is independent
- No shared state between invocations
- Fresh company research for each job
- Clean context for each application

## Output Structure

```
applications/
├── 12345_TechCorp_Solutions_Inc/
│   ├── cv.md
│   ├── cover_letter.md
│   └── company_research.json
├── 67890_Digital_Innovations_LLC/
│   ├── cv.md
│   ├── cover_letter.md
│   └── company_research.json
└── [job_id]_[company_name]/
    ├── cv.md
    ├── cover_letter.md
    └── company_research.json
```

## Tracking Database Schema

```json
{
  "personalization_session": "personalize_20251122_150000",
  "started_at": "2025-11-22T15:00:00Z",
  "completed_at": "2025-11-22T21:23:00Z",
  "source_filter": "filter_20251122_143000",
  "total_jobs": 47,
  "successful": 44,
  "failed": 3,
  "applications": [
    {
      "job_id": "12345",
      "company": "TechCorp Solutions Inc.",
      "title": "Senior Backend Developer",
      "status": "completed",
      "directory": "applications/12345_TechCorp_Solutions_Inc",
      "created_at": "2025-11-22T15:30:00Z",
      "research_quality": "high",
      "files_created": ["cv.md", "cover_letter.md", "company_research.json"],
      "processing_time_seconds": 287
    },
    {
      "job_id": "67890",
      "company": "Digital Innovations LLC",
      "title": "Frontend Engineer",
      "status": "completed",
      "directory": "applications/67890_Digital_Innovations_LLC",
      "created_at": "2025-11-22T15:38:00Z",
      "research_quality": "high",
      "files_created": ["cv.md", "cover_letter.md", "company_research.json"],
      "processing_time_seconds": 312
    },
    {
      "job_id": "99999",
      "company": "StartupXYZ",
      "title": "Product Manager",
      "status": "failed",
      "error": "Company website not accessible",
      "attempted_at": "2025-11-22T15:45:00Z",
      "retry_possible": true
    }
  ]
}
```

## User Interaction

Minimal interaction required:
1. **Start confirmation** - One time at beginning
2. **Progress updates** - Automatic every 5 jobs
3. **Error notifications** - Only for critical issues
4. **Completion summary** - Final report

User should be able to walk away and let the process run.

## Safety & Security

**File Operations:**
- ✅ Read from `user_docs/` templates
- ✅ Read from `output/database/jobs_filtered.json`
- ✅ Write to `applications/[job_id]_[company]/`
- ✅ Update `output/database/applications_tracker.json`
- ✅ Update `output/database/jobs_filtered.json`
- ❌ NO script creation (.py, .sh, .js)
- ❌ NO modifications to templates in `user_docs/`
- ❌ NO batch processing scripts

**Process Integrity:**
- One job at a time (sequential)
- Fresh skill invocation per job
- Independent context per application
- No shortcuts or optimizations that batch jobs

## Example Usage

User: `/personalize`

Expected flow:
1. Verify files exist
2. Load 47 filtered jobs
3. Ask confirmation
4. Process job #1 → Invoke skill → Save results → Update tracker
5. Process job #2 → Invoke skill → Save results → Update tracker
6. [Continue for all 47 jobs]
7. Show completion summary
8. Update filtered database with application paths

Total execution time: 4-8 hours (depending on research depth)
User intervention: Minimal (just start confirmation)

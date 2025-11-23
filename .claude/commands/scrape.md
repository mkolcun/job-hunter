---
description: Start a new job scraping session
---

I need you to start a new job scraping session. Follow these steps carefully:

## Step 1: Gather Requirements

Ask the user for:
1. **Target website URL**: The job listing page to scrape
   - **IMPORTANT**: Use the BASE URL without filters to scrape ALL jobs
   - ✅ Good: `https://www.jobsinvienna.com/` (scrapes all jobs)
   - ❌ Bad: `https://www.jobsinvienna.com/?language[]=en&location.address=Vienna` (filtered - may return 0 jobs)
   - Let the user filter/search the extracted data AFTER scraping
2. **Schema configuration**:
   - Use existing schema at `config/extraction_schema.json`?
   - Or create new schema (invoke schema-builder skill)?
3. **Optional limits**:
   - Maximum number of pages to scrape (default: unlimited)
   - Maximum number of jobs to extract (default: unlimited)

## Step 2: Schema Setup

**If using existing schema**:
- Verify `config/extraction_schema.json` exists
- Display schema summary (required fields, priorities)
- Confirm with user

**If creating new schema**:
- Use the **schema-builder** skill to guide user through schema creation
- Save to `config/extraction_schema.json`
- Show summary of created schema

## Step 3: Initialize Session

Create new session:
1. Generate session ID: `scrape_YYYYMMDD_HHMMSS` (use current timestamp)
2. Create directory structure:
   ```
   output/session_[SESSION_ID]/
   ├── jobs/
   ├── incomplete/
   ├── failed/
   └── checkpoints/
   ```
3. Create initial checkpoint at `output/checkpoints/checkpoint_latest.json`:
   ```json
   {
     "session_id": "scrape_[TIMESTAMP]",
     "start_time": "[ISO_TIMESTAMP]",
     "website": "[USER_PROVIDED_URL]",
     "schema_path": "config/extraction_schema.json",
     "status": "active",
     "stats": {
       "urls_discovered": 0,
       "urls_processed": 0,
       "jobs_extracted": 0,
       "jobs_incomplete": 0,
       "jobs_failed": 0
     }
   }
   ```

## Step 4: Switch to Scraping Mode

**Important**: Switch to **Scraping Mode** output style for the rest of this session by loading the scraping-mode instructions.

From this point on:
- Work autonomously
- Minimize user interruptions
- Report progress periodically
- Handle errors gracefully

## Step 5: Page Classification

Navigate to the target URL and use the **page-classifier** agent to determine:
- **Type A** (Job Detail): Extract this single job
- **Type B** (Job List): Extract all job URLs, then process each
- **Type C** (None): Not a job page, ask user to provide correct URL

## Step 6: URL Extraction (if Type B)

If the page is a job list:
1. Use the **url-extractor** agent to:
   - Extract all job URLs from current page
   - Detect and handle pagination
   - Build complete URL queue
2. Save URL queue to `output/url_queue.json`
3. Report: "Found [N] job URLs across [M] pages"

## Step 7: Data Extraction

For each job URL (or single job if Type A):

1. Use the **antibot-handler** agent to check for CAPTCHAs or anti-bot measures
   - If CAPTCHA detected: Pause and request user to solve it
   - If rate limiting: Implement delays and backoff

2. Use the **data-extractor** agent to extract job data:
   - Load extraction schema
   - Extract all configured fields
   - Assign confidence scores
   - Validate data quality

3. Save extracted job:
   - If complete (≥60% completeness): Save to `output/session_[ID]/jobs/[JOB_ID].json`
   - If incomplete (<60%): Save to `output/session_[ID]/incomplete/[JOB_ID].json`
   - Also append to aggregated file: `output/session_[ID]/jobs.json`

4. Update checkpoint every 10 jobs

5. Report progress every 10 jobs:
   ```
   📊 Progress: 45/120 jobs | 38 complete | 7 incomplete | ETA: 15 min
   ```

## Step 8: Handle Errors

**For each error encountered**:
- **Timeout**: Retry once, then skip
- **CAPTCHA**: Pause for human intervention
- **404/403**: Log and skip
- **Rate limiting**: Implement backoff and retry
- **Malformed HTML**: Best-effort extraction, flag as low quality

**Failed URLs**: Save to `output/session_[ID]/failed/failed_urls.json`

## Step 9: Session Completion

When all URLs processed:

1. Generate final checkpoint
2. Calculate statistics:
   - Total jobs extracted
   - Success rate
   - Average quality grade
   - Processing time

3. Display session summary:
   ```
   ✅ Scraping Session Complete
   =============================
   Session: scrape_20251119_143000
   Duration: 42 minutes

   Results:
     Jobs Extracted: 112/120 (93%)
     Complete: 98 jobs (87%)
     Incomplete: 14 jobs (12%)
     Failed: 6 URLs (5%)

   Quality:
     Avg Completeness: 76%
     Avg Confidence: 78%
     Quality Grade: B+

   Output:
     Jobs data: output/session_scrape_20251119_143000/jobs.json
     Incomplete: output/session_scrape_20251119_143000/incomplete/
     Failed URLs: output/session_scrape_20251119_143000/failed/failed_urls.json
   ```

4. Ask user if they want to:
   - Generate detailed quality report (`/analyze`)
   - Review incomplete or failed jobs
   - Start another scraping session

## Important Notes

- **Save progress continuously**: Update checkpoint every 10 jobs
- **Work autonomously**: Don't ask for confirmation on every action
- **Handle errors gracefully**: Log and continue, don't stop the entire session
- **Respect rate limits**: Use 2-5 second delays between requests
- **Quality over speed**: Prioritize accurate extraction over fast processing
- **Use all available agents**: page-classifier, url-extractor, data-extractor, antibot-handler

## Security Restrictions

**CRITICAL - File Writing Rules**:
- ✅ Agents can ONLY write `.json` files (and `.html` for debugging)
- ✅ Agents can ONLY write to `output/` directories
- ❌ Agents CANNOT create `.py`, `.sh`, `.js`, or any executable files
- ❌ Agents CANNOT create scripts or automation tools
- ❌ Agents CANNOT modify configuration files outside `output/`

**If any agent attempts to violate these rules**:
1. Immediately terminate the agent
2. Report the violation to the user
3. Delete any unauthorized files created
4. Log the incident

**Data Only**: Agents extract and store data, they do NOT generate code.

## Example Usage

User: `/scrape`
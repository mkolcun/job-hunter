---
description: Resume an interrupted scraping session
---

I need you to resume the previous scraping session from its last checkpoint. Follow these steps:

## Step 1: Find Latest Checkpoint

1. Look for `output/checkpoints/checkpoint_latest.json`
2. If not found:
   - Check `output/checkpoints/` for any checkpoint files
   - List available checkpoints to user
   - Ask which session to resume

## Step 2: Load Checkpoint Data

Read the checkpoint file and extract:
- **Session ID**: e.g., `scrape_20251119_143000`
- **Website**: Original target URL
- **Schema**: Path to extraction schema used
- **Statistics**: URLs processed, jobs extracted, etc.
- **Current URL**: Last URL being processed
- **Status**: Should be "active" or "paused"

## Step 3: Verify Session Data

Check that session files exist:
- Session directory: `output/session_[SESSION_ID]/`
- URL queue: `output/url_queue.json`
- Jobs directory: `output/session_[SESSION_ID]/jobs/`
- Checkpoint directory: `output/session_[SESSION_ID]/checkpoints/`

If any critical files are missing:
- Report the issue to user
- Ask if they want to start a new session instead
- Offer to salvage what data exists

## Step 4: Display Resume Status

Show user the session state:
```
📂 Found Session: scrape_20251119_143000
========================================
Started: 2025-11-19 14:30
Website: https://example-jobs.com

Progress:
  URLs: 87/450 processed (19%)
  Jobs: 78 extracted | 9 incomplete | 2 failed

Quality:
  Avg Completeness: 76%
  Avg Confidence: 74%
  Current Grade: B+

Last Activity: 2025-11-19 16:15 (2 hours ago)
Last URL: https://example-jobs.com/job/12387

Resume from URL #88?
```

## Step 5: Confirm with User

Ask: "Resume this session? (y/n)"

**If yes**: Proceed to Step 6
**If no**: Ask if they want to:
- Select a different session to resume
- Start a new session (`/scrape`)
- Archive this session

## Step 6: Load URL Queue

1. Read `output/url_queue.json`
2. Filter URLs by status:
   - **Completed**: Already processed, skip
   - **Failed**: Retry these URLs
   - **Pending**: Not yet processed, start here

3. Build processing queue from pending URLs

4. Report: "Resuming from URL #[N]. [M] URLs remaining."

## Step 7: Switch to Scraping Mode

Load **Scraping Mode** output style to continue autonomous operation.

## Step 8: Resume Processing

Continue from where the session left off:

1. Use the same extraction schema as original session
2. Process pending URLs with **data-extractor** agent
3. Retry failed URLs (up to 3 total attempts)
4. Update the same checkpoint file
5. Append to existing job files

**Important**:
- Maintain the same session ID
- Append to existing `jobs.json` file (don't overwrite)
- Update checkpoint with new statistics
- Keep existing processed jobs

## Step 9: Monitor Progress

Report progress every 10 jobs:
```
📊 Progress: 145/450 jobs | 132 complete | 13 incomplete | ETA: 20 min
```

Handle errors same as original session:
- **CAPTCHA**: Pause for human solving
- **Rate limiting**: Implement backoff
- **Timeouts**: Retry then skip

## Step 10: Session Completion

When all remaining URLs are processed:

1. Update final checkpoint with:
   - Status: "completed"
   - End time: current timestamp
   - Final statistics

2. Display completion summary:
   ```
   ✅ Session Resumed and Completed
   ================================
   Session: scrape_20251119_143000
   Original Start: 2025-11-19 14:30
   Resumed: 2025-11-19 18:45
   Completed: 2025-11-19 20:15
   Total Duration: 5h 45m (with 2h break)

   Final Results:
     Jobs: 412/450 extracted (91.6%)
     Complete: 378 (91.7%)
     Incomplete: 34 (8.3%)
     Failed: 38 URLs (8.4%)

   Quality:
     Avg Completeness: 78%
     Avg Confidence: 74%
     Final Grade: B+

   Output:
     Jobs data: output/session_scrape_20251119_143000/jobs.json
   ```

3. Offer next actions:
   - Generate quality report (`/analyze`)
   - Review failed URLs
   - Start new session

## Handling Edge Cases

### No Checkpoint Found
```
❌ No checkpoint found
=====================
Possible reasons:
  1. No previous scraping session exists
  2. Checkpoint file was deleted
  3. Session completed and archived

Would you like to:
  - Start a new scraping session (/scrape)
  - Check archived sessions
```

### Checkpoint Corrupted
```
⚠️  Checkpoint file corrupted
============================
Attempting to rebuild from job files...

Found: 78 job files in output/session_scrape_20251119_143000/jobs/
URL queue: Missing - cannot determine remaining URLs

Options:
  1. Count these 78 jobs as complete, start fresh URL extraction
  2. Start a new session instead
  3. Manually provide URL list to continue

Which would you prefer?
```

### Session Already Completed
```
ℹ️  Session Already Complete
===========================
Session: scrape_20251119_143000
Status: Completed on 2025-11-19 18:45
Jobs Extracted: 412/450 (91.6%)

This session has already finished. Would you like to:
  - View the quality report
  - Resume a different session
  - Start a new session
```

### Multiple Sessions Available
```
📂 Multiple Sessions Found
==========================
Which session would you like to resume?

1. scrape_20251119_143000 (most recent)
   Progress: 87/450 URLs (19%)
   Last active: 2 hours ago

2. scrape_20251118_093000
   Progress: 234/850 URLs (28%)
   Last active: 1 day ago

3. scrape_20251117_161500
   Progress: 67/320 URLs (21%)
   Last active: 2 days ago

Enter number (1-3) or 'latest' for most recent:
```

## Important Notes

- **Preserve session integrity**: Don't change session ID or overwrite existing data
- **Resume from checkpoint**: Use exact state from checkpoint file
- **Update statistics**: Increment counts, don't reset them
- **Respect original schema**: Use the same extraction schema as the original session
- **Handle new CAPTCHAs**: Anti-bot measures may appear even on resume
- **Verify timestamps**: Ensure checkpoint timestamps are updated

## Error Handling During Resume

If errors occur during resume:
1. **Save progress immediately**: Update checkpoint
2. **Don't lose work**: Keep successfully extracted jobs
3. **Report the issue**: Let user know what went wrong
4. **Offer alternatives**:
   - Retry the operation
   - Skip the problematic URL
   - Pause and save state
   - Abandon resume and salvage data

## Example Usage

User: `/resume`

Expected flow:
1. Find and load checkpoint
2. Show session summary
3. Ask for confirmation
4. Resume processing
5. Complete session
6. Show final results

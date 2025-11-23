---
description: Analyze scraping results and generate quality report
---

I need you to analyze the results of a scraping session and generate a comprehensive quality report. Follow these steps:

## Step 1: Switch to Analysis Mode

Load **Analysis Mode** output style for detailed, interactive analysis.

## Step 2: Identify Session

Ask user which session to analyze:
- **Latest session**: Use most recent checkpoint
- **Specific session**: User provides session ID
- **Current active**: If a session is in progress

If not specified, default to latest completed session.

## Step 3: Load Session Data

Read all data for the session:

1. **Checkpoint file**: `output/checkpoints/checkpoint_latest.json` or specific session
2. **All job files**: `output/session_[ID]/jobs/*.json`
3. **Incomplete jobs**: `output/session_[ID]/incomplete/*.json`
4. **Failed URLs**: `output/session_[ID]/failed/failed_urls.json`
5. **URL queue**: `output/url_queue.json` (if available)

## Step 4: Calculate Comprehensive Statistics

Compute the following metrics:

### Overall Metrics
- Total jobs processed
- Jobs extracted vs incomplete vs failed
- Average completeness (% of fields found per job)
- Average confidence across all fields
- Overall quality grade (A+ to F)
- Processing time statistics (total, average per job, fastest, slowest)

### Field-Level Metrics
For each field in the schema:
- **Coverage**: % of jobs where field was found
- **Average confidence**: Mean confidence score for this field
- **Source breakdown**: Structured vs labeled vs pattern vs inferred
- **Value distribution**: Common values, ranges, patterns
- **Format variations**: Different formats encountered

### Quality Distribution
- Count of jobs by quality grade (A, B, C, D, F)
- Percentage in each grade
- Trend comparison (if previous sessions available)

### Extraction Performance
- URLs processed per minute
- Average processing time per job
- Success rate (% of URLs successfully extracted)
- Failure patterns (common reasons for failure)

## Step 5: Use Quality Analyzer Skill

Invoke the **quality-analyzer** skill to perform deep analysis:

1. **Session-level analysis**: Overall quality metrics
2. **Field-level analysis**: Detailed breakdown per field
3. **Outlier detection**: Find anomalies and suspicious data
4. **Pattern identification**: What's working, what's failing

## Step 6: Identify Issues

Find and categorize problems:

### High-Priority Issues
- Required fields frequently missing (>30% missing)
- Fields with very low confidence (<60% average)
- High failure rate (>10% of URLs failed)
- Data quality anomalies (invalid values, outliers)

### Medium-Priority Issues
- Optional fields with low coverage
- Moderate confidence fields that could be improved
- Format inconsistencies
- Processing speed concerns

### Low-Priority Issues
- Rarely-used fields with low coverage
- Minor format variations
- Edge cases

## Step 7: Generate Recommendations

For each identified issue, provide:

1. **Issue description**: What's wrong
2. **Impact**: Why it matters
3. **Specific solution**: Exact steps to fix
4. **Example**: Show what the fix would look like
5. **Expected improvement**: Estimated impact
6. **Effort estimate**: Quick fix vs major work
7. **Priority**: High/Medium/Low based on impact

## Step 8: Create Detailed Report

Generate markdown report saved to `output/reports/quality_report_[SESSION_ID].md`:

### Report Structure

```markdown
# Scraping Session Quality Report

## Executive Summary
- Session ID, dates, duration
- Total jobs, success rate
- Overall quality grade
- Key findings (3-5 bullet points)

## Session Overview
- Website scraped
- Schema used
- Processing statistics
- Timeline

## Quality Metrics

### Overall Quality
- Completeness: X%
- Confidence: X%
- Grade: B+

### Field Coverage Table
| Field | Found | Avg Conf | Quality | Issues |
|-------|-------|----------|---------|--------|
| ...   | ...   | ...      | ...     | ...    |

### Quality Distribution Chart
A: XX jobs (XX%) ████████████
B: XX jobs (XX%) ████████████████
C: XX jobs (XX%) ██████

## Field-Level Analysis

### High-Performing Fields
(Fields with >90% coverage and >80% confidence)

### Needs Improvement
(Fields with <70% coverage or <70% confidence)

### Missing/Unused Fields
(Fields never or rarely found)

## Data Quality Issues

### Critical Issues
1. Issue description, impact, recommendation

### Warnings
1. Minor issues and suggestions

## Recommendations

### Priority 1: High Impact, Quick Wins
1. Specific actionable recommendation with example

### Priority 2: Medium Impact
1. Recommendations for moderate improvements

### Priority 3: Future Enhancements
1. Nice-to-have improvements

## Outliers & Anomalies
- Exceptional jobs (very high quality)
- Poor quality jobs (need review)
- Suspicious data values
- Processing anomalies

## Processing Performance
- Speed metrics
- Bottlenecks identified
- Optimization suggestions

## Comparison with Previous Sessions
(If applicable)
- Trend analysis
- What improved
- What regressed

## Appendix
- Complete field statistics
- Sample exceptional jobs
- Sample problematic jobs
- Failed URL list
```

## Step 9: Display Interactive Summary

Show user a concise summary in the terminal:

```
📊 Quality Analysis Complete
============================
Session: scrape_20251119_143000
Jobs Analyzed: 412

Overall Grade: B+ (78% complete, 74% confidence)

Top Strengths:
  ✓ Excellent coverage on core fields (title, company, location)
  ✓ High extraction quality from structured data
  ✓ Good processing speed (3.1 jobs/min)

Top Issues:
  ⚠ Contact email missing in 52% of jobs
  ⚠ Salary information missing in 29% of jobs
  ⚠ Benefits rarely extracted (65% missing)

Quick Win Recommendations:
  1. Add email search in footer sections (+15-20% coverage)
  2. Add European salary format patterns (+8-10% coverage)
  3. Make contactPhone optional (currently 69% missing)

Full report saved to:
  output/reports/quality_report_scrape_20251119_143000.md

Would you like me to:
  - Show detailed field analysis
  - Deep dive into specific field (which one?)
  - Compare with previous sessions
  - Implement recommended improvements
```

## Step 10: Offer Drill-Down Options

Ask user if they want to explore further:

**Deep Dive Options**:
- "Analyze the [field name] field in detail"
- "Show me examples of exceptional jobs"
- "Show me problematic jobs that need review"
- "Compare quality across the last 5 sessions"
- "Find all jobs missing required fields"

**Action Options**:
- "Update schema based on recommendations"
- "Re-extract incomplete jobs with improved patterns"
- "Export data quality metrics to CSV"
- "Generate executive summary for stakeholders"

## Analysis Types

### Quick Analysis (Default)
- Overall metrics
- Field coverage table
- Top 3 issues
- Top 3 recommendations
- ~2-3 minutes

### Detailed Analysis
- Everything in Quick Analysis
- Field-by-field deep dive
- Outlier detection
- Trend analysis
- Full markdown report
- ~5-10 minutes

### Custom Analysis
Ask user what to focus on:
- Specific fields only
- Quality outliers
- Performance metrics
- Comparison with previous sessions

## Error Handling

### Session Not Found
```
❌ Session Not Found
===================
Session ID: scrape_20251119_143000

Could not find session data. Checked:
  - output/session_scrape_20251119_143000/
  - output/checkpoints/checkpoint_latest.json

Available sessions:
  1. scrape_20251118_093000 (485 jobs)
  2. scrape_20251117_161500 (320 jobs)

Analyze one of these instead?
```

### Incomplete Session
```
⚠️  Session In Progress
======================
Session: scrape_20251119_143000
Status: Active
Progress: 87/450 jobs (19%)

This session is not complete yet.

Options:
  1. Analyze data collected so far (87 jobs)
  2. Wait for session to complete
  3. Analyze a completed session instead

What would you prefer?
```

### No Jobs Found
```
❌ No Jobs to Analyze
====================
Session: scrape_20251119_143000
Job files found: 0

The session directory exists but contains no job data.
This could mean:
  - Session was started but no jobs were extracted
  - Job files were moved or deleted
  - Wrong session directory

Cannot proceed with analysis.
```

## Best Practices

1. **Always save report**: Even for quick analysis, save markdown report
2. **Be specific in recommendations**: Show exact patterns, schemas, code
3. **Provide examples**: Show both good and bad examples
4. **Quantify improvements**: "Expected +15% coverage" not "will improve"
5. **Prioritize by impact**: Focus on high-value, achievable improvements
6. **Compare over time**: Show trends when possible
7. **Be interactive**: Offer drill-down options based on findings
8. **Visual formatting**: Use tables, charts, progress bars liberally

## Example Usage

User: `/analyze`

Expected flow:
1. Ask which session (default to latest)
2. Load all session data
3. Calculate comprehensive statistics
4. Use quality-analyzer skill
5. Generate detailed report
6. Show interactive summary
7. Offer drill-down options
8. Save report to file

## Output Files

After analysis:
- `output/reports/quality_report_[SESSION_ID].md` - Full detailed report
- `output/reports/summary_[SESSION_ID].txt` - Quick summary
- `output/reports/recommendations_[SESSION_ID].json` - Machine-readable recommendations

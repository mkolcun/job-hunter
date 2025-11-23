---
name: quality-analyzer
description: Analyzes quality of extracted job data, identifies issues, and suggests improvements. Use after scraping to evaluate data completeness and accuracy.
allowed-tools: Read, Grep, Bash
---

# Data Quality Analyzer

## Purpose
Evaluate the quality of extracted job data and provide actionable insights for improving extraction accuracy and completeness.

## When to Use This Skill

Use this skill when:
- Scraping session is complete
- Want to evaluate data quality
- Need to identify extraction issues
- Looking for improvement opportunities
- Validating schema effectiveness

## Analysis Dimensions

### 1. Completeness
Measures how many requested fields were successfully extracted.

**Metrics**:
- **Field Coverage**: % of jobs with each field populated
- **Overall Completeness**: Average % of fields found per job
- **Missing Field Patterns**: Which fields are consistently missing

**Calculation**:
```
Field Coverage = (jobs_with_field / total_jobs) * 100
Overall Completeness = (avg_fields_found / fields_requested) * 100
```

### 2. Confidence
Measures confidence in extracted data accuracy.

**Metrics**:
- **Average Confidence**: Mean confidence score across all fields
- **Per-Field Confidence**: Average confidence for each field type
- **Low Confidence Rate**: % of fields below threshold (60%)

**Confidence Levels**:
- **90-100%**: Excellent (structured data, labeled fields)
- **70-89%**: Good (pattern matches in labeled context)
- **50-69%**: Fair (pattern matches, section-based)
- **<50%**: Poor (inferred, guessed)

### 3. Consistency
Measures data format consistency and standardization.

**Checks**:
- **Format Consistency**: Are dates, salaries, locations in standard format?
- **Value Normalization**: Are similar values normalized (e.g., "remote" vs "100% remote")?
- **Duplicate Detection**: Are there duplicate jobs?

### 4. Source Quality
Tracks how data was extracted.

**Source Types**:
- **Structured**: From Schema.org, JSON-LD (highest quality)
- **Labeled**: From labeled HTML fields (high quality)
- **Pattern**: From regex pattern matches (medium quality)
- **Section**: From content sectioning (medium quality)
- **Inferred**: From contextual clues (low quality)

## Analysis Commands

### 1. Analyze Single Job

**Command**: Analyze quality of a single job

**Process**:
1. Load job JSON file
2. Check each field for:
   - Presence (found/missing)
   - Confidence score
   - Source type
   - Format validation
3. Calculate completeness
4. Assign quality grade

**Output**:
```
📊 Job Quality Analysis
=======================
Job ID: 12345
URL: https://example.com/job/12345

Field Analysis:
  ✓ title: "Senior Software Engineer" (95% conf, labeled)
  ✓ company: "Tech Corp GmbH" (93% conf, labeled)
  ✓ location: "Vienna, Austria" (88% conf, labeled)
  ✓ salary: €60,000 - €80,000 (73% conf, pattern)
  ✓ description: 850 words (91% conf, structured)
  ✓ requirements: 8 items (78% conf, section)
  ⚠ contactEmail: jobs@techcorp.com (65% conf, pattern)
  ✗ contactPhone: Not found
  ✗ benefits: Not found

Completeness: 7/9 fields (78%)
Avg Confidence: 83%
Quality Grade: B+

Issues:
  - Low confidence on contactEmail (65%)
  - Missing contactPhone and benefits

Recommendations:
  - Verify contactEmail manually
  - Check page for hidden contact info
```

**Usage**:
```
Analyze quality of job file output/jobs/12345.json
```

### 2. Analyze Full Session

**Command**: Analyze all jobs in a session

**Process**:
1. Load all job files from session
2. Calculate aggregate statistics:
   - Field coverage per field type
   - Average confidence per field type
   - Completeness distribution
   - Quality grade distribution
3. Identify patterns:
   - Most commonly missing fields
   - Consistently low-confidence fields
   - Extraction source breakdown
4. Generate comprehensive report

**Output**:
```
📊 Session Quality Analysis
===========================
Session: scrape_20251119_143000
Total Jobs: 412

Overall Metrics:
  Completeness: 78% (avg 11.7/15 fields)
  Avg Confidence: 74%
  Quality Grade: B+

Field Coverage:
  ┌─────────────────┬─────────┬────────────┬─────────┐
  │ Field           │ Found   │ Avg Conf   │ Quality │
  ├─────────────────┼─────────┼────────────┼─────────┤
  │ title           │ 100%    │ 95%        │ A+      │
  │ company         │ 100%    │ 93%        │ A+      │
  │ location        │ 98%     │ 88%        │ A       │
  │ description     │ 95%     │ 91%        │ A       │
  │ requirements    │ 82%     │ 78%        │ B+      │
  │ responsibilities│ 79%     │ 76%        │ B+      │
  │ salary          │ 71%     │ 73%        │ B       │
  │ jobType         │ 68%     │ 71%        │ B       │
  │ experienceLevel │ 62%     │ 68%        │ C+      │
  │ contactEmail    │ 48%     │ 68%        │ C+      │
  │ contactPhone    │ 31%     │ 65%        │ C       │
  │ benefits        │ 35%     │ 61%        │ C       │
  │ remotePolicy    │ 58%     │ 72%        │ B-      │
  │ companyDesc     │ 41%     │ 67%        │ C+      │
  │ contactPerson   │ 23%     │ 58%        │ D+      │
  └─────────────────┴─────────┴────────────┴─────────┘

Quality Distribution:
  A (90-100%): 156 jobs (38%) ████████████████████
  B (75-89%):  189 jobs (46%) ██████████████████████████
  C (60-74%):   58 jobs (14%) ████████
  D (<60%):      9 jobs (2%)  ██

Extraction Sources:
  Structured:  12% (best quality)
  Labeled:     45% (high quality)
  Pattern:     31% (medium quality)
  Section:     10% (medium quality)
  Inferred:     2% (low quality)

Top Issues:
  1. contactEmail missing in 52% of jobs (214/412)
  2. contactPhone missing in 69% of jobs (284/412)
  3. benefits missing in 65% of jobs (268/412)
  4. contactPerson low confidence (58% avg)
  5. salary missing in 29% of jobs (119/412)
```

**Usage**:
```
Analyze quality for the current scraping session
```

### 3. Compare Sessions

**Command**: Compare quality across multiple sessions

**Process**:
1. Load multiple session reports
2. Compare metrics:
   - Field coverage trends
   - Confidence score trends
   - Quality grade distribution changes
3. Identify improvements or regressions

**Output**:
```
📊 Session Comparison
=====================

                    Session 1    Session 2    Session 3    Trend
                    Nov 17       Nov 18       Nov 19
Jobs Processed      320          485          412          ─
Avg Completeness    72%          76%          78%          ↗
Avg Confidence      69%          72%          74%          ↗
Quality Grade       B            B+           B+           ↗

Field Coverage Trends:
  salary:           65% → 69% → 71%  ↗ Improving
  contactEmail:     41% → 44% → 48%  ↗ Improving
  benefits:         28% → 32% → 35%  ↗ Improving
  contactPhone:     35% → 32% → 31%  ↘ Declining

Recommendations:
  - contactPhone extraction is declining, review patterns
  - salary and contactEmail showing steady improvement
  - Overall quality trending upward
```

**Usage**:
```
Compare quality across the last 3 scraping sessions
```

### 4. Field-Level Analysis

**Command**: Deep dive into specific field

**Process**:
1. Load all jobs
2. Extract all instances of specified field
3. Analyze patterns:
   - Value distribution
   - Format variations
   - Confidence distribution
   - Source type breakdown
   - Common issues

**Output** (example for "salary"):
```
📊 Field Analysis: salary
==========================
Jobs Analyzed: 412
Coverage: 71% (292/412 found)

Value Distribution:
  €40k-€60k:   78 jobs (27%)
  €60k-€80k:   112 jobs (38%)
  €80k-€100k:  89 jobs (30%)
  €100k+:      13 jobs (5%)

Currency Distribution:
  EUR: 245 (84%)
  USD: 38 (13%)
  GBP: 9 (3%)

Period Distribution:
  Annual: 278 (95%)
  Monthly: 12 (4%)
  Hourly: 2 (1%)

Confidence Distribution:
  90-100%: 45 (15%)  - Structured data
  70-89%:  178 (61%) - Labeled fields
  50-69%:  69 (24%)  - Pattern matches
  <50%:    0 (0%)

Extraction Sources:
  Labeled:     198 (68%)
  Pattern:     87 (30%)
  Structured:  7 (2%)

Format Variations Found:
  ✓ "€60,000 - €80,000 per year"  (112 jobs)
  ✓ "60k-80k EUR"                 (67 jobs)
  ✓ "€60.000 - €80.000"           (45 jobs)
  ⚠ "competitive salary"          (34 jobs) - Not extracted
  ⚠ "salary to be discussed"      (23 jobs) - Not extracted

Common Issues:
  1. 34 jobs mention "competitive salary" - no amount extracted
  2. 23 jobs say "to be discussed" - no range provided
  3. 12 jobs have only minimum salary - no maximum
  4. 8 jobs have ambiguous ranges - needs validation

Recommendations:
  1. Add pattern for "competitive" keyword (mark as unknown)
  2. Handle single-value salaries (assume +20% range)
  3. Add more European number format variations (60.000 vs 60,000)
```

**Usage**:
```
Analyze the salary field across all jobs
```

### 5. Identify Outliers

**Command**: Find anomalous jobs or data

**Process**:
1. Calculate statistical norms (mean, median, std dev)
2. Identify outliers:
   - Unusually high/low completeness
   - Extreme confidence scores
   - Abnormal processing times
   - Suspicious data values

**Output**:
```
📊 Outlier Detection
====================

Quality Outliers:
  Exceptionally Good (>95% complete, >90% conf):
    - Job 12345: 100% complete, 96% conf
    - Job 12567: 100% complete, 94% conf
    (15 jobs total)

  Exceptionally Poor (<40% complete or <50% conf):
    - Job 12489: 27% complete, 48% conf
    - Job 12501: 33% complete, 52% conf
    (9 jobs total)

Data Anomalies:
  Suspicious Salaries:
    - Job 12678: €10,000 - €200,000 (range too wide)
    - Job 12701: €500,000+ (outlier high)

  Invalid Locations:
    - Job 12445: "Earth" (too vague)
    - Job 12512: "123 Main St" (street address, not city)

  Processing Time Anomalies:
    - Job 12489: 2m 34s (avg: 34s) - timeout likely
    - Job 12567: 3m 12s - very slow

Recommendations:
  - Review 9 low-quality jobs manually
  - Validate suspicious salary ranges
  - Improve location extraction patterns
  - Investigate slow jobs for optimization
```

**Usage**:
```
Find outliers and anomalies in the scraping data
```

## Quality Grades

### Grading System

```
A+ (95-100%): Exceptional
  - Nearly perfect completeness (>95%)
  - Very high confidence (>90%)
  - All required fields + most optional
  - Primarily structured/labeled sources

A (90-94%): Excellent
  - High completeness (90-95%)
  - High confidence (85-90%)
  - All required fields + many optional
  - Mix of structured and labeled

B+ (85-89%): Very Good
  - Good completeness (85-90%)
  - Good confidence (80-85%)
  - All required fields + some optional

B (75-84%): Good
  - Acceptable completeness (75-85%)
  - Acceptable confidence (70-80%)
  - All required fields met

C+ (70-74%): Fair
  - Moderate completeness (70-75%)
  - Moderate confidence (65-70%)
  - Required fields mostly met

C (60-69%): Acceptable
  - Low completeness (60-70%)
  - Low confidence (60-65%)
  - Some required fields may be missing

D (50-59%): Poor
  - Very low completeness (<60%)
  - Very low confidence (<60%)
  - Missing required fields

F (<50%): Failed
  - Insufficient data
  - Should be marked as incomplete
```

## Recommendations Engine

Based on analysis, suggest specific improvements:

### Recommendation Categories

1. **Schema Adjustments**
   - Make fields optional if rarely found
   - Remove fields never found
   - Add custom fields for common patterns

2. **Pattern Improvements**
   - Add missing regex patterns
   - Support additional formats
   - Multi-language pattern variations

3. **Extraction Strategy Changes**
   - Use different extraction methods
   - Adjust confidence thresholds
   - Enable/disable structured data priority

4. **Website-Specific Optimizations**
   - Site-specific extraction hints
   - Custom field mappings
   - Known issue workarounds

## Best Practices

1. **Analyze after every session**: Track quality trends
2. **Focus on high-value fields**: Prioritize salary, contact info improvements
3. **Set realistic goals**: 80% completeness is excellent for many fields
4. **Iterate on schema**: Continuously improve based on analysis
5. **Validate samples**: Manually check 10-20 jobs to verify accuracy
6. **Track trends**: Compare sessions to measure improvement

## Usage Examples

**Quick analysis**:
```
Analyze quality of the current scraping session
```

**Deep dive on field**:
```
Analyze the contactEmail field in detail
```

**Compare over time**:
```
Compare quality across the last 5 sessions
```

**Find problems**:
```
Find outliers and data quality issues
```

**Single job review**:
```
Analyze quality of job 12345
```

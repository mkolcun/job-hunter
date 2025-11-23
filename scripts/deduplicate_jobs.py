#!/usr/bin/env python3
"""
Job Deduplication Script
Identifies and merges duplicate job postings across sessions
"""

import os
import json
from datetime import datetime
from collections import defaultdict
import re
from difflib import SequenceMatcher

# Paths
MASTER_DB_PATH = "output/database/jobs_master.json"
DUPLICATES_PATH = "output/database/jobs_duplicates.json"
REVIEW_QUEUE_PATH = "output/database/review_queue.json"
UNIQUE_JOBS_PATH = "output/database/jobs_unique.json"
REPORT_PATH = "output/reports/deduplication_report.md"

def normalize_text(text):
    """Normalize text for comparison"""
    if not text:
        return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    return text.strip()

def normalize_company(company):
    """Normalize company name"""
    if isinstance(company, dict):
        company = company.get('name', '')
    company = normalize_text(company)
    # Remove common suffixes
    company = re.sub(r'\b(gmbh|inc|llc|ltd|ag|corp|corporation|company)\b', '', company)
    return company.strip()

def normalize_location(location):
    """Normalize location"""
    if isinstance(location, dict):
        city = location.get('city', '')
        country = location.get('country', '')
        return normalize_text(f"{city} {country}")
    return normalize_text(location)

def text_similarity(text1, text2):
    """Calculate text similarity using SequenceMatcher"""
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, normalize_text(text1), normalize_text(text2)).ratio()

def jaccard_similarity(text1, text2):
    """Calculate Jaccard similarity between two texts"""
    if not text1 or not text2:
        return 0.0

    words1 = set(normalize_text(text1).split())
    words2 = set(normalize_text(text2).split())

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union) if union else 0.0

def extract_job_url(job):
    """Extract job URL from various field names"""
    for field in ['url', 'source_url', 'applicationUrl', 'job_url', 'link']:
        if field in job and job[field]:
            return str(job[field])
    return None

def calculate_completeness(job):
    """Calculate job data completeness score"""
    important_fields = ['title', 'company', 'location', 'description',
                       'requirements', 'salary', 'contactEmail', 'benefits']

    filled = 0
    for field in important_fields:
        if field in job and job[field]:
            if isinstance(job[field], str) and len(job[field]) > 0:
                filled += 1
            elif isinstance(job[field], dict) and job[field]:
                filled += 1
            elif isinstance(job[field], list) and len(job[field]) > 0:
                filled += 1

    return (filled / len(important_fields)) * 100

def detect_duplicates(jobs):
    """Detect duplicate jobs using multiple strategies"""

    print("🔍 Phase 3: Detecting Duplicates")
    print("=" * 80)
    print()

    duplicate_groups = []
    processed = set()

    # Strategy 1: Exact URL match
    print("Strategy 1: Exact URL matching...")
    url_map = defaultdict(list)
    for job in jobs:
        url = extract_job_url(job)
        if url:
            url_map[url].append(job)

    exact_matches = 0
    for url, job_list in url_map.items():
        if len(job_list) > 1:
            canonical = max(job_list, key=lambda j: calculate_completeness(j))
            duplicates = [j for j in job_list if j['master_id'] != canonical['master_id']]

            if duplicates:
                duplicate_groups.append({
                    'group_id': f"dup_{len(duplicate_groups)+1:03d}",
                    'canonical_job_id': canonical['master_id'],
                    'strategy': 'exact_url',
                    'confidence': 99,
                    'duplicates': [
                        {
                            'job_id': d['master_id'],
                            'session_id': d.get('session_source', 'unknown'),
                            'matched_fields': ['url']
                        } for d in duplicates
                    ]
                })
                exact_matches += len(duplicates)
                for job in job_list:
                    processed.add(job['master_id'])

    print(f"  ✓ Found {exact_matches} exact URL matches")

    # Strategy 2: Normalized composite key (company + title + location)
    print("Strategy 2: Normalized composite key matching...")
    composite_map = defaultdict(list)

    for job in jobs:
        if job['master_id'] in processed:
            continue

        company = normalize_company(job.get('company', ''))
        title = normalize_text(job.get('title', ''))
        location = normalize_location(job.get('location', ''))

        if company and title:
            key = f"{company}|{title}|{location}"
            composite_map[key].append(job)

    composite_matches = 0
    for key, job_list in composite_map.items():
        if len(job_list) > 1:
            # Verify with description similarity
            canonical = max(job_list, key=lambda j: calculate_completeness(j))

            for other_job in job_list:
                if other_job['master_id'] == canonical['master_id']:
                    continue

                desc_sim = jaccard_similarity(
                    canonical.get('description', ''),
                    other_job.get('description', '')
                )

                confidence = 85 + (desc_sim * 10)  # 85-95% based on description

                if confidence >= 85:
                    duplicate_groups.append({
                        'group_id': f"dup_{len(duplicate_groups)+1:03d}",
                        'canonical_job_id': canonical['master_id'],
                        'strategy': 'normalized_composite',
                        'confidence': int(confidence),
                        'duplicates': [{
                            'job_id': other_job['master_id'],
                            'session_id': other_job.get('session_source', 'unknown'),
                            'matched_fields': ['company', 'title', 'location'],
                            'description_similarity': round(desc_sim * 100, 1)
                        }]
                    })
                    composite_matches += 1
                    processed.add(other_job['master_id'])

    print(f"  ✓ Found {composite_matches} normalized composite matches")

    # Strategy 3: Fuzzy title + company match
    print("Strategy 3: Fuzzy matching...")
    fuzzy_matches = 0

    jobs_to_check = [j for j in jobs if j['master_id'] not in processed]

    for i, job1 in enumerate(jobs_to_check):
        for job2 in jobs_to_check[i+1:]:
            if job2['master_id'] in processed:
                continue

            # Compare company
            company1 = normalize_company(job1.get('company', ''))
            company2 = normalize_company(job2.get('company', ''))

            if not company1 or not company2:
                continue

            company_sim = text_similarity(company1, company2)

            if company_sim < 0.8:
                continue

            # Compare title
            title_sim = text_similarity(job1.get('title', ''), job2.get('title', ''))

            if title_sim < 0.75:
                continue

            # Compare location
            location_sim = text_similarity(
                normalize_location(job1.get('location', '')),
                normalize_location(job2.get('location', ''))
            )

            # Calculate overall confidence
            confidence = (company_sim * 0.4 + title_sim * 0.4 + location_sim * 0.2) * 100

            if confidence >= 75:
                canonical = job1 if calculate_completeness(job1) > calculate_completeness(job2) else job2
                duplicate = job2 if canonical == job1 else job1

                duplicate_groups.append({
                    'group_id': f"dup_{len(duplicate_groups)+1:03d}",
                    'canonical_job_id': canonical['master_id'],
                    'strategy': 'fuzzy_match',
                    'confidence': int(confidence),
                    'duplicates': [{
                        'job_id': duplicate['master_id'],
                        'session_id': duplicate.get('session_source', 'unknown'),
                        'matched_fields': ['company', 'title'],
                        'similarities': {
                            'company': round(company_sim * 100, 1),
                            'title': round(title_sim * 100, 1),
                            'location': round(location_sim * 100, 1)
                        }
                    }]
                })
                fuzzy_matches += 1
                processed.add(duplicate['master_id'])

    print(f"  ✓ Found {fuzzy_matches} fuzzy matches")
    print()

    return duplicate_groups

def merge_duplicates(jobs, duplicate_groups, threshold=85):
    """Merge duplicate jobs based on confidence threshold"""

    print(f"🔀 Phase 4: Merging Duplicates (threshold ≥{threshold}%)")
    print("=" * 80)
    print()

    # Filter groups by threshold
    groups_to_merge = [g for g in duplicate_groups if g['confidence'] >= threshold]
    groups_to_review = [g for g in duplicate_groups if 60 <= g['confidence'] < threshold]

    print(f"Merging {len(groups_to_merge)} duplicate groups...")
    print(f"Flagging {len(groups_to_review)} groups for manual review...")
    print()

    # Create job lookup
    job_map = {job['master_id']: job for job in jobs}

    # Track which jobs to remove
    jobs_to_remove = set()

    # Merge process
    merged_count = 0
    for group in groups_to_merge:
        canonical_id = group['canonical_job_id']
        canonical_job = job_map.get(canonical_id)

        if not canonical_job:
            continue

        # Collect data from duplicates
        duplicate_urls = [extract_job_url(canonical_job)]
        session_sources = [canonical_job.get('session_source')]
        original_ids = [canonical_job.get('original_id')]

        for dup in group['duplicates']:
            dup_job = job_map.get(dup['job_id'])
            if not dup_job:
                continue

            # Collect URLs and metadata
            dup_url = extract_job_url(dup_job)
            if dup_url and dup_url not in duplicate_urls:
                duplicate_urls.append(dup_url)

            if dup_job.get('session_source') not in session_sources:
                session_sources.append(dup_job.get('session_source'))

            if dup_job.get('original_id') not in original_ids:
                original_ids.append(dup_job.get('original_id'))

            # Fill missing fields from duplicate (if duplicate has better data)
            for field in ['salary', 'contactEmail', 'benefits', 'requirements']:
                if field in dup_job and dup_job[field]:
                    if field not in canonical_job or not canonical_job[field]:
                        canonical_job[field] = dup_job[field]
                        canonical_job[f'{field}_source'] = dup_job.get('session_source')

            jobs_to_remove.add(dup['job_id'])

        # Add merge metadata
        canonical_job['duplicate_metadata'] = {
            'is_canonical': True,
            'duplicate_count': len(group['duplicates']),
            'duplicate_urls': duplicate_urls,
            'session_sources': session_sources,
            'original_ids': original_ids,
            'merge_date': datetime.utcnow().isoformat() + "Z",
            'merge_strategy': group['strategy'],
            'merge_confidence': group['confidence']
        }

        merged_count += 1

    # Remove duplicate jobs
    unique_jobs = [j for j in jobs if j['master_id'] not in jobs_to_remove]

    print(f"✓ Merged {len(jobs_to_remove)} duplicate jobs")
    print(f"✓ Unique jobs: {len(unique_jobs)}")
    print()

    return unique_jobs, groups_to_review

def calculate_quality_improvement(original_jobs, unique_jobs):
    """Calculate quality metrics improvement"""

    def avg_completeness(jobs):
        if not jobs:
            return 0
        return sum(calculate_completeness(j) for j in jobs) / len(jobs)

    def field_coverage(jobs, field):
        if not jobs:
            return 0
        count = sum(1 for j in jobs if field in j and j[field])
        return (count / len(jobs)) * 100

    original_completeness = avg_completeness(original_jobs)
    unique_completeness = avg_completeness(unique_jobs)

    improvements = {}
    for field in ['salary', 'contactEmail', 'benefits', 'requirements']:
        before = field_coverage(original_jobs, field)
        after = field_coverage(unique_jobs, field)
        improvements[field] = {
            'before': round(before, 1),
            'after': round(after, 1),
            'improvement': round(after - before, 1)
        }

    return {
        'completeness': {
            'before': round(original_completeness, 1),
            'after': round(unique_completeness, 1),
            'improvement': round(unique_completeness - original_completeness, 1)
        },
        'fields': improvements
    }

def generate_report(original_jobs, unique_jobs, duplicate_groups, review_queue, quality_metrics):
    """Generate markdown deduplication report"""

    total_jobs = len(original_jobs)
    unique_count = len(unique_jobs)
    duplicate_count = total_jobs - unique_count
    duplicate_rate = (duplicate_count / total_jobs * 100) if total_jobs > 0 else 0

    # Strategy breakdown
    strategy_stats = defaultdict(lambda: {'count': 0, 'confidences': []})
    for group in duplicate_groups:
        strategy_stats[group['strategy']]['count'] += len(group['duplicates'])
        strategy_stats[group['strategy']]['confidences'].append(group['confidence'])

    report = f"""# Job Deduplication Report

**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
**Database**: {MASTER_DB_PATH}

## Summary

- **Total Jobs Analyzed**: {total_jobs:,}
- **Unique Jobs**: {unique_count:,} ({100 - duplicate_rate:.1f}%)
- **Duplicates Found**: {duplicate_count:,} ({duplicate_rate:.1f}%)
- **Duplicate Groups**: {len(duplicate_groups)}
- **Jobs Flagged for Review**: {len(review_queue)}

## Duplicate Detection by Strategy

| Strategy | Matches | Avg Confidence | % of Duplicates |
|----------|---------|----------------|-----------------|
"""

    for strategy, stats in strategy_stats.items():
        avg_conf = sum(stats['confidences']) / len(stats['confidences']) if stats['confidences'] else 0
        pct = (stats['count'] / duplicate_count * 100) if duplicate_count > 0 else 0
        report += f"| {strategy} | {stats['count']} | {avg_conf:.0f}% | {pct:.1f}% |\n"

    report += f"""
## Data Quality Improvement

### Overall Completeness
- **Before Merge**: {quality_metrics['completeness']['before']:.1f}%
- **After Merge**: {quality_metrics['completeness']['after']:.1f}%
- **Improvement**: +{quality_metrics['completeness']['improvement']:.1f}%

### Field Coverage Improvements

| Field | Before | After | Improvement |
|-------|--------|-------|-------------|
"""

    for field, metrics in quality_metrics['fields'].items():
        report += f"| {field} | {metrics['before']:.1f}% | {metrics['after']:.1f}% | +{metrics['improvement']:.1f}% |\n"

    report += f"""
## Manual Review Queue

**{len(review_queue)} jobs** flagged for manual review

Reasons:
"""

    review_reasons = defaultdict(int)
    for item in review_queue:
        reason = "Low confidence match (60-75%)" if item['confidence'] < 75 else "Other"
        review_reasons[reason] += 1

    for reason, count in review_reasons.items():
        report += f"- {reason}: {count} jobs\n"

    report += f"""
## Recommendations

1. **Review flagged jobs**: {len(review_queue)} jobs need manual verification in `{REVIEW_QUEUE_PATH}`
2. **Quality improvement targets**:
"""

    for field, metrics in quality_metrics['fields'].items():
        if metrics['after'] < 60:
            report += f"   - Improve {field} extraction (current: {metrics['after']:.1f}%)\n"

    report += f"""
## Files Generated

- **Unique Jobs Database**: `{UNIQUE_JOBS_PATH}`
- **Duplicates Database**: `{DUPLICATES_PATH}`
- **Review Queue**: `{REVIEW_QUEUE_PATH}`
- **This Report**: `{REPORT_PATH}`

## Next Steps

1. ✓ Deduplication complete
2. → Review manual queue: `{REVIEW_QUEUE_PATH}`
3. → Export final dataset: Use consolidator skill
4. → Quality analysis: Use quality-analyzer skill
"""

    return report

def main():
    """Main deduplication workflow"""

    # Load master database
    print("Loading master database...")
    with open(MASTER_DB_PATH, 'r', encoding='utf-8') as f:
        master_db = json.load(f)

    original_jobs = master_db['jobs']
    print(f"Loaded {len(original_jobs)} jobs")
    print()

    # Detect duplicates
    duplicate_groups = detect_duplicates(original_jobs)

    # Ask user for threshold (for now, use moderate 85%)
    threshold = 85

    # Merge duplicates
    unique_jobs, review_queue = merge_duplicates(original_jobs, duplicate_groups, threshold)

    # Calculate quality improvements
    quality_metrics = calculate_quality_improvement(original_jobs, unique_jobs)

    # Save unique jobs database
    unique_db = {
        **master_db,
        'deduplication_date': datetime.utcnow().isoformat() + "Z",
        'deduplication_threshold': threshold,
        'original_job_count': len(original_jobs),
        'unique_job_count': len(unique_jobs),
        'jobs': unique_jobs
    }

    with open(UNIQUE_JOBS_PATH, 'w', encoding='utf-8') as f:
        json.dump(unique_db, f, indent=2, ensure_ascii=False)

    # Save duplicates database
    duplicates_db = {
        'analysis_date': datetime.utcnow().isoformat() + "Z",
        'total_jobs': len(original_jobs),
        'unique_jobs': len(unique_jobs),
        'duplicate_groups': len(duplicate_groups),
        'groups': duplicate_groups
    }

    with open(DUPLICATES_PATH, 'w', encoding='utf-8') as f:
        json.dump(duplicates_db, f, indent=2, ensure_ascii=False)

    # Save review queue
    review_queue_db = {
        'last_updated': datetime.utcnow().isoformat() + "Z",
        'pending_reviews': len(review_queue),
        'items': [
            {
                'review_id': f"review_{i+1:03d}",
                'priority': 'medium' if g['confidence'] >= 70 else 'high',
                'group_id': g['group_id'],
                'reason': 'low_confidence_match',
                'confidence': g['confidence'],
                'canonical_job_id': g['canonical_job_id'],
                'duplicate_ids': [d['job_id'] for d in g['duplicates']],
                'strategy': g['strategy']
            }
            for i, g in enumerate(review_queue)
        ]
    }

    with open(REVIEW_QUEUE_PATH, 'w', encoding='utf-8') as f:
        json.dump(review_queue_db, f, indent=2, ensure_ascii=False)

    # Generate report
    report = generate_report(original_jobs, unique_jobs, duplicate_groups, review_queue_db['items'], quality_metrics)

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)

    # Print Phase 5 summary
    print("=" * 80)
    print("📊 Phase 5: Summary")
    print("=" * 80)
    print()
    print("BEFORE:")
    print(f"  Sessions: {master_db['totals']['sessions_consolidated']}")
    print(f"  Total jobs scraped: {len(original_jobs):,}")
    print()
    print("AFTER DEDUPLICATION:")
    print(f"  Unique jobs: {len(unique_jobs):,}")
    print(f"  Duplicates removed: {len(original_jobs) - len(unique_jobs):,} ({(len(original_jobs) - len(unique_jobs)) / len(original_jobs) * 100:.1f}%)")
    print(f"  Pending review: {len(review_queue)}")
    print()
    print("QUALITY IMPROVEMENT:")
    print(f"  Completeness: {quality_metrics['completeness']['before']:.1f}% → {quality_metrics['completeness']['after']:.1f}% (+{quality_metrics['completeness']['improvement']:.1f}%)")
    print()
    print("FILES CREATED:")
    print(f"  Unique jobs DB: {UNIQUE_JOBS_PATH}")
    print(f"  Duplicates DB: {DUPLICATES_PATH}")
    print(f"  Review queue: {REVIEW_QUEUE_PATH}")
    print(f"  Report: {REPORT_PATH}")
    print()
    print("NEXT STEPS:")
    print(f"  1. Review {len(review_queue)} flagged jobs in review queue")
    print("  2. Export unique jobs to desired format")
    print("  3. Run quality analysis")
    print()

if __name__ == "__main__":
    main()

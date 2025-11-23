#!/usr/bin/env python3
"""
Job Consolidation Script
Merges all scraping sessions into a unified master database
"""

import os
import json
from datetime import datetime
from collections import defaultdict

# Session paths
SESSIONS = [
    "output/data_analysis_session_scrape_20251121_192443",
    "output/data_analyst_session_scrape_20251120_182316",
    "output/session_scrape_20251120_184825",
    "output/session_scrape_20251121_123159",
    "output/session_scrape_20251121_181317"
]

OUTPUT_DIR = "output/database"
BACKUP_DIR = "output/database/backups"
REPORTS_DIR = "output/reports"

def extract_session_metadata(session_path):
    """Extract metadata from session directory name"""
    session_name = os.path.basename(session_path)
    parts = session_name.split("_")

    # Extract date and time
    date_str = None
    time_str = None
    for i, part in enumerate(parts):
        if part.startswith("202511") and len(part) == 8:
            date_str = f"{part[0:4]}-{part[4:6]}-{part[6:8]}"
            if i+1 < len(parts) and parts[i+1].isdigit() and len(parts[i+1]) == 6:
                time_str = f"{parts[i+1][0:2]}:{parts[i+1][2:4]}:{parts[i+1][4:6]}"

    timestamp = f"{date_str}T{time_str}Z" if date_str and time_str else None

    # Determine session type
    session_type = "general_search"
    if "data_analyst" in session_name:
        session_type = "filtered_search_data_analyst"
    elif "data_analysis" in session_name:
        session_type = "filtered_search_data_analysis"

    return {
        "session_id": session_name,
        "session_date": timestamp,
        "session_type": session_type,
        "session_path": session_path
    }

def load_job_from_file(file_path, session_metadata):
    """Load a single job file and normalize its structure"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            job_data = json.load(f)

        # Extract job ID from filename or data
        job_filename = os.path.basename(file_path)
        job_id = job_filename.replace('.json', '')

        # Normalize structure - handle different formats
        normalized_job = {
            "master_id": None,  # Will be assigned later
            "original_id": job_data.get('id') or job_data.get('uid') or job_id,
            "source_file": job_filename,
            "session_source": session_metadata["session_id"],
            "session_date": session_metadata["session_date"],
            "consolidation_date": datetime.utcnow().isoformat() + "Z",
        }

        # If job has nested 'data' field, flatten it
        if 'data' in job_data and isinstance(job_data['data'], dict):
            normalized_job.update(job_data['data'])
            # Keep metadata separate
            if 'metadata' in job_data:
                normalized_job['extraction_metadata'] = job_data['metadata']
        else:
            # Job data is at root level
            normalized_job.update(job_data)

        # Preserve original structure in case we need it
        normalized_job['_original_structure'] = job_data

        return normalized_job

    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def consolidate_sessions():
    """Main consolidation function"""

    print("=" * 80)
    print("JOB CONSOLIDATION - Phase 2")
    print("=" * 80)
    print()

    all_jobs = []
    session_stats = []

    master_id_counter = 1

    # Process each session
    for session_path in SESSIONS:
        if not os.path.exists(session_path):
            print(f"⚠ Session not found: {session_path}")
            continue

        session_metadata = extract_session_metadata(session_path)
        print(f"Processing: {session_metadata['session_id']}")

        jobs_dir = os.path.join(session_path, "jobs")

        if not os.path.exists(jobs_dir):
            print(f"  No jobs directory found")
            session_stats.append({
                **session_metadata,
                "jobs_contributed": 0,
                "status": "no_jobs_directory"
            })
            continue

        # Load all job files
        job_files = [f for f in os.listdir(jobs_dir) if f.endswith('.json')]
        jobs_loaded = 0

        for job_file in job_files:
            job_path = os.path.join(jobs_dir, job_file)
            job = load_job_from_file(job_path, session_metadata)

            if job:
                # Assign master ID
                job["master_id"] = f"master_{master_id_counter:05d}"
                master_id_counter += 1
                all_jobs.append(job)
                jobs_loaded += 1

        print(f"  ✓ Loaded {jobs_loaded} jobs")

        session_stats.append({
            **session_metadata,
            "jobs_contributed": jobs_loaded,
            "status": "success"
        })
        print()

    # Create master database structure
    master_db = {
        "version": "1.0",
        "consolidation_date": datetime.utcnow().isoformat() + "Z",
        "consolidation_type": "initial",
        "sessions": session_stats,
        "totals": {
            "sessions_consolidated": len([s for s in session_stats if s['status'] == 'success']),
            "total_jobs": len(all_jobs),
            "date_range": {
                "earliest": min([s['session_date'] for s in session_stats if s['session_date']]),
                "latest": max([s['session_date'] for s in session_stats if s['session_date']])
            }
        },
        "jobs": all_jobs
    }

    # Save master database
    master_db_path = os.path.join(OUTPUT_DIR, "jobs_master.json")
    with open(master_db_path, 'w', encoding='utf-8') as f:
        json.dump(master_db, f, indent=2, ensure_ascii=False)

    file_size_mb = os.path.getsize(master_db_path) / (1024 * 1024)

    # Create backup
    backup_timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"jobs_master_{backup_timestamp}.json")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(master_db, f, indent=2, ensure_ascii=False)

    # Create index for fast lookups
    index = {
        "version": "1.0",
        "created": datetime.utcnow().isoformat() + "Z",
        "indices": {
            "by_session": defaultdict(list),
            "by_company": defaultdict(list),
            "by_location": defaultdict(list)
        },
        "lookups": {
            "original_id_to_master": {}
        }
    }

    for job in all_jobs:
        master_id = job["master_id"]

        # Index by session
        index["indices"]["by_session"][job["session_source"]].append(master_id)

        # Index by company
        if "company" in job:
            company_key = job["company"] if isinstance(job["company"], str) else job["company"].get("name", "unknown")
            index["indices"]["by_company"][company_key.lower()].append(master_id)

        # Index by location
        if "location" in job:
            if isinstance(job["location"], str):
                index["indices"]["by_location"][job["location"].lower()].append(master_id)
            elif isinstance(job["location"], dict):
                city = job["location"].get("city", "")
                if city:
                    index["indices"]["by_location"][city.lower()].append(master_id)

        # Lookup mapping
        index["lookups"]["original_id_to_master"][job["original_id"]] = master_id

    # Convert defaultdicts to regular dicts for JSON
    index["indices"]["by_session"] = dict(index["indices"]["by_session"])
    index["indices"]["by_company"] = dict(index["indices"]["by_company"])
    index["indices"]["by_location"] = dict(index["indices"]["by_location"])

    index_path = os.path.join(OUTPUT_DIR, "jobs_index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    # Print summary
    print("=" * 80)
    print("✓ CONSOLIDATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Sessions Processed: {master_db['totals']['sessions_consolidated']}")
    print(f"Jobs Consolidated: {master_db['totals']['total_jobs']}")
    print(f"Master Database: {master_db_path} ({file_size_mb:.2f} MB)")
    print(f"Backup Created: {backup_path}")
    print(f"Index Created: {index_path}")
    print()

    # Return stats for next phase
    return master_db, index

if __name__ == "__main__":
    master_db, index = consolidate_sessions()

    print("Next Steps:")
    print("  1. Run deduplication")
    print("  2. Generate consolidation report")
    print()

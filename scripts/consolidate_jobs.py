#!/usr/bin/env python3
"""
Job Consolidator - Merges all session jobs into master database
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Set
import re

def normalize_string(s) -> str:
    """Normalize string for comparison"""
    if not s:
        return ""
    # Handle dict objects (shouldn't happen but be safe)
    if isinstance(s, dict):
        s = s.get("value", "") or s.get("name", "") or ""
    # Convert to string
    s = str(s).lower().strip()
    # Remove common business suffixes
    s = re.sub(r'\b(gmbh|ag|ltd|inc|llc|corp|corporation)\b', '', s)
    # Remove diversity markers
    s = re.sub(r'\(m/w/d\)|\(w/m/d\)', '', s)
    # Remove extra whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def extract_job_data(job_obj: dict, session_name: str, structure_type: str) -> dict:
    """Extract standardized job data from different formats"""

    if structure_type == "api_response":
        # Session 2: api_response_all.json
        return {
            "id": job_obj.get("id") or job_obj.get("uid"),
            "url": job_obj.get("application_url"),
            "title": job_obj.get("slug"),
            "company": job_obj.get("company", {}).get("name") if isinstance(job_obj.get("company"), dict) else job_obj.get("company"),
            "location": job_obj.get("location", {}).get("city") if isinstance(job_obj.get("location"), dict) else job_obj.get("location"),
            "session": session_name,
            "raw": job_obj
        }

    elif structure_type == "nested_job":
        # Session 3: {job: {...}}
        job = job_obj.get("job", {})
        location = job.get("location", {})
        if isinstance(location, dict):
            location_str = location.get("city") or location.get("raw")
        else:
            location_str = location

        return {
            "id": job.get("id") or job.get("jobId"),
            "url": job.get("url"),
            "title": job.get("title"),
            "company": job.get("company"),
            "location": location_str,
            "session": session_name,
            "raw": job_obj
        }

    elif structure_type == "data_fields":
        # Session 5: {data: {title: {value: ...}}}
        data = job_obj.get("data", {})
        return {
            "id": job_obj.get("job_id"),
            "url": job_obj.get("url"),
            "title": data.get("title", {}).get("value") if isinstance(data.get("title"), dict) else data.get("title"),
            "company": data.get("company", {}).get("value") if isinstance(data.get("company"), dict) else data.get("company"),
            "location": data.get("location", {}).get("value") if isinstance(data.get("location"), dict) else data.get("location"),
            "session": session_name,
            "raw": job_obj
        }

    return {}

def load_session_jobs(session_path: Path) -> tuple[List[dict], str]:
    """Load jobs from a session directory"""
    session_name = session_path.name

    # Check for api_response_all.json
    api_file = session_path / "api_response_all.json"
    if api_file.exists():
        with open(api_file, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
            return [extract_job_data(job, session_name, "api_response") for job in jobs], "api_response"

    # Check for jobs directory
    jobs_dir = session_path / "jobs"
    if jobs_dir.exists() and jobs_dir.is_dir():
        jobs = []
        for job_file in sorted(jobs_dir.glob("*.json")):
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    job_obj = json.load(f)

                    # Determine structure type
                    if "job" in job_obj:
                        structure_type = "nested_job"
                    elif "data" in job_obj:
                        structure_type = "data_fields"
                    else:
                        # Try to extract directly
                        structure_type = "api_response"

                    job_data = extract_job_data(job_obj, session_name, structure_type)
                    if job_data:
                        jobs.append(job_data)
            except Exception as e:
                print(f"Error loading {job_file}: {e}")
        return jobs, "jobs_directory"

    return [], "unknown"

def detect_duplicates(jobs: List[dict]) -> tuple[List[dict], List[dict]]:
    """Detect and separate duplicates"""
    seen_urls: Set[str] = set()
    seen_fuzzy: Set[str] = set()
    unique_jobs = []
    duplicate_jobs = []

    for job in jobs:
        url = job.get("url", "")

        # Check exact URL match
        if url and url in seen_urls:
            duplicate_jobs.append({**job, "duplicate_reason": "exact_url"})
            continue

        # Check fuzzy match (company + title + location)
        company = normalize_string(job.get("company", ""))
        title = normalize_string(job.get("title", ""))
        location = normalize_string(job.get("location", ""))
        fuzzy_key = f"{company}|{title}|{location}"

        if fuzzy_key in seen_fuzzy and fuzzy_key != "||":
            duplicate_jobs.append({**job, "duplicate_reason": "fuzzy_match", "fuzzy_key": fuzzy_key})
            continue

        # This is unique
        unique_jobs.append(job)
        if url:
            seen_urls.add(url)
        if fuzzy_key != "||":
            seen_fuzzy.add(fuzzy_key)

    return unique_jobs, duplicate_jobs

def main():
    output_dir = Path("output")
    database_dir = output_dir / "database"
    database_dir.mkdir(exist_ok=True)

    # Find all session directories
    session_dirs = [d for d in output_dir.iterdir()
                   if d.is_dir() and "session" in d.name and d.name != "database"]

    print(f"Found {len(session_dirs)} sessions")
    print()

    all_jobs = []
    session_stats = []

    # Load jobs from each session
    for session_dir in sorted(session_dirs):
        jobs, structure_type = load_session_jobs(session_dir)
        all_jobs.extend(jobs)

        stats = {
            "session": session_dir.name,
            "jobs_count": len(jobs),
            "structure_type": structure_type
        }
        session_stats.append(stats)
        print(f"✓ {session_dir.name}: {len(jobs)} jobs ({structure_type})")

    print()
    print(f"Total jobs loaded: {len(all_jobs)}")

    # Detect duplicates
    unique_jobs, duplicate_jobs = detect_duplicates(all_jobs)

    duplicate_rate = (len(duplicate_jobs) / len(all_jobs) * 100) if all_jobs else 0

    print(f"Unique jobs: {len(unique_jobs)}")
    print(f"Duplicates: {len(duplicate_jobs)}")
    print(f"Duplicate rate: {duplicate_rate:.1f}%")
    print()

    # Save outputs
    master_file = database_dir / "jobs_master.json"
    duplicates_file = database_dir / "jobs_duplicates.json"
    csv_file = database_dir / "jobs_unique.csv"
    stats_file = database_dir / "consolidation_stats.json"

    # Save master database
    with open(master_file, 'w', encoding='utf-8') as f:
        json.dump(unique_jobs, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {master_file}")

    # Save duplicates
    with open(duplicates_file, 'w', encoding='utf-8') as f:
        json.dump(duplicate_jobs, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {duplicates_file}")

    # Save CSV
    if unique_jobs:
        import csv
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['id', 'url', 'title', 'company', 'location', 'session']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(unique_jobs)
        print(f"✓ Saved: {csv_file}")

    # Save stats
    stats = {
        "sessions": session_stats,
        "total_jobs": len(all_jobs),
        "unique_jobs": len(unique_jobs),
        "duplicates": len(duplicate_jobs),
        "duplicate_rate": round(duplicate_rate, 2)
    }
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Saved: {stats_file}")

if __name__ == "__main__":
    main()

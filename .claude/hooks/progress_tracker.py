#!/usr/bin/env python3
"""
Progress Tracking Hook

Tracks scraping progress and creates checkpoints for resume capability.
Updates statistics after each job is saved.
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path


CHECKPOINT_FILE = "output/checkpoints/checkpoint_latest.json"
CHECKPOINT_DIR = "output/checkpoints"


def load_checkpoint():
    """Load existing checkpoint or create new one."""
    checkpoint_path = Path(CHECKPOINT_FILE)

    if checkpoint_path.exists():
        try:
            with open(checkpoint_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Corrupted checkpoint, create new
            pass

    # Create new checkpoint
    return {
        "session_id": f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "start_time": datetime.now().isoformat(),
        "stats": {
            "urls_discovered": 0,
            "urls_processed": 0,
            "urls_pending": 0,
            "jobs_extracted": 0,
            "jobs_incomplete": 0,
            "jobs_failed": 0,
            "total_processing_time": 0.0
        },
        "quality_metrics": {
            "total_confidence": 0,
            "total_completeness": 0,
            "jobs_graded": 0
        },
        "current_url": None,
        "last_update": datetime.now().isoformat()
    }


def save_checkpoint(checkpoint):
    """Save checkpoint to file."""
    checkpoint_path = Path(CHECKPOINT_FILE)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    # Update timestamp
    checkpoint["last_update"] = datetime.now().isoformat()

    # Write checkpoint
    with open(checkpoint_path, 'w') as f:
        json.dump(checkpoint, f, indent=2)

    # Also save timestamped backup every 50 jobs
    jobs_processed = checkpoint["stats"]["urls_processed"]
    if jobs_processed % 50 == 0 and jobs_processed > 0:
        backup_file = f"{CHECKPOINT_DIR}/checkpoint_{checkpoint['session_id']}_{jobs_processed}.json"
        Path(backup_file).parent.mkdir(parents=True, exist_ok=True)
        with open(backup_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)


def update_with_job_data(checkpoint, job_data):
    """
    Update checkpoint with information from a newly saved job.

    Args:
        checkpoint: Current checkpoint data
        job_data: Parsed job JSON data
    """
    stats = checkpoint["stats"]
    quality = checkpoint["quality_metrics"]

    # Increment processed count
    stats["urls_processed"] += 1

    # Update URL from job metadata if available
    job = job_data.get('job', {})
    if 'url' in job:
        checkpoint["current_url"] = job['url']

    # Get extraction info
    extraction = job.get('extraction', {})
    fields_found = extraction.get('fieldsFound', 0)
    fields_requested = extraction.get('fieldsRequested', 1)

    # Calculate completeness
    if fields_requested > 0:
        completeness = (fields_found / fields_requested) * 100
    else:
        completeness = 0

    # Determine if job is complete (>= 60% completeness)
    if completeness >= 60:
        stats["jobs_extracted"] += 1
    else:
        stats["jobs_incomplete"] += 1

    # Update quality metrics
    avg_confidence = extraction.get('averageConfidence', 0)
    if avg_confidence > 0:
        quality["total_confidence"] += avg_confidence
        quality["total_completeness"] += completeness
        quality["jobs_graded"] += 1

    # Update processing time
    processing_time = job.get('metadata', {}).get('processingTime', 0)
    if processing_time:
        stats["total_processing_time"] += processing_time

    return checkpoint


def format_progress_update(checkpoint):
    """
    Format a human-readable progress update.

    Args:
        checkpoint: Current checkpoint data

    Returns:
        str: Formatted progress message
    """
    stats = checkpoint["stats"]
    quality = checkpoint["quality_metrics"]

    # Calculate averages
    if quality["jobs_graded"] > 0:
        avg_confidence = quality["total_confidence"] / quality["jobs_graded"]
        avg_completeness = quality["total_completeness"] / quality["jobs_graded"]
    else:
        avg_confidence = 0
        avg_completeness = 0

    # Calculate processing speed
    start_time = datetime.fromisoformat(checkpoint["start_time"])
    elapsed_seconds = (datetime.now() - start_time).total_seconds()
    if elapsed_seconds > 0 and stats["urls_processed"] > 0:
        jobs_per_minute = (stats["urls_processed"] / elapsed_seconds) * 60
    else:
        jobs_per_minute = 0

    # Build progress message
    lines = [
        "\n📊 Scraping Progress Update",
        "=" * 70
    ]

    # Main stats
    total_jobs = stats["jobs_extracted"] + stats["jobs_incomplete"]
    lines.append(f"  Jobs: {total_jobs} total | "
                f"{stats['jobs_extracted']} complete | "
                f"{stats['jobs_incomplete']} incomplete")

    # URLs processed
    if stats["urls_discovered"] > 0:
        progress_pct = (stats["urls_processed"] / stats["urls_discovered"]) * 100
        lines.append(f"  Progress: {stats['urls_processed']}/{stats['urls_discovered']} URLs "
                    f"({progress_pct:.0f}%)")
    else:
        lines.append(f"  Processed: {stats['urls_processed']} URLs")

    # Quality metrics
    if quality["jobs_graded"] > 0:
        lines.append(f"  Quality: {avg_completeness:.0f}% complete | "
                    f"{avg_confidence:.0f}% avg confidence")

    # Speed
    if jobs_per_minute > 0:
        lines.append(f"  Speed: {jobs_per_minute:.1f} jobs/min")

        # ETA if we know total
        if stats["urls_discovered"] > stats["urls_processed"]:
            remaining = stats["urls_discovered"] - stats["urls_processed"]
            eta_minutes = remaining / jobs_per_minute
            if eta_minutes < 60:
                lines.append(f"  ETA: ~{eta_minutes:.0f} minutes")
            else:
                lines.append(f"  ETA: ~{eta_minutes/60:.1f} hours")

    lines.append("=" * 70 + "\n")

    return "\n".join(lines)


# Main execution
if __name__ == "__main__":
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
        file_path = input_data.get('tool_input', {}).get('file_path', '')

        # Only track job data files
        if not file_path.startswith('output/jobs/') or not file_path.endswith('.json'):
            # Not a job file, skip tracking
            sys.exit(0)

        # Ignore aggregate file
        if file_path == 'output/jobs.json':
            sys.exit(0)

        # Load checkpoint
        checkpoint = load_checkpoint()

        # Read job data
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                job_data = json.load(f)

            # Update checkpoint
            checkpoint = update_with_job_data(checkpoint, job_data)

            # Save checkpoint
            save_checkpoint(checkpoint)

            # Print progress update every 10 jobs
            jobs_processed = checkpoint["stats"]["urls_processed"]
            if jobs_processed % 10 == 0 or jobs_processed == 1:
                print(format_progress_update(checkpoint))
            else:
                # Brief update
                stats = checkpoint["stats"]
                print(f"✓ Job {jobs_processed} saved | "
                      f"{stats['jobs_extracted']} complete | "
                      f"{stats['jobs_incomplete']} incomplete")

        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"⚠️  Progress tracker JSON error: {e}", file=sys.stderr)
        sys.exit(0)

    except Exception as e:
        print(f"⚠️  Progress tracker error: {e}", file=sys.stderr)
        sys.exit(0)

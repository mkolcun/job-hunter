#!/usr/bin/env python3
"""
Batch Job Extraction Script

Extracts job data from karriere.at URLs in batch with:
- Progress tracking and checkpoints
- Error handling and retries
- Rate limiting (2-5 second delays)
- Quality metrics
"""

import json
import sys
import time
import random
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from bs4 import BeautifulSoup

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))
from html_extractor import HTMLExtractor


class BatchExtractor:
    """Extract multiple jobs in batch."""

    def __init__(self, session_dir: str, start_id: int, end_id: int):
        """
        Initialize batch extractor.

        Args:
            session_dir: Session output directory
            start_id: Starting job ID (inclusive)
            end_id: Ending job ID (inclusive)
        """
        self.session_dir = Path(session_dir)
        self.start_id = start_id
        self.end_id = end_id

        # Load configuration
        self.base_dir = Path(__file__).parent.parent.parent
        self.queue_file = self.base_dir / "output" / "url_queue.json"
        self.schema_file = self.base_dir / "config" / "extraction_schema.json"
        self.checkpoint_file = self.session_dir / "checkpoint.json"

        # Output directories
        self.jobs_dir = self.session_dir / "jobs"
        self.incomplete_dir = self.session_dir / "incomplete"
        self.failed_dir = self.session_dir / "failed"

        # Create directories
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.incomplete_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)

        # Load data
        self.queue = self._load_queue()
        self.schema = self._load_schema()

        # Statistics
        self.stats = {
            "processed": 0,
            "successful": 0,
            "incomplete": 0,
            "failed": 0,
            "start_time": datetime.now().isoformat(),
            "total_confidence": 0,
            "total_completeness": 0
        }

    def _load_queue(self) -> Dict:
        """Load URL queue."""
        with open(self.queue_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_schema(self) -> Dict:
        """Load extraction schema."""
        with open(self.schema_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_checkpoint(self):
        """Save progress checkpoint."""
        checkpoint = {
            "last_processed_id": self.current_id,
            "stats": self.stats,
            "timestamp": datetime.now().isoformat()
        }
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)

    def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML from URL.

        Args:
            url: Job URL to fetch

        Returns:
            HTML content
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        return response.text

    def _extract_job(self, job: Dict) -> Dict:
        """
        Extract single job.

        Args:
            job: Job metadata from queue

        Returns:
            Extraction result
        """
        job_id = job['id']
        url = job['url']

        try:
            # Fetch HTML
            print(f"  Fetching {url}...", flush=True)
            html = self._fetch_html(url)

            # Extract data
            print(f"  Extracting data...", flush=True)
            extractor = HTMLExtractor(html, self.schema)
            result = extractor.extract_all()

            # Add metadata
            result['job']['id'] = str(job_id)
            result['job']['url'] = url
            result['job']['title'] = job.get('title', '')
            result['job']['metadata'] = {
                "scrapedAt": datetime.now().isoformat(),
                "extractionMethod": "html_parser",
                "sourceTitle": job.get('title', ''),
                "sourceCompany": job.get('company', '')
            }

            # Calculate quality grade
            completeness = result['extraction'].get('dataCompleteness', 0)
            confidence = result['extraction'].get('averageConfidence', 0)

            if completeness >= 80 and confidence >= 75:
                grade = "A"
            elif completeness >= 70 and confidence >= 65:
                grade = "B"
            elif completeness >= 50 and confidence >= 55:
                grade = "C"
            else:
                grade = "D"

            result['extraction']['qualityGrade'] = grade

            return {
                "success": True,
                "job_id": job_id,
                "data": result,
                "quality_grade": grade
            }

        except Exception as e:
            return {
                "success": False,
                "job_id": job_id,
                "error": str(e)
            }

    def _save_job(self, result: Dict):
        """Save job result to appropriate directory."""
        job_id = result['job_id']

        if not result['success']:
            # Failed extraction
            output_file = self.failed_dir / f"{job_id}.json"
            data = {
                "id": job_id,
                "error": result['error'],
                "timestamp": datetime.now().isoformat()
            }
            self.stats['failed'] += 1

        else:
            data = result['data']
            grade = result['quality_grade']

            if grade in ['A', 'B']:
                # Complete job
                output_file = self.jobs_dir / f"{job_id}.json"
                self.stats['successful'] += 1
            else:
                # Incomplete job
                output_file = self.incomplete_dir / f"{job_id}.json"
                self.stats['incomplete'] += 1

            # Update stats
            self.stats['total_confidence'] += data['extraction'].get('averageConfidence', 0)
            self.stats['total_completeness'] += data['extraction'].get('dataCompleteness', 0)

        # Save file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def extract_batch(self):
        """Extract jobs in batch."""
        jobs_to_process = [j for j in self.queue['urls']
                          if self.start_id <= j['id'] <= self.end_id]

        total_jobs = len(jobs_to_process)
        print(f"\nBatch Extraction: Jobs {self.start_id}-{self.end_id}")
        print(f"Total jobs to process: {total_jobs}")
        print("=" * 60)

        for idx, job in enumerate(jobs_to_process, 1):
            self.current_id = job['id']
            job_id = job['id']
            title = job.get('title', 'Unknown')

            print(f"\n[{idx}/{total_jobs}] Job #{job_id}: {title}")

            # Extract job
            result = self._extract_job(job)

            # Save result
            self._save_job(result)

            # Update stats
            self.stats['processed'] += 1

            # Print result
            if result['success']:
                grade = result['quality_grade']
                confidence = result['data']['extraction'].get('averageConfidence', 0)
                completeness = result['data']['extraction'].get('dataCompleteness', 0)
                print(f"  ✓ Grade: {grade} | Confidence: {confidence}% | Complete: {completeness}%")
            else:
                print(f"  ✗ Failed: {result['error']}")

            # Save checkpoint every 10 jobs
            if self.stats['processed'] % 10 == 0:
                self._save_checkpoint()
                self._print_progress()

            # Rate limiting (2-5 seconds)
            if idx < total_jobs:  # Don't delay after last job
                delay = random.uniform(2, 5)
                print(f"  Waiting {delay:.1f}s...", flush=True)
                time.sleep(delay)

        # Final checkpoint
        self._save_checkpoint()

        # Print final summary
        self._print_summary()

    def _print_progress(self):
        """Print progress update."""
        print("\n" + "=" * 60)
        print("CHECKPOINT - Progress Update")
        print(f"Processed: {self.stats['processed']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"Incomplete: {self.stats['incomplete']}")
        print(f"Failed: {self.stats['failed']}")

        if self.stats['successful'] + self.stats['incomplete'] > 0:
            avg_conf = self.stats['total_confidence'] / (self.stats['successful'] + self.stats['incomplete'])
            avg_comp = self.stats['total_completeness'] / (self.stats['successful'] + self.stats['incomplete'])
            print(f"Avg Confidence: {avg_conf:.1f}%")
            print(f"Avg Completeness: {avg_comp:.1f}%")

        print("=" * 60 + "\n")

    def _print_summary(self):
        """Print final summary."""
        print("\n" + "=" * 60)
        print("BATCH EXTRACTION COMPLETE")
        print("=" * 60)

        print(f"\nJobs processed: {self.stats['processed']}")
        print(f"  ✓ Successful: {self.stats['successful']}")
        print(f"  ~ Incomplete: {self.stats['incomplete']}")
        print(f"  ✗ Failed: {self.stats['failed']}")

        if self.stats['successful'] + self.stats['incomplete'] > 0:
            avg_conf = self.stats['total_confidence'] / (self.stats['successful'] + self.stats['incomplete'])
            avg_comp = self.stats['total_completeness'] / (self.stats['successful'] + self.stats['incomplete'])
            print(f"\nQuality Metrics:")
            print(f"  Avg Confidence: {avg_conf:.1f}%")
            print(f"  Avg Completeness: {avg_comp:.1f}%")

        # Calculate time elapsed
        start_time = datetime.fromisoformat(self.stats['start_time'])
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\nTime elapsed: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")

        print("\nOutput directories:")
        print(f"  Complete: {self.jobs_dir}")
        print(f"  Incomplete: {self.incomplete_dir}")
        print(f"  Failed: {self.failed_dir}")
        print("=" * 60)


def main():
    """Main entry point."""
    if len(sys.argv) != 4:
        print("Usage: python extract_batch.py <session_dir> <start_id> <end_id>")
        sys.exit(1)

    session_dir = sys.argv[1]
    start_id = int(sys.argv[2])
    end_id = int(sys.argv[3])

    extractor = BatchExtractor(session_dir, start_id, end_id)
    extractor.extract_batch()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
URL Queue Manager

Manages URL queue for scraping with status tracking and deduplication.
"""

import json
import hashlib
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime


class URLQueue:
    """Manage URLs for scraping with status tracking."""

    def __init__(self, queue_file: str = "output/url_queue.json"):
        """
        Initialize URL queue.

        Args:
            queue_file: Path to queue JSON file
        """
        self.queue_file = queue_file
        self.queue_data = {
            "session_id": None,
            "source_url": None,
            "total_urls": 0,
            "urls": [],
            "stats": {
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0
            }
        }
        self.url_hashes = set()  # For deduplication

    def load(self) -> bool:
        """
        Load queue from file.

        Returns:
            True if loaded successfully
        """
        try:
            if Path(self.queue_file).exists():
                with open(self.queue_file, 'r') as f:
                    self.queue_data = json.load(f)

                # Build hash set for deduplication
                for url_item in self.queue_data["urls"]:
                    url_hash = self._hash_url(url_item["url"])
                    self.url_hashes.add(url_hash)

                return True
            return False

        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Error loading queue: {e}")
            return False

    def save(self) -> bool:
        """
        Save queue to file.

        Returns:
            True if saved successfully
        """
        try:
            Path(self.queue_file).parent.mkdir(parents=True, exist_ok=True)

            with open(self.queue_file, 'w') as f:
                json.dump(self.queue_data, f, indent=2)

            return True

        except IOError as e:
            print(f"❌ Error saving queue: {e}")
            return False

    def initialize(self, session_id: str, source_url: str) -> None:
        """
        Initialize new queue.

        Args:
            session_id: Session identifier
            source_url: Source URL being scraped
        """
        self.queue_data = {
            "session_id": session_id,
            "source_url": source_url,
            "total_urls": 0,
            "extraction_date": datetime.now().isoformat(),
            "urls": [],
            "stats": {
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0
            }
        }
        self.url_hashes = set()

    def add_url(self, url: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add URL to queue if not duplicate.

        Args:
            url: URL to add
            metadata: Optional metadata (source_page, priority, etc.)

        Returns:
            True if added, False if duplicate
        """
        url_hash = self._hash_url(url)

        # Check for duplicate
        if url_hash in self.url_hashes:
            return False

        # Add to queue
        url_item = {
            "url": url,
            "status": "pending",
            "discovered_at": datetime.now().isoformat(),
        }

        if metadata:
            url_item.update(metadata)

        self.queue_data["urls"].append(url_item)
        self.url_hashes.add(url_hash)
        self.queue_data["total_urls"] = len(self.queue_data["urls"])
        self.queue_data["stats"]["pending"] += 1

        return True

    def add_urls_batch(self, urls: List[str], metadata: Optional[Dict] = None) -> int:
        """
        Add multiple URLs in batch.

        Args:
            urls: List of URLs to add
            metadata: Optional metadata for all URLs

        Returns:
            Number of URLs added (excluding duplicates)
        """
        added_count = 0

        for url in urls:
            if self.add_url(url, metadata):
                added_count += 1

        return added_count

    def get_next_pending(self) -> Optional[Dict]:
        """
        Get next pending URL.

        Returns:
            URL item dict or None if no pending URLs
        """
        for url_item in self.queue_data["urls"]:
            if url_item["status"] == "pending":
                return url_item

        return None

    def get_all_pending(self) -> List[Dict]:
        """
        Get all pending URLs.

        Returns:
            List of pending URL items
        """
        return [item for item in self.queue_data["urls"] if item["status"] == "pending"]

    def update_status(self, url: str, status: str, metadata: Optional[Dict] = None) -> bool:
        """
        Update URL status.

        Args:
            url: URL to update
            status: New status (pending, processing, completed, failed)
            metadata: Optional metadata to add

        Returns:
            True if updated
        """
        for url_item in self.queue_data["urls"]:
            if url_item["url"] == url:
                # Update stats
                old_status = url_item["status"]
                if old_status in self.queue_data["stats"]:
                    self.queue_data["stats"][old_status] -= 1

                # Set new status
                url_item["status"] = status
                if status in self.queue_data["stats"]:
                    self.queue_data["stats"][status] += 1

                # Add metadata
                if metadata:
                    url_item.update(metadata)

                # Add timestamp
                url_item[f"{status}_at"] = datetime.now().isoformat()

                return True

        return False

    def mark_processing(self, url: str) -> bool:
        """Mark URL as processing."""
        return self.update_status(url, "processing")

    def mark_completed(self, url: str, job_id: Optional[str] = None,
                       processing_time: Optional[float] = None,
                       quality_grade: Optional[str] = None) -> bool:
        """
        Mark URL as completed.

        Args:
            url: URL that was processed
            job_id: Extracted job ID
            processing_time: Time taken in seconds
            quality_grade: Data quality grade

        Returns:
            True if updated
        """
        metadata = {}
        if job_id:
            metadata["job_id"] = job_id
        if processing_time:
            metadata["processing_time"] = processing_time
        if quality_grade:
            metadata["quality_grade"] = quality_grade

        return self.update_status(url, "completed", metadata)

    def mark_failed(self, url: str, error: str) -> bool:
        """
        Mark URL as failed.

        Args:
            url: URL that failed
            error: Error message

        Returns:
            True if updated
        """
        return self.update_status(url, "failed", {"error": error})

    def get_stats(self) -> Dict:
        """Get queue statistics."""
        return self.queue_data["stats"].copy()

    def get_progress(self) -> Dict:
        """
        Get progress information.

        Returns:
            Progress dict with percentages
        """
        total = self.queue_data["total_urls"]
        stats = self.queue_data["stats"]

        if total == 0:
            return {
                "total": 0,
                "processed": 0,
                "percent_complete": 0
            }

        processed = stats["completed"] + stats["failed"]
        percent = (processed / total) * 100

        return {
            "total": total,
            "pending": stats["pending"],
            "processing": stats["processing"],
            "completed": stats["completed"],
            "failed": stats["failed"],
            "processed": processed,
            "percent_complete": round(percent, 1)
        }

    def _hash_url(self, url: str) -> str:
        """
        Generate hash for URL for deduplication.

        Args:
            url: URL to hash

        Returns:
            URL hash
        """
        # Normalize URL (remove trailing slashes, lowercase)
        normalized = url.lower().rstrip('/')
        return hashlib.md5(normalized.encode()).hexdigest()


# JSON I/O Interface for Agent Calls
if __name__ == "__main__":
    import json
    import sys

    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        action = input_data.get("action")

        queue_file = input_data.get("queue_file", "output/url_queue.json")
        queue = URLQueue(queue_file)

        if action == "initialize":
            # Initialize new queue
            session_id = input_data.get("session_id")
            source_url = input_data.get("source_url")
            queue.initialize(session_id, source_url)
            queue.save()

            result = {
                "success": True,
                "session_id": session_id,
                "message": "Queue initialized"
            }

        elif action == "add_urls":
            # Add URLs to queue
            queue.load()
            urls = input_data.get("urls", [])
            metadata = input_data.get("metadata")

            added = queue.add_urls_batch(urls, metadata)
            queue.save()

            result = {
                "success": True,
                "added_count": added,
                "total_urls": queue.queue_data["total_urls"]
            }

        elif action == "get_next":
            # Get next pending URL
            queue.load()
            next_url = queue.get_next_pending()

            result = {
                "success": True,
                "next_url": next_url
            }

        elif action == "update_status":
            # Update URL status
            queue.load()
            url = input_data.get("url")
            status = input_data.get("status")
            metadata = input_data.get("metadata")

            updated = queue.update_status(url, status, metadata)
            queue.save()

            result = {
                "success": updated,
                "message": "Status updated" if updated else "URL not found"
            }

        elif action == "get_progress":
            # Get progress statistics
            queue.load()
            progress = queue.get_progress()

            result = {
                "success": True,
                "progress": progress
            }

        elif action == "load":
            # Just load and return queue data
            queue.load()

            result = {
                "success": True,
                "queue_data": queue.queue_data
            }

        else:
            result = {"success": False, "error": f"Unknown action: {action}"}

        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)

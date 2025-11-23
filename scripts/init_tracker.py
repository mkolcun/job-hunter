#!/usr/bin/env python3
"""
Application Tracker Initialization Script

Creates or updates the application tracking database.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class ApplicationTracker:
    """Manages application tracking database"""

    def __init__(self, tracker_path: str = "output/database/applications_tracker.json"):
        self.tracker_path = Path(tracker_path)
        self.tracker_data = {}

    def initialize_session(
        self,
        session_id: str,
        source_filter: str,
        total_jobs: int
    ) -> Dict[str, Any]:
        """Initialize a new personalization session"""

        self.tracker_data = {
            "personalization_session": session_id,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "source_filter": source_filter,
            "total_jobs": total_jobs,
            "successful": 0,
            "failed": 0,
            "in_progress": 0,
            "applications": []
        }

        self._save()
        return self.tracker_data

    def load(self) -> Optional[Dict[str, Any]]:
        """Load existing tracker"""
        if not self.tracker_path.exists():
            return None

        try:
            with open(self.tracker_path, 'r', encoding='utf-8') as f:
                self.tracker_data = json.load(f)
            return self.tracker_data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading tracker: {e}")
            return None

    def add_application(
        self,
        job_id: str,
        company: str,
        title: str,
        status: str,
        directory: str,
        **kwargs
    ) -> None:
        """Add an application entry to tracker"""

        application = {
            "job_id": job_id,
            "company": company,
            "title": title,
            "status": status,
            "directory": directory,
            "created_at": datetime.now().isoformat(),
            **kwargs
        }

        # Remove any existing entry for this job_id
        self.tracker_data["applications"] = [
            app for app in self.tracker_data.get("applications", [])
            if app.get("job_id") != job_id
        ]

        # Add new entry
        self.tracker_data["applications"].append(application)

        # Update counters
        self._update_counters()
        self._save()

    def update_application_status(
        self,
        job_id: str,
        status: str,
        **kwargs
    ) -> None:
        """Update status of an application"""

        for app in self.tracker_data.get("applications", []):
            if app.get("job_id") == job_id:
                app["status"] = status
                app["updated_at"] = datetime.now().isoformat()
                app.update(kwargs)
                break

        self._update_counters()
        self._save()

    def complete_session(self) -> None:
        """Mark session as completed"""
        self.tracker_data["completed_at"] = datetime.now().isoformat()
        self._update_counters()
        self._save()

    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        return {
            "total_jobs": self.tracker_data.get("total_jobs", 0),
            "successful": self.tracker_data.get("successful", 0),
            "failed": self.tracker_data.get("failed", 0),
            "in_progress": self.tracker_data.get("in_progress", 0),
            "completion_rate": self._calculate_completion_rate()
        }

    def get_failed_jobs(self) -> list:
        """Get list of failed applications"""
        return [
            app for app in self.tracker_data.get("applications", [])
            if app.get("status") == "failed"
        ]

    def _update_counters(self) -> None:
        """Update success/failed/in_progress counters"""
        applications = self.tracker_data.get("applications", [])

        self.tracker_data["successful"] = sum(
            1 for app in applications if app.get("status") == "completed"
        )
        self.tracker_data["failed"] = sum(
            1 for app in applications if app.get("status") == "failed"
        )
        self.tracker_data["in_progress"] = sum(
            1 for app in applications if app.get("status") == "in_progress"
        )

    def _calculate_completion_rate(self) -> float:
        """Calculate completion rate percentage"""
        total = self.tracker_data.get("total_jobs", 0)
        successful = self.tracker_data.get("successful", 0)

        if total == 0:
            return 0.0

        return round((successful / total) * 100, 2)

    def _save(self) -> None:
        """Save tracker to file"""
        self.tracker_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.tracker_path, 'w', encoding='utf-8') as f:
            json.dump(self.tracker_data, f, indent=2, ensure_ascii=False)


def main():
    """CLI entry point"""
    if len(sys.argv) < 4:
        print("Usage: python init_tracker.py <session_id> <source_filter> <total_jobs>")
        print("\nExample:")
        print("  python init_tracker.py personalize_20251122_150000 filter_20251122_143000 47")
        sys.exit(1)

    session_id = sys.argv[1]
    source_filter = sys.argv[2]
    total_jobs = int(sys.argv[3])

    tracker = ApplicationTracker()
    data = tracker.initialize_session(session_id, source_filter, total_jobs)

    print(f"✅ Tracker Initialized")
    print(f"Session: {session_id}")
    print(f"Source Filter: {source_filter}")
    print(f"Total Jobs: {total_jobs}")
    print(f"\nSaved to: {tracker.tracker_path}")


if __name__ == "__main__":
    main()

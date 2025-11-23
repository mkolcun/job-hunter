#!/usr/bin/env python3
"""
Job Filter Script

Filters jobs from master database based on criteria.
Uses deterministic filtering with AI classification for ambiguous cases.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import re


class JobFilter:
    """Filters jobs based on multiple criteria"""

    def __init__(self, master_db_path: str):
        self.master_db_path = Path(master_db_path)
        self.jobs = []
        self.filtered_jobs = []
        self.stats = {
            "total_scanned": 0,
            "total_matched": 0,
            "filter_breakdown": {},
            "ai_classified": 0,
            "processing_time": 0
        }

    def load_database(self) -> bool:
        """Load master database"""
        try:
            with open(self.master_db_path, 'r', encoding='utf-8') as f:
                self.jobs = json.load(f)
            self.stats["total_scanned"] = len(self.jobs)
            return True
        except FileNotFoundError:
            print(f"Error: Master database not found at {self.master_db_path}")
            return False
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {self.master_db_path}")
            return False

    def filter_by_job_type(self, job: Dict, job_types: List[str]) -> bool:
        """Deterministic: Filter by job type"""
        try:
            job_type = job["raw"]["job"].get("jobType", {})
            if isinstance(job_type, dict):
                job_type_value = job_type.get("value", "").strip()
            else:
                job_type_value = str(job_type).strip()

            return job_type_value in job_types
        except (KeyError, TypeError):
            return False

    def filter_by_experience_level(self, job: Dict, levels: List[str]) -> bool:
        """Deterministic: Filter by experience level"""
        try:
            exp_level = job["raw"]["job"].get("experienceLevel", {})
            if isinstance(exp_level, dict):
                exp_value = exp_level.get("value", "").strip()
            else:
                exp_value = str(exp_level).strip()

            # Case-insensitive matching
            return any(level.lower() == exp_value.lower() for level in levels)
        except (KeyError, TypeError):
            return False

    def filter_by_location_type(self, job: Dict, location_types: List[str]) -> bool:
        """Deterministic: Filter by remote/hybrid/onsite"""
        try:
            remote_policy = job["raw"]["job"].get("remotePolicy", {})
            if isinstance(remote_policy, dict):
                policy_value = remote_policy.get("value", "").strip().lower()
            else:
                policy_value = str(remote_policy).strip().lower()

            # If no remotePolicy, check location.type
            if not policy_value:
                location = job["raw"]["job"].get("location", {})
                if isinstance(location, dict):
                    policy_value = location.get("type", "").strip().lower()

            return any(lt.lower() == policy_value for lt in location_types)
        except (KeyError, TypeError):
            return False

    def filter_by_posted_date(self, job: Dict, days: int) -> bool:
        """Deterministic: Filter by posting date"""
        try:
            posted_date = job["raw"]["job"].get("postedDate", {})
            if isinstance(posted_date, dict):
                date_str = posted_date.get("value", "")
            else:
                date_str = str(posted_date)

            if not date_str:
                return True  # Include jobs with missing date

            # Parse date
            job_date = datetime.fromisoformat(date_str.split('T')[0])
            cutoff_date = datetime.now() - timedelta(days=days)

            return job_date >= cutoff_date
        except (KeyError, TypeError, ValueError):
            return True  # Include on parse error

    def filter_by_keywords(self, job: Dict, keywords: List[str]) -> bool:
        """Fuzzy: Filter by job title keywords"""
        try:
            title = job["raw"]["job"].get("title", {})
            if isinstance(title, dict):
                title_value = title.get("value", "").lower()
            else:
                title_value = str(title).lower()

            description = job["raw"]["job"].get("description", {})
            if isinstance(description, dict):
                desc_value = description.get("value", "").lower()
            else:
                desc_value = str(description).lower()

            # Check if any keyword matches
            for keyword in keywords:
                keyword_lower = keyword.lower()
                # Direct substring match in title (high priority)
                if keyword_lower in title_value:
                    return True
                # Word boundary match
                if self._word_match(keyword_lower, title_value):
                    return True
                # Check in description (lower priority)
                if keyword_lower in desc_value:
                    return True

            return False
        except (KeyError, TypeError):
            return False

    def _word_match(self, keyword: str, text: str) -> bool:
        """Check if all words in keyword appear in text"""
        keyword_words = keyword.split()
        return all(word in text for word in keyword_words)

    def filter_by_salary_range(
        self,
        job: Dict,
        min_salary: Optional[float],
        max_salary: Optional[float],
        currency: str
    ) -> bool:
        """Fuzzy: Filter by salary range"""
        try:
            salary = job["raw"]["job"].get("salary", {})
            if not salary or not isinstance(salary, dict):
                return True  # Include jobs with missing salary

            # Check currency match
            job_currency = salary.get("currency", "").upper()
            if job_currency and job_currency != currency.upper():
                # TODO: Implement currency conversion
                return True  # For now, include different currencies

            # Normalize to annual
            job_min = salary.get("min")
            job_max = salary.get("max")
            period = salary.get("period", "annual").lower()

            if job_min:
                job_min = self._normalize_to_annual(job_min, period)
            if job_max:
                job_max = self._normalize_to_annual(job_max, period)

            # Use whichever is available
            if not job_min and not job_max:
                return True  # Include jobs with no salary amount

            job_min = job_min or job_max
            job_max = job_max or job_min

            # Check if ranges overlap
            if min_salary and max_salary:
                return job_max >= min_salary and job_min <= max_salary
            elif min_salary:
                return job_max >= min_salary
            elif max_salary:
                return job_min <= max_salary

            return True
        except (KeyError, TypeError, ValueError):
            return True  # Include on error

    def _normalize_to_annual(self, amount: float, period: str) -> float:
        """Convert salary to annual amount"""
        if period == "monthly":
            return amount * 12
        elif period == "hourly":
            return amount * 2080  # 40 hours/week * 52 weeks
        else:  # annual
            return amount

    def filter_by_cities(self, job: Dict, cities: List[str]) -> bool:
        """Fuzzy: Filter by city names"""
        try:
            location = job["raw"]["job"].get("location", {})
            if not location:
                return False

            if isinstance(location, dict):
                city = location.get("city", "").lower()
                location_value = location.get("value", "").lower()
            else:
                city = ""
                location_value = str(location).lower()

            # Check if any city matches
            for target_city in cities:
                target_lower = target_city.lower()
                if target_lower == city or target_lower in location_value:
                    return True

            return False
        except (KeyError, TypeError):
            return False

    def filter_by_company(self, job: Dict, company_text: str) -> bool:
        """Fuzzy: Filter by company name substring"""
        try:
            company = job["raw"]["job"].get("company", {})
            if isinstance(company, dict):
                company_value = company.get("value", "").lower()
            else:
                company_value = str(company).lower()

            return company_text.lower() in company_value
        except (KeyError, TypeError):
            return False

    def calculate_match_score(
        self,
        job: Dict,
        criteria_met: List[str],
        total_criteria: int
    ) -> int:
        """Calculate match score as percentage"""
        if total_criteria == 0:
            return 100
        return int((len(criteria_met) / total_criteria) * 100)

    def apply_filters(self, criteria: Dict) -> List[Dict]:
        """Apply all filters to jobs"""
        start_time = datetime.now()
        filtered = []

        # Count total criteria
        total_criteria = sum([
            1 if criteria.get("keywords") else 0,
            1 if criteria.get("location_type") else 0,
            1 if criteria.get("salary_min") or criteria.get("salary_max") else 0,
            1 if criteria.get("experience_levels") else 0,
            1 if criteria.get("job_types") else 0,
            1 if criteria.get("cities") else 0,
            1 if criteria.get("company_contains") else 0,
            1 if criteria.get("posted_days") else 0,
        ])

        # Initialize filter breakdown stats
        filter_names = [
            "job_title_keyword", "location_type", "salary_range",
            "experience_level", "job_type", "city_location",
            "company", "posted_date"
        ]
        for name in filter_names:
            self.stats["filter_breakdown"][name] = {
                "passed": 0,
                "failed": 0,
                "missing_data": 0
            }

        for job in self.jobs:
            criteria_met = []
            criteria_failed = []

            # Apply each filter
            # 1. Job Type
            if criteria.get("job_types"):
                if self.filter_by_job_type(job, criteria["job_types"]):
                    criteria_met.append("job_type")
                    self.stats["filter_breakdown"]["job_type"]["passed"] += 1
                else:
                    criteria_failed.append("job_type")
                    self.stats["filter_breakdown"]["job_type"]["failed"] += 1
                    continue  # Fail fast

            # 2. Experience Level
            if criteria.get("experience_levels"):
                if self.filter_by_experience_level(job, criteria["experience_levels"]):
                    criteria_met.append("experience_level")
                    self.stats["filter_breakdown"]["experience_level"]["passed"] += 1
                else:
                    criteria_failed.append("experience_level")
                    self.stats["filter_breakdown"]["experience_level"]["failed"] += 1
                    continue  # Fail fast

            # 3. Location Type
            if criteria.get("location_type"):
                if self.filter_by_location_type(job, criteria["location_type"]):
                    criteria_met.append("location_type")
                    self.stats["filter_breakdown"]["location_type"]["passed"] += 1
                else:
                    criteria_failed.append("location_type")
                    self.stats["filter_breakdown"]["location_type"]["failed"] += 1
                    continue  # Fail fast

            # 4. Posted Date
            if criteria.get("posted_days"):
                if self.filter_by_posted_date(job, criteria["posted_days"]):
                    criteria_met.append("posted_date")
                    self.stats["filter_breakdown"]["posted_date"]["passed"] += 1
                else:
                    criteria_failed.append("posted_date")
                    self.stats["filter_breakdown"]["posted_date"]["failed"] += 1
                    continue  # Fail fast

            # 5. Keywords
            if criteria.get("keywords"):
                if self.filter_by_keywords(job, criteria["keywords"]):
                    criteria_met.append("job_title")
                    self.stats["filter_breakdown"]["job_title_keyword"]["passed"] += 1
                else:
                    criteria_failed.append("job_title")
                    self.stats["filter_breakdown"]["job_title_keyword"]["failed"] += 1
                    continue  # Fail fast

            # 6. Salary Range
            if criteria.get("salary_min") or criteria.get("salary_max"):
                if self.filter_by_salary_range(
                    job,
                    criteria.get("salary_min"),
                    criteria.get("salary_max"),
                    criteria.get("salary_currency", "EUR")
                ):
                    criteria_met.append("salary_range")
                    self.stats["filter_breakdown"]["salary_range"]["passed"] += 1
                else:
                    criteria_failed.append("salary_range")
                    self.stats["filter_breakdown"]["salary_range"]["failed"] += 1
                    continue  # Fail fast

            # 7. Cities
            if criteria.get("cities"):
                if self.filter_by_cities(job, criteria["cities"]):
                    criteria_met.append("city")
                    self.stats["filter_breakdown"]["city_location"]["passed"] += 1
                else:
                    criteria_failed.append("city")
                    self.stats["filter_breakdown"]["city_location"]["failed"] += 1
                    continue  # Fail fast

            # 8. Company
            if criteria.get("company_contains"):
                if self.filter_by_company(job, criteria["company_contains"]):
                    criteria_met.append("company")
                    self.stats["filter_breakdown"]["company"]["passed"] += 1
                else:
                    criteria_failed.append("company")
                    self.stats["filter_breakdown"]["company"]["failed"] += 1
                    continue  # Fail fast

            # All filters passed - add to results
            match_score = self.calculate_match_score(job, criteria_met, total_criteria)

            filtered_job = {
                **job,
                "filter_match": {
                    "matched_at": datetime.now().isoformat(),
                    "criteria_met": criteria_met,
                    "criteria_failed": criteria_failed,
                    "match_score": match_score,
                    "ai_classified": False,
                    "notes": None
                }
            }
            filtered.append(filtered_job)

        # Update stats
        end_time = datetime.now()
        self.stats["total_matched"] = len(filtered)
        self.stats["processing_time"] = (end_time - start_time).total_seconds()

        return filtered

    def save_results(
        self,
        filtered_jobs: List[Dict],
        output_path: str,
        filter_id: str,
        criteria: Dict
    ):
        """Save filtered jobs and statistics"""
        # Save filtered database
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_jobs, f, indent=2, ensure_ascii=False)

        # Save filter report
        report = {
            "filter_id": filter_id,
            "created_at": datetime.now().isoformat(),
            "source_database": str(self.master_db_path),
            "source_job_count": self.stats["total_scanned"],
            "criteria": criteria,
            "results": {
                "total_matches": self.stats["total_matched"],
                "match_rate_percent": round(
                    (self.stats["total_matched"] / self.stats["total_scanned"] * 100)
                    if self.stats["total_scanned"] > 0 else 0,
                    2
                ),
                "ai_classified_count": self.stats["ai_classified"]
            },
            "filter_breakdown": self.stats["filter_breakdown"],
            "processing": {
                "duration_seconds": round(self.stats["processing_time"], 2),
                "jobs_per_second": round(
                    self.stats["total_scanned"] / self.stats["processing_time"]
                    if self.stats["processing_time"] > 0 else 0,
                    1
                )
            }
        }

        # Add top matches to report
        top_matches = sorted(
            filtered_jobs,
            key=lambda x: x["filter_match"]["match_score"],
            reverse=True
        )[:10]

        report["top_matches"] = [
            {
                "job_id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "match_score": job["filter_match"]["match_score"]
            }
            for job in top_matches
        ]

        # Save report
        report_path = output_file.parent.parent / "reports" / f"filter_results_{filter_id}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return str(output_file), str(report_path)


def main():
    """Main entry point for CLI usage"""
    if len(sys.argv) < 2:
        print("Usage: python filter_jobs.py <criteria_file>")
        print("Criteria file should be JSON with filter parameters")
        sys.exit(1)

    criteria_file = Path(sys.argv[1])
    if not criteria_file.exists():
        print(f"Error: Criteria file not found: {criteria_file}")
        sys.exit(1)

    # Load criteria
    with open(criteria_file, 'r', encoding='utf-8') as f:
        criteria = json.load(f)

    # Initialize filter
    master_db = Path("output/database/jobs_master.json")
    filter_engine = JobFilter(str(master_db))

    # Load database
    if not filter_engine.load_database():
        sys.exit(1)

    print(f"Loaded {filter_engine.stats['total_scanned']} jobs from master database")

    # Apply filters
    print("Applying filters...")
    filtered_jobs = filter_engine.apply_filters(criteria)

    # Save results
    filter_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"output/database/jobs_filtered.json"

    db_path, report_path = filter_engine.save_results(
        filtered_jobs,
        output_path,
        f"filter_{filter_id}",
        criteria
    )

    # Print summary
    print("\n✅ Filtering Complete")
    print("=" * 50)
    print(f"Scanned: {filter_engine.stats['total_scanned']} jobs")
    print(f"Matched: {filter_engine.stats['total_matched']} jobs")
    print(f"Match Rate: {filter_engine.stats['total_matched'] / filter_engine.stats['total_scanned'] * 100:.2f}%")
    print(f"\nProcessing Time: {filter_engine.stats['processing_time']:.2f}s")
    print(f"\nOutput Files:")
    print(f"  ✓ {db_path}")
    print(f"  ✓ {report_path}")


if __name__ == "__main__":
    main()

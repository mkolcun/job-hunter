#!/usr/bin/env python3
"""
Report Generator

Generates quality analysis reports from scraping session data.
"""

import json
from typing import Dict, List
from pathlib import Path
from datetime import datetime


class ReportGenerator:
    """Generate markdown quality reports."""

    def __init__(self, session_dir: str):
        """
        Initialize report generator.

        Args:
            session_dir: Path to session directory
        """
        self.session_dir = Path(session_dir)
        self.jobs_data = []
        self.stats = {}

    def load_session_data(self) -> bool:
        """
        Load all job data from session.

        Returns:
            True if loaded successfully
        """
        try:
            jobs_dir = self.session_dir / "jobs"

            if not jobs_dir.exists():
                print(f"❌ Jobs directory not found: {jobs_dir}")
                return False

            # Load all job JSON files
            for job_file in jobs_dir.glob("*.json"):
                if job_file.name == "jobs.json":  # Skip aggregate file
                    continue

                with open(job_file, 'r') as f:
                    job_data = json.load(f)
                    self.jobs_data.append(job_data)

            return len(self.jobs_data) > 0

        except Exception as e:
            print(f"❌ Error loading session data: {e}")
            return False

    def calculate_statistics(self) -> Dict:
        """
        Calculate comprehensive statistics.

        Returns:
            Statistics dictionary
        """
        if not self.jobs_data:
            return {}

        stats = {
            "total_jobs": len(self.jobs_data),
            "field_coverage": {},
            "field_confidence": {},
            "quality_distribution": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
            "extraction_sources": {"structured": 0, "labeled": 0, "pattern": 0, "section": 0, "inferred": 0},
            "avg_completeness": 0,
            "avg_confidence": 0,
        }

        total_completeness = 0
        total_confidence = 0

        # Analyze each job
        for job_data in self.jobs_data:
            job = job_data.get("job", {})
            extraction = job.get("extraction", {})

            # Completeness
            completeness = extraction.get("dataCompleteness", 0)
            total_completeness += completeness

            # Confidence
            avg_conf = extraction.get("averageConfidence", 0)
            total_confidence += avg_conf

            # Quality grade
            grade = self._calculate_grade(completeness, avg_conf)
            stats["quality_distribution"][grade] += 1

            # Field analysis
            for field_name, field_value in job.items():
                if field_name in ["extraction", "metadata"]:
                    continue

                # Initialize field stats
                if field_name not in stats["field_coverage"]:
                    stats["field_coverage"][field_name] = {"found": 0, "total": 0}
                    stats["field_confidence"][field_name] = []

                stats["field_coverage"][field_name]["total"] += 1

                # Check if field found
                if isinstance(field_value, dict):
                    if field_value.get("found", True):
                        stats["field_coverage"][field_name]["found"] += 1

                        # Confidence
                        conf = field_value.get("confidence", 0)
                        if conf > 0:
                            stats["field_confidence"][field_name].append(conf)

                        # Source
                        source = field_value.get("source", "unknown")
                        if source in stats["extraction_sources"]:
                            stats["extraction_sources"][source] += 1

                elif field_value is not None:
                    stats["field_coverage"][field_name]["found"] += 1

        # Calculate averages
        stats["avg_completeness"] = int(total_completeness / len(self.jobs_data))
        stats["avg_confidence"] = int(total_confidence / len(self.jobs_data))

        # Field-level averages
        for field_name, confidences in stats["field_confidence"].items():
            if confidences:
                stats["field_confidence"][field_name] = int(sum(confidences) / len(confidences))
            else:
                stats["field_confidence"][field_name] = 0

        self.stats = stats
        return stats

    def generate_markdown_report(self, output_path: str) -> bool:
        """
        Generate full markdown report.

        Args:
            output_path: Path to save report

        Returns:
            True if generated successfully
        """
        if not self.stats:
            self.calculate_statistics()

        try:
            report_lines = []

            # Header
            report_lines.append("# Scraping Session Quality Report")
            report_lines.append("")
            report_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"**Session**: {self.session_dir.name}")
            report_lines.append("")

            # Executive Summary
            report_lines.append("## Executive Summary")
            report_lines.append("")
            report_lines.append(f"- **Total Jobs**: {self.stats['total_jobs']}")
            report_lines.append(f"- **Average Completeness**: {self.stats['avg_completeness']}%")
            report_lines.append(f"- **Average Confidence**: {self.stats['avg_confidence']}%")
            grade = self._calculate_grade(self.stats['avg_completeness'], self.stats['avg_confidence'])
            report_lines.append(f"- **Overall Grade**: {grade}")
            report_lines.append("")

            # Field Coverage Table
            report_lines.append("## Field Coverage")
            report_lines.append("")
            report_lines.append("| Field | Found | Coverage | Avg Confidence | Quality |")
            report_lines.append("|-------|-------|----------|----------------|---------|")

            for field_name, coverage_data in sorted(self.stats['field_coverage'].items()):
                found = coverage_data['found']
                total = coverage_data['total']
                coverage_pct = int((found / total) * 100) if total > 0 else 0

                avg_conf = self.stats['field_confidence'].get(field_name, 0)
                field_grade = self._calculate_grade(coverage_pct, avg_conf)

                report_lines.append(f"| {field_name} | {found}/{total} | {coverage_pct}% | {avg_conf}% | {field_grade} |")

            report_lines.append("")

            # Quality Distribution
            report_lines.append("## Quality Distribution")
            report_lines.append("")
            dist = self.stats['quality_distribution']
            for grade in ["A", "B", "C", "D", "F"]:
                count = dist[grade]
                pct = int((count / self.stats['total_jobs']) * 100) if self.stats['total_jobs'] > 0 else 0
                bar = "█" * (pct // 5)  # Visual bar
                report_lines.append(f"- **{grade} Grade**: {count} jobs ({pct}%) {bar}")

            report_lines.append("")

            # Extraction Sources
            report_lines.append("## Extraction Sources")
            report_lines.append("")
            sources = self.stats['extraction_sources']
            total_sources = sum(sources.values())

            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                if total_sources > 0:
                    pct = int((count / total_sources) * 100)
                    report_lines.append(f"- **{source.capitalize()}**: {count} ({pct}%)")

            report_lines.append("")

            # Recommendations
            report_lines.append("## Recommendations")
            report_lines.append("")
            recommendations = self._generate_recommendations()
            for i, rec in enumerate(recommendations, 1):
                report_lines.append(f"### {i}. {rec['title']}")
                report_lines.append("")
                report_lines.append(f"**Issue**: {rec['issue']}")
                report_lines.append(f"**Impact**: {rec['impact']}")
                report_lines.append(f"**Solution**: {rec['solution']}")
                report_lines.append(f"**Expected Improvement**: {rec['improvement']}")
                report_lines.append("")

            # Write report
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write("\n".join(report_lines))

            return True

        except Exception as e:
            print(f"❌ Error generating report: {e}")
            return False

    def _calculate_grade(self, completeness: float, confidence: float) -> str:
        """Calculate quality grade from completeness and confidence."""
        score = (completeness * 0.6) + (confidence * 0.4)

        if score >= 90:
            return "A"
        elif score >= 75:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"

    def _generate_recommendations(self) -> List[Dict]:
        """Generate actionable recommendations based on statistics."""
        recommendations = []

        # Find fields with low coverage
        for field_name, coverage_data in self.stats['field_coverage'].items():
            found = coverage_data['found']
            total = coverage_data['total']
            coverage_pct = (found / total) * 100 if total > 0 else 0

            if coverage_pct < 70:
                missing_pct = 100 - coverage_pct
                recommendations.append({
                    "title": f"Improve {field_name} extraction",
                    "issue": f"{field_name} missing in {missing_pct:.0f}% of jobs",
                    "impact": "Reduces data completeness and usefulness",
                    "solution": f"Add more patterns and aliases for {field_name} extraction",
                    "improvement": f"Expected +15-20% coverage"
                })

        # Find fields with low confidence
        for field_name, avg_conf in self.stats['field_confidence'].items():
            if 0 < avg_conf < 70:
                recommendations.append({
                    "title": f"Increase {field_name} confidence",
                    "issue": f"{field_name} has low confidence ({avg_conf}% avg)",
                    "impact": "Data quality concerns, may need manual verification",
                    "solution": f"Add structured data extraction for {field_name}, improve pattern matching",
                    "improvement": f"Expected +10-15% confidence"
                })

        # Limit to top 5 recommendations
        return recommendations[:5]


# JSON I/O Interface for Agent Calls
if __name__ == "__main__":
    import json
    import sys

    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        action = input_data.get("action", "generate")

        session_dir = input_data.get("session_dir")

        if not session_dir:
            result = {
                "success": False,
                "error": "Missing required field: 'session_dir'"
            }
            print(json.dumps(result))
            sys.exit(1)

        generator = ReportGenerator(session_dir)

        if action == "generate":
            # Generate full report
            if generator.load_session_data():
                stats = generator.calculate_statistics()

                output_path = input_data.get("output_path", "output/reports/quality_report.md")

                if generator.generate_markdown_report(output_path):
                    result = {
                        "success": True,
                        "report_path": output_path,
                        "stats": {
                            "total_jobs": stats["total_jobs"],
                            "avg_completeness": stats["avg_completeness"],
                            "avg_confidence": stats["avg_confidence"]
                        }
                    }
                else:
                    result = {
                        "success": False,
                        "error": "Failed to generate report"
                    }
            else:
                result = {
                    "success": False,
                    "error": "No jobs found in session"
                }

        elif action == "get_stats":
            # Just get statistics without generating report
            if generator.load_session_data():
                stats = generator.calculate_statistics()

                result = {
                    "success": True,
                    "stats": stats
                }
            else:
                result = {
                    "success": False,
                    "error": "No jobs found in session"
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

#!/usr/bin/env python3
"""
Post-Extraction Validation Hook

Validates extracted job data quality and completeness after Write operations.
Checks required fields, confidence scores, and data completeness.
"""
import json
import sys
import os
from pathlib import Path


def validate_job_data(data):
    """
    Validate job data against required fields and confidence thresholds.

    Args:
        data: Parsed JSON data from job file

    Returns:
        List of validation issues found (empty if valid)
    """
    issues = []

    if 'job' not in data:
        return ["No job data found in file"]

    job = data['job']

    # Check required fields (title, company, location minimum)
    required_fields = ['title', 'company', 'location']
    for field in required_fields:
        if field not in job or not job[field]:
            issues.append(f"❌ Missing required field: {field}")

    # Check confidence scores for fields that have them
    low_confidence_fields = []
    for field, value in job.items():
        if isinstance(value, dict) and 'confidence' in value:
            if value['confidence'] < 50:
                low_confidence_fields.append(f"{field} ({value['confidence']}%)")

    if low_confidence_fields:
        issues.append(f"⚠️  Low confidence fields: {', '.join(low_confidence_fields)}")

    # Check data completeness
    extraction = job.get('extraction', {})
    fields_found = extraction.get('fieldsFound', 0)
    fields_requested = extraction.get('fieldsRequested', 1)

    if fields_requested > 0:
        completeness = (fields_found / fields_requested) * 100

        if completeness < 60:
            issues.append(f"⚠️  Low data completeness: {completeness:.0f}% ({fields_found}/{fields_requested} fields)")

    # Check average confidence
    avg_confidence = extraction.get('averageConfidence', 0)
    if avg_confidence > 0 and avg_confidence < 60:
        issues.append(f"⚠️  Low average confidence: {avg_confidence}%")

    # Check for missing contact information (warning, not error)
    has_contact = any(field in job for field in ['contactEmail', 'contactPhone', 'contactPerson'])
    if not has_contact:
        issues.append("ℹ️  No contact information found (email, phone, or person)")

    return issues


def get_quality_grade(data):
    """
    Calculate quality grade based on completeness and confidence.

    Returns:
        str: Grade (A+, A, B+, B, C+, C, D, F)
    """
    job = data.get('job', {})
    extraction = job.get('extraction', {})

    completeness = extraction.get('dataCompleteness', 0)
    avg_confidence = extraction.get('averageConfidence', 0)

    # Calculate weighted score
    score = (completeness * 0.6) + (avg_confidence * 0.4)

    if score >= 90:
        return "A+"
    elif score >= 85:
        return "A"
    elif score >= 80:
        return "B+"
    elif score >= 75:
        return "B"
    elif score >= 70:
        return "C+"
    elif score >= 60:
        return "C"
    elif score >= 50:
        return "D"
    else:
        return "F"


# Main execution
if __name__ == "__main__":
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
        file_path = input_data.get('tool_input', {}).get('file_path', '')

        # Only validate job JSON files in the output directory
        if not file_path.startswith('output/jobs/') or not file_path.endswith('.json'):
            # Not a job file, skip validation
            sys.exit(0)

        # Check if file exists and read it
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                job_data = json.load(f)

            # Validate the data
            issues = validate_job_data(job_data)

            # Get quality grade
            grade = get_quality_grade(job_data)

            # Print validation results
            if issues:
                print(f"\n📋 Data Validation Results for {Path(file_path).name}")
                print("=" * 60)
                for issue in issues:
                    print(f"  {issue}")
                print(f"\n  Quality Grade: {grade}")
                print(f"  File: {file_path}\n")

                # If critical issues, suggest review
                critical_issues = [i for i in issues if i.startswith("❌")]
                if critical_issues:
                    print("  ⚡ Action: Manual review recommended\n")
            else:
                print(f"✅ Data validation passed - Grade: {grade} - {Path(file_path).name}")

        else:
            print(f"⚠️  File not found: {file_path}", file=sys.stderr)

        # Always exit 0 (don't block the operation)
        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block on parse errors

    except Exception as e:
        print(f"❌ Error validating data: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block on errors

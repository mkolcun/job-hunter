#!/usr/bin/env python3
"""
HTML Parser and Data Extractor

Implements extraction logic for job data from HTML using multiple strategies:
- Structured data (Schema.org, JSON-LD)
- Semantic analysis (labeled fields)
- Pattern matching (regex)
- Content sectioning
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import html


class HTMLExtractor:
    """Extract structured job data from HTML."""

    def __init__(self, html_content: str, schema: Dict[str, Any]):
        """
        Initialize HTML extractor.

        Args:
            html_content: HTML content to parse
            schema: Extraction schema defining fields to extract
        """
        self.html = html_content
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.schema = schema
        self.extracted_data = {}

    def extract_all(self) -> Dict[str, Any]:
        """
        Extract all fields defined in schema.

        Returns:
            Dictionary of extracted job data
        """
        result = {
            "job": {},
            "extraction": {
                "fieldsRequested": 0,
                "fieldsFound": 0,
                "averageConfidence": 0,
                "structuredDataAvailable": False
            }
        }

        # Try structured data first
        structured_data = self._extract_structured_data()
        if structured_data:
            result["extraction"]["structuredDataAvailable"] = True
            result["job"].update(structured_data)

        # Count all fields across priorities
        all_fields = {}
        for priority in ["required", "high_priority", "medium_priority", "optional", "custom_fields"]:
            if priority in self.schema.get("extraction_schema", {}):
                all_fields.update(self.schema["extraction_schema"][priority])

        result["extraction"]["fieldsRequested"] = len(all_fields)

        # Extract each field
        total_confidence = 0
        for field_name, field_config in all_fields.items():
            if field_name not in result["job"]:
                extracted = self._extract_field(field_name, field_config)
                if extracted and extracted.get("found"):
                    result["job"][field_name] = extracted
                    result["extraction"]["fieldsFound"] += 1
                    total_confidence += extracted.get("confidence", 0)

        # Calculate average confidence
        if result["extraction"]["fieldsFound"] > 0:
            result["extraction"]["averageConfidence"] = int(
                total_confidence / result["extraction"]["fieldsFound"]
            )

        # Calculate completeness
        if result["extraction"]["fieldsRequested"] > 0:
            result["extraction"]["dataCompleteness"] = int(
                (result["extraction"]["fieldsFound"] / result["extraction"]["fieldsRequested"]) * 100
            )

        return result

    def _extract_structured_data(self) -> Dict[str, Any]:
        """
        Extract data from Schema.org JSON-LD or microdata.

        Returns:
            Extracted structured data
        """
        result = {}

        # Try JSON-LD
        for script in self.soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)

                # Handle JobPosting schema
                if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                    result.update(self._parse_job_posting_schema(data))

                # Handle list of schemas
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'JobPosting':
                            result.update(self._parse_job_posting_schema(item))

            except (json.JSONDecodeError, AttributeError):
                continue

        return result

    def _parse_job_posting_schema(self, data: Dict) -> Dict[str, Any]:
        """Parse Schema.org JobPosting data."""
        result = {}

        # Title
        if 'title' in data:
            result['title'] = {
                "value": data['title'],
                "confidence": 100,
                "source": "structured",
                "found": True
            }

        # Company
        if 'hiringOrganization' in data:
            org = data['hiringOrganization']
            if isinstance(org, dict) and 'name' in org:
                result['company'] = {
                    "value": org['name'],
                    "confidence": 100,
                    "source": "structured",
                    "found": True
                }

        # Location
        if 'jobLocation' in data:
            loc = data['jobLocation']
            if isinstance(loc, dict):
                address = loc.get('address', {})
                if isinstance(address, dict):
                    city = address.get('addressLocality', '')
                    country = address.get('addressCountry', '')
                    location_str = f"{city}, {country}".strip(', ')
                    if location_str:
                        result['location'] = {
                            "value": location_str,
                            "confidence": 100,
                            "source": "structured",
                            "found": True
                        }

        # Salary
        if 'baseSalary' in data:
            salary_data = data['baseSalary']
            if isinstance(salary_data, dict):
                value = salary_data.get('value', {})
                if isinstance(value, dict):
                    result['salary'] = {
                        "min": value.get('minValue'),
                        "max": value.get('maxValue'),
                        "currency": value.get('currency', 'USD'),
                        "period": salary_data.get('unitText', 'YEAR').lower(),
                        "confidence": 100,
                        "source": "structured",
                        "found": True
                    }

        # Description
        if 'description' in data:
            result['description'] = {
                "value": data['description'],
                "confidence": 100,
                "source": "structured",
                "found": True
            }

        # Posted date
        if 'datePosted' in data:
            result['postedDate'] = {
                "value": data['datePosted'],
                "confidence": 100,
                "source": "structured",
                "found": True
            }

        # Employment type
        if 'employmentType' in data:
            result['jobType'] = {
                "value": data['employmentType'],
                "confidence": 100,
                "source": "structured",
                "found": True
            }

        return result

    def _extract_field(self, field_name: str, field_config: Dict) -> Optional[Dict]:
        """
        Extract a single field using multiple strategies.

        Args:
            field_name: Name of field to extract
            field_config: Field configuration from schema

        Returns:
            Extracted field data with confidence score
        """
        field_type = field_config.get('type', 'string')
        aliases = field_config.get('aliases', [field_name])
        min_confidence = field_config.get('min_confidence', 0)

        # Try different extraction methods in order of reliability
        strategies = [
            self._extract_from_labeled_field,
            self._extract_by_pattern,
            self._extract_from_section,
        ]

        for strategy in strategies:
            result = strategy(field_name, field_type, aliases, field_config)
            if result and result.get("found") and result.get("confidence", 0) >= min_confidence:
                return result

        # No extraction succeeded
        return {
            "found": False,
            "value": None,
            "confidence": 0,
            "source": "none"
        }

    def _extract_from_labeled_field(self, field_name: str, field_type: str,
                                     aliases: List[str], config: Dict) -> Optional[Dict]:
        """Extract field from labeled HTML elements."""
        # Search for labels matching aliases
        for alias in aliases:
            # Check various label patterns
            patterns = [
                (By.TAG_NAME, "label", alias),
                (By.CLASS_NAME, "label", alias),
                (By.TAG_NAME, "dt", alias),  # Definition term
                (By.TAG_NAME, "strong", alias),
                (By.TAG_NAME, "b", alias),
            ]

            for by, tag, text in patterns:
                elements = self.soup.find_all(tag)
                for elem in elements:
                    if alias.lower() in elem.get_text().lower():
                        # Found label, get next sibling or parent content
                        value = self._extract_value_near_element(elem, field_type)
                        if value:
                            return {
                                "value": value,
                                "confidence": 85,
                                "source": "labeled",
                                "found": True
                            }

        return None

    def _extract_by_pattern(self, field_name: str, field_type: str,
                            aliases: List[str], config: Dict) -> Optional[Dict]:
        """Extract field using regex patterns."""
        text = self.soup.get_text()

        # Field-specific pattern extraction
        if field_name == "salary" or field_type == "object" and "salary" in field_name.lower():
            return self._extract_salary(text)

        elif field_name in ["contactEmail", "email"] or field_type == "email":
            return self._extract_email(text)

        elif field_name in ["contactPhone", "phone"] or field_type == "phone":
            return self._extract_phone(text)

        elif field_type == "date":
            return self._extract_date(text)

        elif field_type == "string":
            # Generic string extraction
            for alias in aliases:
                pattern = rf"{alias}\s*[:\-]?\s*([^\n\r]+)"
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if len(value) > 3:  # Minimum length
                        return {
                            "value": value,
                            "confidence": 65,
                            "source": "pattern",
                            "found": True
                        }

        return None

    def _extract_salary(self, text: str) -> Optional[Dict]:
        """Extract salary with currency and range."""
        # Various salary patterns
        patterns = [
            # €60,000 - €80,000
            r'€\s?(\d{1,3}(?:[.,]\d{3})*)\s?-\s?€\s?(\d{1,3}(?:[.,]\d{3})*)',
            # $60,000 - $80,000
            r'\$\s?(\d{1,3}(?:,\d{3})*)\s?-\s?\$\s?(\d{1,3}(?:,\d{3})*)',
            # 60k-80k EUR
            r'(\d{1,3})k?\s?-\s?(\d{1,3})k?\s?(EUR|USD|GBP|CHF)',
            # €60.000 - €80.000 (European format)
            r'€\s?(\d{1,3}(?:\.\d{3})*)\s?-\s?€\s?(\d{1,3}(?:\.\d{3})*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()

                # Parse amounts
                min_amount = self._parse_number(groups[0])
                max_amount = self._parse_number(groups[1])

                # Detect currency
                currency = "EUR"
                if '$' in match.group(0):
                    currency = "USD"
                elif '£' in match.group(0):
                    currency = "GBP"
                elif len(groups) > 2:
                    currency = groups[2].upper()

                # Handle 'k' notation
                if 'k' in match.group(0).lower():
                    min_amount *= 1000
                    max_amount *= 1000

                return {
                    "min": int(min_amount),
                    "max": int(max_amount),
                    "currency": currency,
                    "period": "annual",
                    "displayText": match.group(0).strip(),
                    "confidence": 75,
                    "source": "pattern",
                    "found": True
                }

        return None

    def _extract_email(self, text: str) -> Optional[Dict]:
        """Extract email with priority filtering."""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(pattern, text)

        if not emails:
            return None

        # Priority filtering
        priorities = {
            "high": ["jobs@", "careers@", "recruiting@", "hr@", "hiring@"],
            "medium": ["@"],  # Any company email
            "low": ["info@", "contact@", "noreply@"]
        }

        # Filter by priority
        for priority, keywords in priorities.items():
            for email in emails:
                email_lower = email.lower()
                if any(kw in email_lower for kw in keywords):
                    if "noreply" not in email_lower:  # Exclude noreply
                        confidence = 90 if priority == "high" else 75 if priority == "medium" else 60
                        return {
                            "value": email,
                            "priority": priority,
                            "confidence": confidence,
                            "source": "pattern",
                            "found": True
                        }

        # Return first email if no priority match
        return {
            "value": emails[0],
            "priority": "unknown",
            "confidence": 55,
            "source": "pattern",
            "found": True
        }

    def _extract_phone(self, text: str) -> Optional[Dict]:
        """Extract phone number."""
        patterns = [
            r'\+\d{1,3}\s?\(?\d{1,4}\)?\s?\d{1,4}\s?\d{1,4}\s?\d{1,9}',  # International
            r'\(\d{3}\)\s?\d{3}-\d{4}',  # US format
            r'\d{2,4}\s?\d{2,4}\s?\d{2,4}\s?\d{2,4}',  # European
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0).strip()
                # Validate length (7-15 digits)
                digits = re.sub(r'\D', '', phone)
                if 7 <= len(digits) <= 15:
                    return {
                        "value": phone,
                        "confidence": 70,
                        "source": "pattern",
                        "found": True
                    }

        return None

    def _extract_date(self, text: str) -> Optional[Dict]:
        """Extract and normalize date."""
        # Relative dates
        relative_patterns = [
            (r'(\d+)\s+days?\s+ago', 'days'),
            (r'(\d+)\s+weeks?\s+ago', 'weeks'),
            (r'(\d+)\s+months?\s+ago', 'months'),
            (r'yesterday', 'yesterday'),
        ]

        for pattern, unit in relative_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if unit == 'yesterday':
                    date = datetime.now() - timedelta(days=1)
                else:
                    amount = int(match.group(1))
                    if unit == 'days':
                        date = datetime.now() - timedelta(days=amount)
                    elif unit == 'weeks':
                        date = datetime.now() - timedelta(weeks=amount)
                    elif unit == 'months':
                        date = datetime.now() - timedelta(days=amount * 30)

                return {
                    "value": date.strftime('%Y-%m-%d'),
                    "relative": match.group(0),
                    "confidence": 80,
                    "source": "pattern",
                    "found": True
                }

        # Absolute dates
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # ISO format
            r'\d{1,2}/\d{1,2}/\d{4}',  # US format
            r'\d{1,2}\.\d{1,2}\.\d{4}',  # European format
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return {
                    "value": match.group(0),
                    "confidence": 75,
                    "source": "pattern",
                    "found": True
                }

        return None

    def _extract_from_section(self, field_name: str, field_type: str,
                               aliases: List[str], config: Dict) -> Optional[Dict]:
        """Extract field from content sections."""
        # Section headers mapping
        section_mapping = {
            "description": ["about the role", "job description", "position overview", "what you'll do"],
            "requirements": ["requirements", "qualifications", "what we're looking for", "you have"],
            "responsibilities": ["responsibilities", "your tasks", "day-to-day", "duties"],
            "benefits": ["benefits", "what we offer", "perks", "why join us"],
            "companyDescription": ["about us", "about the company", "who we are", "our story"],
        }

        if field_name not in section_mapping:
            return None

        headers = section_mapping[field_name]

        # Find section
        for header in headers:
            # Look for headings containing this text
            for heading_tag in ['h1', 'h2', 'h3', 'h4', 'strong']:
                headings = self.soup.find_all(heading_tag)
                for heading in headings:
                    if header in heading.get_text().lower():
                        # Extract content after this heading
                        content = self._extract_content_after_heading(heading, field_type)
                        if content:
                            return {
                                "value": content,
                                "confidence": 65,
                                "source": "section",
                                "found": True
                            }

        return None

    def _extract_content_after_heading(self, heading_elem, field_type: str) -> Optional[Any]:
        """Extract content following a heading element."""
        if field_type == "array":
            # Extract list items
            items = []
            next_elem = heading_elem.find_next_sibling()

            while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4']:
                if next_elem.name in ['ul', 'ol']:
                    for li in next_elem.find_all('li'):
                        text = li.get_text().strip()
                        if text:
                            items.append(text)

                next_elem = next_elem.find_next_sibling()

            return items if items else None

        else:
            # Extract text paragraphs
            text_parts = []
            next_elem = heading_elem.find_next_sibling()

            while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4']:
                if next_elem.name == 'p':
                    text = next_elem.get_text().strip()
                    if text:
                        text_parts.append(text)

                next_elem = next_elem.find_next_sibling()

            return ' '.join(text_parts) if text_parts else None

    def _extract_value_near_element(self, element, field_type: str) -> Optional[Any]:
        """Extract value near a labeled element."""
        # Try next sibling
        next_elem = element.find_next_sibling()
        if next_elem:
            value = next_elem.get_text().strip()
            if value and len(value) > 2:
                return value

        # Try parent's next sibling
        parent = element.parent
        if parent:
            next_elem = parent.find_next_sibling()
            if next_elem:
                value = next_elem.get_text().strip()
                if value and len(value) > 2:
                    return value

        return None

    @staticmethod
    def _parse_number(num_str: str) -> float:
        """Parse number from string with various formats."""
        # Remove non-digit characters except decimal point
        cleaned = re.sub(r'[^\d.]', '', num_str)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0


# JSON I/O Interface for Agent Calls
if __name__ == "__main__":
    import json
    import sys

    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        html_content = input_data.get("html")
        schema = input_data.get("schema")

        if not html_content or not schema:
            result = {
                "success": False,
                "error": "Missing required fields: 'html' and 'schema'"
            }
            print(json.dumps(result))
            sys.exit(1)

        # Extract data
        extractor = HTMLExtractor(html_content, schema)
        extraction_result = extractor.extract_all()

        # Return success with extracted data
        result = {
            "success": True,
            "data": extraction_result
        }

        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        # Output error as JSON
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)

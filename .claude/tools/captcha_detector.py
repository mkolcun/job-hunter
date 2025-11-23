#!/usr/bin/env python3
"""
CAPTCHA Detector

Detects various types of CAPTCHAs and anti-bot measures in web pages.
"""

import re
from typing import Tuple, Optional, Dict
from bs4 import BeautifulSoup


class CaptchaDetector:
    """Detect CAPTCHAs and anti-bot measures."""

    def __init__(self, html_content: str, url: str = ""):
        """
        Initialize CAPTCHA detector.

        Args:
            html_content: HTML content to analyze
            url: Current page URL
        """
        self.html = html_content.lower()
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.url = url

    def detect(self) -> Tuple[bool, Optional[str], Dict]:
        """
        Detect if page has CAPTCHA or anti-bot measures.

        Returns:
            Tuple of (has_captcha, captcha_type, details)
        """
        # Check each type
        detectors = [
            self._detect_recaptcha(),
            self._detect_hcaptcha(),
            self._detect_cloudflare(),
            self._detect_custom_captcha(),
            self._detect_rate_limiting(),
        ]

        for has_captcha, captcha_type, details in detectors:
            if has_captcha:
                return True, captcha_type, details

        return False, None, {}

    def _detect_recaptcha(self) -> Tuple[bool, Optional[str], Dict]:
        """Detect Google reCAPTCHA."""
        indicators = [
            'recaptcha' in self.html,
            'g-recaptcha' in self.html,
            'google.com/recaptcha' in self.html,
            bool(self.soup.find('div', class_=re.compile(r'.*recaptcha.*', re.I))),
            bool(self.soup.find('iframe', src=re.compile(r'.*recaptcha.*', re.I))),
        ]

        if any(indicators):
            # Determine version
            if 'recaptcha/api.js' in self.html:
                version = "v2"
            elif 'recaptcha/api2' in self.html:
                version = "v2"
            elif 'grecaptcha.execute' in self.html:
                version = "v3"
            else:
                version = "unknown"

            return True, "recaptcha", {
                "version": version,
                "indicators": sum(indicators),
                "description": f"Google reCAPTCHA {version} detected"
            }

        return False, None, {}

    def _detect_hcaptcha(self) -> Tuple[bool, Optional[str], Dict]:
        """Detect hCaptcha."""
        indicators = [
            'hcaptcha' in self.html,
            'h-captcha' in self.html,
            'hcaptcha.com' in self.html,
            bool(self.soup.find('div', class_=re.compile(r'.*h-captcha.*', re.I))),
            bool(self.soup.find('iframe', src=re.compile(r'.*hcaptcha.*', re.I))),
        ]

        if any(indicators):
            return True, "hcaptcha", {
                "indicators": sum(indicators),
                "description": "hCaptcha detected"
            }

        return False, None, {}

    def _detect_cloudflare(self) -> Tuple[bool, Optional[str], Dict]:
        """Detect Cloudflare challenge page."""
        indicators = [
            'checking your browser' in self.html,
            'cloudflare' in self.html and 'challenge' in self.html,
            'cf-ray' in self.html,
            'cf_clearance' in self.html,
            bool(self.soup.find('div', id='cf-wrapper')),
        ]

        if any(indicators):
            return True, "cloudflare", {
                "indicators": sum(indicators),
                "description": "Cloudflare challenge/protection detected"
            }

        return False, None, {}

    def _detect_custom_captcha(self) -> Tuple[bool, Optional[str], Dict]:
        """Detect custom CAPTCHA implementations."""
        keywords = [
            'verify you are human',
            'prove you are not a robot',
            'security check',
            'are you a robot',
            'human verification',
            'please verify',
            'captcha',
        ]

        found_keywords = []
        for keyword in keywords:
            if keyword in self.html:
                found_keywords.append(keyword)

        if found_keywords:
            # Check if likely a CAPTCHA page
            if len(found_keywords) >= 2 or 'captcha' in found_keywords:
                return True, "custom", {
                    "keywords": found_keywords,
                    "description": "Custom CAPTCHA/verification detected"
                }

        return False, None, {}

    def _detect_rate_limiting(self) -> Tuple[bool, Optional[str], Dict]:
        """Detect rate limiting or blocking."""
        keywords = [
            'too many requests',
            'rate limit',
            'slow down',
            'try again later',
            'temporarily blocked',
            'access denied',
            '429',
            '403 forbidden',
        ]

        found_keywords = []
        for keyword in keywords:
            if keyword in self.html:
                found_keywords.append(keyword)

        if found_keywords:
            return True, "rate_limit", {
                "keywords": found_keywords,
                "description": "Rate limiting or blocking detected"
            }

        return False, None, {}

    def get_handling_recommendation(self, captcha_type: str) -> str:
        """
        Get recommended handling strategy for CAPTCHA type.

        Args:
            captcha_type: Type of CAPTCHA detected

        Returns:
            Recommended handling strategy
        """
        recommendations = {
            "recaptcha": "Human-in-the-loop solving recommended. Can use 2captcha service if configured.",
            "hcaptcha": "Human-in-the-loop solving recommended. Can use Anti-Captcha service if configured.",
            "cloudflare": "Wait 5 seconds for challenge to complete. If persists, implement backoff or rotate session.",
            "custom": "Human-in-the-loop solving required. Pause and request manual intervention.",
            "rate_limit": "Implement exponential backoff (5s, 15s, 30s, 60s). Consider rotating IP/session.",
        }

        return recommendations.get(captcha_type, "Unknown CAPTCHA type. Manual intervention required.")


# JSON I/O Interface for Agent Calls
if __name__ == "__main__":
    import json
    import sys

    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        html_content = input_data.get("html", "")
        url = input_data.get("url", "")

        # Detect CAPTCHA
        detector = CaptchaDetector(html_content, url)
        has_captcha, captcha_type, details = detector.detect()

        result = {
            "success": True,
            "has_captcha": has_captcha,
            "captcha_type": captcha_type,
            "details": details
        }

        # Add handling recommendation if CAPTCHA detected
        if has_captcha:
            result["recommendation"] = detector.get_handling_recommendation(captcha_type)

        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result))
        sys.exit(1)

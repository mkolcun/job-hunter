#!/usr/bin/env python3
"""
Browser Controller Tool

Controls Selenium WebDriver with anti-detection measures for scraping.
"""

import time
import random
from typing import Optional, Tuple, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium_stealth import stealth


class BrowserController:
    """Manages browser automation with anti-detection."""

    def __init__(self, headless: bool = False, user_data_dir: Optional[str] = None):
        """
        Initialize browser controller.

        Args:
            headless: Run browser in headless mode
            user_data_dir: Path to Chrome user data directory for session persistence
        """
        self.driver = None
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.current_user_agent = None

        # User agent rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

    def start(self) -> None:
        """Start browser with anti-detection measures."""
        if self.driver:
            return  # Already started

        # Select random user agent
        self.current_user_agent = random.choice(self.user_agents)

        # Configure Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={self.current_user_agent}")

        if self.headless:
            options.add_argument("--headless=new")

        if self.user_data_dir:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")

        # Anti-detection measures
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Start browser
        self.driver = webdriver.Chrome(options=options)

        # Apply selenium-stealth
        stealth(
            self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

    def stop(self) -> None:
        """Stop browser and clean up."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def navigate(self, url: str, timeout: int = 30) -> bool:
        """
        Navigate to URL with human-like behavior.

        Args:
            url: Target URL
            timeout: Page load timeout in seconds

        Returns:
            True if successful
        """
        if not self.driver:
            self.start()

        try:
            self.driver.get(url)

            # Wait for page to load
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Human-like delay
            self._human_delay(1, 3)

            return True

        except TimeoutException:
            print(f"❌ Timeout loading {url}")
            return False
        except WebDriverException as e:
            print(f"❌ Error loading {url}: {e}")
            return False

    def get_html(self) -> str:
        """
        Get current page HTML.

        Returns:
            Page source HTML
        """
        if not self.driver:
            return ""

        return self.driver.page_source

    def scroll_page(self, strategy: str = "natural") -> None:
        """
        Scroll page with human-like behavior.

        Args:
            strategy: Scrolling strategy
                - "natural": Scroll in steps with random delays
                - "full": Scroll to bottom immediately
                - "random": Random scroll positions
        """
        if not self.driver:
            return

        if strategy == "natural":
            # Natural scrolling in steps
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")

            current_position = 0
            while current_position < total_height:
                # Scroll by viewport with some variance
                scroll_amount = random.randint(
                    int(viewport_height * 0.5), int(viewport_height * 0.9)
                )
                current_position += scroll_amount

                self.driver.execute_script(f"window.scrollTo(0, {current_position});")

                # Random delay between scrolls
                time.sleep(random.uniform(0.3, 0.8))

        elif strategy == "full":
            # Scroll to bottom immediately
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(1)

        elif strategy == "random":
            # Random scroll positions
            for _ in range(random.randint(3, 6)):
                position = random.randint(0, 10000)
                self.driver.execute_script(f"window.scrollTo(0, {position});")
                time.sleep(random.uniform(0.3, 0.7))

    def click_element(self, selector: str, by: str = "css") -> bool:
        """
        Click element with human-like behavior.

        Args:
            selector: Element selector
            by: Selector type ("css", "xpath", "id", "class")

        Returns:
            True if clicked successfully
        """
        if not self.driver:
            return False

        try:
            # Convert selector type
            by_mapping = {
                "css": By.CSS_SELECTOR,
                "xpath": By.XPATH,
                "id": By.ID,
                "class": By.CLASS_NAME,
            }

            # Wait for element to be clickable
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((by_mapping.get(by, By.CSS_SELECTOR), selector))
            )

            # Human-like delay before click
            self._human_delay(0.5, 1.5)

            # Click
            element.click()

            # Human-like delay after click
            self._human_delay(1, 2)

            return True

        except Exception as e:
            print(f"❌ Error clicking element {selector}: {e}")
            return False

    def check_for_captcha(self) -> Tuple[bool, Optional[str]]:
        """
        Check if current page contains CAPTCHA.

        Returns:
            Tuple of (has_captcha, captcha_type)
        """
        if not self.driver:
            return False, None

        html = self.get_html().lower()

        # Check for common CAPTCHA types
        if "recaptcha" in html or "g-recaptcha" in html:
            return True, "recaptcha"

        if "hcaptcha" in html or "h-captcha" in html:
            return True, "hcaptcha"

        if "cloudflare" in html and "challenge" in html:
            return True, "cloudflare"

        # Check for common CAPTCHA iframes
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if "recaptcha" in src or "hcaptcha" in src or "captcha" in src:
                    captcha_type = "recaptcha" if "recaptcha" in src else "hcaptcha"
                    return True, captcha_type
        except:
            pass

        return False, None

    def get_cookies(self) -> List[dict]:
        """
        Get current browser cookies.

        Returns:
            List of cookie dictionaries
        """
        if not self.driver:
            return []

        return self.driver.get_cookies()

    def set_cookies(self, cookies: List[dict]) -> None:
        """
        Set browser cookies.

        Args:
            cookies: List of cookie dictionaries
        """
        if not self.driver:
            return

        for cookie in cookies:
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                print(f"⚠️  Could not set cookie: {e}")

    def _human_delay(self, min_seconds: float = 2, max_seconds: float = 5) -> None:
        """
        Add human-like random delay.

        Args:
            min_seconds: Minimum delay
            max_seconds: Maximum delay
        """
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# JSON I/O Interface for Agent Calls
if __name__ == "__main__":
    import json
    import sys

    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        action = input_data.get("action")

        result = {"success": False, "error": None}

        # Initialize browser
        headless = input_data.get("headless", False)
        browser = BrowserController(headless=headless)

        if action == "navigate":
            # Navigate to URL and return HTML
            url = input_data.get("url")
            browser.start()

            if browser.navigate(url):
                html = browser.get_html()
                has_captcha, captcha_type = browser.check_for_captcha()

                result = {
                    "success": True,
                    "html": html,
                    "url": url,
                    "has_captcha": has_captcha,
                    "captcha_type": captcha_type
                }
            else:
                result = {"success": False, "error": "Failed to navigate to URL"}

            browser.stop()

        elif action == "scroll_and_get":
            # Navigate, scroll, and return HTML
            url = input_data.get("url")
            scroll_strategy = input_data.get("scroll_strategy", "natural")

            browser.start()

            if browser.navigate(url):
                browser.scroll_page(scroll_strategy)
                html = browser.get_html()

                result = {
                    "success": True,
                    "html": html,
                    "url": url
                }
            else:
                result = {"success": False, "error": "Failed to navigate to URL"}

            browser.stop()

        elif action == "check_captcha":
            # Just check for CAPTCHA on provided HTML
            html = input_data.get("html", "")
            # For CAPTCHA check, we can work with raw HTML without browser
            has_captcha = "recaptcha" in html.lower() or "hcaptcha" in html.lower()
            captcha_type = None
            if "recaptcha" in html.lower():
                captcha_type = "recaptcha"
            elif "hcaptcha" in html.lower():
                captcha_type = "hcaptcha"

            result = {
                "success": True,
                "has_captcha": has_captcha,
                "captcha_type": captcha_type
            }

        else:
            result = {"success": False, "error": f"Unknown action: {action}"}

        # Output JSON result to stdout
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

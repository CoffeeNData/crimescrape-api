import re
from logging import Logger

import requests
from playwright.sync_api import sync_playwright as pw

from lib.basesearch import BaseSearch

"""
This file contains the necessary utils to do the scraping using different methods.

There are two main classes here:
- StealthSearch: Uses Playwright with Firefox to perform stealthy web scraping that can bypass basic anti-bot measures.
- RequestSearch: Uses the Requests library for straightforward HTTP requests. Should use this unless strictly necessary to use StealthSearch.

In case a complex website is to be scraped with a webdriver, StealthSearch manages all the necessary
resources and avoid leaks by using context managers. The manual use of the drivers through basesearch.py is discouraged.
"""


class StealthSearch(BaseSearch):
    def __init__(self, logger: Logger | None = None, headless: bool = True) -> None:
        """Initializes the Webdriver-based search object."""
        super().__init__(logger)
        self.headless = headless
        self.driver = None
        self.browser = None
        self.playwright = None

    def __enter__(self):
        """Context manager entry point for resource management."""
        self._start_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point for resource cleanup."""
        self._close_driver()
        return False  # Don't suppress exceptions

    def _start_driver(self) -> None:  # type: ignore
        try:
            playwright = pw().start()
            browser = playwright.firefox.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()
            self.driver, self.browser, self.playwright = page, browser, playwright
        except Exception as e:
            # Ensure cleanup in case of failure
            self._close_driver()
            raise e

    def _close_driver(self) -> None:  # type: ignore
        """
        Closes the browser and Playwright instance if they are open.
        """
        if self.browser:
            try:
                self.browser.close()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error closing browser: {e}")
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error stopping Playwright: {e}")
        self.driver = None
        self.browser = None
        self.playwright = None

    @staticmethod
    def _check_for_captcha(content: str) -> bool:
        """Detect common CAPTCHA patterns in the response.

        Args:
            content (str): The response content to check for CAPTCHA indicators.

        Returns:
            bool: True if CAPTCHA is detected, False otherwise.
        """
        captcha_patterns = [
            r'recaptcha',
            r'hcaptcha',
            r'cloudflare.*challenge',
            r'you.*robot',
            r'challenge.*page',
        ]
        content_lower = content.lower()
        return any(re.search(pattern, content_lower) for pattern in captcha_patterns)

    def post_url(
            self, url: str, data: dict | None = None, headers: dict | None = None
    ) -> str | None:
        """
        Send a POST request to the URL with optional POST data
        and return the response.

        Args:
            url: str: The URL to send the POST request to.
            data: dict | None: The data to include in the POST request.
            headers: dict | None: Optional HTTP headers to include in the request.

        Returns: The response content as a string, or None if an error occurs.
        """
        try:
            self._start_driver()
            if self.driver:
                if headers:
                    self.driver.set_extra_http_headers(headers)
                self.driver.request.post(url, data=data if data else None)
                content = self.driver.content()
                return content
            else:
                raise self.InvalidResponseError
        except self.InvalidResponseError as e:
            if self.logger:
                self.logger.error(
                    f"Error trying to fetch URL {url} with data {data}: {e}"
                )
            return ""

    def fetch_url(
            self,
            url: str,
            scroll: bool = False,
            wait_seconds: int | None = None,
            headers: dict | None = None,
    ) -> str | None:
        """
        Fetch the content of the specified URL using the webdriver.

        :param url: The URL to fetch through GET request.
        :param scroll: If True, scrolls the page to load dynamic content.
        :param wait_seconds: The number of seconds to wait after page loads.
        :param headers: Optional HTTP headers to include in the request.
        :return: The HTML content of the page as a string, or None if an error occurs.
        """
        self._start_driver()
        if not self.driver:
            self._close_driver()
            return None

        if headers: self.driver.set_extra_http_headers(headers)

        try:
            self.driver.goto(url)
            if wait_seconds: self.driver.wait_for_timeout(wait_seconds * 1000)

            if scroll:  # Scroll to the bottom and back to the top to load dynamic content
                for _ in range(5):
                    self.driver.evaluate(
                        "window.scrollTo(0, document.body.scrollHeight);"
                    )
                    self.driver.wait_for_timeout(150)
                    self.driver.evaluate("window.scrollTo(0, 0);")
                    self.driver.wait_for_timeout(150)

            src = self.driver.content()
            if self._check_for_captcha(src):
                raise self.CaptchaError
            return src
        except self.CaptchaError:
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error: {e}")
        finally:
            self._close_driver()
        return None


class RequestSearch(BaseSearch):
    def __init__(self, logger: Logger | None = None) -> None:
        """Initializes the Requests-based search object."""
        super().__init__(logger)

    @staticmethod
    def _check_for_captcha(content: str) -> bool:
        """Detect common CAPTCHA patterns in the response.

        Args:
            content (str): The response content to check for CAPTCHA indicators.

        Returns:
            bool: True if CAPTCHA is detected, False otherwise.
        """
        captcha_patterns = [
            r'recaptcha',
            r'hcaptcha',
            r'cloudflare.*challenge',
            r'you.*robot',
            r'challenge.*page',
        ]
        content_lower = content.lower()
        return any(re.search(pattern, content_lower) for pattern in captcha_patterns)

    def fetch_url(self, url: str, headers: dict | None = None) -> str:
        """Fetch the content of the specified URL using requests."""
        try:
            r = requests.get(url=url, headers=headers if headers else None)
            html = r.text
            if self._check_for_captcha(html):
                raise self.CaptchaError
            return html
        except self.CaptchaError:
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error fetching URL {url} with requests: {e}")
            return ""

    def post_url(
            self, url: str, data: dict | None = None, headers: dict | None = None
    ) -> str:
        """Send a POST request to the URL with optional POST data
        and return the response"""
        try:
            r = requests.post(
                url=url,
                data=data if data else None,
                headers=headers if headers else None,
            )
            return r.text
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error while POSTing {url} with data {data}: {e}")
            return ""

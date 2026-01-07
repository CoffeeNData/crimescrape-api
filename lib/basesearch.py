import json
import warnings
from logging import Logger

from bs4 import BeautifulSoup as bs
from rapidfuzz import fuzz

# TODO: Review code and delegate exceptions to callers where applicable.

"""
This file is where the magic happens, so it needs to be clean and manage errors properly.

Exceptions should be raised here. The best practice would be to not create defensive code
unless a specific exception is expected. All other exceptions should be raised to here and
managed properly.

To achieve this, we need to:
- Avoid the code from crashing
- Log errors when they happen
- Never raise errors to crimescrape.py, but empty/None results instead.
"""


class BaseSearch:
    RISK_LEVELS = ["Low", "Medium", "High", "Dangerous"]

    def __init__(self, logger: Logger | None = None) -> None:
        self.fuzzy_match_threshold = 85
        self.logger = logger

    class InvalidResponseError(Exception):
        """Thrown when the returned value is not a valid response"""
        pass

    class CaptchaError(Exception):
        """Thrown when the module has detected a CAPTCHA blocking the codeflow"""
        pass

    @staticmethod
    def gen_response(risk: str, source: str, notice_id: str, charges: list[str] | str = "Unknown") -> dict:
        """Generate the results for a submodule the correct way.

        Args:
            risk (str): The risk for the results.
            source (str): The submodule that this is being generated for.
            notice_id (str): The notice ID for the results.
            charges (list[str]): A list with the found charges/crimes for the suspect.

        Raises:
            ValueError: Returned if the risk is incorrect.

        Returns:
            dict: Returns a dictionary with the built results.
        """
        if isinstance(charges, str):
            charges = [charges]

        if risk not in BaseSearch.RISK_LEVELS:
            raise ValueError(
                f"The supplied risk is invalid: {risk}.\nPlease use one of these: {', '.join(BaseSearch.RISK_LEVELS)}."
            )

        result = {"risk": risk, "notices": {source: {"id": notice_id, "charges": charges}}}
        return result

    def validate_response(self, data: dict) -> dict:  # NOSONAR
        """
        WARNING: Deprecated. This function is only kept for backwards compatibility.
        Check if the data is in a valid format.
        If it is, return the supplied data.
        If It's not, raise an error.
        """
        warnings.warn(
            "validate_response is deprecated, use gen_response for validation instead",
            DeprecationWarning,
            stacklevel=2
        )

        # Check if top-level keys 'risk' and 'notices' exist
        if not isinstance(data, dict):
            raise self.InvalidResponseError

        if "risk" not in data or "notices" not in data:
            raise self.InvalidResponseError

        # Check if 'risk' is a string and has a valid value
        if not isinstance(data["risk"], str) or data["risk"] not in self.RISK_LEVELS:
            raise self.InvalidResponseError

        # Check if 'notices' is a dictionary
        if not isinstance(data["notices"], dict):
            raise self.InvalidResponseError

        # Validate the structure inside 'notices'
        for source, details in data["notices"].items():
            if not isinstance(details, dict):
                raise self.InvalidResponseError

            # Check if 'id' is a string
            if "id" not in details or not isinstance(details["id"], str):
                raise self.InvalidResponseError

            # Check if 'charges' is a list of strings
            if "charges" not in details or not isinstance(details["charges"], list):
                raise self.InvalidResponseError

            for charge in details["charges"]:
                if not isinstance(charge, str):
                    raise self.InvalidResponseError

        return data

    @staticmethod
    def is_name_match(
            local_name: str, remote_name: str, threshold: int = 85
    ) -> bool:
        """Check if the fuzzy match between two names meets the threshold."""
        score = fuzz.ratio(local_name.lower(), remote_name.lower())
        return score >= threshold

    @staticmethod
    def parse_html(html: str) -> bs:
        """Parse the HTML content and return a BeautifulSoup object."""
        return bs(html, "html.parser")

    def parse_json(self, html: str) -> dict:
        """Parse JSON from HTML content."""
        try:
            soup = self.parse_html(html)
            pre_element = soup.find("pre")
            if pre_element is None:
                raise ValueError("No <pre> element found in HTML")
            res = pre_element.get_text()
            return json.loads(res)
        except json.JSONDecodeError as e:
            if self.logger:
                self.logger.error(f"Failed to parse JSON: {e}")
            return {}
        except (ValueError, AttributeError) as e:
            if self.logger:
                self.logger.error(f"Invalid HTML structure: {e}")
            return {}

    @staticmethod
    def extract_text(
            soup: bs, tag: str, attributes: dict = None, default: str = ""
    ) -> str:
        """Helper method to extract text from a BeautifulSoup element."""
        element = soup.find(tag, attributes)
        return element.get_text(strip=True) if element else default

    @staticmethod
    def merge_responses(responses: list[dict]) -> dict:  # NOSONAR (S3776) "Deprecated function"
        """
        Merges a list of dictionaries into one unique dictionary,
        ensuring the highest risk level is retained.

        Args:
            responses (list[dict]): List of dictionaries to merge.

        Returns:
            dict: A merged dictionary.
        """

        def _preserve_order_dedup(items: list) -> list:
            """Remove duplicates while preserving insertion order."""
            seen = set()
            result = []
            for item in items:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result

        def merge_recursive(d1, d2):
            """Recursively merges two dictionaries."""
            for key, value in d2.items():
                if key in d1:
                    if isinstance(d1[key], dict) and isinstance(value, dict):
                        # Merge nested dictionaries
                        merge_recursive(d1[key], value)
                    elif isinstance(d1[key], list) and isinstance(value, list):
                        # Combine lists, ensuring no duplicates while preserving order
                        d1[key] = _preserve_order_dedup(d1[key] + value)
                    elif key == "risk":
                        # Update risk based on priority
                        d1[key] = max(
                            d1[key], value, key=lambda r: BaseSearch.RISK_LEVELS.index(r)
                        )
                    else:
                        # Overwrite value if types are different
                        d1[key] = value
                else:
                    # Add new key-value pair
                    d1[key] = value
            return d1

        # Start with an empty dictionary
        merged_dict = {}
        for d in responses:
            merged_dict = merge_recursive(merged_dict, d)

        return merged_dict

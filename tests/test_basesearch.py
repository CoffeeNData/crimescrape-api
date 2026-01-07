import json
import logging
import warnings
from contextlib import contextmanager
from unittest.mock import Mock

import pytest
from bs4 import BeautifulSoup as bs

from lib.basesearch import BaseSearch


# Fixtures for common test setup
@pytest.fixture
def logger_mock():
    """Provides a mock logger for testing"""
    return Mock(spec=logging.Logger)


@pytest.fixture
def search_with_logger(logger_mock):
    """Provides a BaseSearch instance with a mock logger"""
    return BaseSearch(logger=logger_mock)


@pytest.fixture
def search_without_logger():
    """Provides a BaseSearch instance without a logger"""
    return BaseSearch()


@contextmanager
def ignore_deprecation_warnings():
    """Context manager to ignore DeprecationWarning for deprecated method testing"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        yield


class TestBaseSearchInit:
    """Test BaseSearch initialization"""

    def test_init_with_logger(self, logger_mock):
        """Test initialization with a logger"""
        search = BaseSearch(logger=logger_mock)
        assert search.logger is logger_mock
        assert search.fuzzy_match_threshold == 85

    def test_init_without_logger(self):
        """Test initialization without a logger"""
        search = BaseSearch()
        assert search.logger is None
        assert search.fuzzy_match_threshold == 85

    def test_init_with_none_logger(self):
        """Test initialization with None as logger"""
        search = BaseSearch(logger=None)
        assert search.logger is None


class TestBaseSearchRiskLevels:
    """Test RISK_LEVELS constant"""

    def test_risk_levels_exist(self):
        """Test that RISK_LEVELS are defined"""
        assert BaseSearch.RISK_LEVELS == ["Low", "Medium", "High", "Dangerous"]

    def test_risk_levels_are_strings(self):
        """Test that all risk levels are strings"""
        assert all(isinstance(level, str) for level in BaseSearch.RISK_LEVELS)


class TestGenResponse:
    """Test gen_response static method"""

    def test_gen_response_low_risk(self):
        """Test generating a response with Low risk"""
        result = BaseSearch.gen_response("Low", "FBI", "12345", ["Fraud"])
        assert result["risk"] == "Low"
        assert "FBI" in result["notices"]
        assert result["notices"]["FBI"]["id"] == "12345"
        assert result["notices"]["FBI"]["charges"] == ["Fraud"]

    def test_gen_response_high_risk(self):
        """Test generating a response with High risk"""
        result = BaseSearch.gen_response("High", "Interpol", "ABC123", ["Murder", "Theft"])
        assert result["risk"] == "High"
        assert result["notices"]["Interpol"]["id"] == "ABC123"
        assert result["notices"]["Interpol"]["charges"] == ["Murder", "Theft"]

    def test_gen_response_dangerous_risk(self):
        """Test generating a response with Dangerous risk"""
        result = BaseSearch.gen_response("Dangerous", "OFAC", "XYZ789", ["Terrorism"])
        assert result["risk"] == "Dangerous"
        assert "OFAC" in result["notices"]

    def test_gen_response_medium_risk(self):
        """Test generating a response with Medium risk"""
        result = BaseSearch.gen_response("Medium", "NCA", "MED456", ["Drug Trafficking"])
        assert result["risk"] == "Medium"

    def test_gen_response_invalid_risk(self):
        """Test that invalid risk raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            BaseSearch.gen_response("Critical", "FBI", "12345", ["Fraud"])
        assert "invalid" in str(exc_info.value).lower()

    def test_gen_response_empty_charges(self):
        """Test generating a response with empty charges list"""
        result = BaseSearch.gen_response("Low", "FBI", "12345", [])
        assert result["notices"]["FBI"]["charges"] == []

    def test_gen_response_multiple_charges(self):
        """Test generating a response with multiple charges"""
        charges = ["Murder", "Assault", "Theft", "Fraud"]
        result = BaseSearch.gen_response("High", "FBI", "ID123", charges)
        assert result["notices"]["FBI"]["charges"] == charges


# noinspection PyDeprecation
class TestValidateResponse:
    """Test validate_response method

    Tests the validation logic for response objects, ensuring they conform
    to the expected structure with proper risk levels and notice formatting.
    """

    def test_validate_valid_response(self):
        """Test validating a valid response"""
        search = BaseSearch()
        valid_response = {
            "risk": "High",
            "notices": {
                "FBI": {
                    "id": "12345",
                    "charges": ["Fraud", "Money Laundering"]
                }
            }
        }
        with ignore_deprecation_warnings():
            result = search.validate_response(valid_response)
        assert result == valid_response

    def test_validate_response_not_dict(self):
        """Test that non-dict response raises InvalidResponseError"""
        search = BaseSearch()
        with pytest.raises(BaseSearch.InvalidResponseError):
            with ignore_deprecation_warnings():
                search.validate_response("not a dict")  # type: ignore

    def test_validate_response_missing_risk(self):
        """Test that missing 'risk' key raises InvalidResponseError"""
        search = BaseSearch()
        invalid_response = {
            "notices": {
                "FBI": {"id": "12345", "charges": []}
            }
        }
        with pytest.raises(BaseSearch.InvalidResponseError):
            with ignore_deprecation_warnings():
                search.validate_response(invalid_response)

    def test_validate_response_missing_notices(self):
        """Test that missing 'notices' key raises InvalidResponseError"""
        search = BaseSearch()
        invalid_response = {"risk": "High"}
        with pytest.raises(BaseSearch.InvalidResponseError):
            with ignore_deprecation_warnings():
                search.validate_response(invalid_response)

    def test_validate_response_invalid_risk_value(self):
        """Test that invalid risk value raises InvalidResponseError"""
        search = BaseSearch()
        invalid_response = {
            "risk": "InvalidRisk",
            "notices": {}
        }
        with pytest.raises(BaseSearch.InvalidResponseError):
            with ignore_deprecation_warnings():
                search.validate_response(invalid_response)

    def test_validate_response_notices_not_dict(self):
        """Test that non-dict notices raises InvalidResponseError"""
        search = BaseSearch()
        invalid_response = {
            "risk": "High",
            "notices": "not a dict"
        }
        with pytest.raises(BaseSearch.InvalidResponseError):
            with ignore_deprecation_warnings():
                search.validate_response(invalid_response)

    def test_validate_response_missing_id(self):
        """Test that missing 'id' in source details raises InvalidResponseError"""
        search = BaseSearch()
        invalid_response = {
            "risk": "High",
            "notices": {
                "FBI": {"charges": []}
            }
        }
        with pytest.raises(BaseSearch.InvalidResponseError):
            with ignore_deprecation_warnings():
                search.validate_response(invalid_response)

    def test_validate_response_missing_charges(self):
        """Test that missing 'charges' raises InvalidResponseError"""
        search = BaseSearch()
        invalid_response = {
            "risk": "High",
            "notices": {
                "FBI": {"id": "12345"}
            }
        }
        with pytest.raises(BaseSearch.InvalidResponseError):
            with ignore_deprecation_warnings():
                search.validate_response(invalid_response)

    def test_validate_response_charges_not_list(self):
        """Test that non-list charges raises InvalidResponseError"""
        search = BaseSearch()
        invalid_response = {
            "risk": "High",
            "notices": {
                "FBI": {"id": "12345", "charges": "not a list"}
            }
        }
        with pytest.raises(BaseSearch.InvalidResponseError):
            with ignore_deprecation_warnings():
                search.validate_response(invalid_response)

    def test_validate_response_charge_not_string(self):
        """Test that non-string charge raises InvalidResponseError"""
        search = BaseSearch()
        invalid_response = {
            "risk": "High",
            "notices": {
                "FBI": {"id": "12345", "charges": ["Fraud", 123]}
            }
        }
        with pytest.raises(BaseSearch.InvalidResponseError):
            with ignore_deprecation_warnings():
                search.validate_response(invalid_response)

    def test_validate_response_deprecation_warning(self):
        """Test that calling validate_response raises a deprecation warning"""
        search = BaseSearch()
        valid_response = {
            "risk": "Low",
            "notices": {"FBI": {"id": "123", "charges": []}}
        }
        with pytest.warns(DeprecationWarning):
            search.validate_response(valid_response)


class TestIsNameMatch:
    """Test is_name_match static method

    Tests fuzzy matching of names with configurable similarity thresholds.
    Validates both exact and approximate matching scenarios.
    """

    @pytest.mark.parametrize("name1,name2,threshold,expected", [
        # Exact matches
        ("John Smith", "John Smith", 85, True),
        ("", "", 85, True),
        ("a", "a", 85, True),
        # Case-insensitive matches
        ("john smith", "JOHN SMITH", 85, True),
        # Fuzzy matches above default threshold
        ("John Smith", "Jon Smith", 85, True),
        ("Michael Johnson", "Michael Jonson", 85, True),
        # Fuzzy matches below threshold
        ("John Smith", "Albert Johnson", 85, False),
        # Custom thresholds
        ("John Smith", "John Smit", 95, False),
        ("John Smith", "John S", 50, True),
    ])
    def test_is_name_match_various_scenarios(self, name1, name2, threshold, expected):
        """Test name matching with various scenarios and thresholds"""
        assert BaseSearch.is_name_match(name1, name2, threshold=threshold) == expected


class TestParseHtml:
    """Test parse_html static method"""

    def test_parse_simple_html(self):
        """Test parsing simple HTML"""
        html = "<html><body><p>Hello</p></body></html>"
        result = BaseSearch.parse_html(html)
        assert isinstance(result, bs)
        assert result.find("p").get_text() == "Hello"

    def test_parse_html_with_attributes(self):
        """Test parsing HTML with attributes"""
        html = '<div class="container"><span id="test">Content</span></div>'
        result = BaseSearch.parse_html(html)
        assert result.find("span", {"id": "test"}).get_text() == "Content"

    def test_parse_empty_html(self):
        """Test parsing empty HTML"""
        result = BaseSearch.parse_html("")
        assert isinstance(result, bs)

    def test_parse_malformed_html(self):
        """Test parsing malformed HTML"""
        html = "<div><p>Unclosed"
        result = BaseSearch.parse_html(html)
        assert isinstance(result, bs)

    def test_parse_html_with_special_characters(self):
        """Test parsing HTML with special characters"""
        html = "<p>Special &amp; characters &lt;test&gt;</p>"
        result = BaseSearch.parse_html(html)
        assert "Special & characters <test>" in result.get_text()


class TestParseJson:
    """Test parse_json method

    Tests JSON parsing from HTML content, including error handling
    for malformed JSON and missing HTML elements.
    """

    def test_parse_valid_json_in_pre(self):
        """Test parsing valid JSON from <pre> element"""
        search = BaseSearch()
        html = '<html><pre>{"key": "value", "number": 42}</pre></html>'
        result = search.parse_json(html)
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_parse_complex_json(self):
        """Test parsing complex JSON structure"""
        search = BaseSearch()
        json_data = {"nested": {"key": "value"}, "array": [1, 2, 3]}
        html = f'<pre>{json.dumps(json_data)}</pre>'
        result = search.parse_json(html)
        assert result == json_data

    def test_parse_json_no_pre_element(self):
        """Test parsing when no <pre> element exists"""
        search = BaseSearch()
        html = '<html><body><div>{"invalid": "json"}</div></body></html>'
        result = search.parse_json(html)
        assert result == {}

    def test_parse_json_invalid_json(self):
        """Test parsing invalid JSON in <pre> element"""
        search = BaseSearch()
        html = '<pre>{"invalid json without closing brace</pre>'
        result = search.parse_json(html)
        assert result == {}

    def test_parse_json_with_logger(self, logger_mock):
        """Test parsing invalid JSON logs error when logger is provided"""
        search = BaseSearch(logger=logger_mock)
        html = '<pre>{"invalid json</pre>'
        result = search.parse_json(html)
        assert result == {}
        logger_mock.error.assert_called_once()

    def test_parse_json_no_pre_with_logger(self, logger_mock):
        """Test parsing with no <pre> element logs error when logger is provided"""
        search = BaseSearch(logger=logger_mock)
        html = '<html><body>no pre tag</body></html>'
        result = search.parse_json(html)
        assert result == {}
        logger_mock.error.assert_called_once()

    def test_parse_json_empty_pre(self):
        """Test parsing empty <pre> element"""
        search = BaseSearch()
        html = '<pre></pre>'
        result = search.parse_json(html)
        assert result == {}

    def test_parse_json_whitespace_in_pre(self):
        """Test parsing JSON with whitespace in <pre> element"""
        search = BaseSearch()
        html = '<pre>  {"key": "value"}  </pre>'
        result = search.parse_json(html)
        assert result["key"] == "value"


class TestExtractText:
    """Test extract_text static method

    Tests text extraction from BeautifulSoup elements with various
    scenarios including nested elements, attributes, and edge cases.
    """

    def test_extract_existing_element(self):
        """Test extracting text from existing element"""
        html = '<html><div class="content">Hello World</div></html>'
        soup = bs(html, "html.parser")
        result = BaseSearch.extract_text(soup, "div", {"class": "content"})
        assert result == "Hello World"

    def test_extract_nonexistent_element(self):
        """Test extracting from non-existent element returns default"""
        html = '<html><div>Content</div></html>'
        soup = bs(html, "html.parser")
        result = BaseSearch.extract_text(soup, "span")
        assert result == ""

    def test_extract_custom_default(self):
        """Test extracting with custom default value"""
        html = '<html><div>Content</div></html>'
        soup = bs(html, "html.parser")
        result = BaseSearch.extract_text(soup, "span", default="Not Found")
        assert result == "Not Found"

    def test_extract_text_with_whitespace(self):
        """Test that text is stripped of whitespace"""
        html = '<div>  \n  Content  \n  </div>'
        soup = bs(html, "html.parser")
        result = BaseSearch.extract_text(soup, "div")
        assert result == "Content"

    def test_extract_text_by_id(self):
        """Test extracting text using id attribute"""
        html = '<html><p id="target">Targeted Content</p></html>'
        soup = bs(html, "html.parser")
        result = BaseSearch.extract_text(soup, "p", {"id": "target"})
        assert result == "Targeted Content"

    def test_extract_nested_text(self):
        """Test extracting text from nested elements"""
        html = '<html><div><span><p>Nested Content</p></span></div></html>'
        soup = bs(html, "html.parser")
        result = BaseSearch.extract_text(soup, "p")
        assert result == "Nested Content"

    def test_extract_text_with_special_chars(self):
        """Test extracting text with special characters"""
        html = '<div>Special &amp; chars &lt;test&gt;</div>'
        soup = bs(html, "html.parser")
        result = BaseSearch.extract_text(soup, "div")
        assert "Special & chars <test>" in result


class TestMergeResponses:
    """Test merge_responses static method

    Tests the logic for combining multiple search responses while:
    - Preserving the highest risk level across all responses
    - Deduplicating charges across sources while preserving order
    - Merging notices from multiple sources and handling conflicts
    """

    def test_merge_single_response(self):
        """Test that merging a single response returns it unchanged"""
        responses = [{"risk": "Low", "notices": {"FBI": {"id": "123", "charges": ["Fraud"]}}}]
        result = BaseSearch.merge_responses(responses)
        assert result["risk"] == "Low"
        assert result["notices"]["FBI"]["id"] == "123"

    def test_merge_empty_list(self):
        """Test that merging an empty list returns empty dict"""
        result = BaseSearch.merge_responses([])
        assert result == {}

    def test_merge_duplicate_source_deduplicates_charges(self):
        """Test merging responses from the same source deduplicates charges"""
        responses = [
            {"risk": "Low", "notices": {"FBI": {"id": "123", "charges": ["Fraud"]}}},
            {"risk": "Low", "notices": {"FBI": {"id": "123", "charges": ["Fraud"]}}}
        ]
        result = BaseSearch.merge_responses(responses)
        assert result["risk"] == "Low"
        assert result["notices"]["FBI"]["charges"] == ["Fraud"]

    def test_merge_multiple_sources(self):
        """Test merging responses from different sources"""
        responses = [
            {"risk": "Low", "notices": {"FBI": {"id": "123", "charges": ["Fraud"]}}},
            {"risk": "Medium", "notices": {"Interpol": {"id": "456", "charges": ["Theft"]}}}
        ]
        result = BaseSearch.merge_responses(responses)
        assert "FBI" in result["notices"]
        assert "Interpol" in result["notices"]

    def test_merge_highest_risk(self):
        """Test that highest risk is retained"""
        responses = [
            {"risk": "Low", "notices": {}},
            {"risk": "High", "notices": {}},
            {"risk": "Medium", "notices": {}}
        ]
        result = BaseSearch.merge_responses(responses)
        assert result["risk"] == "High"

    def test_merge_dangerous_risk_is_highest(self):
        """Test that Dangerous is the highest risk level"""
        responses = [
            {"risk": "Dangerous", "notices": {}},
            {"risk": "High", "notices": {}},
            {"risk": "Medium", "notices": {}}
        ]
        result = BaseSearch.merge_responses(responses)
        assert result["risk"] == "Dangerous"

    def test_merge_duplicate_charges(self):
        """Test that duplicate charges are deduplicated"""
        responses = [
            {"risk": "Low", "notices": {"FBI": {"id": "123", "charges": ["Fraud", "Theft"]}}},
            {"risk": "Low", "notices": {"FBI": {"id": "123", "charges": ["Fraud", "Money Laundering"]}}}
        ]
        result = BaseSearch.merge_responses(responses)
        charges = result["notices"]["FBI"]["charges"]
        assert "Fraud" in charges
        assert "Theft" in charges
        assert "Money Laundering" in charges
        assert charges.count("Fraud") == 1  # No duplicates

    def test_merge_preserves_charge_order(self):
        """Test that charge order is preserved during deduplication"""
        responses = [
            {"risk": "Low", "notices": {"FBI": {"id": "123", "charges": ["A", "B", "C"]}}},
            {"risk": "Low", "notices": {"FBI": {"id": "123", "charges": ["B", "D"]}}}
        ]
        result = BaseSearch.merge_responses(responses)
        charges = result["notices"]["FBI"]["charges"]
        # First occurrence order should be preserved
        assert charges.index("A") < charges.index("D")

    def test_merge_multiple_notices_same_response(self):
        """Test merging response with multiple notices"""
        response = {
            "risk": "High",
            "notices": {
                "FBI": {"id": "123", "charges": ["Fraud"]},
                "Interpol": {"id": "456", "charges": ["Theft"]}
            }
        }
        result = BaseSearch.merge_responses([response])
        assert len(result["notices"]) == 2

    def test_merge_complex_structure(self):
        """Test merging complex nested structures"""
        responses = [
            {
                "risk": "Medium",
                "notices": {
                    "FBI": {"id": "123", "charges": ["Fraud"]}
                },
                "metadata": {"source": "FBI"}
            },
            {
                "risk": "High",
                "notices": {
                    "Interpol": {"id": "456", "charges": ["Theft"]}
                },
                "metadata": {"source": "Interpol"}
            }
        ]
        result = BaseSearch.merge_responses(responses)
        assert result["risk"] == "High"
        assert "FBI" in result["notices"]
        assert "Interpol" in result["notices"]
        assert "metadata" in result

    def test_merge_nested_dict_override(self):
        """Test that non-matching nested dict keys are merged"""
        responses = [
            {"risk": "Low", "data": {"key1": "value1"}},
            {"risk": "Low", "data": {"key2": "value2"}}
        ]
        result = BaseSearch.merge_responses(responses)
        assert result["data"]["key1"] == "value1"
        assert result["data"]["key2"] == "value2"


class TestExceptions:
    """Test exception classes"""

    def test_invalid_response_error_exception(self):
        """Test InvalidResponseError can be raised and caught"""
        BaseSearch()
        with pytest.raises(BaseSearch.InvalidResponseError):
            raise BaseSearch.InvalidResponseError()

    def test_captcha_error_exception(self):
        """Test CaptchaError can be raised and caught"""
        BaseSearch()
        with pytest.raises(BaseSearch.CaptchaError):
            raise BaseSearch.CaptchaError()

    def test_invalid_response_error_is_exception(self):
        """Test InvalidResponseError is an Exception"""
        assert issubclass(BaseSearch.InvalidResponseError, Exception)

    def test_captcha_error_is_exception(self):
        """Test CaptchaError is an Exception"""
        assert issubclass(BaseSearch.CaptchaError, Exception)

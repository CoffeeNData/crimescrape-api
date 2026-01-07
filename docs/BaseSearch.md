# Classes and Methods Overview

The code defines a base class for search operations and two derived classes using different methods (
Playwrith/StealthSearch and Requests/RequestsSearch) to fetch web content. It also contains methods for validating data,
matching names using fuzzy logic, parsing HTML/JSON, and more.

## Logging

All the modules must be crafted with an optional logger object in mind. The main reason for this is to pass it to
BaseSearch.
**Developers should NEVER log anything from inside the modules**.
Instead, **use Python's exceptions to delegate this task** to BaseSearch instead of manually handling them.

---

### Class: `BaseSearch`

#### Purpose

The `BaseSearch` class provides common utility methods for performing data validation, fuzzy matching, and HTML/JSON
parsing. It also defines an exception for invalid responses.

#### Methods

- **`__init__(self, logging: Logger | None = None) -> None`**
    - Initializes the `BaseSearch` object with a default fuzzy match threshold value.
    - Also, optionally initializes a logger object.
    - Attributes:
        - `fuzzy_match_threshold`: Default threshold for fuzzy string matching (85).

- **`validate_response(self, data: dict) -> dict`**
  > **WARNING: This function is deprecated**. Only kept for backwards compatibility. Use `gen_respose` for an up-to-date
  approach.
    - Validates if the provided data conforms to a specific format.
    - Checks for required top-level keys (`"risk"` and `"notices"`) and verifies their types and values.
    - Raises `InvalidResponseError` if validation fails.
    - Parameters:
        - `data`: A dictionary to be validated.
    - Returns: The input dictionary if validation succeeds.

- **`gen_response(self, risk: str, source: str, id: str, charges: list[str]) -> dict`**
  > **Note: Please use this function instead of `validate_response` since it has been deprecated.**
    - Builds a response in the correct format.
    - Checks the `risk` is correct. It must be one of these (**case-sensitive**): `Low`, `Medium`, `High`, `Dangerous`.
    - Raises `ValueError` if the `risk` is incorrect.
    - Parameters:
        - `risk`: The risk rating for the found suspect.
        - `source`: The submodule these results belong to. e.g: `europol_most_wanted`
        - `id`: The ID of the notice (if any). Can be blank, but not `None`.
        - `charges`: A list of strings containing all the charges found. Can be blank, but not `None`.
    - Returns: The correctly built results for returning in the submodule in JSON/dict format.

- **`is_name_match(self, local_name: str, remote_name: str, threshold: int = 85) -> bool`**
    - Compares two strings using fuzzy matching with a specified threshold.
    - Parameters:
        - `local_name`: The first string to compare.
        - `remote_name`: The second string to compare.
        - `threshold`: Minimum match score required (default is 85).
    - Returns: `True` if the match score is equal to or greater than the threshold, `False` otherwise.

- **`parse_html(self, html: str) -> bs`**
    - Parses HTML content using `BeautifulSoup`.
    - Parameters:
        - `html`: A string containing the HTML content to parse.
    - Returns: A `BeautifulSoup` object representing the parsed HTML.

- **`parse_json(self, html: str) -> dict`**
    - Extracts and parses JSON data from HTML content.
    - Parameters:
        - `html`: A string containing HTML that includes JSON data.
    - Returns: A dictionary with the parsed JSON data. Returns an empty dictionary if parsing fails.

- **`extract_text(self, soup: bs, tag: str, attributes: dict = {}, default: str = "") -> str`**
    - Extracts text content from a specified HTML tag using a `BeautifulSoup` object.
    - Parameters:
        - `soup`: A `BeautifulSoup` object containing HTML data.
        - `tag`: The HTML tag to search for.
        - `attributes`: A dictionary of attributes for narrowing down the search.
        - `default`: A default string to return if the tag is not found.
    - Returns: The extracted text, or the default string if not found.

- **`merge_results(self, results: list[dict]) -> dict`**
    - Merges two different dict results into one unique dictionary
        - Useful for sites that have multiple search options, but we only can return one unique dict
    - Parameters:
        - `results`: A list of variable lenght on which the dict results are inside.
    - Returns: All the supplied dictionaries as one unique dict.
    - Example:

      ```python
      def search(self, fname: str, lname: str) -> dict | None:
          results = []
          red = self._search_red_notices(fname, lname)
          un = self._search_un_notices(fname, lname)
  
          if not (red or un):
              return None
          if red:
              results.append(red)
          if un:
              results.append(un)
  
          return self.merge_responses(results)
      ```

---

### Class: `StealthSearch`

#### Purpose

The `StealthSearch` class extends `BaseSearch` and uses Playwrith for web scraping.

#### Methods

- **`__init__(self, logging: Logger | None = None, headless: bool = True) -> None`**
    - Initializes the `StealthSearch` object.
    - Also, optionally passes a logger object to the superclass.
    - Parameters:
        - `headless`: Boolean flag indicating whether to run the Playwrith browser in headless mode (default is `True`).
        - `logging`: Logger object to reuse from callers and pass to BaseSearch. Optional.

- **`_start_driver(self) -> None`**
  > Since this driver is shared amongst the whole class/object, multithreading two different functions that require the
  driver will
  > surely result in a race condition. Avoid multithreading the same driver at all costs.
    - Starts a Playwrith Firefox driver instance for the whole object.
    - A driver is auto-started on every request. Manual use of this function is discouraged.

- **`_close_driver(self) -> None`**
    - Closes the Playwrith driver for the whole object.

- **
  `fetch_url(self, url: str, scroll: bool = False, wait_seconds: int | None = None, headers: dict | None = None) -> str`
  **
  > This function starts and closes a driver automatically. Manually using a driver is discouraged.
    - Fetches the content of a specified URL using a Playwrith driver.
    - Parameters:
        - `url`: The URL to fetch.
        - `scroll`: Boolean indicating whether to scroll to the bottom of the page (default is `False`).
        - `wait_seconds`: Optional time to wait after loading the page (in seconds).
        - `headers`: Optional dictionary with custom headers to add to the request.
    - Returns: The page source as a string. Returns an empty string if an error occurs.

- **`post_url(self, url: str, data: dict | None = None, headers: dict | None = None) -> str`**
    - Fetches the content of a specified URL via POST request optionally sending supplied data.
    - Parameters:
        - `url`: The URL to send the POST request to.
        - `data`: Optional field to supply POST data for the request.
        - `headers`: Optional dictionary with custom headers to add to the request.
    - Returns: The response result as a string. Returns an empty string if an error occurs.

---

### Class: `RequestSearch`

#### Purpose

The `RequestSearch` class extends `BaseSearch` and uses the `requests` library to fetch web content.

#### Methods

- **`__init__(self, logging: Logger | None = None) -> None`**
    - Initializes the `RequestSearch` object.
    - Also, optionally passes a logger object to the superclass.

- **`fetch_url(self, url: str, headers: dict | None = None) -> str`**
    - Fetches the content of a specified URL using the `requests` library.
    - Parameters:
        - `url`: The URL to fetch.
        - `headers`: Optional dictionary with custom headers to add to the request.
    - Returns: The response text as a string. Returns an empty string if an error occurs.

- **`post_url(self, url: str, data: dict | None = None, headers: dict | None = None) -> str`**
    - Fetches the content of a specified URL via POST request optionally sending supplied data.
    - Parameters:
        - `url`: The URL to send the POST request to.
        - `data`: Optional field to supply POST data for the request.
        - `headers`: Optional dictionary with custom headers to add to the request.
    - Returns: The response result as a string. Returns an empty string if an error occurs.

---

### Nested Exception Class: `InvalidResponseError`

- **Purpose**: Raised by `validate_response` when the data does not conform to the expected format.

---

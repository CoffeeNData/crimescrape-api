# Crafting modules

## Module structure

A module is a Python file that contains a single class and a unique `search` function inside.
The modules should be located under `/sources` in this repositiry.

Since modules need to make requests to the servers, a [set of utilities](BaseSearch.md) has been prepared for their
development.
**Missing this documentation will heavily punish the codebase**, making it harder to maintain and to update.

## Deciding the engine for the module

CrimeScrape brings two different top-level classes to navigate and process data.

### RequestSearch

This is a Python `requests`-based module. It is simple to use and fast performing. Supports both GET and POST requests.

Since this is fast, simple and lightweight, this is the preferred engine to use during module development.
Use of this engine is encouraged whenever it is possible.

### StealthSearch

This engine is a Firefox stealthy webdriver with both headed and headless support.
Thanks to Playwright and multithreading on the API, the performance has greatly been increased since its private PoC.

Its main purpose is to be undetected by most anti-bot technologies and to grab DOM-rendered content.

It is fast yet still noticeably slower than `RequestSearch` engine.
The use of this engine is discouraged since it is very resource-intensive.

## Module syntax

A set of standard rules and conventions are applied when crafting the modules.
This is to improve readability and maintenance as well as making development faster.

### Rules and conventions

- A module is a python file with the name format `thiswebsite.py`
- Each module file must contain only one class named with the format `ThisWebsiteSearch`
- Each module class NEEDS to contain a `search` function. This is the function that will be called by default in the API
  and standalone program.
- Other functions must start with an underscore. Example: `def _this_is_my_helper_function(self, website:str) -> None`
- Modules will return `None` if no result was found.
- If there were found results, you need to return the result of `BaseSearch.gen_response()`. See the docs for more
  information.
- For logging, use exceptions in the modules. `BaseSearch` will handle the logging.

### Crafting a RequestSearch module

RequestSearch modules are a bit easier to craft since they do not need all the webdriver management.

#### Example: RequestSearch module to search by name

```python
from sources.basesearch import RequestSearch


class MyOwnModuleSearch(RequestSearch):
    def __init__(self, logging: Logger | None = None) -> None:
        super().__init__(logging)
        self.baseurl = "http://example.com/"

    # Example helper function
    def _helper_function_1(self) -> None:
        example.do_stuff()

    # Another example function
    def _extract_content(self, soup) -> tuple[str, str, list]:
        # Example function that will scrape the
        # provided site and will return a list
        # containing the final results
        return content

    # Mandatory function that will perform the search
    def search(self, fname: str, lname: str) -> dict | None:
        site = self.fetch_url(self.baseurl)
        soup = self.parse_html(site)  # parse_html converts HTML content into a BeautifulSoup object

        self._helper_function_1()

        content = self._extract_content(soup)
        if not content:
            return None  # Nothing was found

        risk: str, notice_id: str, charges: list = content
        return self.gen_response(risk, "mymodulesearch", notice_id, charges)
```

### Crafting a StealthSearch module

StealthSearch modules are a bit trickier to craft.
A simple interface to code new is provided with the engine, but it is STRONGLY adviced to keep at hand the Playwright
docs.

Things to keep in mind:

- **AVOID starting or closing the driver manually at all costs**.
    - Sometimes websites are more complex and we need to do this. In this case, **DO NOT use the integrated fetch and
      post functions as this will CRASH the module**.
- Drivers are started and stopped automatically on each request.

In general, developing StealthSearch modules is pretty straightforward.
The syntax is the same as in the previous RequestSearch example, but with one exception: the `__init__` function must
account for headless mode.
This is easy and looks like this:

```python
def __init__(self, logging: Logger | None = None, headless: bool = True):
    super().__init__(logging, headless)  # Support for headless mode!
```

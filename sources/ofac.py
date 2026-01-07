from logging import Logger

from lib.searchutils import StealthSearch


class OFACSearch(StealthSearch):
    def __init__(self, headless: bool = False, logging: Logger | None = None):
        super().__init__(logger=logging, headless=headless)
        self.ofac_url = "https://sanctionssearch.ofac.treas.gov/"

    def _search_for_target(self, query: str) -> None:
        """Navigate the site using supplied query as search term"""

        if not self.driver:
            raise ValueError(
                "Tried to navigate the site but the webdriver hasnt been started"
            )

        self.driver.goto(self.ofac_url)
        self.driver.select_option(
            'select[name="ctl00$MainContent$ddlType"]', value="Individual"
        )  # Select "Individual" from the dropdown.
        self.driver.fill(
            'input[name="ctl00$MainContent$txtLastName"]', query
        )  # Fill in the "Name:" field.
        self.driver.click(
            'input[name="ctl00$MainContent$btnSearch"]'
        )  # Click the search button.
        self.driver.wait_for_load_state("domcontentloaded")

    def _get_details_url(self) -> str:
        """Gets the URL where the details of the first match are located"""

        if not self.driver:
            raise ValueError(
                "Tried to navigate the site but the webdriver hasnt been started"
            )

        # Load site content
        site = self.driver.content()
        soup = self.parse_html(site)

        # Parse the grid to find the first occurrence relative URL
        table = soup.find("table", {"id": "gvSearchResults"})
        row = table.find("tr")  # type: ignore
        col = row.find("td")  # type: ignore
        uncomplete_url = col.find("a")["href"]  # type: ignore

        # Craft a full URL
        url = f"{self.ofac_url}{uncomplete_url}"
        return url

    def _grab_details(self, url: str) -> dict:
        """Extracts the details from the suspect given a URL"""

        if not self.driver:
            raise ValueError(
                "Tried to navigate the site but the webdriver hasnt been started"
            )

        # Go to the URL and parse the content to a BeautifulSoup object
        self.driver.goto(url)
        self.driver.wait_for_load_state("domcontentloaded")
        site = self.driver.content()
        soup = self.parse_html(site)

        # Get notice ID
        table = soup.find("table", {"class": "MainTable"})
        row = table.findAll("tr")[1]  # type: ignore
        col = row.findAll("td")[3]  # type: ignore
        notice_id = col.get_text(strip=True)

        # Get the risk-related cell
        risk_table = soup.find("table", {"id": "ctl00_MainContent_gvIdentification"})
        risk_row = risk_table.findAll("tr")[1]  # type: ignore
        risk_col = risk_row.findAll("td")
        risk_cell = risk_col[0].get_text(strip=True)

        # Evaluate risk
        risk = ""
        if ("drug" or "murder" or "kill" or "terrorist" or "terrorism") in risk_cell:
            risk = "Dangerous"
        else:
            risk = "High"

        # Evaluate charges
        table = soup.find("table", {"id": {"ctl00_MainContent_gvIdentification"}})
        row = table.findAll("tr")[1]  # type: ignore
        col = row.findAll("td")[1]
        charges = [col.get_text(strip=True)]

        return self.gen_response(risk, "ofac-sanctions", notice_id, charges)

    def search(self, fname: str, lname: str) -> dict | None:
        """
        Search the OFAC Sanctions List by name.
        If both surname and given names are provided, the query is formatted as:
            surname, given names
        Returns the result in the standard format using validate_response.
        """
        # Format the query to match OFAC's display format.
        if fname and lname:
            query = f"{fname}, {lname}"
        else:
            query = f"{fname} {lname}".strip()

        try:
            # Make sure the driver is up before messing up
            self._start_driver()
            if not self.driver:
                return None

            # Search subject
            self._search_for_target(query)

            # Check if there are any results
            site = self.driver.content()
            soup = self.parse_html(site)
            div = soup.find("div", {"id": "ctl00_MainContent_divResults"})
            lookup_results = div.get_text(strip=True)  # type: ignore
            lookup_results = lookup_results.split("Lookup Results: ")[1]
            lookup_results = lookup_results.split(" Found")[0]
            lookup_results = int(lookup_results)

            # If there's no results, exit.
            if lookup_results < 1:
                return None

            details_url = self._get_details_url()
            return self._grab_details(details_url)

        finally:
            self._close_driver()

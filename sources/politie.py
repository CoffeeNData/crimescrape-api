from logging import Logger

from bs4 import BeautifulSoup as bs

from lib.searchutils import StealthSearch


class PolitieSearch(StealthSearch):
    def __init__(self, headless: bool = True, logging: Logger | None = None):
        # Initialize the parent class with optional headless browsing
        super().__init__(logger=logging, headless=headless)
        self.search_url = (
            "https://www.politie.nl/en/search?type=gezocht&sort=relevance&query="
        )

    def _verify_wanted(self, searchlist: bs) -> bool:
        """Verifies if a suspect is marked as 'Wanted' on the page.

        Args:
            searchlist (bs): BeautifulSoup object containing search results.

        Returns:
            bool: True if 'Wanted' tag is found, otherwise False.
        """
        try:
            wanted_text = searchlist.find("div", {"class": "tag-item"})
            return bool(wanted_text and wanted_text.get_text(strip=True) == "Wanted")
        except AttributeError:  # More specific error handling
            return False

    def _get_risk_score(self, charges: list) -> str:
        """Determines the risk score based on a list of charges.

        Args:
            charges (list): List of charge descriptions.

        Returns:
            str: Risk level, either 'Dangerous' or 'High'.
        """
        high_risk_keywords = {"murder", "narcotics", "drugs", "trafficking", "traffick"}
        for charge in charges:
            # Check if any high-risk keyword is in the charge description
            if any(keyword in charge.lower() for keyword in high_risk_keywords):
                return "Dangerous"
        return "High"

    def _grab_info(self, url: str) -> dict:
        """Extracts suspect information from a specific URL.

        Args:
            url (str): URL to fetch suspect details.

        Returns:
            dict: Dictionary containing risk level, case ID, and charges.
        """
        site = self.parse_html(self.fetch_url(url))
        banner_data = site.find("dl", {"class": "blok-onderkant-2 metadata-dl"})

        # Extract the case ID if available
        case_id = "Unavailable"
        if banner_data:
            case_text = banner_data.get_text(separator="|", strip=True)
            if "Case number:" in case_text:
                try:
                    case_id = case_text.split("Case number:|")[1].split("|")[0]
                except IndexError:
                    pass  # Maintain 'Unavailable' if parsing fails

        # Extract charges if available
        charges = ["Unavailable"]
        charges_section = site.find("section", {"class": "content-blocks clearfix"})
        if charges_section:
            charges_text = charges_section.get_text(strip=True, separator="|").split(
                "|"
            )
            if len(charges_text) > 1:
                charges = charges_text[1:]  # Ignore the first "Description" tag

        # Determine risk level
        risk = self._get_risk_score(charges)

        return {
            "risk": risk,
            "notices": {
                "politie-netherlands": {
                    "id": case_id,
                    "charges": charges,
                }
            },
        }

    def search(self, fname: str, lname: str) -> dict | None:
        """Searches for the most wanted person by name.

        Args:
            fname (str): First name of the person.
            lname (str): Last name of the person.

        Returns:
            dict | None: Search results if a match is found, otherwise None.
        """
        fullname = (
            f"{fname} {lname}".title()
        )  # Use titlecase for better search compatibility
        data = self.fetch_url(f"{self.search_url}{fullname}", wait_seconds=1)
        bs_data = self.parse_html(data)

        # Attempt to find the overview item containing suspect information
        searchlist = bs_data.find("div", {"class": "overview-item"})
        if not searchlist:
            return None

        subject = searchlist.find("a")
        if not subject or not self._verify_wanted(searchlist):
            return None

        infourl = subject.get("href", "")
        if not infourl:
            return None

        # Gather detailed information and validate the response structure
        ret = self._grab_info(infourl)
        return self.validate_response(ret)

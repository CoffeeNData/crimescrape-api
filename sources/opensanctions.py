from logging import Logger
from time import sleep

from lib.basesearch import BaseSearch
from lib.searchutils import StealthSearch


class OpenSanctionsSearch(StealthSearch):
    def __init__(self, logging: Logger | None = None, headless: bool = True) -> None:
        super().__init__(logger=logging, headless=headless)
        self.base_url = "https://www.opensanctions.org"

    def search(self, fname: str, lname: str) -> dict | None:
        """Search a suspect in OpenSanctions"""

        # Search
        try:
            site = self.fetch_url(
                f"{self.base_url}/search/?q={fname} {lname}", wait_seconds=3
            )
        # Retry if CAPTCHA is found. Won't make a second attempt
        except BaseSearch.CaptchaError:
            sleep(5)
            site = self.fetch_url(
                f"{self.base_url}/search/?q={fname} {lname}", wait_seconds=3
            )

        soup = self.parse_html(site)

        # Get the details URL
        res_list = soup.findAll("div", {"class": "col-md-8"})[1]  # type: ignore
        res_item = res_list.find("a")  # type: ignore
        details_url = self.base_url + res_item["href"]  # type: ignore

        # Extract details
        try:
            site = self.fetch_url(details_url, wait_seconds=3)
        except BaseSearch.CaptchaError:
            sleep(5)
            site = self.fetch_url(details_url, wait_seconds=3)
        soup = self.parse_html(site)

        # Parse suspect tags
        tags = []
        for tag in soup.findAll(
            "span", {"class": "badge"}  # type: ignore
        ):  # This matches more things than necessary but it still works
            tags.append(tag.get_text(strip=True))

        # Evaluate risk
        risk = "Low"
        if "Sanctioned entity" in tags:
            risk = "Medium"
        if "Crime" in tags:
            risk = "High"
        if "Wanted" in tags:
            risk = "Dangerous"

        # Set remaining data
        notice_id = ""
        charges = [
            details_url
        ]  # We put the URL as charges since there are lots of resources
        source = "opensanctions"

        # Finally return
        return self.gen_response(risk, source, notice_id, charges)

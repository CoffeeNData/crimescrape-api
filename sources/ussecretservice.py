from logging import Logger

from bs4 import BeautifulSoup as bs

from lib.searchutils import RequestSearch


class SecretServiceSearch(RequestSearch):
    def __init__(self, logging: Logger | None = None):
        super().__init__(logger=logging)
        self.base_url = "https://www.secretservice.gov"

    def _get_details(self, details_url: str) -> dict:
        site = self.fetch_url(details_url)
        site = self.parse_html(site)

        risk: str = "High"
        charges: list[str]

        # Check if there's a reward on their head. If there is, risk = Dangerous
        reward_banner = site.find(
            "section",
            {
                "class": "usa-graphic-list usa-section usa-section--dark bg-blue stat-section three-cards-container news-three-cards padding-left-2"
            },
        )
        if reward_banner:
            reward_banner = reward_banner.find("h2")
            reward_banner = reward_banner.get_text(strip=True)
            if "Reward" in reward_banner:
                risk = "Dangerous"

        # Extract the charges
        page_content = site.find(
            "div",
            {"class": "usa-layout-docs__main"},
        )
        page_content = page_content.get_text(separator="|", strip=True)  # type: ignore
        page_content = page_content.split("CASE SUMMARY|")[1]
        page_content = page_content.split("|Relevant Links")[0]
        charges = page_content.split("|")

        return self.gen_response(risk, "us-secret-service", "", charges)

    def _process_grid(self, grid: bs, fullname: str) -> str | None:
        """Check if it's a match and then extract the details URL"""

        for card in grid:
            name = card.find("div", {"class": "text"})  # type: ignore

            name = name.find("h3")
            name = name.get_text(strip=True).upper()

            if self.is_name_match(name, fullname):
                details_url = card.find("a", {"class": "usa-button"})["href"]  # type: ignore
                details_url = self.base_url + details_url
                return details_url
        return None

    def search(self, fname: str, lname: str) -> dict | None:
        site = self.fetch_url("https://www.secretservice.gov/investigations/mostwanted")
        site = self.parse_html(site)
        fullname = f"{fname} {lname}".upper()

        grid = site.findAll(
            "div", {"class": "wanted-card"}
        )

        details_url = self._process_grid(grid, fullname)  # type: ignore

        details = self._get_details(details_url)
        return details if details else None

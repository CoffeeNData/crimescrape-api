from logging import Logger

from lib.searchutils import StealthSearch


class NCASearch(StealthSearch):
    def __init__(self, headless: bool = True, logging: Logger | None = None):
        super().__init__(logger=logging, headless=headless)
        self.nca_url = "https://www.nationalcrimeagency.gov.uk/most-wanted"

    def _parse_names(self, soup) -> list[dict]:
        """Parse the raw soup into a loopable list of dictionaries containing the names and URLs"""
        name_divs = soup.findAll("div", {"itemprop": "blogPost"})
        criminals = []

        for div in name_divs:
            try:
                name = (
                    div.find("div", {"class": "page-header"})
                    .get_text(strip=True)
                    .upper()
                )
                charges = div.find("div", {"class": "intro-text"}).get_text(strip=True)
                criminals.append({"name": name, "charges": [charges]})
            except AttributeError as e:
                print(f"Error parsing entry: {e}")
                continue

        return criminals

    def search(self, fname: str, lname: str) -> dict | None:
        """Search UK's NCA most wanted list"""
        try:
            src = self.fetch_url(self.nca_url)
            soup = self.parse_html(src)
        except Exception as e:
            print(f"Error fetching or parsing URL: {e}")
            return None

        fullname = f"{fname} {lname}".upper()

        # Parse names and URLs
        for suspect in self._parse_names(soup):
            if self.is_name_match(fullname, suspect["name"]):
                return self.validate_response(
                    {
                        "risk": "Dangerous",
                        "notices": {
                            "nca-most-wanted": {"id": "", "charges": suspect["charges"]}
                        },
                    }
                )

        return None

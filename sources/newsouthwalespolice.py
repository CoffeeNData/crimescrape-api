from logging import Logger

from lib.searchutils import RequestSearch


class NewSouthWalesPoliceSearch(RequestSearch):
    def __init__(self, logging: Logger | None = None):
        super().__init__(logger=logging)
        self.base_url = "https://www.police.nsw.gov.au/can_you_help_us/"

    def _get_notice(self, url: str) -> dict | None:
        """Extract the details for a found suspect"""

        # Retrieve the site and get the details
        site = self.fetch_url(url)
        site = self.parse_html(site)
        detail_grid = site.find("div", {"class": "wantedProfileBio"})
        detail_rows = detail_grid.findAll("div", {"class": "mw-detail"})  # type: ignore

        # Try to find the charges
        for row in detail_rows:
            row_text = row.get_text(strip=True)
            # row_text = row_text.upper()

            if "WANTED FOR" in row_text.upper():  # Found them
                charges_str: str = row_text.split(":")[1]
                results = self.gen_response(
                    "High", "newsouthwales-most-wanted", "", [charges_str]
                )
                return results
        else:
            raise self.InvalidResponseError(
                f"Suspect was found but we failed retrieving details."
            )

    def search(self, fname: str, lname: str) -> dict | None:
        site = self.fetch_url(self.base_url + "wanted")
        site = self.parse_html(site)

        # Get the suspect grid
        suspect_grid = site.find("ul", {"class": "p-photo-grid__list"})
        suspects = suspect_grid.findAll("li")  # type: ignore

        # Search inside the grid
        fullname = (fname + " " + lname).upper()
        for suspect in suspects:
            sfullname = suspect.find("img", {"class": "p-photo-grid__img"})[
                "alt"
            ].upper()

            if self.is_name_match(fullname, sfullname):  # They're in here
                url = suspect.find("a", {"class": "p-photo-grid__link"})["href"]
                url = self.base_url + url
                try:
                    notice = self._get_notice(url)
                    return notice
                except self.InvalidResponseError as e:
                    print(f"An error occured during search for {fullname}: {e}")
                    return None

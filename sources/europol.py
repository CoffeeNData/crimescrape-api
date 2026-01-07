from logging import Logger

from lib.searchutils import StealthSearch


class EuropolSearch(StealthSearch):
    def __init__(self, headless: bool = True, logging: Logger | None = None):
        super().__init__(logger=logging, headless=headless)

    @staticmethod
    def _get_subject_list(soup) -> list[dict]:
        slist = []

        # Should not fail, so we don't try/except
        for item in soup.find_all("div", {"class": "wanted_teaser_quick_info"}):
            try:
                # Parse the name
                namediv = item.find("div", {"class": "micro-title"}).get_text()
                slname, sfname = namediv.split(", ")
                sfullname = f"{sfname} {slname}".upper()

                # Get the charges
                charges = item.find("div", {"class": "crime"}).get("data-crime-area")

                # Are they dangerous?
                try:
                    is_dangerous = (
                        item.find("div", {"class": "is-dangerous"}).get_text()
                    )
                except AttributeError:
                    is_dangerous = False

                # Process and append
                slist.append([
                    {
                        "fullname": sfullname if sfullname else "",
                        "charges": charges if charges else "",
                        "dangerous": is_dangerous if is_dangerous else False,
                        "nid": "",  # No notice ID available anymore
                    }
                ])
            except ValueError:
                continue
        return slist

    def search(self, fname: str, lname: str) -> dict | None:
        src = self.fetch_url("https://eumostwanted.eu/", wait_seconds=3)
        soup = self.parse_html(src)
        fullname = f"{fname} {lname}".upper()

        # First, get all the names in the site
        slist = self._get_subject_list(soup)
        if not slist:
            raise RuntimeError("Failed to retrieve subject list from Europol Most Wanted")

        # Now loop through the subjects to see if there's a match
        for s in slist:
            if self.is_name_match(fullname, s[0]["fullname"]):
                risk = "Dangerous" if s[0]["dangerous"] else "High"
                source = "europol-most-wanted"
                notice_id = s[0]["nid"]
                charges = s[0]["charges"]
                return self.gen_response(risk, source, notice_id, charges)
        return None

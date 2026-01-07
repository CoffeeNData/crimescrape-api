from logging import Logger
from urllib.parse import quote_plus as urlencode

from lib.searchutils import StealthSearch


class InterpolSearch(StealthSearch):
    def __init__(self, headless: bool = True, logging: Logger | None = None):
        """Initializes the InterpolSearch object, inheriting from BaseSearch."""
        super().__init__(logger=logging, headless=headless)

    def _process_notice(self, notice_data: dict, notice_type: str) -> dict:
        """Process notice data to extract relevant information."""
        charges_tmp = [
            warrant.get("charge", "Unknown")
            for warrant in notice_data.get("arrest_warrants", [])
        ]
        try:
            charges = charges_tmp[0].split(";\r\n")
        except:
            charges = charges_tmp
        return {
            "risk": "Dangerous",
            "notices": {
                f"interpol-{notice_type}-notice": {
                    "id": notice_data.get("entity_id"),
                    "charges": charges or ["No charges available"],
                }
            },
        }

    def _search_red_notices(self, fname: str, lname: str) -> dict | None:
        """Search Interpol Red Notices by first and last name."""
        search_url = f"https://ws-public.interpol.int/notices/v1/red?name={lname}&forename={fname}"
        html = self.fetch_url(search_url)
        src = self.parse_json(html)

        if src.get("total", 0) == 0:
            return None

        noticeid = src["_embedded"]["notices"][0]["entity_id"]
        notice_url = (
            f"https://ws-public.interpol.int/notices/v1/red/{urlencode(noticeid)}"
        )
        notice_data = self.parse_json(self.fetch_url(notice_url))
        return self.validate_response(self._process_notice(notice_data, "red"))

    def _search_un_notices(self, fname: str, lname: str) -> dict | None:
        """Search UN Notices by first and last name."""
        search_url = f"https://ws-public.interpol.int/notices/v1/un?name={lname}&page=1&resultPerPage=1000"
        html = self.fetch_url(search_url)
        src = self.parse_json(html)

        for notice in src.get("_embedded", {}).get("notices", []):
            if (
                notice["forename"].upper() == fname.upper()
                and notice["name"].upper() == lname.upper()
            ):
                noticeid = notice["entity_id"]
                notice_url = f"https://ws-public.interpol.int/notices/v1/un/persons/{urlencode(noticeid)}"
                notice_data = self.parse_json(self.fetch_url(notice_url))
                return self.validate_response(self._process_notice(notice_data, "un"))
        return None

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

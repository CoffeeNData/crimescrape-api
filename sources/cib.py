import json
from logging import Logger

from lib.searchutils import RequestSearch


class CIBSearch(RequestSearch):
    def __init__(self, logging: Logger | None = None) -> None:
        super().__init__(logger=logging)

        # CIB provides a basic JSON API to retrieve the suspects
        self.url = "https://www.cib.npa.gov.tw/en/app/openData/globalcase/list?module=globalcase&mserno=f684c981-0fd0-44a8-a37d-07b100b26ae2&type=json"

    def _extract_noticeid(self, entry) -> str:
        noticeid = entry["images"][0]["fileurl"]
        noticeid = noticeid.split("=")
        noticeid = noticeid[2]
        noticeid = noticeid.split("&")
        noticeid = noticeid[0]
        return noticeid

    def search(self, fname: str, lname: str) -> dict | None:
        json_data: list[dict] = json.loads(self.fetch_url(self.url))
        fullname = f"{fname} {lname}".upper().replace(
            "-", ""
        )  # Chinese names often have hyphens, but we don't want em

        for entry in json_data:
            try:
                # Parse name
                slname, sfname = (
                    entry["secSubject"].upper().replace("-", "").split(", ")
                )  # Again, remove the hyphen
                sfullname = f"{sfname} {slname}"
            except:
                sfullname = entry["secSubject"]

            if self.is_name_match(fullname, sfullname, 60):
                noticeid = self._extract_noticeid(entry)
                charges = entry["accusation"].lower().capitalize()
                risk: str = (
                    "Dangerous" if ("DRUG" or "NARCOTIC") in charges else "Medium"
                )

                # Sometimes there are multiple charges
                charges = charges.split("&amp;")

                res = {
                    "risk": risk,
                    "notices": {
                        "cib-most-wanted": {
                            "id": noticeid,
                            "charges": charges,
                        }
                    },
                }
                return self.validate_response(res)

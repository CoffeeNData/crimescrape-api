import json
from logging import Logger

import requests

from lib.searchutils import RequestSearch


class OFSISearch(RequestSearch):
    def __init__(self, logging: Logger | None = None) -> None:
        super().__init__(logger=logging)
        self.search_url = "https://ofsiconlistsearch.search.windows.net"
        self.api_key = "Pxja1OS8r5bjQElByZahu5Fqzc6ufTMRyS2RPxXh3YAzSeC2rN3n"
        """
        NOTE:
        Since their site is fueled by their own API, a key is needed.
        Of course, it can be found by digging in the XHR source of the site:
            - XHR URL: https://sanctionssearchapp.ofsi.hmtreasury.gov.uk/main.bundle.js
            - Variable name: searchApiKey
        """

    def search(self, fname: str, lname: str) -> dict | None:

        # Craft the custom request
        query = f"{fname} {lname}"

        url = (
            self.search_url
            + "/indexes/livesearch/docs?api-version=2021-04-30-Preview&$filter=(GrpStatus eq 'A' or GrpStatus eq 'I')&$top=1&$skip=0&$count=true&$orderby=search.score() desc,Name6,name1,name2,name3&search="
            + query
        )
        headers = {
            "Api-Key": self.api_key,  # An API key is needed and supplied by the page itself
        }

        # Get data
        r = requests.get(url=url, headers=headers)
        data = json.loads(r.text)
        data = data["value"][0]
        # Set results
        risk = "High"
        source = "ofsi-sanctions"
        notice_id = data["FCOId"]
        charges = [data["UKStatementOfReasons"]]
        return self.gen_response(risk, source, notice_id, charges)

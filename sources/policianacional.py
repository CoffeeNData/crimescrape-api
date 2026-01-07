import re
from logging import Logger

from lib.searchutils import RequestSearch


class PoliciaNacionalSearch(RequestSearch):
    def __init__(self, logging: Logger | None = None) -> None:
        super().__init__(logger=logging)
        self.searchurl = "https://www.policia.es/_es/colabora_masbuscados.php"
        self.baseurl = "https://www.policia.es/_es/"

    @staticmethod
    def _parse_name(parentdiv) -> str:
        res = parentdiv.find("h5", {"class": "card-title text-center"})
        res = res.get_text(strip=False)
        res = res.replace("\t", "")
        res = res.replace("\n", " ")  # Replace the remaining newline with a space
        res = res.replace("\r", "")  # Replace the carriage return
        res = res[1:]  # Remove first character, which is a space
        res = res.upper()
        return res

    def _get_charges(self, suspect_file) -> list[str]:
        # Extract the URL of the details
        fileurl = suspect_file.find("a")
        fileurl = fileurl["href"]
        fileurl = f"{self.baseurl}{fileurl}"

        # Request the file and process it
        soup = self.parse_html(self.fetch_url(fileurl))
        info = soup.findAll("dd", {"class": "col-sm-7"})
        info = info[2]
        info = info.get_text(strip=True)  # type: ignore
        info = info.split("buscado por ")[1]

        # Split charges
        info = re.split(r",| y | e ", info)

        # Parse and clean the charges
        charges = []
        for i in info:
            i = i.strip()
            i = i.capitalize()
            if i.endswith("."):
                i = i[:-1]
            charges.append(i)
        return charges

    def search(self, fname: str, lname: str) -> dict | None:
        fullname = f"{fname} {lname}".upper()
        soup = self.parse_html(self.fetch_url(self.searchurl))

        # Find all the suspect files
        files = soup.findAll(
            "div",
            {
                "class": "col-12 col-md-6 col-lg-4 col-xl-2 my-3 d-flex align-items-stretch justify-content-center m-md-3 m-lg-1"
            },
        )

        # Loop through them until we get a match
        for file in files:
            # Check if it's our guy
            name = self._parse_name(file)
            if self.is_name_match(fullname, name):
                # It's our guy, so parse
                charges = self._get_charges(file)
                risk = "Dangerous"
                source = "policianacional-most-wanted"
                notice_id = ""
                return self.gen_response(risk, source, notice_id, charges)
        return None

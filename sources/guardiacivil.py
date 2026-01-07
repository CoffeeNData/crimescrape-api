from logging import Logger
from time import sleep

from lib.searchutils import RequestSearch


class GuardiaCivilSearch(RequestSearch):
    def __init__(self, logging: Logger | None = None) -> None:
        super().__init__(logger=logging)
        self.searchurl = (
            "https://web.guardiacivil.es/es/colaboracion/Buscados/buscados/"
        )
        self.baseurl = "https://www.guardiacivil.es"

    def search(self, fname: str, lname: str) -> dict | None:
        fullname = f"{fname} {lname}".upper()

        # Find out how many pages are in the database
        src = self.fetch_url(self.searchurl)
        soup = self.parse_html(src)

        # Parse the page number
        page_n = soup.find("div", {"class": "paginacion_contenedor"})  # Find the element
        page_n = page_n.find("a", {"class": "paginacion_ultima"})  # Find the last page link
        page_n = page_n["href"]  # Get the href attribute
        page_n = page_n.split("page=")  # Split to isolate the page number
        page_n = page_n[1]  # Keep only the page number
        page_n = int(page_n)  # Cast to an integer for easier processing

        # Loop first around pages
        details_url = None
        for page in range(
                1, page_n + 1
        ):  # for in range loops are non-inclusive so we add 1 to the range
            url = f"{self.searchurl}?pagina={page}"
            soup = self.parse_html(self.fetch_url(url))
            suspect_files = soup.findAll("div", {"class": "contenido_elemento"})

            for file in suspect_files:
                name = file.find("h3", {"class": "nombre-buscado"})
                name = name.get_text().strip()

                if self.is_name_match(fullname, name):
                    url_temp = file.find("a")
                    url_temp = url_temp["href"]
                    details_url = f"{self.baseurl}{url_temp}"
                    break

            if details_url:
                return self.gen_response("Dangerous", "guardiacivil-most-wanted", "", "Unknown")
            sleep(3)
        return None

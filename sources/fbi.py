from logging import Logger

from lib.searchutils import StealthSearch


class FBISearch(StealthSearch):
    def __init__(self, headless: bool = True, logging: Logger | None = None):
        """Initializes the FBISearch object, inheriting from BaseSearch."""
        super().__init__(logger=logging, headless=headless)
        self.non_dangerous_crimes = ["White Collar Crimes", "Counterintelligence"]

    def _clean_charges(self, charges_str: str) -> list[str]:
        """Parse the charges for a cleaner reading and more solid typing"""
        charges = charges_str.split("; ")
        res = []
        for charge in charges:
            # if charge.startswith(" "):
            #     charge = charge[1:]
            # if charge.endswith(" "):
            #     charge = charge[-1]
            charge = charge.lower().capitalize()
            res.append(charge)
        return res

    def _scrape_details(
        self, notice_url: str, matched_name: str, crime: str = ""
    ) -> dict:
        """Scrape the details of the matched notice and return risk level and charges."""
        soup = self.parse_html(self.fetch_url(notice_url))
        name_banner = self.extract_text(
            soup, "h1", {"class": "documentFirstHeading"}, matched_name
        )

        if name_banner != matched_name:
            print(
                f"[ERROR] Name mismatch: expected '{matched_name}', found '{name_banner}'"
            )
            return self._default_notice(crime)

        charges = self.extract_text(soup, "p", {"class": "summary"}, "Unknown")
        warning_banner = self.extract_text(
            soup, "h3", {"class": "wanted-person-warning panel"}, ""
        )
        risk = "Dangerous" if "DANGEROUS" in warning_banner else "High"

        return {
            "risk": risk,
            "notices": {
                "fbi-most-wanted": {
                    "id": crime.lower().replace(" ", ""),
                    "charges": self._clean_charges(charges),
                }
            },
        }

    def _default_notice(self, crime: str) -> dict:
        """Default notice in case of errors or mismatches."""
        return {
            "risk": "High" if crime in self.non_dangerous_crimes else "Dangerous",
            "notices": {"fbi-most-wanted": {"id": "", "charges": ["Unknown"]}},
        }

    def _perform_search(
        self, url: str, fname: str, lname: str, name_selector: dict, scroll: bool = True
    ) -> dict | None:
        """General search method with optional scrolling."""
        soup = self.parse_html(self.fetch_url(url, scroll=scroll))

        fullname = f"{fname} {lname}".upper()
        for item in soup.find_all(name_selector["tag"], name_selector["attributes"]):
            name = self.extract_text(
                item, name_selector["name_tag"], name_selector["name_class"], ""
            )
            if self.is_name_match(fullname, name):
                crime = self.extract_text(
                    item,
                    name_selector.get("crime_tag", ""),
                    name_selector.get("crime_class", {}),
                )
                return self._scrape_details(item.find("a")["href"], name, crime)
        return None

    def _search_most_wanted(self, fname: str, lname: str) -> dict | None:
        """Search FBI's Most Wanted list."""
        name_selector = {
            "tag": "li",
            "attributes": {"class": "portal-type-person castle-grid-block-item"},
            "name_tag": "h3",
            "name_class": {"class": "title"},
        }
        url = "https://www.fbi.gov/wanted/topten"

        res = self._perform_search(url, fname, lname, name_selector, scroll=False)
        return res

    def _search_fugitives(self, fname: str, lname: str) -> dict | None:
        """Search FBI's Fugitive list."""
        name_selector = {
            "tag": "li",
            "attributes": {"class": "portal-type-person castle-grid-block-item"},
            "name_tag": "p",
            "name_class": {"class": "name"},
            "crime_tag": "h3",
            "crime_class": {"class": "title"},
        }
        url = "https://www.fbi.gov/wanted/fugitives"

        res = self._perform_search(url, fname, lname, name_selector)
        return res if res else None

    def _search_terrorists(self, fname: str, lname: str) -> dict | None:
        """Search FBI's Terrorist list."""
        name_selector = {
            "tag": "li",
            "attributes": {"class": "portal-type-person castle-grid-block-item"},
            "name_tag": "p",
            "name_class": {"class": "name"},
            "crime_tag": "h3",
            "crime_class": {"class": "title"},
        }
        url = "https://www.fbi.gov/wanted/terrorism"

        res = self._perform_search(url, fname, lname, name_selector)
        return res if res else None

    def search(self, fname: str, lname: str) -> dict | None:
        results = []
        most_wanted = self._search_most_wanted(fname, lname)
        fugitives = self._search_fugitives(fname, lname)
        terrorists = self._search_terrorists(fname, lname)

        if not (most_wanted or fugitives or terrorists):
            return None
        if most_wanted and most_wanted != "":
            results.append(most_wanted)
        if fugitives and fugitives != "":
            results.append(fugitives)
        if terrorists and terrorists != "":
            results.append(terrorists)

        return self.merge_responses(results)

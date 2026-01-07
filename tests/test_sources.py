import pytest

from lib.basesearch import BaseSearch
from sources.cib import CIBSearch
from sources.europol import EuropolSearch
from sources.fbi import FBISearch
from sources.guardiacivil import GuardiaCivilSearch
from sources.interpol import InterpolSearch
from sources.nca import NCASearch
from sources.newsouthwalespolice import NewSouthWalesPoliceSearch
from sources.ofac import OFACSearch
from sources.ofsi import OFSISearch
from sources.opensanctions import OpenSanctionsSearch
from sources.policianacional import PoliciaNacionalSearch
from sources.ussecretservice import SecretServiceSearch

HEADLESS = True


class TestModules:

    def test_fbi_most_wanted(self):
        expected_result = {
            "risk": "High",
            "notices": {
                "fbi-most-wanted": {
                    "id": "",
                    "charges": [
                        "Conspiracy to commit wire fraud",
                        "Wire fraud",
                        "Conspiracy to commit money laundering",
                        "Conspiracy to commit securities fraud",
                        "Securities fraud",
                    ],
                }
            },
        }

        fbimw = FBISearch(headless=HEADLESS)
        result = fbimw._search_most_wanted("Ruja", "Ignatova")
        del fbimw
        assert result == expected_result

    def test_fbi_fugitives(self):
        expected_results = {
            "risk": "Dangerous",
            "notices": {
                "fbi-most-wanted": {
                    "id": "violentcrimes-murders",
                    "charges": [
                        "Unlawful flight to avoid prosecution - murder, attempted murder"
                    ],
                }
            },
        }

        fbif = FBISearch(headless=HEADLESS)
        results = fbif._search_fugitives("Robert", "Morales")
        del fbif
        assert results == expected_results

    def test_fbi_terrorists(self):
        expected_results = {
            "risk": "Dangerous",
            "notices": {
                "fbi-most-wanted": {
                    "id": "seekinginformation-terrorism",
                    "charges": [""],
                }
            },
        }

        fbit = FBISearch(headless=HEADLESS)
        results = fbit._search_terrorists("Issa", "Barrey")
        del fbit
        assert results == expected_results

    def test_interpol_red_notice(self):
        expected_results = {
            "risk": "Dangerous",
            "notices": {
                "interpol-red-notice": {
                    "id": "2024/47665",
                    "charges": [
                        "Participation in activities of a terrorist organization",
                        "Participation in activities of an illegal armed formation.",
                    ],
                }
            },
        }

        interpol = InterpolSearch(headless=HEADLESS)
        res = interpol._search_red_notices("Fatima", "Kotieva")
        del interpol
        assert res == expected_results

    def test_interpol_un_notice(self):
        expected = {
            "risk": "Dangerous",
            "notices": {
                "interpol-un-notice": {
                    "id": "2024/11227",
                    "charges": ["No charges available"],
                }
            },
        }

        interpol = InterpolSearch(headless=HEADLESS)
        res = interpol._search_un_notices("Renel", "Destina")
        del interpol
        assert res == expected

    def test_europol_most_wanted(self):
        expected = {'notices': {
            'europol-most-wanted': {'charges': ['Sexual exploitation of children and child pornography'], 'id': ''}},
            'risk': 'High'}

        europol = EuropolSearch(headless=HEADLESS)
        res = europol.search("Daniel", "Portka")
        del europol
        assert res == expected

    def test_nca_most_wanted(self):
        expected = {
            "risk": "Dangerous",
            "notices": {
                "nca-most-wanted": {
                    "id": "",
                    "charges": [
                        "wanted in connection with conspiracy to supply diamorphine"
                    ],
                }
            },
        }

        nca = NCASearch(headless=HEADLESS)
        res = nca.search("Osman", "Aydeniz")
        del nca
        assert res == expected

    def test_guardia_civil_most_wanted(self):
        expected = {
            "risk": "Dangerous",
            "notices": {"guardiacivil-most-wanted": {"id": "", "charges": ["Unknown"]}},
        }

        gc = GuardiaCivilSearch()
        res = gc.search("Bozivoj", "Kosmakovy")
        del gc
        assert res == expected

    def test_policia_nacional_most_wanted(self):
        expected = {'notices': {'policianacional-most-wanted': {
            'charges': ['Delito contra la salud pública', 'Delito de tenencia ilícita de arma',
                        'Delito de blanqueo de capitales'], 'id': ''}}, 'risk': 'Dangerous'}

        pn = PoliciaNacionalSearch()
        res = pn.search("Julio", "Herrera Nieto")
        del pn
        assert res == expected

    def test_cib_most_wanted(self):
        expected = {
            "risk": "Medium",
            "notices": {
                "cib-most-wanted": {
                    "id": "782819984953864192",
                    "charges": [
                        "Violation of the narcotics endangerment prevention act"
                    ],
                }
            },
        }

        cib = CIBSearch()
        res = cib.search("Hungtien", "Lee")
        del cib
        assert res == expected

    def test_secret_service_without_reward(self):
        expected = {'notices': {'us-secret-service': {'charges': [
            'From at least May 2007 through July 2017, Aleksey Timofeyevich Stroganov was allegedly part of a criminal conspiracy to hack into the computer networks of individuals and companies and steal, among other things, debit and credit card numbers and personal identifying information associated with the cardholders.',
            'Stroganov and his co-conspirators harvested data associated with hundreds of millions credit card and banking accounts. To profit from the scheme, Stroganov oversaw a network of re-sellers and vendors who Stroganov provided with access to databases containing personal identifying information and payment card data for hundreds of thousands of accounts. The vendors then sold that data over the dark net through cybercrime forums and dark net websites. In total, the scheme resulted in losses to financial institutions exceeding $35 million.',
            'Stroganov is charged with one count of conspiracy to commit wire fraud affecting a financial institution, three counts of wire fraud, three counts of bank fraud, and three counts of aggravated identity theft.',
            'The prosecution is being handled by the U.S. Attorney’s Office for the District of New Jersey and the U.S. Department of Justice Criminal Division’s Computer Crime and Intellectual Property Section (CCIPS).'],
            'id': ''}}, 'risk': 'High'}

        ss = SecretServiceSearch()
        res = ss.search("Aleksey", "Timofeyevich Stroganov")
        del ss
        assert res == expected

    def test_secret_service_with_reward(self):
        expected = {'notices': {'us-secret-service': {'charges': [
            'The indictment in this matter alleges that, beginning on or about February 2016 through on or about March 2017, Artem Viacheslavovich Radchenko recruited Oleksandr Vitalyevich Ieremenko and other hackers in Ukraine and managed their criminal efforts to enrich themselves through a sophisticated securities fraud scheme. Ieremenko successfully hacked into the computer networks of the U.S. Securities and Exchange Commission (SEC) and extracted valuable data regarding the financial earnings of publicly traded companies.',
            'Radchenko and Ieremenko’s scheme focused on stealing annual, quarterly, and current reports of publicly traded companies before the reports were disseminated. Many of the stolen reports contained material non-public information concerning, among other things, the earnings of the companies. Radchenko and Ieremenko sought to profit illegally from the scheme by selling access to the non-public information contained in these “yet-to-be” disclosed reports and by trading in the securities of the companies before the investing public learned the same information.',
            'On January 15, 2019, a federal grand jury in the District of New Jersey charged Radchenko and Ieremenko with securities fraud conspiracy, wire fraud, wire fraud conspiracy, computer fraud and computer fraud conspiracy.',
            'The prosecution is being handled by the U.S. Department of Justice Criminal Division’s Computer Crime and Intellectual Property Section and the U.S. Attorney’s Office in New Jersey. The U.S. Department of State is offering a reward of up to $1 million for information leading to the arrest and/or conviction of Radchenko and Ieremenko for participating in transnational organized crime.'],
            'id': ''}}, 'risk': 'Dangerous'}

        ss = SecretServiceSearch()
        res = ss.search("Artem", "Viacheslavovich Radchenko")
        del ss
        assert res == expected

    def test_new_south_wales_police_most_wanted(self):
        expeted = {
            "risk": "High",
            "notices": {
                "newsouthwales-most-wanted": {
                    "id": "",
                    "charges": [
                        "In relation to the 1999 bashing murder of a man at Erskine Park."
                    ],
                }
            },
        }

        try:
            sw = NewSouthWalesPoliceSearch()
            res = sw.search("Brady", "Hamilton")
            del sw
        except BaseSearch.CaptchaError:
            pytest.skip("Captcha triggered")
        assert res == expeted

    def test_ofac_search(self):
        expected_result = {
            "risk": "High",
            "notices": {
                "ofac-sanctions": {
                    "id": "UKRAINE-EO13660",
                    "charges": [
                        "Ukraine-/Russia-Related Sanctions Regulations, 31 CFR 589.201 and/or 589.209"
                    ],
                }
            },
        }

        ofac = OFACSearch(headless=True)
        result = ofac.search("Peter", "Savchenko")  # Exact name from OFAC
        del ofac
        assert result == expected_result

    def test_ofsi_search(self):
        exp_res = {'notices': {'ofsi-sanctions': {'charges': [
            ' Petr Olegovich Aven (hereinafter AVEN) is an involved person under the Russia (Sanctions) (EU Exit) Regulations 2019 on the basis of the following grounds:\u202f(1) AVEN is or has been involved in obtaining a benefit from or supporting the Government of Russia by working as a director or equivalent at Alfa Group Consortium, an entity carrying on business in a sector of strategic significance, namely the Russian financial services sector; (2) AVEN has been involved in obtaining a benefit from or supporting the Government of Russia by working as a director or equivalent at ABH Holding, an entity carrying on business in a sector of strategic significance to the Government of Russia, namely the Russian financial services sector; (3) AVEN has been involved in obtaining a benefit from or supporting the Government of Russia by working as a director or equivalent at Alfa-Bank (Russia), an entity carrying on business in a sector of strategic significance to the Government of Russia, namely the Russian financial services sector; (4) AVEN is or has been involved in destabilising Ukraine or undermining or threatening the territorial integrity, sovereignty, or independence of Ukraine by working as a director at AlfaStrakhovanie, an entity which provides financial services to a person that could contribute to destabilising Ukraine or undermining or threatening the territorial integrity, sovereignty, or independence of Ukraine; (5) AVEN is associated with a person who is or has been so involved, namely Mikhail FRIDMAN.  '],
            'id': 'RUS0665'}}, 'risk': 'High'}

        assert OFSISearch().search("Aven", "Pyotr") == exp_res

    def test_opensanctions_search(self):
        try:
            exp_res = {
                "risk": "Dangerous",
                "notices": {
                    "opensanctions": {
                        "id": "",
                        "charges": [
                            "https://www.opensanctions.org/entities/NK-LviGFkkKTKFcCqg98PUKsa/"
                        ],
                    }
                },
            }
            res = OpenSanctionsSearch().search("Mikhail", "Pavlovich Matveev")
        except BaseSearch.CaptchaError:
            pytest.skip("Captcha triggered")
        assert res == exp_res

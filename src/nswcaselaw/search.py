from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup

from nswcaselaw.constants import CASELAW_SEARCH_URL, COURTS

TEXT_FIELDS = [
    "body",
    "title",
    "before",
    "catchwords",
    "party",
    "mnc",
    "startDate",
    "endDate",
    "fileNumber",
    "legislationCited",
    "casesCited",
]


class CaseLawException(Exception):
    pass


class Search:
    """
    Class representing a CaseLaw query. Intialise it with a dictionary
    of search parameters.
    """

    def __init__(self, query_args: Dict[str, str]):
        self._search = query_args
        self._params = None

    @property
    def search(self) -> Dict[str, str]:
        return self._search

    def build_query(self):
        self._params = [(field, self._search.get(field, "")) for field in TEXT_FIELDS]
        self._params.extend(self.courts_query("courts", self._search["courts"]))
        self._params.extend(self.courts_query("tribunals", self._search["courts"]))

    def courts_query(self, court_type: str, indices: List[int]) -> List[Tuple[str]]:
        params = []
        for court in COURTS[court_type]:
            if court[0] in indices:
                params.append((court_type, court[0]))
            params.append(("_" + court_type, "on"))
        return params

    def results(self):
        self.build_query()
        print(self._params)
        r = requests.get(CASELAW_SEARCH_URL, self._params)
        if r.status_code == 200:
            results = self.scrape_results(r)
            for result in results:
                yield result
        else:
            raise CaseLawException(f"Bad status_code {r.status_code}")
        # request next page, if appropriate, after a wait

    def scrape_results(self, r: requests.Response) -> List[str]:
        soup = BeautifulSoup(r.text, "html.parser")
        decisions = [a for a in soup.find_all("a") if a["href"][:9] == "/decision"]
        return decisions

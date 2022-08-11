import logging
import re
import time
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup

from nswcaselaw.constants import CASELAW_SEARCH_URL, COURTS

_logger = logging.getLogger(__name__)


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

RESULTS_RE = re.compile(r"Displaying \d+ - \d+ of (\d+)")
PAGE_SIZE = 20

PAUSE_SECONDS = 20


class CaseLawException(Exception):
    pass


class Decision:
    def __init__(self, **kwargs):
        self._title = kwargs.get("title")
        self._before = kwargs.get("before")
        self._date = kwargs.get("date")
        self._catchwords = kwargs.get("catchwords")
        self._uri = kwargs.get("uri")

    def __repr__(self):
        """
        Returns the decision fields which are available from the search
        results page as a comma-separated list in quotes.
        """
        return ",".join(
            [
                f'"{p}"'
                for p in [
                    self._title,
                    self._uri,
                    self._date,
                    self._before,
                    self._catchwords,
                ]
            ]
        )

    @property
    def title(self):
        return self._title

    @property
    def before(self):
        return self._before

    @property
    def date(self):
        return self._date

    @property
    def catchwords(self):
        return self._catchwords

    @property
    def link(self):
        return self._uri

    def fetch(self):
        """
        Load and scrape the body of this decision
        """
        # todo
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
        self._params = [("page", "")]  # initial query has no page
        self._params.extend(
            [(field, self._search.get(field, "")) for field in TEXT_FIELDS]
        )
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
        """
        Pages through search results until we've finished, pausing for PAUSE_SECONDS
        before the next request.
        """
        self.build_query()
        _logger.info("Fetching page 1...")
        r = requests.get(CASELAW_SEARCH_URL, self._params)
        if r.status_code == 200:
            n_results, results = self.scrape_results(r.text)
            for result in results:
                yield result
        n_pages = (n_results - 1) // PAGE_SIZE + 1
        for page in range(1, n_pages):
            time.sleep(PAUSE_SECONDS)
            self._params[0] = ("page", str(page))
            _logger.info(f"Fetching page {page + 1} of {n_pages}...")
            r = requests.get(CASELAW_SEARCH_URL, self._params)
            if r.status_code == 200:
                n, results = self.scrape_results(r.text)
                for result in results:
                    yield result
            else:
                raise CaseLawException(f"Bad status_code {r.status_code}")

    def scrape_results(self, html) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        header_strings = list(soup.find("h1").stripped_strings)
        m = RESULTS_RE.match(header_strings[1])
        if not m:
            raise CaseLawException("Couldn't get number of results from HTML")
        n_results = int(m[1])
        results = soup.find_all("div", {"class": "row result"})
        decisions = [self.scrape_decision(r) for r in results]
        return n_results, decisions

    def scrape_decision(self, row):
        try:
            header = row.find("h4")
            link = header.find("a")
            uri = link["href"]
            title = "".join(link.stripped_strings)
            before = ""
            date = ""
            catchwords = ""
            divs = [d for d in header.next_siblings if d.name == "div"]
            if divs:
                cps = divs[0].find_all("p")
                if len(cps) > 1:
                    catchwords = "".join(cps[1].stripped_strings)
            ul = row.find("ul")
            if ul:
                values = ul.find_all("li", {"class": "list-group-item"})
                if len(values) >= 2:
                    before = "".join(values[1].stripped_strings)
                if len(values) >= 4:
                    date = "".join(values[3].stripped_strings)
            return Decision(
                title=title,
                uri=uri,
                catchwords=catchwords,
                before=before,
                date=date,
            )
        except Exception as e:
            _logger.warn(f"HTML parse error {e}")
            return None

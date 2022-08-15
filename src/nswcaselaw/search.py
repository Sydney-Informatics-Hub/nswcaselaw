import logging
import re
import time
from typing import Generator, List, Tuple

import requests
from bs4 import BeautifulSoup

from nswcaselaw.constants import CASELAW_SEARCH_URL, COURTS, index_to_court
from nswcaselaw.decision import Decision

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

COURTS_FIELDS = ["courts", "tribunals"]

RESULTS_RE = re.compile(r"Displaying \d+ - \d+ of (\d+)")
PAGE_SIZE = 20

SEARCH_PAUSE_SECONDS = 5


class CaseLawException(Exception):
    pass


class Search:
    """
    Class representing a CaseLaw query.

    Keyword args:
        body (str)
        title (str)
        before (str) - name of judge etc
        catchwords (str)
        party (str)
        mnc (str) - citation
        startDate (str) - start date as "dd/mm/yyyy"
        endDate (str) - end date as "dd/mm/yyyy"
        fileNumber (str)
        legislationCited (str)
        casesCited (str)
        courts (list of int) - indices starting at 1 from court list
        tribunals (list of int) - indices starting at 1 from tribunals list

    """

    def __init__(self, **kwargs):
        self._query = {}
        for field in TEXT_FIELDS + COURTS_FIELDS:
            self._query[field] = kwargs.get(field)
        self._params = None

    @property
    def params(self):
        return self._params

    def build_query(self):
        """
        Converts the dict of search params into a list of tuples which can
        be passed through requests. The reason for this is to imitate the
        courts/tribunals selector
        """
        self._params = [("page", "")]  # initial query has no page
        self._params.extend(
            [(field, self._query.get(field, "")) for field in TEXT_FIELDS]
        )
        for field in COURTS_FIELDS:
            self._params.extend(self.courts_query(field, self._query[field]))

    def courts_query(self, court_type: str, indices: List[int]) -> List[Tuple[str]]:
        """
        Generates a list of court or tribunal params with the ones the
        user has selected switched on.
        """
        params = []
        if indices is not None:
            ids = [index_to_court(court_type, idx)[0] for idx in indices]
        else:
            ids = []
        for court in COURTS[court_type]:
            if court[0] in ids:
                params.append((court_type, court[0]))
            params.append(("_" + court_type, "on"))
        return params

    def query(self) -> Generator[Decision, None, None]:
        """
        Runs a query against CaseLaw, repeating it for as many pages as are
        needed to get all of the matching results. Pauses between pages so that
        we don't get banned.
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
            time.sleep(SEARCH_PAUSE_SECONDS)
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
        if len(header_strings) < 2:
            raise CaseLawException("Couldn't get results element from HTML")
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

import logging
import time

import requests
from bs4 import BeautifulSoup

from nswcaselaw.constants import CASELAW_BASE_URL

FETCH_PAUSE_SECONDS = 5

_logger = logging.getLogger(__name__)


class Decision:
    """
    Class representing a Decision in CaseLaw. These are returned by the
    Search object with the metadata which is given in the results page.
    The rest of the object's data can be retrieved with the Decision's
    fetch method.
    """

    def __init__(self, **kwargs):
        self._values = {}
        self._title = kwargs.get("title")
        self._before = kwargs.get("before")
        self._date = kwargs.get("date")
        self._catchwords = kwargs.get("catchwords")
        self._uri = kwargs.get("uri")
        self._mnc = ""
        self._hearingDates = ""
        self._dateOfOrders = ""
        self._decisionDate = ""
        self._jurisdiction = ""
        self._decision = ""
        self._legislationCited = ""
        self._casesCited = ""
        self._parties = ""
        self._category = ""
        self._fileNumber = ""
        self._representation = ""
        self._judgment = ""
        self._csv = None
        self._dict = None

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

    @property
    def id(self):
        """The unique identifier in the decision URI"""
        if self._uri:
            parts = self._uri.split("/")
            return parts[-1]
        else:
            return None

    @property
    def values(self):
        return self._values

    @property
    def html(self):
        return self._html

    @property
    def csv(self):
        if self._csv is None:
            self._csv = ",".join(
                [
                    f'"{p}"'
                    for p in [
                        self._title,
                        self._uri,
                        self._date,
                        self._mnc,
                        self._before,
                        self._catchwords,
                        self._hearingDates,
                        self._dateOfOrders,
                        self._decisionDate,
                        self._jurisdiction,
                        self._decision,
                        self._legislationCited,
                        self._casesCited,
                        self._parties,
                        self._category,
                        self._fileNumber,
                        self._representation,
                    ]
                ]
            )
            self._csv = self._csv.replace("\n", " ")
        return self._csv

    @property
    def dict(self):
        if self._dict is None:
            self._dict = {
                "title": self._title,
                "uri": self._uri,
                "date": self._date,
                "mnc": self._mnc,
                "before": self._before,
                "catchwords": self._catchwords,
                "hearingDates": self._hearingDates,
                "dateOfOrders": self._dateOfOrders,
                "decisionDate": self._decisionDate,
                "jurisdiction": self._jurisdiction,
                "decision": self._decision,
                "legislationCited": self._legislationCited,
                "casesCited": self._casesCited,
                "parties": self._parties,
                "category": self._category,
                "fileNumber": self._fileNumber,
                "representation": self._representation,
                "judgment": self._judgment,
            }
        return self._dict

    def fetch(self):
        """
        Load and scrape the body of this decision
        """
        r = requests.get(CASELAW_BASE_URL + self._uri)
        if r.status_code == 200:
            self._html = r.text
            self.scrape(self._html)
        time.sleep(FETCH_PAUSE_SECONDS)

    def elt_text(self, elt):
        return "\n".join(elt.stripped_strings)

    def _find_value(self, pattern):
        matches = [f for f in self._values.keys() if pattern in f]
        if not matches:
            self._warning(f"{pattern} not found")
            return ""
        if len(matches) > 1:
            self._warning(f"Multiple matchs for {pattern}")
        return self._values[matches[0]]

    def _warning(self, message):
        """
        Emits a warning with this decisions URI and title prepended
        """
        _logger.warning(f"[{self._uri} {self._title}] {message}")

    # NOTE I have only done these for Supreme Court judgments. Are there other
    # formats?
    # TODO: these should be Classes

    def scrape(self, html):
        soup = BeautifulSoup(html, "html.parser")
        if self._title is None:
            self._scrape_title(soup)
        try:
            if self._new_style_scrape(soup):
                return True
            if self._old_style_scrape(soup):
                return True
        except Exception as e:
            self._warning(f"Scrape failed: {e}")
            return False

    def _scrape_title(self, soup):
        title = soup.find("title")
        if title:
            title_text = " ".join(title.stripped_strings)
            title_text = title_text.split("-")[0]
            self._title = title_text.strip()
        else:
            self._warning("No title tag")

    def _new_style_scrape(self, soup):
        dts = soup.find_all("dt")
        if not dts:
            return False
        for dt in dts:
            dd = dt.find_next_sibling("dd")
            field = dt.string
            paras = dd.find_all("p")
            if paras:
                self._values[field] = [self.elt_text(p) for p in paras]
            else:
                self._values[field] = self.elt_text(dd)
        self._mnc = self._find_value("Medium Neutral Citation")
        self._hearingDates = self._find_value("Hearing dates")
        self._dateOfOrders = self._find_value("Date of orders")
        self._decisionDate = self._find_value("Decision date")
        self._jurisdiction = self._find_value("Jurisdiction")
        self._before = self._find_value("Before")
        # Decision matches with a ":" to disambiguate from "Decision date"
        self._decision = self._find_value("Decision:")[0]
        self._catchwords = self._new_catchwords(self._find_value("Catchwords"))
        self._legislationCited = self._fix_whitespace(
            self._find_value("Legislation Cited")
        )
        self._casesCited = self._fix_whitespace(self._find_value("Cases Cited"))
        self._parties = self._find_value("Parties").split("\n")
        self._category = self._find_value("Category")
        self._fileNumber = self._find_value("File Number")
        self._representation = self._find_value("Representation").split("\n")
        judgment = soup.find("div", _class="body")
        if judgment:
            self._judgment = str(judgment)  # leaving as HTML for now
        return True

    def _fix_whitespace(self, values):
        return [v.replace("\n", " ") for v in values]

    def _new_catchwords(self, catchwords):
        if catchwords is None or not catchwords:
            return []
        return [cw.strip() for cw in catchwords[0].split("\u2014")]

    def _old_style_scrape(self, soup):
        rows = soup.find_all("tr")
        if not rows:
            return False
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                field = self.elt_text(cells[1])
                self._values[field] = self.elt_text(cells[2])
            else:
                j = self._looks_like_judgment(cells)
                if j:
                    self._judgment = j
        self._mnc = self._find_value("CITATION")
        self._hearingDates = self._find_value("HEARING DATE")
        self._dateOfOrders = self._find_value("DATE OF ORDERS")
        self._decisionDate = self._find_value("JUDGMENT DATE")
        self._jurisdiction = self._find_value("JURISDICTION")
        self._category = self._find_value("CATEGORY")
        self._before = self._find_value("JUDGMENT OF")
        self._decision = self._find_value("DECISION")
        self._catchwords = self._old_catchwords(self._find_value("CATCHWORDS"))
        self._legislationCited = self._find_value("LEGISLATION CITED").split("\n")
        self._casesCited = self._find_value("CASES CITED").split("\n")
        self._parties = self._find_value("PARTIES").split("\n")
        self._fileNumber = self._find_value("FILE NUMBER")
        counsel = self._find_value("COUNSEL").split("\n")
        solicitors = self._find_value("SOLICITORS").split("\n")
        if counsel is not None:
            self._representation = counsel
        if solicitors is not None:
            self._representation += solicitors
        # fixme: the judgment!!
        return True

    def _old_catchwords(self, catchwords):
        if catchwords is None:
            return []
        return [cw.strip() for cw in catchwords.split("-")]

    def _looks_like_judgment(self, cells):
        if len(cells) != 2:
            return None
        return cells[1]  # this is pretty dumb, assume a judgment table is 2

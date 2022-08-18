import logging
import time

import requests
from bs4 import BeautifulSoup

from nswcaselaw.constants import CASELAW_BASE_URL

FETCH_PAUSE_SECONDS = 5

_logger = logging.getLogger(__name__)

CSV_FIELDS = [
    "title",
    "uri",
    "date",
    "mnc",
    "before",
    "catchwords",
    "hearingDates",
    "dateOfOrders",
    "decisionDate",
    "jurisdiction",
    "decision",
    "legislationCited",
    "casesCited",
    "parties",
    "category",
    "fileNumber",
    "representation",
]


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
        self._csv = None

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
        return self._values.ger("title")

    @property
    def before(self):
        return self._values.get("before")

    @property
    def date(self):
        return self._values.get("date")

    @property
    def catchwords(self):
        return self._values.get("catchwords")

    @property
    def link(self):
        return self._uri

    @property
    def hearingDates(self):
        return self._values.get("hearingDates")

    @property
    def dateOfOrders(self):
        return self._values.get("dateOfOrders")

    @property
    def decisionDate(self):
        return self._values.get("decisionDate")

    @property
    def jurisdiction(self):
        return self._values.get("jurisdiction")

    @property
    def decision(self):
        return self._values.get("decision")

    @property
    def legislationCited(self):
        return self._values.get("legislationCited")

    @property
    def casesCited(self):
        return self._values.get("casesCited")

    @property
    def parties(self):
        return self._values.get("parties")

    @property
    def category(self):
        return self._values.get("category")

    @property
    def fileNumber(self):
        return self._values.get("fileNumber")

    @property
    def representation(self):
        return self._values.get("representation")

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
    def csv(self):
        if self._csv is None:
            self._csv = ",".join([f'"{p}"' for p in CSV_FIELDS])
            self._csv = self._csv.replace("\n", " ")
        return self._csv

    def fetch(self):
        """
        Load and scrape the body of this decision
        """
        r = requests.get(CASELAW_BASE_URL + self._uri)
        if r.status_code == 200:
            self._html = r.text
            self.scrape(self._html)
        time.sleep(FETCH_PAUSE_SECONDS)

    def load_file(self, test_file):
        with open(test_file, "r") as fh:
            html = fh.read()
            return self.scrape(html)

    def _warning(self, message):
        """
        Emits a warning with this decisions URI and title prepended
        """
        _logger.warning(f"[{self._uri} {self._title}] {message}")

    def scrape(self, html):
        self._soup = BeautifulSoup(html, "html.parser")
        try:
            scraper = self._get_scraper()
            self._values = scraper.scrape()
            return True
        except Exception as e:
            self._warning(f"Scrape failed: {e}")
            return False

    def _get_scraper(self):
        """
        Determing which scraper to use, based on the soup. This should maybe
        be part of the Scraper class?
        """
        dts = self._soup.find_all("dt")
        if not dts:
            return OldScScraper(self)
        else:
            return NewScScraper(self)


class Scraper:
    """
    Superclass for scrapers - each scraper deals with a different HTML
    format from CaseLaw.
    """

    def __init__(self, decision):
        self._decision = decision
        self._soup = decision._soup
        self._raw = {}
        self._values = {}

    def _warning(self, message):
        self._decision._warning(message)

    def scrape(self):
        data = self._scrape_metadata()
        data["title"] = self._scrape_title()
        return data

    def _strings(self, elt):
        return "\n".join(elt.stripped_strings)

    def _fix_whitespace(self, values):
        return [v.replace("\n", " ") for v in values]

    def _find_value(self, pattern):
        matches = [f for f in self._raw.keys() if pattern in f]
        if not matches:
            self._warning(f"{pattern} not found")
            return ""
        if len(matches) > 1:
            self._warning(f"Multiple matches for {pattern}")
        return self._raw[matches[0]]

    def _scrape_title(self):
        title = self._soup.find("title")
        if title:
            title_text = " ".join(title.stripped_strings)
            title_text = title_text.split("-")[0]
            return title_text.strip()
        else:
            self._warning("No title tag")


class NewScScraper(Scraper):

    PATTERNS = {
        "mnc": "Medium Neutral Citation",
        "hearingDates": "Hearing dates",
        "dateOfOrders": "Date of orders",
        "decisionDate": "Decision date",
        "jurisdiction": "Jurisdiction",
        "before": "Before",
        "decision": "Decision:",
        "catchwords": "Catchwords",
        "legislationCited": "Legislation Cited",
        "casesCited": "Cases Cited",
        "parties": "Parties",
        "category": "Category",
        "fileNumber": "File Number",
        "representation": "Representation",
    }

    def _scrape_metadata(self):
        for dt in self._soup.find_all("dt"):
            dd = dt.find_next_sibling("dd")
            header = dt.string
            paras = dd.find_all("p")
            if paras:
                self._raw[header] = [self._strings(p) for p in paras]
            else:
                self._raw[header] = self._strings(dd)

        for field, pattern in self.PATTERNS.items():
            self._values[field] = self._find_value(pattern)

        self._values["decision"] = self._values["decision"][0]
        self._values["catchwords"] = self._catchwords(self._values["catchwords"])
        for f in ["legislationCited", "casesCited"]:
            self._values[f] = self._fix_whitespace(self._values[f])
        self._values["parties"] = self._values["parties"].split("\n")
        self._values["representation"] = self._values["representation"].split("\n")
        judgment = self._soup.find("div", _class="body")
        if judgment:
            self._values["judgment"] = str(judgment)  # leaving as HTML for now
        else:
            self._values["judgment"] = ""
        return self._values

    def _catchwords(self, catchwords):
        if catchwords is None or not catchwords:
            return []
        return [cw.strip() for cw in catchwords[0].split("\u2014")]


class OldScScraper(Scraper):

    PATTERNS = {
        "mnc": "CITATION",
        "hearingDates": "HEARING DATE",
        "dateOfOrders": "DATE OF ORDERS",
        "decisionDate": "JUDGMENT DATE",
        "jurisdiction": "JURISDICTION",
        "before": "JUDGMENT OF",
        "decision": "DECISION",
        "catchwords": "CATCHWORDS",
        "legislationCited": "LEGISLATION CITED",
        "casesCited": "CASES CITED",
        "parties": "PARTIES",
        "category": "CATEGORY",
        "fileNumber": "FILE NUMBER",
        "counsel": "COUNSEL",
        "solicitors": "SOLICITORS",
    }

    def _scrape_metadata(self):
        rows = self._soup.find_all("tr")
        if not rows:
            return {}
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                header = self._strings(cells[1])
                self._raw[header] = self._strings(cells[2])
            else:
                j = self._looks_like_judgment(cells)
                if j:
                    self._values["judgment"] = j

        for field, pattern in self.PATTERNS.items():
            self._values[field] = self._find_value(pattern)
        self._values["catchwords"] = self._catchwords(self._values["catchwords"])
        for f in ["legislationCited", "casesCited", "parties", "counsel", "solicitors"]:
            self._values[f] = self._values[f].split("\n")
        if self._values["counsel"] is not None:
            self._values["representation"] = self._values.pop("counsel")
        else:
            self._values["representation"] = []
        if self._values["solicitors"] is not None:
            self._values["representation"] += self._values.pop("solicitors")
        # fixme: the judgment!!
        return self._values

    def _catchwords(self, catchwords):
        if catchwords is None:
            return []
        return [cw.strip() for cw in catchwords.split("-")]

    def _looks_like_judgment(self, cells):
        if len(cells) != 2:
            return None
        return cells[1]  # this is pretty dumb, assume a judgment table is 2

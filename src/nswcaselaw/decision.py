import time

import requests
from bs4 import BeautifulSoup

from nswcaselaw.constants import CASELAW_BASE_URL

FETCH_PAUSE_SECONDS = 5


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

    # NOTE I have only done these for Supreme Court judgments. Are there other
    # formats?

    def scrape(self, html):
        soup = BeautifulSoup(html, "html.parser")
        if self._new_style_scrape(soup):
            return True
        if self._old_style_scrape(soup):
            return True
        return False

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
        self._mnc = self._values.get("Medium Neutral Citation:")
        self._hearingDates = self._values.get("Hearing dates:")
        self._dateOfOrders = self._values.get("Date of orders:")
        self._decisionDate = self._values.get("Decision date:")
        self._jurisdiction = self._values.get("Jurisdiction:")
        self._before = self._values.get("Before:")
        self._decision = self._values.get("Decision:")
        self._catchwords = self._values.get("Catchwords:")
        self._legislationCited = self._values.get("Legislation Cited:")
        self._casesCited = self._values.get("Legislation Cited:")
        self._parties = self._values.get("Parties:")
        self._category = self._values.get("Category:")
        self._fileNumber = self._values.get("File Number(s):")
        self._representation = self._values.get("Representation:")
        judgment = soup.find("div", _class="body")
        if judgment:
            self._judgment = str(judgment)  # leaving as HTML for now
        return True

    def _old_style_scrape(self, soup):
        rows = soup.find_all("tr")
        if not rows:
            return False
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                field = cells[1].string
                self._values[field] = self.elt_text(cells[2])
            else:
                j = self._looks_like_judgment(cells)
                if j:
                    self._judgment = j
        self._mnc = self._values.get("CITATION :")
        self._hearingDates = self._values.get("HEARING DATE(S) :")
        self._dateOfOrders = self._values.get("Date of orders:")
        self._decisionDate = self._values.get("JUDGMENT DATE :")
        self._jurisdiction = self._values.get("JURISDICTION :")
        self._before = self._values.get("JUDGMENT OF :")
        self._decision = self._values.get("DECISION :")
        self._catchwords = self._values.get("CATCHWORDS :")
        self._legislationCited = self._values.get("LEGISLATION CITED :")
        self._casesCited = self._values.get("CASES CITED :")
        self._parties = self._values.get("PARTIES :")
        self._fileNumber = self._values.get("FILE NUMBER(S) :")
        counsel = self._values.get("COUNSEL :")
        solicitors = self._values.get("SOLICITORS :")
        if counsel is not None:
            self._representation = counsel
        if solicitors is not None:
            self._representation += solicitors
        # fixme: the judgment!!
        return True

    def _looks_like_judgment(self, cells):
        if len(cells) != 2:
            return None
        return cells[1]  # this is pretty dumb, assume a judgment table is 2

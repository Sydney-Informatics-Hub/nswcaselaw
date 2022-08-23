"""Classes for working with individual judgments
"""


import logging
import re
import time
from typing import List

import requests
from bs4 import BeautifulSoup

from nswcaselaw.constants import CASELAW_BASE_URL

FETCH_PAUSE_SECONDS = 5

SCRAPER_WARNING = """
Warning: downloading full decisions has only been tested on the Supreme Court.
While results can be downloaded for other courts and tribunals, full decisions
are unlikely to work.
"""

_logger = logging.getLogger(__name__)

BASE_FIELDS = [
    "title",
    "uri",
    "before",
    "decisionDate",
    "catchwords",
]

CSV_FIELDS = [
    "title",
    "uri",
    "decisionDate",
    "mnc",
    "before",
    "catchwords",
    "hearingDates",
    "dateOfOrders",
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
        for field in BASE_FIELDS:
            self._values[field] = kwargs.get(field)
        self._csv = None

    @property
    def title(self):
        return self._values.get("title")

    @property
    def before(self):
        return self._values.get("before")

    @property
    def catchwords(self):
        return self._values.get("catchwords")

    @property
    def uri(self):
        return self._values.get("uri")

    @property
    def decisionDate(self):
        return self._values.get("decisionDate")

    @property
    def hearingDates(self):
        return self._values.get("hearingDates")

    @property
    def dateOfOrders(self):
        return self._values.get("dateOfOrders")

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
    def judgment(self):
        return self._values.get("judgment")

    @property
    def id(self):
        """Returns the unique identifier in the decision URI"""
        if self.uri:
            parts = self.uri.split("/")
            return parts[-1]
        else:
            raise ValueError("Called id when uri not set")

    @property
    def values(self):
        return self._values

    def __repr__(self):
        """Returns the decision fields which are available from the search
        results page as a comma-separated list in quotes.
        """
        return ",".join(
            [
                f'"{p}"'
                for p in [
                    self.title,
                    self.uri,
                    self.decisionDate,
                    self.before,
                    self.catchwords,
                ]
            ]
        )

    @property
    def csv(self):
        """Returns all of the decision's fields except for the judgment
        as a CSV-safe string with double-quotes escaped."""
        if self._csv is None:
            values = [self._csv_value(p) for p in CSV_FIELDS]
            self._csv = ",".join([f'"{v}"' for v in values])
            self._csv = self._csv.replace("\n", " ")
        return self._csv

    def _csv_value(self, field):
        v = self._values.get(field, "")
        if type(v) == list:
            v = "; ".join(v)
        v = v.replace('"', "'")
        return v

    def fetch(self):
        """Downloads the full decision from CaseLaw and scrapes it. Returns
        a dictionary of the scraped values.

        Returns:
          dict of str: str
        """
        r = requests.get(CASELAW_BASE_URL + self.uri)
        if r.status_code == 200:
            self._html = r.text
            return self.scrape(self._html)
        time.sleep(FETCH_PAUSE_SECONDS)

    def load_file(self, test_file):
        """Load an HTML file and scrape the contents

        Args:
          test_file (str): the file to load
        Returns:
          Dict of (str: str): the scraped values
        """
        with open(test_file, "r") as fh:
            html = fh.read()
            return self.scrape(html)

    def _warning(self, message):
        """Logs a warning, adding this decision's uri and title"""
        _logger.warning(f"[{self.uri} {self.title}] {message}")

    def scrape(self, html):
        """Scrape an HTML decision, populating this object's _values dict
        and returning the values as a dict.

        Args:
          html (str): the HTML
        Returns:
          Dict of (str: str): the scraped values
        """
        self._soup = BeautifulSoup(html, "html.parser")
        try:
            scraper = self._get_scraper()
            self._warning(f"Scraping with {scraper}")
            scraped_values = scraper.scrape()
            for k, v in scraped_values.items():
                self._values[k] = v
            return self._values
        except Exception as e:
            self._warning(f"Scrape failed: {e}")
            return False

    def _get_scraper(self):
        """Using features from the parsed HTML, deduce which Scraper subclass
        should be used, instantiate it and return it

        Returns:
          :obj:`nswcaselaw.decision.Scraper`: A Scraper
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
        """Issue a warning via the Scraper's parent Decision so that it gets
        identified with the decision uri and title"""
        self._decision._warning(message)

    def scrape(self):
        """Top-level scrape method

        Returns:
          Dict(str: str): the values scraped from the HTML
        """
        data = self._scrape_metadata()
        data["title"] = self._scrape_title()
        data["uri"] = self._scrape_uri()
        return data

    def _strings(self, elt):
        """Utility to get the text content of an element"""
        return "\n".join(elt.stripped_strings)

    def _fix_whitespace(self, values: List[str]):
        """Replaces all newlines in an array of values with spaces

        Args:
          values (List(str)) - list of strings

        Returns:
          List(str)
        """
        return [v.replace("\n", " ") for v in values]

    def _find_value(self, substring):
        """Look for a substring in the keys of the _raw dict, which are values
        the scraper has got from whatever tabular representation is in its
        version of the HTML. Warns if there is no matching value, or if there
        is more than one.

        Args:
          substring (str): a string to search for in the _raw keys

        Returns:
          str: the first value which matches, or an empty string
        """
        matches = [f for f in self._raw.keys() if substring in f]
        if not matches:
            self._warning(f"{substring} not found")
            return ""
        if len(matches) > 1:
            self._warning(f"Multiple matches for {substring}")
        return self._raw[matches[0]]

    def _scrape_title(self):
        """Gets the case title from the <title> tag."""
        title = self._soup.find("title")
        if title:
            title_text = " ".join(title.stripped_strings)
            title_text = title_text.split("-")[0]
            return title_text.strip()
        else:
            self._warning("No title tag")

    def _scrape_uri(self):
        """Deduce the URI from the HTML for those cases (tests) where we didn't\
        already download it from the URI
        """
        if self._decision.uri:
            return self._decision.uri
        links = self._soup.find_all("a")
        dl_links = [a for a in links if a.get("href", "")[:9] == "/decision"]
        if dl_links:
            href = dl_links[0]["href"].split("/")
            return "/".join(href[:3])


class NewScScraper(Scraper):
    """Scraper for more recent Supreme Court judgments, which use a <dt> <dd>
    list for the metadata"""

    SUBSTRINGS = {
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
        """Scrape the core metadata from the soup object"""
        for dt in self._soup.find_all("dt"):
            dd = dt.find_next_sibling("dd")
            header = dt.string
            paras = dd.find_all("p")
            if paras:
                self._raw[header] = [self._strings(p) for p in paras]
            else:
                self._raw[header] = self._strings(dd)

        for field, substring in self.SUBSTRINGS.items():
            self._values[field] = self._find_value(substring)

        # some new-style decisions don't wrap catchwords, legslation or
        # cases in <p> tags - split these on newlines

        for f in ["catchwords", "legislationCited", "casesCited"]:
            self._values[f] = self._ensure_list(self._values[f])

        self._values["decision"] = self._values["decision"][0]
        self._values["catchwords"] = self._catchwords(self._values["catchwords"])
        for f in ["legislationCited", "casesCited"]:
            self._values[f] = self._fix_whitespace(self._values[f])

        self._values["parties"] = self._values["parties"].split("\n")
        self._values["representation"] = self._values["representation"].split("\n")
        self._values["judgment"] = self._scrape_judgment()
        return self._values

    def _ensure_list(self, value):
        """Some catchwords and lists of legislation and cases cited are not
        delimited by <p> tags, but are separated by newlines. This method
        normalises them into lists of strings.
        """
        if type(value) == list:
            return value
        else:
            return value.split("\n")

    def _catchwords(self, catchwords):
        """Normalise catchwords and split them on dashes or hyphens"""
        if catchwords is None or not catchwords:
            return []
        return [cw.strip() for cw in re.split("[\u2014-]", catchwords[0])]

    def _scrape_judgment(self):
        """Parse the body of the judgment into a list of paragraphs"""
        body = self._soup.find("div", {"class": "body"})
        if not body:
            self._warning("Couldn't find <div> with judgment")
            return []
        paragraphs = []
        for child in body.children:
            if child.name == "h2":
                paragraphs.append("##" + self._strings(child))
            elif child.name == "ol":
                n = int(child["start"])
                for li in child.find_all("li"):
                    paragraphs.append(str(n) + " " + self._strings(li))
                    n += 1
            elif child.name == "p":
                if not self._ignored_paras(child):
                    text = self._strings(child)
                    if text:
                        paragraphs.append(text)
        return paragraphs

    def _ignored_paras(self, p):
        """Test for old-style judgment paragraphs which we want to ignore"""
        if "class" in p.attrs:
            if "disclaimer" in p["class"] or "lastupdate" in p["class"]:
                return True
        stars = re.compile(r"\*+")
        if stars.match(self._strings(p)):
            return True
        return False


class OldScScraper(Scraper):
    """Scraper for more recent Supreme Court judgments, which use a <dt> <dd>
    list for the metadata"""

    SUBSTRINGS = {
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
        """Scrape the core metadata from the soup object"""
        rows = self._soup.find_all("tr")
        if not rows:
            return {}
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                header = self._strings(cells[1])
                self._raw[header] = self._strings(cells[2])

        for field, substring in self.SUBSTRINGS.items():
            self._values[field] = self._find_value(substring)
        self._values["catchwords"] = self._catchwords(self._values["catchwords"])
        for f in ["legislationCited", "casesCited", "parties", "counsel", "solicitors"]:
            self._values[f] = self._values[f].split("\n")
        if self._values["counsel"] is not None:
            self._values["representation"] = self._values.pop("counsel")
        else:
            self._values["representation"] = []
        if self._values["solicitors"] is not None:
            self._values["representation"] += self._values.pop("solicitors")
        self._values["judgment"] = self._scrape_judgment()
        return self._values

    def _catchwords(self, catchwords):
        """Normalise catchwords and split them on dashes or hyphens"""
        if catchwords is None:
            return []
        return [cw.strip() for cw in catchwords.split("-")]

    def _scrape_judgment(self):
        """Parse the body of the judgment into a list of paragraphs"""
        paragraphs = []
        for tr in self._soup.find_all("tr"):
            for td in tr.find_all("td"):
                uls = td.find_all("ul")
                if uls:
                    for child in td.children:
                        if child.name == "ul":
                            # some uls contain text: these are indented passages
                            ul_content = "\n".join(child.stripped_strings).strip()
                            if ul_content and paragraphs:
                                paragraphs[-1].append(ul_content)
                            paragraphs.append([])
                        else:
                            if paragraphs:
                                section = child.text
                                if section.strip():
                                    paragraphs[-1].append(section)
        paragraphs = [" ".join(p) for p in paragraphs]
        paragraphs = [p for p in paragraphs if p.strip()]
        return paragraphs

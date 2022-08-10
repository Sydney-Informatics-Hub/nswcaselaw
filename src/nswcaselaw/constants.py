from typing import Dict

import requests
from bs4 import BeautifulSoup

from nswcaselaw.nswcaselaw import CASELAW_SEARCH_URL

__author__ = "Mike Lynch"
__copyright__ = "The University of Sydney"
__license__ = "MIT"


def get_courts_and_tribunals() -> Dict[str, str]:
    """
    Returns a dict of court IDs to court names from the advanced search
    page of CaseLaw
    """
    r = requests.get(CASELAW_SEARCH_URL)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        bodies = {}
        for body_type in ["courts", "tribunals"]:
            bodies[body_type] = {}
            for control in soup.find_all("input", {"name": body_type}):
                body_id = control.get("value")
                body_name = list(control.parent.stripped_strings)[0]
                bodies[body_type][body_id] = body_name
        return bodies
    return None

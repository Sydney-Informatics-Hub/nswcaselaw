from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup

CASELAW_SEARCH_URL = "https://www.caselaw.nsw.gov.au/search/advanced"

# I'm keeping two lists for courts and tribunals, even though their ids
# don't overlap now - the search API separates them, so in theory they
# could change and start to overlap

COURTS = {
    "courts": [
        ("54a634063004de94513d827a", "Children's Court"),
        ("54a634063004de94513d827b", "Compensation Court"),
        ("54a634063004de94513d8278", "Court of Appeal"),
        ("54a634063004de94513d8279", "Court of Criminal Appeal"),
        ("54a634063004de94513d827c", "District Court"),
        ("54a634063004de94513d827d", "Drug Court"),
        ("54a634063004de94513d828e", "Industrial Court"),
        ("54a634063004de94513d8285", "Industrial Relations Commission (Commissioners)"),
        ("54a634063004de94513d827e", "Industrial Relations Commission (Judges)"),
        ("54a634063004de94513d827f", "Land and Environment Court (Commissioners)"),
        ("54a634063004de94513d8286", "Land and Environment Court (Judges)"),
        ("54a634063004de94513d8280", "Local Court"),
        ("54a634063004de94513d8281", "Supreme Court"),
    ],
    "tribunals": [
        (
            "54a634063004de94513d8282",
            "Administrative Decisions Tribunal (Appeal Panel)",
        ),
        ("54a634063004de94513d8287", "Administrative Decisions Tribunal (Divisions)"),
        (
            "54a634063004de94513d8289",
            (
                "Civil and Administrative Tribunal "
                "(Administrative and Equal Opportunity Division)"
            ),
        ),
        (
            "54a634063004de94513d828d",
            "Civil and Administrative Tribunal (Appeal Panel)",
        ),
        (
            "54a634063004de94513d828b",
            "Civil and Administrative Tribunal (Consumer and Commercial Division)",
        ),
        ("173b71a8beab2951cc1fab8d", "Civil and Administrative Tribunal (Enforcement)"),
        (
            "54a634063004de94513d828c",
            "Civil and Administrative Tribunal (Guardianship Division)",
        ),
        (
            "54a634063004de94513d828a",
            "Civil and Administrative Tribunal (Occupational Division)",
        ),
        ("54a634063004de94513d8283", "Dust Diseases Tribunal"),
        ("1723173e41f6b6d63f2105d3", "Equal Opportunity Tribunal"),
        ("5e5c92e1e4b0c8604babc749", "Fair Trading Tribunal"),
        ("5e5c92c5e4b0c8604babc748", "Legal Services Tribunal"),
        ("54a634063004de94513d8284", "Medical Tribunal"),
        ("54a634063004de94513d8288", "Transport Appeal Boards"),
    ],
}


def fetch_courts() -> Dict[str, List[Tuple[str, str]]]:
    """
    Fetches the advanced search page of CaseLaw and builds the COURTS
    dict above with ids and names of courts and tribunals
    """
    r = requests.get(CASELAW_SEARCH_URL)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        courts = {}
        for court_type in ["courts", "tribunals"]:
            courts[court_type] = []
            for control in soup.find_all("input", {"name": court_type}):
                court_id = control.get("value")
                court_name = list(control.parent.stripped_strings)[0]
                courts[court_type].append((court_id, court_name))
        return courts
    return None


def index_to_court(court_type: str, court_idx: int) -> Tuple[str, str]:
    """
    Return the tuple for court or tribunal n, starting at 1
    """
    if court_type not in COURTS:
        raise ValueError("Unknown court type")
    if court_idx < 1 or court_idx > len(COURTS[court_type]):
        raise ValueError("Court index out of range")
    return COURTS[court_type][court_idx - 1]

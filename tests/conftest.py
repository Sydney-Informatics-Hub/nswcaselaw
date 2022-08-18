from pathlib import Path

import pytest


@pytest.fixture
def search_fixtures():
    fixtures_dir = Path("tests/fixtures")
    return {
        "html": fixtures_dir / "results.html",
        "csv": fixtures_dir / "results.csv",
        "n_results": 1284,
    }


@pytest.fixture
def scrape_fixtures():
    fixtures_dir = Path("tests/fixtures")
    return {
        "old": fixtures_dir / "scrape_old.html",
        "new": fixtures_dir / "scrape_new.html",
        "metadata": {
            "title": "Jarndyce v Jarndyce",
            "mnc": "Jarndyce v Jarndyce [1979] King's Bench 20232",
            "before": "Xasiuisf J",
            "catchwords": [
                "NONSENSE",
                "fake catchwords",
                "blague",
                "ballyhoo",
                "MORE STUFF",
                "and nonsense",
            ],
            "hearingDates": "23/9/76-24/9/79",
            "dateOfOrders": "3/10/79",
            "decisionDate": "10 October 1979",
            "jurisdiction": "Equity",
            "decision": "Whether the scraper passes tests or not",
            "legislationCited": [
                "Corporations Act 2001 (Cth)",
                "FooBar Act 2022 (NSW)",
            ],
            "casesCited": ["Re Foo", "Re Bar", "Re Quux"],
            "parties": ["Jarndyce Sr", "Jarndyce Jr"],
            "category": "Costs",
            "fileNumber": "SC\nasw0439e9f",
            "representation": [
                "J Law-Talking-Guy SC (Plaintiff)",
                "Mr Saul Goodman (Defendant)",
                "Law Firm 1 (Plaintiff)",
                "Law Firm 2 (Defendant)",
            ],
            "judgment": [
                "1 Paragraph 1 of judgment",
                "2 Paragraph 2 of judgment",
                "3 Paragraph 3 of judgment",
            ],
        },
    }

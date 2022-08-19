import logging

import pytest

from nswcaselaw.nswcaselaw import Decision

_logger = logging.getLogger(__name__)


def test_basic_fields(scrape_fixtures):
    md = scrape_fixtures["basic_metadata"]
    d = Decision(**md)
    assert d.title == md["title"]
    assert d.before == md["before"]
    assert d.date == md["date"]
    assert d.catchwords == md["catchwords"]
    assert d.uri == md["uri"]


@pytest.mark.parametrize("style", ["new", "old"])
def test_decision_scrape(scrape_fixtures, style):
    d = Decision()
    md = scrape_fixtures["metadata"]
    with open(scrape_fixtures[style], "r") as fh:
        html = fh.read()
        result = d.scrape(html)
        assert result
        assert d.values == md
        assert d.hearingDates == md["hearingDates"]
        assert d.dateOfOrders == md["dateOfOrders"]
        assert d.decisionDate == md["decisionDate"]
        assert d.jurisdiction == md["jurisdiction"]
        assert d.decision == md["decision"]
        assert d.legislationCited == md["legislationCited"]
        assert d.casesCited == md["casesCited"]
        assert d.parties == md["parties"]
        assert d.category == md["category"]
        assert d.fileNumber == md["fileNumber"]
        assert d.representation == md["representation"]
        assert d.judgment == md["judgment"]

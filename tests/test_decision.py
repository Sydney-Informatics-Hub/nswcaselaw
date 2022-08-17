import logging

import pytest

from nswcaselaw.nswcaselaw import Decision

_logger = logging.getLogger(__name__)


@pytest.mark.parametrize("style", ["old"])
def test_decision_scrape(scrape_fixtures, style):
    d = Decision()
    with open(scrape_fixtures[style], "r") as fh:
        html = fh.read()
        d.scrape(html)
        values = d.dict
        values.pop("judgment")
        values.pop("date")
        values.pop("uri")
        assert d.dict == scrape_fixtures["metadata"]

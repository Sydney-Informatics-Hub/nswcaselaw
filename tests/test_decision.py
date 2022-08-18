import logging

import pytest

from nswcaselaw.nswcaselaw import Decision

_logger = logging.getLogger(__name__)


@pytest.mark.parametrize("style", ["new", "old"])
def test_decision_scrape(scrape_fixtures, style):
    d = Decision()
    with open(scrape_fixtures[style], "r") as fh:
        html = fh.read()
        result = d.scrape(html)
        assert result
        assert d.values == scrape_fixtures["metadata"]

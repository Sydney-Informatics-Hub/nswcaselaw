import logging

import pytest

from nswcaselaw.constants import COURTS, index_to_court
from nswcaselaw.nswcaselaw import Search

_logger = logging.getLogger(__name__)


def test_results_scrape(search_fixtures):
    """Tests web parsing without actually hitting Caselaw"""
    s = Search()
    with open(search_fixtures["html"], "r") as fh:
        html = fh.read()
        n_results, results = s.scrape_results(html)
        assert n_results == search_fixtures["n_results"]
        with open(search_fixtures["csv"], "r") as cfh:
            for line in cfh:
                got = repr(results.pop(0))
                expect = line.rstrip()
                assert got == expect
        assert len(results) == 0


@pytest.mark.parametrize("court_type", ["courts", "tribunals"])
def test_court_ids(court_type):
    for i, court_tuple in enumerate(COURTS[court_type]):
        c = index_to_court(court_type, i + 1)
        assert c[0] == court_tuple[0]


@pytest.mark.parametrize("court_type", ["courts", "tribunals"])
def test_court_query(court_type):
    for i, court_tuple in enumerate(COURTS[court_type]):
        c = index_to_court(court_type, i + 1)
        q = {court_type: [i + 1]}
        s = Search(**q)
        s.build_query()
        cparams = [p for p in s.params if p[0] == court_type]
        assert len(cparams) == 1
        assert cparams[0][1] == c[0]

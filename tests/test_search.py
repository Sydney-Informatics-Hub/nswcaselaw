import logging

from nswcaselaw.nswcaselaw import Search

_logger = logging.getLogger(__name__)


def test_search(search_fixtures):
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

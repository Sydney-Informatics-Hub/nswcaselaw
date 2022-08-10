from nswcaselaw.nswcaselaw import Search


def test_search():
    """Search tests"""
    search = Search({"body": "crime"})
    for result in search.results():
        assert result is not None

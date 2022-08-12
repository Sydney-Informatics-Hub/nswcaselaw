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

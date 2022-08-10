import argparse
import logging
import sys
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from nswcaselaw import __version__

__author__ = "Mike Lynch"
__copyright__ = "The University of Sydney"
__license__ = "MIT"

_logger = logging.getLogger(__name__)

CASELAW_SEARCH_URL = "https://www.caselaw.nsw.gov.au/search/advanced"
# WAIT_TIME


class CaseLawException(Exception):
    pass


class Search:
    """
    Class representing a CaseLaw query. Intialise it with a dictionary
    of search parameters.
    """

    def __init__(self, search: Dict[str, str]):
        self._search = search

    @property
    def search(self) -> Dict[str, str]:
        return self._search

    def results(self):
        """yield results until we've finished"""
        r = requests.get(CASELAW_SEARCH_URL, self._search)
        if r.status_code == 200:
            results = self.scrape_results(r)
            for result in results:
                yield result
        else:
            raise CaseLawException(f"Bad status_code {r.status_code}")
            # request next page, if appropriate, after a wait

    def scrape_results(self, r: requests.Response) -> List[str]:
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.find_all("a")
        return links


# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="NSW CaseLaw tool")
    parser.add_argument(
        "--version",
        action="version",
        version="nswcaselaw {ver}".format(ver=__version__),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    parser.add_argument(
        "--body",
        type=str,
        help="Free text search of the entire judgment",
    )
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main(args):
    """Wrapper allowing :func:`fib` to be called with string arguments in a CLI fashion

    Instead of returning the value from :func:`fib`, it prints the result to the
    ``stdout`` in a nicely formatted message.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    search = Search({"body": args.body})
    for r in search.results():
        print(r)


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()

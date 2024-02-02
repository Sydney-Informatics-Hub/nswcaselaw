"""A module for downloading NSW case law decisions

nswcaselaw is a module for downloading and parsing court and tribunal
decisions from https://www.caselaw.nsw.gov.au/

    from nswcaselaw.search import Search

    search = Search(courts=[13], catchwords="defamation")

    for decision in search.results():
        print(f"Case: {decision.title}")
        decision.fetch()
        judgment = decision.judgment

"""

import argparse
import csv
import json
import logging
import re
import sys
from pathlib import Path

from nswcaselaw import __version__
from nswcaselaw.constants import CASELAW_BASE_URL, COURTS
from nswcaselaw.decision import SCRAPER_WARNING, Decision
from nswcaselaw.search import Search

__author__ = "Mike Lynch"
__copyright__ = "The University of Sydney"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


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
        "--list",
        type=str,
        choices=["courts", "tribunals"],
        help="Print a list of courts or tribunals",
    )
    parser.add_argument(
        "--dump", type=Path, default=None, help="Dir to dump HTML for debugging"
    )
    parser.add_argument(
        "--test-parse",
        type=Path,
        default=None,
        help="Test scraper on an HTML document and print results as JSON",
    )
    parser.add_argument("--body", type=str, help="Full text search")
    parser.add_argument("--title", type=str, help="Case name")
    parser.add_argument("--before", type=str)
    parser.add_argument("--catchwords", type=str)
    parser.add_argument("--party", type=str)
    parser.add_argument("--citation", type=str, help="Must include square brackets")
    parser.add_argument("--startDate", type=str, help="Earliest decision date")
    parser.add_argument("--endDate", type=str, help="Lastest decision date")
    parser.add_argument("--fileNumber", type=str)
    parser.add_argument("--legislationCited", type=str)
    parser.add_argument("--casesCited", type=str)
    parser.add_argument(
        "--courts",
        type=int,
        nargs="+",
        default=[],
        help="Select one or more by index number (see --list courts)",
    )
    parser.add_argument(
        "--tribunals",
        type=int,
        nargs="+",
        default=[],
        help="Select one or more by index number (see --list tribunals)",
    )
    parser.add_argument(
        "--uris", type=Path, default=None, help="CSV file with caselaw URIs"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Search results will be written to this file as CSV",
    )
    parser.add_argument(
        "--download",
        type=Path,
        default=None,
        help="Save decisions as JSON to the directory DOWNLOAD",
    )
    parser.add_argument("--limit", type=int, default=None, help="Max results")
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stderr, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def list_courts(court_type: str):
    """Print a list of courts or tribunals, with indices, to stdout

    Args:
      court_type (str): either "courts" or "tribunals"
    """
    if court_type not in COURTS:
        _logger.error("Court type must be either 'courts' or 'tribunals'")
    else:
        for index, (_, name) in enumerate(COURTS[court_type]):
            print(f"{index + 1:2d}. {name}")
        print(SCRAPER_WARNING)


def test_scrape(test_file: str):
    """Load an HTML file and scrape it, printing the results as JSON.

    Used for testing development of different scraper backends.

    Args:
      test_file (str): file to scrape
    """
    d = Decision()
    if d.load_file(test_file):
        print(json.dumps(d.values, indent=2))
    else:
        print(f"scrape of {test_file} failed")


def run_query(args: argparse.Namespace):
    """Run a search query against caselaw, printing the search results as
    CSV, and downloading the full decision text as JSON into a directory if
    one is provided

    Args:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    search = Search(
        body=args.body,
        title=args.title,
        before=args.before,
        catchwords=args.catchwords,
        party=args.party,
        mnc=args.citation,
        startDate=args.startDate,
        endDate=args.endDate,
        fileNumber=args.fileNumber,
        legislationCited=args.legislationCited,
        casesCited=args.casesCited,
        courts=args.courts,
        tribunals=args.tribunals,
    )
    n = 0
    with output_stream(args.output) as fh:
        csvout = csv.writer(fh, dialect="excel")
        for decision in search.results():
            if n == 0:
                # only print the header if there's at least one result
                csvout.writerow(decision.header)
            if args.download:
                download_decision(decision, args)
            csvout.writerow(decision.row)
            n += 1
            if args.limit and n >= args.limit:
                break


def download_uris(args: argparse.Namespace):
    """Loads a spreadsheet with caselaw URLs and downloads and parses each
    decision.

    Args:
      :obj:`argparse.Namespace`: command line parameters namespace
    """

    n = 0
    with output_stream(args.output) as fh:
        csvout = csv.writer(fh, dialect="excel")
        for uri in load_uris_from_csv(args.uris):
            print(uri)
            decision = Decision(uri=uri)
            if args.download:
                download_decision(decision, args)
                csvout.writerow(decision.row)
                n += 1
                if args.limit and n >= args.limit:
                    break


def output_stream(outfile):
    """Either opens a file for output, or returns stdout if the filename is
    empty.

    Args:
      outfile (str): a filename or ''
    Return:
      :obj:`_io.TextIOWrapper`: an output stream
    """
    if outfile:
        return open(outfile, "w", newline="")
    else:
        return sys.stdout


def download_decision(decision, args):
    """Fetch the full detains for a decision, and write out the JSON, and
    optionally the HTML, to the download and dump directory

    Args:
      decision (:obj:`nswcaselaw.decision.Decision`): a decision
      args: (:obj:`argparse.Namespace`:): the command-line args
    """
    decision.fetch()  # what happens if this fails?
    if args.dump:
        htmlfile = (args.dump / decision.id).with_suffix(".html")
        with open(htmlfile, "w") as fh:
            if decision.html is not None:
                fh.write(decision.html)
            else:
                fh.write("No content")
    jsonfile = (args.download / decision.id).with_suffix(".json")
    with open(jsonfile, "w") as fh:
        fh.write(json.dumps(decision.values, indent=2))


def load_uris_from_csv(csvfile):
    """
    Read a CSV file and get everything which looks like a caselaw URL and
    return it as a Generator of str
    Args:
        csvfile(:obj:`pathlib.Path`)
    Return:
        Generator(str)
    """
    url_re = re.compile(CASELAW_BASE_URL + "(/decision/[a-f0-9]+)")
    with open(csvfile, "r", newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for val in row:
                m = url_re.match(val)
                if m:
                    yield m.group(1)


def main(args):
    """
    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    if args.test_parse:
        test_scrape(args.test_parse)
    else:
        if args.list:
            list_courts(args.list)
        else:
            if args.uris:
                download_uris(args)
            else:
                if not (args.courts or args.tribunals):
                    _logger.error(
                        """
You must select at least one court or tribunal.

Use the --list courts or --list tribunals options for a list of available
options.
"""
                    )
                else:
                    run_query(args)


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()

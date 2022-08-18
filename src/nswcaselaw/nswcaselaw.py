import argparse
import json
import logging
import sys
from pathlib import Path

from nswcaselaw import __version__
from nswcaselaw.constants import COURTS
from nswcaselaw.decision import Decision
from nswcaselaw.search import Search

__author__ = "Mike Lynch"
__copyright__ = "The University of Sydney"
__license__ = "MIT"

_logger = logging.getLogger(__name__)

# WAIT_TIME


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
        "--download",
        type=Path,
        default=None,
        help="Download full judgments and write JSON to this directory",
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


def list_courts(court_type: str):
    """
    Print a list of courts or tribunals, with indices, to stdout
    """
    for index, (_, name) in enumerate(COURTS[court_type]):
        print(f"{index + 1:2d}. {name}")


def test_scrape(test_file):
    d = Decision()
    if d.load_file(test_file):
        print(json.dumps(d.values, indent=2))
    else:
        print(f"scrape of {test_file} failed")


def run_query(args: argparse.Namespace):
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
    for decision in search.query():
        if args.download:
            decision.fetch()
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
        print(decision.csv)


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

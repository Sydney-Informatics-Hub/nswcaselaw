import argparse
import logging
import sys
from typing import Dict

from nswcaselaw import __version__
from nswcaselaw.constants import COURTS, court_id
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
    parser.add_argument("--body", type=str, help="Full text search")
    parser.add_argument("--title", type=str, help="Case name")
    parser.add_argument(
        "--before",
        type=str,
        help="Judge, commissioner, magistrate, member, registrar or assessor",
    )
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
        help="Select one or more by index number (see --list courts)",
    )
    parser.add_argument(
        "--tribunals",
        type=int,
        nargs="+",
        help="Select one or more by index number (see --list tribunals)",
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


def args_to_query(args: argparse.Namespace) -> Dict[str, str]:
    """
    Build the query dictionary from the command-line args
    """
    query = {}
    if args.body:
        query["body"] = args.body
    if args.title:
        query["title"] = args.title
    if args.before:
        query["before"] = args.before
    if args.catchwords:
        query["catchwords"] = args.catchwords
    if args.party:
        query["party"] = args.party
    if args.citation:
        query["mnc"] = args.citation
    if args.startDate:
        query["startDate"] = args.startDate
    if args.endDate:
        query["endDate"] = args.endDate
    if args.fileNumber:
        query["fileNumber"] = args.fileNumber
    if args.legislationCited:
        query["legislationCited"] = args.legislationCited
    if args.casesCited:
        query["casesCited"] = args.casesCited
    if args.courts:
        query["courts"] = [court_id("courts", c)[0] for c in args.courts]
    if args.tribunals:
        query["tribunals"] = [court_id("tribunals", c)[0] for c in args.tribunals]
    return query


def main(args):
    """
    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    if args.list:
        list_courts(args.list)
    else:
        if not (args.courts or args.tribunals):
            _logger.error("You must select at least one court or tribunal")
        else:
            query = args_to_query(args)
            search = Search(query)
            for r in search.results():
                print(r)


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()

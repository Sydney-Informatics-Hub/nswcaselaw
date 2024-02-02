# nswcaselaw

A Python toolkit for downloading and extracting textual data from the NSW
CaseLaw website at https://www.caselaw.nsw.gov.au/

## Usage

Sample usage in Python code or a Jupyter notebook

    from nswcaselaw.search import Search
    import json

    query = Search(courts=[13], catchwords="succession", pause=1)

    for decision in query.results():
      decision.fetch()
      print(json.dumps(decision.values, indent=2))

    url = query.url


## CLI tool 

To generate a CSV of search results

    nswcaselaw --courts 13 --catchwords succession --output cases.csv

To download complete decisions as JSON documents

    nswcaselaw --courts 13 --catchwords succession --output cases.csv  --download ./decisions

To list available courts and tribunals (NOTE: full web scraping is only
tested on Supreme Court decisions)

    nswcaselaw --list courts
    nswcaselaw --list tribunals

Command-line parameters:

    -h, --help            show help message and exit
    --version             show program's version number and exit
    -v, --verbose         set loglevel to INFO
    -vv, --very-verbose   set loglevel to DEBUG
    --list {courts,tribunals}
                          Print a list of courts or tribunals
    --dump DUMP           Dir to dump HTML for debugging
    --test-parse TEST_PARSE
                          Test scraper on an HTML document and print results as
                          JSON
    --body BODY           Full text search
    --title TITLE         Case name
    --before BEFORE
    --catchwords CATCHWORDS
    --party PARTY
    --citation CITATION   This must include square brackets
    --startDate STARTDATE
                          Earliest decision date
    --endDate ENDDATE     Lastest decision date
    --fileNumber FILENUMBER
    --legislationCited LEGISLATIONCITED
    --casesCited CASESCITED
    --pause PAUSE         Seconds to wait between requests: default 10
    --courts COURTS [COURTS ...]
                          Select one or more by index number (see --list courts)
    --tribunals TRIBUNALS [TRIBUNALS ...]
                          Select one or more by index number (see --list
                          tribunals)
    --uris URIS           CSV file with caselaw URIs to download
    --output OUTPUT       Search results will be written to this file as CSV
    --download DOWNLOAD   Save decisions as JSON to the directory DOWNLOAD
    --limit LIMIT         Max results
  

Installation
============

Follow the instructions at https://docs.conda.io/projects/conda/en/latest/user-guide/install/download.html to install Conda.

To create a conda environment with Jupyter and nswcaselaw

    conda create -n mycaselaw jupyter
    conda activate mycaselaw
    pip install nswcaselaw
  
Once the dependencies are installed

    jupyter notebook

will start Jupyter and open a browser. Any notebooks you create in this will
be able to import the nswcaselaw module as shown above

    from nswcaselaw.search import Search

To install nswcaselaw without Jupyter, follow the same steps to install Conda,
and then create a new environment as follows

    conda create -n mycaselaw
    conda activate mycaselaw
    pip install nswcaselaw

You should now be able to use the ``nswcaselaw`` command from a terminal (on
Mac or Linux) or the Anaconda prompt (on Windows).

## Acknowledgements

This project is partially funded by a 2022 University of Sydney Research
Accelerator (SOAR) Prize awarded to Ben Chen.

## Note

This project has been set up using PyScaffold 4.3. For details and usage
information on PyScaffold see https://pyscaffold.org/.

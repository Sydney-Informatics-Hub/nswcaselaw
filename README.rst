
.. image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
    :alt: Project generated with PyScaffold
    :target: https://pyscaffold.org/

|

==========
nswcaselaw
==========

A Python toolkit for downloading and extracting textual data from the NSW
CaseLaw website at https://www.caselaw.nsw.gov.au/

Usage
=====

Sample usage in Python code or a Jupyter notebook::

  from nswcaselaw.search import Search
  import json

  query = Search(courts=[13], catchwords="succession")

  for decision in query.results():
      decision.fetch()
      print(json.dumps(decision.values, indent=2))


CLI tool 
========

To generate a CSV of search results::

  nswcaselaw --courts 13 --catchwords succession --output cases.csv

To download complete decisions as JSON documents::

  nswcaselaw --courts 13 --catchwords succession --output cases.csv  --downloads ./decisions

To list available courts and tribunals (NOTE: full web scraping is only
tested on Supreme Court decisions)::

  nswcaselaw --list courts
  nswcaselaw --list tribunals
  

Installation
============

Follow the instructions at https://docs.conda.io/projects/conda/en/latest/user-guide/install/download.html to install Conda.

To create a conda environment with Jupyter and nswcaselaw::

  conda create -n mycaselaw jupyter
  conda activate mycaselaw
  pip install nswcaselaw
  
Once the dependencies are installed::

  jupyter notebook

will start Jupyter and open a browser. Any notebooks you create in this will
be able to import the nswcaselaw module as shown above::

  from nswcaselaw.search import Search

To install nswcaselaw without Jupyter, follow the same steps to install Conda,
and then create a new environment as follows::

  conda create -n mycaselaw
  conda activate mycaselaw
  pip install nswcaselaw

You should now be able to use the ``nswcaselaw`` command from a terminal (on
Mac or Linux) or the Anaconda prompt (on Windows).

Note
====

This project has been set up using PyScaffold 4.3. For details and usage
information on PyScaffold see https://pyscaffold.org/.

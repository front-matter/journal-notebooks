#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 19 13:29:49 2020

@author: Martyn Rittman, mrittman@crossref.org

Some functions that act as a simple wrapper to query Crossref event data and 
make some interpretations. Contributions, fixes and additions welcome!

"""

from datetime import datetime
import pandas as pd
from pandas.tseries.offsets import DateOffset


# Functions to query event data
from .eventData import eventData
# Functions to interpret event data json files
from .eventRecord import eventRecord

from .evidenceRecords import evidenceRecords
from .activityLogs import activityLogs

# Function to query the REST API
from .restApi import restApi

# Function to get the last n months


def lastNmonths(n: int) -> list:
    '''
    Find the first and last dates of the last n months. Returns a list of 
    ordered doubles, e.g. [('2017-12-01', '2017-12-31'), ('2018-01-01', '2018-01-31'),...]

    Useful for building queries with monthly date ranges. e.g.

    rng = t.last_n_months(30)
    query_template = "https://api.crossref.org/works?from-created-date={start}&until-created-date={end}"
    queries = [query_template.format(start=start, end=end) for start, end in rng]


    Parameters
    ----------
    n : int
        The number of previous months you want to know.

    Returns
    -------
    list
        List of ordered doubles containing the first and last days in a month
        in the format YYYY-MM-DD.

    '''

    start = (datetime.utcnow().date() + DateOffset(months=-n)).date()
    return [
        (f"{d.year}-{d.month:02}-01", f"{d.year}-{d.month:02}-{d.day}")
        for d in pd.date_range(start, periods=n, freq="M")
    ]

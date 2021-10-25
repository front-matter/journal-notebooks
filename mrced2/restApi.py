# -*- coding: utf-8 -*-

import requests
import json
import re
import datetime
import glom


class restApi:
    ''' A class to query the Crossref REST API

    basic usage: use runQuery() to build and execute a command

    See https://github.com/CrossRef/rest-api-doc for online documentation


    '''

    def __init__(self, **kwargs):
        ''' Initalise some things
                self.outputFile - json file that the query results are saved to

        '''

        # Options for the user to define, some can be provided as keywords

        # output filename
        if "outputFile" in kwargs:
            self.outputFile = kwargs["outputFile"]
        elif "filename" in kwargs:
            self.outputFile = kwargs["filename"]  # alternative keyword
        else:
            # file that the output from the query are saved as, should be json
            self.outputFile = '10.21105/works.json'

        # user email address
        if "mailto" in kwargs:
            self.mailto = kwargs["mailto"]
        else:
            self.mailto = 'Anonymous'

        # Internal variables
        # displays the command executed; note that the acutal call is done with the requests package
        self.success = False  # True if the last API call was successful

    def runQuery(self, row, retry=1, quiet=False):
        '''

        Parameters
        ----------

        row: 
            data frame row with ["obj_id"] and ["count"]

        retry: int
            number of times to retry the API query if it fails. Simple version of tenacity

        quiet: boolean
            if true, nothing is printed to screen.

        Returns
        -------
        None.

        '''

        # Short message to say things are getting going
        if not(quiet):
            print(f"REST API query started for {row['obj_id'][16:]}...")

        # the query URL
        url = "https://api.crossref.org/works/" + row["obj_id"][16:]

        for ii in range(retry):
            # make the API request using parameters from buildQuery()
            r = requests.get(url)

            # print a short confirmation on completion
            if not(quiet):
                print('REST API query complete ', r.status_code)

            # stop if there wasn't a response
            if r.status_code in (200, 201):
                self.success = True
                jsonData = r.json()
                if jsonData["message"]["type"] == "posted-content":
                    self.work = {
                        "doi": row["obj_id"][16:],
                        "tweets": row["count"],
                        "archive": jsonData["message"]["institution"][0]["name"] if "institution" in jsonData["message"] else None,
                        "subject-area": jsonData["message"]["group-title"] if "group-title" in jsonData["message"] else None,
                        "covid": re.search(r"(CoV-2|COVID)", (jsonData["message"]["title"][0] + jsonData["message"]["abstract"]), re.IGNORECASE) is not None,
                        "title": jsonData["message"]["title"][0],
                        "authors": str(list(map(self.authorName, jsonData["message"]["author"]))),
                        "abstract": re.sub('^<title>.*?</title>', '', re.sub(r"jats:", "", jsonData["message"]["abstract"])),
                        "posted": self.date_parts_to_string(jsonData["message"]["posted"]["date-parts"][0])
                    }
                else:
                    self.work = None

                break

            else:
                self.success = False
                self.work = None

    def authorName(self, a):
        return {"name": ' '.join([a["given"] if "given" in a else '', a["family"] if "family" in a else ''])}

    def date_parts_to_string(self, date_parts, fill: bool = False):
        # from https://manubot.github.io/manubot/reference/manubot/cite/csl_item/
        """

        Return a CSL date-parts list as ISO formatted string:

        ('YYYY', 'YYYY-MM', 'YYYY-MM-DD', or None).

        date_parts: list or tuple like [year, month, day] as integers.

            Also supports [year, month] and [year] for situations where the day or month-and-day are missing.

        fill: if True, set missing months to January

            and missing days to the first day of the month.

        """

        if not date_parts:

            return None

        if not isinstance(date_parts, (tuple, list)):

            raise ValueError(f"date_parts must be a tuple or list")

        while fill and 1 <= len(date_parts) < 3:

            date_parts.append(1)

        widths = 4, 2, 2

        str_parts = []

        for i, part in enumerate(date_parts[:3]):

            width = widths[i]

            if isinstance(part, int):

                part = str(part)

            if not isinstance(part, str):

                break

            part = part.zfill(width)

            if len(part) != width or not part.isdigit():

                break

            str_parts.append(part)

        if not str_parts:

            return None

        iso_str = "-".join(str_parts)

        return iso_str

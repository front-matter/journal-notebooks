# -*- coding: utf-8 -*-

import requests
import json
#from tenacity import retry, stop_after_attempt, wait_random_exponential
try:
    from mrced2.eventRecord import eventRecord
except:
    from eventRecord import eventRecord


class eventData:
    ''' A class to query the Crossref event data API

    basic usage: use buildQuery() to build a command and runCommand() to execute it

    See https://www.eventdata.crossref.org/guide/service/query-api/ for online documentation


    '''

    def __init__(self, **kwargs):
        ''' Initalise some things
                self.queryUrl - executed to query the Crossref event data API
                self.outputFile - json file that the query results are saved to
                facetLimit - number of results returned when looking for a facet
                rows - number of rows of full results to add into json file
                self.cursor - a cursor for the next search, if required
                self.pageCount - iterates through results pages

        '''

        # Options for the user to define, some can be provided as keywords

        # output filename
        if "outputFile" in kwargs:
            self.outputFile = kwargs["outputFile"]
        elif "filename" in kwargs:
            self.outputFile = kwargs["filename"]  # alternative keyword
        else:
            # file that the output from the query are saved as, should be json
            self.outputFile = '10.21105/ced.json'

        # user email address
        if "mailto" in kwargs:
            self.mailto = kwargs["mailto"]
        else:
            self.mailto = 'Anonymous'

        if "facetLimit" in kwargs:
            self.facetLimit = kwargs["facetLimit"]
        else:
            self.facetLimit = '*'  # number of facet  results to report

        if "rows" in kwargs:
            self.rows = kwargs["rows"]
        else:
            self.rows = 1000  # default number of rows to report

        # Internal varaibles
        # displays the command executed; note that the acutal call is done with the requests package
        self.queryUrl = ''
        self.cursor = "-1"  # a null value for the next cursor
        self.pageCount = 1  # iterates through results pages, also used in filenames
        self.success = False  # True if the last API call was successful

    def buildQuery(self, filters, quiet=False, cursor=None):
        ''' Build the query for the eventdata API, but don't execute it. Run 'runcommand' to execute.

        Parameters
        ----------

        quiet: boolean
            if True nothing the api query isn't printed

        cursor: str or boolean
            if True, it will use the cursor from the previous query (if there is one)
            if a string, it will use the string as a cursor

        filters: dict
            - e.g. {obj_id : "10.1111/12345678, facets = "newsfeed"}

            kwargs can contain:
                from-occurred-date # as YYYY-MM-DD
                until-occurred-date # as YYYY-MM-DD
                from-collected-date # as YYYY-MM-DD
                until-collected-date # as YYYY-MM-DD
                from-updated-date # as YYYY-MM-DD
                until-updated-date # as YYYY-MM-DD
                subj-id # quoted URL or a DOI
                obj-id # quoted URL or a DOI
                subj-id.prefix # DOI prefix like 10.5555, if Subject is a DOI
                obj-id.prefix # DOI prefix like 10.5555, if Object is a DOI
                subj-id.domain # domain of the subj-id e.g. en.wikipedia.org
                obj-id.domain # domain of the obj-url e.g. en.wikipedia.org
                subj.url # quoted full URL
                obj.url # quoted full URL
                subj.url.domain # domain of the optional subj.url, if present e.g. en.wikipedia.org
                obj.url.domain # domain of the optional obj.url, if present e.g. en.wikipedia.org
                subj.alternative-id # optional subj.alternative-id
                obj.alternative-id # optional obj.alternative-id
                relation-type # relation type ID
                source # source ID
                facets # a facet (type of data to return summary stats for)

                See https://www.eventdata.crossref.org/guide/service/query-api/ for online documentation

        '''

        # List of arguments used by event data, ensures that queries are correctly formed
        allowedArgs = ('from-occurred-date', 'until-occurred-date', 'from-collected-date',
                       'until-collected-date', 'from-updated-date', 'until-updated-date',
                       'subj-id', 'obj-id', 'subj-id.prefix', 'obj-id.prefix',
                       'subj-id.domain', 'obj-id.domain', 'subj.url', 'obj.url',
                       'subj.url.domain', 'obj.url.domain', 'subj.alternative-id',
                       'obj.alternative-id', 'relation-type', 'source', 'facet', 'rows')

        # Start to build the query parameters required for the API request
        params = {}
        params['mailto'] = self.mailto

        if not('rows') in filters:
            params['rows'] = self.rows

        # if using a cursor
        if cursor:
            # use the cursor from previous query
            if (cursor == True) & (self.cursor != '-1'):
                params['cursor'] = self.cursor
            # user-defined cursor
            elif cursor != True:
                params['cursor'] = cursor

        for k in filters:
            if k in allowedArgs:
                # save keyword and parameter (e.g. from-collected-date=2020-01-01)
                params[k] = str(filters[k])
            else:
                # error message in case
                print('non-standard filter found, ' +
                      k + ', ' + str(filters[k]))

        # add count to facets
        if 'facet' in params:
            params['facet'] = params['facet'] + ':' + str(self.facetLimit)

        self.params = params

        if not(quiet):
            # For the benefit of users, display the query to be made
            self.queryUrl = 'https://api.eventdata.crossref.org/v1/events?'

            # add parameters to the text query
            for p in params:
                self.queryUrl += str(p) + "=" + str(self.params[p]) + "&"

            self.queryUrl = self.queryUrl[:-1]
            print(self.queryUrl)

    def runCommand(self):
        print("please use runQuery, runCommand will be deprecated")

        self.runQuery()

    def runQuery(self, retry=1, quiet=False, saveToFile=True):
        '''
        Run the query defined by buildQuery(), uses requests

        Parameters
        ----------

        Retry: int
            number of times to retry the API query if it fails. Simple version of tenacity

        quiet: boolean
            if true, nothing is printed to screen.
        saveToFile : boolean
            Saves the result to self.outputFile if 
            set to True. The default is True.

        Returns
        -------
        None.

        '''

        # Short message to say things are getting going
        if not(quiet):
            print("Event Data query started...")

        # the query URL
        # "https://api-staging.eventdata.crossref.org/v1/events"
        url = "https://api.eventdata.crossref.org/v1/events"

        for ii in range(retry):
            # make the API request using parameters from buildQuery()
            r = requests.get(url, params=self.params)

            # print a short confirmation on completion
            if not(quiet):
                print('API query complete ', r.status_code)

            # stop if there wasn't a response
            if r.status_code in (200, 201):
                self.success = True
                # find and save the next cursor (add to next call to iterate results pages)
                jsonData = r.json()
                self.cursor = jsonData["message"]["next-cursor"]

                self.events = eventRecord()
                self.events.jsonData = jsonData

                if saveToFile:
                    with open(self.outputFile, 'w') as f:
                        # save the json result to file
                        json.dump(jsonData, f)
                        if not(quiet):
                            print("output file written to " + self.outputFile)

                break

            else:
                self.success = False

    def getNextPage(self):
        '''
        Run the same query as before iterating the cursor.

        Returns
        -------
        None.

        '''

        # put the cursor into the parameters
        if self.cursor in ("-1", None):
            print("max page limit reached", self.cursor)
            self.cursor = "-1"

        else:
            self.params["cursor"] = self.cursor

            # add a page number to the result
            if self.outputFile[-5:] == ".json":
                fdum = self.outputFile  # fix to set the outputFile as it was
                self.outputFile = self.outputFile[:-5] + \
                    str(self.pageCount).zfill(3) + ".json"
            else:
                self.outputFile = self.outputFile[:-
                                                  5] + str(self.pageCount).zfill(3)

            # run the search
            try:
                self.runQuery(retry=1)
            except:
                print('failure for ' + self.outputFile)

            # iterate the page number
            if self.success:
                self.pageCount += 1

            # fix to set the outputFile back as it was
            self.outputFile = fdum

    def getAllPages(self, maxPages, filters, fileprefix='test'):
        '''
        Run a query then iterate all pages to get the full results

        Parameters
        ----------

        maxPages - set a limit for the number of pages to retrieve
        maxQueries - a limit for hte number of API queries to make (some may fail)
        filters - same as for buildQuery()

        Returns
        -------
        None.

        '''

        if 'rows' in filters:
            if filters['rows'] == 0:
                print('zero rows defined')
                return
        elif self.rows == 0:
            print('zero rows defined')
            return

        # Subsequent runs
        query = 0

        for x in range(maxPages):

            self.outputFile = fileprefix + str(x).zfill(4) + '.json'
            self.buildQuery(filters, cursor=True)
            self.runQuery(retry=5)

            if (self.cursor == '-1') | (self.cursor == None):
                break

            if self.success == False:
                print('unsuccessful query')
                break


if __name__ == "__main__":

    ed = eventData(mailto='eventdata@crossref.org')

    fl = {'from-collected-date': '2021-02-01', 'rows': 100,
          'until-collected-date': '2021-02-04', 'source': 'plaudit'}
    # ed.buildQuery(fl, cursor=True)
    # ed.runQuery(retry = 5)

    ed.getAllPages(5, fl)

    ed.events.getHits()

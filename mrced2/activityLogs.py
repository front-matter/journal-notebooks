'''
Package for extracting data from Crossref Event Data evidence logs.

@author: Martyn Rittman

'''

import datetime
import requests
import json


class activityLogs:

    def __init__(self):

        self.outputFile = 'test.json'

        self.queryPrefix = 'https://evidence.eventdata.crossref.org/log/'
        self.query = ""
        self.jsonData = []
        self.success = False

    def buildQuery(self, date):
        '''
        Build a query of the evidence logs

        Parameters
        ==========
        date: date in text of datetime format, e.g. 2021-01-01T01

        Returns
        =======
        None


        '''

        if type(date) == str:

            self.query = self.queryPrefix + date + '.txt'

        print(self.query)

    def runQuery(self, quiet=False):
        '''
        Use requests to run the query defined by buildQuery
        '''

        r = requests.get(self.query)

        # print a short confirmation on completion
        if not(quiet):
            print('Evidence log API query complete ', r.status_code)

        # stop if there wasn't a response
        if r.status_code in (200, 201):
            self.success = True
            # find and save the next cursor (add to next call to iterate results pages)
            tx = r.text

            # make the output json compatible

            # split lines
            logsd = tx.split('\n')

            self.jsonData = []  # new object with successfully transformed lines
            for l in range(len(logsd)):
                try:
                    # turn line into a dictionary
                    self.jsonData.append(eval(logsd[l]))
                except:
                    pass

        else:
            self.success = False

    # ====================================

    # Analysis scripts

    def getEvidenceRecords(self):
        '''
        Examine the log entries and pull out any evidence records mentioned.

        Returns
        -------
        None.

        '''

        evidenceRecords = []

        for log in self.jsonData:

            # see if there's an evidence record mentioned
            try:
                evrec = log['r']
            except:
                # we didn't find an activity log
                continue

            # we've already seen this one
            if evrec in evidenceRecords:
                continue

            evidenceRecords.append(evrec)

        return evidenceRecords


if __name__ == '__main__':

    al = activityLogs()
    al.buildQuery('2021-01-17T01')

    al.runQuery()

    actlogs = al.getActivityLogs()

    print(actlogs)
    print(len(actlogs))

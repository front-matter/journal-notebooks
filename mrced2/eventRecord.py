#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  8 14:28:58 2020

@author: martynrittman
"""

import json
import pandas as pd
import pprint


class eventRecord():
    '''

    Stores json data with events, and performs analysis

    Use loadJson(filename) to read a json file and turn it into a Python dictionary
    addJsonData - pass a dictionary directly here
    getFacets - will nicely display and save facet data in the file
    displayHits - save and print the total number of results found for a query
    combineFacets - combines facet data solved in multiple files
    displayEvents - print the first n events
    searchEvents - countEvents with some property
    filterEvents - create a subset of events by filtering
    eventHist - find counts of events with certain properties
    dictValueCheck - used by eventHist, checks for values in a dictionary


    '''

    def __init__(self, **kwargs):
        ''' Initialisation. The variables here are set elsewhere, no user input is needed.

        Parameters
        ----------

        kwargs:

        filename - loads this file if passed as a keyword argument


        '''

        self.jsonData = {}  # A dictionary populated by loadJson
        self.stats = {}  # dictionary with statistics about the data, e.g. total hits and facets

        if "filename" in kwargs:
            self.loadJson(kwargs["filename"])

    # ========================================================================

    # Get json data in and out

    def loadJson(self, filename):
        ''' load a json file (filename) and turn it into a dictionary, self.jsonData

            returns 1 for success, otherwise returns 0'''

        with open(filename) as f:
            try:
                # Use the json package to load the data
                self.jsonData = json.load(f)
                status = self.jsonData["status"]

                # Set a boolean to determine whether the query worked
                if status == 'failed':
                    self.jsonLoadSuccess = False
                else:
                    self.jsonLoadSuccess = True

                return self.jsonLoadSuccess

            except:
                # Print a message but don't raise an exception in case of failure
                print('JSON file could not be read, check the contents')

                return False  # failure

    def addJsonData(self, jsonData):
        ''' add data from a dictionary. There is a brief check on the format, 
        although this isn't very extensive so be careful.

        Parameters
        ----------

        jsonData: a dictionary containing data formatted correctly.

        Returns
        --------
        self.jsonLoadSuccess: boolean reporting on whether the json looked to be 
                            in the correct format.        

        '''

        self.jsonData = jsonData
        self.jsonLoadSuccess = True

        try:
            self.jsonData['message']['events']
        except:
            self.jsonLoadSuccess = False

        return self.jsonLoadSuccess

    def mergeJsons(self, fileList, folder=""):
        '''
        A function to join multiple json files into one, for example if you collect
        different pages for a single call.

        Parameters
        ----------
        fileList : List of strings
            A list of files for which events should be merged.
        folder : String
            optional argument to include in case all files are in a subfolder,
            will be prefixed to the file name before opening.
        saveToFile : boolean
            Saves the merged json contents to self.outputFile if 
            set to True. The default is True.
        quiet: boolean
            if True nothing will be printed

        Returns
        -------
        None.

        '''

        # add a backslash to the folder name if the user didn't
        if (folder != "") & (folder[:-1] != "/"):
            folder += "/"

        # reset the json data to be empty
        self.jsonData = {"status": "ok", "message": {
            "events": [], "total-results": 0}}

        # iterate the file list
        for fname in fileList:
            try:
                with open(folder + fname) as f:
                    # get the data from the file using the json module

                    js = json.load(f)

                    # append the events if the file contains valid results
                    if js["status"] == "ok":
                        self.jsonData["message"]["events"] = self.jsonData["message"]["events"] + \
                            js["message"]["events"]
                        self.jsonData["message"]["total-results"] += js["message"]["total-results"]

            except:
                # print a message but continue to the next file if something goes wrong
                print("failed to load " + fname)

        # check if something loaded
        if len(self.jsonData["message"]["events"]) > 0:
            self.jsonLoadSuccess = True

        # save to a new JSON file
        with open("10.21105/ced.json", 'w') as f:
            # save the json result to file
            json.dump(self.jsonData, f)
            print("output file written to " + "10.21105/ced.json")

    def getStatus(self):
        ''' Check the Json data to see the status of the search 

        Returns
        -------
        str:
            status as reported in json data, with values: success, failed, null
            null is produced by this function in the case that the status is not
            included in the json data. 

        '''

        try:
            status = self.jsonData["status"]
        except:
            print('no status data in json')
            return 'null'

        return status

    # ========================================================================

    # Analysis functions

    def getHits(self, quiet=False):
        ''' Report the total number of results found in a json file. Updates the variable self.totalHits.

        Parameters
        ----------
        quiet: boolean
            if True nothing will be printed

        Returns
        -------
        Total number of results found in the json data, if found, otherwise returns -1


        '''

        # check if the json is valid
        s = self.getStatus()
        if s != 'ok':
            print('no hits - invalid json')
            return -1

        # Get the number of results
        h = self.jsonData['message']['total-results']
        self.stats['hits'] = h

        # print results
        if not(quiet):
            print(h, "events found")

        return h

    def displayEvents(self, n):
        '''

        Prints the first n events from a JSON file, or fewer if there wasn't that many events

        Displays the subject doi, object doi or URL and the relationship type

        Parameters
        ----------
        n : Int
            The number of events to display.

        Returns
        -------
        None

        '''

        # check if the json is valid
        s = self.getStatus()
        if s != 'ok':
            print('no events - invalid json')
            return -1

        # Check if n is more than the number of available events
        if n > len(self.jsonData["message"]["events"]):
            n = len(self.jsonData["message"]["events"])

        # Display the events
        for ev in range(n):

            # Get the relevant event from the data
            try:
                d = self.jsonData["message"]["events"][ev]
            except IndexError:
                break

            # line to output to the screen
            print("obj_id: " + d["obj_id"] + ", subj_id:" +
                  d["subj_id"] + ", relationship: " + d["relation_type_id"])

    def getFacets(self, quiet=True):
        ''' 

        Get facet data from the json file.

        Parameters
        ----------
        quiet: boolean (False)
            prints out the facets if True

        Returns
        -------
            dict:
                a dictionary containing facet data {facet1: value1, facet2: value2, ...}

        '''

        try:
            self.stats['facets'] = self.jsonData['message']['facets']
        except:
            print('no facets in json file')
            return

        if not(quiet):
            pprint.pprint(self.stats['facets'])

        return self.stats['facets']

    def searchEvents(self, field, value):
        '''
        Search events for some kind of characteristic. Matches if value is
        contained in the field, i.e. it matches substrings.

        Counts matches in the first and second level dictionaries (obj and subj), it doesn't
        distinguish between object and subject

        Parameters:
            field: String
                name of any field in an event (e.g. id, terms, obj_id)

            value: String
                value of a field to search for

        '''

        count = 0
        for ev in self.jsonData["message"]["events"]:

            dc = [ev]

            # add the object and subject so they're searched at the same time
            # as first level fields.
            try:
                dc.append(ev['obj'])
            except:
                pass
            try:
                dc.append(ev['subj'])
            except:
                pass

            # search top level fields, object and subject for the specified data
            for d in dc:
                if field in d:
                    if value in d[field]:
                        count += 1

        return count

    def filterEvents(self, mode="AND", useSubjs=False, useObjs=False, filters={}):
        '''
        filter all the events found by some criteria

        Parameters
        ----------

        mode:
            "AND", "OR" or "NOT", determines whether to match all or one of the conditions

        **kwargs : dict of lists
            in the format: {field : [value1, value2, ...]}
            will filter all events to find those where the dicionary key is field and the dictionary value is value1, value2,...

        Returns
        -------
        self.filteredEvents : eventRecord object
            Subset of self.eventData["message"]["items"] with events that match the criteria given

        '''

        # check if the json is valid
        s = self.getStatus()
        if s != 'ok':
            print('invalid json')
            return

        # Stop if the mode isn't correct
        if not(mode in ["AND", "OR", "NOT"]):
            print("Supply a valid mode for filtering")
            return

        # reset the filter
        self.filteredEvents = []

        # iterate events
        for event in self.jsonData["message"]["events"]:

            # populate a list with the event and possibly subdictionaries
            dc = [event]
            # case where objects are searched
            if useObjs:
                try:
                    dc.append(event['obj'])
                except:
                    pass
            # case where subjects are searched
            if useSubjs:
                try:
                    dc.append(event['subj'])
                except:
                    pass

            # Case where everything's got to match
            if mode == 'AND':

                # look through all fields
                found = True  # boolean to say we've found everything we've looked for so far
                for field in filters:

                    # look for all user-give values for this field
                    for value in filters[field]:
                        found_in_one_subdict = False

                        # look through the subdictionaries
                        for subdict in dc:
                            if self.dictValueCheck(subdict, field, value):

                                # value found!
                                found_in_one_subdict = True

                        if not(found_in_one_subdict):
                            found = False

                        # stop looking through the values
                        if not(found):
                            break

                    # stop looking through the fields (and move onto the next event)
                    if not(found):
                        break

                # if we've looked through all field and found something
                if found:
                    self.filteredEvents.append(event)

        # build a new instance with the filtered events as events
        jd = eventRecord()
        jd.jsonData = {"status": "ok", "message": {
            "total-results": len(self.filteredEvents), "events": self.filteredEvents}}
        jd.jsonLoadSuccess = True

        return jd

    def eventHist(self, field, bins=[], useObjs=False, useSubjs=False):
        '''
        Pool data from events based on field. Requires a json file to be loaded.

        Note that if the same item is found in multiple fields it will register all
        of them, e.g. for doi in the subject and object

        Parameters:
        -----------

        field: string
            field (dictionary key) on which to run the query

        bins: list of strings
            if provided, these are used as predefined keys for the output dictionary

        useObjs:
            look through the objects as well

        useSubjs:
            look through the subjects as well

        Returns:
        --------
        histData: dictionary of keys and integers
            the count of each key found in the data.


        '''

        # check if the json is valid
        s = self.getStatus()
        if s != 'ok':
            print('invalid json')
            return -1

        # Case where a list of values is provided by the user
        if len(bins) == 0:
            binBool = False
        else:
            binBool = True

        # ======================================

        # Initialise the output dictionary
        self.histData = {}
        # If necessary, add defined user values
        if binBool:
            for b in bins:
                self.histData[b] = 0

        # Iterate the loaded events
        for ev in self.jsonData["message"]["events"]:
            found = False  # was a match found?

            # populate a list with the event and possibly subdictionaries
            dc = [ev]
            # case where objects are searched
            if useObjs:
                try:
                    dc.append(ev['obj'])
                except:
                    pass
            # case where subjects are searched
            if useSubjs:
                try:
                    dc.append(ev['subj'])
                except:
                    pass

            # iterate the previous bins
            for b in self.histData:
                # check to see if the value can be found in the field
                for d in dc:
                    # Try and match the field with the bin value
                    if field in d:
                        if b in d[field]:
                            self.histData[b] += 1
                            found = True

            # add new bins in the case where the list of bins isn't predefined
            if (not(binBool)) & (not(found)):
                if field in ev:
                    # add a new item to the dictionary
                    self.histData[ev[field]] = 1

        # Output
        return self.histData

    def dictValueCheck(self, d, field, value):
        '''
        Check if a value is in a given field of a dictionary

        Parameters
        ----------
        d : dictionary
            Any dictionary.

        Returns
        -------
        boolean
            Was the value found in the field?

        '''

        if field in d:
            if value in d[field]:
                return True

            else:
                return False

        else:
            return False


if __name__ == '__main__':

    jr = eventRecord(filename="test.json")

    jr.displayEvents(20)
    jr.getHits()

    fl = {'source': ['twitter']}
    fe = jr.filterEvents()

    fe.getHits()

    hist = jr.eventHist('source_id')
    print(hist)

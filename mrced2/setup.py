#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 29 08:43:35 2020

@author: martynrittman
"""

from setuptools import setup

setup(name='mrced2',
      version='0.1',
      description='Build and run queries of the Crossref event data API',
      url='https://gitlab.com/crossref/event_data_notebooks',
      author='Martyn Rittman',
      author_email='mrittman@crossref.org',
      license='MIT',
      packages=['mrced2'],
      zip_safe=False)

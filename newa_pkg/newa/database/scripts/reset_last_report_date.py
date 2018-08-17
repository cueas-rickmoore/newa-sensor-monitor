#! /Volumes/projects/venvs/newa/bin/python

import os, sys

from datetime import datetime
import numpy as N

from rccpy.utils.timeutils import dateAsInt

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

year = int(args[0])
month = int(args[1])
day = int(args[2])
if len(args) > 3: hour = int(args[3])
else: hour = 23
max_report_date = dateAsInt((year, month, day))
max_report_time = (max_report_date * 100) + hour

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

factory = ObsnetDataFactory(options)

index_manager = factory.getFileManager('index', mode='r')
last_reports = index_manager.getData('last_report')
index_manager.closeFile()

for indx in range(len(last_reports)):
    last_report = last_reports[indx]
    if last_report == max_report_date:
        last_reports[indx] = max_report_time
    elif last_report > max_report_time:
        last_reports[indx] = max_report_time

factory.backupIndexFile()
index_manager = factory.getFileManager('index', mode='a')
index_manager.updateDataset('last_report', last_reports)
index_manager.closeFile()

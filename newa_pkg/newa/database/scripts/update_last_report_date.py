#! /Volumes/projects/venvs/newa/bin/python

import os, sys
from datetime import datetime

from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

from newa.factory import ObsnetDataFactory
from newa.database.sensors import latestReportDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-m', action='store_true', dest='missing_only', default=False)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

message = '%(network)s : %(sid)s : %(name)s : last report date changed from %(last_report)s to %(last)d'

debug = options.debug
missing_only = options.missing_only
test_run = options.test_run

today = datetime.now()
today = datetime(today.year, today.month, today.day, 23)
icao_base_time = today - ONE_DAY

# date is input, use it as the latest possible report date
if len(args) > 0:
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
    if len(args) > 3: newa_base_time = datetime(year, month, day, int(args[3]))
    else: newa_base_time = datetime(year, month, day, 23)
# otherwise, latest_possible report date is yesterday
else:
    newa_base_time = today - ONE_DAY

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

factory = ObsnetDataFactory(options)

index_manager = factory.getFileManager('index', mode='r')
datasets = index_manager.getData('datasets')
last_reports, last_report_attrs = index_manager.getData('last_report', True)
networks = index_manager.getData('network')
names = index_manager.getData('name')
sids = index_manager.getData('sid')
ucanids = index_manager.getData('ucanid')
index_manager.closeFile()
del index_manager

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

num_changed = 0

for station_index in range(len(sids)):

    # set up simple station dict for use in UCAN calls
    station = { 'datasets'    : datasets[station_index],
                'last_report' : last_reports[station_index],
                'name'        : names[station_index],
                'network'     : networks[station_index],
                'sid'         : sids[station_index],
                'ucanid'      : ucanids[station_index],
              }

    is_missing = last_reports[station_index] < 0
    if missing_only and not is_missing: continue

    print 'updating last report date for :\n', station
    last_report = latestReportDate(station,newa_base_time,icao_base_time,debug)

    # set last_reports to latest date found
    if last_report != last_reports[station_index]:
        last_reports[station_index] = last_report
        num_changed += 1
        station['last'] = last_report
        print message % station
        sys.stdout.flush()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if num_changed > 0 and not test_run:
    backup_filepath = factory.backupIndexFile()
    print 'Index file backed up to', backup_filepath

    print 'Last report date will be updated for %d stations.' % num_changed
    manager = factory.getFileManager('index', mode='a')
    manager.replaceDataset('last_report', last_reports, last_report_attrs)
    manager.closeFile()
    print 'Station index file has been updated.'
    print factory.getFilepath('index')


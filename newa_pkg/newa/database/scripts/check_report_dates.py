#! /Volumes/projects/venvs/newa/bin/python

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

from rccpy.utils.timeutils import dateAsInt

from newa.factory import ObsnetDataFactory
from newa.database.sensors import latestReportDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('--bbox', action='store', type='string', dest='bbox',
                  default=None)
parser.add_option('--county', action='store', type='string', dest='county',
                  default=None)
parser.add_option('--name', action='store', type='string', dest='name',
                  default=None)
parser.add_option('--network', action='store', type='string', dest='network',
                  default=None)
parser.add_option('--sid', action='store', type='string', dest='sid',
                  default=None)
parser.add_option('--state', action='store', type='string', dest='state',
                  default=None)

parser.add_option('-d', action='store_true', dest='detailed', default=False)
parser.add_option('-m', action='store', type='string', dest='metadata',
                  default='sid,name,network,datasets,first_hour,last_report')
parser.add_option('-s', action='store', type='string', dest='sort_by',
                  default='name')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test_index', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

message = '%(state)s : %(network)s : %(sid)s : %(name)s : last reported %(last)d vs %(last_report)d'
test_msg = '%(state)s : %(network)s : %(sid)s : %(name)s : last reported %(last_report)d'

debug = options.debug
test_index = options.test_index

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
test_last_day = dateAsInt(newa_base_time)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

criteria = ('bbox','county','name','network','sid','state')
factory = ObsnetDataFactory(options)
criteria = factory._validCriteria(options, criteria)
metadata = list(factory._parseMetadata(options.metadata))
if 'datasets' not in metadata: metadata.append('datasets')
if 'first_hour' not in metadata: metadata.append('first_hour')
if 'last_report' not in metadata: metadata.append('last_report')
if 'name' not in metadata: metadata.append('name')
if 'sid' not in metadata: metadata.append('sid')
if 'state' not in metadata: metadata.append('state')
if 'ucanid' not in metadata: metadata.append('ucanid')

for station in factory.getIndexedStations(metadata, criteria, options.sort_by):
    if test_index:
        prev_last_report = station['last_report']
        prev_last_day = prev_last_report / 100
        if prev_last_day != test_last_day:
            print test_msg % station
    else:
        last_report = latestReportDate(station, newa_base_time, icao_base_time,
                                       debug)
        station['last'] = last_report
        if not debug:
            station['last'] = last_report
            last_day = last_report / 100
            prev_last_report = station['last_report']
            prev_last_day = prev_last_report / 100
            if last_day != prev_last_day: print message % station
        else: print message % station
    sys.stdout.flush()


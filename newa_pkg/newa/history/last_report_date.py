#! /Users/rem63/venvs/nrcc_prod/bin/python

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta

import numpy as N

from rccpy.utils.exceptutils import reportLastException
from rccpy.utils.report import Reporter
from rccpy.utils.timeutils import dateAsInt

from newa.ucan import HourlyDataConnection
from newa.validation import PhysicalLimitsValidator

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config as CONFIG
from newa.factory import RAW_DATA_ELEMENTS

ONE_DAY = relativedelta(days=1)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('--date', action='store', type='string', dest='date',
                  default=None)
parser.add_option('--mail_to', action='store', type='string', dest='mail_to',
                  default='rem63@cornell.edu')

parser.add_option('-d', action='store', type='string', dest='dump_filepath',
                  default='last_report_dump.py')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

test_run = options.test
if test_run: debug = True
else: debug = options.debug

dump_filepath = os.path.normpath(options.dump_filepath)

if len(args) > 0:
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
    if len(args) > 3: first_hour_in_day = int(args[3])
    base_time = datetime(year, month, day, 1)
else:
    date = datetime.now() - relativedelta(days=1)
    base_time = datetime(date.year, date.month, date.day, 23)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

bad_station = '\n%(network)s station %(ucanid)d : %(sid)s : %(name)s'
missing_data = 'No data reported on %s : last report date is %s'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

factory = ObsnetDataFactory(options)
stations = factory.getIndexedStations('all')
num_stations = len(stations)

for station in stations:
    ucanid = station['ucanid']
    if debug: print '%(ucanid)d : %(sid)s : %(name)s' % station

    raw_elements = [name for name in station['elements'].split(',') if name]
    raw_elements.sort()
    num_elements = len(raw_elements)
    if debug: print num_elements, raw_elements

    # make connection to UCAN server
    connection = HourlyDataConnection(2, first_hour_in_day=1)
    
    end_time = base_time
    start_time = end_time - relativedelta(hours=23)

    invalid = True
    while invalid:
        missing = [ ]

        for element in raw_elements:
            #if debug: print '\nelement', element
            first_hour, last_hour, data = \
                connection.getData(station,element,start_time,end_time,debug)
            num_hours = len(data)
            if num_hours == 24 and len(N.where(N.isfinite(data))[0]) > 0:
                station['last_report'] = dateAsInt(start_time)
                invalid = False
                break

        end_time -= ONE_DAY
        start_time -= ONE_DAY

dump_file = open(dump_filepath, 'w')
dump_file.write(repr(stations[0]))
for station in stations[1:]:
    dump_file.write('\n')
    dump_file.write(repr(station))
dump_file.close()


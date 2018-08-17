#! /Volumes/projects/venvs/newa/bin/python

import os, sys
from datetime import datetime

from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

from rccpy.utils.timeutils import asDatetime

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

parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

separator = 72 * '*'
message = '%(num_days)4d days ago : %(active)s : %(name)s (%(sid)s) last reported on %(last_hour)s'

debug = options.debug
test_run = options.test_run

today = datetime.now()
base_time = today - ONE_DAY

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

metadata = ['sid','name','active','network','last_report']

if options.bbox is not None:
    metadata.append('lat')
    metadata.append('lon')
if options.county is not None: metadata.append('county')
if options.state is not None: metadata.append('state')

factory = ObsnetDataFactory(options)
stations = factory.argsToStationData((), options, tuple(metadata))
stations = sorted(stations, key=lambda station : station['name'])

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

verified_stations = [ ]

print '\n Active Stations\n%s' % separator
for station in stations:
    last_hour = asDatetime(station['last_report'], True)
    station['last_hour'] = last_hour.strftime('%b %d, %Y at %I %p')
    delta = base_time - last_hour
    station['num_days'] = delta.days
    verified_stations.append(station)

stations = sorted(verified_stations, key=lambda station : station['num_days'])

for station in stations:
    print message % station


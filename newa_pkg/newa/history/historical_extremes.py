#! /Users/rem63/venvs/nrcc_prod/bin/python

import os, sys

from rccpy.utils.exceputils import reportLastException

from newa.history import historicalExtremes
from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

APP = os.path.split(sys.argv[0])[1]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# station search criteria
parser.add_option('--bbox', action='store', type='string', dest='bbox',
                  default=None)
parser.add_option('--county', action='store', type='string', dest='county',
                  default=None)
parser.add_option('--sid', action='store', type='string', dest='sid',
                  default=None)
parser.add_option('--network', action='store', type='string',
                  dest='network', default=None)
parser.add_option('--state', action='store', type='string', dest='state',
                  default=None)

parser.add_option('-e', action='store', type='string', dest='elements',
                  default='all')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-x', action='store_true', dest='replace_existing',
                  default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

procmsg = '\nProcessing station %d of %d : %d : %s (%s)' 
skipmsg = '\nSkipping station %d of %d : %d : %s (%s)' 

debug = options.debug
replace_existing = options.replace_existing

factory = ObsnetDataFactory(options)
stations = factory.argsToStationData(args, options, 'all')
total_stations = len(stations)

station_num = 0
for station in stations:
    if 'id' in station:
        station['sid'] = station['id']
        del station['id']
    ucanid = station['ucanid']
    station_id = station['sid']
    station_name = station['name']
    station_num += 1

    # hourly data file must already exist
    filepath = factory.getFilepathForUcanid(ucanid, 'hours')
    if not os.path.exists(filepath):
        print skipmsg % (station_num, total_stations, ucanid,
                         station_id, station_name)
        errmsg = 'Hourly data file for station %d does not exist : %s' 
        print errmsg % (ucanid, filepath)
        continue

    if replace_existing:
        stats_filepath = factory.getFilepathForUcanid(ucanid, 'statistics')
        if os.path.exists(stats_filepath): os.remove(stats_filepath)

    # we're going to process this station
    print procmsg % (station_num, total_stations, ucanid, station_id,
                     station_name)

    try:
        historicalExtremes(factory, ucanid, options.elements, debug)
    except:
        reportLastException(APP)
        os._exit(1)

    sys.stdout.flush()
    sys.stderr.flush()


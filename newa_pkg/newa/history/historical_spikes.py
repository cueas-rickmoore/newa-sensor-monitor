#! /Users/rem63/venvs/nrcc_prod/bin/python

import os, sys

from rccpy.utils.options import stringToTuple
from rccpy.utils.exceptutils import reportLastException

from newa.history import historicalSpikes
from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

APP = os.path.split(sys.argv[0])[1]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-e', action='store', type='string', dest='elements',
                  default='all')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-x', action='store_true', dest='replace_existing',
                  default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

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

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

procmsg = '\nProcessing station %d of %d : %d : %s (%s)' 
skipmsg = '\nSkipping station %d of %d : %d : %s (%s)' 

debug = options.debug
elements = options.elements
if elements != 'all': elements = stringToTuple(elements)
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

    # open spike log file
    if not debug:
        log_filepath = factory.getFilepathForUcanid(ucanid, 'spikes')
        log_file = open(log_filepath, 'wt')
    else: log_file = None

    # we're going to process this station
    announce = procmsg % (station_num, total_stations, ucanid,
                          station_id, station_name)
    print announce
    if log_file: log_file.write(announce)

    try:
        historicalSpikes(factory, ucanid, elements, log_file, debug)
    except:
        reportLastException(APP)
        os._exit(1)

    if log_file:
        log_file.close()
        msg =  'Created spike log file for %s at %s'
        print msg % (station_name, log_filepath)
    sys.stdout.flush()
    sys.stderr.flush()


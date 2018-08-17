#! /Volumes/projects/venvs/newa/bin/python

import os, sys

from rccpy.utils.exceptutils import captureLastException
from rccpy.utils.options import stringToTuple
from rccpy.utils.timeutils import dateAsInt

from newa.buddies import BuddyLocator
from newa.history import historicalExtremes
from newa.history import historicalSequences
from newa.history import historicalSpikes

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
# global options
parser.add_option('-d', action='store', type='string', dest='datasets',
                  default='all')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-x', action='store_true', dest='replace_existing',
                  default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

# statistic-specific options
parser.add_option('--bmd', action='store', type='int', default=1.0,
                  dest='max_buddy_distance')
parser.add_option('--bmx', action='store', type='int', dest='max_buddies',
                  default=5)
parser.add_option('--bmy', action='store', type='int', dest='min_buddy_years',
                  default=15)
parser.add_option('--mrn', action='store', type='int', dest='min_run_length',
                  default=2)
parser.add_option('--rm', action='store_true', dest='report_missing',
                  default=False)
parser.add_option('--sc', action='store', type='int',
                   dest='sequence_count_cutoff',
                   default=CONFIG.sequences.min_count_cuttoff)

# station search criteria
parser.add_option('--bbox', action='store', type='string', dest='bbox',
                  default=None)
parser.add_option('--county', action='store', type='string', dest='county',
                  default=None)
parser.add_option('--sid', action='store', type='string', dest='sid',
                  default=None)
parser.add_option('--network', action='store', type='string', dest='network',
                  default=None)
parser.add_option('--state', action='store', type='string', dest='state',
                  default=None)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

procmsg = '\nProcessing station %d of %d : %d : %s (%s)' 
skipmsg = '\nSkipping station %d of %d : %d : %s (%s)' 

debug = options.debug
replace_existing = options.replace_existing
report_missing = options.report_missing
seq_count_cutoff = options.sequence_count_cutoff
if options.datasets != 'all':
    datasets = list(stringToTuple(options.datasets))
else: datasets = None

factory = ObsnetDataFactory(options)
stations = factory.argsToStationData(args, options)
total_stations = len(stations)

buddy_locator = BuddyLocator(factory, options.min_buddy_years,
                             options.max_buddies, options.max_buddy_distance)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

exceptions_encountered = [ ]

station_num = 0
for station in stations:
    ucanid = station['ucanid']
    station_id = station['sid']
    station_name = station['name']
    if options.datasets == 'all': datasets = station['datasets']
    station_num += 1

    # hourly data file must already exist
    filepath = factory.getFilepathForUcanid(ucanid, 'hours')
    if not os.path.exists(filepath):
        print skipmsg % (station_num, total_stations, ucanid, station_id,
                         station_name)
        errmsg = 'Hourly data file for station %d does not exist : %s' 
        print errmsg % (ucanid, filepath)
        continue # gotta quit if there is no hourly data
    else:
        filepath = factory.getFilepathForUcanid(ucanid, 'statistics')
        if os.path.exists(filepath):
            if not replace_existing:
                print skipmsg % (station_num, total_stations, ucanid,
                                 station_id, station_name)
                errmsg = 'Statistics database for station %d already exists : %s' 
                print errmsg % (ucanid, filepath)
                continue
            else: os.remove(filepath)
        # create a new statistics file and initialize with station attributes
        if not os.path.exists(filepath):
            manager = factory.getFileManager((ucanid,'hours'),mode='r')
            attrs = manager.getFileAttributes()
            manager.closeFile()
            manager = factory.getFileManager((ucanid,'statistics'),mode='w')
            manager.setFileAttributes(**attrs)
            manager.closeFile()
            del manager

        # we're going to process this station
        announce = procmsg % (station_num, total_stations, ucanid,
                              station_id, station_name)
        print announce

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    if debug: print 'historical extremes for %d' % ucanid

    try:
        historicalExtremes(factory, ucanid, datasets, debug)
    except:
        where = 'historicalExtremes for station %d' % ucanid
        exception_type, formatted, details = captureLastException()
        if debug:
            print where
            print exception_type
            if details is not None: print details
            print ''.join(formatted)
            os._exit(99)
        else:
            exceptions_encountered.append((where,exception_type,formatted,details))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    if not debug: # open sequence log file
        log_filepath = factory.getFilepath((ucanid,'sequences'))
        log_file = open(log_filepath, 'wt')
        log_file.write(announce)
    else:
        log_file = None
        print 'sequence history for %d' % ucanid

    try:
        historicalSequences(factory, ucanid, datasets, options.report_missing,
                            log_file, options.min_run_length, debug)
    except:
        where = 'historicalSequences for station %d' % ucanid
        exception_type, formatted, details = captureLastException()
        if debug:
            print where
            print exception_type
            if details is not None: print details
            print ''.join(formatted)
            os._exit(99)
        else:
            exceptions_encountered.append((where,exception_type,formatted,details))
    else:
        if log_file:
            log_file.close()
            msg =  'Created sequence log file for %s at %s'
            print msg % (station_name, log_filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    if not debug: # open spike log file
        log_filepath = factory.getFilepath((ucanid,'spikes'))
        log_file = open(log_filepath, 'wt')
        log_file.write(announce)
    else:
        log_file = None
        print 'spike history for %d' % ucanid

    try:
        historicalSpikes(factory, ucanid, datasets, log_file, debug)
    except:
        where = 'historicalSpikes for station %d' % ucanid
        exception_type, formatted, details = captureLastException()
        if debug:
            print where
            print exception_type
            if details is not None: print details
            print ''.join(formatted)
            os._exit(99)
        else:
            exceptions_encountered.append((where,exception_type,formatted,details))
    else:
        if log_file:
            log_file.close()
            msg =  'Created spike log file for %s at %s'
            print msg % (station_name, log_filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    if debug: print 'locate buddies for %d' % ucanid

    try:
        num_buddies =\
        buddy_locator.findAndSave(station['ucanid'], station['lon'],
                                  station['lat'],
                                  dateAsInt(station['first_hour']),
                                  dateAsInt(station['last_report']))
    except:
        where = 'buddy locator for station %d' % ucanid
        exception_type, formatted, details = captureLastException()
        if True: #debug:
            print where
            print exception_type
            if details is not None: print details
            print ''.join(formatted)
            os._exit(99)
        else:
            exceptions_encountered.append((where,exception_type,formatted,details))
    else:
        print '    %d buddies found for %d' % (num_buddies, ucanid)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    sys.stdout.flush()
    sys.stderr.flush()


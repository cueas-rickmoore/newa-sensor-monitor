#! /Volumes/projects/venvs/newa/bin/python

import os, sys
from datetime import datetime

import numpy as N

from rccpy.hdf5.manager import HDF5DataFileManager

from newa.factory import ObsnetDataFactory
from newa.database.index import getDictTemplate
from newa.database.utils import readSpreadsheetFile, downloadMetadata
from newa.database.utils import writeStationsToFile, getStateName

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config as CONFIG
META_DOWNLOAD = CONFIG.metadata.download
MUTABLE_DATASETS = CONFIG.metadata.mutable
NULLABLE_DATASETS = CONFIG.metadata.nullable

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# define input options

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-b', action='store_false', dest='backup', default=True)
parser.add_option('-c', action='store', type='string', dest='columns',
                  default=None)
parser.add_option('-l', action='store_false', dest='live_download',
                  default=True)
parser.add_option('-s', action='store', type='string', dest='states',
                  default=None)
parser.add_option('-t', action='store', type='string', dest='tab_labels',
                  default=None)
parser.add_option('-u', action='store', type='string', dest='root_url',
                  default=META_DOWNLOAD.root_url)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# interpret input options

if len(args) == 3:
    download_date = datetime(int(args[0]), int(args[1]), int(args[2]))
else: download_date = datetime.now()

create_backup = options.backup
live_download = options.live_download

# default labels for files where first row does not contain column labels
default_tabs = options.tab_labels
if default_tabs is None:
    default_tabs = META_DOWNLOAD.tab_labels
else:
    if ',' in default_tabs:
        default_tabs = tuple( [ label.strip()
                                for label in default_tabs.split(',') ] )
    else:
        errmsg = 'Value of input option -t is invalid : %s' % default_tabs
        raise ValueError, errmsg

# root URL for metadata download file
root_url = options.root_url

# list of states to update
states = options.states
if states is None:
    states = CONFIG.metadata.states
else:
    if ',' in states:
        states = tuple([state.strip().upper() for state in states.split(',')])
    elif len(states) == 2:
        states = (states.upper(),)
    else:
        errmsg = 'Value of input option -s is invalid : %s' % states
        raise ValueError, errmsg
last_state = states[-1]

# creat a factory instance and get directory/file paths
factory = ObsnetDataFactory(options)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

date_str = download_date.strftime('%Y%m%d')
time_str = datetime.now().strftime('%y%m%d.%H%M')

debug = options.debug

# get path to station index file
index_filepath = factory.getFilepath('index')
if not os.path.exists(index_filepath):
    raise IOError, 'Station index file not accessable : %s' % index_filepath

# make a backup copy of index file
if create_backup: factory.backupIndexFile()

# get log directory path
log_dirpath = os.path.join(factory.getDirectoryPath('working'), 'updates')
if not os.path.exists(log_dirpath):
    os.makedirs(log_dirpath)

# get file path for change log
change_log_name = '%s_changes.log' % time_str
change_log_path = os.path.join(log_dirpath, change_log_name)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# get 'sid' dataset from index file
manager = factory.getFileManager('index', mode='r')
sids = manager.getData('sid')
all_datasets = manager.listDatasets()

index_map = dict([(enum[1],enum[0]) for enum in enumerate(sids)])
manager.closeFile()
del sids

# track new stations
new_stations = [ ]
first_state = states[0]
last_state = states[-1]

change_log = None
change_log_empty=True

# loop thru state by state
for state in states:
    if debug:
        print '\n\n-----------------------------------------------------------'
        print state
    if state is not "Other":
        state_name = getStateName(state)
    else: state_name = "Other"
    if debug: print 'checking for updates in', state_name 

    if live_download:
        # download metadata for stations in this state
        stations = downloadMetadata(root_url, state, date_str, debug=debug)
    else:
        # check for download file
        template_dict = {'date':date_str, 'state':state}
        filename = META_DOWNLOAD.dest_tmpl % template_dict
        download_filepath = os.path.join(index_filepath, 'downloads', filename)
        if os.path.exists(download_filepath):
            stations = readSpreadsheetFile(filepath, '\t')
        else: continue

    if stations is None: continue

    # sort stations by sid so it will be easier to find them in the log files
    stations = sorted(stations, key=lambda station: station['sid'])

    # look for differences and apply changes
    change_counter = 0

    manager.openFile(mode='a')

    for station in stations:
        if debug: print '\n', station

        # ignore stations with no 'sid' - they are either errors or 
        # placeholders for new stations yet to be integrated into ACIS
        if len(station['sid']) < 2: continue

        stn_index = index_map.get(station['sid'], None)
        if stn_index is None:
            if state is not 'Other': station['state'] = state
            else: station['state'] = station['sid'].split('_')[0].upper()
            new_stations.append(station)
        else:
            sid = station['sid']

            before = { }
            after = { }

            active = station.get('active', None)
            if active:
                if len(station['active']) == 1:
                    station['active'] = station['active'].upper()
                else: station['active'] = station['active'].upper()[0]
            else:
                print '\nStation has no value for "active"'
                print station
                continue

            for name, meta_value in station.items():
                # skip immutable data 
                if name not in MUTABLE_DATASETS: continue

                current_value = manager.hdf5_file[name][stn_index]

                if name not in NULLABLE_DATASETS:
                    # don't erase and don't change if not different
                    if meta_value and meta_value != current_value:
                        before[name] = current_value
                        #TODO: make sure to deserialize new value
                        manager.hdf5_file[name][stn_index] = meta_value
                        after[name] = meta_value
                else: # OK to set to NULL
                    # change only when different
                    if meta_value != current_value:
                        before[name] = current_value
                        #TODO: make sure to deserialize new value
                        manager.hdf5_file[name][stn_index] = meta_value
                        after[name] = meta_value

            if after:
                tmpl = getDictTemplate(after.keys())

                if change_log is None:
                    change_log = open(change_log_path, 'a')
                if change_log_empty:
                    change_log.write('[')
                    change_log_empty = False

                if change_counter == 0:
                    if state != first_state: change_log.write(',\n')
                    change_log.write('{"state":"%s","stations":[' % state)
                change_counter += 1

                if change_counter > 1: change_log.write(',')
                change_log.write('\n{"sid":"%s",' % sid)
                change_log.write('\n       "before":%s,' % (tmpl % before))
                change_log.write('\n       "after":%s}' % (tmpl % after))

    # save changes for state
    manager.closeFile()

    if change_log is not None:
        change_log.write('\n]}')
        if state == last_state: change_log.write('\n]')
        change_log.close()
        change_log = None

# save new stations
if new_stations:
    # file path for new station log
    new_station_file = '%s_new.log' % time_str
    new_station_file_path = os.path.join(log_dirpath, new_station_file)
    # write new stations as dump file
    writeStationsToFile(new_stations, new_station_file_path, 'dump', 'w')
    print '%d new stations saved to file %s' % (len(new_stations),
                                                new_station_file_path)
    fmt = '%(active)s : %(state)s : %(sid)s : %(name)s' 
    for station in new_stations:
        if station['active'] == 'Y': station['active'] == 'Add'
        print fmt % station


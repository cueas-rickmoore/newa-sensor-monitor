#! /Volumes/projects/venvs/newa/bin/python

import os, sys
from datetime import datetime

import numpy as N

from newa.factory import ObsnetDataFactory
from newa.ucan import updateWithUcanMetadata

from newa.database.index import getDictTemplate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.database.index import INDEX
MISSING = { }
for key in INDEX.keys():
    MISSING[key] = INDEX[key].missing

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-a', action='store_false', dest='must_be_active',
                  default=True)
parser.add_option('-s', action='store', type='string', dest='sort_by',
                  default='name')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

factory = ObsnetDataFactory(options)

update_log_filepath = os.path.normpath(args[0])
if not os.path.isfile(update_log_filepath):
    dirpath = factory.getDirectoryPath('updates')
    update_log_filepath = os.path.join(dirpath, args[0])
if not os.path.isfile(update_log_filepath):
    raise IOError, "Log file not found : %s" % update_log_filepath

debug = options.debug
must_be_active = options.must_be_active
sort_by = options.sort_by
verbose = debug or options.verbose

# get all stations currently in the index file
manager = factory.getFileManager('index','r')
column_names = manager.listDatasets()
column_created = { } # original creation date of column
for name in column_names:
    column_created[name] = manager.getDatasetAttribute(name, 'created')
num_columns = len(column_names)
stations = list(factory.getIndexedStations(column_names, None, sort_by))
manager.closeFile()
del manager

print '%d stations curently in the index' % len(stations)
new_stations = [ ]

# read the log file
update_log_file = open(update_log_filepath, 'r')
line = update_log_file.readline()
while line:
    station = eval(line.strip())
    # station must be active before it gets in
    if not ('active' in station and station['active'] == 'Yes'):
        print 'station %(sid)s : %(name)s is not active' % station
        line = update_log_file.readline()
        continue

    # need to delete any extra data items
    useful_keys = [ ]
    for key in station:
        if key in column_names: useful_keys.append(key)
        else: del station[key]

    # try to fill in any empty columns with data from ACIS/UCAN
    if len(useful_keys) < num_columns:
        try:
            station = updateWithUcanMetadata(station)
        except KeyError, e:
            print 'ERROR :', str(e)

    for name in column_names:
        if name not in station: station[name] = MISSING[name]

    # check to make sure the station has datasets
    if not ('datasets' in station and station['datasets']):
       print 'station %(sid)s : %(name)s has no datasets' % station
       line = update_log_file.readline()
       continue

    # make sure the station is actually reporting
    if station['last_report'] != -32768:
        print 'station %(sid)s : %(name)s will be added to index' % station
        new_stations.append(station)
    else: print 'station %(sid)s : %(name)s has never reported' % station

    line = update_log_file.readline()

update_log_file.close()

if len(new_stations) == 0:
    print 'no new stations were dded to the index'
    os._exit(0)
print '%d new stations will be added to index' % len(new_stations)

# add new stations and re-sort
stations.extend(new_stations)
stations = sorted(stations, key=lambda station: station[sort_by])
num_stations = len(stations)
print 'new index will contain %d stations' % num_stations

# fill the column list with data from each station
columns = dict([(name, [ ]) for name in column_names])
for station in stations:
    for name in column_names:
        columns[name].append(station[name])

# make sure that all of the new columns are the correct length
for name, data in columns.items():
    if len(data) != num_stations:
        errmsg = '%s column has %d entries, but there are %d stations'
        raise RuntimeError, errmsg % (name, len(data), num_stations)

# backup the existing index file
index_filepath, backup_filepath = factory.backupIndexFile(keep_original=False)

time_str = datetime.now().strftime('%y%m%d.%H%M')
# create a new version of the index file that contains valid stations
# from the log file
manager = factory.getFileManager('index','w')
update_time = manager._timestamp()
for name, data in columns.items():
    attrs = { 'created' : column_created[name],
              'updated' : update_time,
              'description' : INDEX[name].description,
              'missing' : MISSING[name],
            }
    units = INDEX[name].units
    if units: attrs['units'] = units

    dtype = INDEX[name].data_type
    if verbose: print 'adding "%s" dataset to the index file' % name
    manager.createDataset(name, N.array(data, dtype=dtype), attrs)
manager.closeFile()

# get log directory path
log_dirpath = os.path.join(factory.getDirectoryPath('working'), 'updates')
if not os.path.exists(log_dirpath):
    os.makedirs(log_dirpath)
# get file path for change log
change_log_name = '%s_added.log' % time_str
change_log_path = os.path.join(log_dirpath, change_log_name)

change_log = open(change_log_path, 'a')
station = new_stations[0]
change_log.write(getDictTemplate(station) % station)
if new_stations > 1:
    for station in new_stations[1:]:
        change_log.write('\n')
        change_log.write(getDictTemplate(station) % station)
change_log.close()


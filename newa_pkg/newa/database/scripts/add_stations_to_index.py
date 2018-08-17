#! /Volumes/projects/venvs/newa/bin/python

import os, sys

import numpy as N

from newa.factory import ObsnetDataFactory
from newa.database.utils import readDumpFile

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.database.index import INDEX
MISSING = { }
for key in INDEX.keys():
    MISSING[key] = INDEX[key].missing

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-f', action='store', type='string', dest='file_fmt',
                  default='dump')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-s', action='store', type='string', dest='sort_by',
                  default='name')
parser.add_option('-y', action='store_true', dest='test', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

factory = ObsnetDataFactory(options)

if os.path.isfile(os.path.normpath(args[0])):
    dump_filepath = os.path.normpath(args[0])
else:
    dirpath = factory.getDirectoryPath('updates')
    dump_filepath = os.path.join(dirpath, args[0])

file_fmt = options.file_fmt
sort_by = options.sort_by

# get all stations currently in the index file
manager = factory.getFileManager('index','r')
column_names = manager.listDatasets()
column_created = { }
columns = { }
for name in column_names:
    column_created[name] = manager.getDatasetAttribute(name, 'created')
    columns[name] = [ ]
stations = list(factory.getIndexedStations(column_names, None, sort_by))
manager.closeFile()
del manager

# read the dump file and add the new stations to the list
stations.extend(list(readDumpFile(dump_filepath)))
# then sort the new station list
stations = sorted(stations, key=lambda station: station[sort_by])
num_stations = len(stations)

for station in stations:
    for name in column_names:
        columns[name].append(station.get(name, MISSING[name]))
del stations

# backup the index file
index_filepath = factory.getFilepath('index')
backup_filepath = factory._backupFilePath(index_filepath)
os.rename(index_filepath, backup_filepath)
if os.path.isfile(backup_filepath):
    print 'Index backed up to', backup_filepath
else:
    print 'ERROR : could not complete backup to', backup_filepath
    os._exit(99)

manager = factory.getFileManager('index','w')
update_time = manager._timestamp()
for name, data in columns.items():
    if len(data) != num_stations:
        errmsg = '%s dataset has %d entries, but there are %d stations'
        raise RuntimeError, errmsg % (name, len(data), num_stations)

    attrs = { 'created' : column_created[name],
              'updated' : update_time,
              'description' : INDEX[name].description,
              'missing' : MISSING[name],
            }
    units = INDEX[name].units
    if units: attrs['units'] = units

    dtype = INDEX[name].data_type
    manager.createDataset(name, N.array(data, dtype=dtype), attrs)
manager.closeFile()


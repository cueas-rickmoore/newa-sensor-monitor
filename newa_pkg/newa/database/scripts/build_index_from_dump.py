#! /Volumes/projects/venvs/newa/bin/python

import os
from datetime import datetime

import numpy as N

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.database.index import INDEX, getDictTemplate
INDEX_KEYS = INDEX.keys()
MISSING = dict(zip(INDEX_KEYS, [INDEX[key].missing for key in INDEX_KEYS]))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-s', action='store', type='string', dest='sort_by',
                  default='name')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# read the dump file with all stations to be placed in the index
dump_filepath = os.path.abspath(args[0])
dump_file = open(dump_filepath,'r')
stations = eval(dump_file.read())
dump_file.close()
stations = sorted(stations, key=lambda station: station[options.sort_by])

# create the index array dictionary
arrays = { }
for key in INDEX_KEYS:
    arrays[key] = [ ]

# populate the index arrays with station data
for station in stations:
    for key in INDEX_KEYS:
        if key in station:
            arrays[key].append(station[key])
        else:
            arrays[key].append(MISSING[key])

# save the index arrays to the index file
factory = ObsnetDataFactory(options)
if factory.fileExists('index'): factory.backupIndexFile()

index_manager = factory.getFileManager('index', mode='w')
for key, dataset in INDEX.items():
    print 'creating array for', key
    data = N.array(arrays[key], dtype=dataset.data_type)
    attrs = { 'missing' : dataset.missing,
              'description' : dataset.description,
            }
    if key in ('lon','lat','elev'):
        valid = data[N.where(N.isfinite(data))]
        attrs['min'] = N.min(valid)
        attrs['max'] = N.max(valid)

    if dataset.units is not None: attrs['units'] = dataset.units

    index_manager.createDataset(key, data, attrs)

print 'Created index file', index_manager.hdf5_filepath
index_manager.closeFile()

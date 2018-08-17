#! /Volumes/projects/venvs/newa/bin/python

import os, sys

import numpy as N

from newa.factory import ObsnetDataFactory
from newa.ucan import updateWithUcanMetadata
from newa.database.utils import readDumpFile

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.database.index import INDEX
INDEX_COLUMNS = INDEX.keys()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-o', action='store', type='string', dest='output_filepath',
                  default='merge_dump_files_output.py')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

input_filepaths = [ ]
for arg in args:
    input_filepaths.append(os.path.normpath(arg))

stations = [ ]
station_ids = [ ]
index_dict = { }

for input_filepath in input_filepaths:
    for station in readDumpFile(input_filepath):

        # make sure not to add any new data columns
        for key in station:
            if key not in INDEX_COLUMNS: del station[key]

        # update existing station
        sid = station['sid']
        if sid in station_ids:
            stations[index_dict[sid]].update(station)
        # add new station
        else:
            try:
                station = updateWithUcanMetadata(station)
            except KeyError, e:
                print 'ERROR :', str(e)
            else:
                for key in INDEX_COLUMNS:
                    if key not in station: station[key] = INDEX[key].missing
                index_dict[sid] = len(station_ids)
                stations.append(station) 
                station_ids.append(sid)

# sort stations by sid
stations = sorted(stations, key=lambda station: station['sid'])

# dump merged stations to a file
filepath = os.path.abspath(options.output_filepath)
writeStationsToFile(stations, filepath, fmt='dict', mode='w')
print 'merged dumps saved to file :', filepath


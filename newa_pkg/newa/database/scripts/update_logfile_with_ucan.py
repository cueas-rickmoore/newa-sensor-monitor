#! /Volumes/projects/venvs/newa/bin/python

import os, sys

import numpy as N

from newa.factory import ObsnetDataFactory
from newa.ucan import updateWithUcanMetadata
from newa.database.utils import readDumpFile, writeStationsToFile

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.database.index import INDEX
INDEX_COLUMNS = INDEX.keys()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-o', action='store', type='string', dest='output_filepath',
                  default=None)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if os.path.isfile(os.path.normpath(args[0])):
    input_filepath = os.path.normpath(args[0])
    dirpath, filename = os.path.split(input_filepath)
else:
    factory = ObsnetDataFactory(options)
    dirpath = factory.getDirectoryPath('updates')
    filename = args[0]
    input_filepath = os.path.join(dirpath, filename)

if options.output_filepath is None:
    output_filepath = '%s.dump' % os.path.splitext(input_filepath)[0]
else: output_filepath = os.path.abspath(option.output_filepath)

stations = [ ]
station_ids = [ ]
index_dict = { }

for station in readDumpFile(input_filepath):

    # make sure not to add any new data columns
    for key in station:
        if key not in INDEX_COLUMNS: del station[key]

    try:
        station = updateWithUcanMetadata(station)
    except KeyError, e:
        print 'ERROR :', str(e)
    else:
        for key in INDEX_COLUMNS:
            if key not in station: station[key] = INDEX[key].missing
        stations.append(station) 

# sort stations by sid
stations = sorted(stations, key=lambda station: station['sid'])

# dump merged stations to a file
writeStationsToFile(stations, output_filepath, fmt='dump', mode='w')
print 'merged dumps saved to file :', output_filepath


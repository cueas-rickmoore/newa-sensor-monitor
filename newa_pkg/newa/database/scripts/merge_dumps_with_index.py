#! /Volumes/projects/venvs/newa/bin/python

import os, sys

import numpy as N

from newa.factory import ObsnetDataFactory
from newa.ucan import updateWithUcanMetadata

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.database.index import INDEX, getDictTemplate
INDEX_KEYS = INDEX.keys()
MISSING = dict(zip(INDEX_KEYS, [INDEX[key].missing for key in INDEX_KEYS]))
STATION_TEMPLATE = getDictTemplate()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-o', action='store', type='string', dest='output_filepath',
                  default='merge_dumps_with_index_output.py')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

input_filepaths = [ ]
for arg in args:
    input_filepaths.append(os.path.normpath(arg))

factory = ObsnetDataFactory(options)
stations = list(factory.getIndexedStations('all'))
index_dict = dict( [ (station['sid'], indx)
                     for (indx, station) in enumerate(stations) ] )
station_ids = list(index_dict.keys())

for input_filepath in input_filepaths:
    input_file = open(input_filepath, 'r')
    dump_stations = eval(input_file.read())
    input_file.close()

    new_stations = [ ]
    new_station_ids = [ ]

    for station in dump_stations:
        sid = station['sid']

        # update existing station
        if sid in station_ids:
            stations[index_dict[sid]].update(station)
        # add new station
        else:
            try:
                station = updateWithUcanMetadata(station)
            except KeyError, e:
                print 'ERROR :', str(e)
            else:
                new_index = len(station_ids)
                index_dict[sid] = new_index
                for key in INDEX_KEYS:
                    if key not in station:
                        station[key] = MISSING[key]
                stations.append(station) 
                station_ids.append(sid)

# sort stations by sid
stations = sorted(stations, key=lambda station: station['sid'])
# dump merged stations to a file
output_filepath = os.path.abspath(options.output_filepath)
output_file = open(output_filepath, 'w')
output_file.write('(')
for station in stations:
    output_file.write(STATION_TEMPLATE % station)
    output_file.write(',\n')
output_file.write(')')
output_file.close()
print 'merged index saved to file :', output_filepath


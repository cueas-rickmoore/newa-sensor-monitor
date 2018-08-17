#! /Volumes/projects/venvs/newa/bin/python

import os, sys

from rccpy.utils.options import stringToTuple

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def compareData(value_1, value_2):
    if isinstance(value_1, (tuple,list,basestring)):
        set_1 = set(value_1)
        set_2 = set(value_2)
        diff_1 = (set_1 - set_2)
        diff_2 = (set_2 - set_1)
        if len(diff_1) > 0  or len(diff_2) > 0:
            return (diff_1, (set_1 & set_2), diff_2)
        else: return (value_1,)
    else:
        return (value_1 - value_2,)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-k', action='store', type='string', dest='match_key',
                  default='ucanid')
parser.add_option('-m', action='store', type='string', dest='metadata',
                  default='ucanid,sid,name')
parser.add_option('-s', action='store', type='string', dest='sort_by',
                  default='ucanid')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

match_key = options.match_key
metadata = stringToTuple(options.metadata)

if ',' in args[0]:
    dataset_keys = args[0].split(',')
else: dataset_keys = [args[0], args[0]]

input_filepath = os.path.abspath(args[1])
if ',' in input_filepath:
    data_key, input_filepath= input_filepath.split(',')
else:
    data_key = match_key
input_file = open(input_filepath, 'r')
data = eval(input_file.read().strip().replace('\n',''))
input_file.close()

stations = { }
dataset_name = dataset_keys[0]
if isinstance(data, (tuple,list)):
    for station in data:
        keep = { }
        keep[data_key] = station[data_key]
        for key in metadata:
            if key in station: keep[key] = station[key]
        keep[dataset_name] = station[dataset_name]
        stations[station[match_key]] = keep
elif isinstance(data, dict):
    keep = { }
    for key, station in data.items():
        keep[data_key] = key
        for key in metadata:
            if key in station: keep[key] = station[key]
        keep[dataset_name] = station[dataset_name]
        stations[station[match_key]] = keep
else:
    raise TypeError, 'Invalid type for arg 2, must be tuple, list or dict'
del data

input_filepath = os.path.abspath(args[2])
if ',' in input_filepath:
    data_key, input_filepath = input_filepath.split(',')
else:
    data_key = match_key
    input_filepath = input_filepath
input_file = open(input_filepath, 'r')
data = eval(
       input_file.read().replace('\n','').replace(', ',',').replace(': ',':'))
input_file.close()

dataset_key = dataset_keys[1]
if isinstance(data, (tuple,list)):
    for station in data:
        master = stations[station[match_key]]
        for key in metadata:
            if key not in master: master[key] = station[key]
        master[dataset_name] = compareData(master[dataset_name],
                                           station[dataset_key])
elif isinstance(data, dict):
    for key, station in data.items():
        if key in stations:
            master = stations[key]
            for key in metadata:
                if key not in master: master[key] = station[key]
            master[dataset_name] = compareData(master[dataset_name],
                                               station[dataset_key])
        else:
            print '\n %s not present in first file' % key
            print station
else:
    raise TypeError, 'Invalid type for arg 2, must be tuple, list or dict'
del data

# sort stations by ucanid
stations = stations.values()
stations = sorted(stations, key=lambda station: station[options.sort_by])

# dump stations with merged data to a file
dump_filepath = os.path.abspath('compare_dataset_dump.py')
dump_file = open(dump_filepath, 'w')
dump_file.write('(')
for station in stations:
    dump_file.write(repr(station))
    dump_file.write(',\n')
dump_file.write(')')
dump_file.close()
print 'data differences saved to file :', dump_filepath


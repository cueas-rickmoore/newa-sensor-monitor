#! /Volumes/projects/venvs/newa/bin/python

import os, sys

import numpy as N

from rccpy.utils.options import stringToTuple

from newa.factory import ObsnetDataFactory
from newa.ucan import updateWithUcanMetadata

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.database.index import FILEMAKER_COLUMN_MAP, REVERSE_COLUMN_MAP
COLUMN_MAP_KEYS = FILEMAKER_COLUMN_MAP.keys()

from newa.database.index import INDEX
INDEX_KEYS = INDEX.keys()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-c', action='store', type='string', dest='columns_to_save',
                  default=None)
parser.add_option('-d', action='store', type='string', dest='dump_filepath',
                  default='merged_spreadsheet_dump.py')
parser.add_option('-i', action='store', type='string',
                  dest='input_dump_filepath', default=None)
parser.add_option('-n', action='store', type='string', dest='default_network',
                  default='newa')
parser.add_option('-s', action='store', type='string', dest='separator',
                  default='\t')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
default_network = options.default_network
separator = options.separator

if options.columns_to_save is None or options.columns_to_save == 'all':
    columns_to_save = INDEX_KEYS
else: columns_to_save = stringToTuple(options.columns_to_save)
if 'index' in columns_to_save:
    columns_to_save = list(columns_to_save)
    indx = columns_to_save.index('index')
    del columns_to_save[indx]
    columns_to_save = tuple(set(columns_to_save) | set(INDEX_KEYS))
elif 'ucanid' not in columns_to_save:
    columns_to_save = list(columns_to_save)
    columns_to_save.insert(0,'ucanid')
    columns_to_save = tuple(columns_to_save)
print 'columns_to_save', columns_to_save

input_filepaths = [ ]
for arg in args:
    input_filepaths.append(os.path.normpath(arg))

if options.input_dump_filepath is not None:
    input_dump_file = open(os.path.abspath(options.input_dump_filepath), 'r')
    stations = eval(input_dump_file.read())
    input_dump_file.close()
else:
    factory = ObsnetDataFactory(options)
    stations = factory.getIndexedStations('all')

index_dataset_names = stations[0].keys()
new_index_names = [ ]

for input_filepath in input_filepaths:
    if debug: print '\nreading file', input_filepath
    input_file = open(input_filepath, 'rU')
    # get column names from first line in file
    line = input_file.readline()
    if debug: print line
    column_names = [column.strip() for column in line.split(separator)]
    num_ss_columns = len(column_names)
    index_column_names = [ ]
    for name in column_names:
        if name in INDEX_KEYS:
            index_column_names.append(name)
        elif name in COLUMN_MAP_KEYS:
            index_column_names.append(FILEMAKER_COLUMN_MAP[name])
        elif name in columns_to_save: 
            index_column_names.append(name)
        else: index_column_names.append('IGNORE')

    column_indexes = [indx for indx in range(len(index_column_names))
                           if index_column_names[indx] != 'IGNORE']
    new_columns = [name for name in index_column_names if name != 'IGNORE'
                        and name not in index_dataset_names
                        and name not in new_index_names]
    if len(new_columns) > 0: new_index_names.extend(new_columns)

    # find the index key field name
    if 'ucanid' in index_column_names: index_key = 'ucanid'
    elif 'sid' in index_column_names: index_key = 'sid'
    elif 'name' in index_column_names: index_key = 'name'
    else:
        input_file.close()
        errmsg = 'Spreadsheet does not have a column that maps to an index key'
        errmsg += '\nSpreadsheet : %s' % input_filepath
        raise KeyError, errmsg
    if index_key in column_names:
        ss_key_column = column_names.index(index_key)
    else: ss_key_column = column_names.index(REVERSE_COLUMN_MAP[index_key])

    # create a dictionary of existing stations using the index key
    station_dict = { }
    existing_keys = [ ]
    for station in stations:
        station_dict[station[index_key]] = station
    existing_keys = tuple([key for key in station_dict.keys()])

    # read the spreadsheet and update the stations
    line = input_file.readline().replace('"','')
    if debug: print 'line 2', line
    line_num = 2
    while line:
        data = line.split(separator)
        # tsv files from Excel that had ^M as line separators get screwed up
        # when the ^M is removed
        if data[-1] == '\n': data[-1] = ''
        elif data[-1].endswith('\n'):
            data[-1] = data[-1].strip()
        # the last \t may also disapper if the last column was empty
        # this is especially a problem with the MAC version of Excel
        if num_ss_columns - len(data) == 1:
            data.append('')

        if len(data) == num_ss_columns:
            station_key = data[ss_key_column]
            if station_key in existing_keys:
                # update existing station
                station = station_dict[station_key]
            else:
                print 'creating new station record', station_key, data[1]
                # create new station
                station = { index_key : station_key, }
            # update with columns from input record
            for indx in column_indexes:
                station_column_name = index_column_names[indx]
                if station_column_name == 'active':
                    station[station_column_name] = data[indx][0]
                elif station_column_name != index_key:
                    station[station_column_name] = data[indx]
            # make sure that the station is assigned to a network
            if 'network' not in station:
                station['network'] = default_network
            # update new station with UCAN metadata and add to statioon_dict
            if station_key not in existing_keys:
                try:
                    station = updateWithUcanMetadata(station)
                except KeyError, e:
                    print 'ERROR :', str(e)
                else:
                    station_dict[station_key] = station 
        else:
            errmsg = 'ERROR : incomplete data record at line %d of file %s'
            print errmsg % (line_num, input_filepath)
            errmsg = 'ERROR : line should have %d columns, but only %d are present.'
            print errmsg % (num_ss_columns, len(data))
            print 'LINE :', line.strip().replace(separator,',')

        line = input_file.readline()
        line_num += 1
    input_file.close()

    # put stations back into array for next spreadsheet
    stations = station_dict.values()

# sort stations by ucanid
stations = sorted(stations, key=lambda station: station['ucanid'])

# dump stations with merged data to a file
dump_filepath = os.path.abspath(options.dump_filepath)
dump_file = open(dump_filepath, 'w')
dump_file.write('(')
for station in stations:
    station_keys = station.keys()
    for key in station_keys:
        if key not in columns_to_save: del station[key]
    for key in columns_to_save:
        if name == 'IGNORE': continue
        if name not in station:
            try:
                station[name] = INDEX[name].missing
            except KeyError:
                station[name] = None
    dump_file.write(repr(station))
    dump_file.write(',\n')
dump_file.write(')')
dump_file.close()
print 'merged station data saved to file :', dump_filepath


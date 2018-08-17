#! /Volumes/projects/venvs/newa/bin/python

import os, sys

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('--network', action='store', type='string', dest='network',
                  default=None)
parser.add_option('--state', action='store', type='string', dest='state',
                  default=None)

parser.add_option('-d', action='store_true', dest='datasets_as_tuple',
                  default=False)
parser.add_option('-m', action='store', type='string', dest='metadata',
                  default='all')
parser.add_option('-s', action='store', type='string', dest='sort_by',
                  default='name')
parser.add_option('-t', action='store_true', dest='as_tsv_file', default=False)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

datasets_as_tuple = options.datasets_as_tuple
sort_by = options.sort_by

if len(args) > 0:
    dump_filepath = os.path.normpath(args[0])
    filepath, ext = os.path.splitext(dump_filepath)
    if ext in ('.txt','.tsv'): as_tsv_file = True
    else: as_tsv_file = False
else:
    as_tsv_file = options.as_tsv_file
    dump_filepath = 'station_index_dump'
    if as_tsv_file: dump_filepath += '.tsv'
    else: dump_filepath += '.py'

factory = ObsnetDataFactory(options)
criteria = factory._validCriteria(options, ('network','state'))
metadata = factory._parseMetadata(options.metadata)

dump_file = open(dump_filepath, 'w')
# tab separated values file
if as_tsv_file:
    dump_file.write('\t'.join(metadata))
    for station in factory.getIndexedStations(metadata, criteria, sort_by):
        line = '\t'.join([str(station[key]) for key in metadata])
        dump_file.write('\n%s' % line)
# importable python object file
else:
    dump_file.write('(')
    for station in factory.getIndexedStations(metadata, criteria, sort_by):
        if datasets_as_tuple:
            station['datasets'] = tuple([dataset.strip()
                                  for dataset in station['datasets'].split(',')])
        dump_file.write(repr(station))
        dump_file.write(',\n')
    dump_file.write(')')

dump_file.close()


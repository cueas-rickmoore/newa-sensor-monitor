#! /Volumes/projects/venvs/newa/bin/python

import os, sys

from rccpy.utils.options import stringToTuple

from newa.factory import ObsnetDataFactory
from newa.database.index import getSortBy
from newa.databse.utils import writeStationsToFile

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('--active', action='store', type='string', dest='active',
                  default=None)
parser.add_option('--bbox', action='store', type='string', dest='bbox',
                  default=None)
parser.add_option('--county', action='store', type='string', dest='county',
                  default=None)
parser.add_option('--network', action='store', type='string', dest='network',
                  default=None)
parser.add_option('--state', action='store', type='string', dest='state',
                  default=None)

parser.add_option('-m', action='store', type='string', dest='metadata',
                  default='all')
parser.add_option('-o', action='store', type='string', dest='output_format',
                  default='dump')
parser.add_option('-s', action='store', type='string', dest='sort_by',
                  default='network,ucanid')
options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

search_keys = ('active','bbox','county','network','state')
metadata = stringToTuple(options.metadata)
sort_by = stringToTuple(options.sort_by)
index_metadata = tuple(set(metadata) | set(sort_by))

sort_by_template = getSortBy(*sort_by)
def sortBy(station):
    return sort_by_template % station

if len(args) > 0:
    filepath = os.path.abspath(os.path.normpath(args[0]))
    path, ext = os.path.splitext(filepath)
    output_format = ext[1:]
    if output_format == 'py': output_format = 'dump'
else:
    output_format = options.output_format
    fileroot = 'indexed_metadata_summary'
    filepath = os.path.abspath('%s.%s' % (fileroot,output_format))

factory = ObsnetDataFactory(options)
stations = factory.argsToStationData(( ), options, index_metadata, 'index',
                                     search_keys)
stations = sorted(stations, key=sortBy)
writeStationsToFile(stations, filepath, output_format, mode='w')

msg = " metadata summary for %d stations written to file" % len(stations)
print msg, filepath

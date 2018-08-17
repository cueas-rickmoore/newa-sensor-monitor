#! /Volumes/projects/venvs/newa/bin/python

import os, sys
from datetime import datetime

from rccpy.stations.ucan import UcanConnection

from newa.services import NewaWebServicesClient
from newa.ucan import updateWithUcanMetadata
from newa.database.utils import writeStationsToFile

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

JSON_STR = '"network":"%(network)s", "state":"%(state)s", "county":"%(county)s"'
JSON_STR +=', "sid":"%(sid)s", "ucanid":%(ucanid)d, "name":"%(name)s"'
JSON_STR +=', "gmt":%(gmt)d, "datasets":"%(datasets)s"'

SORT_KEY = lambda station:'%(network)s %(state)s %(id)s' % station

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-d', action='store_false', dest='update_datasets',
                  default=True)
parser.add_option('-f', action='store', type='string', dest='file_fmt',
                  default='dump')
parser.add_option('-m', action='store_false', dest='update_metadata',
                  default=True)
parser.add_option('-n', action='store', type='string', dest='network',
                  default=None)
options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
errmsg = 'skipped %(network)s station %(sid)s : %(name)s : no ucanid available'
procmsg = 'processed %(network)s station %(sid)s : %(name)s : %(ucanid)d'

file_fmt = options.file_fmt
update_metadata = options.update_metadata

if len(args) > 0:
    filepath = os.path.normpath(args[0])
    dirpath, filename = os.path.split(filepath)
else:
    filename = 'newa_stations.%s' % file_fmt
    filepath = os.path.abspath(filename)
name, file_ext = os.path.splitext(filename)

newa_client = NewaWebServicesClient()
if update_metadata: ucan = UcanConnection()

stations = [ ]

for station in [ station for station in newa_client.request('stationList', 'all')
                 if options.network is None or station['network'] == options.network ]:
    station['network'] = station['network'].encode('iso-8859-1')
    station['sid'] = station['id'].encode('iso-8859-1')
    del station['id']

    if update_metadata:
        try:
            station = updateWithUcanMetadata(station, ucan,
                                             options.update_datasets)
        except KeyError, e:
            print errmsg % station
            continue
    
    print errmsg % station
    stations.append(station)

if update_metadata: del ucan
del newa_client

stations = sorted(stations, key=SORT_KEY)
writeStationsToFile(stations, filepath, file_fmt, 'w')

print len(stations), 'downloaded from NEWA and written to', filepath


#! /Users/rem63/venvs/nrcc_prod/bin/python

import os, sys
from datetime import datetime

import numpy as N

from newa.factory import ObsnetDataFactory
from newa.buddies import BuddyLocator

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

BUDDY_RECORD_TYPE = [ ('ucanid','<i4'), ('distance','f4'),
                      ('start_date','<i2',4), ('total_hours','<i4') ]
EMPTY_BUDDY_RECORD = (-32768, N.nan, (0,0,0,0), -32768)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-b', action='store', type='int', dest='max_buddies',
                  default=4)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if len(args) > 0:
    by_ucanid = tuple([int(arg) for arg in args])
else: by_ucanid = None

factory = ObsnetDataFactory(options)
index_manager = factory.getFileManager('index', mode='r')

max_buddies = options.max_buddies

networks = index_manager.getData('network')
icao = N.where(networks=='icao')
not_icao = N.where(networks!='icao')
del networks

lats = index_manager.getData('lat')
icao_lats = lats[icao]
lats = lats[not_icao]

lons = index_manager.getData('lon')
icao_lons = lons[icao]
lons = lons[not_icao]

ucanids = index_manager.getData('ucanid')
icao_ids = ucanids[icao]
ucanids = ucanids[not_icao]
if by_ucanid is None: by_ucanid = ucanids
icao_stations = len(icao_ids)

buddy_cushion = max_buddies + 10
# loop through stations in by_ucanid and find 4 nearest stations
for ucanid in by_ucanid:
    indx = N.where(ucanids == ucanid)
    # calculate distance to all other stations
    lon_diffs = icao_lons - lons[indx]
    lat_diffs = icao_lats - lats[indx]
    distances = N.sqrt( (lon_diffs*lon_diffs) + (lat_diffs*lat_diffs) )
    possibles = [ (distances[i], icao_ids[i]) for i in range(icao_stations) ]
    possibles.sort()

    buddies =  [ ]
    for distance, icao_id in possibles:
        buddy_manager = factory.getFileManager((icao_id,'hours'), mode='r')
        buddy_attrs = buddy_manager.getFileAttributes()
        start_hour = tuple(buddy_attrs['earliest_hour'])[:4]
        end_hour = tuple(buddy_attrs['latest_hour'])[:4]
        delta = datetime(*end_hour) - datetime(*start_hour)
        num_hours = (delta.days * 24) + (delta.seconds / 3600) 
        buddies.append((icao_id, distance, start_hour, num_hours))
        if len(buddies) >= max_buddies: break

    if len(buddies) < max_buddies:
        for n in range(len(buddies),max_buddies):
            buddies.append(EMPTY_BUDDY_RECORD)

    record = N.rec.fromrecords(buddies, BUDDY_RECORD_TYPE, (len(buddies),))
    print 'Adding buddies record to stats file for %d' % ucanid
    stats_manager = factory.getFileManager((ucanid,'statistics'), mode='a')
    attrs = { 'description' : 'buddy stations in ICAO network', }
    stats_manager.updateDataset('buddies', record, attrs)
    stats_manager.closeFile()


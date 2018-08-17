#! /Users/rem63/venvs/nrcc_prod/bin/python

import os, sys
from datetime import datetime

import numpy as N

from rccpy.timeseries.multi import MultipleTimeSeries

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

BUDDY_RECORD_TYPE = [ ('ucanid','<i4'), ('distance','f4'),
                      ('start_date','<i2',4), ('total_hours','<i4') ]
EMPTY_BUDDY_RECORD = (-32768, N.nan, (0,0,0,0), -32768)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-b', action='store', type='int', dest='max_buddies',
                  default=5)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)

parser.add_option('--numyears', action='store', type='int', dest='num_years',
                  default=15)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

factory = ObsnetDataFactory(options)
index_manager = factory.getFileManager('index', mode='r')

max_buddies = options.max_buddies
min_num_years = options.num_years
min_num_hours = min_num_years * (365 * 24)

networks = index_manager.getData('network')
potential_buddies = N.where( (networks=='icao') | (networks=='cu_log') )
num_potential_buddies = len(potential_buddies[0])

ucanids = index_manager.getData('ucanid')
potential_buddy_ids = ucanids[potential_buddies]
if len(args) > 0:
    ucanids = tuple(ucanids)
    need_buddies = [ucanids.index(int(arg)) for arg in args]
    need_buddies.sort()
else:
    need_buddies = list(N.where(networks!='icao')[0])

lats = index_manager.getData('lat')
potential_buddy_lats = lats[potential_buddies]
lons = index_manager.getData('lon')
potential_buddy_lons = lons[potential_buddies]
all_first_hours = index_manager.getData('first_hour')
all_last_reports = index_manager.getData('last_report')

buddy_cushion = max_buddies + 10
# loop through stations in need_buddies and find best max_buddies stations
for indx in need_buddies:
    ucanid = ucanids[indx]
    site_first_hour = asDatetime(all_first_hours[indx])
    site_last_report = asDatetime(all_last_reports[intx])
    delta = site_last_report - site_first_hour
    site_num_hours = (delta.days * 24) + (delta.seconds / 3600) + 1

    # calculate distance to all other stations
    lon_diffs = potential_buddy_lons - lons[indx]
    lat_diffs = potential_buddy_lats - lats[indx]
    distances = N.sqrt( (lon_diffs*lon_diffs) + (lat_diffs*lat_diffs) )
    possibles = [ (distances[i], i) for i in range(num_potential_buddies) ]
    possibles.sort(key=lambda x: x[0])

    buddies =  [ ]
    # test for coverage
    for distance, i in possibles:
        buddy_first_hour = all_first_hours[i]
        # eliminate stations with unknown time range
        if buddy_first_hour < 0: continue
        buddy_first_hour = asDatetime(buddy_first_hour)
        buddy_last_report = asDatetime(all_last_reports[i])
        delta = buddy_last_report - buddy_first_hour
        buddy_num_hours = (delta.days * 24) + (delta.seconds / 3600) + 1
        if buddy_num_hours >= min_num_hours:
            # caclulate average difference in temperature values
            # between site and buddy
            manager = factory.getFileManager((ucaind,'hours'),'r')
            site_temp, site_attrs = manager.getData('temp',True)
            site_info = ('site', site_temp, site_first_hour, site_attrs)
            manage.closeFile()

            manager = factory.getFileManager((ucainds[i],'hours'),'r')
            buddy_temp, buddy_attrs = manager.getData('temp',True)
            buddy_info = ('buddy', buddy_temp, buddy_first_hour, buddy_attrs)
            manage.closeFile()
            del manager

            time_series = MultipleTimeSeries(site_info, buddy_info)
            temps = time_series.getData()
            diffs = N.absolute(temps['site'] - temps['buddy'])
            avg_diff = N.nanmean(diffs)
            del time_series, buddy_temp, site_temp

            buddies.append((distance, buddy_num_hours, avg_diff, start_hour, i))
        if len(buddies) >= buddy_cushion: break


    if len(buddies) < max_buddies:
        for n in range(len(buddies),max_buddies):
            buddies.append(EMPTY_BUDDY_RECORD)

    record = N.rec.fromrecords(buddies, BUDDY_RECORD_TYPE, (len(buddies),))
    print 'Adding buddies record to stats file for %d' % ucanid
    stats_manager = factory.getFileManager((ucanid,'statistics'), mode='a')
    attrs = { 'description' : 'buddy stations in ICAO network', }
    try:
        stats_manager.replaceDataset('buddies', record, attrs)
    except Exception as e:
        print "something is wrong with", ucanid, 'buddy records'
        raise
    stats_manager.closeFile()


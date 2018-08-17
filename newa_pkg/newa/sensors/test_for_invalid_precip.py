#! /Volumes/projects/venvs/newa/bin/python

import os, sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)
import urllib, urllib2

# set filter to ignore warings about arrays that are all N.nan
import warnings
warnings.filterwarnings('ignore',"All-NaN slice encountered")

try:
   import json 
except ImportError:
   import simplejson as json

import numpy as N

from rccpy.grid.utils import neighborNodes
from rccpy.utils.timeutils import asDatetime, dateAsInt, dateAsTuple

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CLOSEST_DIFF_MSG = 'closest diff = %-.2f : station = %-.2f : grid node = %-.2f'
DASHES = '-' * 80
EQUALS = '=' * 80
GRID_DATA_MSG = 'grid data : [%s]'
SKIP_MSG = '\nSkipping station %(sid)s : (%(name)s) : %(ucanid)d'
STATION_INFO = '\n%s\n%%(sid)s : %%(name)s : %%(ucanid)d \n%s' % (EQUALS,DASHES)
STN_DATA_MSG = 'stn data : [%s]'
THE_LAST_STATION = None

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getPrecipGrid(factory, station, _date_, test_run):
    if test_run:
        if GRID_CACHE['year'] != _date_.year:
            working_dir = os.path.abspath(factory.getDirectoryPath('working'))
            filename = 'compag_conus_%d.h5' % _date_.year
            filepath = os.path.join(working_dir, filename)
            manager = HDF5DataFileManager(filepath, 'r')
            GRID_CACHE['year'] = _date_.year
            GRID_CACHE['data'] = manager.getData('pcpn')
            GRID_CACHE['lats'] = manager.getData('lat')
            GRID_CACHE['lons'] = manager.getData('lon')
            # getDataWhere(self, dataset_names, criteria)
            manager.closeFile()

        if station['sid'] != GRID_CACHE['sid']:
            GRID_CACHE['sid'] = station['sid']
            indexes = neighborNodes(station['lon'], station['lat'],
                                    GRID_CACHE['lons'], GRID_CACHE['lats'], 9)
            GRID_CACHE['indexes'] = indexes
        julian = _date_.timetuple().tm_yday
        return GRID_CACHE['data'][julian][GRID_CACHE['indexes']]

    else:
        lon = station['lon']
        lat = station['lat']
        bbox_str = str(lon-0.05) + ',' + str(lat-0.05)
        bbox_str += ',' + str(lon+0.05) + ',' + str(lat+0.05)
        if station['sid'] != GRID_CACHE['sid']:
            params = { "bbox" : bbox_str, "date" : _date_.strftime('%Y%m%d'),
                       "grid" : 3, "elems" : "pcpn", 'meta' : 'll' }
        else:
            params = { "bbox" : bbox_str, "date" : _date_.strftime('%Y%m%d'),
                       "grid" : 3, "elems" : "pcpn" }

        params = urllib.urlencode({'params':json.dumps(params)})
        request = urllib2.Request('http://data.rcc-acis.org/GridData',
                                  params, {'Accept':'application/json'})
        response = urllib2.urlopen(request)
        result = json.loads(response.read())
        # ACIS may return a grid that is filled with '-999' and json converts
        # it to an int64 array. So we need to specify dtype as float
        precip = N.array(result['data'][0][1], dtype=float).flatten()
        # handle case where ACIS puts 'inf' into the json string
        precip[ N.where(N.isinf(precip)) ] = N.nan
        # handle case where ACIS puts '-999' into the json string
        precip[ N.where(precip == -999) ] = N.nan

        if station['sid'] != GRID_CACHE['sid']:
            GRID_CACHE['sid'] = station['sid']
            GRID_CACHE['lats'] = N.array(result['meta']['lat']).flatten()
            lat_diffs = station['lat'] - GRID_CACHE['lats']
            GRID_CACHE['lons'] = N.array(result['meta']['lon']).flatten()
            lon_diffs = station['lon'] - GRID_CACHE['lons']
            distances = N.sqrt( (lon_diffs*lon_diffs) + (lat_diffs*lat_diffs) )
            GRID_CACHE['distances'] = distances
            GRID_CACHE['closest'] = N.where(distances == distances.min())
            GRID_CACHE['size'] = precip.size

        return precip

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getStationPrecip(factory, station, _date_, cushion=0, test_run=False):
    _datetime_ = asDatetime(_date_)
    start_time = _datetime_ - ONE_DAY + relativedelta(hours=7)
    end_time = _datetime_ + relativedelta(hours=7)
    if cushion != 0:
        start_time -= relativedelta(hours=cushion)
        end_time += relativedelta(hours=cushion)

    if test_run:
        if station['sid'] == STATION_CACHE['sid']:
            data = STATION_CACHE['data']
            dates = STATION_CACHE['dates']
        else:
            # hourly data file must already exist
            filepath = factory.getFilepathForUcanid(station['ucanid'], 'hours')
            if not os.path.exists(filepath):
                print SKIP_MSG % station
                print 'Hourly data file does not exist : %s' % filepath
                return None
            manager = HDF5DataFileManager(filepath, 'r')
            data = manager.getData('pcpn.value')
            STATION_CACHE['data'] = data
            dates = manager.getData('pcpn.date')
            STATION_CACHE['dates'] = dates
            STATION_CACHE['sid'] = station['sid']

        _start_time = dateAsInt(start_time, True)
        _end_time = dateAsInt(end_time, True)
        indexes = N.where( (dates > (_start_time-1)) & (dates < _end_time) )
        if len(indexes[0]) > 0: return data[indexes]
        return None

    else:
        start_time = dateAsTuple(start_time, True) 
        end_time = dateAsTuple(end_time, True)
        ucan = HourlyDataConnection(days_per_request=1)
        _start_date_, _end_date_, precip =\
        ucan.getData(station, 'pcpn', start_time, end_time)
        precip = N.array(precip)
        precip[N.where(N.isinf(precip))] = N.nan
        return precip

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def arrayToString(precip):
    if len(precip.shape) > 1:
        return ' '.join(['%-.2f' % p for p in precip])
    else: return ' '.join(['%-.2f' % p for p in precip])

def isStationAnomaly(stn_precip, grid_precip, threshold, station, date_str):
    global THE_LAST_STATION
    compare_msg = 'station = %-.2f : grid = %-.2f'
    refactor_msg = 'refactored : [%s]'

    stn_total = stn_precip.sum()
    grid_max = N.nanmax(grid_precip)

    if grid_max > threshold:
        if stn_total == 0:
            if station['sid'] != THE_LAST_STATION:
                print STATION_INFO % station
                THE_LAST_STATION = station['sid']
            print '\n%s :' % date_str
            print STN_DATA_MSG % arrayToString(stn_precip)
            print GRID_DATA_MSG % arrayToString(grid_precip)
            print compare_msg % (stn_total, grid_max)
            precip = getStationPrecip(factory, station, date, 6, test_run)
            refactored = precip.sum()
            print refactor_msg % arrayToString(precip)
            print compare_msg % (refactored, grid_max)
            if refactored == 0:
                print "station NO, grid YES"
                return True
            else:
                print "station YES?, grid YES"
                return False
        else:
            detectLargeDiffs(date_str, station, stn_total, stn_precip,
                             grid_max, grid_precip)
            return False

    elif grid_max == 0:
        if stn_total > threshold:
            if station['sid'] != THE_LAST_STATION:
                print STATION_INFO % station
                THE_LAST_STATION = station['sid']
            print '\n%s :' % date_str
            print STN_DATA_MSG % arrayToString(stn_precip)
            print GRID_DATA_MSG % arrayToString(grid_precip)
            print compare_msg % (stn_total, grid_max)
            print "station YES, grid NO"
            return True
        else:
            return False
    else:
        detectLargeDiffs(date_str, station, stn_total, stn_precip,
                         grid_max, grid_precip)
        return False

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def detectLargeDiffs(date_str, station, stn_total, stn_precip, grid_max,
                     grid_precip):
    global THE_LAST_STATION

    closest_precip = grid_precip[GRID_CACHE['closest']]
    closest_diff = stn_total - closest_precip
    closest_gt_station = 'closest node precip is %-.2f times greater than station'
    closest_msg = 'station = %-.2f : closest node = %-.2f : diff = %-.2f'
    grid_diff = stn_total - grid_max
    grid_gt_station = 'max grid precip is %-.2f times greater than station'
    max_diff_msg = 'station = %-.2f : grid max = %-.2f : diff = %-.2f'
    station_gt_closest = 'station precip is %-.2f times greater than closest node'
    station_gt_grid = 'station precip is %-.2f times greater than grid max'

    if stn_total > 0 and grid_max > 0:
        grid_magnitude = max(stn_total,grid_max) / min(stn_total,grid_max)
    else: grid_magnitude = None

    closest_magnitude = [ ]
    for indx in range(len(closest_precip)):
        precip = closest_precip[indx]
        if stn_total > 0 and precip > 0:
            magnitude = max(stn_total,precip) / min(stn_total,precip)
        else: magnitude = None
        closest_magnitude.append(magnitude)

    if grid_magnitude > 9.9:
        if station['sid'] != THE_LAST_STATION:
            print STATION_INFO % station
            THE_LAST_STATION = station['sid']
        print '\n%s :' % date_str
        print STN_DATA_MSG % arrayToString(stn_precip)
        print GRID_DATA_MSG % arrayToString(grid_precip)
        print max_diff_msg % (stn_total, grid_max, grid_diff)
        if grid_magnitude:
            if stn_total > grid_max:
                print station_gt_grid % grid_magnitude
            else: print grid_gt_station % grid_magnitude
        for indx in range(len(closest_precip)):
            precip = closest_precip[indx]
            diff = closest_diff[indx]
            print closest_msg % (stn_total, precip, diff)
            if closest_magnitude:
                magnitude = closest_magnitude[indx]
                if magnitude:
                    if stn_total > precip:
                        print station_gt_closest % magnitude
                    else: print closest_gt_station % magnitude
        print "station YES, grid YES"

    elif abs(grid_diff) > 1.0:
        if station['sid'] != THE_LAST_STATION:
            print STATION_INFO % station
            THE_LAST_STATION = station['sid']
        print '\n%s :' % date_str
        print STN_DATA_MSG % arrayToString(stn_precip)
        print GRID_DATA_MSG % arrayToString(grid_precip)
        print max_diff_msg % (stn_total, grid_max, grid_diff)
        for indx in range(len(closest_precip)):
            precip = closest_precip[indx]
            diff = closest_diff[indx]
            print closest_msg % (stn_total, precip, diff)
        print "station YES, grid YES"

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# station search criteria
parser.add_option('--bbox', action='store', type='string', dest='bbox',
                  default=None)
parser.add_option('--county', action='store', type='string', dest='county',
                  default=None)
parser.add_option('--sid', action='store', type='string', dest='sid',
                  default=None)
parser.add_option('--network', action='store', type='string',
                  dest='network', default=None)
parser.add_option('--state', action='store', type='string', dest='state',
                  default=None)

parser.add_option('--mt', action='store', type='int', dest='missing_threshold',
                  default=1)
parser.add_option('--pt', action='store', type='float', dest='precip_threshold',
                  default=0.05)

parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if len(args) >= 3:
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
    start_date = datetime(year, month, day)
if len(args) >= 6:
    year = int(args[3])
    month = int(args[4])
    day = int(args[5])
    end_date = datetime(year, month, day)
else: end_date = start_date + ONE_DAY

debug = options.debug
test_run = options.test_run

if test_run:
    from rccpy.hdf5.manager import HDF5DataFileManager
    GRID_CACHE = { 'year' : -32768, 'sid' : None }
    STATION_CACHE = { 'sid' : None, }
else:
    from newa.ucan import getTsVarType, HourlyDataConnection
    from rccpy.hdf5.manager import HDF5DataFileManager
    GRID_CACHE = { 'year' : -32768, 'sid' : None }

missing_threshold = options.missing_threshold
threshold = options.precip_threshold

factory = ObsnetDataFactory(options)
stations = factory.argsToStationData((), options)

num_days = (end_date - start_date).days
print num_days, 'days', start_date, 'thru', end_date

for station in stations:
    date = start_date
    missing_days = 0
    while date < end_date:
        date_str = date.strftime('%B %d, %Y')
        stn_precip = getStationPrecip(factory, station, date, test_run=test_run)
        if stn_precip is None or len(stn_precip) == 0:
            missing_days += 1
            date += ONE_DAY
            continue
        else:
            missing = N.where(N.isnan(stn_precip))
            num_missing = len(missing[0])
            if num_missing == len(stn_precip):
                missing_days += 1
                date += ONE_DAY
                continue
            elif num_missing > missing_threshold:
                if station['sid'] != THE_LAST_STATION:
                    print STATION_INFO % station
                    THE_LAST_STATION = station['sid']
                msg = '\n%s : precip missing for %d hours'
                print msg % (date_str, num_missing)
                date += ONE_DAY
                continue

        grid_precip = getPrecipGrid(factory, station, date, test_run)

        if isStationAnomaly(stn_precip, grid_precip, threshold, station, 
                            date_str):
            print '***** SEND EMAIL *****'

        date += ONE_DAY

    if missing_days > 0:
        if station['sid'] != THE_LAST_STATION:
            print STATION_INFO % station
        THE_LAST_STATION = station['sid']
        msg  = '\nno precip reported for %d of %d days' 
        print msg % (missing_days, num_days)

# MUST TURN OFF WARNING FILTER !!!!!
warnings.resetwarnings()

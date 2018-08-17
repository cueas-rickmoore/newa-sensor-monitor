#! /Volumes/projects/venvs/newa/bin/python

import os, sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib, urllib2

try:
   import json 
except ImportError:
   import simplejson as json

import numpy as N

from rccpy.utils.timeutils import asDatetime, dateAsTuple

from newa.factory import ObsnetDataFactory
from newa.ucan import HourlyDataConnection

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

COMPARE_MSG = 'station total = %-.2f : grid min = %-.2f : grid max = %-.2f'
GRID_DATA_MSG = '\ngrid data for %s :\n[%s]'
STATION_INFO = '%(sid)s : %(name)s : %(ucanid)d'
STN_DATA_MSG = '\nstation data from %s to %s :\n[%s]'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getGridData(factory, station, _date_, dataset_name):
    lon = station['lon']
    lat = station['lat']
    bbox_str = str(lon-0.05) + ',' + str(lat-0.05)
    bbox_str += ',' + str(lon+0.05) + ',' + str(lat+0.05)
    params = { "bbox" : bbox_str, "date" : _date_.strftime('%Y%m%d'),
               "grid" : 3, "elems" : "pcpn"}
    params = urllib.urlencode({'params':json.dumps(params)})
    request = urllib2.Request('http://data.rcc-acis.org/GridData',
                                  params, {'Accept':'application/json'})
    response = urllib2.urlopen(request)
    result = json.loads(response.read())
    # ACIS may return a grid that is filled with '-999' and json converts
    # it to an int64 array. So we need to specify dtype as float
    data = N.array(result['data'][0][1], dtype=float).flatten()
    # handle case where ACIS puts 'inf' into the json string
    data[ N.where(N.isinf(data)) ] = N.nan
    # handle case where ACIS puts '-999' into the json string
    data[ N.where(data == -999) ] = N.nan
    return data

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getStationData(factory, station, _date_, dataset_name, cushion=0):
    _datetime_ = asDatetime(_date_)
    start_time = (_datetime_ - relativedelta(days=1)) + relativedelta(hours=8)
    end_time = _datetime_ + relativedelta(hours=7)
    if cushion != 0:
        start_time -= relativedelta(hours=cushion)
        end_time += relativedelta(hours=cushion)

    start_time = dateAsTuple(start_time, True) 
    end_time = dateAsTuple(end_time, True)
    ucan = HourlyDataConnection(days_per_request=1)
    _start_date_, _end_date_, data =\
    ucan.getData(station, dataset_name, start_time, end_time)
    data = N.array(data)
    data[N.where(N.isinf(data))] = N.nan
    return datetime(*_start_date_), datetime(*_end_date_), data

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def arrayToString(data):
    if len(data.shape) == 2:
        return '\n'.join([' '.join(['%-.2f' % d for d in data[row]])
                          for row in data])
    else: return ' '.join(['%-.2f' % d for d in data])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# station search criteria
parser.add_option('--name', action='store', type='string', dest='name',
                  default=None)
parser.add_option('--sid', action='store', type='string', dest='sid',
                  default=None)
parser.add_option('--uid', action='store', type='string', dest='ucanid',
                  default=None)

parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if options.sid is None and options.name is None and options.ucanid is None:
    print 'You must se one of the following options : --sid, --name or --ucanid'
    os.exit(99)

dataset_name = args[0]
year = int(args[1])
month = int(args[2])
day = int(args[3])
date = datetime(year, month, day)
print date.strftime('Retrieving data for %B %d, %Y')

factory = ObsnetDataFactory(options)
station = factory.argsToStationData((), options)[0]

criteria = factory._validCriteria(options, ('sid','name','ucanid'))
metadata = ('lat','lon','name','network','sid','state','ucanid')
station = factory.getIndexedStations(metadata, criteria)[0]
print STATION_INFO % station

start, end, stn_data = getStationData(factory, station, date, dataset_name)
print STN_DATA_MSG % (start.strftime('%Y-%m-%d:%H'),end.strftime('%Y-%m-%d:%H'),
                      arrayToString(stn_data))

grid_data = getGridData(factory, station, date, dataset_name)
print GRID_DATA_MSG % (date.strftime('%Y-%m-%d'), arrayToString(grid_data))

print COMPARE_MSG % (N.nansum(stn_data), N.nanmin(grid_data), N.nanmax(grid_data))

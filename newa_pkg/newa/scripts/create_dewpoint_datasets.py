#! /Users/rem63/venvs/nrcc_prod/bin/python

import os, sys

import numpy as N

from rccpy.atmos.dewpt import generateDewpointArray
from rccpy.atmos.dewpt import calculateDewpointDepression
from rccpy.utils.timeutils import asDatetime

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-x', action='store_true', dest='replace_existing',
                  default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

procmsg = '\nprocessing station %d of %d : %d : %s (%s)' 
skipmsg = '\nNo hourly data file for station %d of %d : %d : %s (%s)' 

debug = options.debug
replace_existing = options.replace_existing

factory = ObsnetDataFactory(options)
stations = factory.argsToStationData(args, options)
total_stations = len(stations)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

station_num = 0

for station in stations:
    station_num += 1
    ucanid = station['ucanid']

    filepath = factory.getFilepathForUcanid(station['ucanid'], 'hours')
    if os.path.exists(filepath):
        manager = factory.getStationFileManager((ucanid,'hours'),'a')
    else:
        print skipmsg % (station_num, total_stations, ucanid, station['sid'],
                         station['name'])
        continue

    # we're going to process this station
    print procmsg % (station_num, total_stations,ucanid, station['sid'],
                     station['name'])

    # check to see if dewpt already exists and deal with it
    gen_dewpt = True
    if 'dewpt' in manager.listGroups():
        if replace_existing: manager.deleteGroup('dewpt')
        else: gen_dewpt = False

    if gen_dewpt:
        (rhum_data,rhum_attrs),(temp_data,temp_attrs) = \
        manager.getData(('rhum.value','temp.value'),True)
        rhum_data = factory.transformData('rhum', rhum_data, False)
        print rhum_data
        temp_data = factory.transformData('temp', temp_data, False)
        print ' '
        print temp_data
        temp_start_hour = asDatetime(temp_attrs['first_hour'])

        dewpt_start_hour, dewpt_end_hour, dewpt_data = \
        generateDewpointArray(rhum_data, asDatetime(rhum_attrs['first_hour']),
                              temp_data, temp_start_hour, 'F')

        print ' '
        print dewpt_data
        factory.createHourlyDataGroup(manager, 'dewpt', dewpt_data,
                                      dewpt_start_hour, dewpt_end_hour,
                                      units=temp_attrs['units'],
                                      min=N.nanmin(dewpt_data),
                                      max=N.nanmax(dewpt_data), missing=-32768)

    else:
        dewpt_data, dewpt_attrs = manager.getData('dewpt.value',True)
        dewpt_data = factory.transformData('dewpt', dewpt_data, False) 
        dewpt_start_hour = asDatetime(dewpt_attrs['first_hour'])
        temp_data, temp_attrs = manager.getData('temp.value',True)
        temp_data = factory.transformData('temp', temp_data, False) 
        temp_start_hour = asDatetime(temp_attrs['first_hour'])

    gen_dewpt_depr = True
    if 'dewpt_depr' in manager.listGroups():
        if replace_existing: manager.deleteGroup('dewpt_depr')
        else: gen_dewpt_depr = False

    if gen_dewpt_depr:
        start_hour, end_hour, data = \
        calculateDewpointDepression(dewpt_data, dewpt_start_hour,
                                    temp_data, temp_start_hour)
        factory.createHourlyDataGroup(manager, 'dewpt_depr', data, start_hour,
                                      end_hour, min=N.nanmin(data),
                                      max=N.nanmax(data), missing=-32768)

    sys.stdout.flush()
    sys.stderr.flush()


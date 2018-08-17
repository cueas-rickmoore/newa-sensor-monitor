#! /Users/rem63/venvs/nrcc_prod/bin/python

import os, sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

import numpy as N

from rccpy.atmos.dewpt import generateDewpointArray
from rccpy.atmos.dewpt import calculateDewpointDepression
from rccpy.hdf5.manager import HDF5DataFileManager
from rccpy.stations.ucan import UcanConnection, UcanInvalidElementError

from rccpy.utils.exceptutils import reportLastException
from rccpy.utils.options import stringToTuple
from rccpy.utils.timeutils import asDatetime, dateAsTuple
from rccpy.utils.units import convertUnits

from newa.factory import ObsnetDataFactory
from newa.ucan import getTsVarType

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config as CONFIG
ELEMENTS = CONFIG.elements
NETWORKS = CONFIG.networks

DATE_FORMULA = 'year*1000000 + month*10000 + day*100 + hour'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def generateHoursArray(first_hour, last_hour):
    hour = asDatetime(first_hour)
    last_hour = asDatetime(last_hour)
    interval = relativedelta(hours=1)
    hours = [ ]
    while hour <= last_hour:
        int_date = (hour.year*1000000) + (hour.month * 10000)
        int_date += (hour.day * 100) + hour.hour
        hours.append(int_date)
        hour += interval
    return N.array(hours, dtype='i4')

def transformData(station, element, data):
    if element in ('dewpt','dewpt_depr'):
        dt, mv, to_units, tsv, from_units = getTsVarType(station, 'temp')
    else: dt, mv, to_units, tsv, from_units = getTsVarType(station, element)
    data = convertUnits(data, from_units, to_units)
    data[N.where(N.isnan(data))] = -32768
    data[N.where(N.isinf(data))] = -32768
    return N.array(data, dtype='i2')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def addElementDatasets(manager, station, element, data, first_hour, last_hour,
                       **kwargs):
    # create element group
    attrs = { }
    attrs['created'] = manager._timestamp()
    attrs['description'] = kwargs.get('description',
                                      ELEMENTS[element].description)
    attrs['first_hour'] = dateAsTuple(first_hour, True)
    attrs['frequency'] = 'hour'
    attrs['interval'] = 1
    attrs['last_hour'] = dateAsTuple(last_hour, True)
    print '\n  creating %s element group' % element
    manager.createGroup(element, attrs)

    # generate the dates array and use it to create a dataset
    dataset_name = '%s.date' % element
    print '    creating %s dataset' % dataset_name
    manager.createDataset(dataset_name, generateHoursArray(first_hour,last_hour),
                          attrs)
    manager.setDatasetAttribute(dataset_name, 'description',
                                'Year,Month,Day,Hour')
    manager.setDatasetAttribute(dataset_name, 'date_formula', DATE_FORMULA)

    # create value dataset
    dataset_name = '%s.value' % element
    for attr_name, attr_value in kwargs.items():
        if attr_name not in attrs: attrs[attr_name] = attr_value
    attrs['value_type'] = ELEMENTS[element].value_type
    print '    creating %s dataset' % dataset_name
    data = transformData(station, element, data)
    manager.createDataset(dataset_name, data, attrs)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('--days', action='store', type='int', dest='days_per_request',
                  default=30)

parser.add_option('--bbox', action='store', type='string', dest='bbox',
                  default=None)
parser.add_option('--county', action='store', type='string', dest='county',
                  default=None)
parser.add_option('--network', action='store', type='string', dest='network',
                  default=None)
parser.add_option('--sid', action='store', type='string', dest='sid',
                  default=None)
parser.add_option('--state', action='store', type='string', dest='state',
                  default=None)

parser.add_option('-e', action='store', type='string', dest='elements',
                  default='all')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-x', action='store_true', dest='replace_existing',
                  default=False)
parser.add_option('-y', action='store_true', dest='test', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if len(args) > 0 and args[0].isdigit():
    end_date = (int(args[0]), int(args[1]), int(args[2]))
    if len(args) > 3: args = args[4:]
    else: args = ()
else: end_date = None

search_keys = ('bbox','county','network','sid','state')

if options.elements == 'all':
    all_elements = list(ELEMENTS.keys())
else: all_elements = list(stringToTuple(options.elements))
all_elements.sort()

factory = ObsnetDataFactory(options)
stations = factory.argsToStationData(args, options, search_keys=search_keys)

stations.sort(key=lambda x: x['ucanid'])
total_stations = len(stations)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

badmsg = 'encountered known bad station %s : %s (%s)' 
procmsg = '\nprocessing station %d of %d : %d : %s (%s)' 
skipmsg = 'skipping station %d of %d : %d : %s (%s)' 

days_per_request = options.days_per_request
replace_existing = options.replace_existing
test_run = options.test
if test_run: debug = True
else: debug = options.debug

station_num = 0

for station in stations:
    station_num += 1
    ucan = UcanConnection(None, days_per_request)

    filepath = factory.getFilepathForUcanid(station['ucanid'], 'hours')
    if os.path.exists(filepath):
        if replace_existing: os.remove(filepath)
        else:
            print skipmsg % (station_num, total_stations, station['ucanid'],
                             station['sid'], station['name'])
            continue

    # we're going to process this station
    print procmsg % (station_num, total_stations, station['ucanid'],
                     station['sid'], station['name'])

    # get a manager for the new file
    manager = factory.getFileManager(filepath,'w')
    manager.setFileAttribute('created',manager._timestamp())
    manager.setFileAttributes(**station)

    available_elements = NETWORKS[station['network']].elements
    elements = [elem for elem in all_elements if elem in available_elements]

    earliest_hour = (9999, 99, 99, 99)
    latest_hour = (0, 0, 0, 0)

    dewpt_data = None
    rhum_data = None
    temp_data = None

    for element in elements:
        dtype, missing_value, units, tsv_name, tsv_units =\
        getTsVarType(station, element)
        try:
            first_hour, last_hour, data =\
            ucan.getHourlyData(station, tsv_name, dtype, tsv_units,
                               missing_value, None, end_date, debug)
        except UcanInvalidElementError as e:
            print ' ', e.args[0]
            continue

        earliest_hour = min(first_hour, earliest_hour)
        latest_hour = max(last_hour, latest_hour)

        # extra attributes for the data values dataset
        value_attrs = { 'units' : units, 'missing' : -32768 }
        if N.isfinite(missing_value):
            valid = data[N.where(data != missing_value)]
        else:
            valid = data[N.where(N.isfinite(data))]
        if len(valid) > 0:
            value_attrs['min'] = N.min(valid)
            value_attrs['max'] = N.max(valid)
        else:
            value_attrs['min'] = missing_value
            value_attrs['max'] = missing_value

        # calculate dewpoints if both temp and rhum are available
        if element == 'temp':
            temp_attrs = value_attrs
            temp_base_hour = datetime(*first_hour)
            temp_data = data
            temp_data[N.where(N.isinf(temp_data))] = N.nan
            temp_first_hour = first_hour
            temp_last_hour = last_hour
            temp_units = tsv_units
            if rhum_data is not None:
                print '\n  generating dewpoint data array'
                dewpt_first_hour, dewpt_last_hour, dewpt_data = \
                generateDewpointArray(rhum_data, rhum_base_hour, temp_data,
                                      temp_base_hour, temp_units)
                dewpt_data[N.where(dewpt_data == -32768)] = N.inf

        elif element == 'rhum':
            rhum_attrs = value_attrs
            rhum_base_hour = datetime(*first_hour)
            rhum_data = data
            rhum_data[N.where(N.isinf(rhum_data))] = N.nan
            rhum_first_hour = first_hour
            rhum_last_hour = last_hour
            if temp_data is not None:
                dewpt_first_hour, dewpt_last_hour, dewpt_data = \
                generateDewpointArray(data, rhum_base_hour, temp_data,
                                      temp_base_hour, temp_units)
                dewpt_data[N.where(dewpt_data == -32768)] = N.inf
        else:
            addElementDatasets(manager, station, element, data, first_hour,
                               last_hour, **value_attrs)

    # create the 'dewpt', 'dewpt_depr', 'rhum' and 'temp' element datasets
    if dewpt_data is not None:
        first_hour, last_hour, depr_data = \
        calculateDewpointDepression(dewpt_data, dewpt_first_hour,
                                    temp_data, temp_base_hour)
        addElementDatasets(manager, station, 'dewpt_depr', depr_data,
                           first_hour, last_hour, units=temp_attrs['units'],
                           min=N.nanmin(depr_data), max=N.nanmax(depr_data),
                           missing=-32768)
        del depr_data
        depr_data = None

        caveat = "%s (calculated using Temperature and Relative Humidity)"
        description = caveat % ELEMENTS[element].description
        addElementDatasets(manager, station, 'dewpt', dewpt_data,
                           dewpt_first_hour, dewpt_last_hour, 
                           description=description, units=temp_attrs['units'],
                           min=N.nanmin(dewpt_data), max=N.nanmax(dewpt_data),
                           missing=-32768)
        del dewpt_data
        dewpt_data = None

    if rhum_data is not None:
        addElementDatasets(manager, station, 'rhum', rhum_data,
                           rhum_first_hour, rhum_last_hour, **rhum_attrs)
        del rhum_data
        rhum_data = None

    if temp_data is not None:
        addElementDatasets(manager, station, 'temp', temp_data,
                           temp_first_hour, temp_last_hour, **temp_attrs)
        del temp_data
        temp_data = None

    manager.setFileAttribute('first_hour',earliest_hour)
    manager.setFileAttribute('last_hour',latest_hour)
    manager.closeFile()
    print 'created file for %s at %s' % (station['name'], filepath)
    sys.stdout.flush()
    sys.stderr.flush()


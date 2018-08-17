#! /Users/rem63/venvs/nrcc_prod/bin/python

import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

import numpy as N

from rccpy.utils.data import validValues
from rccpy.utils.options import optionsAsDict, stringToTuple
from rccpy.utils.timeutils import asDatetime, isLeapYear
from rccpy.utils.timeutils import dateAsInt, decodeIntegerDate
from rccpy.utils.units import getConversionFunction

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DATASET_MSG = 'saved %s %s dataset for station %d'
DATE_FORMULA = 'year*10000 + month*100 + day'
CALC_STATS_FOR = ('srad','st4i','st8i','temp')
PROCESSING_MSG = 'processing %s hours dataset for station %d'
SKIPPING_MSG = 'skipping %s hours dataset for station %d'
TOO_SHORT_MSG = 'Insufficient time span : %d years required, %d years available'
SEARCH_KEYS = ('bbox','network','sid','ucanid')

OBJECT_DESCRIPTIONS = {
       'element.mean' : 'average element for each hour',
       'element.mean' : 'average element for each hour',
       'element.stddev' : 'standard deviation of element for each hour',

       'element.mean' : 'average element for each hour',
       'element.mean' : 'average element for each hour',
       'element.stddev' : 'standard deviation of element for each hour',

       'element.mean' : 'average element for each hour',
       'element.mean' : 'average element for each hour',
       'element.stddev' : 'standard deviation of element for each hour',

       'element.mean' : 'average element for each hour',
       'element.mean' : 'average element for each hour',
       'element.stddev' : 'standard deviation of element for each hour',

       }
DATASET_KEYS = [key for key in OBJECT_DESCRIPTIONS.keys() if '.' in key]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def relativeHours(hours):
    days = hours / 24
    hours = hours % 24
    return relativedelta(days=days, hours=hours)

def timediff(start_hour, last_hour):
    delta = last_hour - start_hour
    return (delta.days * 24) + (delta.seconds / 3600)

def transformInput(dataset_name, data, missing=-32768):
    data = N.array(data, dtype=float)
    if N.isfinite(missing): data[N.where(data==missing)] = N.inf
    if dataset_name in('pcpn','srad'): data /= 100.0
    return data

def transformOutput(dataset_name, data, missing=-32768):
    if dataset_name in ('pcpn','srad'): data *= 100
    data[N.where(N.isnan(data))] = missing
    data[N.where(N.isinf(data))] = missing
    return N.array(data, dtype='i2')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('--bbox', action='store', type='string', dest='bbox',
                  default=None)
parser.add_option('--county', action='store', type='string', dest='county',
                  default=None)
parser.add_option('--id', action='store', type='string', dest='id',
                  default=None)
parser.add_option('--network', action='store', type='string', dest='network',
                  default=None)
parser.add_option('--state', action='store', type='string', dest='state',
                  default=None)

parser.add_option('--dd', action='store', type='int', dest='duration_days',
                  default=9)
parser.add_option('--dh', action='store', type='int', dest='duration_hours',
                  default=3)
parser.add_option('-e', action='store', type='string', dest='elements',
                  default=None)
parser.add_option('--my', action='store', type='int', dest='min_year_span',
                  default=15)
parser.add_option('--pm', action='store', type='int', dest='percent_missing',
                  default=10)
parser.add_option('--rr', action='store', type='int', dest='report_rate',
                  default=0)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-x', action='store_true', dest='replace_existing',
                  default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
duration_days = options.duration_days
days_cushion = duration_days / 2
if duration_days == days_cushion * 2:
    raise ValueError, 'Value of --dd option must be an odd number.'
duration_hours = options.duration_hours
hours_cushion = duration_hours / 2
if duration_hours == hours_cushion * 2:
    raise ValueError, 'Value of --dh option must be an odd number.'
if options.elements is None:
    elements = CALC_STATS_FOR
else:
    elements = stringToTuple(options.elements)
min_year_span = options.min_year_span
percent_missing = options.percent_missing
report_rate = options.report_rate
replace_existing = options.replace_existing

max_sample_size = durtions_days * durations_hours
min_sample_size = int(max_sample_size * (1.0 - (percent_missing / 100.)))
rel_hours_cushion = relativedelta(hours=hours_cushion)

# create a factory, then use it to get the list of stations
factory = ObsnetDataFactory(options)
if len(args) > 0:
    ucanids = [int(arg) for arg in args]
else:
    criteria = factory._validCriteria(options, SEARCH_KEYS)
    ucanids = factory.getStationIdsFromArgs(args, criteria)

# apply rule to replace existing data files
if replace_existing:
    for ucanid in ucanids:
        filepath = factory.getFilepathForUcanid(ucanid,'hour-stats')
        if os.path.exists(filepath): os.remove(filepath)
else:
    ucanids = [uid for uid in ucanids
              if not os.path.exists(factory.getFilepathForUcanid(uid,'hour-stats'))]

# process each station in the list
for ucanid in ucanids:

    hours_manager = factory.getStationFileManager((ucanid,'hours'), 'r')
    if options.elements is None:
        elements = hours_manager.hdf5_file.keys()
    else:
        elements = stringToTuple(options.elements)

    stats_manager = factory.getStationFileManager((ucanid,'hour-stats'), 'w')
    stats_manager.setFileAttributes(**hours_manager.getFileAttributes())
    stats_manager.setFileAttribute('created', stats_manager._timestamp())

    earliest_hour = 9999999999
    latest_hour = -32768

    for element in elements:
        if debug:
            print ' '
            print ' '

        # get start/end time
        hours_attrs = hours_manager.getDataAttributes('%s.date' % element)
        first_hour = tuple(hours_attrs['first_hour'])
        earliest_hour = min(earliest_hour, dateAsInt(first_hour))
        base_hour = datetime(*first_hour)
        
        last_hour = tuple(hours_attrs['last_hour'])
        latest_hour = max(latest_hour, dateAsInt(last_hour))
        last_hour = datetime(*last_hour)
        num_years = (last_hour.year - first_hour.year) + 1
        if num_years < min_year_span:
            print SKIPPING_MSG % (element, ucanid)
            print TOO_SHORT_MSG % (min_year_span, num_years)
            continue
        else:
            print PROCESSING_MSG % (element, ucanid)


        raw_data, raw_attrs = hours_manager.getData('%s.value' % element, True)
        raw_data = transformInput(element, raw_data, N.nan)
        raw_hour_index = hours_cushion
        last_index = len(raw_data) - hours_cushion

        current_year = current_hour.year
        is_leap_year = isLeapYear(current_year)
        year_index = 0

        current_month = current_hour.month
        is_leap_month = iis_leap_year and current_month == 2

        currrent_hour = base_hour + rel_hours_cushion

        hour_matrix = [ [ [ ] for i in range(24) ] for j in range(365) ]
        while raw_hour_index <= last_index:
            if current_hour.year != current_year:
                current_year = current_hour.year
                is_leap_year = isLeapYear(current_year)
                year_index += 1
                current_month = 0 # force next if statement to fire
            if current_hour.month != current_month:
                current_month = current_hour.month
                is_leap_month = is_leap_year and current_month == 2
            if is_leap_month and current_hour.day == 29:
                raw_hour_index += 2
            else:
                start_index = raw_hour_index - hours_cushion
                end_index = raw_hour_index + hours_cushion
                data = raw_data[start_index:end_index]
                data = list(data[N.where(N.isfinite(data))])
                num_hours = len(data)
                if num_hours > 0:
                    julian = current_hour.timetuple().tm_yday - 1
                    hour_matrix[julian,current_hour.hour].extend(data)
                raw_hour_index += 1

        # save the stats as datasets
        attrs = { 'created' : created,
                  'description' : DESCRIPTIONS[element],
                  'first_date' : (base_hour+rel_hours_cushion).timetuple()[:4],
                  'frequency' : 'day',
                  'interval' : 1,
                  'last_date' : (last_hour-rel_hours_cushion).timetuple()[:4],
                }
        stats_manager.createGroup(element, attrs)
        print 'created %s data group' % element

        # build stats datasets
        count_matrix = N.zeros((365,24),'i2')
        hourly_means = N.empty((365,24), float)
        hourly_means.fill(N.nan)
        hourly_stddevs = N.empty((365,24), float)
        hourly_stddevs.fill(N.nan)
        for i in range(365):
            for j in range(24):
                data = N.array(hour_matrix[i,j])
                if len(data) >= min_sample_size:
                    count_matrix[i,j] = len(data)
                    hourly_means[i,j] = N.mean(data)
                    hourly_stddevs[i,j] = N.std(data)

        # save the stats datasets
        dataset_name = '%s.count' % element
        attrs = { 'created' : created,
                  'description' : OBJECT_DESCRIPTIONS[dataset_name],
                  'last_date' : last_date,
                  'format' : 'year*10000+month*100+day',
                  'frequency' : 'day',
                  'interval' : 1,
                  'report_time' : '%02d:00' % target_hour,
                  'first_date' : first_date,
                }
        dates = [year*10000 + month*100 + day for (year,month,day) in dates]
        stats_manager.createDataset(dataset_name, N.array(dates, dtype='i4'),
                                   attrs)

    hours_manager.closeFile()

    stats_manager.setFileAttribute('earliest_date',
                                  decodeIntegerDate(earliest_hour)[:3])
    stats_manager.setFileAttribute('latest_date',
                                  decodeIntegerDate(latest_hour)[:3])
    stats_manager.closeFile()


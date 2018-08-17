
from datetime import datetime
from dateutil.relativedelta import relativedelta

import numpy as N

from rccpy.utils.timeutils import asDatetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DATE_ARRAY_GENERATORS = { }
DATE_STRING_FORMATS = { 'hour' : '%Y-%m-%d-%H', 'day' : '%Y-%m-%d',
                        'month' : '%Y-%m', 'year' : '%Y' }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def generateHoursArray(start_hour, end_hour, **kwargs):
    first_hour = asDatetime(start_hour)
    last_hour = asDatetime(end_hour)
    interval = relativedelta(hours=int(kwargs.get('interval',1)))
    date_format = kwargs.get('date_format', None)
    as_numpy = kwargs.get('as_numpy', True)

    hours = [ ]
    hour = first_hour
    if date_format in (datetime,object,'object'):
        while hour <= last_hour:
            hours.append(hour)
            hour += interval
        dtype = 'object'
        as_numpy = False

    elif date_format in (int,'int'):
        while hour <= last_hour:
            hours.append( (hour.year * 1000000) + (hour.month * 10000) +
                          (hour.day * 100) + hour.hour )
            hour += interval
        dtype = N.dtype(int)

    elif date_format == 'tuple':
        while hour <= last_hour:
            hours.append((hour.year,hour.month,hour.day,hour.hour))
            hour += interval
        dtype = N.dtype( { 'names':['year','month','day','hour'],
                           'formats':['i2','i2','i2','i2'] } )

    else:
        if date_format is None: date_format = '%Y-%m-%d-%H'
        while hour <= last_hour:
            hours.append(hour.strftime(date_format))
            hour += interval
        dtype='|S%d' % len(hours[0])

    if as_numpy: return N.array(hours, dtype=dtype)
    else: return tuple(hours)

DATE_ARRAY_GENERATORS['hour'] = generateHoursArray

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def generateDaysArray(start_date, end_date, **kwargs):
    first_date = asDatetime(start_date)
    last_date = asDatetime(end_date)
    interval = relativedelta(days=int(kwargs.get('interval',1)))
    date_format = kwargs.get('date_format', None)
    as_numpy = kwargs.get('as_numpy', True)

    days = [ ]
    date = first_date
    if date_format in (datetime,object,'object'):
        while date <= last_date:
            days.append(date)
            date += interval
        dtype = 'object'
        as_numpy = False

    elif date_format in (int,'int'):
        while date <= date_hour:
            days.append( (date.year * 10000) + (date.month * 100) + date.day )
            date += interval
        dtype = int

    elif date_format == 'tuple':
        while date <= last_date:
            days.append((date.year,date.month,date.day))
            date += interval
        dtype = N.dtype( { 'names':['year','month','day'],
                           'formats':['i2','i2','i2'] } )

    else:
        if date_format is None: date_format = '%Y-%m-%d'
        while date <= last_date:
            days.append(date.strftime(date_format))
            date += interval
        dtype='|S%d' % len(days[0])

    if as_numpy: return N.array(days, dtype=dtype)
    else: return tuple(days)

DATE_ARRAY_GENERATORS['day'] = generateDaysArray

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def generateMonthsArray(start_date, end_date, **kwargs):
    first_date = asDatetime(start_date)
    last_date = asDatetime(end_date)
    interval = relativedelta(days=int(kwargs.get('interval',1)))
    date_format = kwargs.get('date_format', None)
    as_numpy = kwargs.get('as_numpy', True)

    months = [ ]
    date = first_date
    if date_format in (datetime,object,'object'):
        while date <= last_date:
            months.append(date)
            date += interval
        dtype = 'object'
        as_numpy = False

    elif date_format in (int,'int'):
        while date <= last_date:
            months.append( (date.year * 100) + date.month )
            date += interval
        dtype = 'i2'

    elif date_format == 'tuple':
        while date <= last_date:
            months.append((date.year,date.month))
            date += interval
        dtype = N.dtype( { 'names':['year','month'],'formats':['i2','i2'] } )

    else:
        if date_format is None: date_format ='%Y-%m'
        while date <= last_date:
            months.append(date.strftime(date_format))
            date += interval
        dtype='|S%d' % len(months[0])

    if as_numpy: return N.array(months, dtype=dtype)
    else: return tuple(months)

DATE_ARRAY_GENERATORS['month'] = generateMonthsArray

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def generateYearsArray(start_year, end_year, **kwargs):
    first_year = asDatetime(start_year)
    last_year = asDatetime(end_year)
    interval = relativedelta(years=int(kwargs.get('interval',1)))
    date_format = kwargs.get('date_format', None)
    as_numpy = kwargs.get('as_numpy', True)

    years = [ ]
    date = first_year
    if date_format in (datetime,object,'object'):
        while date <= last_year:
            years.append(date)
            date += interval
        dtype = 'object'
        as_numpy = False

    elif date_format in (int,'int'):
        while date <= last_year:
            years.append(date.year)
            date += interval
        dtype = 'i2'

    else:
        if date_format is None: date_format ='%Y'
        while date <= last_year:
            years.append(date.strftime(date_format))
            date += interval
        dtype='|S%d' % len(years[0])

    if as_numpy: return N.array(years, dtype=dtype)
    else: return tuple(years)

DATE_ARRAY_GENERATORS['year'] = generateYearsArray

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def dateArrayGenerator(frequency):
    arrayGenerator = DATE_ARRAY_GENERATORS.get(frequency)
    if arrayGenerator is None:
        raise ValueError, 'No date generator for %s frequency' % frequency
    return arrayGenerator


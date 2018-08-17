
import datetime
from dateutil.relativedelta import relativedelta
from copy import copy
from pytz import timezone
import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

SMALLEST_YEAR_INT = 1800
SMALLEST_DATE_INT = SMALLEST_YEAR_INT * 10000
SMALLEST_TIME_INT = SMALLEST_DATE_INT * 100

LARGEST_YEAR_INT = 2199
LARGEST_DATE_INT = (LARGEST_YEAR_INT * 10000) + 1231
LARGEST_TIME_INT = (LARGEST_DATE_INT * 100) + 23

MONTHS = ('Jan','Feb','Mar','Apr','May','Jun',
          'Jul','Aug','Sep','Oct','Nov','Dec')
MONTH_NAMES = ('January','February','March','April','May','June','July',
               'August','September','October','November','December')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

EASTERN_TIMEZONE = timezone('US/Eastern')

def isDaylightSavingsTime(date):
    if isinstance(date, (datetime.datetime, datetime.date)):
        noon = datetime.datetime(*date.timetuple()[:3], hour=12)
    elif type(date) in (tuple,list) and len(date) >= 3:
        noon = datetime.datetime(*date, hour=12)
    local = EASTERN_TIMEZONE.localize(noon)
    if local.dst() is not None: return True
    return False

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def isLeapYear(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def isLeapDay(date):
    if isinstance(date, (datetime.datetime, datetime.date)):
        return date.day == 29 and date.month == 2 and isLeapYear(date.year)
    elif type(date) in (tuple,list) and len(date) >= 3:
        return date[2] == 29 and date[1] == 2 and isLeapYear(date[0])
    raise ValueError, 'Invalid date : %s : %s' % (str(date),type(date))

def daysInYear(year):
    if isLeapYear(year): return 366
    return 365

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def lastDayOfMonth(year, month):
    if month in (1,3,5,7,8,10,12):
        return 31
    elif month in (4,6,9,11):
        return 30
    else:
        if isLeapYear(year): return 29
        return 28

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def decodeIntegerDate(date):
    if date > 1000000000: # YYYYMMDDHH
        return ( date/1000000, (date/10000) % 100, (date/100) % 100,
                 date % 100  )
    elif date > 10000000: # YYYYMMDD
        return ( date/10000, (date/100) % 100, date % 100, 0 )
    elif date > 100000: #YYYYMM
        return ( date/100, date % 100, 1, 0 )
    else:
        raise ValueError, 'Invalid integer date : %d' % date

def asDatetime(date, separator='-'):
    if isinstance(date,datetime.datetime): return date
    elif isinstance(date,datetime.date):
       return datetime.datetime(date.year,date.month,date.day,0)

    if isinstance(date,basestring):
        if separator in date:
            date = [int(item) for item in date.split(separator)]
        elif date.isdigit():
            date = decodeIntegerDate(int(date))
        else:
            raise ValueError, 'Invalid date string : %d' % date
    elif isinstance(date,(int,long,N.int16,N.int32,N.int64)):
        date = decodeIntegerDate(date)
    elif date.__class__.__name__ == 'ndarray':
        date = tuple(date)

    if isinstance(date,(tuple,list,N.ndarray)):
        date = list(date)
        if len(date) == 2: date.append(1)
        if len(date) == 3: date.append(0)
        return datetime.datetime(*date)

    raise ValueError, 'Unsupported type for date : %s' % date.__class__.__name__

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def dateStringToTuple(whatever, need_hour=False):
    """ Converts a tuple, list, int, long or string into a date string
    with a consistent format, either "YYYYMMDD" or "YYYYMMDDHH" when
    the hour is present.
    """
    if not isinstance(whatever, basestring):
        raise TypeError, 'Unsupported type for dte string : %s' % type(whatever)

    if whatever.isdigit():
        if len(whatever) == 8:
            # test for year as 1st element
            if int(whatever[:4]) >= SMALLEST_YEAR_INT:
                year = int(whatever[:4])
                month = int(whatever[4:6])
                day = int(whatever[6:])
            # test for year as last element
            elif int(whatever[4:]) >= SMALLEST_YEAR_INT:
                year = int(whatever[4:])
                month = int(whatever[:2])
                day = int(whatever[2:4])
            else:
                errmsg = 'Unable to parse date string : %s'
                raise ValueError, errmsg % whatever
            hour = 0
        elif len(date_str) == 10:
            if int(whatever[:4]) >= SMALLEST_YEAR_INT:
                year = int(whatever[:4])
                month = int(whatever[4:6])
                day = int(whatever[6:8])
            elif int(whatever[4:8]) >= SMALLEST_YEAR_INT:
                year = int(whatever[4:8])
                month = int(whatever[:2])
                day = int(whatever[2:4])
            else:
                errmsg = 'Unable to parse date string : %s'
                raise ValueError, errmsg % whatever
            hour = int(whatever[8:])
        else:
            errmsg = 'Unable to parse date string : %s'
            raise ValueError, errmsg % whatever

    else:
        if '-' in whatever: parts = whatever.split('-')
        elif '/' in whatever: parts = whatever.split('/')
        elif '.' in whatever: parts = whatever.split('.')
        else:
            errmsg = 'Unable to parse date string : %s'
            raise ValueError, errmsg % whatever

        if len(parts[0]) == 4:
            year = int(parts[0])
            month = int(parts[1])
            if len(parts) == 3:
                if ':' in parts[2]:
                    day, hour = [int(part) for part in parts[2].split(':')]
                else:
                    day = int(parts[2])
                    hour = 0
            elif len(parts) == 4:
                day = int(parts[2])
                hour = int(parts[3])
            else:
                errmsg = 'Unable to parse date string : %s'
                raise ValueError, errmsg % whatever

        elif len(parts[2]) == 4:
            month = int(parts[0])
            day = int(parts[1])
            if len(parts) == 3:
                if ':' in parts[2]:
                    year, hour = [int(part) for part in parts[2].split(':')]
                else:
                    year = int(parts[2])
                    hour = 0
            elif len(parts) == 4:
                year = int(parts[2])
                hour = int(parts[3])
            else:
                errmsg = 'Unable to parse date string : %s'
                raise ValueError, errmsg % whatever

        else:
            errmsg = 'Unable to parse date string : %s'
            raise ValueError, errmsg % whatever

    if need_hour: return (year,month,day,hour)
    else: return (year,month,day)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def dateAsString(whatever, need_hour=False, date_format='ymd'):
                
    # convert eveything to a tuple
    if isinstance(whatever, basestring):
        date = dateStringToTuple(whatever, need_hour)
    elif isinstance(whatever, list):
        date = tuple(whatever)
    elif not isinstance(whatever, tuple):
        date = dateAsTuple(whatever, need_hour)

    date = datetime.datetime(*date)
    if date_format == 'ymd':
        if need_hour: format_ = '%Y%m%d%H'
        else: format_ = '%Y%m%d'
        return date.strftime(format_)

    elif date_format == 'mdy':
        if need_hour: format_ = '%m%d%Y%H'
        else: format_ = '%m%d%Y'
        return date.strftime(format_)

    else:
        return date.strftime(date_format)

    errmsg = 'Unsupported date value %s : %s'
    raise ValueError, errmsg % (str(type(whatever)),str(whatever))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def dateAsInt(whatever, need_hour=False):
    """ Converts a tuple, list or string into an integer value. Value
    is either YYYYMMDD or YYYYMMDDHH when hour is present. This function
    will also verify that int and long values follow the rules for integer
    dates.

    NOTE: All generated dates will be validated as reasonable before
    being returned.
    """
    if isinstance(whatever, (int,long,N.int16,N.int32,N.int64)):
        if whatever > 1000000:
            if need_hour: return whatever
            else: whatever / 100
        elif whatever > 10000:
            if need_hour: return whatever * 100
            else: return whatever

    # from here on, it's easier to convert eveything else to a tuple
    if not isinstance(whatever, (tuple,list,N.ndarray)):
        whatever = dateAsTuple(whatever, need_hour)

    tuple_size = len(whatever) 
    if tuple_size not in (3,4):
        errmsg = 'Unsupported date type = %s : value = %s'
        raise ValueError, errmsg % (str(type(whatever)),str(whatever))

    date = 0
    for indx in range(tuple_size):
        date *= 100
        date += whatever[indx]
    if need_hour:
        if tuple_size == 3: date *= 100
        return date
    else:
        if tuple_size == 4: date /= 100
        return date

    errmsg = 'Unsupported date value %s : %s'
    raise ValueError, errmsg % (str(type(whatever)),str(whatever))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def dateAsTuple(whatever, need_hour=False):
    """ Converts a tuple, list, int, long or string into a date string
    with a consistent format, either "YYYYMMDD" or "YYYYMMDDHH" when
    the hour is present.
    """
    if isinstance(whatever, (int,long))\
    or (hasattr(whatever,'dtype') and whatever.dtype.kind == 'i'):
        return decodeIntegerDate(whatever)

    elif isinstance(whatever, datetime.datetime):
        if need_hour: return whatever.timetuple()[:4]
        else: return whatever.timetuple()[:3]

    elif isinstance(whatever, datetime.date):
        if need_hour: return (whatever.year, whatever.month, whatever.day, 0)
        else: return (whatever.year, whatever.month, whatever.day)

    elif isinstance(whatever, basestring):
        return dateStringToTuple(whatever, need_hour)

    elif isinstance(whatever, list):
        date_tuple = tuple(whatever)

    elif isinstance(whatever, tuple):
        date_tuple = copy(whatever)

    else:
        errmsg = 'Unsupported date value %s : %s'
        raise ValueError, errmsg % (str(type(whatever)),str(whatever))

    # sort out what is in the tuple and what was requested
    if len(date_tuple) == 4: # has hour as last component
        if need_hour: return date_tuple
        else: return date_tuple[:-1]
    elif len(date_tuple) == 3: # hour not included
        if date_tuple[2] >= SMALLEST_YEAR_INT: # year is last element
            date_tuple = (date_tuple[2],date_tuple[0],date_tuple[1])
        if need_hour: date_tuple += (0,)
        return date_tuple
    elif len(date_tuple) > 4:
        if need_hour: return date_tuple[:4]
        else: return date_tuple[:3]

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def timeSpanToIntervals(start_time, end_time, hours_per_interval,
                        first_hour_of_day=0):
    _date_time = start_time
    
    if hours_per_interval > 1:
        num_intervals_in_day = 24 / hours_per_interval
        daily_intervals = [ intvl*hours_per_interval
                            for intvl in range(num_intervals_in_day)]

        # need first interval at or after start_time
        if start_time.hour > daily_intervals[-1]:
            first_interval = 0
            _date_time = datetime.datetime(start_time.year,start_time.month,
                                           start_time.day,0)
            _date_time += relativedelta(days=1)
        else:
            first_interval = [intvl for intvl in daily_intervals
                              if intvl >= start_time.hour][0]
            _date_time = datetime.datetime(start_time.year,start_time.month,
                                           start_time.day,first_interval)

    interval_delta = relativedelta(hours=hours_per_interval)
    intervals = [ ]

    while _date_time <= end_time:
        date = indexableDate(_date_time)
        hour = _date_time.hour
        intervals.append((date,hour))
        _date_time += interval_delta

    return tuple(intervals)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def timeSpan(target_date, target_hour, duration, hours_per_interval):
    """ Simple time span calculation, no UTC corrections or `cushion`
    intervals

    Returns start time and end time of the time span as datetime objects
    """
    date = target_date.timetuple()[:3]
    end_time = datetime.datetime(*date, hour=target_hour)
    start_time = end_time - relativedelta(hours=duration-1)

    return start_time, end_time

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def utcTimeSpan(target_date, target_hour, duration, hours_per_interval,
                cushion=0, east_utc_limit=None, west_utc_limit=None,
                debug=False):
    """ Calculates the start_time and end_time spanning 'duration' hours.
    Applies appropriate east and west UTC corrections so that intervals
    required for both east coast and west coast calculations are included.
    Additionally allows for 'cushion' intervals at either end of the time
    span so that spline interpolations won't produce end artifacts within
    the useful intervals.

    Returns UTC start time and UTC end time of the time span as datetime
    objects
    """
    # Target date and hour are specified in US Eastern time.
    #
    # Assume that time in interval data grids is in hours since UTC 0Z
    # and models report each day from 00Z t0 23Z where 0Z is MIDNIGHT
    # and 11Z is NOON

    # target date and hour are the basis for the END of the time span
    if isinstance(target_date, (datetime.datetime,datetime.date)):
        date = target_date.timetuple()[:3]
        target_date_and_hour = datetime.datetime(*date, hour=target_hour)
    else:
        target_date_and_hour = datetime.datetime(*target_date,
                                                 hour=target_hour)

    # In order to access data for the correct interval from the
    # model's files, we need the corrsponding UTC time.
    # Start with the UTC offsets for the Eastern time zone 
    if isDaylightSavingsTime(target_date):
        eastern_timezone_offset = -4
        # east/west limits were passed as EST offsests so they need to
        # be adjusted to DST
        east_utc_limit += 1
        west_utc_limit += 1
    else:
        eastern_timezone_offset = -5

    if debug:
        print 'target', target_date_and_hour
        print 'Eastern TZ offset', eastern_timezone_offset
        print 'East UTC limit', east_utc_limit
        print 'West UTC limit', west_utc_limit
    #
    # Because the input is date/time from US time zones, the UTC time
    # is LATER in the day.  Since standard UTC offsets are negative in
    # the US, we must add the absolute value of the UTC offset to the
    # US time.
    #
    # In this step, we are only interested in the Eastern time
    # adjustments for other time zones are made later.
    relative_utc_offset = relativedelta(hours=abs(eastern_timezone_offset))
    end_time = target_date_and_hour + relative_utc_offset
    if hours_per_interval > 1 and (end_time.hour % hours_per_interval) > 0:
        end_hour = (end_time.hour / hours_per_interval) * hours_per_interval
        end_hour += hours_per_interval
        if end_hour < 24:
            end_time += relativedelta(hours=end_hour-end_time.hour)
        else:
            end_time -= relativedelta(hours=end_time.hour)
            end_time += relativedelta(days=1, hours=end_hour-24)
    #
    # still workiing strictly in Eastern time zone ....
    # start time is 'duration' earlier than end time. However,
    # 'duration' is inclusive of start and end, so we really
    # need to subtract one less hour
    start_time = end_time - relativedelta(hours=duration-1)

    if debug:
        print 'Eastern UTC time offset applied:'
        print '   start time', start_time
        print '   end time', end_time

    # start time is now relative to Eastern time, but we will encounter
    # nodes in other US time zones.
    #
    # adjust the end time to account for starting in time zones with
    # UTC offsets greater than Eastern time.
    if east_utc_limit > eastern_timezone_offset:
        offset = east_utc_limit - eastern_timezone_offset
        start_time -= relativedelta(hours=offset)

        if debug:
            print 'East time zone adjustements applied:'
            print '   start time', start_time
            print '   end time', end_time
            print '   start offset applied', offset
    #
    # adjust the start time to account for ending time zones with UTC
    # offsets less than Eastern time.
    if west_utc_limit < eastern_timezone_offset:
        offset = eastern_timezone_offset - west_utc_limit 
        end_time += relativedelta(hours=offset)

        if debug:
            print 'West time zone adjustements applied:'
            print '   start time', start_time
            print '   end time', end_time
            print '   end offset applied', offset

    # may need at least one interval 'cushion' at either end of the time
    # span so that spline interpolations won't produce end artifacts
    # within the useful intervals.
    # Also need to take into account models where the time b/w
    # intervals is not 1 hour
    offset = relativedelta(hours=cushion*hours_per_interval)
    start_time -= offset
    end_time += offset

    if debug:
        print 'Cushion adjustements applied:'
        print '   start time', start_time
        print '   end time', end_time
        print '   offset applied', offset.hours

    return start_time, end_time


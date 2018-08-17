import datetime
from dateutil.relativedelta import relativedelta

from rccpy.utils.timeutils import lastDayOfMonth

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

VALID_FREQUENCIES = ('hour','day','month','year')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def monthsDuration(date, duration):
    # always return a calendar month
    #
    # date is the last day of a month
    if date.day == lastDayOfMonth(date.year,date.month):
        month = date.month - duration + 1
        if month < 1:
            month += 12
            year = date.year - 1
        else: year = date.year
        return datetime.datetime(year, month, 1) # day is always 1
    # date is not last day of month
    else:
        month = date.month - duration
        if month < 1:
            month += 12
            year = date.year - 1
        else: year = date.year
        _date = datetime.datetime(year, month, date.day)
        return _date + relativedelta(days=1)

def monthsInterval(date, interval):
    # always return a calendar month
    month = date.month + interval
    if month > 12:
        month -= 12
        year = date.year + 1
    else: year = date.year
    # passed date is the last day of a month
    if date.day == lastDayOfMonth(date.year,date.month):
        return datetime.datetime(year, month, lastDayOfMonth(year,month))
    # passed date is not last day of month
    else:
        return datetime.datetime(year, month, date.day)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def yearsDuration(date, duration):
    # always return a calendar year
    year = date.year - duration
    #
    # date is the last day of a month
    if date.day == lastDayOfMonth(date.year,date.month):
        day = lastDayOfMonth(year,date.month) # in case it is Febraury
        _date = datetime.datetime(year, date.month, day)
    # date is not last day of month
    else:
        _date = datetime.datetime(year, date.month, date.day)
    return _date + relativedelta(days=1)

def yearsInterval(date, interval):
    # always return a calendar year
    year = date.year + interval
    # passed date is the last day of a month
    if date.day == lastDayOfMonth(date.year,date.month):
        return datetime.datetime(year, date.month,
                                 lastDayOfMonth(year,date.month))
    # passed date is not last day of month
    else:
        return datetime.datetime(year, date.month, date.day)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TimeIterator(object):

    def __init__(self, iter_start, iter_end, interval=1, duration=1):
        self.iter_start, self.iter_end = self.setTimeSpan(iter_start, iter_end)
        if self.iter_start > self.iter_end:
            errmsg = 'Interval start time (%s) is later than interval end time (%s)'
            raise ValueError, errmsg % (iter_start.strftime("%Y-%m-%d:%H"),
                                        iter_end.strftime("%Y-%m-%d:%H"))

        self._interval_func, self._interval_type, self._interval = \
                                             self.setInterval(interval)
        self._duration_func, self._duration_type, self._duration = \
                                                  self.setDuration(duration)
        self._current_end = None

    def __iter__(self):
        return self

    def next(self):
        if self._current_end != None:
            self._current_end = self._interval_func(self._current_end)
        else:
            self._current_end = self.iter_start
        if self._current_end <= self.iter_end:
            return self._duration_func(self._current_end), self._current_end
        raise StopIteration

    def setTimeSpan(iter_start, iter_end):
        raise NotImplementedError

    def setInterval(interval):
        raise NotImplementedError

    def setDuration(duration):
        raise NotImplementedError


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class HourIterator(TimeIterator):

    def setTimeSpan(self, iter_start, iter_end):

        if not isinstance(iter_start, datetime.datetime):
            if isinstance(iter_start, datetime.date):
                iter_start = datetime.datetime.combine(iter_start,
                                                       datetime.time(0))

            elif isinstance(iter_start, (list,tuple)):
                if len(iter_start) == 3:
                   iter_start = datetime.datetime(iter_start[0], iter_start[1],
                                                  iter_start[2], 0)
                elif len(iter_start) == 4:
                   iter_start = datetime.datetime(*iter_start)
                else:
                    errmsg = 'Invalid date/time for iter_start : %s = %s'
                    raise ValueError, errmsg % (iter_start.__class__.__name__,
                                                str(iter_start))
            else:
                errmsg = 'Invalid type for iter_start : %s = %s' 
                raise TypeError, errmsg % (interval.__class__.__name__,
                                           str(interval))

        if not isinstance(iter_start, datetime.datetime):
            if isinstance(iter_end, datetime.date):
                iter_end = datetime.datetime.combine(iter_end,datetime.time(23))

            elif isinstance(iter_end, (list,tuple)): 
                if len(iter_end) == 3:
                    iter_end = datetime.datetime(iter_end[0],iter_end[1],
                                                 iter_end[2],23)
                elif len(iter_start) == 4:
                    iter_end = datetime.datetime(*iter_end)
                else:
                    errmsg = 'Invalid date/time %s for iter_end : %s'
                    raise ValueError, errmsg % (iter_end.__class__.__name__,
                                                str(iter_end))
            else:
                errmsg = 'Invalid type for iter_end : %s = %s' 
                raise TypeError, errmsg % (iter_end.__class__.__name__,
                                           str(iter_end))

        return iter_start, iter_end

    def setInterval(self, interval):
        if isinstance(interval, int):
            interval_func = lambda dt : dt + relativedelta(hours=interval)
            return interval_func, 'hour', interval

        elif isinstance(interval, basestring):
            if interval == 'hour':
                interval_func = lambda dt : dt + relativedelta(hours=1)
            elif interval == 'day' :
                interval_func = lambda dt : dt + relativedelta(days=1)
            elif interval == 'month' :
                interval_func = lambda dt : self._monthsInterval(dt, 1)
            else :
                raise ValueError, 'Invalid value for interval : %s' % interval
            return interval_func, interval, 1

        elif isinstance(interval, (list,tuple)) and len(interval) == 2:
            if not isinstance(interval[0], basestring) \
            or not isinstance(interval[1], int):
                errmsg = 'Invalid value for interval : %s = %s'
                raise ValueError, errmsg % (interval.__class__.__name__,
                                            str(interval))
            if interval[0] == 'hour':
                interval_func = lambda dt : dt + relativedelta(hours=interval[1])
            elif interval[0] == 'day':
                interval_func = lambda dt : dt + relativedelta(days=interval[1])
            elif interval[0] == 'month':
                interval_func = lambda dt : self._monthsInterval(dt, interval[1])
            else :
                errmsg = 'Invalid value for interval : %s = %s'
                raise ValueError, errmsg % (interval.__class__.__name__,
                                            str(interval))
            return interval_func, interval[0], interval[1]

        errmsg = 'Invalid type for interval : %s = %s' 
        raise TypeError, errmsg % (interval.__class__.__name__, str(interval))

    def setDuration(self, duration):
        if isinstance(duration, int):
            duration_func = lambda dt : dt - relativedelta(hours=duration-1)
            return duration_func, 'hour', duration

        elif isinstance(duration, basestring):
            if duration == 'hour':
                duration_func = lambda dt : dt - relativedelta(hours=0)
            elif duration == 'day':
                duration_func = lambda dt : dt - relativedelta(days=1)
            elif duration == 'month':
                duration_func = lambda dt : self._monthsDuration(dt, 1)
            else:
                errmsg = 'Invalid value for duration : %s = %s' 
                raise ValueError, errmsg % (duration.__class__.__name__,
                                            str(duration))
            return duration_func, duration, 1

        elif isinstance(duration, (tuple,list)) and len(duration) == 2:
            if not isinstance(duration[0], basestring) \
            or not isinstance(duration[1], int):
                errmsg = 'Invalid value for duration : %s = %s' 
                raise ValueError, errmsg % (duration.__class__.__name__,
                                            str(duration))
            
            if duration[0] == 'hour':
                duration_func = lambda dt : dt - relativedelta(hours=duration[1]-1)
            elif duration[0] == 'day':
                duration_func = lambda dt : dt - relativedelta(days=duration[1])
            elif duration[0] == 'month':
                duration_func = lambda dt : self._monthsDuration(dt, duration[1])
            else:
                errmsg = 'Invalid value for duration : %s = %s' 
                raise ValueError, errmsg % (duration.__class__.__name__,
                                            str(duration))
            return duration_func, duration[0], duration[1]

        errmsg = 'Invalid type for duration : %s' 
        raise TypeError, errmsg % (duration.__class__.__name__, str(duration))

    def _monthsDuration(self, date, interval):
        _date = _monthsDuration(date,interval)
        _date = datetime.datetime(_date.year, _date.month, _date.day, date.hour)
        return _date + relativedelta(hours=1)

    def _monthsInterval(self, date, interval):
        _date = monthsInterval(date,interval)
        return datetime.datetime(_date.year, _date.month, _date.day, date.hour)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DayIterator(TimeIterator):
    
    def setTimeSpan(self, iter_start, iter_end):
        if isinstance(iter_start, (list,tuple)):
            if len(iter_start) == 2:
                iter_start = (iter_start[0], iter_start[1],
                              lastDayOfMonth(*iter_start))
            iter_start = datetime.date(*iter_start)
        elif not isinstance(iter_start, datetime.date):
            errmsg = 'Invalid type for iter_start : %s' 
            raise TypeError, errmsg % (iter_start.__class__.__name__,
                                       str(iter_start))

        if isinstance(iter_end, (list,tuple)):
            if len(iter_end) == 2:
                iter_end = (iter_end[0], iter_end[1], lastDayOfMonth(*iter_end))
            iter_end = datetime.date(*iter_end)
        elif not isinstance(iter_end, datetime.date):
            errmsg = 'Invalid type for iter_end : %s' 
            raise TypeError, errmsg % (iter_end.__class__.__name__,
                                       str(iter_end))

        return iter_start, iter_end

    def setInterval(self, interval):
        if isinstance(interval, int):
            interval_func = lambda dt : dt + relativedelta(days=interval)
            return interval_func, 'day', interval

        elif isinstance(interval, basestring):
            if interval == 'day':
                interval_func = lambda dt : dt + relativedelta(days=1)
            elif interval == 'month':
                interval_func = lambda dt : monthsInterval(dt,1)
            elif interval == 'year':
                interval_func = lambda dt : yearsInterval(dt,1)
            else :
                raise ValueError, 'Invalid value for interval : %s' % interval
            return interval_func, interval, 1

        elif isinstance(interval, (list,tuple)) and len(interval) == 2:
            if not isinstance(interval[0], basestring) \
            or not isinstance(interval[1], int):
                errmsg = 'Invalid value for interval : %s = %s' 
                raise ValueError, errmsg % (interval.__class__.__name__,
                                            str(interval))
            if interval[0] == 'day':
                interval_func = lambda dt : dt + relativedelta(days=interval[1])
            elif interval[0] == 'month':
                interval_func = lambda dt : monthsInterval(dt,interval[1])
            elif interval[0] == 'year':
                interval_func = lambda dt : yearsInterval(dt,interval[1])
            else:
                errmsg = 'Invalid value for interval : %s = %s'
                raise ValueError, errmsg % (interval.__class__.__name__,
                                            str(interval))
            return interval_func, interval[0], interval[1]

        errmsg = 'Invalid type for interval : %s = %s' 
        raise TypeError, errmsg % (interval.__class__.__name__, str(interval))

    def setDuration(self, duration):
        if isinstance(duration, int):
            duration_func = lambda dt : dt - relativedelta(days=duration-1)
            return duration_func, 'day', duration

        elif isinstance(duration, basestring):
            if duration == 'day':
                duration_func = lambda dt : dt
            elif duration == 'month':
                duration_func = lambda dt : monthsDuration(dt, 1)
            elif duration == 'year':
                duration_func = lambda dt : yearsDuration(dt, 1)
            else:
                errmsg = 'Invalid value for duration : %s = %s' 
                raise ValueError, errmsg % (duration.__class__.__name__,
                                            str(duration))
            return duration_func, duration, 1

        elif isinstance(duration, (tuple,list)) and len(duration) == 2:
            if not isinstance(duration[0], basestring) \
            or not isinstance(duration[1], int):
                errmsg = 'Invalid value for duration : %s = %s' 
                raise ValueError, errmsg % (duration.__class__.__name__,
                                            str(duration))
            if duration[0] == 'day':
                duration_func = lambda dt : dt - relativedelta(days=duration[1]-1)
            elif duration[0] == 'month':
                duration_func = lambda dt : monthsDuration(dt, duration[1])
            elif duration[0] == 'year':
                duration_func = lambda dt : yearsDuration(dt, duration[1])
            else:
                errmsg = 'Invalid value for duration : %s = %s' 
                raise ValueError, errmsg % (duration.__class__.__name__,
                                            str(duration))
            return duration_func, duration[0], duration[1]

        errmsg = 'Invalid type for duration : %s' 
        raise TypeError, errmsg % (duration.__class__.__name__, str(duration))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class MonthIterator(TimeIterator):
    
    def setTimeSpan(self, iter_start, iter_end):
        if isinstance(iter_start, (list,tuple)):
            if len(iter_start) == 2:
                iter_start = (iter_start[0], iter_start[1],
                              lastDayOfMonth(*iter_start))
            iter_start = datetime.date(*iter_start)
        elif not isinstance(iter_start, datetime.date):
            errmsg = 'Invalid type for iter_start : %s' 
            raise TypeError, errmsg % (iter_start.__class__.__name__,
                                       str(iter_start))

        if isinstance(iter_end, (list,tuple)):
            if len(iter_end) == 2:
                iter_end = (iter_end[0], iter_end[1], lastDayOfMonth(*iter_end))
            iter_end = datetime.date(*iter_end)
        elif not isinstance(iter_end, datetime.date):
            errmsg = 'Invalid type for iter_end : %s' 
            raise TypeError, errmsg % (iter_end.__class__.__name__,
                                       str(iter_end))

        return iter_start, iter_end

    def setInterval(self, interval):
        if isinstance(interval, int):
            interval_func = lambda dt : monthsInterval(dt, interval)
            return interval_func, 'month', interval

        elif isinstance(interval, basestring):
            if interval == 'month':
                interval_func = lambda dt : monthsInterval(dt,1)
            elif interval == 'year':
                interval_func = lambda dt : yearsIntercal(dt,1)
            else :
                raise ValueError, 'Invalid value for interval : %s' % interval
            return interval_func, interval, 1

        elif isinstance(interval, (list,tuple)) and len(interval) == 2:
            if not isinstance(interval[0], basestring) \
            or not isinstance(interval[1], int):
                errmsg = 'Invalid value for interval : %s = %s' 
                raise ValueError, errmsg % (interval.__class__.__name__,
                                            str(interval))
            if interval[0] == 'month':
                interval_func = lambda dt : monthsInterval(dt,interval[1])
            elif interval[0] == 'year':
                interval_func = lambda dt : yearsInterval(dt,interval[1])
            else:
                errmsg = 'Invalid value for interval : %s = %s'
                raise ValueError, errmsg % (interval.__class__.__name__,
                                            str(interval))
            return interval_func, interval[0], interval[1]

        errmsg = 'Invalid type for interval : %s = %s' 
        raise TypeError, errmsg % (interval.__class__.__name__, str(interval))

    def setDuration(self, duration):
        if isinstance(duration, int):
            duration_func = lambda dt : monthsDuration(dt, duration)
            return duration_func, 'month', duration

        elif isinstance(duration, basestring):
            if duration == 'month':
                duration_func = lambda dt : monthsDuration(dt, 1)
            elif duration == 'year':
                duration_func = lambda dt : yearsDuration(dt, 1)
            else:
                errmsg = 'Invalid value for duration : %s = %s' 
                raise ValueError, errmsg % (duration.__class__.__name__,
                                            str(duration))
            return duration_func, duration, 1

        elif isinstance(duration, (tuple,list)) and len(duration) == 2:
            if not isinstance(duration[0], basestring) \
            or not isinstance(duration[1], int):
                errmsg = 'Invalid value for duration : %s = %s' 
                raise ValueError, errmsg % (duration.__class__.__name__,
                                            str(duration))
            if duration[0] == 'month':
                duration_func = lambda dt : monthsDuration(dt, duration[1])
            elif duration[0] == 'year':
                duration_func = lambda dt : yearsDuration(dt, duration[1])
            else:
                errmsg = 'Invalid value for duration : %s = %s' 
                raise ValueError, errmsg % (duration.__class__.__name__,
                                            str(duration))
            return duration_func, duration[0], duration[1]

        errmsg = 'Invalid type for duration : %s' 
        raise TypeError, errmsg % (duration.__class__.__name__, str(duration))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import functools

def season_to_date(dt,season=(1,1)) :
    r = dt + relativedelta(day=season[1],month=season[0])
    if r > dt : r = r - relativedelta(years=1)
    return r

    def block_by_year(self) :
        blk, cYr = [], None
        for sD,eD in self :
            if cYr is None : cYr = eD.year
            if eD.year != cYr :
                if len(blk) > 0 : yield blk
                blk = [(sD,eD)]
                cYr = eD.year
            else : blk.append((sD,eD))
        if len(blk) > 0 : yield blk

class Season_Iterator(object) :
    "Base unit is day"
    kind = "dly"
    precision = 3
    def __init__(self, iter_start, iter_end, interval=1, duration=1) :
        if type(iter_start) in (list,tuple) : iter_start = datetime.date(*iter_start)
        if type(iter_end) in (list,tuple) : iter_end = datetime.date(*iter_end)
        self.iter_start = iter_start
        self.iter_end = iter_end
        if type(interval) == int : self._interval = lambda x : relativedelta(days=(interval*x))
        else :
            if interval == 'dly' : self._interval = lambda x : relativedelta(days=x)
            elif interval == 'mly' : self._interval = lambda x : relativedelta(months=x)
            elif interval == 'yly' : self._interval = lambda x : relativedelta(years=x)
            elif interval[0] == 'dly' :
                self._interval = lambda x : relativedelta(days=interval[1]*x)
            elif interval[0] == 'mly' :
                self._interval = lambda x : relativedelta(months=interval[1]*x)
            else : raise TypeError('invalid interval')
        if type(duration) == int :
            self._duration = lambda x : x - relativedelta(days=duration-1)
        else :
            if duration == 'mtd' : self._duration = lambda x : x - relativedelta(day=1)
            elif duration == 'ytd' : self._duration = lambda x : x - relativedelta(day=1,month=1)
            elif duration[0] == 'std' :
                self._duration = functools.partial(season_to_date,season=duration[1:3])
            elif duration[0] == 'mly' :
                self._duration = lambda x : x - relativedelta(months=duration[1])
            elif duration[0] == 'dly' :
                self._duration = lambda x : x - relativedelta(days=duration[1]-1)
            else : raise TypeError('invalid duration')

        self._index = 0
        self._interval_start = self.start

    def __iter__(self) :
        return self

    def next(self):
        if self._interval_start <= self.end:
            start = self._interval_start
            self._index += 1
            return self._duration(self._cDT), self._cDT
        raise StopIteration

    def block_by_year(self) :
        blk, cYr = [], None
        for sD,eD in self :
            if cYr is None : cYr = eD.year
            if eD.year != cYr :
                if len(blk) > 0 : yield blk
                blk = [(sD,eD)]
                cYr = eD.year
            else : blk.append((sD,eD))
        if len(blk) > 0 : yield blk


class Yly_Iterator(object) :
    "Base unit is year"
    kind = "yly"
    precision = 1
    def __init__(self, iter_start, iter_end, interval=1, duration=1) :
        # round to full year
        if type(iter_start) in (list,tuple) : iter_start = datetime.date(iter_start[0],1,1)
        elif type(iter_start) == int : iter_start = datetime.date(iter_start,1,1)
        if type(iter_end) in (list,tuple) : iter_end = datetime.date(iter_end[0],1,1)
        elif type(iter_end) == int : iter_end = datetime.date(iter_end,1,1)        
        self.iter_start = iter_start = iter_start+relativedelta(day=1,month=1)
        self.iter_end = iter_end = (iter_end+relativedelta(day=1,month=1,years=1))-relativedelta(days=1)
        if type(interval) == int : self._interval = lambda x : relativedelta(years=(interval*x))
        else :
            if interval == 'yly' : self._interval = lambda x : relativedelta(years=x)
            elif interval[0] == 'yly' :
                self._interval = lambda x : relativedelta(years=interval[1]*x)
            else : raise TypeError('invalid interval')
        self.is_scalar = False
        if type(duration) == int :
            self._duration = lambda x : x - relativedelta(years=duration-1)
            self.is_scalar = duration == 1
        else : raise TypeError('invalid duration')
        self.full_iter_start = self._duration(iter_start)
        self.full_iter_end = iter_end

        self._cDT = self.iter_start
        self._index = 0
        self._nextYear = relativedelta(years=1,month=1,day=1)
        self._oneDay = relativedelta(days=1)

    def __iter__(self) :
        return self

    def next(self) :
        self._cDT = self.iter_start + self._interval(self._index)
        if self._cDT <= self.iter_end:
            self._index += 1
            eDT = self._cDT + self._nextYear - self._oneDay
            return self._duration(self._cDT), eDT
        raise StopIteration


    
def DateIterator(iter_start, iter_end, kind='dly', interval=1, duration=1) :
    if kind == 'dly' : return Dly_Iterator(iter_start, iter_end, interval, duration)
    elif kind == 'mly' : return Mly_Iterator(iter_start, iter_end, interval, duration)
    elif kind == 'yly' : return Yly_Iterator(iter_start, iter_end, interval, duration)
    elif kind == 'hrly' : return Hrly_Iterator(iter_start, iter_end, interval, duration)
    else : raise ValueError('unknown date iterator kind')

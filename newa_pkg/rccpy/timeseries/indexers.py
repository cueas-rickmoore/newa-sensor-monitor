""" Time Series indexers """

from datetime import datetime
from dateutil.relativedelta import relativedelta

from rccpy.utils.timeutils import asDatetime

from .iterators import monthsInterval

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

TIME_INDEXERS = { }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TimeIndexer(object):

    def __init__(self, base_time, interval):
        self.base_time = asDatetime(base_time)
        self.interval = interval

    def __call__(self, interval_start, interval_end=None):
        if interval_start is None or interval_start == ':':
            start_index = 0
        else: start_index = self.index(interval_start)

        if interval_end is None or interval_end == interval_start:
            end_index = start_index
        else: end_index = self.index(interval_end)

        return start_index, end_index

    def index(self, date_time):
        raise NotImplementedError

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class HourIndexer(TimeIndexer):

    def index(self, date_time):
        _date_time = asDatetime(date_time)
        if _date_time == self.base_time: return 0
        delta = _date_time - self.base_time
        hours = (delta.days * 24) + (delta.seconds / 3600)
        if (hours % self.interval) == 0: return hours / self.interval 
        else: return (hours + self.interval) / self.interval

    def listDates(self, interval_start, interval_end, interval=None):
        if interval is None: num_hours = relativedelta(hours=self.interval)
        else: num_hours = relativedelta(hours=interval)
        dates = [ ]
        date = asDatetime(interval_start)
        while date <= asDatetime(interval_end):
            dates.append(date)
            date += num_hours
        return tuple(dates)


TIME_INDEXERS['hour'] = HourIndexer

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DayIndexer(TimeIndexer):

    def index(self, date_time):
        _date_time = asDatetime(date_time)
        if _date_time == self.base_time: return 0
        delta = _date_time - self.base_time
        if (delta.days % self.interval) == 0: return delta.days / self.interval
        else: return (delta.days + self.interval) / self.interval

    def listDates(self, interval_start, interval_end, interval=None):
        if interval is None: num_days = relativedelta(days=self.interval)
        else: num_days = relativedelta(days=interval)
        dates = [ ]
        date = asDatetime(interval_start)
        while date <= asDatetime(interval_end):
            dates.append(date)
            date += num_days
        return tuple(dates)

TIME_INDEXERS['day'] = DayIndexer

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class MonthIndexer(TimeIndexer):

    early_errmsg = "Date is earlier than dataset's base date"

    def index(self, date_time):
        _date_time = asDatetime(date_time)
        _base_time = self.base_time
        if _date_time.year == _base_time.year\
        and _date_time.month == _base_time.month: return 0

        _interval = self.interval
        # index may be negative if date_time is earlier than base_time
        years = _date_time.year - _base_time.year
        if years == 0: # both in same year
            months = _date_time.month - _base_time.month
        else: # different years
            months = (years * 12) + (_date_time.month - _base_time.month)
        if (months % _interval) == 0: return months / _interval
        else: return (months + _interval) / _interval

    def listDates(self, interval_start, interval_end, interval=None):
        if interval is None: _interval = self.interval
        else: _interval = interval
        dates = [ ]
        date = asDatetime(interval_start)
        while date <= asDatetime(interval_end):
            dates.append(date)
            date = monthsInterval(date, _interval)
        return tuple(dates)

TIME_INDEXERS['month'] = MonthIndexer

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def timeIndexer(frequency, base_time, interval):
    IndexerClass = TIME_INDEXERS.get(frequency, None)
    if IndexerClass is None:
        raise ValueError, 'No indexer for %s frequency' % frequency
    return IndexerClass(base_time, interval)


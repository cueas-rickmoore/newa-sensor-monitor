""" Time Series datasets """

import datetime
from dateutil.relativedelta import relativedelta

import numpy as N

from rccpy.utils.exceptutils import ShapeMismatchException
from rccpy.utils.timeutils import asDatetime

from .generators import dateArrayGenerator
from .indexers import timeIndexer
from .iterators import timeIterator

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def pythonDataType(data_type):
    if isinstance(data_type, N.dtype):
        if data_type.kind == 'f': return float
        elif data_type.kind == 'i': return int
        elif data_type.kind == 'S': return basestring
        else:
            errmsg = 'Cannot convert %s to python data type.' % str(data_type)
            raise ValueError, errmsg
    return data_type

def defaultMissingValue(dtype):
    if dtype.kind == 'f': return N.inf
    elif dtype.kind == 'i': return -32768
    elif dtype.kind == 'S': return ''
    else: return None

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TimeSeries(object):

    def __init__(self, name, base_time, data_array, **kwargs):
        """
        Single dataset time series

        Arguments :
            name =  name for data in time series
            base_time = datetime object : Date/time corresponding to the
                        first item in `data_array`.
            data_array = Numpy array of values. If multidemensional, the
                         first dimension must be time.

            kwargs can be used to voverride the default value for the follwing :
              value_type = The type of data values in the time series data set.
                             'linear' indicates linear data (i.e. data linearly
                             increases or decrease from one value to another
                             to the decimal precision of the software).
                             'discrete' is similar to 'linear' except thot
                             values may only be whole numbers.
                             'direction' indicates data consisting spherical
                             compass directions (i.e. values from 0 to 360
                             are valid). The defualt is 'linear'
                             If a tuple/list is passed, the first item must
                             be the type, followed by the lower value limit,
                             then the upper value limit)
              frequency = Frequency of (time units between) items in 
                          `data_array`. Valid values are "hour", "day",
                          "month", "year". Default is 'hour'.
              interval = Number of time units per array node. Default is 1
                         (e.g. increment=2 and frequency='hour' means there
                         are 2 hours between each array index)
              missing_value = Value used for missing items in `data_array`.
                              Defualt is -32768 for integer arrays and
                              N.nan for float arrays.
        """
        #TODO : handle 2D arrays

        self.base_time = asDatetime(base_time)
        self.data_name = name
        self.data = data_array
        self.data_interval = interval = int(kwargs.get('interval', 1))
        self.data_type = pythonDataType(data_array.dtype)
        self.description = kwargs.get('description', '?')
        self.frequency = str(kwargs.get('frequency', 'hour'))
        self.units = kwargs.get('units', 'unknown')

        value_type = kwargs.get('value_type', None)
        if value_type is not None:
            self.value_type = value_type[0]
            self.lower_limit = float(value_type[1])
            self.upper_limit = float(value_type[2])
        else:
            self.value_type = 'linear'
            self.lower_limit = N.NINF
            self.upper_limit = N.inf

        self.missing_value = kwargs.get('missing_value', kwargs.get('missing',
                                        defaultMissingValue(data_array.dtype)))
        if self.missing_value is None:
            errmsg = 'No default missing value for dtype :'
            return ValueError, errmsg % dtype.__class__.__name__

        if self.frequency == 'hour':
            def _asDatetime(_time):
                if isinstance(_time, datetime): return _time
                elif isinstance(_time, (tuple,list)): return datetime(*_time)
                else: return datetime( _time/1000000, (_time/10000) % 100,
                                       (_time/100) % 100, _time % 100 )
            def _indexForTime(_time):
                delta = asDatetime(_time) - self.base_time
                hours = (delta.days * 24) + (delta.seconds / 3600)
                indx = hours / interval
                over = hours % interval
                if over > 0: return indx + 1
                else: return indx
            def _relativeDelta(hours): return relativedelta(hours=hours)
            def _timeAsString(_time): return _time.strftime('%Y-%m-%d:%H')
            def _timeAtIndex(indx):
                return self.base_time + relativedelta(hours=indx*interval)

        elif self.frequency == 'day':
            def _asDatetime(_time):
                if isinstance(_time, datetime): return _time
                if isinstance(_time, (tuple,list)): return datetime(*_time)
                else: return datetime( _time/10000, (_time/100) % 100,
                                       _time % 100 )
            def _indexForTime(_time):
                indx = (asDatetime(_time) - self.base_time).days / interval
                over = (asDatetime(_time) - self.base_time).days % interval
                if over > 0: return indx + 1
                else: return indx
            def _relativeDelta(days): return relativedelta(days=days)
            def _timeAsString(_time): return _time.strftime('%Y-%m-%d')
            def _timeAtIndex(indx):
                return self.base_time + relativedelta(days=indx*interval)

        elif self.frequency == 'month':
            def _asDatetime(_time):
                if isinstance(_time, datetime): return _time
                if isinstance(_time, (tuple,list)): return datetime(*_time)
                else: return datetime( _time/100, _time % 100, 1 )
            def _indexForTime(_time):
                date_time = asDatetime(_time)
                years = date_time.year - self.base_time.year
                months = years * 12
                if date_time.month != 12: months -= (12 - date_time.month)
                if self.base_time.month != 1: months -= self.base_time.month - 1
                return months
            def _relativeDelta(months): return relativedelta(months=months)
            def _timeAsString(_time): return _time.strftime('%Y-%m')
            def _timeAtIndex(indx):
                return self.base_time + relativedelta(months=indx*interval)

        elif self.frequency == 'year':
            def _asDatetime(_time):
                if isinstance(_time, datetime): return _time
                if isinstance(_time, (tuple,list)): return datetime(*_time)
                else: return datetime( _time/100, _time % 100, 1 )
            def _indexForTime(_time):
                return asDatetime(_time).year - self.base_time.year
            def _relativeDelta(years): return relativedelta(years=years)
            def _timeAsString(_time): return _time.strftime('%Y')
            def _timeAtIndex(indx):
                return self.base_time + relativedelta(years=indx*interval)

        else:
            raise KeyError, 'Unsupported data frequency : %s' % self.frequency

        self.asDatetime = _asDatetime
        self.indexForTime = _indexForTime
        self.relativeDelta = _relativeDelta
        self.timeAsString = _timeAsString
        self.timeAtIndex = _timeAtIndex

        elapsed_time = (len(data_array) - 1) * self.data_interval
        self.last_time = self.base_time + self.relativeDelta(elapsed_time)

        self.indexer = timeIndexer(self.frequency, self.base_time,
                                   self.data_interval)
        self.generator = dateArrayGenerator(self.frequency)

    # - - - - - - - - - - - - - - - - - -  - - - - - - - - - - - - - - - - - -

    def getDates(self, start_time=None, end_time=None, interval=None,
                       date_format=None):
        if start_time is None or start_time == ':': start_time = self.base_time
        if end_time is None or end_time == ':': end_time = self.last_time
        if interval is None: interval = self.data_interval
        return self.generator(start_time, end_time, interval=interval,
                              as_numpy=True, date_format=date_format)

    def getIndexes(self, start_time, end_time):
        """ returns tuple containing index of start_time and index of end_time
        """
        _start_time, _end_time = self._validTimes(start_time, end_time)
        return self.indexer(_start_time, _end_time)

    # - - - - - - - - - - - - - - - - - -  - - - - - - - - - - - - - - - - - -

    def getData(self, start_time=None, end_time=None):
        start_index, end_index = self.getIndexes(start_time, end_time)
        return self._getData(self.data, self.missing_value, start_index,
                             end_index)

    def calcDataStatistics(self, start_time=None, end_time=None):
        if start_time is None or start_time == ':'\
        and end_time is None or end_time == ':':
            # calculate stats for entire dataset
            return self._calcArrayStatistics(self.data, self.missing_value)
        # calculate stats for some subset of data
        start, end = self.getIndexes(start_time, end_time)
        return self._calcArrayStatistics( self._getData(self.data,
                                          self.missing_value, start, end),
                                          self.missing_value)

    # - - - - - - - - - - - - - - - - - -  - - - - - - - - - - - - - - - - - -

    def getIndexer(self, start_time=None, end_time=None, interval=None,
                         duration=None):
        _start_time, _end_time = self._validTimes(start_time, end_time)
        return TimeSeriesIndexIterator(self, _start_time, _end_time, interval,
                                             duration)

    def getIterator(self, start_time=None, end_time=None, interval=None,
                          duration=None):
        _start_time, _end_time = self._validTimes(start_time, end_time)
        return TimeSeriesDataIterator(self, _start_time, _end_time, interval,
                                            duration)

    # - - - - - - - - - - - - - - - - - -  - - - - - - - - - - - - - - - - - -

    def getSequenceDetector(self):
        from rccpy.timeseries.detectors import TimeSeriesSequenceDetector
        return TimeSeriesSequenceDetector(self)

    def getSpikeDetector(self):
        from rccpy.timeseries.detectors import timeSeriesSpikeDetector
        return timeSeriesSpikeDetector(self)

    # - - - - - - - - - - - - - - - - - -  - - - - - - - - - - - - - - - - - -

    def getRelativeIncrement(self, increment):
        if self.frequency == 'hour': return relativedelta(hours=increment)
        elif self.frequency == 'day': return relativedelta(days=increment)
        elif self.frequency == 'month': return relativedelta(months=increment)
        elif self.frequency == 'year': return relativedelta(years=increment)
        errmsg = "Unable to create relativedleta for '%s' data frequency"
        raise RuntimeError, error % self.frequency 

    # - - - - - - - - - - - - - - - - - -  - - - - - - - - - - - - - - - - - -

    def _calcArrayStatistics(self, numpy_array, missing_value=None):
        if missing_value is None: missing = self.missing_value
        else: missing = missing_value

        if N.isfinite(missing):
            valid_values = numpy_array[N.where(numpy_array!=missing)]
            if numpy_array.dtype.kind == 'f':
                valid_values = valid_values[N.where(N.isfinite(valid_values))]
        else:
            valid_values = numpy_array[N.where(N.isfinite(numpy_array))]

        if len(valid_values) > 0:
            statistics =  { 'min' : N.min(valid_values),
                            'max' : N.max(valid_values),
                            'mean' : N.mean(valid_values),
                            'stddev' : N.std(valid_values),
                            'median' : N.median(valid_values),
                            'missing' : len(numpy_array) - len(valid_values),
                            'coverage' : len(valid_values),
                          }
        else:
            statistics =  { 'min' : missing, 'max' : missing,
                            'mean' : missing, 'stddev' : 0.0,
                            'median' : missing,
                            'missing' : len(numpy_array),
                            'coverage' : len(numpy_array),
                          }
        return statistics

    def _getData(self, _array, missing, start_index, last_index):
        array_size = _array.size
        dtype = _array.dtype

        if start_index < 0:
            if last_index == start_index:
                return N.array([missing,])
            elif last_index < 0:
                too_early = (last_index - 1) - start_index
                return N.array([missing for m in range(too_early)],
                                dtype=dtype)
            else:
                end_index = last_index+1
                data = [missing for m in range(abs(start_index))]
                if end_index < array_size:
                    data.extend(list(_array[0:end_index]))
                else:
                    data.extend(list(_array[:]))
                    if end_index > array_size:
                        overflow = end_index - array_size 
                        data.extend([missing for m in range(overflow)])
                return N.array(data, dtype=dtype)

        elif start_index < array_size:
            if last_index == start_index:
                return _array[start_index]
            else:
                end_index = last_index+1
                if end_index < array_size:
                    return _array[start_index:end_index]
                elif end_index == array_size:
                    return _array[start_index:]
                else: # end_index > array_size
                    print 'end_index > array_size', end_index, array_size
                    data = list(_array[start_index:])
                    overflow = end_index - array_size
                    data.extend([missing for m in range(overflow)])
                    return N.array(data, dtype=dtype)

        else: # start_index is beyond end of available data
            end_index = last_index+1
            msg = 'start_index is beyond end of available data'
            print msg, start_index, array_size
            over_the_top = end_index - start_index
            return N.array([missing for m in range(over_the_top)],
                            dtype=dtype)

    def _validTimes(self, start_time, end_time):
        """ returns tuple containing index of start_time and index of end_time
        """
        if start_time is None or start_time == ':':
            if end_time is None: return self.base_time, self.base_time
            elif end_time == ':': return self.base_time, self.last_time
            return self.base_time, asDatetime(end_time)
        else:
            _start_time = asDatetime(start_time)
            if end_time is None: return _start_time, _start_time 
            elif end_time == ':': return _start_time, self.last_time
            return _start_time, asDatetime(end_time)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TimeSeriesIndexIterator(object):

    def __init__(self, time_series, start_time=None, end_time=None,
                       interval=None, duration=None):
        """ handles instances of the TimeSeriesData class or it's
            subclassses
        """
        #TODO : handle 2D arrays
        iter_start, iter_end = time_series._validTimes(start_time, end_time)
        if interval is None: interval = time_series.data_interval
        if duration is None: duration = time_series.data_interval

        self.time_series = time_series
        self.indexer = time_series.indexer
        self.iterator = timeIterator(time_series.frequency, iter_start,
                                     iter_end, interval, duration)

    # - - - - - - - - - - - - - - - - - -  - - - - - - - - - - - - - - - - - -

    def __iter__(self):
        return self

    def next(self):
        self.latest_interval = self.iterator.next()
        self.latest_indexes = self.indexer(*self.latest_interval)
        return self.latest_indexes

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TimeSeriesDataIterator(object):

    def __init__(self, time_series, start_time=None, end_time=None,
                       interval=None, duration=None):
        """ handles instances of the TimeSeriesData class or it's
            subclassses
        """
        #TODO : handle 2D arrays
        iter_start, iter_end = time_series._validTimes(start_time, end_time)
        if interval is None: interval = time_series.interval
        if duration is None: duration = time_series.interval

        self.time_series = time_series
        self.iterator = timeIterator(time_series.frequency, iter_start,
                                     iter_end, interval, duration)

    def __iter__(self):
        return self

    def next(self):
        self.latest_interval = self.iterator.next()
        return self.time_series.getData(*self.latest_interval)


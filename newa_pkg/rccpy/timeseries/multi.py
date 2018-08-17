""" Time Series datasets """

from datetime import datetime
from dateutil.relativedelta import relativedelta

import numpy as N

from rccpy.utils.timeutils import asDatetime

from rccpy.timeseries.generators import dateArrayGenerator
from rccpy.timeseries.indexers import timeIndexer
from rccpy.timeseries.iterators import timeIterator

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def defaultMissingValue(dtype):
    if dtype.kind == 'f': return N.inf
    elif dtype.kind == 'i': return -32768
    elif dtype.kind == 'S': return ''
    else:
        errmsg = 'No default missing value for dtype :'
        return ValueError, errmsg % dtype.__class__.__name__

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class MultipleTimeSeries(object):

    def __init__(self, *data_info):
        """
        Multiple dataset time series.
        
        All datasets must be the same frequency and interval.

        Arguments
        ---------
            data_info : information tuples, one for each dataset
                        (name, data, base_time, data_attrs)
                name : name of dataset
                data : numpy array containing data
                base_time : date of first item in array
                data_attrs : data attributes dictionary
                    as a minimum it should have the following:
                    value_type : The type of data in the time series data set.
                         'linear' indicates linear data (i.e. data linearly
                                  increases or decrease from one value to
                                  another to the decimal precision of the 
                                  software).
                         'discrete' is similar to 'linear' except thot
                                    values may only be whole numbers.
                         'direction' indicates data consisting spherical
                                     compass directions (i.e. values from 0 to
                                     360 valid).
                          The defualt is 'linear'.
                          If a tuple/list is passed, the first item must
                          be the type, followed by the lower value limit,
                          then the upper value limit)
                    missing : value that indicates missing data
                    frequency : frequency of the data (i.e. 'hour','day',etc.)
                                Default is 'hour'.
                    interval : number of time units between entries in the
                               data array. Default is 1.
        """
        #TODO : handle 2D arrays

        frequency = str(data_info[0][-1].get('frequency','hour'))
        self.frequency = frequency
        interval = int(data_info[0][-1].get('interval',1))
        self.interval = interval

        if frequency == 'hour':
            def _relativeDelta(interval): return relativedelta(hours=interval)
        elif frequency == 'day':
            def _relativeDelta(interval): return relativedelta(days=interval)
        elif frequency == 'month':
            def _relativeDelta(interval): return relativedelta(months=interval)
        elif frequency == 'year':
            def _relativeDelta(interval): return relativedelta(years=interval)
        else:
            raise KeyError, 'Unsupported data frequency : %s' % frequency
        self.relativeDelta = _relativeDelta
        
        self.base_times = { }
        self.value_types = { }
        self.datasets = { }
        self.dataset_names = [ ]
        self.indexers = { }
        self.lower_limits = { }
        self.upper_limits = { }
        self.missing_values = { }

        common_start_time = datetime.now()
        common_end_time = datetime(1000,1,1)

        for name, data, base_time, data_attrs in data_info:
            self.dataset_names.append(name)
            self.datasets[name] = data
            self.base_times[name] = _base_time = asDatetime(base_time)
            common_start_time = max(common_start_time, _base_time)

            elapsed_time = (len(data)-1) * self.interval
            last_time = _base_time + self.relativeDelta(elapsed_time)
            common_end_time = min(common_end_time, last_time)

            value_type = data_attrs.get('value_type', None)
            if isinstance(value_type, (tuple,list)):
                self.value_types[name] = value_type[0]
                self.lower_limits[name] = value_type[1]
                self.upper_limits[name] = value_type[2]
            else:
                self.value_types[name] = value_type
                self.lower_limits[name] = N.NINF
                self.upper_limits[name] = N.inf

            missing = data_attrs.get('missing', None)
            if missing is None:
                if data.dtype.kind == 'i': missing = -32768
                elif data.dtype.kind == 'f':
                    if len(N.where(N.isinf(data))) > 0: missing = N.inf
                    else: missing = N.nan
            self.missing_values[name] = missing

            self.indexers[name] = timeIndexer(frequency, _base_time, interval)

        self.common_start_time = common_start_time
        self.common_end_time = common_end_time

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

        self.generator = dateArrayGenerator(self.frequency)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDates(self, start_time=None, end_time=None, interval=None,
                       date_format=None):
        if start_time is None: start_time = self.common_start_time
        if end_time is None: end_time = self.common_end_time
        if interval is None: interval = self.interval
        return self.generator(start_time, end_time, interval=interval,
                              as_numpy=True, date_format=date_format)

    def getIndexes(self, start_time, end_time):
        if start_time is None: start_time = self.common_start_time
        if end_time is None: end_time = self.common_end_time
        indexes = { }
        for name in self.dataset_names:
            indexes[name] = self.indexers[name](start_time, end_time)
        return indexes

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getData(self, start_time, end_time):
        if start_time is None: start_time = self.common_start_time
        if end_time is None: end_time = self.common_end_time
        data = { }
        for name in self.dataset_names:
            start_index, end_index = self.indexers[name](start_time, end_time)
            data[name] = self._getData(self.datasets[name],
                                       self.missing_values[name],
                                       start_index, end_index)
        return data

    def getDataByName(self, dataset_name, start_time=None, end_time=None):
        if start_time is None: start_time = self.common_start_time
        if end_time is None: end_time = self.common_end_time

        start_index,end_index = self.indexers[dataset_name](start_time,end_time)
        return self._getData(self.datasets[dataset_name],
                             self.missing_values[dataset_name],
                             start_index, end_index)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getIndexer(self, start_time=None, end_time=None,
                         interval=None, duration=None):
        return MultiTimeSeriesIndexIterator(self, start_time, end_time,
                                                  interval, duration)

    def getIterator(self, start_time=None, end_time=None, interval=None,
                          duration=None):
        return MultiTimeSeriesDataIterator(self, start_time, end_time,
                                                 interval, duration)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getRelativeIncrement(self, increment):
        if self.frequency == 'hour': return relativedelta(hours=increment)
        elif self.frequency == 'day': return relativedelta(days=increment)
        elif self.frequency == 'month': return relativedelta(months=increment)
        elif self.frequency == 'year': return relativedelta(years=increment)
        errmsg = "Unable to create relativedleta for '%s' data frequency"
        raise RuntimeError, error % self.frequency

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def add(self, dataset_name_1, dataset_name_2, start_time=None,
                  end_time=None):
        data_1 = self.getDataByName(dataset_name_1, start_index, end_index)
        data_2 = self.getDataByName(dataset_name_2, start_index, end_index)
        return data_1 + data_2

    def difference(self, dataset_name_1, dataset_name_2, start_time=None,
                         end_time=None):
        data_1 = self.getDataByName(dataset_name_1, start_index, end_index)
        data_2 = self.getDataByName(dataset_name_2, start_index, end_index)
        return data_1 - data_2

    def divide(self, dataset_name_1, dataset_name_2, start_time=None,
                     end_time=None):
        data_1 = self.getDataByName(dataset_name_1, start_index, end_index)
        data_2 = self.getDataByName(dataset_name_2, start_index, end_index)
        return data_1 / data_2

    def multiply(self, dataset_name_1, dataset_name_2, start_time=None,
                       end_time=None):
        data_1 = self.getDataByName(dataset_name_1, start_index, end_index)
        data_2 = self.getDataByName(dataset_name_2, start_index, end_index)
        return data_1 * data_2

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _getData(self, dataset, missing, start_index, end_index):
        array_size = len(dataset)
        dtype = dataset.dtype

        if start_index < 0:
            if end_index < 0:
                too_early = end_index - start_index
                return N.array([missing for m in range(too_early)],
                                dtype=dtype)
            else:
                data = [missing for m in range(abs(start_index))]
                if end_index < array_size:
                    data.extend(list(dataset[0:end_index]))
                else:
                    data.extend(list(dataset[:]))
                    if end_index > array_size:
                        overflow = end_index - array_size 
                        data.extend([missing for m in range(overflow)])
                return N.array(data, dtype=dtype)

        elif start_index < array_size:
            if end_index < array_size:
                return dataset[start_index:end_index]
            elif end_index == array_size:
                return dataset[start_index:]
            else: # end_index > array_size
                print 'end_index > array_size', end_index, array_size
                data = list(dataset[start_index:])
                overflow = end_index - array_size
                data.extend([missing for m in range(overflow)])
                return N.array(data, dtype=dtype)

        else: # start_index is beyond end of available data
            msg = 'start_index is beyond end of available data'
            print msg, start_index, array_size
            over_the_top = end_index - start_index
            return N.array([missing for m in range(over_the_top)],
                            dtype=dtype)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class MultiTimeSeriesIndexIterator(object):

    def __init__(self, time_series, start_time=None, end_time=None,
                       interval=None, duration=None):
        """ handles instances of the MultiTimeSeries class or it's
            subclassses
        """
        #TODO : handle 2D arrays
        if start_time is None: iter_start = time_series.common_start_time
        else: iter_start = asDatetime(start_time)
        if end_time is None: iter_end = time_series.common_end_time
        else: iter_end = asDatetime(end_time)
        if interval is None: interval = time_series.interval
        if duration is None: duration = time_series.interval

        self.dataset_names = time_series.dataset_names
        self.indexers = time_series.indexers
        self.iterator = timeIterator(time_series.frequency, iter_start,
                                     iter_end, interval, duration)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __iter__(self):
        return self

    def next(self):
        indexes = { }
        self.latest_interval = self.iterator.next()
        for name in self.dataset_names:
            indexes[name] = self.indexers[name](*self.latest_interval)
        self.latest_indexes = indexes
        return indexes

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class MultiTimeSeriesDataIterator(object):

    def __init__(self, time_series, start_time=None, end_time=None,
                       interval=None, duration=None):
        """ handles instances of the TimeSeriesData class or it's
            subclassses
        """
        if start_time is None: iter_start = time_series.common_start_time
        else: iter_start = asDatetime(start_time)
        if end_time is None: iter_end = time_series.common_end_time
        else: iter_end = asDatetime(end_time)
        if interval is None: interval = time_series.interval
        if duration is None: duration = time_series.interval

        self.iterator = timeIterator(time_series.frequency, iter_start,
                                     iter_end, interval, duration)

    def __iter__(self):
        return self

    def next(self):
        self.latest_interval = self.iterator.next()
        return self.time_series.getData(*self.latest_interval)


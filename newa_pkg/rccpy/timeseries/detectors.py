
from datetime import datetime
from dateutil.relativedelta import relativedelta

import numpy as N

from rccpy.analysis.base import BaseDetector
from rccpy.analysis.sequence import SequenceDetector
from rccpy.analysis.spike import SpikeDetector, CircularAngleSpikeDetector

from rccpy.utils.timeutils import asDatetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

LAST_DAY_OF_MONTH = (31,28,31,30,31,30,31,31,30,31,30,31)
ONE_MONTH = relativedelta(months=1)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TimeSeriesDetectorMixin:

    def __call__(self, start_time=None, end_time=None, filters=None):
        """ Wrapper for a required sequence of steps
        """
        self.detected = self.detect(start_time, end_time)
        self.filters = filters
        if filters is not None: self.filter_groups = self.applyFilters(filters)
        else: self.filter_groups = None
        return self.detected

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def asDatetime(self, time_):   return self.time_series.asDatetime(time_)
    def indexForTime(self, time_): return self.time_series.indexForTime(time_)
    def relativeDelta(self, delta): return self.time_series.relativeDelta(delta)
    def timeAsString(self, time_): return self.time_series.timeAsString(time_)
    def timeAtIndex(self, indx):   return self.time_series.timeAtIndex(indx)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def detect(self, start_time=None, end_time=None):
        if start_time is None: start_index = 0
        else: start_index = self.indexForTime(self.asDatetime(start_time))

        if end_time is None: end_index = len(self.data)
        else: end_index = self.indexForTime(self.asDatetime(end_time))

        if self.data_type == int:
            data_array = self.data
            data_array[N.where(N.isinf(data_array))] = self.missing_value
            data_array[N.where(N.isnan(data_array))] = self.missing_value
            return self._detect(N.array(data_array, dtype=int), start_index,
                                end_index)
        else:
            return self._detect(self.data, start_index, end_index)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class TimeSeriesSequenceDetector(TimeSeriesDetectorMixin, SequenceDetector):

    REPORT_FORMAT = '%s%%4d %ss (%%s thru %%s) @ %%d = %%s'
    SAVE_FORMAT = '\n%s%%4d %ss (%%s thru %%s) @ %%d = %%s'

    def __init__(self, time_series, tolerance=N.inf):
        SequenceDetector.__init__(self, time_series.data_type, 
                                  time_series.missing_value, tolerance)
        self.base_time = time_series.base_time
        self.data = time_series.data
        self.frequency = time_series.frequency
        self.last_time = time_series.last_time
        self.time_series = time_series

    def _calcStatsByMonth(self, sequences):
        if self.frequency not in ('hour','day'):
            errmsg = '`%s` frequency not supported by _calcStatsByMonth()'
            raise ValueError, errmsg % self.frequency

        sequences_by_month = [ [ ] for month in range(12) ]
        for run in sequences:
            diff_2_1 = self.relativeDelta((run[2]-run[1])+1)
            start_time = self.base_time + diff_2_1
            sequences_by_month[start_time.month-1].append(run)
            
            end_time = self.timeAtIndex(run[2])
            if (end_time.month > start_time.month or
                end_time.year > start_time.year):

                end_date = datetime(end_time.year, end_time.month,
                                    LAST_DAY_OF_MONTH[end_time.month-1],23)
                date = start_time + ONE_MONTH
                while date < end_date:
                    sequences_by_month[date.month-1].append(run)
                    date += ONE_MONTH

        return tuple( [ self._calcStatistics(runs)
                        for runs in sequences_by_month ] )

    def _reportSequences(self, sequences, spacer='    '):
        fmt = self.REPORT_FORMAT % (spacer,self.frequency)
        sequences.sort(key=lambda x:x[2])
        for run in sequences:
            start_time = self.timeAtIndex((run[2]-run[1])+1)
            end_time = self.timeAtIndex(run[2])
            print fmt % (run[1], self.timeAsString(start_time),
                         self.timeAsString(end_time), run[2], run[0])

    def _saveSequences(self, output_file, sequences, spacer='    '):
        fmt = self.SAVE_FORMAT % (spacer, self.frequency)
        for run in sequences:
            start_time = self.timeAtIndex((run[2]-run[1])+1)
            end_time = self.timeAtIndex(run[2])
            line = fmt % (run[1], self.timeAsString(start_time),
                          self.timeAsString(end_time), run[2], run[0])
            output_file.write(line)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SpikeDetectorMixin:

    REPORT_FORMAT = '%s spike @ %%s (%%d) : magnitude (%%d, %%d) : value = %%d'
    SAVE_FORMAT = '\n%s spike @ %%s (%%d) : magnitude (%%d, %%d) : value = %%d'

    def _calcStatsByMonth(self, spikes):
        if self.frequency not in ('hour','day'):
            errmsg = '`%s` frequency not supported by _calcStatsByMonth()'
            raise ValueError, errmsg % self.frequency

        spikes_by_month = [ [ ] for month in range(12) ]
        for spike in spikes:
            spike_time = self.timeAtIndex(spike[1])
            spikes_by_month[spike_time.month-1].append(spike)

        return tuple( [ self._calcStatistics(spikes)
                        for spikes in spikes_by_month ] )

    def _reportSpikes(self, spikes, spacer='    '):
        fmt = self.REPORT_FORMAT % spacer
        if isinstance(spikes, tuple): spikes = list(spikes)
        spikes.sort(key=lambda x:x[1])
        for spike in spikes:
            spike_time = self.base_time + self.relativeDelta(spike[1])
            print fmt % (self.timeAsString(spike_time),spike[1],spike[0][0],
                         spike[0][1],spike[2])

    def _saveSpikes(self, output_file, spikes, spacer='    '):
        fmt = self.SAVE_FORMAT % spacer
        if isinstance(spikes, tuple): spikes = list(spikes)
        spikes.sort(key=lambda x:x[1])
        for spike in spikes:
            spike_time = self.base_time + self.relativeDelta(spike[1])
            line = fmt % (self.timeAsString(spike_time),spike[1],spike[0][0],
                          spike[0][1],spike[2])
            output_file.write(line)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SimpleTimeSeriesSpikeDetector(TimeSeriesDetectorMixin, SpikeDetectorMixin,
                                    SpikeDetector):

    def __init__(self, time_series, tolerance=N.inf):
        SpikeDetector.__init__(self, time_series.data_type, 
                                     time_series.missing_value)
        self.base_time = time_series.base_time
        self.data = time_series.data
        self.frequency = time_series.frequency
        self.last_time = time_series.last_time
        self.time_series = time_series

class CircAngTimeSeriesSpikeDetector(TimeSeriesDetectorMixin,
                                     SpikeDetectorMixin,
                                     CircularAngleSpikeDetector):

    def __init__(self, time_series, tolerance=N.inf):
        SpikeDetector.__init__(self, time_series.data_type, 
                                     time_series.missing_value)
        self.base_time = time_series.base_time
        self.data = time_series.data
        self.frequency = time_series.frequency
        self.last_time = time_series.last_time
        self.time_series = time_series

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def timeSeriesSpikeDetector(time_series):
    if time_series.content_type[0] == 'direction':
        return CircAngTimeSeriesSpikeDetector(time_series)
    else:
        return SimpleTimeSeriesSpikeDetector(time_series)


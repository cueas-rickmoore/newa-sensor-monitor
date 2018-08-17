

import numpy as N

from rccpy.analysis.sequence import SequenceDetector
from rccpy.analysis.spike import SpikeDetector, CircularAngleSpikeDetector

from rccpy.utils.timeutils import asDatetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class BaseValidator(object):

    def __init__(self, dataset_name, missing, units, cushions=(0,0),
                       first_hour_in_day=0, **kwargs):
        self._pre_init_hook(**kwargs)

        self.dataset_name = dataset_name
        self.missing = missing
        self.units = units
        self.cushions = cushions
        self.first_hour_in_day = first_hour_in_day

        if N.isfinite(self.missing):
            def _isMissing(value): return value == self.missing
        else:
            def _isMissing(value): return not N.isfinite(value)
        self.isMissing = _isMissing

        self.detected = [ ]
        self.isvalid = None

        self._post_init_hook(**kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def hasValidData(self):
        first_index_in_day = self.cushions[0]
        last_index_in_day = len(self.isvalid) - self.cushions[1]
        return True in self.isvalid[first_index_in_day:last_index_in_day]

    def hourFromIndex(self, indx):
        return (indx - self.cushions[0]) + self.first_hour_in_day

    def updateTrackers(self, isvalid):
        if isvalid is not None and False in isvalid:
            if self.isvalid is None: self.isvalid = isvalid
            else:
                for indx in range(len(isvalid)):
                    if isvalid[indx] == False: self.isvalid[indx] = False

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _capture(self, indx, reason):
        self.detected.append(reason)
        self.isvalid[indx] = False

    def _postInitHook(self, **kwargs):
        pass

    def _preInitHook(self, **kwargs):
        pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

ALL_MISSING = 'Data missing for %s at all hours'
MISSING_VALUES_AT = 'Missing data for %s at the following hours : %s'

class PhysicalLimitsValidator(BaseValidator):

    def _postInitHook(self, **kwargs):
        self.value_type = kwargs['value_type']

        lower_limit = kwargs['lower_limit']
        if N.isneginf(lower_limit):
            def _valueIsTooLow(value): return False
        else:
            def _valueIsTooLow(value): return value < float(lower_limit)
        self._valueIsTooLow = _valueIsTooLow
        self.lower_limit = lower_limit

        upper_limit = kwargs['upper_limit']
        if N.isposinf(upper_limit):
            def _valueIsTooHigh(value): return False
        else:
            def _valueIsTooHigh(value): return value > float(upper_limit)
        self._valueIsTooHigh = _valueIsTooHigh
        self.upper_limit = upper_limit

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, date, data):
        num_hours = len(data)
        start_index = self.cushions[0]
        end_index = num_hours - self.cushions[1]
        self.detected = [ ]
        if self.isvalid is None:
            self.isvalid = [True for item in data]

        return self._validate_(date, data,  start_index, end_index)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _validate_(self, date, data, start_index, end_index):
        indx = start_index
        missing = [ ]
        low_indexes_ = [ ]
        high_indexes_ = [ ]
        while indx < end_index:
            value = data[indx]
            hour = self.hourFromIndex(indx)
            # missing, nothing else matters
            if self.isMissing(value):
                missing.append(hour)
                self.isvalid[indx] = False
            # test against observed/theoretical physical limits
            elif self._valueIsTooLow(value):
                low_indexes_.append(indx)
                self._capture(indx,
                             ('invalid','extp',hour,value,self.lower_limit,-1))
            elif self._valueIsTooHigh(value):
                high_indexes_.append(indx)
                self._capture(indx,
                             ('invalid','extp',hour,value,self.upper_limit,+1))
            indx += 1

        #num_missing = len(missing)
        #if num_missing == end_index - start_index:
        #    self.detected = [('missing', ALL_MISSING % self.dataset_name),]
        #elif num_missing > 0:
        #    missing_hours = ', '.join(['%02d' % hour for hour in missing])
        #    msg = MISSING_VALUES_AT % (self.dataset_name, missing_hours)
        #    self.detected.append(('missing', msg))
        return missing

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ExtremesValidator(PhysicalLimitsValidator):

    def _postInitHook(self, **kwargs):
        self.value_type = kwargs['value_type']

        self.severities = kwargs.get('severity', ('invalid', 'suspect',))
        self.stddevs = { }
        for severity in self.severities:
            self.stddevs[severity] = kwargs[severity]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, date, stats_matrix, data):
        start_index = self.cushions[0]
        num_hours = len(data)
        end_index = num_hours - self.cushions[1]
        self.detected = [ ]
        if self.isvalid is None:
            self.isvalid = [True for item in data]

        # validate against physical extremes
        missing_ = self._validate_(date, data, start_index, end_index)
        if not self.hasValidData(): return missing_

        # needed for validatation against Period of Record for the month
        stats = stats_matrix[asDatetime(date).month]
        mean = stats[3]
        stddev = stats[5]

        for severity in self.severities:
            num_stddevs = self.stddevs[severity]
            upper_limit = mean + (num_stddevs * stddev)
            lower_limit = mean - (num_stddevs * stddev)

            indx = start_index
            while indx < end_index:
                if self.isvalid[indx]:
                    value = data[indx]
                    if value > upper_limit:
                        hour = self.hourFromIndex(indx)
                        detail = (severity, 'exts', hour, value, upper_limit,
                                  num_stddevs)
                        self._capture(indx, detail)
                    elif value < lower_limit:
                        detail = (severity, 'exts', hour, value, lower_limit,
                                  -num_stddevs)
                        self._capture(indx, detail)
                indx+=1

        return missing_

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

class SequenceValidator(BaseValidator):

    def _postInitHook(self, **kwargs):
        self.value_type = kwargs['value_type']

        self.severities = kwargs.get('severity', ('invalid', 'suspect',))
        self.stddevs = { }
        for severity in self.severities:
            self.stddevs[severity] = kwargs[severity]

        self.severities = ('invalid', 'suspect',)
        self.filters = kwargs['filters']
        self.tolerance = kwargs['tolerance']

        self.detector = SequenceDetector(self.value_type, self.missing,
                                         self.tolerance)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, date, stats_matrix, data):
        num_hours = len(data)
        front_cushion = self.cushions[0]
        end_index = num_hours - self.cushions[1]
        self.detected = [ ]
        if self.isvalid is None:
            self.isvalid = [True for item in data]
            has_valid_data = True
        else: has_valid_data =  self.hasValidData()

        if not has_valid_data: return
        # detect all sequences ... don't use filters for now
        detected = self.detector(data, 0, end_index)
        if len(detected) == 0: return

        # validate against Period of Record 
        stats = stats_matrix[asDatetime(date).month]
        mean = stats[3]
        stddev = stats[5]

        for severity in self.severities:
            num_stddevs = self.stddevs[severity]
            limit = mean + (num_stddevs * stddev)

            for value, length, end_index in detected:
                if end_index < front_cushion: continue
                if length > limit and self.isvalid[end_index]:
                    end_hour = self.hourFromIndex(end_index)
                    detail = (severity, 'seq', end_hour, value, length, limit,
                              num_stddevs)
                    self._capture(end_index, detail)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _capture(self, end_index, reason):
        length = reason[4]
        for indx in range(end_index-length, end_index):
            self.isvalid[indx] = False

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SpikeValidator(BaseValidator):

    def _postInitHook(self, **kwargs):
        self.value_type = kwargs['value_type']

        self.severities = kwargs.get('severity', ('invalid', 'suspect',))
        self.stddevs = { }
        for severity in self.severities:
            self.stddevs[severity] = kwargs[severity]

        self.severities = ('invalid', 'suspect',)
        self.filters = kwargs['filters']

        if dataset_name == 'wdir':
            self.detector = CircularAngleSpikeDetector(self.value_type,
                                                       self.missing)
        else: self.detector = SpikeDetector(self.value_type, self.missing)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, date, stats_matrix, data, isvalid=None):
        num_hours = len(data)
        start_index = self.cushions[0] - 1
        end_index = (num_hours - self.cushions[1]) + 1
        self.detected = [ ]
        if self.isvalid is None:
            self.isvalid = [True for item in data]
            has_valid_data = True
        else: has_valid_data =  self.hasValidData()

        if not has_valid_data: return
        # detect any spikes ... don't use filters for now
        detected = self.detector(data, start_index, end_index)
        if len(detected) == 0: return

        # validate against Period of Record for the month
        stats = stats_matrix[asDatetime(date).month]
        mean = stats[3]
        stddev = stats[5]

        for severity in self.severities:
            num_stddevs = self.stddevs[severity]
            limit = mean + (num_stddevs * stddev)

            for spike, indx, value in detected:
                magnitude = min(abs(spike[0]),abs(spike[1]))
                if magnitude > limit  and self.isvalid[indx]:
                    hour = self.hourFromIndex(indx)
                    detail = (severity, 'spk', hour, value, spike, limit,
                              num_stddevs)
                    self._capture(indx, detail)


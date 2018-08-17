
from datetime import datetime
from dateutil.relativedelta import relativedelta
from copy import copy

import Data, Meta
UnknownUcanId = Meta.MetaQuery.UnknownUcanId
import ucanCallMethods

import numpy as N

from rccpy.stations.vardefs import getTsVarCodeset
from rccpy.utils.data import safedict, AsciiSafeDict

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

ONE_HOUR = relativedelta(hours=1)
STATION_INFO = 'Network %(network)s : Station %(sid)s : %(name)s : %(ucanid)d'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from rccpy.stations.vardefs import UcanUndefinedElementError

class UcanDataError(Exception): pass
class UcanDateMismatchError(Exception): pass
class UcanInvalidElementError(Exception): pass
class UcanInvalidTsvarError(Exception): pass
class UcanStationIDError(Exception): pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class UcanErrorExplanation(Exception): pass

def explainException(e, station_dict, detail=None):
    exception_type = e.__class__.__name__
    args = list(e.args)
    args.insert(0, STATION_INFO % station_dict)
    args.insert(0, 'UCAN Exception : %s' % exception_type)
    if detail is not None: args.append(detail)
    return '\n'.join(args)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class UcanConnection(object):

    def __init__(self, base_date=None, max_days_per_request=30):
        if base_date is None:
            base_date = (1900,1,1,0)
        elif isinstance(base_date, list):
            base_date = tuple(base_date)

        if isinstance(base_date, tuple):
            if len(base_date) == 3:
                self.base_date = base_date + (0,)
            elif len(base_date) == 4:
                self.base_date = base_date
            else:
                errmsg = "Invalid value for `base_date` : %s"
                raise ValueError, errmsg % str(base_date)
        else:
            errmsg = "Invalid type for `base_date` : %s"
            raise ValueError, errmsg % str(type(base_date))

        self.hours_per_request = max_days_per_request*24
        self.request_delta = relativedelta(hours=self.hours_per_request)

        self.ucan = ucanCallMethods.general_ucan()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def elapsedHours(self, start_time, end_time):
        if isinstance(start_time, (tuple,list)):
            start_time = datetime(*start_time)
        if isinstance(end_time, (tuple,list)):
            end_time = datetime(*end_time)
        
        delta = end_time - start_time
        return (delta.days * 24) + (delta.seconds / 3600)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getHourlyData(self, station_dict, elem, dtype, units, missing,
                            start_date=None, end_date=None, debug=False):
        if debug: print 'UcanConnection.getHourlyData'

        _station_dict = AsciiSafeDict.makeSafe(station_dict, True)
        sid = self._getStationId(_station_dict, False)
        ucanid = station_dict['ucanid']

        if isinstance(elem,(tuple,list)):
            ts_var = self._getTsVar(_station_dict, elem)
        else:
            ts_var = self.getTsVar(_station_dict, elem)

        try:
            ts_var.setUnits(units)
        except Exception as e:
            detail = "failed call to ts_var.setUnits('%s') for '%s'" % (units,elem)
            raise UcanDataError, explainException(e, station_dict, detail)

        ts_var.setMissingDataAsFloat(-32768.)

        start_range, end_range = ts_var.getValidDateRange()
        if debug:
            print 'as input'
            print sid, ucanid, elem, 'requested', start_date, end_date
            print sid, ucanid, elem, 'available', start_range, end_range

        if start_date is None:
            start_date_ = max(self.base_date, tuple(start_range))
        else:
            start_date_ = max(copy(start_date), tuple(start_range))
            if len(start_date_) == 3: start_date_ += (0,)
        start_date_ = datetime(*start_date_)
        start_range = datetime(*start_range)

        if end_date is None: end_date_ = tuple(end_range)
        else:
            end_date_ = min(copy(end_date), tuple(end_range))
            if len(end_date_) == 3: end_date_ += (23,)
        end_date_ = datetime(*end_date_)
        end_range = datetime(*end_range)

        if debug:
            print 'as datetime'
            print sid, ucanid, elem, 'requested', start_date_, end_date_
            print sid, ucanid, elem, 'available', start_range, end_range

        # add ONE_HOUR to end_date_ because ts_var always returns one hour
        # less than requested
        end_time = end_date_ + ONE_HOUR

        # break up time span into self.hours_per_request increments due to
        # tsvar/ucan server limitations
        start_span = copy(start_date_)
        spans = [ ]
        while start_span < end_time:
            elapsed = self.elapsedHours(start_span, end_time)
            if elapsed > self.hours_per_request:
                end_span = start_span + self.request_delta
            else:
                end_span = end_time
            spans.append( (start_span.timetuple()[:4],
                           end_span.timetuple()[:4]) )
            # set next 'start_span' to previous `end_span` because ts_var
            # always returns one hour less than requested
            start_span = end_span

        # accumulate data array
        hourly_data = [ ]
    
        # add retrievable data to array
        for start_span, end_span in spans:
            if debug: print 'set span', start_span, end_span
            try:
                ts_var.setDateRange(start_span, end_span)

            except Data.TSVar.UnavailableDateRange:
                # sometimes we get bad time ranges so we pass back
                # a bunch of missing values
                hours = self.elapsedHours(start_span, end_span)
                tsv_data = [-32768 for hour in range(hours)]

            except Exception as e:
                ts_var.release()
                msg = "failed call to ts_var.setDateRange(%s, %s) for '%s'"
                detail = msg % (str(start_span), str(end_span), elem)
                raise UcanDataError, explainException(e, station_dict, detail)

            else:
                try:
                    tsv_data = ts_var.getDataSeqAsFloat()
                    #print start_span, end_span
                    #print tsv_data
                except Exception as e:
                    ts_var.release()
                    msg = "failed call to ts_var.getDataSeqAsFloat() for '%s' from %s thru %s"
                    detail = msg % (elem, str(start_span), str(end_span))
                    explanation = explainException(e, station_dict, detail)
                    raise UcanDataError, explanation

            hourly_data.extend(tsv_data)

        ts_var.release()

        if debug:
            msg = '%s %d : num hours = %d : num_days = %d'
            num_hours = len(hourly_data)
            print msg % (sid,ucanid, num_hours, num_hours/24)

        hourly_data = N.array(hourly_data, dtype=dtype)
        if missing != -32768:
            hourly_data[N.where(hourly_data == -32768)] = missing
        return (start_date_.timetuple()[:4], end_date_.timetuple()[:4],
                hourly_data)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getMetadata(self, station_dict):
        _station_dict = AsciiSafeDict.makeSafe(station_dict, True)
        query = self.ucan.get_query()
        try:
            metadata = query.getInfoForUcanIdAsSeq(_station_dict['ucanid'],())
            metadata = ucanCallMethods.NameAny_to_dict(metadata[-1].fields)
            if 'id' in metadata and isinstance(metadata['id'], int):
                metadata['id'] = str(metadata['id'])
            return metadata
        except Exception as e:
            detail = "failed for query metadata using UCAN interface."
            raise UcanDataError, explainException(e, station_dict, detail)
        finally:
            query.release()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getTsVar(self, station_dict, element_name):
        network = station_dict['network'].encode('iso-8859-1')
        if not isinstance(station_dict, AsciiSafeDict): 
            _station_dict = AsciiSafeDict.makeSafe(station_dict, True)
        else: _station_dict = station_dict
        stn_id = self._getStationId(_station_dict, True)

        exception = None
        major_minor_group = None
        tsvar_groups = getTsVarCodeset(network, element_name)
        for major_minor_group in tsvar_groups:
            try:
                return self._getTsVar(_station_dict, major_minor_group, False)
            except Exception as e:
                if 'UnknownUcanId' in e.__class__.__name__:
                    exception = e
                else: raise e

        uid = _station_dict['ucanid']
        msg = 'Unable to acquire tsvar for %s element of station %s (%s)' 
        detail = msg % (element_name, station_dict['sid'], station_dict['name'])
        mms = str(major_minor_group)
        #mms = ' and '.join( ['(%d,%d)' % major_minor
        #                     for major_minor in major_minor_group])
        msg = '%s are not valid tsvars for the station/network combination.'
        detail = msg % mms
        raise UcanInvalidTsvarError, explainException(exception, station_dict, detail)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getValidDateRange(self, station_dict, elem, debug=False):
        _station_dict = AsciiSafeDict.makeSafe(station_dict, True)
        if isinstance(elem,(tuple,list)):
            ts_var = self._getTsVar(_station_dict, elem)
        else:
            ts_var = self.getTsVar(_station_dict, elem)

        start_time, end_time = ts_var.getValidDateRange()
        ts_var.release()

        return start_time, end_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ucanid(self, station_dict):
        network = station_dict['network'].encode('iso-8859-1')
        _station_dict = AsciiSafeDict.makeSafe(station_dict, True)
        station_id = self._getStationId(_station_dict, True)
        try:
            query = self.ucan.get_query()
            result = query.getUcanFromIdAsSeq(station_id, network)
        except Exception as e:
            detail = 'Unable to acquire UCAN ID for station.'
            raise UcanStationIDError, explainException(e, station_dict, detail)
        finally:
            query.release()

        if len(result) > 0:
            return result[-1].ucan_id
        else:
            errmsg = 'UCAN ID was not found for : %s'
            raise KeyError, errmsg % (STATION_INFO % station_dict)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _getTsVar(self, station_dict, major_minor_tuple,
                        explain_exception=True):
        if not isinstance(station_dict, AsciiSafeDict): 
            _station_dict = AsciiSafeDict.makeSafe(station_dict, True)
        else: _station_dict = station_dict
        major, minor = major_minor_tuple
        data = self.ucan.get_data()
        try:
            if _station_dict['network'] == 'icao':
                station_id = self._getStationId(_station_dict, True)
                return data.newTSVarNative(major, minor, station_id)
            else:
                return data.newTSVar(major, minor, _station_dict['ucanid'])
        except Exception as e:
            data.release()
            if explain_exception:
                msg = '(%d,%d) is not a valid tsvar for the network/ucanid combination.'
                explain = explainException(e, station_dict, msg % (major,minor))
                raise UcanInvalidTsvarError, explain
            else: raise e

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _getStationId(self, station_dict, encode=True):
        if not isinstance(station_dict, AsciiSafeDict): 
            _station_dict = AsciiSafeDict.makeSafe(station_dict, True)
        else: _station_dict = station_dict
        if 'id' in _station_dict:
            if isinstance(_station_dict['id'], int):
                 return str(_station_dict['id'])
            else:
                if encode: return _station_dict['id'].upper().encode('ascii')
                else: return _station_dict['id']
        else:
            if isinstance(_station_dict['sid'], int):
                 return str(_station_dict['sid'])
            else:
                if encode: return _station_dict['sid'].upper().encode('ascii')
                else: return _station_dict['sid']



import itertools

try:
    import simplejson as json
except ImportError:
    import json

import numpy as N

from rccpy.acis.client import BaseAcisClient

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from nrcc.stations.client import PRECIP_ELEM_NAMES

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AcisStationDataClient(BaseAcisDataClient):


    def getData(self, **kwargs):
        station = self.getRawData(elems, start_date, end_date, meta,
                                  method, **kwargs)
        elem_dict = self.extractArraysAndSerialize(elems, station['data'])
        del station['data']
        station['data'] = elem_dict
        return station

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getMaskedData(self, elems, start_date, end_date=None, meta=None,
                            ignore_outliers=False,  method='POST', **kwargs):
        if self.debug:
            msg = 'getMaskedData(elems=%s, start_date=%s, end_date=%s,'
            msg += ' meta=%s, ignore_outliers=%s, method=%s, **kwargs=%s)'
            print msg % (str(elems), str(start_date), str(end_date),
                         str(meta), ignore_outliers, method, str(kwargs))
        #
        station = self.getData(elems, start_date, end_date, meta, method,
                               **kwargs)
        if 'error' in station:
            errmsg = station['error'] + '\n(%s, %s, %s, %s)'
            raise ValueError, errmsg % (str(elems), str(start_date),
                                        str(end_date), str(kwargs))

        # mask out missing values in data arrays 
        for elem_id in station['elems']:
            elem_data = station['data'][elem_id]
            elem_data = N.ma.masked_where(N.isnan(elem_data), elem_data)
            station['data'][elem_id] = elem_data
        #
        return station

    def getRawData(self, elems, start_date, end_date=None, meta=None,
                         method='POST', **kwargs):
        if self.debug:
            msg = 'getRawData(elems=%s, start_date=%s, end_date=%s,'
            msg += ' meta=%s, method=%s, **kwargs=%s)'
            print msg % (str(elems), str(start_date), str(end_date),
                         str(meta), method, str(kwargs))
        #
        start_date = self.dateAsString(start_date)
        if end_date is not None:
            end_date = self.dateAsString(end_date)
        else:
            end_date = start_date

        kwargs.update({ 'sDate':start_date, 'eDate':end_date })
        if meta is not None:
            kwargs['meta'] = meta
        elems, data, response = self.request('StnData', method, elems=elems,
                                              **kwargs)

        try:
            station = json.loads(data)
        except ValueError:
            ecode = 500
            errmsg = 'Server Error : '
            if 'DOCTYPE HTML PUBLIC' in data:
                if 'server encountered an internal error' in data:
                    errmsg += 'server encountered an unspecified internal error.'
                    ecode = 503
                else:
                    errmsg += 'server returned HTML, not valid JSON.\n'
                    errmsg +=  data
            else:
                errmsg = 'Improperly formated JSON return by server.\n'
                errmsg +=  data
            raise urllib2.HTTPError(response.geturl(),ecode,errmsg,None,None)

        if self.debug:
            print 'Web service returned the following :'
            print station

        station['start_date'] = start_date
        station['end_date'] = end_date
        return elems, station

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def extractArrays(self, station_data):
        return map(list, itertools.izip(*station_data))

    def extractArraysAndSerialize(self, elems, station_data):
        elem_ids = [self.validElementID(elem) for elem in elems]
        elem_data = self.extractArrays(station_data)
        elem_dict = { 'dates' : N.array(elem_data[0]) } 
        i = 0
        while i < len(elem_ids):
            j=i+1
            elem_id = elem_ids[i]
            elem_dict[elem_id] = self.serializeElemArray(elem_id, elem_data[j])
            i+=1
        del elem_data, elem_ids
        return elem_dict

    def serializeElemArray(self, elem_id, data, show_trace=False):
        data_array = N.array(data, dtype=unicode)
        data_array[data_array == 'M'] = u'-32768.'
        if elem_id in PRECIP_ELEM_NAMES:
            data_array[data_array == 'S'] = u'-32768.'
            data_array[data_array == 'A'] = u'-32768.'
            data_array[data_array == 'T'] = u'0.005'
        data_array = N.array(data_array, dtype=float)
        data_array[data_array <= -32768.] = N.nan
        return data_array


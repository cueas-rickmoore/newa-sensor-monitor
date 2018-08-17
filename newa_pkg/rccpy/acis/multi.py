
from datetime import datetime
import urllib2

try:
    import simplejson as json
except ImportError:
    import json

import numpy as N

from nrcc.stations.client import BaseAcisDataClient

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AcisMultiStationDataClient(BaseAcisDataClient):

    AREA_CODE_KEYS = frozenset(['state','county','climdiv','cwa','basin',
                                'bbox'])

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getData(self, elems, date, metadata=None, method='POST',
                      **request_args):
        if self.debug:
            msg = 'getData(elems=%s, sdate=%s, meta=%s, method=%s)'
            print msg % (str(elems), str(date), str(metadata), method)

        stations = self.getRawData(elems, date, metadata, method,
                                   **request_args)
        return self.serializeDataValues(stations)

    def getRawData(self, elems, date, metadata=None, method='POST',
                         **request_args):
        if self.debug:
            msg = 'getRawData(elems=%s, sdate=%s, meta=%s, method=%s, %s)'
            print msg % (str(elems), str(date), str(metadata), method,
                         str(request_args))

        matches = self.AREA_CODE_KEYS & set(request_args.keys())
        if len(matches) < 1:
            errmsg = 'An area code is required for multi-station data requests.'
            raise ValueError, errmsg
        elif len(matches) > 1:
            errmsg = 'Only one area code may be specified for multi-station data requests.'
            raise ValueError, errmsg

        request_args['date'] = self.dateAsString(date)
        if elems is None:
            request_args['elems'] = self.default_elements
        else:
            request_args['elems'] = elems
        if metadata is None:
            request_args['meta'] = self.default_metadata
        else:
            request_args['meta'] = metadata

        start_time = datetime.now()

        elems, data, response = self.request('MultiStnData', method,
                                             **request_args)
        stations = self._pythonObjectsFromJson(data, response,
                                               json.dumps(request_args))

        if self.performance:
            self.reporter.logPerformance(start_time,
                                          "Converted json to dict in")

        stations['elems'] = elems

        if 'error' in stations:
            raise ValueError, stations['error']

        return stations

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def allStationsInState(self, state, elems, date, metadata=None, **kwargs):
        if self.debug:
            print 'acquiring data for stations in', state, date
        start_time = datetime.now() # for performance reporting
        kwargs['state'] = state
        stations = self.getData(elems, date, metadata, **kwargs)

        if self.performance:
            msg = 'Retrieved and serialized data for %d stations in %s in'
            self.reporter.logPerformance(start_time,
                                         msg % (len(stations['data']),state))
        return stations

    def serializeDataValues(self, stations):
        elements = stations['elems']
        elem_indexes = range(len(elements))

        for station in stations['data']:
            if 'data' not in station: continue
            for indx in elem_indexes:
                serialized = self.serializeDataValue(elements[indx],
                                                     station['data'][indx])
                station['data'][indx] = serialized

        return stations


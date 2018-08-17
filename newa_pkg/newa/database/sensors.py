
import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

import numpy as N

from rccpy.utils.timeutils import asDatetime, dateAsInt

from newa.ucan import HourlyDataConnection
from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def latestReportDate(station, newa_base_time, icao_base_time, debug=False):
    """ Returns latest date that any sensor reported
    """
    last_report = 0

    if debug:
        print '\nprocessing station %(sid)s : %(name)s' % station
    
    # get list of datasets to check
    sensor_types = [sensor_type.strip()
                     for sensor_type in station['datasets'].split(',')]
    sensor_types.sort()

    # make connection to UCAN server
    connection = HourlyDataConnection()

    # reset start/end times
    if station['network'] == 'icao':
        requested_end_time = icao_base_time
    else: requested_end_time = newa_base_time

    # looking for latest date that any data sensor reported
    for sensor_type in sensor_types:

        # find out the range of dates available for this dataset
        data_start_time, data_end_time =\
        connection.getValidDatetimeRange(station, sensor_type, False)
        if debug:
            msg = '    %s : ucan advertised time span = %s thru %s'
            print msg % (sensor_type, data_start_time.strftime('%Y%m%d:%H'),
                         data_end_time.strftime('%Y%m%d:%H'))

        end_time = min(requested_end_time, data_end_time)
        start_time = end_time - relativedelta(hours=23)
        if debug:
            msg = '    %s : interval start time = %s, interval end time = %s'
            print msg % (sensor_type, start_time.strftime('%Y%m%d%H'),
                         end_time.strftime('%Y%m%d%H'))
        # get data for first interval
        data_from, data_to, data = \
        connection.getData(station, sensor_type, start_time, end_time, False)
        data_from = dateAsInt(data_from,True)
        data_to = dateAsInt(data_to,True)

        # work backwards to latest finite value returned, if any
        _continue_ = True
        while _continue_:
            # must contain 24 hours to be valid data
            if len(data) == 24:
                if debug:
                    msg = '    %s : data returned for period %d to %d'
                    print msg % (sensor_type, data_from, data_to)
                # look for latest hour that a finite data value was returned
                for hour in range(23,-1,-1):
                    if N.isfinite(data[hour]):
                        valid_time = start_time + relativedelta(hours=hour)
                        valid_time = dateAsInt(valid_time, True)
                        last_report = max(valid_time, last_report)
                        if debug:
                            msg = '    %s : finite value (%-.2f) found at data[%d] : %d'
                            print msg % (sensor_type, data[hour], hour, valid_time)
                        _continue_ = False
                        break
            else:
                if debug:
                    msg = '    %s : ALL data missing in period %d to %d'
                    print msg % (sensor_type, data_from, data_to)

            # go back one day and check again
            start_time -= ONE_DAY
            if (int(start_time.strftime('%Y%m%d%H')) > last_report
                and start_time >= data_start_time):
                end_time -= ONE_DAY
                data_from, data_to, data = \
                connection.getData(station,sensor_type,start_time,end_time,False)
                data_from = dateAsInt(data_from,True)
                data_to = dateAsInt(data_to,True)
            else: _continue_ = False

    # delete the UCAN connection for this station
    del connection
    
    return last_report


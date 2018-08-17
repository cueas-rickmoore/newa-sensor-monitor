
from datetime import datetime

import numpy as N

from newa.sensors.detector import SensorErrorDetector

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.sensors.config import sensors as SENSORS

DASHES = '-' * 80
EQUALS = '=' * 80
NO_PRECIP = '%(name)s (%(sid)s) did not detect precip yet grid shows precip in all nearby nodes'
GHOST_PRECIP = '%(name)s (%(sid)s) detected precip but no nearby grid nodes show precip'
STATION_EMAIL_SENT = 'Email sent to : %s'
STATION_IDENT = '\n%(sid)s : %(name)s : %(ucanid)d'
STATION_INFO = '\n\n%s%s\n%s' % (EQUALS,STATION_IDENT,DASHES)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def arrayToString(precip):
    if len(precip.shape) > 1:
        return ' '.join(['%-.2f' % p for p in precip])
    else: return ' '.join(['%-.2f' % p for p in precip])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class PrecipErrorDetector(SensorErrorDetector):

    def __init__(self, decisionTree, start_hour=7, end_hour=7, padding=6,
                       missing_threshold=1, grid_offset=0.05, networks='all',
                       notify_stations=False, track_missing=False, 
                       verbose=False, test_run=False, debug=False):
        SensorErrorDetector.__init__(self, 'pcpn', decisionTree, start_hour,
                            end_hour, padding, missing_threshold, grid_offset,
                            networks, notify_stations, track_missing, verbose,
                            test_run, debug)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ghostPrecip(self, date, sensor, station, grid):
        debug = self.debug
        verbose = self.verbose

        station['error'] = GHOST_PRECIP % station
        message = 'station = %-.2f : grid = 0' % station['total_precip']
        self._trackStationError(date, station, message, grid)

        station, email_msg = self.sendStationEmail(sensor, station)
        if 'email_sent_to' in station:
            message = STATION_EMAIL_SENT % station['email_sent_to']
        else: message = '***** no email sent *****'
        if debug: print message
        else: self.writeToLog(date, '\n%s' % message)
        self._addSummaryMessage(station, message)

        return station, email_msg

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def noPrecip(self, date, sensor, station, grid):
        debug = self.debug
        verbose = self.verbose

        extended, start_time, end_time =\
        self.getStationData(date, sensor, station, self.padding)

        extended_total = extended.sum()
        num_nodes = len(N.where(grid >= SENSORS.pcpn.grid_threshold)[0])
        if extended_total == 0 and num_nodes == grid.size:
            station['error'] = NO_PRECIP % station

            grid_max = N.nanmax(grid)
            grid_min = N.nanmin(grid)
            if grid_min != grid_max:
                grid_str = 'grid = %-.2f to %-.2f' % (grid_min, grid_max)
            else: grid_str = 'grid = %-.2f' % grid_min

            total_precip = station['total_precip']
            message = 'station = %-.2f : %s' % (total_precip, grid_str)
            self._trackStationError(date, station, message, grid)

            message = 'extended : [%s]' % arrayToString(extended)
            if debug: print message
            else: self.writeToLog(date, '\n%s' % message)
            if debug or verbose: self._addSummaryMessage(station, message)

            message = 'extended station = %-.2f : %s' % (extended_total, grid_str)
            if debug: print message
            else: self.writeToLog(date, '\n%s' % message)
            if debug or verbose: self._addSummaryMessage(station, message)

            station, email_msg = self.sendStationEmail(sensor, station)
            if 'email_sent_to' in station:
                message = STATION_EMAIL_SENT % station['email_sent_to']
            else: message = '***** no email sent *****'
            if debug: print message
            else: self.writeToLog(date, '\n%s' % message)
            self._addSummaryMessage(station, message)

            return station, email_msg 
        return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _isValidStationData(self, date, station, data_info):
        debug = self.debug
        if data_info is None:
            if self.track_missing:
                errmsg = 'precip data is not available for this date.'
                if debug: print errmsg
                self._trackStationError(date, station, errmsg)
            return False

        data, start_time, end_time = data_info
        if len(data) == 0:
            if self.track_missing:
                errmsg = 'precip data wass not reported on this date.'
                if debug: print errmsg
                self._trackStationError(date, station, errmsg)
            return False

        num_missing = len(N.where(N.isnan(data))[0])
        if num_missing > self.missing_threshold:
            if self.track_missing:
                errmsg = '%d of 24 hours had missing precip data' % num_missing
                if debug: print errmsg % (num_missing, self.missing_threshold)
                self._trackStationError(date, station, errmsg)
            return False

        return True

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _trackStationError(self, date, station, details, grid=None):
        SensorErrorDetector._trackStationError(self, date, station, details)
        if grid is not None:
            debug = self.debug
            verbose = self.verbose

            data = 'station : [%s]' % arrayToString(station['data'])
            if debug: print data
            else: self.writeToLog(date, '\n%s' % data)
            if debug or verbose: self._addSummaryMessage(station, data)

            data = 'grid data : [%s]' % arrayToString(grid)
            if debug: print data
            else: self.writeToLog(date, '\n%s' % data)
            if debug or verbose: self._addSummaryMessage(station, data)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _preprocessStationData(self, station, data_info):
        data, start_time, end_time = data_info
        station['data'] = data
        station['start_time'] = datetime(*start_time)
        station['end_time'] = datetime(*end_time)
        station['total_precip'] = data.sum()
        return station


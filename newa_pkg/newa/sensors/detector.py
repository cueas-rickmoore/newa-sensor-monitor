#! /Users/rem63/venvs/nrcc_prod/bin/python

import os, sys
from datetime import datetime
import urllib, urllib2

from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

try:
   import json 
except ImportError:
   import simplejson as json

import numpy as N

from rccpy.grid.utils import neighborNodes
from rccpy.utils.mailers import SmtpMailer, SmtpHtmlMailer
from rccpy.utils.timeutils import asDatetime
from rccpy.utils.timeutils import dateAsInt, dateAsTuple, dateAsString

from newa.ucan import getTsVarType, HourlyDataConnection

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config as CONFIG

from newa.sensors.config import sensors as SENSORS

DASHED_LINE = ('-' * 80)
EQUALS_LINE = ('=' * 80)
STATION_INFO = '%(sid)s : %(name)s : %(ucanid)d : active=%(active)s'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SensorErrorDetector(object):

    def __init__(self, sensor, decisionTree, start_hour=8, end_hour=7,
                       padding=0, missing_threshold=1, grid_offset=0.05,
                       networks='all', notify_stations=False,
                       track_missing=False, verbose=False, test_run=False,
                       debug=False):

        self.grid_offset = grid_offset
        self.debug = debug
        self.decisionTree = decisionTree
        self.end_hour = relativedelta(hours=end_hour)
        self.missing_threshold = missing_threshold
        if networks == 'all': self.networks = None
        else: self.networks = networks
        self.notify_stations = notify_stations
        self.padding = padding
        self.sensor = sensor
        self.start_hour = relativedelta(hours=start_hour)
        self.test_run = test_run
        self.track_missing = track_missing
        self.verbose = verbose | debug | test_run

        self.headers = SENSORS.email.header
        self.html_templates = SENSORS.email.content.error.html
        self.html_error_keys = SENSORS.email.content.error.html.keys()
        self.summary_templates = SENSORS.email.content.summary
        self.text_templates = SENSORS.email.content.error.text
        self.text_error_keys = SENSORS.email.content.error.text.keys()

        self.data_cache = { 'stn_sid':None, 'grid_sid':None }
        self.mailer = None
        self.previous_station_id = None
        self.summary_by_station = { }

        self.log_dirpath = CONFIG.log_dirpath
        self.log_filepath = None
        self.log_file = None
        self.log_date = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, date, station):
        debug = self.debug
        sensor = self.sensor

        if self._isStationOfInterest(station):
            station_info = '%(sid)s : %(name)s' % station
            if debug:
                print '\n***** processing', station_info

            data_info = self.getStationData(date, sensor, station)
            if self._isValidStationData(date, station, data_info):
                grid = self.getGridData(date, sensor, station)
                station = self._preprocessStationData(station, data_info)
                return self.decisionTree(self, date, sensor, station, grid)
        return None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getGridData(self, date, sensor, station):
        lon = station['lon']
        lat = station['lat']

        bbox_str = str(lon - self.grid_offset) + ','
        bbox_str += str(lat - self.grid_offset) + ','
        bbox_str += str(lon + self.grid_offset) + ','
        bbox_str += str(lat + self.grid_offset)
        if station['sid'] != self.data_cache['grid_sid']:
            params = { "bbox" : bbox_str, "date" : date.strftime('%Y%m%d'),
                       "grid" : 3, "elems" : "%s" % sensor,
                       'meta' : 'll' }
            new_station = True
        else:
            params = { "bbox" : bbox_str, "date" : date.strftime('%Y%m%d'),
                       "grid" : 3, "elems" :  "%s" % sensor }
            new_station = False

        params = urllib.urlencode({'params':json.dumps(params)})
        request = urllib2.Request('http://data.rcc-acis.org/GridData',
                                  params, {'Accept':'application/json'})
        response = urllib2.urlopen(request)
        result = json.loads(response.read())

        # ACIS may return a grid that is filled with '-999' and json converts
        # it to an int64 array. So we need to specify dtype as float
        data = N.array(result['data'][0][1], dtype=float).flatten()
        # handle case where ACIS puts 'inf' into the json string
        data[ N.where(N.isinf(data)) ] = N.nan
        # handle case where ACIS puts '-999' into the json string
        data[ N.where(data == -999) ] = N.nan

        if new_station: # save grid info for this station
            lats = N.array(result['meta']['lat']).flatten()
            lat_diffs = station['lat'] - lats
            lons = N.array(result['meta']['lon']).flatten()
            lon_diffs = station['lon'] - lons
            distances = N.sqrt( (lon_diffs*lon_diffs) + (lat_diffs*lat_diffs) )
            
            self.data_cache['grid_sid'] = station['sid']
            self.data_cache['closest'] = N.where(distances == distances.min())
            self.data_cache['distances'] = distances
            self.data_cache['grid_lats'] = lats
            self.data_cache['grid_lons'] = lons

        return data

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getStationData(self, date, sensor, station, padding=0):
        ucan = HourlyDataConnection(days_per_request=2)

        if station['sid'] != self.data_cache['stn_sid']:
            ucan_start, ucan_end = ucan.getValidDatetimeRange(station,
                                                              sensor)
            self.data_cache['ucan_start'] = ucan_start
            self.data_cache['ucan_end'] = ucan_end
            self.data_cache['stn_sid'] = station['sid']
        else:
            ucan_start = self.data_cache['ucan_start']
            ucan_end = self.data_cache['ucan_end']

        start_time, end_time = self._getStartEndTime(date)
        if padding > 0:
            hours = relativedelta(hours=padding)
            start_time -= hours
            end_time += hours

        if start_time < ucan_start or start_time > ucan_end: return None
        if end_time > ucan_end or end_time < ucan_start: return None

        start_time = dateAsTuple(start_time, True) 
        end_time = dateAsTuple(end_time, True)
        _start_date_, _end_date_, data =\
        ucan.getData(station, sensor, start_time, end_time)
        del ucan

        data = N.array(data)
        data[N.where(N.isinf(data))] = N.nan
        return data, start_time, end_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def initStationMailer(self, smtp_host):
        if self.mailer is not None: self.mailer.stop()
        self.mailer = SmtpHtmlMailer(smtp_host)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def sendStationEmail(self, sensor, station):
        if not self.notify_stations: return station, None

        header = self._getEmailHeader('error', station)

        end_time = station['end_time']
        station['period_end'] = end_time.strftime('%b %d, %Y at %I %p')

        if sensor in self.text_error_keys:
            station['signature'] = header['signature']
            text = self.text_templates[sensor] % station
        else: text = None

        station['signature'] = station['signature'].replace('\n','</br>')
        html = self.html_templates[sensor] % station

        msg  = self.mailer.sendMessage(header['sender'], header['mail_to'],
                                       header['subject'], html, text=text,
                                       cc=header['cc'], bcc=header['bcc'], 
                                       test=False, debug=False)
        if self.verbose:
            if self.debug:
                print '\nMessage sent:'
                print msg.as_string()
            else:
                print '\nemail sent to :', header['mail_to']
                print 'subject :', header['subject']

        if msg is not None:
            station['email_sent_to'] = msg['To']
        return station, msg

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def sendSummaryEmail(self, smtp_host, preface=None, subject=None):
        header = self._getEmailHeader('summary', {'sensor' : self.sensor,})
        if subject is not None: header['subject'] = subject

        if preface is not None: summary = preface
        else: summary = ''
        if self.debug: print 'sendSummaryEmail header:\n', header

        if self.summary_by_station:
            station_names = self.summary_by_station.keys()
            station_names.sort()
            for name in station_names:
                summary += '\n' + '\n'.join(self.summary_by_station[name])

        mailer = SmtpMailer(smtp_host)
        msg  = mailer.sendMessage(header['sender'], header['mail_to'],
                                  header['subject'], summary,
                                  cc=header['cc'], bcc=header['bcc'], 
                                  test=False, debug=False)
        mailer.stop()

        if self.verbose:
            print '\nSummary email sent to :', header['mail_to']
            print 'subject :', header['subject']

        return msg

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def stopStationMailer(self):
        if self.mailer is not None: self.mailer.stop()

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def closeLogFile(self):
        if self.log_file is not None:
            self.log_file.close()
            self.log_file = None

    def logFilePath(self, date):
        filename = '%s_%s_sensor_error.log' % (date.strftime('%Y%m%d'),
                                               self.sensor)
        return os.path.join(self.log_dirpath, filename)

    def openLogFile(self, date, mode='a'):
        self.closeLogFile()
        filepath = self.logFilePath(date)
        self.log_file = open(filepath, mode)
        self.log_filepath = filepath
        self.log_date = date
        return self.log_file

    def writeToLog(self, date, message):
        if date != self.log_date or self.log_file is None:
            self.openLogFile(date)
        self.log_file.write(message)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def _addSummaryMessage(self, station, *messages):
        name = station['name']
        if name not in self.summary_by_station:
            self.summary_by_station[name] = [ ]
        if len(messages) == 1:
            self.summary_by_station[name].append(messages[0])
            if self.debug: print messages[0]
        else:
            self.summary_by_station[name].extend(messages)
            if self.debug: print '\n'.join(messages)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _getEmailHeader(self, header_key, station):
        header_tmpls = self.headers[header_key]
        if self.debug:
            header_tmpls.update(self.headers['debug'].asDict())
            if 'error' in station:
                header_tmpls['subject'] = station['error']
        elif self.test_run:
            header_tmpls.update(self.headers['test'].asDict())
            if 'error' in station:
                header_tmpls['subject'] = station['error']

        if 'sensor' not in station: station['sensor'] = self.sensor

        header = { 'sender'    : header_tmpls['sender'] % station,
                   'mail_to'   : header_tmpls['mail_to'] % station,
                   'signature' : header_tmpls['signature'],
                 }

        subject = header_tmpls['subject'] % station
        if self.test_run: subject = station.get('error', subject)
        header['subject'] = subject

        if 'title' in header_tmpls:
            header['title'] = header_tmpls['title'] % station

        cc = header_tmpls.get('cc',None)
        if cc is not None:
            if '%(bcontact)s' in cc:
                bcontact = station.get('bcontact', None)
                bemail = station.get('bemail', None)
                if bcontact and bemail: cc = cc % station
                else: cc = None
        header['cc'] = cc

        bcc = header_tmpls.get('bcc',None)
        if bcc and '%(' in bcc: header['bcc'] = bcc % station
        else: header['bcc'] = bcc

        return header

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _getStartEndTime(self, date):
        if isinstance(date, (tuple,list)):
            _datetime_ = datetime(date[0], date[1], date[2], 0)
        else:
            _datetime_ = datetime(date.year, date.month, date.day, 0)
        start_time = (_datetime_ - ONE_DAY) + self.start_hour
        end_time = _datetime_ + self.end_hour
        return start_time, end_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _isValidStationData(self, date, station, data):
        if data is None: return False
        return True

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _isStationOfInterest(self, station):
        if station['active'] != 'Y': return False
        if self.networks is not None \
        and station['network'] not in self.networks: return False
        return True

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _preprocessStationData(self, station, data_info):
        data, start_time, end_time = data_info
        station['data'] = data
        station['start_time'] = datetime(*start_time)
        station['end_time'] = datetime(*end_time)
        return station

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _trackStationError(self, date, station, details):
        debug = self.debug
        verbose = self.verbose

        if station['sid'] != self.previous_station_id:
            station_info = STATION_INFO % station
            info = '\n\n%s\n%s\n%s' % (EQUALS_LINE, station_info, DASHED_LINE)
            if debug: print station_info
            else: self.writeToLog(date, info)
            self._addSummaryMessage(station, ' ', EQUALS_LINE, station_info,
                                    DASHED_LINE)
            self.previous_station_id = station['sid']

        if 'error' in station:
            error = '\n%s\n%s' % (date.strftime('%B %d, %Y'), station['error'])
            if debug: print error
            else: self.writeToLog(date, '\n%s' % error)
            self._addSummaryMessage(station, error)

        if details:
            if debug: print details
            else: self.writeToLog(date, '\n%s' % details)
            self._addSummaryMessage(station, details)


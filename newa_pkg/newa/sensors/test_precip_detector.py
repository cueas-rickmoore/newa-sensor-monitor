#! /Volumes/projects/venvs/newa/bin/python

import os, sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

# necessary to set filters to ignore certain warnings issued by NUMPY 
import warnings

from rccpy.utils.mailers import SmtpHtmlMailer
#from rccpy.utils.mailers import SmtpMailer

from newa.factory import ObsnetDataFactory
from newa.sensors.decisions import precipValidationTree
from newa.sensors.precip import PrecipErrorDetector

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config as CONFIG
from newa.sensors.config import sensors as SENSORS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# station search criteria
parser.add_option('--bbox', action='store', type='string', dest='bbox',
                  default=None)
parser.add_option('--county', action='store', type='string', dest='county',
                  default=None)
parser.add_option('--name', action='store', type='string', dest='name',
                  default=None)
parser.add_option('--networks', action='store', type='string', dest='networks',
                  default='cu_log,newa')
parser.add_option('--sid', action='store', type='string', dest='sid',
                  default=None)
parser.add_option('--smtp', action='store', type='string', dest='smtp_host',
                  default=CONFIG.services.email.smtp_host)
parser.add_option('--state', action='store', type='string', dest='state',
                  default=None)

parser.add_option('-e', action='store', type='int', dest='end_hour',
                  default=SENSORS.end_hour)
parser.add_option('-g', action='store', type='float', dest='grid_offset',
                  default=SENSORS.grid_offset)
parser.add_option('-m', action='store', type='string', dest='metadata',
                  default=SENSORS.station_metadata)
parser.add_option('-p', action='store', type='int', dest='padding',
                  default=SENSORS.pcpn.resample_padding)
parser.add_option('-r', action='store_false', dest='run_detector',
                  default=True)
parser.add_option('-s', action='store', type='int', dest='start_hour',
                  default=SENSORS.start_hour)
parser.add_option('-t', action='store', type='int', dest='missing_threshold',
                  default=SENSORS.pcpn.missing_threshold)
parser.add_option('-v', action='store_false', dest='verbose', default=True)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_false', dest='test_run', default=True)
parser.add_option('-z', action='store_false', dest='debug', default=True)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

separator = "*" * 72
header = "\n%s\n%%(name)s (%%(sid)s)\n%s\n" % (separator, separator)

sensor = 'pcpn'

num_args = len(args)
if num_args == 6:
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
    start_date = datetime(year, month, day, 0)
    year = int(args[3])
    month = int(args[4])
    day = int(args[5])
    end_date = datetime(year, month, day, 0)
elif num_args == 3:
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
    start_date = end_date = datetime(year, month, day, 0)
elif num_args == 0: 
    # cannot check the current date because ACIS grid coverage is always
    # 1 day behind station data coverage
    now = datetime.now() - ONE_DAY
    start_date = end_date = datetime(now.year, now.month, now.day, 0)
else:
    explain = "%d is an invalid number of arguments. Must be"
    explain += " 0 for the current day, 3 for a single day (year,month.day)"
    explain += " or 6 for a time span (start date and end date)"
    raise ValueError, explain % num_args

debug = options.debug
end_hour = options.end_hour
grid_offset = options.grid_offset
loggable = False
metadata = options.metadata.split(',')
missing_threshold = options.missing_threshold
networks = tuple(options.networks.split(','))
padding = options.padding
notify_stations = False
run_detector = options.run_detector
smtp_host = options.smtp_host
start_hour = options.start_hour
verbose = options.verbose
test_run = options.test_run

if options.county is not None and 'county' not in metadata:
    metadata.append('county')
if options.state is not None and 'state' not in metadata:
    metadata.append('state')

num_days = (end_date - start_date).days + 1
date_str = start_date.strftime('%Y-%m-%d')
if num_days == 1: print '1 day', date_str
else: print num_days, 'days', date_str, 'thru', end_date.strftime('%Y-%m-%d')

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# crcreate the detector
detector = PrecipErrorDetector(precipValidationTree, start_hour, end_hour,
                               padding, missing_threshold, grid_offset,
                               networks, notify_stations, verbose, test_run,
                               debug)

# get the stations for this run
if run_detector:
    factory = ObsnetDataFactory(options)
    stations = factory.argsToStationData((), options, tuple(metadata))
    for station in stations:
        date = start_date
        while date <= end_date:
            detected = detector(date, station)
            date += ONE_DAY

    # create the preface for the summary email
    if end_date is None or end_date == start_date:
        date_str = 'on %s' % start_date.strftime('%B %d, %Y')
    else:
        date_str = 'from %s to %s' % (start_date.strftime('%B %d, %Y'),
                                      end_date.strftime('%B %d, %Y'))

    
    print detector.summary_by_station
    if detector.summary_by_station:
        preface = 'Stations with precip sensor errors %s' % date_str
        subject = 'Potential precip sensor errors detected.'
    else:
        preface = 'No precip sensor errors detected %s' % date_str
        subject = 'No precip sensor errors detected.'

header = detector._getEmailHeader('summary',{'sensor':'pcpn'})
print 'summary email header :'
keys = header.keys()
keys.sort()
print '\n'.join([ '    %s = %s' % (key, header[key]) for key in keys])

if run_detector:
    email_msg = detector.sendSummaryEmail(smtp_host, preface, subject)

sys.stdout.flush()

# turn annoying numpy warnings back on
warnings.resetwarnings()


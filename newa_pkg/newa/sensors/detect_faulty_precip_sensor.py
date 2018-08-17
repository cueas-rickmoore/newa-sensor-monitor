#! /Volumes/projects/venvs/newa/bin/python

import os, sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

# necessary to set filters to ignore certain warnings issued by NUMPY 
import warnings

from rccpy.utils.exceptutils import captureLastException
from rccpy.utils.mailers import SmtpHtmlMailer

from newa.factory import ObsnetDataFactory
from newa.sensors.decisions import precipValidationTree
from newa.sensors.precip import PrecipErrorDetector

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config as CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def detectLargeDiffs(date_str, station, stn_total, stn_precip, grid_max,
                     grid_precip):

    closest_precip = grid_precip[DATA_CACHE['closest']]
    closest_diff = stn_total - closest_precip
    closest_gt_station = 'closest node precip is %-.2f times greater than station'
    closest_msg = 'station = %-.2f : closest node = %-.2f : diff = %-.2f'
    grid_diff = stn_total - grid_max
    grid_gt_station = 'max grid precip is %-.2f times greater than station'
    max_diff_msg = 'station = %-.2f : grid max = %-.2f : diff = %-.2f'
    station_gt_closest = 'station precip is %-.2f times greater than closest node'
    station_gt_grid = 'station precip is %-.2f times greater than grid max'

    if stn_total > 0 and grid_max > 0:
        grid_magnitude = max(stn_total,grid_max) / min(stn_total,grid_max)
    else: grid_magnitude = None

    closest_magnitude = [ ]
    for indx in range(len(closest_precip)):
        precip = closest_precip[indx]
        if stn_total > 0 and precip > 0:
            magnitude = max(stn_total,precip) / min(stn_total,precip)
        else: magnitude = None
        closest_magnitude.append(magnitude)

    if grid_magnitude > 9.9:
        print max_diff_msg % (stn_total, grid_max, grid_diff)
        if grid_magnitude:
            if stn_total > grid_max:
                print station_gt_grid % grid_magnitude
            else: print grid_gt_station % grid_magnitude
        for indx in range(len(closest_precip)):
            precip = closest_precip[indx]
            diff = closest_diff[indx]
            print closest_msg % (stn_total, precip, diff)
            if closest_magnitude:
                magnitude = closest_magnitude[indx]
                if magnitude:
                    if stn_total > precip:
                        print station_gt_closest % magnitude
                    else: print closest_gt_station % magnitude

    elif abs(grid_diff) > 1.0:
        print max_diff_msg % (stn_total, grid_max, grid_diff)
        for indx in range(len(closest_precip)):
            precip = closest_precip[indx]
            diff = closest_diff[indx]
            print closest_msg % (stn_total, precip, diff)

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
                  default=7)
parser.add_option('-g', action='store', type='float', dest='grid_offset',
                  default=0.05)
parser.add_option('-m', action='store', type='int', dest='missing_threshold',
                  default=1)
parser.add_option('-n', action='store_true', dest='notify_stations',
                  default=False)
parser.add_option('-p', action='store', type='int', dest='padding',
                  default=6)
parser.add_option('-s', action='store', type='int', dest='start_hour',
                  default=8)
parser.add_option('-t', action='store_true', dest='track_missing',
                  default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

separator = "*" * 72
header = "\n%s\n%%(name)s (%%(sid)s)\n%s\n" % (separator, separator)

station_email_sent = 'Email sent to : %s'
sensor = 'pcpn'

DATA_CACHE = { 'year' : -32768, 'grid_sid' : None, 'stn_sid' : None }

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
loggable = not debug
missing_threshold = options.missing_threshold
if ',' in options.networks:
    networks = tuple(options.networks.split(','))
else: networks = networks
padding = options.padding
notify_stations = options.notify_stations
verbose = options.verbose
smtp_host = options.smtp_host
start_hour = options.start_hour
test_run = options.test_run
track_missing = options.track_missing

metadata = ['sid','name','ucanid','active','network','lat','lon',
            'first_hour','last_report']

if options.county is not None: metadata.append('county')
if options.state is not None: metadata.append('state')

factory = ObsnetDataFactory(options)
stations = factory.argsToStationData((), options, tuple(metadata))

num_days = (end_date - start_date).days + 1
date_str = start_date.strftime('%Y-%m-%d')
if num_days == 1: print '1 day', date_str
else: print num_days, 'days', date_str, 'thru', end_date.strftime('%Y-%m-%d')

# filter annoying numpy warnings
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")

# create mail servers to handle the different types of email messages
#text_mailer = SmtpMailer(CONFIG.services.email.smtp_host)

detector = PrecipErrorDetector(precipValidationTree, start_hour, end_hour,
                               padding, missing_threshold, grid_offset,
                               networks, notify_stations, track_missing,
                               verbose, test_run, debug)

# remove any lingering log files from previous runs for these dates
if loggable:
    date = start_date
    while date <= end_date:
        log_filepath = detector.logFilePath(date)
        if os.path.exists(log_filepath): os.remove(log_filepath)
        date += ONE_DAY

# only start the station mailer if we are going to use it
if notify_stations: detector.initStationMailer(smtp_host)

for station in stations:
    date = start_date
    while date <= end_date:
        try:
            detected = detector(date, station)
        except Exception as e:
            xtype, formatted, details = captureLastException()
            print "\n\nCaught", xtype, "excetpion for station on", date
            print station
            print ''.join(formatted)
            print ''.join(details)
        date += ONE_DAY
# stop the station mailer daemon
if notify_stations: detector.stopStationMailer()

# create the preface for the summary email
if end_date is None or end_date == start_date:
    date_str = 'on %s' % start_date.strftime('%B %d, %Y')
else:
    date_str = 'from %s to %s' % (start_date.strftime('%B %d, %Y'),
                                  end_date.strftime('%B %d, %Y'))
if detector.summary_by_station:
    preface = 'Stations with precip sensor issues %s' % date_str
    subject = 'Potential precip sensor errors detected.'
else:
    preface = 'No precip sensor issues detected %s' % date_str
    subject = 'No precip sensor issues detected.'

# always send the summary email to someone
email_msg = detector.sendSummaryEmail(smtp_host, preface, subject)
if debug: print email_msg

# turn annoying numpy warnings back on
warnings.resetwarnings()


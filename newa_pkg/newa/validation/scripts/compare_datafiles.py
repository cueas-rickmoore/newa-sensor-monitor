#! /Volumes/projects/venvs/newa/bin/python

import os

from rccpy.timeseries.data import TimeSeries
from rccpy.utils.timeutils import lastDayOfMonth

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from rccpy.config import WORKING_DIR

DATASET_NAMES = ('pcpn.date', 'pcpn.value', 'temp.date', 'temp.value')
OLD_DATASET_NAMES = ('pcpn','temp')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getTimeSpanFromArgs(args):
    if len(args) < 2: return None, None

    start_year = int(args[0])
    start_month = int(args[1])

    if len(args) == 2:
        # find all hours in a month
        start_time = (start_year, start_month, 1, 1)
        end_time = (start_year, start_month,
                    lastDayOfMonth(start_year,start_month), 24)

    elif len(args) == 3:
        # find hours in a day
        day = int(args[2])
        start_time = (start_year, start_month, day, 1)
        end_time = (start_year, start_month, day, 24)

    elif len(args) == 4:
        if len(args[2]) == 4:
            # all hours in a span of months
            start_time = (start_year, start_month, 1, 1)
            end_year = int(args[2])
            end_month = int(args[3])
            end_time = (end_year, end_month,
                        lastDayOfMonth(end_year,end_month), 24)
        else:
            # one single hour
            start_time = (start_year, start_month, int(args[2]), int(args[3]))
            end_time = start_time

    elif len(args) == 5:
        # span of hours in a single day
        day = int(args[2])
        start_time = (start_year, start_month, day, int(args[3]))
        end_time = (start_year, start_month, day, int(args[4]))

    elif len(args) == 6:
        # span of multiple full days
        start_time = (start_year, start_month, int(args[2]), 1)
        end_time = (int(args[3]), int(args[4]), int(args[5]), 24)

    elif len(args) == 8:
        # span of multiple days
        start_time = (start_year, start_month, int(args[2]), int(args[3]))
        end_time = (int(args[4]), int(args[5]), int(args[6]), int(args[7]))

    else:
        errmsg = 'Unable to determine date range from command line arguments'
        raise ValueError, errmsg

    return start_time, end_time

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('--ext', action='store', type='string', dest='extension',
                  default='.tsv')
parser.add_option('-o', action='store', type='string', dest='output_dir',
                  default=None)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=WORKING_DIR)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# get list of datasets from input arguments
first_file = args[0]
first_dataset = args[1]
second_file = args[2]
second_dataset = args[3]

file_extension = options.extension
if not file_extension.startswith('.'): file_extension.insert(0, '.')

# get time span from input arguments
start_time, end_time = getTimeSpanFromArgs(args[4:])
print 'time span', start_time, end_time

# set local variables from options
debug = options.debug

# create a factory, then use it to get the list of stations
factory = ObsnetDataFactory(options)

# get a data manager for first file
filepath = '%s.h5' % first_file
filepath = os.path.join(factory.config.working_dir,'%s.h5' % first_file)
manager = factory.getStationFileManager(filepath, 'r')
# get the first dataset
attrs, data = manager.getData(first_dataset, True)
# convert to a time series dataset and get it's iterator
time_series = TimeSeries(first_dataset, data, None, False, '-', **attrs)
start_index, end_index = time_series.getIndexes(start_time, end_time)
# get the subset
first_data = time_series.getIntervalData(start_index, end_index)
first_dates = time_series.getDates(start_time, end_time)
manager.closeFile()

# get a data manager for second file
filepath = os.path.join(factory.config.working_dir,'%s.h5' % second_file)
manager = factory.getStationFileManager(filepath, 'r')
# get the first dataset
attrs, data = manager.getData(second_dataset, True)
# convert to a time series dataset and get it's iterator
time_series = TimeSeries(second_dataset, None, False, '-', **attrs)
start_index, end_index = time_series.getIndexes(start_time, end_time)
# get the data subset
second_data = time_series.getIntervalData(start_index, end_index)
second_dates = time_series.getDates(start_time, end_time)
manager.closeFile()

filename = '%s_%s' % (first_file, first_dataset.replace('.','_'))
filename += '_%s_%s' % (second_file, second_dataset.replace('.','_'))
filename += file_extension

if options.output_dir is not None:
    output_dir = os.path.normpath(options.output_dir)
else:
    output_dir = factory.config.working_dir

output_file = open(os.path.join(output_dir, filename), 'wt')

print 'first', len(first_data), len(first_dates)
print 'second', len(second_data), len(second_dates)

for indx in range(len(first_data)):
    line = '%s\t%s\t%s\t%s' % (str(first_dates[indx]), str(first_data[indx]),
                               str(second_data[indx]), str(second_dates[indx]))
    output_file.write('%s\n' % line)
output_file.close()


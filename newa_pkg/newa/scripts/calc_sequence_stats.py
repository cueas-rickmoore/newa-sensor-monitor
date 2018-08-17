#! /Users/rem63/venvs/nrcc_prod/bin/python

import os, sys

from rccpy.hdf5.manager import HDF5DataFileManager
from rccpy.analysis.stats import emptyStatsDataset, newStatsRecord
from rccpy.timeseries.data import TimeSeries
from rccpy.utils.options import stringToTuple
from rccpy.utils.exceptutils import reportLastException

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

APP = os.path.split(sys.argv[0])[1]

from newa.config import config
WORKING_DIR = config.working_dir
MIN_RUN_LENGTHS = config.sequences.min_run_lengths

from newa.scripts.factory import MONTHS

from newa.datasets import CONTENT_TYPES, DESCRIPTIONS

DATA_TYPES = { 'pcpn' : float, 'srad' : float }

SEQ_COUNT = '%smin count = %d ... max count = %d ... mean count = %d'
SEQ_COVERAGE = '%stotal runs found = %s'
SEQ_STATS = '%smedian count = %d ... count std deviation = %d'
SEQUENCE_FILTERS = {
        'default' : ( ('x==x', '', 'identical values', str),
                      ('missing', '', 'missing values', 'missing'), ),
        'lwet' : ( ('x==0', 'if run[0] == 0', 'leaf wetness == 0', '0'),
                   ('0<X<60', 'if (run[0] > 0 and run[0] < 60)', '0 < leaf wetness < 60', lambda x:'%d' % x),
                   ('x==60', 'if run[0] == 60', 'leaf wetness == 60', '60'),
                   ('missing', '', 'missing values for leaf wetness', 'missing'), ),
        'pcpn' : ( ('x==0', 'if run[0] == 0', 'precipitation == 0', '0'),
                   ('x>0', 'if run[0] > 0', 'precipitation > 0', lambda x:('%5.2f' % x).strip()),
                   ('missing', '', 'missing precipitation values', 'missing'), ),
        'rhum' : ( ('0<x<100', 'if (run[0] > 0 and run[0] < 100)', '0 < humidity < 100', lambda x:'%d' % x),
                   ('x==100', 'if run[0] == 100', 'humidity == 100', '100'),
                   ('missing', '', 'missing values', 'missing'), ),
        'srad' : ( ('x==0', 'if run[0] == 0', 'surface radiation == 0', '0'),
                   ('x>0', 'if run[0] > 0', 'surface radiation > 0', lambda x:('%5.2f' % x).strip()),
                   ('missing', '', 'missing surface radiation values', 'missing'), ),
        'temp' : ( ('x==x', '', 'identical temperature values', lambda x:'%d' % x),
                   ('missing', '', 'missing temperature values', 'missing'), ),
        'wdir' : ( ('x==x', '', 'identical wind directions', lambda x:'%d' % x),
                   ('missing', '', 'missing wind directions values', 'missing'), ),
        'wspd' : ( ('x<5', 'if run[0] < 5', 'wind speed < 5', lambda x:'%d' % x),
                   ('5<=x<10', 'if run[0] >= 5 and run[0] < 10', '5 <= wind speed < 10', lambda x:'%d' % x),
                   ('x>=10', 'if run[0] >= 10', 'wind speed >= 10', lambda x:'%d' % x),
                   ('missing', '', 'missing wind speed values', 'missing'), ),
        'zero' : ( ('x<0', 'if run[0] < 0', 'value < 0', str),
                   ('x==0', 'if run[0] == 0', 'value == 0', '0'),
                   ('x>0', 'if run[0] > 0', 'value > 0', str),
                   ('missing', '', 'missing values', 'missing'), ),
        }
SEQUENCE_FILTERS['st4i'] = SEQUENCE_FILTERS['temp']
SEQUENCE_FILTERS['st8i'] = SEQUENCE_FILTERS['temp']
SUPPORTED_ELEMENTS = SEQUENCE_FILTERS.keys()

TIME_SUBSETS = {
        'lwet' : { 'x==60' : ( (0,23), (9,21), (21,9) ), },
        'rhum' : { 'x==100' : ( (0,23), (9,21), (21,9) ), },
        'srad' : { 'x==0' : ( (9,21), ), 'x>0' : ( (9,21), ), },
        }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def reportStatistics(seq_log_file, stats, label1, label2, indent='    '):
    stats_indent = indent + '    '

    print '\n%s%s sequence statistics for %s' % (indent,label1,label2)
    print SEQ_COVERAGE % (stats_indent,stats['coverage'])
    print SEQ_COUNT % (stats_indent,stats['min'], stats['max'],stats['mean'])
    print SEQ_STATS % (stats_indent,stats['median'],stats['stddev'])
    if seq_log_file:
        seq_log_file.write('\n%s%s sequence statistics for %s' %
                            (indent,label1,label2))
        msg = SEQ_COVERAGE % (stats_indent,stats['coverage'])
        seq_log_file.write('\n' + msg)
        msg = SEQ_COUNT % (stats_indent,stats['min'],stats['max'],stats['mean'])
        seq_log_file.write('\n' + msg)
        msg = SEQ_STATS % (stats_indent,stats['median'],stats['stddev'])
        seq_log_file.write('\n' + msg)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def createOrUpdateGroup(stats_manager, group_name, description, create_msg,
                        attrs=None):
    # create the HDF5 group if it's not there already
    if group_name not in stats_manager.listGroups():
        # create the elements sequence group
        if attrs is None:
            attrs = { 'created' : stats_manager._timestamp(),
                      'description' : description,
                    }
        print '    creating %s group' % create_msg
        stats_manager.createGroup(group_name, attrs)
    else:
        if attrs is None:
            attrs = { 'updated' : stats_manager._timestamp(), }
        stats_manager.setGroupAttributes(group_name, **attrs)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def calcSequenceStatistics(factory, ucanid, elements, min_run_length,
                           report_missing, seq_log_file, debug):

    # get a manager for the hourly data file
    hours_manager = factory.getStationFileManager((ucanid,'hours'), 'r')

    # get a manager with update access to the historical statistics data file
    stats_manager = factory.getStatisticsFileManager(ucanid,'a')

    # limit to elements available in the network
    elems = [ elem for elem in elements if elem in SUPPORTED_ELEMENTS
              and elem in hours_manager.listGroups() ]

    for element in elems:
        data, data_attrs = hours_manager.getData('%s.value' % element, True)
        first_hour = tuple(data_attrs['first_hour'])
        last_hour = tuple(data_attrs['last_hour'])
        missing_value = data_attrs['missing']
        if 'content_type' not in  data_attrs:
            data_attrs['content_type'] = CONTENT_TYPES[element]
        # need a threshold for minimum length of runs to use for statstics
        if min_run_length is None: report_threshold = MIN_RUN_LENGTHS[element]
        else: report_threshold = min_run_length

        # find ALL sequences
        time_series = TimeSeries(element, first_hour, data, **data_attrs)
        detector = time_series.getSequenceDetector()

        # calculate statistics for filtered sequence groups
        seq_filters = SEQUENCE_FILTERS.get(element,None)
        sequences = detector(filters=seq_filters)
        num_valid = 0
        num_missing = 0
        seq_stats = detector.calcStatistics()
        for key, sequences in detector.filter_groups.items():
            if len(sequences) > 0:
                # need total number of runs above threshold
                if key == 'missing': num_missing = len(sequences)
                else: num_valid += len(sequences)

        # no runs at or above threshold ... admittedly rare, but possible for
        # stations with a very short history
        if num_valid == 0 and (num_missing == 0 or not report_missing):
            continue

        elem_descr = DESCRIPTIONS[element]
        # create the element group if it's not already there
        attrs = { 'last_hour' : last_hour,
                  'first_hour' : first_hour,
                  'min' : data_attrs['min'],
                  'max' : data_attrs['max'],
                }
        if element not in stats_manager.listGroups():
            attrs['created'] =  stats_manager._timestamp()
            attrs['description'] = elem_descr
        else:
            attrs['updated'] =  stats_manager._timestamp()
        createOrUpdateGroup(stats_manager, element, elem_descr,
                            '%s element' % element, attrs)

        # create the sequences group if it's not there already
        seq_group_name = '%s.sequences' % element
        createOrUpdateGroup(stats_manager, seq_group_name,
                            'sequence statistics for %s' % elem_descr,
                            '%s sequence statistics' % element)

        # create a stats data group for each sequnce group
        for seq_stats_key, stats in seq_stats.items():
            if seq_stats_key == 'missing' and not report_missing: continue
            if stats['coverage'] == 0: continue
            process_date = stats_manager._timestamp()

            # report sequences statistics for entire time period
            if debug:
                reportStatistics(None, stats, element, seq_stats_key)
            else:
                reportStatistics(seq_log_file, stats, element, seq_stats_key)

            # create the stats dataset
            dataset_name = '%s.%s' % (seq_group_name, seq_stats_key)
            stats_dataset = emptyStatsDataset(13,('period',3))
            # insert POR statistics into stats dataset
            stats['period'] = 'POR'
            stats_dataset[0] = newStatsRecord(process_date, stats, ('period',3))

            # sort sequences by month and report statistics
            sequences = detector.filter_groups.get(seq_stats_key, ())
            monthly_stats = detector._calcStatsByMonth(sequences)
            for indx in range(12):
                month = MONTHS[indx]
                # insert statistics for the month into stats dataset
                stats = monthly_stats[indx]
                stats['period'] = month
                stats_dataset[indx+1] = newStatsRecord(process_date, stats,
                                                       ('period',3))

                # report statistics for the month
                reportStatistics(seq_log_file,stats,dataset_name,month,' '*12)

            # replace or create the stats dataset
            if stats_manager.datasetExists(dataset_name):
                stats_manager.setDatasetAttribute(dataset_name, 'updated',
                                                  stats_manager._timestamp())
                stats_manager.replaceDataset(dataset_name, stats_dataset)
            else:
                descrip = 'sequnece statistics for %s' % seq_stats_key
                attrs = { 'created' : stats_manager._timestamp(),
                          'description' : descrip }
                stats_manager.createDataset(dataset_name, stats_dataset, attrs)

            # create a listing of all sequences above minimum run length
            if sequences:
                sequences = [ run for run in sequences
                              if run[1] > min_run_length ]
            if sequences:
                if seq_log_file:
                    detector._saveSequences(seq_log_file, sequences)
                else:
                    detector._reportSequences(sequences)

    hours_manager.closeFile()
    stats_manager.closeFile()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if __name__ == "__main__":

    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option('-c', action='store', type='int', dest='count_cutoff',
                      default=None)
    parser.add_option('-e', action='store', type='string', dest='elements',
                      default='all')
    parser.add_option('-m', action='store_true', dest='report_missing',
                      default=False)
    parser.add_option('-w', action='store', type='string', dest='working_dir',
                      default=WORKING_DIR)
    parser.add_option('-z', action='store_true', dest='debug', default=False)

    # station search criteria
    parser.add_option('--bbox', action='store', type='string', dest='bbox',
                      default=None)
    parser.add_option('--county', action='store', type='string', dest='county',
                      default=None)
    parser.add_option('--sid', action='store', type='string', dest='sid',
                      default=None)
    parser.add_option('--network', action='store', type='string',
                      dest='network', default=None)
    parser.add_option('--state', action='store', type='string', dest='state',
                      default=None)

    options, args = parser.parse_args()

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    procmsg = '\nProcessing station %d of %d : %d : %s (%s)' 
    skipmsg = '\nSkipping station %d of %d : %d : %s (%s)' 

    debug = options.debug
    if options.elements == 'all':
        elements = list(MIN_RUN_LENGTHS.keys())
    else:
        elements = list(stringToTuple(options.elements))

    factory = ObsnetDataFactory(options)
    stations = factory.argsToStationData(args, options, 'all')
    total_stations = len(stations)
    
    station_num = 0
    for station in stations:
        station_num += 1
        ucanid = station['ucanid']

        if 'id' in station:
            station['sid'] = station['id']
            del station['id']

        # hourly data file must already exist
        filepath = factory.getFilepathForUcanid(ucanid, 'hours')
        if not os.path.exists(filepath):
            print skipmsg % (station_num, total_stations, ucanid,
                             station['sid'], station['name'])
            errmsg = 'Hourly data file for station %d does not exist : %s' 
            print errmsg % (station['ucanid'], filepath)

        # open sequence log file
        if not debug:
            seq_log_filename = '%d_sequences.log' % ucanid
            seq_log_filepath = os.path.join(factory.config.working_dir,
                                            seq_log_filename)
            seq_log_file = open(seq_log_filepath, 'wt')
        else: seq_flog_file = None

        # we're going to process this station
        announce = procmsg % (station_num, total_stations, ucanid,
                              station['sid'], station['name'])
        print announce
        if seq_log_file: seq_log_file.write(announce)

        try:
            calcSequenceStatistics(factory,ucanid,elements,options.count_cutoff,
                                   options.report_missing,seq_log_file,debug)
        except:
            reportLastException(APP)
            os._exit(1)

        if seq_log_file:
            seq_log_file.close()
            msg =  'Created sequence log file for %s at %s'
            print msg % (station['name'], seq_log_filepath)
        sys.stdout.flush()
        sys.stderr.flush()


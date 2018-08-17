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

from newa.scripts.factory import MONTHS
from newa.datasets import CONTENT_TYPES, DESCRIPTIONS

SPIKE_COVERAGE = '%stotal spikes found = %d'
SPIKE_MAGNITUDE = '%smin spike = %s ... max spike = %s ... mean spike = %s'
SPIKE_STATS = '%smedian spike = %s ... std deviation = %s'

SPIKE_FILTERS = {
      'dewpt_depr' : (('x>0', 'if spike != 0', 'dew point depression spike > 0', str),),
      'rhum' : (('x>0', 'if spike != 0', 'humidity spike > 0', str),),
      'srad' : (('x>0', 'if spike != 0', 'surface radiation spike > 0', str),),
      'temp' : (('x>0', 'if spike != 0', 'temperature spike > 0', str),),
      'wdir' : (('x>0', 'if spike != 0', 'wind direction spike > 0', str),),
      'wspd' : (('x>0', 'if spike != 0', 'wind speed spike > 0', str),),
     }
SPIKE_FILTERS['st4i'] = SPIKE_FILTERS['temp']
SPIKE_FILTERS['st8i'] = SPIKE_FILTERS['temp']
SUPPORTED_ELEMENTS = SPIKE_FILTERS.keys()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def reportStatistics(spike_log_file, stats, label1, label2, indent='    '):
    stats_indent = indent + '    '

    print '\n%s%s statistics for %s' % (indent,label1,label2)
    print SPIKE_COVERAGE % (stats_indent,stats['coverage'])
    print SPIKE_MAGNITUDE % (stats_indent,stats['min'],stats['max'],stats['mean'])
    print SPIKE_STATS % (stats_indent,stats['median'],stats['stddev'])
    if spike_log_file:
        spike_log_file.write('\n%s%s statistics for %s' %
                            (indent,label1,label2))
        msg = SPIKE_COVERAGE % (stats_indent,stats['coverage'])
        spike_log_file.write('\n' + msg)
        msg = SPIKE_MAGNITUDE % (stats_indent,stats['min'],stats['max'],stats['mean'])
        spike_log_file.write('\n' + msg)
        msg = SPIKE_STATS % (stats_indent,stats['median'],stats['stddev'])
        spike_log_file.write('\n' + msg)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def createOrUpdateGroup(stats_manager, group_name, description, create_msg,
                        attrs=None):
    # create the HDF5 group if it's not there already
    if group_name not in stats_manager.listGroups():
        # create the elements spike group
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

def calcSpikeStatistics(factory, ucanid, elements, spike_log_file, debug):

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

        # find ALL spikes
        time_series = TimeSeries(element, first_hour, data, **data_attrs)
        detector = time_series.getSpikeDetector()

        # calculate statistics for filtered spike groups
        spike_filter_groups = SPIKE_FILTERS.get(element,None)
        spikes = detector(filters=spike_filter_groups)
        num_valid = 0
        num_missing = 0
        spike_stats = detector.calcStatistics()
        for _filter in detector.filters:
            spikes = detector.filter_groups[_filter[0]]
            if len(spikes) > 0: num_valid += len(spikes)

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

        # create the spikes group if it's not there already
        spike_group_name = '%s.spikes' % element
        createOrUpdateGroup(stats_manager, spike_group_name,
                            'spike statistics for %s' % elem_descr,
                            '%s spike statistics' % element)

        # create a stats data group for each sequnce group
        for stats_key, stats in spike_stats.items():
            if stats['coverage'] == 0: continue
            process_date = stats_manager._timestamp()

            # report spikes statistics for entire time period
            if debug:
                reportStatistics(None, stats, element, stats_key)
            else:
                reportStatistics(spike_log_file, stats, element, stats_key)

            # create the stats dataset
            dataset_name = '%s.%s' % (spike_group_name, stats_key)
            stats_dataset = emptyStatsDataset(13,('period',3))
            # insert POR statistics into stats dataset
            stats['period'] = 'POR'
            stats_dataset[0] = newStatsRecord(process_date, stats, ('period',3))

            # sort spikes by month and report statistics
            spikes = detector.filter_groups.get(stats_key, ())

            monthly_stats = detector._calcStatsByMonth(spikes)
            for indx in range(12):
                month = MONTHS[indx]
                # insert statistics for the month into stats dataset
                stats = monthly_stats[indx]
                stats['period'] = month
                stats_dataset[indx+1] = newStatsRecord(process_date, stats,
                                                       ('period',3))

                # report statistics for the month
                reportStatistics(spike_log_file,stats,dataset_name,month,' '*12)

            # replace or create the stats dataset
            if stats_manager.datasetExists(dataset_name):
                stats_manager.setDatasetAttribute(dataset_name, 'updated',
                                                  stats_manager._timestamp())
                stats_manager.replaceDataset(dataset_name, stats_dataset)
            else:
                descrip = 'spike statistics for %s' % stats_key
                attrs = { 'created' : stats_manager._timestamp(),
                          'description' : descrip }
                stats_manager.createDataset(dataset_name, stats_dataset, attrs)

            if spikes:
                if spike_log_file:
                    detector._saveSpikes(spike_log_file, spikes)
                else:
                    detector._reportSpikes(spikes)

    hours_manager.closeFile()
    stats_manager.closeFile()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if __name__ == "__main__":

    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option('-e', action='store', type='string', dest='elements',
                      default='all')
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
        elements = list(SPIKE_FILTERS.keys())
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

        # open spike log file
        if not debug:
            spike_log_filename = '%d_spikes.log' % ucanid
            spike_log_filepath = os.path.join(factory.config.working_dir,
                                            spike_log_filename)
            spike_log_file = open(spike_log_filepath, 'wt')
        else: spike_flog_file = None

        # we're going to process this station
        announce = procmsg % (station_num, total_stations, ucanid,
                              station['sid'], station['name'])
        print announce
        if spike_log_file: spike_log_file.write(announce)

        try:
            calcSpikeStatistics(factory,ucanid,elements,spike_log_file,debug)
        except:
            reportLastException(APP)
            os._exit(1)

        if spike_log_file:
            spike_log_file.close()
            msg =  'Created spike log file for %s at %s'
            print msg % (station['name'], spike_log_filepath)
        sys.stdout.flush()
        sys.stderr.flush()


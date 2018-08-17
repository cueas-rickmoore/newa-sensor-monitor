
import os, sys

import numpy as N

from rccpy.analysis.stats import emptyStatsDataset, newStatsRecord
from rccpy.timeseries.data import TimeSeries

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config as CONFIG
MIN_RUN_LENGTHS = CONFIG.sequences.min_run_lengths
SEQUENCE_ELEMENTS = CONFIG.sequences.filters.keys()
SPIKE_ELEMENTS = CONFIG.spikes.filters.keys()

from newa.factory import MONTHS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def reportStatistics(log_file, stats, label1, label2, stats_fmt, distrib_fmt,
                     coverage_fmt, indent='    '):
    stats_indent = indent + '    '

    print '\n%s%s statistics for %s' % (indent,label1,label2)
    print coverage_fmt % (stats_indent,stats['coverage'])
    print stats_fmt % (stats_indent,stats['min'], stats['max'],stats['mean'])
    print distrib_fmt % (stats_indent,stats['median'],stats['stddev'])
    if log_file is not None:
        log_file.write('\n%s%s statistics for %s' %
                            (indent,label1,label2))
        msg = coverage_fmt % (stats_indent,stats['coverage'])
        log_file.write('\n' + msg)
        msg = stats_fmt % (stats_indent,stats['min'],stats['max'],stats['mean'])
        log_file.write('\n' + msg)
        msg = distrib_fmt % (stats_indent,stats['median'],stats['stddev'])
        log_file.write('\n' + msg)

def createOrUpdateGroup(stats_manager, group_name, description, create_msg,
                        attrs=None):
    # create the database group if it's not there already
    if group_name not in stats_manager.listGroups():
        # create the elements extreme group
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
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def historicalExtremes(factory, ucanid, elements, debug=False):
    EXTR_COVERAGE_FMT = '%stotal hours found = %d'
    EXTR_STATS_FMT = '%smin = %s ... max = %s ... mean = %s'
    EXTR_DISTRIB_FMT = '%smedian = %s ... std deviation = %s'

    # get a manager for the hourly data file
    hours_manager = factory.getFileManager((ucanid,'hours'), 'r')
    if elements == 'all': elems = hours_manager.listGroups()
    else: # limit to elements available in the network
        elems = [ elem for elem in elements
                  if elem in hours_manager.listGroups() ]

    # get a manager with update access to the historical statistics data file
    stats_manager = factory.getFileManager((ucanid,'statistics'),'a')

    # loop thru the list of elements
    for element in elems:
        print ucanid, element
        dataset_name = '%s.value' % element
        element_config = CONFIG.elements[element].asDict()
        data, data_attrs = hours_manager.getSerialData(dataset_name, True)
        frequency = data_attrs['frequency']
        first_time = 'first_%s' % frequency
        last_time = 'last_%s' % frequency
        base_time = tuple(data_attrs[first_time])
        end_time = tuple(data_attrs[last_time])
        missing_value = data_attrs['missing']
        if 'content_type' not in  data_attrs:
            data_attrs['content_type'] = element_config['value_type']
        time_series = TimeSeries(element, base_time, data, **data_attrs)
        month_array = N.array([ date[1] for date in 
                                time_series.getDates(date_format='tuple') ],
                              dtype=int)

        elem_descr = element_config['description']
        # create the element group if it's not already there
        attrs = { first_time : base_time,
                  last_time : end_time,
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

        # create the stats dataset and add period of record stats
        dataset_name = '%s.extremes' % element
        time_stamp = stats_manager._timestamp()
        stats_dataset = emptyStatsDataset(13,('period',3))
        stats = time_series.calcDataStatistics()
        stats['period'] = 'POR'
        stats_dataset[0] = newStatsRecord(time_stamp, stats, ('period',3))
        reportStatistics(None, stats, dataset_name, 'POR', EXTR_STATS_FMT,
                         EXTR_DISTRIB_FMT, EXTR_COVERAGE_FMT)

        # find extremes for each month and insert into statistics dataset
        for month in range(1,13):
            indexes = N.where(month_array==month)
            stats = time_series._calcArrayStatistics(data[indexes])
            stats['period'] = Month = MONTHS[month-1]
            stats_dataset[month] = newStatsRecord(time_stamp, stats,
                                                   ('period',3))
            reportStatistics(None, stats, dataset_name, Month, EXTR_STATS_FMT,
                             EXTR_DISTRIB_FMT, EXTR_COVERAGE_FMT,' '*8)

        # replace or create the stats dataset
        if stats_manager.datasetExists(dataset_name):
            stats_manager.setDatasetAttribute(dataset_name, 'updated',
                                              stats_manager._timestamp())
            stats_manager.replaceDataset(dataset_name, stats_dataset)
        else:
            descrip = 'extreme statistics for %s' % element
            attrs = { 'created' : stats_manager._timestamp(),
                      'description' : descrip,
                      first_time : base_time,
                      last_time : end_time,
                    }
            stats_manager.createDataset(dataset_name, stats_dataset, attrs)

    hours_manager.closeFile()
    stats_manager.closeFile()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def historicalSequences(factory, ucanid, elements, report_missing, log_file,
                        min_run_length=None, debug=False):
    SEQ_COVERAGE_FMT = '%stotal runs found = %s'
    SEQ_STATS_FMT = '%smin count = %d ... max count = %d ... mean count = %d'
    SEQ_DISTRIB_FMT = '%smedian count = %d ... count std deviation = %d'

    # get a manager for the hourly data file
    hours_manager = factory.getFileManager((ucanid,'hours'), 'r')

    # get a manager with update access to the historical statistics data file
    stats_manager = factory.getFileManager((ucanid,'statistics'),'a')

    # limit to elements in the sequence set
    data_groups = hours_manager.listGroups()
    if elements == 'all':
        elems = [ elem for elem in data_groups if elem in SEQUENCE_ELEMENTS ]
    else:
        elems = [ elem for elem in elements
                       if elem in SEQUENCE_ELEMENTS and elem in data_groups ]

    for element in elems:
        # need a threshold for minimum length of runs to use for statstics
        if min_run_length is None: report_threshold = MIN_RUN_LENGTHS[element]
        else: report_threshold = min_run_length

        element_config = CONFIG.elements[element].asDict()

        dataset_name = '%s.value' % element
        data, data_attrs = hours_manager.getSerialData(dataset_name, True)
        frequency = data_attrs['frequency']
        first_time = 'first_%s' % frequency
        last_time = 'last_%s' % frequency
        base_time = tuple(data_attrs[first_time])
        end_time = tuple(data_attrs[last_time])
        missing_value = data_attrs['missing']
        if 'content_type' not in  data_attrs:
            data_attrs['content_type'] = element_config['value_type']

        # find ALL sequences
        time_series = TimeSeries(element, base_time, data, **data_attrs)
        detector = time_series.getSequenceDetector()

        # calculate statistics for filtered sequence groups
        seq_filters = CONFIG.sequences.filters[element]
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

        elem_descr = element_config['description']
        # create the element group if it's not already there
        attrs = { first_time : base_time,
                  last_time : end_time,
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
                reportStatistics(None, stats, element, seq_stats_key,
                                 SEQ_STATS_FMT, SEQ_DISTRIB_FMT,
                                 SEQ_COVERAGE_FMT)
            else:
                reportStatistics(log_file, stats, element, seq_stats_key, 
                                 SEQ_STATS_FMT, SEQ_DISTRIB_FMT,
                                 SEQ_COVERAGE_FMT)

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
                reportStatistics(log_file, stats, dataset_name, month,
                                 SEQ_STATS_FMT, SEQ_DISTRIB_FMT,
                                 SEQ_COVERAGE_FMT, ' '*12)

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
                if log_file: detector._saveSequences(log_file, sequences)
                else: detector._reportSequences(sequences)

    hours_manager.closeFile()
    stats_manager.closeFile()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def historicalSpikes(factory, ucanid, elements, log_file, debug):
    SPIKE_COVERAGE_FMT = '%stotal spikes found = %d'
    SPIKE_STATS_FMT = '%smin spike = %s ... max spike = %s ... mean spike = %s'
    SPIKE_DISTRIB_FMT = '%smedian spike = %s ... std deviation = %s'

    # get a manager for the hourly data file
    hours_manager = factory.getFileManager((ucanid,'hours'), 'r')

    # get a manager with update access to the historical statistics data file
    stats_manager = factory.getFileManager((ucanid,'statistics'), 'a')

    # limit to elements in the spike set
    data_groups = hours_manager.listGroups()
    if elements == 'all':
        elems = [ elem for elem in data_groups if elem in SPIKE_ELEMENTS ]
    else:
        elems = [ elem for elem in elements
                       if elem in SPIKE_ELEMENTS and elem in data_groups ]

    for element in elems:
        element_config = CONFIG.elements[element].asDict()

        dataset_name = '%s.value' % element
        data, data_attrs = hours_manager.getSerialData(dataset_name, True)
        frequency = data_attrs['frequency']
        first_time = 'first_%s' % frequency
        last_time = 'last_%s' % frequency
        base_time = tuple(data_attrs[first_time])
        end_time = tuple(data_attrs[last_time])
        missing_value = data_attrs['missing']
        if 'content_type' not in  data_attrs:
            data_attrs['content_type'] = element_config['value_type']
        # need a threshold for minimum length of runs to use for statstics

        # find ALL spikes
        time_series = TimeSeries(element, base_time, data, **data_attrs)
        detector = time_series.getSpikeDetector()

        # calculate statistics for filtered spike groups
        spike_filter_groups = CONFIG.spikes.filters[element]
        spikes = detector(filters=spike_filter_groups)
        num_valid = 0
        num_missing = 0
        spike_stats = detector.calcStatistics()
        for _filter in detector.filters:
            spikes = detector.filter_groups[_filter[0]]
            if len(spikes) > 0: num_valid += len(spikes)

        elem_descr = element_config['description']
        # create the element group if it's not already there
        attrs = { first_time : base_time,
                  last_time : end_time,
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
                reportStatistics(None, stats, element, stats_key,
                                 SPIKE_STATS_FMT, SPIKE_DISTRIB_FMT,
                                 SPIKE_COVERAGE_FMT)
            else:
                reportStatistics(log_file, stats, element, stats_key,
                                 SPIKE_STATS_FMT, SPIKE_DISTRIB_FMT,
                                 SPIKE_COVERAGE_FMT)

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
                reportStatistics(log_file, stats, dataset_name, month, 
                                 SPIKE_STATS_FMT, SPIKE_DISTRIB_FMT,
                                 SPIKE_COVERAGE_FMT,' '*12)

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
                if log_file: detector._saveSpikes(log_file, spikes)
                else: detector._reportSpikes(spikes)

    hours_manager.closeFile()
    stats_manager.closeFile()


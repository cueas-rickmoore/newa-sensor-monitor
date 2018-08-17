#! /Volumes/projects/venvs/newa/bin/python

import os, sys

from datetime import datetime
from dateutil.relativedelta import relativedelta

import numpy as N

from rccpy.stations.ucan import UcanConnection, UcanUndefinedElementError
from rccpy.stations.ucan import UcanInvalidElementError, UcanInvalidTsvarError

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config as CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-a', action='store', type='int', dest='max_attempts',
                  default=5)
parser.add_option('-u', action='store_false', dest='update', default=True)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

test_run = options.test
if test_run:
    debug = True
    update = False
else:
    debug = options.debug
    update = options.update
max_attempts = options.max_attempts

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

factory = ObsnetDataFactory(options)
index_manager = factory.getFileManager('index', mode='r')
index_datasets, datasets_attrs = index_manager.getData('datasets',True)
index_ucanids = index_manager.getData('ucanid')
num_stations = len(index_ucanids)
networks = index_manager.getData('network')
sids = index_manager.getData('sid')
index_manager.closeFile()
del index_manager

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

num_changed = 0
ucanid_list = tuple(index_ucanids)
attempt = 1
do_over = [ ]

while len(ucanid_list) > 0 and attempt <= max_attempts:
    print '\nUpdate attempt # %d\n' % attempt

    for ucanid in ucanid_list:
        station_index = N.where(index_ucanids == ucanid)[0][0]
        network = networks[station_index]
        # set up simple station dict for use in UCAN calls
        station = { 'ucanid':ucanid, 'network': network,
                'sid':sids[station_index] }
        if debug:
            print 'processing %(network)s station %(ucanid)d : %(sid)s' % station
        connection = UcanConnection(None, 2)

        tsvar = None
        valid_datasets = [ ]

        for element in CONFIG.networks[network].datasets:
            if tsvar is not None:
                ts_var.release()
                tsvar = None
            try:
                tsvar = connection.getTsVar(station, element)
            except (UcanInvalidElementError, UcanInvalidTsvarError,
                    UcanUndefinedElementError) as e:
                if debug:
                    print '   ', element, e.__class__.__name__ 
                    print '       ', e
            except Exception as e:
                class_name = e.__class__.__name__
                if class_name == 'UnauthorizedAccess':
                    do_over.append(ucanid)
                    print '   ', e
                    print '    skipping station, will try again'
                    break
                else:
                    print '   ', element, e.__class__.__name__ 
                    print '       ', e
                    if hasattr(e, 'args'): print '        ', e.args
            else:
                valid_datasets.append(element)

        if tsvar is not None:
            ts_var.release()
            tsvar = None

        if len(valid_datasets) > 0 and ucanid not in do_over:
            old_datasets = index_datasets[station_index].split(',')
            # get symmetric difference of the two sets of datasets
            # i.e. datasets in either set but not both sets
            sym_diff = set(old_datasets) ^ set(valid_datasets)
            if len(sym_diff) > 0:
                elem_string = ','.join(valid_datasets)
                msg = '    %s datasets = %s'
                if not debug:
                    msg = '%(network)s : station %(ucanid)d : %(sid)s : datasets changed'
                    print msg % station
                print msg % ('old', index_datasets[station_index])
                print msg % ('new', elem_string)
                index_datasets[station_index] = elem_string
                num_changed += 1

    ucanid_list = tuple(do_over)
    do_over = [ ]
    attempt += 1

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

num_left = len(ucanid_list)
attempt -= 1
if num_left == 0:
    print '\nCompleted discovery after %d attempts.' % attempt
    if num_changed > 0:
        factory.backupIndexFile()
        msg = 'Differences were discovered in %d of %d stations.'
        print msg % (num_changed, num_stations)
        if update:
            index_manager = factory.getFileManager('index', mode='a')
            index_manager.replaceDataset('datasets', index_datasets,
                                         datasets_attrs)
            index_manager.closeFile()
            print 'The database has been updated.' 
        else:
            print 'The database was not updated during this test run.' 
    else:
        print 'No changes were discovered in the element list of any station.'
        print 'The database was not updated.' 
else:
    print '\n******************************************************************'
    msg = '* %d unresolved access isssues after %d attempts'
    print msg % (num_left, attempt)
    print '* Database update was aborted'
    print '******************************************************************'


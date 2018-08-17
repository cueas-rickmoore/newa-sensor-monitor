#! /Volumes/projects/venvs/newa/bin/python

import os, sys
print os.__file__
import numpy as N

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.database.index import INDEX

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-k', action='store', type='string', dest='index_key',
                  default='ucanid')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

master_index_key = options.index_key
test_run = options.test
if test_run: debug = True
else: debug = options.debug

dump_filepath = os.path.normpath(args[0])

# look for an input list of columns to update
if len(args) > 1:
    update_datasets = { }
    for arg in args[1:]:
        # the arg may be a mapping of the dataset name used in the dump file
        # to the dataset name expected by the index file
        if ':' in arg:
            dump_key, index_key = arg.split(':')
            update_datasets[dump_key] = index_key
        else: update_datasets[arg] = arg
# the list of columns to update was bnot on the command line
else: update_datasets = None

# open the index dataset and get the current set of keys
factory = ObsnetDataFactory(options)
index_manager = factory.getFileManager('index','r')
existing_index_keys = list(index_manager.listDatasets())
if debug: print '\nexisting keys', existing_index_keys

# get the master index dataset
index_key_dataset,index_key_attrs = index_manager.getData(master_index_key,True)
index_key_dataset_size = len(index_key_dataset)

# open the dump file and read the first line
dump_file = open(dump_filepath, 'r')
update_dict = eval(dump_file.readline())
update_index = N.where(index_key_dataset==update_dict[master_index_key])

# if the list of datasets to update was not passed on the command line
# we need to create one from the list of keys in the dump file
if update_datasets is None:
    update_datasets = { }
    for key in update_dict.keys():
        update_datasets[key] = key
if debug:
    print '\ndump keys', update_datasets
    print ' '

# retrieve the existing datasets from the index file
new_datasets = [ ]
index_datasets = { }
index_datasets_attrs = { }
for dump_key, index_key in update_datasets.items():
    if index_key != master_index_key:
        if index_key in existing_index_keys:
            dataset, attrs = index_manager.getData(index_key, True)
            if 'description' in attrs: del attrs['description']
            if 'missing' in attrs: del attrs['missing']
            if 'units' in attrs: del attrs['units']
        else:
            column = INDEX[index_key]
            if debug:
                msg = "creating '%s' type array for %s" 
                print msg % (column.dtype, index_key)
            dataset = N.empty(index_key_dataset_size, column.dtype)
            dataset.fill(column.missing)
            attrs = { }

        attrs['description'] = column.description
        if column.missing: attrs['missing'] = column.missing
        if column.units: attrs['units'] = units
        new_datasets.append(index_key)
        # update the index dataset with the value from the update_dict
        dataset[update_index] = update_dict[dump_key]
        index_datasets[index_key] = dataset
        index_datasets_attrs[index_key] = attrs
# done with the index file for now
index_manager.closeFile()

if debug: print ' '
# continue reading the file until the end
line = dump_file.readline()
while line:
    update_dict = eval(line.strip())
    update_index = N.where(index_key_dataset==update_dict[master_index_key])
    if debug:
        print 'processing %d : %s' % (update_index[0][0],
                                      update_dict[master_index_key])
    # update each index dataset with the value from the update_dict
    for dump_key, index_key in update_datasets.items():
        if index_key != master_index_key:
            # remember that the values in index_datasets contain the tuple
            # (dataset, attrs) ... so the array is at index 0 into that tuple
            index_datasets[index_key][update_index] = update_dict[dump_key]
    # read the next line
    line = dump_file.readline()
# done with dump file
dump_file.close()

if test_run:
    print ' '
    msg = '%s %s, len %d, type %s'
    for index_key, dataset in index_datasets.items():
        if index_key in existing_index_keys:
            print msg % ('replace', index_key, len(dataset), dataset.dtype)
        else: print msg % ('create', index_key, len(dataset), dataset.dtype)
        print dataset[215:]
        print ' '
else:
    factory.backupIndexFile()
    index_manager = factory.getFileManager('index','a')
    for index_key, dataset in index_datasets.items():
        attrs = index_datasets_attrs[index_key]
        if index_key in existing_index_keys:
            index_manager.replaceDataset(index_key, dataset, attrs)
        else: index_manager.createDataset(index_key, dataset, attrs)
    index_manager.closeFile()


#! /Volumes/projects/venvs/newa/bin/python

import numpy as N

from newa.factory import ObsnetDataFactory
from newa.database.index import getDictTemplate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-d', action='store', type='string', dest='dataset_names',
                  default=None)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-y', action='store_true', dest='test_run', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)
options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

factory = ObsnetDataFactory(options)
manager = factory.getFileManager('index','r')

dataset_name = args[0]
value = args[1]
if dataset_name == 'ucanid':
   value = N.int64(value)

debug = options.debug
test_run = options.test_run
verbose = debug or test_run

if options.dataset_names is not None:
    dataset_names = options.dataset_names.split(',')
else: dataset_names = manager.listDatasets()

# get all stations currently in the index file
data = manager.getData(dataset_name)
indx = N.where(data == value)[0][0]

station = { }
for name in dataset_names:
    station[name] = manager.getDataset(name)[indx]
print getDictTemplate(station) % station


#! /Volumes/projects/venvs/newa/bin/python

import os, sys

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('--network', action='store', type='string', dest='network',
                  default=None)
parser.add_option('--state', action='store', type='string', dest='state',
                  default=None)

parser.add_option('-s', action='store', type='string', dest='sort_by',
                  default='name')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

filepath = os.path.normpath(args[0])
if os.path.isfile(filename):
    manager_1 = factory.getFileManager(filepath, 'r')
else:
    dirpath = factory.getDirectoryPath('working')
    filepath = os.path.join(working_dir, filepath)
    manager_1 = factory.getFileManager(filepath_1, 'r')
filename_1 = os.path.split(manager_1.getFilePath())[1]

if len(args) > 1:
    filepath = os.path.normpath(args[0])
    if os.path.isfile(filepath):
        manager_2 = factory.getFileManager(filepath, 'r')
    else:
        dirpath = factory.getDirectoryPath('working')
        filepath = os.path.join(working_dir, filepath)
        manager_2 = factory.getFileManager(filepath, 'r')
else:
    manager_2 = factory.getFileManager('index','r')
filename_2 = os.path.split(manager_2.getFilePath())[1]

column_names_1 = manager_1.listDatasets()
num_cols_1 = len(column_names_1)
print filename_1, 'has', num_cols_1, 'columns'
column_names_1 = column_names_1.sort()

column_names_2 = manager_2.listDatasets()
num_cols_2 = len(column_names_2)
print filename_2, 'has', num_cols_2 , 'columns'
column_names_2 = column_names_2.sort()

if column_names_1 != column_names_2:
    set_1 = set(column_names_1)
    set_2 = set(column_names_2)
    
    print 


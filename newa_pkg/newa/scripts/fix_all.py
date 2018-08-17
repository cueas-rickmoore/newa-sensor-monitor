#! /Users/rem63/venvs/nrcc_prod/bin/python

import os, sys

from newa.manager import ObsnetDataFileManager

from newa.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-z', action='store_true', dest='debug', default=False,
                  help='show all available debug output')

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

factory = ObsnetDataFactory(options)
dirpath = factory.getDirectoryPath('hours')
for filename in os.listdir(dirpath):
    if filename.endswith('.h5'):
        print 'fixing', filename
        manager = ObsnetDataFileManager(os.path.join(dirpath,filename),mode='a')
        if 'daily_pcpn' in manager.listGroups():
            manager.setDatasetAttribute('daily_pcpn.value','missing',-32768)
        manager.closeFile()


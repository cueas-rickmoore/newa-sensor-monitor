#! /Volumes/projects/venvs/newa/bin/python

import os, sys
from datetime import datetime

from newa.factory import ObsnetDataFactory
from newa.database.utils import downloadMetadata

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config as CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# define input options

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-s', action='store', type='string', dest='states',
                  default=None)
parser.add_option('-t', action='store_true', dest='tsv', default=False)
parser.add_option('-u', action='store', type='string', dest='root_url',
                  default=None)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# interpret input options
debug = options.debug
if options.tsv: file_format = 'tsv'
else: file_format = 'dump'


# root URL for metadata download file
root_url = options.root_url
if root_url is None:
    root_url = CONFIG.metadata.download.root_url
if not root_url.endswith('/'): root_url += '/'

# list of states to update
states = options.states
if states is None:
    states = CONFIG.metadata.states
else:
    if ',' in states:
        states = tuple([state.strip().upper() for state in states.split(',')])
    elif len(states) == 2:
        states = (states.upper(),)
    else:
        errmsg = 'Value of input option -s is invalid : %s' % states
        raise ValueError, errmsg

# creat a factory instance and get directory/file paths
factory = ObsnetDataFactory(options)
index_dirpath = factory.getDirectoryPath('index')
download_dirpath = os.path.join(index_dirpath, 'downloads')
if not os.path.exists(download_dirpath): os.makedirs(download_dirpath)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

date_str = datetime.now().strftime('%Y%m%d')

for state in states:
    filepath = downloadMetadata(root_url, state, date_str, file_format,
                                download_dirpath, debug=debug)
    if filepath is not None:
        print 'saved metadata for %s in %s' % (state, filepath)


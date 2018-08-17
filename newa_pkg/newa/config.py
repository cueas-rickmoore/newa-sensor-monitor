
import os
import platform

from rccpy.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize the configuration
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

config = ConfigObject('config', None, 'metadata')
#config.bad_stations = ('kmqe','knzw',)
config.dev_station_ids = [ 60,61,91,94,95,17832,18343,26861,31795,33631,
                    33644,33645,33686,33688,33689,33690,33691 ]

config.backup_date_format = '%y%m%d.%H%M%S'
config.metadata.column_map = { 'Active' : 'active', 'Contact Name' : 'contact',
       'Contact Email' : 'email', 'Contact Phone' : 'phone',
       'Backup Contact Email' :'bemail', 'Backup Contact Name' : 'bcontact',
       'Instrument Brand' : 'sensor', 'Instrument Connection' : 'uplink',
       'Network' : 'network', 'Station ID' : 'sid', 'Station Name' : 'name' }
config.metadata.download = {
                'dest_tmpl' : '%(date)s_Metadata_Download_%(state)s',
                'root_url' : 'http://squall.nrcc.cornell.edu/~keith/NEWA_Export',
                'source_tmpl' : '%(state)s_Metadata_Export.tsv',
                'tab_labels' : ( 'Station ID', 'Station Name',
                                 'Contact Name', 'Contact Phone', 'Contact Email',
                                 'Backup Contact Name', 'Backup Contact Email',
                                 'Instrument Brand', 'Instrument Connection',
                                 'Active', 'Network'),
                }
config.metadata.states = ('CT','MA','MN','NC','NH','NJ','NY','PA','VT','Other')
config.metadata.mutable = ('active', 'bcontact', 'bemail', 'contact', 'email',
                           'name', 'network', 'sensor', 'uplink')
config.metadata.nullable = ('bcontact', 'bemail') #,'sid') ?

config.search_keys = ('bbox','county','name','network','sid','state','ucanid')
if 'windows' in platform.system().lower():
    config.working_dir = 'C:\\\\Work\\NRCC\\data\\newa'
else:
    config.working_dir = '/Volumes/data/app_data/newa/prod'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# import topic-specific configuration files
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa._config.datasets import datasets
config.elements = datasets
config.addChild(datasets)

from newa._config.networks import networks
config.addChild(networks)

from newa._config.services import services
config.addChild(services)

from newa._config.statistics import extremes, sequences, spikes
config.addChild(extremes)
config.addChild(sequences)
config.addChild(spikes)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# update with parameters from external configuration file
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if 'NEWA_CONFIG_PY' in os.environ:
    cfgfile = open(os.environ['NEWA_CONFIG_PY'],'r')
    overrides = eval(cfgfile.read())
    cfgfile.close()
    config.update(overrides)
if 'log_dirpath' not in config.keys():
    config.log_dirpath = os.path.join(config.working_dir, 'logs')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# derive configuration parameters that are dependent on the value of others
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

raw_datasets = [ ]
generator_sources = [ ]
generator_targets = { }
for key, parameters in config.datasets.items():
    if 'dependencies' in parameters:
        generator_targets[key] = parameters['dependencies']
        generator_sources.extend([name for name in parameters['dependencies']
                                       if name not in generator_sources])
    else: raw_datasets.append(key)
config.raw_datasets = tuple(raw_datasets)
del raw_datasets

generator_sources.sort()
config.generator = { 'targets' : generator_targets,
                     'sources' : tuple(generator_sources) }
del generator_targets, generator_sources

config.sequences.datasets = config.sequences.filters.keys()
config.spikes.datasets = config.spikes.filters.keys()



import os
import optparse
from datetime import datetime

import numpy as N

from rccpy.hdf5.manager import HDF5DataFileManager
from newa.manager import ObsnetDataFileManager
from rccpy.timeseries.generators import dateArrayGenerator
generateHoursArray = dateArrayGenerator('hour')

from rccpy.utils.config import ConfigObject
from rccpy.utils.data import dictToConstraints
from rccpy.utils.data import safeDataKey, safevalue, safedict
from rccpy.utils.options import optionsAsDict, stringToTuple

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

PKG_DIRPATH, _f_ = os.path.split(__file__)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config as CONFIG
SEARCH_KEYS = CONFIG.search_keys
WORKING_DIR = CONFIG.working_dir
RAW_DATA_ELEMENTS = tuple([key for key in CONFIG.elements.keys()
                           if not CONFIG.elements[key].has_key('dependencies')])

from newa.elements import PRECIP_ELEMENTS, TEMPERATURE_ELEMENTS
from newa.datasets import VALUE_TYPES, DESCRIPTIONS, HOURLY_DATA_TYPES
from newa.database.index import INDEX
from rccpy.utils.timeseries import VALID_FREQUENCIES
from rccpy.utils.timeutils import MONTHS

DATE_FORMULAE = { 'hour' : 'year*1000000 + month*10000 + day*100 + hour',
                  'day' : 'year*10000 + month*100 + day',
                  'month' : 'year*100 + month'
                }

DEFAULT_FILEPATH_TEMPLATE = '%d_%s.h5'
FILEPATH_TEMPLATES = { 'hour'       : 'hours%s%%d_hours.h5' % os.sep,
                       'hours'      : 'hours%s%%d_hours.h5' % os.sep,
                       'day'        : 'days%s%%d_days.h5' % os.sep,
                       'days'       : 'days%s%%d_days.h5' % os.sep, 
                       'seq'        : 'log%s%%d_sequences.log' % os.sep, 
                       'sequence'   : 'log%s%%d_sequences.log' % os.sep, 
                       'sequences'  : 'log%s%%d_sequences.log' % os.sep, 
                       'spike'      : 'log%s%%d_spikes.log' % os.sep, 
                       'spikes'     : 'log%s%%d_spikes.log' % os.sep, 
                       'stats'      : 'statistics%s%%d_statistics.h5' % os.sep, 
                       'statistics' : 'statistics%s%%d_statistics.h5' % os.sep,
                     }
                     
DIRECTORY_KEYS = ('day', 'days', 'hour', 'hours', 'index', 'log', 'stats',
                  'statistics', 'test', 'tests', 'work', 'working')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ObsnetDataFactory(object):

    def __init__(self, options, **kwargs):
        self.config = ConfigObject('config', None)

        if isinstance(options, dict): opt_dict = options
        else: opt_dict = optionsAsDict(options)

        for key, value in opt_dict.items():
            if not key.startswith('_') and value is not None:
                self.config[key] = opt_dict[key]

        for key, value in kwargs.items():
            if not key.startswith('_') and value is not None:
                self.config[key] = kwargs[key]
        if 'pkg_path' not in self.config: self.config['pkg_path'] = PKG_DIRPATH

        config_keys = self.config.keys()

        if 'working_dir' not in config_keys:
            self.config['working_dir'] = WORKING_DIR

        if 'ManagerClass' not in config_keys:
            self.config.newChild('ManagerClass')
            self.config.ManagerClass.hdf5 = HDF5DataFileManager
            self.config.ManagerClass.index = HDF5DataFileManager
            self.config.ManagerClass.stats = HDF5DataFileManager
            self.config.ManagerClass.statistics = HDF5DataFileManager
            self.config.ManagerClass.hour = ObsnetDataFileManager
            self.config.ManagerClass.hours = ObsnetDataFileManager
            self.config.ManagerClass.day = ObsnetDataFileManager
            self.config.ManagerClass.days = ObsnetDataFileManager

        if 'station_filename_tmpl' not in config_keys:
            self.config['station_filename_tmpl'] = '%d_%s.h5'

        if 'station_index_file' not in config_keys:
            index_filepath = os.path.join(self.config.working_dir,
                                          'station_index.h5')
            self.config['station_index'] = index_filepath
        if 'debug' not in config_keys:
            self.config.debug = False
        self.debug = self.config.debug

    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def argsToStationData(self, args, options, metadata='all', filepath=None,
                                search_keys=SEARCH_KEYS, sort_by=None):
        criteria = self._validCriteria(options, search_keys)

        num_args = len(args)
        if num_args > 0:
            # request for list of stations
            if args[0].isdigit():
                if metadata == 'ucanid': return [int(arg) for arg in args]
                else:
                    stations = [self.getStations(metadata,{'ucanid':int(arg),})[0]
                                     for arg in args]
            # request for range of stations from index file
            elif ':' in args[0]:
                stations = self.getStations(metadata, criteria)
                # request for range of stations
                stations = self._rangeOfStations(stations, args)
            # request for stations from source other than index file
            else:
                filepath = args[0]
                if filepath != 'newa' and filepath not in DIRECTORY_KEYS:
                    filepath = os.path.normpath(filepath)
                stations = self.getStations(metadata, criteria, filepath)
                # request was for all stations
                if num_args > 1:
                    if ':' not in args[1]:
                        errmsg = 'Invalid argument list : "%s:'
                        raise ValueError, errmsg % ' '.join(args)
                    # request for range of stations
                    stations = self._rangeOfStations(stations, args[1:])

        else:
            stations = self.getStations(metadata, criteria, filepath)

        if sort_by is not None and len(stations) > 1:
            stations = self._sortStations(stations,sort_by)
        if metadata == 'ucanid':
            return [station['ucanid'] for station in stations]
        else:
            return stations

    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def backupIndexFile(self, keep_original=True):
        index_filepath = self.getFilepath('index')
        if not os.path.exists(index_filepath):
            errmsg = 'Station index file not accessable : %s' % index_filepath
            raise IOError, errmsg

        time_str = datetime.now().strftime(CONFIG.backup_date_format)
        index_rootpath, ext = os.path.splitext(index_filepath)
        backup_filepath = self._backupFilePath(index_filepath)
        try:
            if keep_original:
                os.system('cp %s %s' % (index_filepath, backup_filepath))
            else: os.system('mv %s %s' % (index_filepath, backup_filepath))
        except:
            e, param, ttback = sys.exc_info()
            print e, param
            print tback
            errmsg = 'Unable to create backup file :', backup_filepath
            raise IOError, errmsg
        return index_filepath, backup_filepath

    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def fileExists(self, file_key_or_path):
        filepath = self.getFilepath(file_key_or_path)
        return os.path.isfile(filepath)

    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def getDirectoryPath(self, directory_key):
        if directory_key in ('day','days'):
            return os.path.join(self.config.working_dir, 'days')
        elif directory_key in ('hour','hours'):
            return os.path.join(self.config.working_dir, 'hours')
        elif directory_key in ('index','work','working'):
            return self.config.working_dir
        elif directory_key in ('log','logs'):
            return os.path.join(self.config.working_dir, 'logs')
        elif directory_key in ('stats','statistics'):
            return os.path.join(self.config.working_dir, 'statistics')
        elif directory_key in ('test','tests'):
            return os.path.join(self.config.working_dir, 'tests')
        elif directory_key in ('scripts','validation'):
            if directory_key in self.config:
                return self.config[directory_key]
            else: return os.path.join(self.config['pkg_path'],directory_key)
        else: 
            return os.path.join(self.config.working_dir, directory_key)

    def getFileManager(self, file_key_or_path, mode='r'):
        filepath = self.getFilepath(file_key_or_path)
        if filepath is None:
            raise ValueError, errmsg % file_key_or_path

        if os.path.exists(filepath):
            if mode == 'w':
                return self.getManagerClass(file_key_or_path)(filepath, 'a')
            else: return self.getManagerClass(file_key_or_path)(filepath, mode)
        else:
            if mode == 'r': raise IOError, 'File not found : %s' % filepath
            dirpath, filename = os.path.split(filepath)
            if not os.path.exists(dirpath): os.makedirs(dirpath)
            manager = self.getManagerClass(file_key_or_path)(filepath, 'w')
            manager.setFileAttribute('created', manager._timestamp())
            return manager

    def getFilepath(self, file_key_or_path):
        if isinstance(file_key_or_path, int):
            return self.getFilepathForUcanid(file_key_or_path)
        elif isinstance(file_key_or_path, (tuple,list)):
            return self.getFilepathForUcanid(*file_key_or_path)
        elif isinstance(file_key_or_path, basestring):
            if file_key_or_path.endswith('.h5'):
                return file_key_or_path
            elif file_key_or_path == 'index':
                return self.config.station_index
        return None

    def getFilepathForUcanid(self, ucanid, file_type='hours'):
        if not isinstance(ucanid, int): ucaind = int(ucanid)
        filename_tmpl = FILEPATH_TEMPLATES.get(file_type, None)
        if filename_tmpl is None:
            filepath = DEFAULT_FILEPATH_TEMPLATE % (ucanid, file_type)
        else:
            filepath = filename_tmpl % ucanid
        filepath = os.path.join(self.config.working_dir, filepath)
        dirpath = os.path.split(filepath)[0]
        if not os.path.exists(dirpath): os.makedirs(dirpath)
        return filepath

    def getManagerClass(self, file_key_or_path):
        if isinstance(file_key_or_path, (tuple,list)):
            filetype = file_key_or_path[1]
        elif file_key_or_path.endswith('.h5'): filetype = 'hdf5'
        else: filetype = file_key_or_path
        
        if filetype in self.config.ManagerClass.keys():
            return self.config.ManagerClass[filetype]

        errmsg = 'Unable to detect file type for %s' % str(file_key_or_path)
        raise ValueError, errmsg


    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def getStations(self, metadata='ucanid', criteria=None, filepath=None,
                          sort_by=None):
        if filepath is None or filepath == 'index':
            return self.getIndexedStations(metadata, criteria, sort_by)
        elif filepath == 'newa':
            return self.getNewaStations(metadata, criteria, sort_by)
        elif filepath == 'ucan':
            return self.getUcanStations(metadata, criteria, sort_by)
        elif isinstance(filepath, (list,tuple)):
            return self.getStationsInDirectory(filepath[0],filepath[1],
                                               metadata, criteria, sort_by)
        try:
            return self.getStationsInDirectory(filepath,metadata,criteria,sort_by)
        except ValueError:
            return self.readStationListFile(filepath,metadata,criteria,sort_by)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getIndexedStations(self, metadata='all', criteria=None, sort_by=None):

        manager = self.getFileManager('index', mode='r')
        dataset_names = self._parseMetadata(metadata, manager)
        _criteria = self._validCriteria(criteria, dataset_names)
        datasets = manager.getDataWhere(dataset_names, _criteria)
        manager.closeFile()

        stations = [ ]
        for stn_indx in range(len(datasets[0])):
            station = { }
            for indx in range(len(dataset_names)):
                station[safeDataKey(dataset_names[indx])] =\
                                         safevalue(datasets[indx][stn_indx])
            stations.append(station)

        if sort_by is not None:
            stations = self._sortStations(stations, sort_by)
        return stations

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getNewaStations(self, metadata=None, criteria=None,  sort_by=None):
        from newa.services import NEWA_METADATA, NewaWebServicesClient
        client = NewaWebServicesClient()

        stations = [ ]
        for station in client.request('stationList', 'all'):
            station = safedict(station,True)
            station['sid'] = str(station['id']) # str() converts numeric ids
            del station['id']
            stations.append(station)
        del client

        if metadata is None:
            stations = self._constrain(stations, NEWA_METADATA, criteria)
        else:
            NEWA_METADATA
            stations = self._constrain(stations, metadata, criteria)
        if sort_by is not None: stations = self._sortStations(stations,sort_by)
        return stations

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getUcanStations(self, metadata='all', criteria=None, sort_by=None):
        from rccpy.stations.ucan import UcanConnection, UnknownUcanId

        dataset_names = self._parseMetadata(metadata)

        missing_county = INDEX.county.missing
        missing_gmt = INDEX.gmt.missing

        stations = [ ]
        ucan = UcanConnection()
        for station in self.getNewaStations(dataset_names, criteria):
            if 'sid' in dataset_names: station['sid'] = station['id']
            del station['id']
            try:
                ucanid = ucan.ucanid(station)
            except KeyError as e:
                if self.debug:
                    msg = 'Unable to acquire UCAN ID for %s : %s'
                    print msg % (station['sid'],station['name'])
                continue
            else:
                if 'ucanid' in dataset_names:
                    station['ucanid'] = ucanid
                try:
                    meta = ucan.getMetadata(station)
                except UnknownUcanId:
                    if self.debug:
                        print 'No metadata avaiable for UCAN ID :', ucanid
                    if 'county' in dataset_names:
                        station['county'] = missing_county
                    if 'gmt' in dataset_names:
                        station['gmt'] = missing_gmt
                else:
                    if 'county' in dataset_names:
                        station['county'] = meta['county']
                    if 'gmt' in dataset_names:
                        gmt = meta['gmt_offset']
                        if gmt > 0: station['gmt'] = -gmt 
                        else: station['gmt'] = gmt 

        del ucan
        if sort_by is not None: stations = self._sortStations(stations,sort_by)
        return stations

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getStationsInDirectory(self, directory_key_or_path, metadata='all',
                                     criteria=None, file_type=None,
                                     sort_by=None):
        dataset_names = self._parseMetadata(metadata)
        _criteria = self._validCriteria(criteria, station.keys())
        constraints = dictToConstraints(_criteria, ') and (')

        if os.path.exists(directory_key_or_path):
            directory_path = directory_key_or_path
        else: directory_path = self.getDirectoryPath(directory_key_or_path)
        if file_type is None:
            file_suffix = '_%s.h5' % directory_key_or_path
        else:
            file_suffix = '_%s.h5' % file_type
        has_elements = 'hour' in file_suffix

        filepaths = [ ]
        for name in os.listdir(directory_path):
            if name.endswith(file_suffix):
                filepaths.append(os.path.join(directory_path, name))
        if len(filepaths) < 1: return ()

        stations = [ ]
        ManagerClass = self.getManagerClass(directory_key_or_path)
        for filepath in filepaths:
            manager = ManagerClass(filepaths[0], 'r')
            attrs = manager.getFileAttributes()
            manager.closeFile()

            if constraints is None or eval(constraints,globals(),attrs):
                station =  { }
                for key, value in attrs:
                    if key in dataset_names: station[key] = value

                if has_elements and 'elements' in dataset_names:
                    station['elements'] = ','.join(manager.listGroups())

                stations.append(station)

        if sort_by is not None: stations = self._sortStations(stations,sort_by)
        return stations

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def readStationListFile(self, filepath, metadata='all', criteria=None,
                                  sort_by=None):
        dataset_names = self._parseMetadata(metadata)
        dataset_names.sort()
        _criteria = self._validCriteria(criteria, station.keys())
        constraints = dictToConstraints(_criteria, ') and (')
        stations = [ ]

        filename, file_ext = os.path.splitext(filepath)
        stn_file = open(filepath,'r')
        if file_ext == '.json':
            for station in json.loads(stn_file.read())['stations']:
                station = safedict(station)
                if 'id' in station:
                    station['sid'] = station['id']
                    del station['id']
                if constraints is not None or eval(constraints,globals(),station):
                    stations.append(station)
        else:
            for station in eval(stn_file.read().replace('\n','').replace(' ','')):
                station = safedict(station)
                if 'id' in station:
                    station['sid'] = station['id']
                    del station['id']
                if constraints is not None or eval(constraints,globals(),station):
                    stations.append(station)
        stn_file.close()

        station_datasets = stations[0].keys()
        station_datasets.sort()
        if station_datasets != dataset_names:
            for station in stations:
                for key in station:
                    if key not in dataset_names: del statin[key]

        if sort_by is not None: stations = self._sortStations(stations,sort_by)
        return stations

    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def createHourlyDataGroup(self, manager, element, data, start_hour,
                                    end_hour, **kwargs):
        # create element group
        attrs = { }
        attrs['created'] = manager._timestamp()
        attrs['description'] = kwargs.get('description', DESCRIPTIONS[element])
        attrs['first_hour'] = start_hour.timetuple()[:4]
        attrs['frequency'] = 'hour'
        attrs['interval'] = 1
        attrs['last_hour'] = end_hour.timetuple()[:4]
        manager.createGroup(element, attrs)

        # generate the dates array and use it to create a dataset
        dataset_name = '%s.date' % element
        hours = generateHoursArray(start_hour, end_hour, date_format=int,
                                   interval=1, as_numpy=True)
        manager.createDataset(dataset_name, hours, attrs)
        manager.setDatasetAttribute(dataset_name, 'description',
                                    'Year,Month,Day,Hour')
        manager.setDatasetAttribute(dataset_name, 'date_formula',
                                    DATE_FORMULAE['hour'])

        # cretae value dataset
        dataset_name = '%s.value' % element
        for attr_name, attr_value in kwargs.items():
            if attr_name not in attrs: attrs[attr_name] = attr_value
        if 'value_type' not in attrs:
            attrs['value_type'] = VALUE_TYPES[element]
        if 'missing' not in attrs: attrs['missing'] = -32768
        if 'units' not in attrs: attrs['units'] = HOURLY_DATA_TYPES[element][2]

        manager.createDataset(dataset_name, self.transformData(element,data),
                              attrs)

    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def getConfigParameter(self, parameter_name):
        return self.config.get(parameter_name, None)

    def transformData(self, element, data, to_dataset=True):
        if to_dataset:
            if element in PRECIP_ELEMENTS: data *= 100.
            elif element in TEMPERATURE_ELEMENTS: data *= 10.
            data[N.where(N.isnan(data))] = -32768
            data[N.where(N.isinf(data))] = -32768
            return N.array(data, dtype='i2')
        else:
            data = N.array(data, dtype=float)
            data[data == -32768] = N.nan
            if element in PRECIP_ELEMENTS: data /= 100.
            elif element in TEMPERATURE_ELEMENTS: data /= 10.
            return data
    
    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def _backupFilePath(self, filepath):
        time_str = datetime.now().strftime(CONFIG.backup_date_format)
        rootpath, ext = os.path.splitext(filepath)
        backup_filepath = '%s_%s%s' % (rootpath, time_str, ext)
        return backup_filepath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _constrain(self, stations, metadata, criteria, manager=None):
        if criteria is not None:
            _criteria = self._validCriteria(criteria, metadata)
            constraints = dictToConstraints(_criteria, ' & ')
            stations = [station for station in stations 
                                if eval(constraints,globals(),station)]
        if metadata != 'all':
            dataset_names = self._parseMetadata(metadata, manager)
            for station in stations:
                for key in station:
                    if key not in dataset_names:
                        del station[key]
        return stations

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _getFrequencyFromFilename(self, filename):
        for frequency in VALID_FREQUENCIES:
            if frequency in filename: return frequency
        if 'dbm' in filename: return 'hour'
        raise KeyError, 'Cannot determine frequency from file name'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _parseMetadata(self, metadata, manager=None):
        if isinstance(metadata, basestring):
            if metadata == 'all':
                if manager is not None:
                    return tuple(manager.listDatasets())
                else: return RAW_DATA_ELEMENTS
            else: return stringToTuple(metadata)
        elif isinstance(metadata, (list,tuple)):
            return tuple(metadata)
        else:
            errmsg = "'metadata' argument is an invalid type: %s"
            raise TypeError, errmsg % type(metadata)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _rangeOfStations(self, stations, *args):
        """ return range of stations as sepcified in args)
        """
        gop = 'gt'
        lop = 'lt'
        ucanid_low = 0
        ucanid_high = 9999999999
        if ':' in args[0]:
            op, limit = args[arg_indx].split(':')
            if limit.isdigit():
                if op in ('ge','gt'):
                    gop = op
                    ucanid_low = int(limit)
                elif op in ('le','lt'):
                    lop = op
                    ucanid_high = int(limit)
            else:
                raise ValueError, 'Invalid argument : %s' % args[0]

        if len(args) > 1:
            op, limit = args[1].split(':')
            if limit.isdigit():
                if gop and op in ('le','lt'):
                    lop = op
                    ucanid_high = int(limit)
                elif lop and op in ('ge','gt'):
                    lop = op
                    ucanid_low = int(limit)
            else:
                raise ValueError, 'Invalid argument : %s' % args[arg_indx]
        else:
            raise ValueError, 'Invalid argument list : "%s:' % ' '.join(args)

        if gop == 'ge':
            if lop == 'le':
                return [station for station in stations
                                if station['ucanid'] >= ucanid_low 
                                and station['ucanid'] <= ucanid_high]
            else:
                return [station for station in stations
                                if station['ucanid'] >= ucanid_low
                                and station['ucanid'] < ucanid_high]
        else:
            if lop == 'le':
                return [station for station in stations
                                if station['ucanid'] > ucanid_low 
                                and station['ucanid'] <= ucanid_high]
            else:
                return [station for station in stations
                                if station['ucanid'] > ucanid_low
                                and station['ucanid'] < ucanid_high]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _sortStations(self, stations, sort_by):
        if isinstance(sort_by, basestring):
            sort_keys = [key.strip() for key in sort_by.split(',')]
        elif isinstance(sort_by, (list,tuple)):
            sort_keys = sort_by
        else:
            errmsg = "'sort_by' argument is an invalid type: %s"
            raise TypeError, errmsg % type(sort_by)

        keys = ["station['%s']" % key for key in sort_keys]
        template = '"(%s,)"' % ','.join(keys)

        def sortBy(station):
            return eval(template, globals(), station)
        return sorted(stations, key=sortBy)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _validCriteria(self, criteria, dataset_names):
        if criteria is not None:
            valid_criteria = { }

            if isinstance(criteria, optparse.Values):
                for key, value in vars(criteria).items():
                    if value is None: continue
                    if (key == 'bbox' or key in dataset_names):
                        valid_criteria[key] = value

            elif isinstance(criteria, dict):
                for key, value in criteria.items():
                    if (key == 'bbox' or key in dataset_names):
                        valid_criteria[key] = value

            elif isinstance(criteria, (list,tuple)):
                valid_criteria = [ ]
                for rule in criteria:
                    if rule[0] in dataset_names:
                        valid_criteria.append(rule)
                if valid_criteria:
                    valid_criteria = tuple(valid_criteria)

            if valid_criteria: return valid_criteria
        return None

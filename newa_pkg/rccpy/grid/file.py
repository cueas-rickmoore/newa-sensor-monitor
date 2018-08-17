""" Abstract base class that defines the minimum API for data file managers.
"""

import os
from copy import deepcopy
from datetime import datetime

import numpy as N

from nrcc.utils.units import convertUnits


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

PRECIP_DATASET = 'pcpn'
MAXTEMP_DATASET = 'maxt'
MINTEMP_DATASET = 'mint'

OBSERVED_PREFIX = 'obs_'
OBSERVED_ELEV = OBSERVED_PREFIX + 'elev'
OBSERVED_MAXTEMP = OBSERVED_PREFIX + MAXTEMP_DATASET
OBSERVED_MINTEMP = OBSERVED_PREFIX + MINTEMP_DATASET
OBSERVED_PRECIP = OBSERVED_PREFIX + PRECIP_DATASET

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DATASET_DESCRIPTIONS = { 'elev' : 'elevation',
                         'lat'  : 'latitude',
                         'lon'  : 'longitude',
                         'mask' : 'land/sea mask (continental US)',
                         MAXTEMP_DATASET : 'maximum temperature',
                         MINTEMP_DATASET : 'minimum temperature',
                         PRECIP_DATASET  : 'precipitation',
                         OBSERVED_MAXTEMP : 'maximum observed temperature',
                         OBSERVED_MINTEMP : 'minimum observed temperature',
                         OBSERVED_PRECIP  : 'observed precipitation',
                       }

DATASET_TYPES = { 'elev' : N.dtype(float),
                  'lat'  : N.dtype(float),
                  'lon'  : N.dtype(float),
                  MAXTEMP_DATASET  : N.dtype(float),
                  MINTEMP_DATASET  : N.dtype(float),
                  PRECIP_DATASET   : N.dtype(float),
                  OBSERVED_ELEV    : N.dtype(float),
                  OBSERVED_MAXTEMP : N.dtype(float),
                  OBSERVED_MINTEMP : N.dtype(float),
                  OBSERVED_PRECIP  : N.dtype(float),
                }

DATASET_UNITS = { 'elev' : 'ft',
                  'lat'  : 'DD',
                  'lon'  : 'DD',
                  MAXTEMP_DATASET  : 'F',
                  MINTEMP_DATASET  : 'F',
                  PRECIP_DATASET   : 'in',
                  OBSERVED_ELEV    : 'ft',
                  OBSERVED_MAXTEMP : 'F',
                  OBSERVED_MINTEMP : 'F',
                  OBSERVED_PRECIP  : 'in',
                }

MASKED_VALUES = { 'elev' : N.nan,
                  'lat'  : N.nan,
                  'lon'  : N.nan,
                  MAXTEMP_DATASET  : N.nan,
                  MINTEMP_DATASET  : N.nan,
                  PRECIP_DATASET   : N.nan,
                  OBSERVED_ELEV    : N.nan,
                  OBSERVED_MAXTEMP : N.nan,
                  OBSERVED_MINTEMP : N.nan,
                  OBSERVED_PRECIP  : N.nan,
                }

MISSING_VALUES = { 'elev' : N.inf,
                   'lat'  : N.inf,
                   'lon'  : N.inf,
                   MAXTEMP_DATASET  : N.inf,
                   MINTEMP_DATASET  : N.inf,
                   PRECIP_DATASET   : N.inf,
                   OBSERVED_ELEV    : N.inf,
                   OBSERVED_MAXTEMP : N.inf,
                   OBSERVED_MINTEMP : N.inf,
                   OBSERVED_PRECIP  : N.inf,
                 }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

#class DatasetKey(dict):
class DatasetKey:

    def __init__(self, name, access_key=None, **kwargs):
        self.name = name
        if access_key is None:
            self.access_key = name
        else:
            self.access_key = access_key
        for var_name in kwargs.keys():
            setattr(self, var_name, kwargs[var_name])

    def get(self, var_name, default=None):
        return self.__dict__.get(var_name, default)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DataFileManager(object):

    DATA_TYPES = deepcopy(DATASET_TYPES)
    DATA_UNITS = deepcopy(DATASET_UNITS)
    DESCRIPTIONS = deepcopy(DATASET_DESCRIPTIONS)
    
    DEFAULT_MASKED = N.nan
    MASKED = deepcopy(MASKED_VALUES)

    DEFAULT_MISSING = N.inf
    MISSING = deepcopy(MISSING_VALUES)

    FLOAT_UNITS = ('C','F','K','mm','cm','m','km','in','ft')

    def __init__(self, managed_filepath, keep_open=False, allow_updates=False):
        self._managed_filepath = os.path.normpath(managed_filepath)
        self._keep_open = keep_open
        self._allow_updates = allow_updates
        self._area_mask = None

        self._managed_file = None
        self._managed_file_mode = None
        self._valid_access_keys = ()
        self._file_attributes = None

        if not os.path.isfile(self._managed_filepath):
            errmsg = 'Data file not found : ' + self._managed_filepath
            raise IOError, errmsg

        self.openFile('r')
        self.conditionalClose()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    @classmethod
    def newFile(_class_, managed_filepath, file_attributes={}, datasets=()):
        """ Alternative constructor that creates a new, writeable data file
        and returns it's manager.
        """
        managed_filepath = os.path.normpath(managed_filepath)
        if os.path.exists(managed_filepath):
            errmsg = 'Data file already exists : ' + managed_filepath
            raise IOError, errmsg

        time_stamp = _class_._timestamp_()

        new_file = _class_._openFile_(managed_filepath, 'w')
        _class_._setFileAttribute_(new_file, 'created', time_stamp)

        for attr_name, attr_value in file_attributes.items():
            _class_._setFileAttribute_(new_file, attr_name, attr_value)

        for dataset_key, data_array, attrs in datasets:
            if attrs is None: attrs = { }
            attrs['created'] = time_stamp
            if not isinstance(dataset_key, DatasetKey):
                _class_._createDataset_(new_file, DatasetKey(dataset_key),
                                        data_array, attrs)
            else:
                _class_._createDataset_(new_file, dataset_key, data_array,
                                        attrs)
        # make sure the new data is saved to the file
        _class_._closeFile_(new_file)

        # create a manager for the file
        manager = _class_(managed_filepath, keep_open=True, allow_updates=True)
        for dataset_key, data_array, attrs in datasets:
            if attrs is None: attrs = { }
            attrs = manager._datasetCreateAttrs(DatasetKey(dataset_key),
                                                data_array, attrs)
            del attrs['created']
            manager.setDatasetAttributes(dataset_key, attrs)

        # give derived class a chance to do it's thing
        _class_._postCreateHook_(manager, file_attributes, datasets)
        manager.closeFile()
        manager.setOpenState(False)

        # return an instance of the _class_ that can access data in the file
        return manager

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def allowUpdates(self, allow=True):
        self._allow_updates = allow

    def closeFile(self):
        """ Unconditional close of opened data file.
        """
        if self._managed_file is not None:
            self._closeFile_(self._managed_file)
            self._managed_file = None
            self._managed_file_mode = None

    def conditionalClose(self):
        """ Conditional close of opened data file. Only closes file if
        the constructor argument "keep_open" was set to False (the
        defualt).
        """
        if not self._keep_open:
            self.closeFile()

    def openFile(self, mode):
        """ Opens the file specified by the constructor argument
        "managed_filepath".
        """
        if mode not in ('r','a'):
            errmsg = "Umsupported access mode for the current data file."
            raise IOError, errmsg

        # file is "locked" to prevent updates
        if mode == 'a' and not self._allow_updates:
            errmsg = "Updates are not allowed in the current data file."
            raise IOError, errmsg

        if self._managed_file is not None:
            # file is already open in requested mode
            if mode == self._managed_file_mode:
                return self._managed_file
            # file is already open in different mode
            self.closeFile()

        managed_file = self._openFile_(self._managed_filepath, mode)
        if mode == 'a':
            self._setFileAttribute_(managed_file, 'updated', self._timestamp())

        self._managed_file = managed_file
        self._managed_file_mode = mode
        self._valid_access_keys = self._getDatasetKeys_(managed_file)
        self._file_attributes = self._getFileAttributes_(managed_file)

        return managed_file

    def setOpenState(self, state=True):
        self._keep_open = state

    def updatesAllowed(self):
        return self._allow_updates

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def assertDatasetExists(self, dataset_key):
        if not self.datasetExists(dataset_key):
            self.conditionalClose()
            dataset = dataset_key.name + ':' + dataset_key.access_key
            errmsg = "'%s' dataset is not present in current data file.\n"
            errmsg += self._managed_filepath
            raise KeyError, errmsg % dataset

    def datasetExists(self, dataset_key):
        if type(dataset_key) in (str, unicode):
            return dataset_key in self._valid_access_keys
        else:
            return dataset_key.access_key in self._valid_access_keys

    def listDatasetKeys(self):
        """ Returns as list of valid data keys.
        """
        return self._valid_access_keys

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getData(self, dataset_keys, **kwargs):

        if not isinstance(dataset_keys, (tuple,list)):
            decoded_key = self._decodeDatasetKey(dataset_keys)
            data, attrs = self.getRawData(decoded_key, **kwargs)
            data, attrs = self._serialize(decoded_key, data, attrs, **kwargs)
            data_info = (data, attrs)

        else:
            data_info = { }
            for dataset_key in dataset_keys:
                decoded_key = self._decodeDatasetKey(dataset_key)
                data, attrs = self.getRawData(decoded_key, **kwargs)
                data, attrs = self._serialize(decoded_key, data, attrs,
                                              **kwargs)
                data_info[dataset_key] = (data, attrs)

        return data_info

    def getRawData(self, dataset_key, **kwargs):
        """ Returns raw data for dataset indicated by dataset_key as a
        numpy array.
        """
        decoded_key = self._decodeDatasetKey(dataset_key)
        data_file = self.openFile('r')
        self.assertDatasetExists(decoded_key)

        dataset_attrs = self._getDatasetAttrs_(data_file, decoded_key)
        data = self._dataSubset(decoded_key,
                                self._getData_(data_file, decoded_key))
        dataset_attrs['dtype'] = data.dtype
        self.conditionalClose()
        return data, dataset_attrs

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def deleteDatasetAttribute(self, dataset_key, attr_name):
        """ Delete an attribute of the dataset indicated by dataset_key.
        """
        decoded_key = self._decodeDatasetKey(dataset_key)
        data_file = self.openFile('a')
        self.assertDatasetExists(decoded_key)

        dataset = self._getDataset_(data_file, decoded_key)
        self._deleteDatasetAttribute_(dataset, attr_name)
        self.conditionalClose()

    def getDatasetAttribute(self, dataset_key, attr_name):
        """ Returns the value of the attribute for the dataset indicated
        by dataset_name.
        """
        decoded_key = self._decodeDatasetKey(dataset_key)
        data_file = self.openFile('r')
        self.assertDatasetExists(decoded_key)

        try:
            attr_value = self._getDatasetAttr_(data_file,decoded_key,attr_name)
        except:
            attr_value = None
        self.conditionalClose()

        return attr_value

    def getDatasetAttributes(self, dataset_key, attr_names=()):
        """ Returns dictionary with values of the attributes for the
        dataset indicated by dataset_name.
        """
        decoded_key = self._decodeDatasetKey(dataset_key)
        data_file = self.openFile('r')
        self.assertDatasetExists(decoded_key)

        if len(attr_names) > 0:
            all_attrs = self._getDatasetAttrs_(data_file, decoded_key)
            dataset_attrs = { }
            for attr_name in attr_names:
                dataset_attrs[attr_name] = all_attrs.get(attr_name, None)
        else:
            dataset_attrs = self._getDatasetAttrs_(data_file, decoded_key)
        self.conditionalClose()

        return dataset_attrs

    def getDatasetShape(self, dataset_key):
        """ Returns the shape tuple for the dataset indicated by dataset_hey.
        """
        decoded_key = self._decodeDatasetKey(dataset_key)
        data_file = self.openFile('r')
        self.assertDatasetExists(decoded_key)
        shape = self._getDatasetShape_(data_file, decoded_key)
        self.conditionalClose()
        return shape

    def getDatasetType(self, dataset_key):
        """ Returns the type of the items in the dataset.
        """
        decoded_key = self._decodeDatasetKey(dataset_key)
        data_file = self.openFile('r')
        self.assertDatasetExists(decoded_key)
        dataset_type = self._getDatasetType_(data_file, decoded_key)
        self.conditionalClose()
        return dataset_type

    def refreshCreateAttributes(self, dataset_key, attributes=None):
        decoded_key = self._decodeDatasetKey(dataset_key)
        data_file = self.openFile('r')
        self.assertDatasetExists(decoded_key)
        data, attrs = self.getRawData(decoded_key)
        create_attrs = self._datasetCreateAttrs(decoded_key, data, attributes)
        self.setDatasetAttributes(decoded_key, create_attrs)
        self.conditionalClose()

    def setDatasetAttribute(self, dataset_key, attr_name, attr_value):
        """ Set the value of an attribute of the dataset indicated by
        dataset_key.
        """
        decoded_key = self._decodeDatasetKey(dataset_key)
        data_file = self.openFile('a')
        self.assertDatasetExists(decoded_key)

        dataset = self._getDataset_(data_file, decoded_key)
        self._setDatasetAttribute_(dataset, attr_name, attr_value)
        self.conditionalClose()

    def setDatasetAttributes(self, dataset_key, attributes):
        """ Set the values of multiple attributes of the dataset indicated
        by dataset_key.
        """
        decoded_key = self._decodeDatasetKey(dataset_key)
        data_file = self.openFile('a')
        self.assertDatasetExists(decoded_key)

        dataset = self._getDataset_(data_file, decoded_key)
        for attr_name, attr_value in attributes.items():
            self._setDatasetAttribute_(dataset, attr_name, attr_value)
        self.conditionalClose()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def deleteFileAttribute(self, attr_name):
        """ Delete an attribute of the current data file.
        """
        data_file = self.openFile('a')
        self._deleteFileAttribute_(data_file, attr_name)
        self.conditionalClose()

    def getFileAttributes(self, attr_names=()):
        if self._file_attributes is None:
            self.openFile('r')
            self.conditionalClose()
        if len(attr_names) > 0:
            file_attrs = { }
            for attr_name in attr_names:
                value = self._file_attributes.get(attr_name,None)
                file_attrs[attr_name] = value
        else:
            file_attrs = self._file_attributes
        
        return file_attrs

    def setFileAttribute(self, attr_name, attr_value):
        """ Set the value of and attribute of the current data file.
        """
        data_file = self.openFile('a')
        self._setFileAttribute_(data_file, attr_name, attr_value)
        self.conditionalClose()

    def setFileAttributes(self, **attributes):
        """ Set the values of multiple attributes of the current data file.
        """
        data_file = self.openFile('a')
        for attr_name,attr_value in attributes.items():
            self._setFileAttribute_(data_file, attr_name, attr_value)
        self.conditionalClose()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def createDataset(self, dataset_key, data_array, attributes=None, **kwargs):
        decoded_key = self._decodeDatasetKey(dataset_key)
        if len(data_array) == 0:
            errmsg = 'Attempting to create dataset %s:%s with an empty array.'
            raise ValueError, errmsg % (decoded_key.name,decoded_key.access_key)

        if not isinstance(data_array, N.ndarray):
            data_array = self._dataAsArray(decoded_key.name, data_array)

        data_file = self.openFile('a')

        if not self.datasetExists(decoded_key):
            attrs = self._datasetCreateAttrs(decoded_key, data_array,
                                             attributes)
            dataset = self._createDataset_(data_file, decoded_key, data_array,
                                           attrs, **kwargs)
            self.conditionalClose()
            self._refreshValidAccessKeys()
        else:
            self.conditionalClose()
            errmsg = "Dataset '%s' already exists in current file."
            raise IOError, errmsg % decoded_key.name

        return dataset

    def updateDataset(self, dataset_key, data_array, attributes=None, **kwargs):
        decoded_key = self._decodeDatasetKey(dataset_key)
        if len(data_array) == 0:
            errmsg = 'Attempting to update dataset %s:%s with an empty array.'
            raise ValueError, errmsg % (decoded_key.name,decoded_key.access_key)

        if not isinstance(data_array, N.ndarray):
            data_array = self._dataAsArray(decoded_key.name, data_array)

        data_file = self.openFile('a')

        if self.datasetExists(decoded_key):
            attrs = self._datasetUpdateAttrs(decoded_key, data_array,
                                             attributes)
            dataset = self._updateDataset_(data_file, decoded_key, data_array,
                                           attrs, **kwargs)
        else:
            attrs = self._datasetCreateAttrs(decoded_key, data_array,
                                             attributes)
            dataset = self._createDataset_(data_file, decoded_key, data_array,
                                           attrs, **kwargs)
        self.conditionalClose()
        self._refreshValidAccessKeys()
        return dataset

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def applyAreaMask(self, dataset_key, data):
        if self._area_mask is not None:
            return N.ma.array(data, mask=self._area_mask, keep_mask=True)
        return data

    def maskInvalidData(self, dataset_key, data_array, data_attrs):
        decoded_key = self._decodeDatasetKey(dataset_key)
        mask_value = self._maskValue(decoded_key, data_attrs)
        missing_value = self._missingValue(decoded_key, data_attrs)

        masked = self._maskEqualTo(data_array, mask_value)
        if not self._valuesAreEqual(mask_value, missing_value):
            masked = self._maskEqualTo(masked, missing_value)
        return self.applyAreaMask(decoded_key, masked)

    def setAreaMask(self, mask_name='mask'):
        """ Returns the area mask as an array.
        """
        mask_array, attrs = self.getRawData(mask_name)
        self._area_mask = mask_array

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _dataArrayType(self, dataset_name, dataset):
        return self.DATA_TYPES.get(dataset_name,None)

    def _dataAsArray(self, dataset_name, dataset):
        if isinstance(dataset, N.ndarray): return dataset
        return N.array(dataset, dtype=self._dataArrayType(dataset_name,dataset))

    def _dataDescription(self, dataset_key, data_attrs=None):
        if type(data_attrs) == dict:
            return data_attrs.get('description', dataset_key.get('description',
                                  self.DESCRIPTIONS.get(dataset_key.name,None)))
        else:
            return dataset_key.get('description',
                                 self.DESCRIPTIONS.get(dataset_key.name,None))

    def _dataSubset(self, dataset_key, data):
        return data

    def _dataUnits(self, dataset_key, data_attrs=None):
        if type(data_attrs) == dict:
            return data_attrs.get('units', dataset_key.get('units',
                                  self.DATA_UNITS.get(dataset_key.name,None)))
        else:
            return dataset_key.get('units',
                                   self.DATA_UNITS.get(dataset_key.name,None))

    def _datasetCreateAttrs(self, dataset_key, data_array, attributes=None):
        attrs = { }
        if type(attributes) == dict: attrs.update(attributes)
        attr_keys = attrs.keys()
        if 'created' not in attr_keys:
            attrs['created'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if 'description' not in attr_keys:
            description = self._dataDescription(dataset_key, attributes)
            if description is not None: attrs['description'] = description
        if 'units' not in attr_keys:
            units = self._dataUnits(dataset_key, attributes)
            if units is not None: attrs['units'] = units
        if self._isNumericData(data_array):
            extreme = self._maxValidValue(dataset_key, data_array)
            if extreme is not None:
                attrs['max'] = extreme
            extreme = self._minValidValue(dataset_key, data_array)
            if extreme is not None:
                attrs['min'] = extreme
        return attrs

    def _datasetUpdateAttrs(self, dataset_key, data_array, attributes=None):
        attrs = { }
        if type(attributes) == dict: attrs.update(attributes)
        attrs['updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self._isNumericData(data_array):
            extreme = self._maxValidValue(dataset_key, data_array)
            if extreme is not None:
                attrs['max'] = extreme
            extreme = self._minValidValue(dataset_key, data_array)
            if extreme is not None:
                attrs['min'] = extreme
        return attrs

    def _decodeDatasetKey(self, dataset_key):
        if isinstance(dataset_key, DatasetKey):
            return dataset_key
        elif isinstance(dataset_key, basestring):
            name, key_dict = self._parseDatasetKeyString(dataset_key)
            if key_dict:
                return DatasetKey(name, name, **key_dict)
            else:
                return DatasetKey(name, name)
        elif type(dataset_key) == dict:
            dict_keys = dataset_key.keys()
            if 'name' in dict_keys:
                name = dataset_key['name']
                if 'access_key' in dict_keys:
                    access_key = dataset_key['access_key']
                    del dataset_key['access_key']
                else:
                    access_key = name
                del dataset_key['name']
                return DatasetKey(name, access_key, **dataset_key)
            else:
                errmsg = "Invalid dataset_key, dict must comtaim a 'name' emtry."
                raise ValueError, errmsg
        else:
            errmsg = "Invalid type for dataset_key, it must be str or dict."
            raise TypeError, errmsg

    def _isNumericData(self, data_array):
        return data_array.dtype.kind in (N.dtype(float).kind, N.dtype(int).kind)

    def _maskEqualTo(self, data_array, mask_value):
        if mask_value is not None:
            if N.isfinite(mask_value):
                kind_of_data = data_array.dtype.kind
                if kind_of_data == N.dtype(float).kind:
                    return N.ma.masked_values(data_array, mask_value)
                elif kind_of_data == N.dtype(int).kind:
                    return N.ma.masked_equal(data_array, mask_value)
                return N.ma.masked_where(data_array == mask_value, data_array)
            elif N.isinf(mask_value):
                return N.ma.masked_where(N.isinf(data_array), data_array)
            elif N.isnan(mask_value):
                return N.ma.masked_where(N.isnan(data_array), data_array)
        return data_array

    def _maskValue(self, dataset_key, data_attrs):
        if type(data_attrs) == dict:
            value = data_attrs.get('masked', dataset_key.get('masked',
                                   self.MASKED.get(dataset_key.name,None)))
        else:
            value = dataset_key.get('masked',
                                    self.MASKED.get(dataset_key.name,None))
        if value is not None: return value
        dtype = data_attrs.get('dtype', None)
        if dtype is not None and type(dtype) == N.dtype and\
           dtype.kind == 'f': return self.DEFAULT_MASKED
        return None

    def _maxValidValue(self, dataset_key, data_array, data_attrs={}):
        valid = self._validData(dataset_key, data_array, data_attrs)
        if len(valid) > 0:
            if valid.dtype.kind == 'f':
                return N.nanmax(valid)
            else:
                return valid.max()
        # no valid values
        return self._missingValue(self._decodeDatasetKey(dataset_key),
                                  data_attrs)

    def _minValidValue(self, dataset_key, data_array, data_attrs={}):
        valid = self._validData(dataset_key, data_array, data_attrs)
        if len(valid) > 0:
            if valid.dtype.kind == 'f':
                return N.nanmin(valid)
            else:
                return valid.min()
        # no valid values
        return self._missingValue(self._decodeDatasetKey(dataset_key),
                                  data_attrs)

    def _missingValue(self, dataset_key, data_attrs):
        if type(data_attrs) == dict:
            value = data_attrs.get('missing', dataset_key.get('missing',
                                   self.MISSING.get(dataset_key.name,None)))
        else:
            value = dataset_key.get('missing',
                                    self.MISSING.get(dataset_key.name,None))
        if value is not None: return value
        dtype = data_attrs.get('dtype', None)
        if dtype is not None and type(dtype) == N.dtype and\
           dtype.kind == 'f': return self.DEFAULT_MISSING
        return None

    def _parseDatasetKeyString(self, data_key_string):
        left_bracket = data_key_string.find('[')
        if left_bracket < 0:
            return data_key_string, { }
        else:
            name = data_key_string[:left_bracket]
            _slice_ = data_key_string[left_bracket+1:-1]
            if _slice_.isdigit():
                return name, {'slice' : int(_slice_)}
            else:
                parts = _slice_.split(':')
                if len(parts[0]) > 0:
                    start = int(parts[0])
                else:
                    start = ':'
                if len(parts[1]) > 0:
                    end = int(parts[1])
                else:
                    end = ':'
                return name, {'slice' : (start, end),}

    def _refreshValidAccessKeys(self):
        data_file = self.openFile('r')
        self._valid_access_keys = self._getDatasetKeys_(data_file)
        self.conditionalClose()

    def _serialize(self, dataset_key, data, data_attrs, **kwargs):
        data_units = self._dataUnits(dataset_key, data_attrs)
        serial_units = kwargs.get('units', data_units)
        if data_units == serial_units:
            return data, data_attrs

        if data_units is None:
            errmsg = "Cannot convert '%s' dataset to '%s' units."
            raise KeyError, errmsg % (dataset_key.name, serial_units)

        per_degree = kwargs.get('per_degree',False)
        try:
            if not per_degree:
                data = convertUnits(data, data_units, serial_units)
            else:
                data = convertUnits(data, 'd'+data_units, 'd'+serial_units)
        except:
            errmsg = "Cannot convert '%s' from '%s' to '%s'."
            raise KeyError, errmsg % (dataset_key.name, data_units, serial_units)

        data_attrs['units'] = serial_units
        return data, data_attrs

    def _timestamp(self, date_time=None):
        return self._timestamp_(date_time)

    def _validData(self, dataset_key, data_array, data_attrs):
        decoded_key = self._decodeDatasetKey(dataset_key)
        valid = self.applyAreaMask(decoded_key, data_array)
        mask_value = self._maskValue(decoded_key, data_attrs)
        missing_value = self._missingValue(decoded_key, data_attrs)
        if valid.dtype.kind == 'f':
            valid = valid[N.where(N.isfinite(valid))]
            if mask_value is not None and N.isfinite(mask_value):
                valid = valid[N.where(valid != mask_value)]
            if missing_value is not None and N.isfinite(missing_value):
                valid = valid[N.where(valid != missing_value)]
        else:
            if mask_value is not None:
                valid = valid[N.where(valid != mask_value)]
            if missing_value is not None:
                valid = valid[N.where(valid != missing_value)]

        return valid

    def _valuesAreEqual(self, value_1, value_2):
        if value_1 is None or value_2 is None or\
           (N.isfinite(value_1) and N.isfinite(value_1)):
            return value_1 == value_2
        if N.isnan(value_1) and N.isnan(value_2): return True
        if N.isposinf(value_1) and N.isposinf(value_2): return True
        if N.isneginf(value_1) and N.isneginf(value_2): return True
        return False

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    # static methods
    #
    # these are specific to the file format and must be implemented by
    # the mixin class that manages the file fomat
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _closeFile_(data_file):
        """ Closes the file-like object passed by data_file.
        """
        raise NotImplementedError

    @staticmethod
    def _createDataset_(data_file, dataset_key, data_array, attributes,
                        **kwargs):
        """ Creates a new dataset in the data file and returns a pointer to
        it. Raises IOError exception if the dataset already exists.
        """
        raise NotImplementedError

    @staticmethod
    def _deleteDatasetAttribute_(dataset, attr_name):
        """ Deletes and attribute of a dataset.
        """
        raise NotImplementedError

    @staticmethod
    def _deleteFileAttribute_(data_file, attr_name):
        """ Deletes an attribute of the file.
        """
        raise NotImplementedError

    @staticmethod
    def _getData_(data_file, dataset_key):
        """ Returns the data for the dataset indicated by dataset_key as an
        array.
        """
        raise NotImplementedError

    @staticmethod
    def _getDataMask_(data_file, mask_name):
        """ Returns the data mask indicated by mask_name as an array.
        """
        raise NotImplementedError

    @staticmethod
    def _getDataset_(data_file, dataset_key):
        """ Returns the dataset indicated by dataset_key.
        """
        raise NotImplementedError

    @staticmethod
    def _getDatasetAttr_(data_file, dataset_key, attr_name):
        """ Returns a the value of a single attribute of the dataset
        indicated by dataset_key.
        """
        raise NotImplementedError

    @staticmethod
    def _getDatasetAttrs_(data_file, dataset_key):
        """ Returns a dictionary of attr_name/attr_value pairs for all
        queryable attributes of the dataset indicated by dataset_key.
        """
        raise NotImplementedError

    @staticmethod
    def _getDatasetKeys_(data_file):
        """ Returns a tuple with the list of the keys for all datasets in
        the file.
        """
        raise NotImplementedError

    @staticmethod
    def _getDatasetType_(data_file, dataset_key):
        """ Returns a the type of data in the dataset.
        """
        raise NotImplementedError

    @staticmethod
    def _getFileAttributes_(data_file):
        """ Returns a dictionary of attr_name/attr_value pairs for all
        setable attributes of the file.
        """
        raise NotImplementedError

    @staticmethod
    def _openFile_(filepath, mode):
        """ Returns a pointer to an instance of a file-like object for
        accessing data in 'filepath'.
        """
        raise NotImplementedError

    @staticmethod
    def _postCreateHook_(manager, file_attributes=None, datasets=None):
        """ Allows a class to handle special requirements when creating new
        files via the 'newFile' method.
        """
        pass

    @staticmethod
    def _setDatasetAttribute_(dataset, attr_name, attr_value):
        """ Set the value of the dataset attribute indicated by attr_name.
        """
        raise NotImplementedError

    @staticmethod
    def _setFileAttribute_(data_file, attr_name, attr_value):
        """ Set the value of the data file attribute indicated by attr_name.
        """
        raise NotImplementedError

    @staticmethod
    def _timestamp_(date_time=None):
        if date_time is None:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            return date_time.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def _updateDataset_(data_file, dataset_key, data_array, attributes,
                        **kwargs):
        """ Update a dataset in the data file. If the dataset does not exist,
        it is created. Returns a pointer to the dataset.
        """
        raise NotImplementedError


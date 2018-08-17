""" Abstract base class that defines the minimum API for data file managers.
"""

import os
from copy import deepcopy
from datetime import datetime

import numpy as N

from rccpy.utils.units import convertUnits

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DataFileManager(object):

    def __init__(self, filepath, protected=False):
        fullpath = os.path.abspath(filepath):
        if not os.path.isfile(fullpath):
            errmsg = 'Data file not found : %s' % fullpath
            raise IOError, errmsg

        self._filepath = fullpath
        self._protected = protected

        self._file = None
        self._file_mode = None
        self._file_attributes = None
        self._dataset_names = ()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    @classmethod
    def newFile(_class_, filepath, file_attributes={}, datasets=()):
        """ Alternative constructor that creates a new, writeable data file
        and returns it's manager.
        """
        filepath = os.path.abspath(filepath)
        if os.path.exists(filepath):
            errmsg = 'Data file already exists : ' + filepath
            raise IOError, errmsg

        time_stamp = _class_._timestamp_()

        # create a new empty file
        new_file = _class_._openFile_(filepath, 'w')
        _class_._closeFile_(new_file)

        # create a manager, open the file and set file attributes
        manager = _class_.__init__(filepath, protected=False)
        manager.openFile('a')
        manager.setFileAttribute_('created', time_stamp)
        for attr_name, attr_value in file_attributes.items():
            manager.setFileAttribute(attr_name, attr_value)
        manager.closeFile() # save updates to the file

        # create the datasets
        manager.openFile('a')
        for dataset_name, data_array, attrs in datasets:
            if attrs is None: attrs = { }
            attrs['created'] = time_stamp
            manager.createDataset(dataset_name, data_array, attrs)
        manager.closeFile() # save updates to the file

        # add dataset attributes
        manager.openFile('a')
        for dataset_name, data_array, attrs in datasets:
            if attrs is None: attrs = { }
            attrs = manager._datasetCreateAttrs(dataset_name, data_array, attrs)
            del attrs['created']
            manager.setDatasetAttributes(dataset_name, attrs)
        manager.closeFile() # save updates to the file

        # give derived classes a chance to do their thing
        _class_._postCreateHook_(manager, file_attributes, datasets)

        # return an instance of the _class_ that can access data in the file
        return manager

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def protect(self, protected=True):
        self._protected = protected

    def assertFileOpen(self, mode='r'):
        if self._file is None:
            if mode == 'r': self.openFile('r')
            else:
                errmsg = "Data file is not open : %s" % self._filepath
                raise IOError, errmsg % dataset_name
        else:
            if mode == 'a':
                if not self.isProtected():
                    errmsg = "Data file is not open for writes : %s"
                    raise IOError, errmsg % self._filepath
                if self._file_mode not in ('a','w'):
                    errmsg = "Updates are not allowed in data file : %s"
                    raise IOError, errmsg % self._filepath

    def closeFile(self):
        """ Unconditional close of opened data file.
        """
        if self._file is not None:
            self._closeFile_(self._file)
            self._file = None
            self._file_mode = None

    def openFile(self, mode):
        """ Opens the file specified by the constructor argument
        "filepath".
        """
        if mode not in ('r','a'):
            errmsg = "Unsupported access mode for data file : %s"
            raise IOError, errmsg % self._filepath

        # file is "locked" to prevent updates
        if mode == 'a' and not self._protected:
            errmsg = "Updates not allowed in data file : %s"
            raise IOError, errmsg % self._filepath

        if self._file is not None:
            # file is already open in requested mode
            if mode == self._file_mode:
                return self._file
            # file is already open in different mode
            self.closeFile()

        file = self._openFile_(self._filepath, mode)
        if mode == 'a':
            self._setFileAttribute_(file, 'updated', self._timestamp())

        self._file = file
        self._file_mode = mode
        self._dataset_names = self._getDatasetNames_(file)
        self._file_attributes = self._getFileAttributes_(file)

        return file

    def isProtected(self):
        return self._protected

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def assertDatasetExists(self, dataset_name):
        if not self.datasetExists(dataset_name):
            errmsg = "'%s' dataset is not present in current data file.\n"
            errmsg += self._filepath
            raise KeyError, errmsg % dataset_name

    def datasetExists(self, dataset_name):
        return dataset_name in self._dataset_names

    def listDatasets(self):
        """ Returns as list of valid data keys.
        """
        return self._dataset_names

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getData(self, dataset_names, **kwargs):
        if isinstance(dataset_names, basestring):
            data = self.getRawData(dataset_names, **kwargs)
            attrs = self._getDatasetAttrs_(self._file, dataset_name)
            data, attrs = self._serialize(dataset_names, data, attrs, **kwargs)
            data_info = (data, attrs)

        elif isinstance(dataset_names, (tuple,list)):
            data_info = { }
            for dataset_name in dataset_names:
                data, attrs = self.getRawData(dataset_name, **kwargs)
                data, attrs = self._serialize(dataset_name, data, attrs,
                                              **kwargs)
                data_info[dataset_name] = (data, attrs)
        else:

        return data_info

    def getRawData(self, dataset_name, **kwargs):
        """ Returns raw data for dataset indicated by dataset_name as a
        numpy array.
        """
        self.assertFileOpen('r')
        self.assertDatasetExists(dataset_name)
        return self._dataSubset(dataset_name,
                                self._getData_(self._file, dataset_name))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def deleteDatasetAttribute(self, dataset_name, attr_name):
        """ Delete an attribute of the dataset indicated by dataset_name.
        """
        self.assertFileOpen()
        self.assertDatasetExists(dataset_name)

        dataset = self._getDataset_(self._file, dataset_name)
        self._deleteDatasetAttribute_(dataset, attr_name)

    def getDatasetAttribute(self, dataset_name, attr_name):
        """ Returns the value of the attribute for the dataset indicated
        by dataset_name.
        """
        self.assertFileOpen('r')
        self.assertDatasetExists(dataset_name)

        try:
            attr_value = self._getDatasetAttr_(self._file,dataset_name,attr_name)
        except:
            attr_value = None

        return attr_value

    def getDatasetAttributes(self, dataset_name, attr_names=()):
        """ Returns dictionary with values of the attributes for the
        dataset indicated by dataset_name.
        """
        self.assertFileOpen('r')
        self.assertDatasetExists(dataset_name)

        if len(attr_names) > 0:
            all_attrs = self._getDatasetAttrs_(self._file, dataset_name)
            dataset_attrs = { }
            for attr_name in attr_names:
                dataset_attrs[attr_name] = all_attrs.get(attr_name, None)
        else:
            dataset_attrs = self._getDatasetAttrs_(self._file, dataset_name)

        return dataset_attrs

    def getDatasetShape(self, dataset_name):
        """ Returns the shape tuple for the dataset indicated by dataset_hey.
        """
        self.assertFileOpen('r')
        self.assertDatasetExists(dataset_name)
        shape = self._getDatasetShape_(self._file, dataset_name)
        return shape

    def getDatasetType(self, dataset_name):
        """ Returns the type of the items in the dataset.
        """
        self.assertFileOpen('r')
        self.assertDatasetExists(dataset_name)
        dataset_type = self._getDatasetType_(self._file, dataset_name)
        return dataset_type

    def refreshCreateAttributes(self, dataset_name, attributes=None):
        self.assertFileOpen('r')
        self.assertDatasetExists(dataset_name)
        data, attrs = self.getRawData(dataset_name)
        create_attrs = self._datasetCreateAttrs(dataset_name, data, attributes)
        self.setDatasetAttributes(dataset_name, create_attrs)

    def setDatasetAttribute(self, dataset_name, attr_name, attr_value):
        """ Set the value of an attribute of the dataset indicated by
        dataset_name.
        """
        self.assertFileOpen('a')
        self.assertDatasetExists(dataset_name)

        dataset = self._getDataset_(self._file, dataset_name)
        self._setDatasetAttribute_(dataset, attr_name, attr_value)

    def setDatasetAttributes(self, dataset_name, attributes):
        """ Set the values of multiple attributes of the dataset indicated
        by dataset_name.
        """
        self.assertFileOpen('a')
        self.assertDatasetExists(dataset_name)

        dataset = self._getDataset_(self._file, dataset_name)
        for attr_name, attr_value in attributes.items():
            self._setDatasetAttribute_(dataset, attr_name, attr_value)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def deleteFileAttribute(self, attr_name):
        """ Delete an attribute of the current data file.
        """
        self.assertFileOpen('a')
        self._deleteFileAttribute_(self._file, attr_name)

    def getFileAttributes(self, attr_names=()):
        if self._file_attributes is None:
            self.openFile('r')
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
        self.assertFileOpen('a')
        self._setFileAttribute_(self._file, attr_name, attr_value)

    def setFileAttributes(self, **attributes):
        """ Set the values of multiple attributes of the current data file.
        """
        self.assertFileOpen('a')
        for attr_name,attr_value in attributes.items():
            self._setFileAttribute_(self._file, attr_name, attr_value)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def createDataset(self, dataset_name, data_array, attributes=None, **kwargs):
        self.assertFileOpen('a')

        if len(data_array) == 0:
            errmsg = 'Attempting to create dataset %s with an empty array.'
            raise ValueError, errmsg % dataset_name

        if not isinstance(data_array, N.ndarray):
            data_array = self._dataAsArray(dataset_name, data_array)

        if not self.datasetExists(dataset_name):
            attrs = self._datasetCreateAttrs(dataset_name, data_array,
                                             attributes)
            dataset = self._createDataset_(self._file, dataset_name, data_array,
                                           attrs, **kwargs)
            self._refreshDatasetList()
        else:
            errmsg = "Dataset '%s' already exists in current file."
            raise IOError, errmsg % dataset_name

        return dataset

    def updateDataset(self, dataset_name, data_array, attributes=None, **kwargs):
        if len(data_array) == 0:
            errmsg = 'Attempting to update dataset %s with an empty array.'
            raise ValueError, errmsg % dataset_name

        if not isinstance(data_array, N.ndarray):
            data_array = self._dataAsArray(dataset_name, data_array)

        self.assertFileOpen('a')

        if self.datasetExists(dataset_name):
            attrs = self._datasetUpdateAttrs(dataset_name, data_array,
                                             attributes)
            dataset = self._updateDataset_(self._file, dataset_name, data_array,
                                           attrs, **kwargs)
        else:
            attrs = self._datasetCreateAttrs(dataset_name, data_array,
                                             attributes)
            dataset = self._createDataset_(self._file, dataset_name, data_array,
                                           attrs, **kwargs)
        self._refreshDatasetList()
        return dataset

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def maskInvalidData(self, dataset_name, data_array, data_attrs):
        mask_value = self._maskValue(dataset_name, data_attrs)
        masked = self._maskEqualTo(data_array, mask_value)

        missing_value = self._missingValue(dataset_name, data_attrs)
        if not self._valuesAreEqual(mask_value, missing_value):
            masked = self._maskEqualTo(masked, missing_value)
        return masked

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _dataArrayType(self, dataset_name, dataset):
        return self.DATA_TYPES.get(dataset_name,None)

    def _dataAsArray(self, dataset_name, dataset):
        if isinstance(dataset, N.ndarray): return dataset
        return N.array(dataset, dtype=self._dataArrayType(dataset_name,dataset))

    def _dataDescription(self, dataset_name, data_attrs=None):
        if type(data_attrs) == dict:
            return data_attrs.get('description', dataset_name.get('description',
                                  self.DESCRIPTIONS.get(dataset_name,None)))
        else:
            return dataset_name.get('description',
                                 self.DESCRIPTIONS.get(dataset_name,None))

    def _dataSubset(self, dataset_name, data):
        return data

    def _dataUnits(self, dataset_name, data_attrs=None):
        if type(data_attrs) == dict:
            return data_attrs.get('units', dataset_name.get('units',
                                  self.DATA_UNITS.get(dataset_name,None)))
        else:
            return dataset_name.get('units',
                                   self.DATA_UNITS.get(dataset_name,None))

    def _datasetCreateAttrs(self, dataset_name, data_array, attributes=None):
        attrs = { }
        if type(attributes) == dict: attrs.update(attributes)
        attr_keys = attrs.keys()
        if 'created' not in attr_keys:
            attrs['created'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if 'description' not in attr_keys:
            description = self._dataDescription(dataset_name, attributes)
            if description is not None: attrs['description'] = description
        if 'units' not in attr_keys:
            units = self._dataUnits(dataset_name, attributes)
            if units is not None: attrs['units'] = units
        if self._isNumericData(data_array):
            extreme = self._maxValidValue(dataset_name, data_array)
            if extreme is not None:
                attrs['max'] = extreme
            extreme = self._minValidValue(dataset_name, data_array)
            if extreme is not None:
                attrs['min'] = extreme
        return attrs

    def _datasetUpdateAttrs(self, dataset_name, data_array, attributes=None):
        attrs = { }
        if type(attributes) == dict: attrs.update(attributes)
        attrs['updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self._isNumericData(data_array):
            extreme = self._maxValidValue(dataset_name, data_array)
            if extreme is not None:
                attrs['max'] = extreme
            extreme = self._minValidValue(dataset_name, data_array)
            if extreme is not None:
                attrs['min'] = extreme
        return attrs

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

    def _maskValue(self, dataset_name, data_attrs):
        if type(data_attrs) == dict:
            value = data_attrs.get('masked', dataset_name.get('masked',
                                   self.MASKED.get(dataset_name,None)))
        else:
            value = dataset_name.get('masked',
                                    self.MASKED.get(dataset_name,None))
        if value is not None: return value
        dtype = data_attrs.get('dtype', None)
        if dtype is not None and type(dtype) == N.dtype and\
           dtype.kind == 'f': return self.DEFAULT_MASKED
        return None

    def _maxValidValue(self, dataset_name, data_array, data_attrs={}):
        valid = self._validData(dataset_name, data_array, data_attrs)
        if len(valid) > 0:
            if valid.dtype.kind == 'f':
                return N.nanmax(valid)
            else:
                return valid.max()
        # no valid values
        return self._missingValue(dataset_name, data_attrs)

    def _minValidValue(self, dataset_name, data_array, data_attrs={}):
        valid = self._validData(dataset_name, data_array, data_attrs)
        if len(valid) > 0:
            if valid.dtype.kind == 'f':
                return N.nanmin(valid)
            else:
                return valid.min()
        # no valid values
        return self._missingValue(dataset_name, data_attrs)

    def _missingValue(self, dataset_name, data_attrs):
        if type(data_attrs) == dict:
            value = data_attrs.get('missing', dataset_name.get('missing',
                                   self.MISSING.get(dataset_name,None)))
        else:
            value = dataset_name.get('missing',
                                    self.MISSING.get(dataset_name,None))
        if value is not None: return value
        dtype = data_attrs.get('dtype', None)
        if dtype is not None and type(dtype) == N.dtype and\
           dtype.kind == 'f': return self.DEFAULT_MISSING
        return None

    def _refreshDatasetList(self):
        self.assertFileOpen('r')
        self._dataset_names = self._getDatasetNames_(self._file)

    def _serialize(self, dataset_name, data, data_attrs, **kwargs):
        data_units = self._dataUnits(dataset_name, data_attrs)
        serial_units = kwargs.get('units', data_units)
        if data_units == serial_units:
            return data, data_attrs

        if data_units is None:
            errmsg = "Cannot convert '%s' dataset to '%s' units."
            raise KeyError, errmsg % (dataset_name, serial_units)

        per_degree = kwargs.get('per_degree',False)
        try:
            if not per_degree:
                data = convertUnits(data, data_units, serial_units)
            else:
                data = convertUnits(data, 'd'+data_units, 'd'+serial_units)
        except:
            errmsg = "Cannot convert '%s' from '%s' to '%s'."
            raise KeyError, errmsg % (dataset_name, data_units, serial_units)

        data_attrs['units'] = serial_units
        return data, data_attrs

    def _timestamp(self, date_time=None):
        return self._timestamp_(date_time)

    def _validData(self, dataset_name, data_array, data_attrs):
        data_array = data_array[N.where(N.isfinite(data_array))]

        mask_value = self._maskValue(dataset_name, data_attrs)
        if mask_value is not None and N.isfinite(mask_value):
            data_array = data_array[N.where(data_array != mask_value)]

        missing_value = self._missingValue(dataset_name, data_attrs)
        if missing_value is not None and N.isfinite(missing_value) \
        and not self._valuesAreEqual(mask_value,missing_value):
            data_array = data_array[N.where(data_array != missing_value)]
        
        return data_array

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
    def _createDataset_(data_file, dataset_name, data_array, attributes,
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
    def _getData_(data_file, dataset_name):
        """ Returns the data for the dataset indicated by dataset_name as an
        array.
        """
        raise NotImplementedError

    @staticmethod
    def _getDataMask_(data_file, mask_name):
        """ Returns the data mask indicated by mask_name as an array.
        """
        raise NotImplementedError

    @staticmethod
    def _getDataset_(data_file, dataset_name):
        """ Returns the dataset indicated by dataset_name.
        """
        raise NotImplementedError

    @staticmethod
    def _getDatasetAttr_(data_file, dataset_name, attr_name):
        """ Returns a the value of a single attribute of the dataset
        indicated by dataset_name.
        """
        raise NotImplementedError

    @staticmethod
    def _getDatasetAttrs_(data_file, dataset_name):
        """ Returns a dictionary of attr_name/attr_value pairs for all
        queryable attributes of the dataset indicated by dataset_name.
        """
        raise NotImplementedError

    @staticmethod
    def _getDatasetNames_(data_file):
        """ Returns a tuple with the list of the keys for all datasets in
        the file.
        """
        raise NotImplementedError

    @staticmethod
    def _getDatasetType_(data_file, dataset_name):
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
    def _updateDataset_(data_file, dataset_name, data_array, attributes,
                        **kwargs):
        """ Update a dataset in the data file. If the dataset does not exist,
        it is created. Returns a pointer to the dataset.
        """
        raise NotImplementedError


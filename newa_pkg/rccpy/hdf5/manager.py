""" HDF5GridManagerMixin class for accessing data from HDF5 encoded grid files.
"""

import os
from datetime import datetime

import h5py
import numpy as N

from rccpy.utils.data import safestring, safevalue, safedict
from rccpy.utils.data import safeDataKey, dictToWhere, listToWhere
from rccpy.utils.units import getConversionFunction

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DatasetKey(object):

    def __init__(self, name, access_key=None, **kwargs):
        self.name = safeDataKey(name)
        if access_key is None:
            self.access_key = self.name
        else:
            self.access_key = safeDataKey(access_key)
        for var_name in kwargs.keys():
            setattr(self, var_name, kwargs[var_name])

    def get(self, var_name, default=None):
        return self.__dict__.get(var_name, default)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def fullObjectPath(hdf5_object):
    path = [hdf5_object.name, ]
    parent = hdf5_object.parent
    while parent.name != '/':
        path.append(parent.name)
        parent = parent.parent
    if len(path) > 1:
        path.reverse()
        return '.'.join(path)
    elif len(path) == 1:
        return path[0]
    else:
        return 'file'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

WALK_ERRMSG = "%s has no child named '%s'"

def dottedKey(key):
    if key.startswith('/'): return key[1:].replace('/','.')
    return key.replace('/','.')

def walkForKeys(hdf5_object, include_datasets=True, include_groups=True):
    keys = [ ]
    for obj in hdf5_object.values():
        if isinstance(obj, h5py.Dataset):
            if include_datasets: keys.append(dottedKey(obj.name))
        else:
            if include_groups: keys.append(dottedKey(obj.name))
            for key in walkForKeys(obj, include_datasets, include_groups):
                keys.append(dottedKey(key))
    keys.sort()
    return tuple(keys)

def walkToObject(root_object, object_key):
    if isinstance(object_key, basestring):
        path = [safeDataKey(key) for key in object_key.split('.')]
    else: path = [safeDataKey(key) for key in object_key]
    try:
        _object = root_object[path[0]]
    except KeyError:
        raise KeyError, WALK_ERRMSG % (fullObjectPath(root_object),path[0])
    if len(path) == 1: return _object
    else:
        return walkToObject(_object, path[1:])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class HDF5DataFileMixin:
    """ Mixin class that reads, transforms and subsets data arrays in
    HDF5-encoded files.
    """

    def assertDatasetObject(self, _object):
        if not isinstance(_object, h5py.Dataset):
            errmsg = "Object at '%s' is not an HDF5 dataset."
            raise TypeError, errmsg % fullObjectPath(_object)

    def assertFileObject(self, _object):
        if _object.name not in ('/',''):
            errmsg = "Object at '%s' is not an HDF5 file."
            raise TypeError, errmsg % fullObjectPath(_object)

    def assertGroupObject(self, _object):
        if isinstance(_object, h5py.Dataset):
            errmsg = "Object at '%s' is not an HDF5 group."
            raise TypeError, errmsg % fullObjectPath(_object)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _getData_(self, parent, dataset_name, include_attributes=False,
                        **kwargs):
        dataset = self._getDataset_(parent, dataset_name)
        indexes = kwargs.get('indexes',None)
        if indexes is not None and len(indexes[0]) > 0:
            data = dataset.value[indexes]
        else: data = dataset.value
        if include_attributes: return (data, dict(dataset.attrs))
        else: return data

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _createDataset_(self, parent, dataset_name, numpy_array, attributes,
                        **kwargs):
        """ Creates a new dataset in the data file and returns a pointer to
        it. Raises IOError exception if the dataset already exists.
        """
        dataset_key = safeDataKey(dataset_name)
        if dataset_key in parent.keys():
            errmsg = "'%s' dataset already exists in current data file."
            raise IOError, errmsg % dataset_name

        create_args = { }
        for arg_name in kwargs:
            create_args[safe_name(arg_name)] = kwargs[arg_name]

        if 'maxshape' in create_args:
            if 'dtype' not in create_args:
                raise IOError, "'dtype' is required for extendable datasets."
            if len(numpy_array) != len(create_args['maxshape']):
                errmg = '3rd argument must be the initial shape of the array.'
                raise IOError, errmsg
            initial_shape = numpy_array
            dataset = parent.create_dataset(dataset_key, initial_shape,
                                            **create_args)
        else:
            if 'dtype' not in create_args\
            and numpy_array.dtype == N.dtype(object):
                create_args['dtype'] = h5py.new_vlen(str)
            
            dataset = parent.create_dataset(dataset_key, data=numpy_array,
                                            **create_args)
 
        for attr_name, attr_value in attributes.items():
            if attr_name != 'dtype' and attr_value is not None:
                dataset.attrs[safeDataKey(attr_name)] = safevalue(attr_value)

        return dataset

    def _deleteDatasetAttribute_(self, parent, dataset_name, attr_name):
        dataset = self._getDataset_(parent, dataset_name)
        self._deleteObjectAttribute_(dataset, attr_name)

    def _getDataset_(self, parent, dataset_name):
        """ Returns the dataset indicated by dataset_key.
        """
        _object = self._getObject_(parent, dataset_name)
        self.assertDatasetObject(_object)
        return _object

    def _getDatasetAttribute_(self, parent, dataset_name, attr_name):
        """ Returns a the value of a single attribute of the dataset
        indicated by dataset_key.
        """
        dataset = self._getDataset_(parent, dataset_name)
        try:
            return self._getObjectAttribute_(dataset, attr_name)
        except Exception as e:
            errmsg = "ERROR retrieving attribute '%s' from dataset '%s'"
            e.args = (errmsg % (attr_name, dataset_name),) + e.args
            raise e
    _getDatasetAttr_ = _getDatasetAttribute_

    def _getDatasetAttributes_(self, parent, dataset_name):
        """ Returns a the value of a single attribute of the dataset
        indicated by dataset_key.
        """
        return dict(self._getDataset_(parent, dataset_name).attrs)
    _getDatasetAttrs_ = _getDatasetAttributes_

    def _getDatasetKeys_(self, hdf5_object):
        """ Returns a tuple with the list of the keys for all datasets in
        the HDF5 object.
        """
        keys = [ key for key in hdf5_object.keys() 
                 if isinstance(hdf5_object[key], h5py.Dataset) ]
        keys.sort()
        return tuple(keys)

    def _getDatasetShape_(self, parent, dataset_name):
        """ Returns a dictionary of attr_name/attr_value pairs for all
        setable attributes of the dataset indicates by dataset_key.
        """
        return self._getDataset_(parent, dataset_name).shape

    def _getDatasetType_(self, parent, dataset_name):
        """ Returns a dictionary of attr_name/attr_value pairs for all
        setable attributes of the dataset indicates by dataset_key.
        """
        return self._getDataset_(parent, dataset_name).dtype

    def _setDatasetAttribute_(self, parent, dataset, attr_name, attr_value):
        """ Returns a dictionary of attr_name/attr_value pairs for all
        setable attributes of the dataset indicates by dataset_key.
        """
        dataset = self._getDataset_(parent, dataset_name)
        self._setObjectAttributes_(dataset, attr_name, attr_value)

    def _setDatasetAttributes_(self, parent, dataset, attr_dict):
        dataset = self._getDataset_(parent, dataset_name)
        self._setObjectAttributes_(dataset, attr_dict)

    def _updateDataset_(self, parent, dataset_name, numpy_array, attributes,
                        **kwargs):
        """ Update a dataset in the data file. If the dataset does not exist,
        it is created. Returns a pointer to the dataset.
        """
        dataset_key = safeDataKey(dataset_name)
        if dataset_key not in parent.keys():
            errmsg = "'%s' dataset is not in current data file."
            raise IOError, errmsg % dataset_name

        if len(numpy_array.shape) == 3:
            parent[dataset_key][:,:,:] = numpy_array[:,:,:]
        elif len(numpy_array.shape) == 2:
            parent[dataset_key][:,:] = numpy_array[:,:]
        elif len(numpy_array.shape) == 1:
            parent[dataset_key][:] = numpy_array[:]

        dataset = parent[dataset_key]
        for attr_name, attr_value in attributes.items():
            try:
                dataset.attrs[safeDataKey(attr_name)] = safevalue(attr_value)
            except Exception as e:
                errmsg = "Could not set attribute '%s' to '%s' for dataset '%s'"
                ds_name = dataset.name
                if ds_name.startswith('/'): ds_name = ds_name[1:]
                errmsg = errmsg % (attr_name, str(attr_value), ds_name)
                e.args = (errmsg,) + e.args
                raise

        return dataset
    
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _closeFile_(self, data_file):
        """ Closes the file-like object passed by data_file.
        """
        self.assertFileObject(data_file)
        data_file.close()

    def _deleteFileAttribute_(self, data_file, attr_name):
        self.assertFileObject(data_file)
        return self._deleteObjectAttribute_(date_file, attr_name)

    def _getFileAttribute_(self, data_file, attr_name):
        self.assertFileObject(data_file)
        return self._getObjectAttribute_(data_file, attr_name)

    def _getFileAttributes_(self, data_file):
        self.assertFileObject(data_file)
        return self._getObjectAttributes_(data_file)

    def _openFile_(self, filepath, mode):
        """ Returns a pointer to an instance of a file-like object for
        accessing data in 'filepath'.
        """
        try:
            return h5py.File(filepath, mode)
        except:
            print 'Unable to open file in mode %s : %s' % (mode, filepath)
            raise

    def _setFileAttribute_(self, data_file, attr_name, attr_value):
        self.assertFileObject(data_file)
        self._setObjectAttribute_(data_file, attr_name, attr_value)

    def _setFileAttributes_(self, data_file, attr_dict):
        self.assertFileObject(data_file)
        self._setObjectAttributes_(data_file, attr_dict)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _createGroup_(self, parent, group_name, **kwargs):
        """ Creates a new group in the parent and returns a pointer to
        it. Raises IOError exception if the group already exists.
        """
        group_key = safeDataKey(group_name)
        if group_key in parent.keys():
            errmsg = "'%s' group already exists in %s"
            raise IOError, errmsg % (group_name, fullObjectPath(parent))

        group = parent.create_group(group_name)
        if kwargs:
            for attr_name, attr_value in kwargs.items():
                self._setObjectAttribute_(group, attr_name, attr_value)
        return group

    def _deleteGroupAttribute_(self, parent, group_name, attr_name):
        group = self._getGroup_(parent, group_name)
        return self._deleteObjectAttribute_(group, attr_name)

    def _getGroup_(self, parent, group_name):
        """ Returns the dataset indicated by dataset_key.
        """
        _object = self._getObject_(parent, group_name)
        self.assertGroupObject(_object)
        return _object

    def _getGroupAttribute_(self, parent, group_name, attr_name):
        group = self._getGroup_(parent, group_name)
        return self._getObjectAttribute_(group, attr_name)

    def _getGroupAttributes_(self, group_name):
        group = self._getGroup_(parent, group_name)
        return self._getObjectAttributes_(group)

    def _setGroupAttribute_(self, parent, group_name, attr_name, attr_value):
        group = self._getGroup_(parent, group_name)
        self._setObjectAttribute_(group, attr_name, attr_value)

    def _setGroupAttributes_(self, parent, group_name, attr_dict):
        group = self._getGroup_(parent, group_name)
        self._setObjectAttributes_(group, attr_dict)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _deleteObject_(self, parent, object_key):
        """ deletes the object indicated by object_key.
        """
        key = safeDataKey(object_key)
        if key in parent.keys(): del parent[key]

    def _deleteObjectAttribute_(self, _object, attr_name):
        """ Deletes an attribute of an object.
        """
        try:
            del _object.attrs[safeDataKey(attr_name)]
        except Exception as e:
            errmsg = "Could not delete attribute '%s' of object '%s'"
            obj_name = fullObjectPath(_object)
            if obj_name.startswith('/'): obj_name = obj_name[1:]
            errmsg = errmsg % (attr_name, obj_name)
            e.args = (errmsg,) + e.args
            raise

    def _getObject_(self, parent, object_key):
        """ Returns the object indicated by object_key.
        """
        try:
            return parent[safeDataKey(object_key)]
        except KeyError as e:
            errmsg = "HDF5 file does not have a data object named '%s'"
            e.args = (errmsg % object_key,) + e.args
            raise e
        except Exception as e:
            errmsg = "Error during attempt to access data object named '%s'"
            e.args = (errmsg % object_key,) + e.args
            raise e

    def _getObjectAttribute_(self, _object, attr_name):
        """ Returns a the value of a single attribute of an object
        """
        try:
            return _object.attrs[safeDataKey(attr_name)]
        except Exception as e:
            obj_name = fullObjectPath(_object)
            if obj_name.startswith('/'): obj_name = obj_name[1:]
            errmsg = "ERROR retrieving attribute '%s' from object '%s'"
            e.args = (errmsg % (attr_name, obj_name),) + e.args
            raise e

    def _getObjectAttributes_(self, _object):
        """ Returns a dictionary of attr_name/attr_value pairs for all
        setable attributes of the object.
        """
        return safedict(dict(_object.attrs), safe_values=True)

    def _getObjectKeys_(self, _object):
        """ Returns a tuple with a list keys for all contained objects.
        """
        if hasattr(_object,'keys'):
            keys = _object.keys()
            keys.sort()
            return tuple(keys)
        else:
            errmsg = "%s object at '%s' does not support children"
            raise LookupError, errmsg % (_object.__class__.__name__,
                                         fullObjectPath(_object))

    def _getObjectShape_(self, _object):
        """ Returns a dictionary of attr_name/attr_value pairs for all
        setable attributes of the dataset indicates by dataset_key.
        """
        if isinstance(_object, h5py.Dataset): return _object.shape()
        else: return len(_object.keys())

    def _setObjectAttribute_(self, _object, attr_name, attr_value):
        """ Returns a dictionary of attr_name/attr_value pairs for all
        setable attributes of the dataset indicates by dataset_key.
        """
        try:
            _object.attrs[safeDataKey(attr_name)] = safestring(attr_value)
        except Exception as e:
            errmsg = "Could not set attribute '%s' to '%s' for object '%s'"
            obj_name = fullObjectPath(_object)
            if obj_name.startswith('/'): obj_name = obj_name[1:]
            errmsg = errmsg % (attr_name, str(attr_value), obj_name)
            e.args = (errmsg,) + e.args
 
    def _setObjectAttributes_(self, _object, attr_dict):
        for attr_name, attr_value in attr_dict.items():
            self._setObjectAttribute_(_object, attr_name, attr_value)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class HDF5DataFileManager(HDF5DataFileMixin, object):

    def __init__(self, hdf5_filepath=None, mode='r'):
        self.hdf5_filepath = hdf5_filepath
        self.hdf5_file = None
        self.hdf5_file_mode = mode
        self.dataset_names = ()
        self.open_container = ('',None)
        if hdf5_filepath is not None:
            self.openFile(hdf5_filepath, mode)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def copy(self, to_object, object_names=()):
        if object_names:
            for object_name in object_names:
                self._hdf5_file.copy(object_name, to_object)
        else: # none specified, copy all contained objects
            for object_name in self._hdf5_file.keys():
                self._hdf5_file.copy(object_name, to_object)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getData(self, dataset_names, include_attributes=False, **kwargs):
        self.assertFileOpen()
        if isinstance(dataset_names, (tuple,list)):
            data = [ ]
            for name in dataset_names:
                name, parent = self._keyToNameAndParent(self.hdf5_file,name)
                _data = self._getData_(parent,name,include_attributes,**kwargs)
                data.append(_data)
            return tuple(data)
        else:
            name,parent = self._keyToNameAndParent(self.hdf5_file,dataset_names)
            return self._getData_(parent,name,include_attributes,**kwargs)

    def getDataWhere(self, dataset_names, criteria=None,
                           include_attributes=False):
        datasets = [ ]
        if criteria:
            indexes = self._where(criteria)
            if indexes and len(indexes[0]) > 0:
                return self.getData(dataset_names, include_attributes,
                                    indexes=indexes)
            else:
                errmsg = 'No entries meet search criteria : %s'
                raise ValueError, errmsg % str(criteria)
        return self.getData(dataset_names, include_attributes)

    def getSerialData(self, dataset_names, serial_criteria,
                            include_attributes=False, **kwargs):
        data = self.getData(dataset_names, True, **kwargs)
        if isinstance(dataset_names, (tuple,list)):
            data == list(data)
            for indx in range(len(dataset_names)):
                _array_, attrs = data[indx]
                serial_attrs = serial_criteria[indx]
                _array_, attrs = self._serialize(_array_, attrs, serial_attrs)
                if include_attributes: data[indx] = (_array_, attrs)
                else: data[indx] = _array_
            return tuple(data)
        else:
            data, attrs = self._serialize(data[0], data[1], serial_criteria)
            if include_attributes: return data, attrs
            else: return data

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def createDataset(self, dataset_name, numpy_array, attributes={}, **kwargs):
        self.assertFileWritable()

        attrs = safedict(attributes)
        if 'created' not in attrs:
            attrs['created'] = self._timestamp()

        name, parent = self._keyToNameAndParent(self.hdf5_file, dataset_name)
        dataset = self._createDataset_(parent, name, numpy_array, attrs,
                                       **kwargs)
        self._registerDatasetName(fullObjectPath(dataset))
        return dataset

    def createExtensibleDataset(self, dataset_name, initial_shape, max_shape,
                                      dtype, fill_value, attributes={},
                                      chunk_size=None, compression='lzf'):
        self.assertFileWritable()

        attrs = safedict(attributes)
        if 'created' not in attrs:
            attrs['created'] = self._timestamp()

        name, parent = self._keyToNameAndParent(self.hdf5_file, dataset_name)
        dataset = self._createDataset_(parent, name, initial_shape, attrs,
                                       dtype=dtype, maxshape=max_shape, 
                                       fillvalue=fill_value, chunks=chunk_size,
                                       compression=compression)
        self._registerDatasetName(fullObjectPath(dataset))
        return dataset

    def datasetExists(self, dataset_name, parent_name=None):
        return dataset_name in self.listDatasets(parent_name)

    def getDatasetNames(self):
        return self.dataset_names

    def insertData(self, dataset_name, indexes, data):
        dataset = self.getdataset(dataset_name)
        if isinstance(indexes, int):
            dataset[indexes] = data
        elif isinstance(indexes, (tuple,list)):
            index_strings = [ ]
            for item in indexes:
                if isinstance(indexes, (tuple,list)):
                    index_strings.append(':'.join([str(it) for it in item]))
                else:
                    index_strings.append(str(item))
            update_string = 'dataset[%s] = data' % ','.join(index_strings)
            eval(update_string)
        else:
            TypeError, 'Invalid type for indexes : %s' % type(indexes)

    def listDatasets(self, parent_name=None):
        self.assertFileOpen()
        if parent_name is None: parent = self.hdf5_file
        else: parent = self.getObject(parent_name)
        names = [ ]
        for key in walkForKeys(parent, True, False):
            if key.startswith('/'): names.append(key[1:])
            else: names.append(key)
        return tuple(names)

    def replaceDataset(self, dataset_name, data, attributes):
        self.deleteDataset(dataset_name)
        attributes['updated'] = self._timestamp()
        self.createDataset(dataset_name, data, attributes)

    def resizeDataset(self, dataset_name, max_index):
        self.assertFileOpen()
        dataset = self.getDataset(dataset_name)
        old_shape = self.hdf5_file[dataset_name].shape
        new_size = (max_index,) + old_shape[1:]
        self.hdf5_file[dataset_name].resize(new_size)

    def updateDataset(self, dataset_name, numpy_array, attributes={}, **kwargs):
        self.assertFileWritable()
        
        name, parent = self._keyToNameAndParent(self.hdf5_file, dataset_name)
        if name in self.dataset_names:
            dataset = self._updateDataset_(parent, name, numpy_array,
                                           attributes, **kwargs)
        else:
            dataset = self._createDataset_(parent, name, numpy_array, 
                                           attributes, **kwargs)
            self._registerDatasetName(fullObjectPath(dataset))
        return dataset

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def deleteDataset(self, dataset_name):
        self.deleteObject(dataset_name)

    def deleteDatasetAttribute(self, dataset_name, attr_name):
        self.assertFileWritable()
        self._deleteObjectAttribute_(self.getDataset(dataset_name), attr_name)

    def getDataset(self, dataset_name):
        self.assertFileOpen()
        _object = self.getObject(dataset_name)
        self.assertDatasetObject(_object)
        return _object

    def getDatasetAttribute(self, dataset_name, attr_name):
        self.assertFileOpen()
        return self._getObjectAttribute_(self.getDataset(dataset_name),
                                         attr_name)

    def getDatasetAttributes(self, dataset_name):
        self.assertFileOpen()
        return self._getObjectAttributes_(self.getDataset(dataset_name))
    getDatasetAttrs = getDatasetAttributes

    def getDatasetShape(self, dataset_name):
        self.assertFileOpen()
        return self.getDataset(dataset_name).shape

    def getDatasetType(self, dataset_name):
        self.assertFileOpen()
        return self.getDataset(dataset_name).dtype

    def setDatasetAttribute(self, dataset_name, attr_name, attr_value):
        self.assertFileWritable()
        self._setObjectAttribute_(self.getDataset(dataset_name),
                                  attr_name, attr_value)

    def setDatasetAttributes(self, dataset_name, **kwargs):
        self.assertFileWritable()
        self._setObjectAttributes_(self.getDataset(dataset_name), kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def assertFileOpen(self):
        if self.hdf5_file is None: raise IOError, 'No open HDF5 file.'

    def assertFileWritable(self):
        if self.hdf5_file is None: raise IOError, 'No open HDF5 file.'
        if self.hdf5_file_mode not in ('w','a'): 
            raise IOError, 'HDF5 file is not writable.'

    def closeFile(self):
        if self.hdf5_file is not None:
            self._closeFile_(self.hdf5_file)
            self.hdf5_file = None
            self.hdf5_file_mode = None
        self.open_container = ('',None)

    def deleteFileAttribute(self, attr_name):
        self.assertFileWritable()
        self._deleteFileAttribute_(self.hdf5_file, attr_name)

    def getFileAttribute(self, attr_name):
        self.assertFileOpen()
        return self._getFileAttribute_(self.hdf5_file, attr_name)

    def getFileAttributes(self):
        self.assertFileOpen()
        return self._getFileAttributes_(self.hdf5_file)

    def getFilePath(self):
        return self.hdf5_filepath

    def openFile(self, hdf5_filepath=None, mode='r'):
        self.closeFile()
        if hdf5_filepath is None:
            self.hdf5_file = self._openFile_(self.hdf5_filepath, mode)
        else:
            self.hdf5_file = self._openFile_(hdf5_filepath, mode)
            self.hdf5_filepath = hdf5_filepath
        self.hdf5_file_mode = mode
        self.dataset_names = self._getDatasetKeys_(self.hdf5_file)

    def setFileAttribute(self, attr_name, attr_value):
        self.assertFileWritable()
        self._setFileAttribute_(self.hdf5_file, attr_name, attr_value)

    def setFileAttributes(self, **kwargs):
        self.assertFileWritable()
        for attr_name, attr_value in kwargs.items():
            self._setFileAttribute_(self.hdf5_file, attr_name, attr_value)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def createGroup(self, group_name, attributes={}):
        """ Creates a new group in the parent and returns a pointer to
        it. Raises IOError exception if the group already exists.
        """
        name, parent = self._keyToNameAndParent(self.hdf5_file, group_name)
        if name in parent.keys():
            errmsg = "'%s' group already exists in current data file."
            raise IOError, errmsg % group_name

        group = self._createGroup_(parent, name, **attributes)
        self.open_container = (fullObjectPath(group), group)
        return group

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def deleteGroup(self, group_name):
        self.deleteObject(group_name)

    def deleteGroupAttribute(self, group_name, attr_name):
        self.assertFileWritable()
        group = self.getGroup(group_name)
        self._deleteObjectAttribute_(self.getGroup(group_name), attr_name)

    def getGroup(self, group_name):
        self.assertFileOpen()
        _object = self.getObject(group_name)
        self.assertGroupObject(_object)
        return _object

    def getGroupAttribute(self, group_name, attr_name):
        self.assertFileOpen()
        return self._getObjectAttribute_(self.getGroup(group_name), attr_name)

    def getGroupAttributes(self, group_name):
        self.assertFileOpen()
        return self._getObjectAttributes_(self.getGroup(group_name))

    def groupExists(self, group_name, parent_name=None):
        return group_name in self.listGroups(parent_name)

    def listGroups(self, parent_name=None):
        self.assertFileOpen()
        if parent_name is None: parent = self.hdf5_file
        else: parent = self.getObject(parent_name)
        return walkForKeys(parent, False, True)

    def setGroupAttribute(self, group_name, attr_name, attr_value):
        self.assertFileWritable()
        self._setObjectAttribute_(self.getGroup(group_name), attr_name,
                                  attr_value)

    def setGroupAttributes(self, group_name, **kwargs):
        self.assertFileWritable()
        self._setObjectAttributes_(self.getGroup(group_name), kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def deleteObject(self, object_name):
        self.assertFileWritable()
        self._deleteObject_(self.hdf5_file, object_name)

    def deleteObjectAttribute(self, object_name, attr_name):
        self._deleteObjectAttribute_(self.getObject(object_name), attr_name)

    def getObject(self, object_name):
        self.assertFileOpen()
        object_path = self._keyToPath(object_name)
        if self.open_container[1] is not None:
            if self.open_container[0] == self._pathToKey(object_path[:-1]):
               return self.open_container[1][object_path[-1]]
            try:
                return walkToObject(self.open_container[1], object_path)
            except KeyError:
                pass
        _object = walkToObject(self.hdf5_file, object_path)
        self.open_container = (self._pathToKey(object_path[:-1]),_object.parent)
        return _object

    def getObjectAttribute(self, object_name, attr_name):
        self.assertFileOpen()
        return self._getObjectAttribute_(self.getObject(object_name), attr_name)

    def getObjectAttributes(self, object_name):
        self.assertFileOpen()
        return self._getObjectAttributes_(self.getObject(object_name))

    def getObjectShape(self, object_name):
        self.assertFileOpen()
        return self._getObjectShape_(self.getObject(object_name))

    def opjectExists(self, object_name, parent_name=None):
        return object_name in self.listObjects(parent_name)

    def listObjects(self, parent_name=None):
        self.assertFileOpen()
        if parent_name is None: parent = self.hdf5_file
        else: parent = self.getObject(parent_name)
        names = list(self._getObjectKeys_(self.getObject(object_name)))
        names.sort()
        return names
    
    def setObjectAttribute(self, object_name, attr_name, attr_value):
        self.assertFileWritable()
        _object = self.getObject(object_name)
        self._setObjectAttribute_(_object, attr_name, attr_value)

    def setObjectAttributes(self, object_name, **kwargs):
        self.assertFileWritable()
        self._setObjectAttributes_(self.getObject(object_name), kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _keysToPaths(self, object_keys):
        if isinstance(object_keys, basestring):
            return (self._keyToPath(object_keys),)
        elif isinstance(object_keys, (tuple,list)):
            return tuple([ self._keyToPath(key) for key in object_keys ])
        else:
            errmsg = 'Invalid type for object keys %s : %s'
            raise TypeError, errmsg % (object_keys.__class__.__name__,
                                       str(object_keys))

    def _keyToPath(self, object_key):
        if isinstance(object_key, DatasetKey):
            return (object_key.name,)
        if isinstance(object_key, (tuple,list)):
            return tuple(object_key)
        elif isinstance(object_key, basestring):
            if '.' in object_key:
                return tuple(object_key.split('.'))
            else: return (object_key,)
        else:
            errmsg = 'Invalid type for object name %s : %s'
            raise TypeError, errmsg % (object_key.__class__.__name__,
                                       str(object_key))

    def _keyToNameAndParent(self, root_object, object_key):
        object_path = self._keyToPath(object_key)
        if len(object_path) == 1:
            return object_path[0], root_object
        else:
            parent_path = '.'.join(object_path[:-1])
            if self.open_container[0] != parent_path:
                parent = walkToObject(root_object, object_path[:-1])
                self.open_container = (parent_path, parent)
            return object_path[-1], self.open_container[1]

    def _pathToKey(self, object_path):
        if isinstance(object_path, DatasetKey):
            object_path = object_path.name
        if isinstance(object_path, basestring):
            return object_path
        elif isinstance(object_path, (tuple,list)):
            return '.'.join(object_path)
        else:
            errmsg = 'Invalid type for object path %s : %s'
            raise TypeError, errmsg % (object_path.__class__.__name__,
                                       str(object_path))

    def _parentFromKey(self, root_object, object_key):
        object_path = self._keyToPath(object_key)
        return self._parentFromPath(root_object, object_path)

    def _parentFromPath(self, root_object, object_path):
        if len(object_path) == 1:
            return root_object
        else:
            parent_path = '.'.join(object_path[:-1])
            if self.open_container[0] != parent_path:
                return walkToObject(root_object, object_path[:-1])
            return self.open_container[1]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerDatasetName(self, dataset_name):
        if dataset_name not in self.dataset_names:
            names = list(self.dataset_names)
            names.append(dataset_name)
            names.sort()
            self.dataset_names = tuple(names)

    def _timestamp(self, date_time=None):
        if date_time is None:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            return date_time.strftime('%Y-%m-%d %H:%M:%S')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _serialize(self, data, attrs, serial_attrs):
        serial_type = serial_attrs[0]
        if serial_type == float:
            if data.dtype.kind != 'f': data = N.array(data, dtype=float)
        elif serial_type == int:
            if data.dtype.kind != 'i': data = N.array(data, dtype=int)
        elif isinstance(serial_type, basestring):
            if N.dtype(serial_type) != data.dtype:
                data = N.array(data, dtype=serial_type)

        missing = attrs['missing']
        serial_missing = serial_attrs[2]
        if N.isfinite(missing):
            if serial_missing != missing:
                data[N.where(data == missing)] = serial_missing
                attrs['missing'] = serial_missing
        elif N.isnan(missing):
            if not N.isnan(serial_missing):
                data[N.where(N.isnan(data))] = serial_missing
                attrs['missing'] = serial_missing
        elif N.isinf(missing):
            if not N.isinf(serial_missing):
                data[N.where(N.isinf(data))] = serial_missing
                attrs['missing'] = serial_missing

        if serial_attrs[1] != attrs['units']:
            convert = getConversionFunction(attrs['units'], serial_attrs[1])
            if convert is not None: data = convert(data)
            attrs['units'] = serial_attrs[1]

        return data, attrs

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _where(self, criteria):
        if criteria:
            errmsg = 'Key for filter criteria is not a valid dataset name : %s'
            where = None
            constraint_data = { }
            dataset_names = self.listDatasets()

            if isinstance(criteria, dict):
                for key, constraint in criteria.items():
                    if constraint is None: continue
                    if key == 'bbox':
                        constraint_data['lon'] = self.getData('lon')
                        constraint_data['lat'] = self.getData('lat')
                    elif key in dataset_names:
                        if key not in constraint_data:
                            constraint_data[key] = self.getData(key)
                    else: raise KeyError, errmsg % key
                if constraint_data:
                    where = dictToWhere(criteria)

            elif isinstance(criteria, (list,tuple)):
                for rule in criteria:
                    key = rule[0]
                    if key in dataset_names:
                        if key not in constraint_data:
                            constraint_data[key] = self.getData(key)
                    else: raise KeyError, errmsg % key
                if constraint_data:
                    where = listToWhere(criteria)

            if where is not None:
                return eval(where, globals(), constraint_data)

        return None


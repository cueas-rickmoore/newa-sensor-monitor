""" HDF5GridManagerMixin class for accessing data from HDF5 encoded grid files.
"""

import os
from datetime import datetime

from rccpy.hdf5.manager import fullObjectPath
from rccpy.hdf5.manager import HDF5DataFileManager
from rccpy.utils.data import safedict

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config as CONFIG
CONFIG_ELEMENTS = CONFIG.elements.keys()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getSerialCriteria(dataset_name):
    if '.' in dataset_name:
        parts = dataset_name.split('.')
        if parts[-1] in ('date','value') :
            if parts[-2] in CONFIG_ELEMENTS:
                return CONFIG.elements[parts[-2]].serial_type
        else:
            if parts[-1] in CONFIG_ELEMENTS:
                return CONFIG.elements[parts[-1]].serial_type
    if dataset_name in CONFIG_ELEMENTS:
        return CONFIG.elements[dataset_name].serial_type
    else: return None

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ObsnetDataFileManager(HDF5DataFileManager):

    def __init__(self, filepath=None, mode='r'):
        HDF5DataFileManager(self, filepath, mode)
        self.filepath = filepath

    def getSerialData(self, dataset_names, include_attributes=False, **kwargs):

        data = self.getData(dataset_names, True, **kwargs)
        if isinstance(dataset_names, (tuple,list)):
            data == list(data)
            for indx in range(len(dataset_names)):
                serial_attrs = getSerialCriteria(dataset_names[indx])
                if serial_attrs is not None:
                    _array_, attrs = data[indx]
                    _array_, attrs = self._serialize(_array_, attrs, serial_attrs)
                    if include_attributes: data[indx] = (_array_, attrs)
                    else: data[indx] = _array_
            return tuple(data)
        else:
            serial_attrs = getSerialCriteria(dataset_names)
            if serial_attrs is not None:
                data, attrs = self._serialize(data[0], data[1], serial_attrs)
            if include_attributes: return data, attrs
            else: return data

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def createDataset(self, dataset_name, numpy_array, attributes={}, **kwargs):
        self.assertFileWritable()

        attrs = self._verfiyCreateAttributes(dataset_name, attributes,
                                             numpy_array)
        name, parent = self._keyToNameAndParent(self.hdf5_file, dataset_name)
        dataset = self._createDataset_(parent, name, numpy_array, attrs,
                                       **kwargs)
        self._registerDatasetName(fullObjectPath(dataset))
        return dataset

    def createExtensibleDataset(self, dataset_name, initial_shape, max_shape,
                                      dtype, fill_value, attributes={},
                                      chunk_size=None, compression='lzf'):
        self.assertFileWritable()

        attrs = self._verfiyCreateAttributes(dataset_name, attributes,
                                             numpy_array)
        name, parent = self._keyToNameAndParent(self.hdf5_file, dataset_name)
        dataset = self._createDataset_(parent, name, initial_shape, attrs,
                                       dtype=dtype, maxshape=max_shape, 
                                       fillvalue=fill_value, chunks=chunk_size,
                                       compression=compression)
        self._registerDatasetName(fullObjectPath(dataset))
        return dataset

    def _verfiyCreateAttributes(self, dataset_name, attributes, numpy_array):
        attrs = safedict(attributes)
        if 'created' not in attrs:
            attrs['created'] = self._timestamp()
        
        is_date = dataset_name.endswith('.date')
        is_value = dataset_name.endswith('.value')
        
        path = dataset_name.split('.')
        if is_date or is_value:
            element = path[-2]
            if element in CONFIG_ELEMENTS:
                if 'frequency' not in attrs:
                    attrs['frequency'] = CONFIG.elements[element].raw_type[3]
                if 'interval' not in attrs:
                    attrs['interval'] = CONFIG.elements[element].raw_type[4]

        else: element = path[-1]

        if is_value:
            if element in CONFIG_ELEMENTS:
                element_config = CONFIG.elements[element]
                if 'description' not in attrs:
                    attrs['description'] = element_config.description
                if 'missing' not in attrs:
                    attrs['missing'] = element_config.raw_type[2]
                if 'units' not in attrs:
                    attrs['units'] = element_config.raw_type[1]
                if 'value_type' not in attrs: 
                    attrs['value_type'] = element_config.value_type
        elif is_date:
            if numpy_array.dtype.kind == 'i' and 'date_formula' not in attrs:
                if attrs['frequency'] == 'hour':
                    attrs['date_formula'] = 'year*1000000 + month*10000 + day*100 + hour'
                elif attrs['frequency'] == 'day':
                    attrs['date_formula'] = 'year*10000 + month*100 + day'
                elif attrs['frequency'] == 'month':
                    attrs['date_formula'] = 'year*100 + month'
            if 'description' not in attrs:
                if attrs['frequency'] == 'hour':
                    attrs['description'] = 'Year,Month,Day,Hour'
                elif attrs['frequency'] == 'day':
                    attrs['description'] = 'Year,Month,Day'
                elif attrs['frequency'] == 'month':
                    attrs['description'] = 'Year,Month'

        return attrs


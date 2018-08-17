""" Abstract base classes that define the minimum API for array file managers.
"""

from copy import deepcopy

import numpy as N

from .manager import DataFileManager
from .geo import GeoDataFileMixin

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ArrayFileManager(DataFileManager):
    """ Abstract base class that defines the minimum API for array file
    managers.
    """

    def __init__(self, managed_filepath, keep_open=False, allow_updates=False):
        DataFileManager.__init__(self, managed_filepath, keep_open=keep_open,
                                       allow_updates=allow_updates)
        # set default bounds to include entire dataset
        self.setIndexBounds()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getIndexBounds(self):
        """ Returns a tuple containg the minimum and maximum array indexes
        """
        return (self.min_index, self.max_index)

    def setIndexBounds(self, min_index=None, max_index=None):
        self.min_index = min_index
        self.max_index = max_index

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _dataSubset(self, dataset_key, numpy_array):
        if 'slice' in dataset_key:
            parts = dataset_key['slice'].split(':')
            if len(parts[0]) > 0:
                slice_start = int(parts[0])
            else:
                slice_start = None
            if len(parts[1]) > 0:
                slice_end = int(parts[1])
            else:
                slice_end = None
        else:
            slice_start = self.min_index
            slice_end = self.max_index

        if slice_start is None:
            if slice_end is None:
                return numpy_array
            return numpy_array[:slice_end]
        else:
            if slice_end is None:
                return numpy_array[slice_start:]
            return numpy_array[slice_start:slice_end]


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GeoArrayFileManager(GeoDataFileMixin, ArrayFileManager):
    """ Abstract base class that defines the minimum API for array file
    managers that support subsetting by geographic coordinates.
    """

    DATA_TYPES = deepcopy(ArrayFileManager.DATA_TYPES)
    DATA_TYPES['lon'] = N.dtype(float)
    DATA_TYPES['lat'] = N.dtype(float)

    DATA_UNITS = deepcopy(ArrayFileManager.DATA_UNITS)
    DATA_UNITS['lon'] = 'DD'
    DATA_UNITS['lat'] = 'DD'

    DESCRIPTIONS = deepcopy(ArrayFileManager.DESCRIPTIONS)
    DESCRIPTIONS['lon'] = 'longitude'
    DESCRIPTIONS['lat'] = 'latitude'

    MASKED = deepcopy(ArrayFileManager.MASKED)
    MASKED['lon'] =  N.nan
    MASKED['lat'] =  N.nan

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __init__(self,  managed_filepath, keep_open=False, allow_updates=False):
        ArrayFileManager.__init__(self, managed_filepath, keep_open=keep_open,
                                        allow_updates=allow_updates)
        self.lons, self.lats = self._initCoordinateLimits()

    def _initCoordinateLimits(self):
        """ Sets the absolute limts for lon/lat and index coordinates for
        grids present in the file.
        """
        # initialize index bounds
        self.indexes = None

        # capture lon,lat limits for grids in data file
        return GeoDataFileMixin._initCoordinateLimits(self)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getMapConfig(self):
        # set the basic projection paramaeters
        config = self.getProjectionParameters()
        config.update(self.getDataBounds())
        return config

    def getProjectionParameters(self):
        return { }

    def setLonLatBounds(self, bbox=None):
        self.indexes = None
        
        if bbox is not None:
            # indexes of all points within bounding box
            self.indexes = N.where( (self.lons >= bbox[0]) &
                                    (self.lats >= bbox[1]) &
                                    (self.lons <= bbox[2]) &
                                    (self.lats <= bbox[3]) )
        self.bounds = bbox
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def index2ll(self, x, y=None):
        """ Returns the lon/lat coordinates of the grid node at the x,y index
        point.
        """
        return self.lons[x], self.lats[x]

    def ll2index(self, lon, lat, max_radius=0.5):
        """ Returns the index (or indexes) of the array item(s) closest to the
        lon/lat coordinate point.
        NOTE: multiple array items will be returned ONLY if more than one item
              is EXACTLY the same distance from the import coordinates.
        """
        lons = self.lons
        lats = self.lats
        indexes = N.where( (lons == lon) and (lats == lat) )
        if len(indexes[0]) == 1:
            return indexes[0][0]
        elif len(indexes[0]) > 1:
            return indexes[0]

        for radius in N.arange(.1,max_radius+.1,.1):
            bbox = (lon-radius, lat-radius, lon+radius, lat+radius)
            indexes = N.where( (lons >= bbox[0]) & (lats >= bbox[1]) &
                               (lons <= bbox[2]) & (lats <= bbox[3]) )
            if len(indexes[0]) == 1:
                return indexes[0][0]
            elif len(indexes[0]) > 1:
                lon_diffs = lon - self.lons[indexes]
                lat_diffs = lat - self.lats[indexes]
                sum_of_squares = (lon_diffs*lon_diffs) + (lat_diffs*lat_diffs)
                distances = N.sqrt(sum_of_squares)
                dindexes = N.where(distances==distances.min())
                indexes = indexes[0][dindexes]
                if len(indexes[0]) == 1:
                    return indexes[0][0]
                return indexes[0]
        return None
    
    def ll2xy(self, lon, lat):
        """ Returns projected x,y coordinates that correspond to the lon/lat
        coordinate point.
        """
        if self.PROJECTION is not None:
            return self.PROJECTION.ll2xy(lon,lat)
        errmsg = "Cannot execute transform, 'PROJECTION' attribute has no value."
        raise AttributeError, errmsg

    def xy2ll(self, x, y):
        """ Returns the lat/lon coordinates that correspond to the preojected
        x/y coordniates.
        """
        if self.PROJECTION is not None:
            return self.PROJECTION.xy2ll(x,y)
        errmsg = "Cannot execute transform, 'PROJECTION' attribute has no value."
        raise AttributeError, errmsg



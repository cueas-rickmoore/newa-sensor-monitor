""" Mixin classes that define the minimum API for data file managers that
support subsetting by geographic coordinates.
"""

import numpy as N


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GeoDataFileMixin:
    """ Mixin class that defines the minimum API for data file managers that
    support subsetting by geographic coordinates.
    """

    PROJECTION = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getCoordinateLimits(self):
        limits = { }
        limits['min_avail_lon'] = self._min_avail_lon
        limits['max_avail_lon'] = self._max_avail_lon
        limits['min_avail_lat'] = self._min_avail_lat
        limits['max_avail_lat'] = self._max_avail_lat

    def getDataBounds(self):
        bounds = { }
        if self.bounds is None:
            bounds['llcrnrlon'] = self._min_avail_lon
            bounds['llcrnrlat'] = self._min_avail_lat
            bounds['urcrnrlon'] = self._max_avail_lon
            bounds['urcrnrlat'] = self._max_avail_lat
        else:
            bounds['llcrnrlon'] = self.bounds[0]
            bounds['llcrnrlat'] = self.bounds[1]
            bounds['urcrnrlon'] = self.bounds[2]
            bounds['urcrnrlat'] = self.bounds[3]
        return bounds

    def getLonLat(self):
        """ Returns lon, lat coordinate arrays.
        """
        self.openFile('r')
        try:
            lons,attrs = self.getRawData('lon')
            lats,attrs = self.getRawData('lat')
            self.conditionalClose()
        except IOError:
            self.conditionalClose()
            return self._projectLonLat_()
        except Exception:
            raise

        return N.array(lons,dtype=float), N.array(lats,dtype=float)

    def setLonLatBounds(self, bbox=None):
        msg = 'setLonLatBounds method not implemented for %s Class.' 
        raise NotImplementedError, msg % self.__class__.__name__

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _dataSubset(self, dataset_key, dataset):
        if self.indexes is not None:
            return dataset[self.indexes]
        else:
            return dataset

    def _initCoordinateLimits(self):
        """ Sets the absolute limts for lon/lat and index coordinates for
        grids present in the file.
        """
        # initialize index bounds
        self.bounds = None

        try:
            lons, attrs = self.getRawData('lon')
            lats, attrs = self.getRawData('lat')
        except:
            raise
            raise RuntimeError, 'No latitiude or longitude data vailable.'

        self._min_avail_lat = N.nanmin(lats)
        self._max_avail_lat = N.nanmax(lats)
        self._min_avail_lon = N.nanmin(lons)
        self._max_avail_lon = N.nanmax(lons)

        return lons, lats

    def _projectLonLat_(self):
        msg = '_projectLonLat_ method not implemented for %s Class.' 
        raise NotImplementedError, msg % self.__class__.__name__

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GeoGridFileManager(GeoDataFileMixin, GridFileManager):
    """ Abstract base class to define API for grid file managers.
    """

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __init__(self, managed_filepath, keep_open=False, allow_updates=False):
        GridFileManager.__init__(self, managed_filepath,  keep_open=keep_open,
                                       allow_updates=allow_updates)
        self._initCoordinateLimits()

    def _initCoordinateLimits(self):
        """ Sets the absolute limts for lon/lat and index coordinates for
        grids present in the file.
        """
        # capture lon,lat limits for grids in data file
        lons, lats = GeoDataFileMixin._initCoordinateLimits(self)

        # initialize index bounds
        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None
        self.col = None
        self.row = None

        # determine base x,y indexes for projection
        self._base_x, self._base_y = self.PROJECTION.ll2index(lons[0,0],
                                                              lats[0,0])

        # capture index limits for grids in data file
        self._min_avail_x = 0
        self._min_avail_y = 0
        if self.COORDINATE_ORDER == 'xy':
            self._max_avail_x = lons.shape[0] 
            self._max_avail_y = lons.shape[1]
        else:
            self._max_avail_x = lons.shape[1] 
            self._max_avail_y = lons.shape[0]

        return lons, lats

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getCoordinateLimits(self):
        limits = { }
        limits['min_avail_lon'] = self._min_avail_lon
        limits['max_avail_lon'] = self._max_avail_lon
        limits['min_avail_lat'] = self._min_avail_lat
        limits['max_avail_lat'] = self._max_avail_lat
        limits['max_avail_x'] = self._max_avail_x
        limits['min_avail_x'] = self._min_avail_x
        limits['max_avail_y'] = self._max_avail_y
        limits['min_avail_y'] = self._min_avail_y
        return limits

    def gridIndexBounds(self):
        if self.min_x is not None:
            min_x = max(self.min_x, self._min_avail_x)
            max_x = min(self.max_x+1, self._max_avail_x)
            min_y = max(self.min_y, self._min_avail_y)
            max_y = min(self.max_y+1, self._max_avail_y)
            return (min_x, max_x, min_y, max_y)
        else:
            return (self._min_avail_x, self._max_avail_x,
                    self._min_avail_y, self._max_avail_y)

    def setLonLatBounds(self, point_or_bbox=None):
        self.bounds = point_or_bbox
        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None
        self.col = None
        self.row = None
        if point_or_bbox is not None:
            if len(point_or_bbox) == 2:
                self.col, self.row = self.ll2index(*point_or_bbox)
            elif len(point_or_bbox) == 4:
                if self.REGULAR_GRID:
                    self._setBoundsForRegularGrid(point_or_bbox)
                else:
                    self._setBoundsForIrregularGrid(point_or_bbox)
            else:
                errmsg = "Invalid value for 'point_or_bbox'. It must contain "
                errmsg += "either a point (lon,lat) or a bounding box "
                errmsg += "(min_lon,min_lat,max_lon,max_lat)."
                raise ValueError, errmsg

    def _setBoundsForRegularGrid(self, point_or_bbox):
        x1, y1 = self.ll2index(*point_or_bbox[:2])
        x2, y2 = self.ll2index(*point_or_bbox[2:])
        self.min_x = x1
        self.max_x = x2
        self.min_y = y1
        self.max_y = y2

    def _setBoundsForIrregularGrid(self, point_or_bbox):
        lons, lats = self.getLonLat()
        indexes = N.where( (lons >= point_or_bbox[0]) &
                           (lons <= point_or_bbox[2]) &
                           (lats >= point_or_bbox[1]) &
                           (lats <= point_or_bbox[3]) )
        if self.COORDINATE_ORDER == 'xy':
            self.min_x = min(indexes[0])
            self.max_x = max(indexes[0])
            self.min_y = min(indexes[1])
            self.max_y = max(indexes[1])
        else:
            self.min_y = min(indexes[0])
            self.max_y = max(indexes[0])
            self.min_x = min(indexes[1])
            self.max_x = max(indexes[1])

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def index2ll(self, x, y):
        """ Returns the lon/lat coordinates of the grid node at the x,y index
        point.
        """
        if self.PROJECTION is not None:
            return self.PROJECTION.index2ll(x+self._base_x ,y+self._base_y)
        errmsg = "Cannot execute transform, 'PROJECTION' attribute has no value."
        raise AttributeError, errmsg

    def ll2index(self, lon, lat):
        """ Returns the x,y indexes of the grid node that is closest to the
        lon/lat coordinate point.
        """
        if self.PROJECTION is not None:
            x,y = self.PROJECTION.ll2index(lon,lat)
            return x-self._base_x, y-self._base_y
        errmsg = "Cannot execute transform, 'PROJECTION' attribute has no value."
        raise AttributeError, errmsg

    def ll2findex(self, lon, lat):
        """ Returns the floating point x,y indexes into the grid.
        """
        if self.PROJECTION is not None:
            x,y = self.PROJECTION.ll2findex(lon,lat)
            return x-self._base_x, y-self._base_y
        errmsg = "Cannot execute transform, 'PROJECTION' attribute has no value."
        raise AttributeError, errmsg

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _dataSubset(self, dataset_key, dataset):
        if self.COORDINATE_ORDER == 'xy':
            return getXYDataSubset(self, dataset)
        else:
            return getYXDataSubset(self, dataset)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _postCreateHook_(manager, file_attributes, datasets):
        """ Allows a class to handle special requirements when creating new
        files via the 'newFile' method.
        """
        if 'x_offset' not in file_attributes and\
           'y_offset' not in file_attributes:
            manager.setFileAttributes( x_offset=manager._base_x,
                                       y_offset=manager._base_y )


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from .search import gridSearch, radialSearch, relativeSearch

class GeoGridDataSearch(object):

    def __init__(self, grid_file_manager, dataset_names):
        self.manager = grid_file_manager
        self.lons, self.lats = self.manager.getLonLat()
        self.grid_shape = self.lons.shape

        if isinstance(dataset_names, basestring):
            self.dataset_names = (dataset_names,)
        elif isinstance(dataset_names, (list,tuple)):
            self.dataset_names = dataset_names
        else:
            raise TypeError, "Unsupported data type for 'dataset_names'."
        self.num_datasets = len(self.dataset_names)

        self.grids = { }
        for dataset_name in self.dataset_names:
            grid, attrs = self.manager.getData(dataset_name)
            self.grids[dataset_name] = grid

        self.max_x = self.manager._max_avail_x
        self.max_y = self.manager._max_avail_y

        self.bbox = (self.manager._min_avail_lon, self.manager._min_avail_lat,
                     self.manager._max_avail_lon, self.manager._max_avail_lat)

        self.coord_order = self.manager.COORDINATE_ORDER
        if self.coord_order == 'yx':
            self.col_indx = 1
            self.row_indx = 0
            self.dataValue = lambda grid,x,y : grid[y,x]
        else:
            self.col_indx = 0
            self.row_indx = 1
            self.dataValue = lambda grid,x,y : grid[x,y]
        self.col_indexes = range(self.grid_shape[self.col_indx])
        self.row_indexes = range(self.grid_shape[self.row_indx])

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def isWithinSearchArea(self, lon, lat):
        data_bbox = self.bbox
        if lon < data_bbox[0]: return False
        if lon > data_bbox[2]: return False
        if lat < data_bbox[1]: return False
        if lat > data_bbox[3]: return False
        return True

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataForNode(self, node_x, node_y):
        values = [ ]
        for dataset_name in self.dataset_names:
            grid = self.grids[dataset_name]
            values.append(self.dataValue(grid,node_x,node_y))
        return tuple(values)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataForNodeContaining(self, locus_lon, locus_lat):
        """ Return data for the grid node that contains the locus point.
        """
        x_index, y_index = self.manager.ll2index(locus_lon, locus_lat)
        # make sure that locus point is within the grid
        if x_index < 0 or x_index > self.max_x or\
           y_index < 0 or y_index > self.max_y :
                data = tuple([N.nan for name in range(len(self.dataset_names))])
                return data, (-1,-1), N.nan
        
        if x_index == self.max_x: x_index = -1
        if y_index == self.max_y: y_index = -1

        values = self.dataForNode(x_index, y_index)
        node_lon, node_lat = self.manager.index2ll(x_index, y_index)
        lon_diff = locus_lon - node_lon
        lat_diff = locus_lat - node_lat
        distance = math.sqrt((lon_diff*lon_diff)+(lat_diff*lat_diff))
        return values, (x_index, y_index), distance

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataForNodes(self, indexes):
        data = [ ]
        for dataset_name in self.dataset_names:
            grid = self.grids[dataset_name]
            values = [ ]
            for indx in range(len(indexes[0])):
                node_x = indexes[self.col_indx][indx]
                node_y = indexes[self.row_indx][indx]
                values.append(self.dataValue(grid,node_x,node_y))
            data.append(N.array(values))
        return tuple(data)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataAtRelativeIndexes(self, locus_x, locus_y, relative_indexes):
        """ Return data for grid nodes at relative_indexes to the locus node.
        """
        indexes, distances = relativeSearch(locus_x, locus_y, relative_indexes,
                                         self.lons, self.lats, self.coord_order)
        data = self.dataForNodes(indexes)
        return data, indexes, distances

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataInRadius(self, locus_lon, locus_lat, search_radius):
        """ Return data for all grid nodes within a circular area surrounding
        the locus point.
        """
        indexes, distances = radialSearch(locus_lon, locus_lat, search_radius,
                                         self.lons, self.lats, self.coord_order)
        data = self.dataForNodes(indexes)
        return data, indexes, distances

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataInGrid(self, locus_lon, locus_lat, search_radius):
        """ Return data for all grid nodes within a rectangular area
        surrounding the locus point.
        """
        indexes, distances = gridSearch(locus_lon, locus_lat, search_radius,
                                        self.lons, self.lats, self.coord_order)
        data = self.dataForNodes(indexes)
        return data, indexes, distances


""" Abstract base class that define the minimum API for derived classes.
        if self._xform_count == 0 or if self._xform_count/1000 == 0:
"""

import math
from copy import deepcopy

import numpy as N

from .geo import GeoDataFileMixin
from .manager import DatasetKey
from .subset import getXYDataSubset, getYXDataSubset

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Grid(object):
    """ Abstract base class to define API for grid file managers.
    """

    def __init__(self, grid, **attributes):
        self._preInitHook()

        self.grid = grid
        self.grid_shape = self.grid.shape
        self._initIndexBounds()

        self.attrs = { }
        for name, value in attributes.items():
            self.attrs[name] = value

        self._postInitHook()

    def _initIndexBounds(self):
        """ Capture index limits of grids in data file.
        """
        self.bounds = None

        self.row = None
        self.row_min = 0
        self.row_max = self.grid.shape[0]

        self.col = None
        self.col_min = 0
        self.col_max = self.grid.shape[1]

    def _preInitHook(self):
        pass

    def _postInitHook(self):
        pass

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getIndexBounds(self):
        """ Returns a tuple containg the minimum and maximum x and y indexes
        """
        return self.bounds

    def setIndexBounds(self, point_or_bbox=None):
        if point_or_bbox is not None:
            self.bounds = self._gridBounds_(point_or_bbox)
        else: self.bounds = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getAttributes(self, *attr_names):
        """ Provides acces to attribute values of a single grid
        if no attribute names are passed, returns a dictionary containing
        all known attributes
        if one attribute name is passed, returns the value of the attribute
        if multiple attribute names are passed, returns a dictionary with
        an entry for each attribute name in the list
        """
        num_attrs = len(attr_names)
        if num_attrs == 0:
            attrs = { }
            for name, value in self.attrs.items():
                attrs[name] = value
            return attrs
        elif num_attrs == 1:
            return self.attrs[attr_names[0]]
        else:
            attrs = { }
            for name in attr_names:
                attrs[name] = self.attrs[name]
            return attrs

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getData(self):
        return self._dataInBounds_(grid, self.bounds)

    def getDataAt(self, row, col):
        return self.grid[row,col]

    def getDataInBbox(self, bbox):
        return self.grid[ bbox[0]:bbox[2], bbox[1]:bbox[3] ]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _gridBounds_(self, point_or_bbox):
        if point_or_bbox is not None:
            if len(point_or_bbox) == 2:
                return tuple(point_or_bbox)

            elif len(point_or_bbox) == 4:
                row_min = point_or_bbox[0]
                row_max = point_or_bbox[2]

                col_min = point_or_bbox[1]
                col_max = point_or_bbox[3]

                return ( row_min, row_max, col_min, col_max )
            else:
                errmsg = "Invalid value for 'point_or_bbox'. It must contain "
                errmsg += "either a point (row, col) or a bounding box "
                errmsg += "(row_min, col_min, row_max, col_max)."
                raise ValueError, errmsg

        else:
            return self.bounds

    def _dataInBounds_(self, grid, bounds=None):
        if bounds is None:
            return grid
        elif len(bounds) == 2:
            x, y = bounds
            return grid[x:y]
        else:
            row_min, col_min, row_max, col_max = bounds
            return grid[row_min:row_max, col_min:col_max]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class MultiGrid(object):
    """ Abstract base class to define API for grid file managers.
    """

    def __init__(self, **grids):
        self._preInitHook()

        self.grids = { }
        self.attrs = { }
        self.grid_shape = None
        for name, grid, attrs in grids.items():
            self.attrs[name] = attrs
            self.grids[name] = grid
            if self.grid_shape:
                if grid.shape != self.grid_shape:
                    raise ValueError, 'Inconsiustent grid shapes'
            else:
                self.grid_shape = grid.shape
        self._initIndexBounds()

        self._postInitHook()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getData(self, *grid_names):
        """ Provides access to bounded grid data
        if no grid names are passed, returns a dictionary containing data
        for all known grids
        if one grid name is passed, returns the data for a single grid
        if multiple grid names are passed, returns a dictionary with
        an entry for each grid name in the list
        """
        num_grids = len(grid_names)
        if num_grids == 0:
            grids = { }
            for name, grid in self.grids.items():
                grids[name] = self._dataInBounds_(grid, self.bounds)
            return grids
        elif num_grids == 1:
            grid = self.grids[grid_names[0]]
            return self._dataInBounds_(grid, self.bounds)
        else:
            grids = { }
            for name in grid_names:
                grid = self.grids[name]
                grids[name] = self._dataInBounds_(grid, self.bounds)
            return grids

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDataAt(self, row, col, *grid_names):
        num_grids = len(grid_names)
        if num_grids == 0:
            data = [ ]
            for name, grid in self.grids.items():
                data.append(grid[row,col])
            return tuple(data)
        elif num_grids == 1:
            return self.grids[grid_names[0]][row,col]
        else:
            data = [ ]
            for name in grid_names:
                data.append(self.grids[name][row,col])
            return tuple(data)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDataInBbox(self, bbox, *grid_names):
        num_grids = len(grid_names)
        if num_grids == 0:
            grids = { }
            for name, grid in self.grids.items():
                grids[name] = grid[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            return grids
        elif num_grids == 1:
            grid = self.grids[grid_names[0]]
            return = grid[ bbox[0]:bbox[2], bbox[1]:bbox[3] ]
        else:
            grids = { }
            for name in grid_names:
                grid = self.grids[name]
                grids[name] = grid[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            return grids

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getAttributes(self,  grid_name, *attr_names):
        """ Provides acces to attribute values of a single grid
        if no attribute names are passed, returns a dictionary containing
        all known attributes
        if one attribute name is passed, returns the value of the attribute
        if multiple attribute names are passed, returns a dictionary with
        an entry for each attribute name in the list
        """
        num_attrs = len(attr_names)
        all_attrs = self.attrs[grid_name]

        if num_attrs == 0:
            for name, value in all_attrs.items():
                attrs[name] = value
            return attrs
        elif num_attrs == 1:
            return all_attrs[attr_names[0]]
        else:
            attrs = { }
            for name in attr_names:
                attrs[name] = all_attrs[name]
            return attrs


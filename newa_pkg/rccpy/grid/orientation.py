""" Methods to extract subsets of grids.
"""

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getXYDataSubset(self, dataset):
    """ Returns a subset of a grid that is within the grid manager's
    bounding box.
    """
    if self.min_x is not None:
        min_x, max_x, min_y, max_y = self.gridIndexBounds()

        if max_x < dataset.shape[0]:
            if max_y < dataset.shape[1]:
                return dataset[min_x:max_x, min_y:max_y]
            else:
                return dataset[min_x:max_x, min_y:]
        else:
            if max_y < dataset.shape[1]:
                return dataset[min_x:, min_y:max_y]
            else:
                return dataset[min_x:, min_y:]

    # asking for a single point
    elif self.x is not None:
        return dataset[self.x, self.y]

    # asking for the whole dataset
    return dataset


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getYXDataSubset(self, dataset, dtype=float):
    """ Returns a subset of a grid that is within the grid manager's
    lon/lat bounding box. Grid shape must be [y index, x index].
    """ 
    if self.min_x is not None:
        min_x, max_x, min_y, max_y = self.gridIndexBounds()

        if max_y < dataset.shape[0]:
            if max_x < dataset.shape[1]:
                return dataset[min_y:max_y, min_x:max_x]
            else:
                return dataset[min_y:max_y, min_x:]
        else:
            if max_x < dataset.shape[1]:
                return dataset[min_y:, min_x:max_x]
            else:
                return dataset[min_y:, min_x:]

    # asking for a single point
    elif self.x is not None:
        return dataset[self.y, self.x]

    # asking for the whole dataset
    return dataset


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getXYZDataSubset(self, dataset, min_z=None, max_z=None):
    """ Returns a subset of a grid that is within the z index window and
    grid manager's lon/lat bounding box from a grid. Grid shape must be
    [x, y, z].
    """
    if min_z == ':': min_z = 0
    if max_z >= dataset.shape[2]: max_z = ':'

    # coordinate bounds is a point
    if self.x is not None:
        # no slice in z dimension
        if min_z is None:
            return dataset[self.x, self.y, :]

        # single value at point
        if max_z is None:
            return dataset[self.x, self.y, min_z]

        # slice the Z dimension
        if min_z > 0:
            if max_z != ':' :
                return dataset[self.x, self.y, min_z:max_z]
            else:
                return dataset[self.x, self.y, min_z:]
        else:
            if max_z != ':':
                return dataset[self.x, self.y, :max_z]
            else:
                return dataset[self.x, self.y, :]
    
    # no co1ordinate bounds
    if self.min_x is None:
        subset = dataset[:,:,:]

    # coordinate bounds is a rectangle
    else:
        min_x, max_x, min_y, max_y = self.gridIndexBounds()
        if max_x >= dataset.shape[0]:
            if max_y >= dataset.shape[1]:
                subset = dataset[min_x:, min_y:, :]
            else:
                subset = dataset[min_x:, min_y:max_y, :]
        else:
            if max_y >= dataset.shape[1]:
                subset = dataset[min_x:max_x, min_y:, :]
            else:
                subset = dataset[min_x:max_x, min_y:max_y, :]

    # no slice in Z dimension
    if min_z is None:
        return subset

    # single value for each node
    if max_z is None:
        return subset[:, :, min_z]

    # slice the Z dimension
    if min_z > 0:
        if max_z != ':':
            return subset[:, :, min_z:max_z]
        else:
            return subset[:, :, min_z:]
    else:
        if max_z != ':':
            return subset[:, :, :max_z]
        else:
            return subset


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getYXZDataSubset(self, dataset, min_z=None, max_z=None):
    """ Returns a subset of a grid that is within the z index window and
    grid manager's lon/lat bounding box from a grid. Grid shape must be
    [y, x, z].
    """
    if min_z == ':': min_z = 0
    if max_z >= dataset.shape[2]: max_z = ':'

    # coordinate bounds is a point
    if self.x is not None:
        # no slice in z dimension
        if min_z is None:
            return dataset[self.y, self.x, :]

        # single value at point
        if max_z is None:
            return dataset[self.y, self.x, min_z]

        # slice the Z dimension
        if min_z > 0:
            if max_z != ':' :
                return dataset[self.y, self.x, min_z:max_z]
            else:
                return dataset[self.y, self.x, min_z:]
        else:
            if max_z != ':':
                return dataset[self.y, self.x, :max_z]
            else:
                return dataset[self.y, self.x, :]
    
    # no co1ordinate bounds
    if self.min_x is None:
        subset = dataset[:,:,:]

    # coordinate bounds is a rectangle
    else:
        min_x, max_x, min_y, max_y = self.gridIndexBounds()
        if max_y >= dataset.shape[0]:
            if max_x >= dataset.shape[1]:
                subset = dataset[min_y:, min_x:, :]
            else:
                subset = dataset[min_y:, min_x:max_x, :]
        else:
            if max_x >= dataset.shape[1]:
                subset = dataset[min_y:max_y, min_x:, :]
            else:
                subset = dataset[min_y:max_y, min_x:max_x, :]

    # no slice in Z dimension
    if min_z is None:
        return subset

    # single value for each node
    if max_z is None:
        return subset[:, :, min_z]
    
    # slice the Z dimension
    if min_z > 0:
        if max_z != ':':
            return subset[:, :, min_z:max_z]
        else:
            return subset[:, :, min_z:]
    else:
        if max_z != ':':
            return subset[:, :, :max_z]
        else:
            return subset


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getZXYDataSubset(self, dataset, min_z=None, max_z=None):
    """ Returns a subset of a grid that is within the z index window and
    grid manager's lon/lat bounding box from a grid. Grid shape must be
    [z, x, y].
    """
    if min_z == ':': min_z = 0
    if max_z >= dataset.shape[0]: max_z = ':'

    # coordinate bounds is a point
    if self.x is not None:
        # no slice in z dimension
        if min_z is None:
            return dataset[:, self.x, self.y]

        # single value at point
        if max_z is None:
            return dataset[min_z, self.x, self.y]

        # slice the Z dimension
        if min_z > 0:
            if max_z != ':' :
                return dataset[min_z:max_z, self.x, self.y]
            else:
                return dataset[min_z:, self.x, self.y]
        else:
            if max_z != ':':
                return dataset[:max_z, self.x, self.y]
            else:
                return dataset[:, self.x, self.y]

    # no co1ordinate bounds
    if self.min_x is None:
        subset = dataset[:,:,:]

    # coordinate bounds is a rectangle
    else:
        min_x, max_x, min_y, max_y = self.gridIndexBounds()
        if max_x >= dataset.shape[1]:
            if max_y >= dataset.shape[2]:
                subset = dataset[:, min_x:, min_y:]
            else:
                subset = dataset[:, min_x:, min_y:max_y]
        else:
            if max_y >= dataset.shape[2]:
                subset = dataset[:, min_x:max_x, min_y:]
            else:
                subset = dataset[:, min_x:max_x, min_y:max_y]

    # no slice in Z dimension
    if min_z is None:
        return subset

    # single value for each node
    if max_z is None:
        return subset[min_z, :, :]

    # slice the Z dimension
    if min_z > 0:
        if max_z != ':':
            return subset[min_z:max_z, :, :]
        else:
            return subset[min_z:, :, :]
    else:
        if max_z != ':':
            return subset[:max_z, :, :]
        else:
            return subset


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getZYXDataSubset(self, dataset, min_z=None, max_z=None):
    """ Returns a subset of a grid that is within the z index window and
    grid manager's lon/lat bounding box from a grid. Grid shape must be
    [z, y, x].
    """
    if min_z == ':': min_z = 0
    if max_z >= dataset.shape[0]: max_z = ':'

    # coordinate bounds is a point
    if self.x is not None:
        # no slice in z dimension
        if min_z is None:
            return dataset[:, self.y, self.x]

        # single value at point
        if max_z is None:
            return dataset[min_z, self.y, self.x]

        # slice the Z dimension
        if min_z > 0:
            if max_z != ':' :
                return dataset[min_z:max_z, self.y, self.x]
            else:
                return dataset[min_z:, self.y, self.x]
        else:
            if max_z != ':':
                return dataset[:max_z, self.y, self.x]
            else:
                return dataset[:, self.y, self.x]

    # no coordinate bounds
    if self.min_x is None:
        subset = dataset[:,:,:]

    # coordinate bounds is a rectangle
    else:
        min_x, max_x, min_y, max_y = self.gridIndexBounds()
        if max_y >= dataset.shape[1]:
            if max_x >= dataset.shape[2]:
                subset = dataset[:, min_y:, min_x:]
            else:
                subset = dataset[:, min_y:, min_x:max_x]
        else:
            if max_x >= dataset.shape[2]:
                subset = dataset[:, min_y:max_y, min_x:]
            else:
                subset = dataset[:, min_y:max_y, min_x:max_x]

    # no slice in Z dimension
    if min_z is None:
        return subset

    # single value for each node
    if max_z is None:
        return subset[min_z, :, :]

    # slice the Z dimension
    if min_z > 0:
        if max_z != ':':
            return subset[min_z:max_z, :, :]
        else:
            return subset[min_z:, :, :]
    else:
        if max_z != ':':
            return subset[:max_z, :, :]
        else:
            return subset


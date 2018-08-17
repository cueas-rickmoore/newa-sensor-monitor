
import math
import sys

import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

RELATIVE_INDEXES = {  9 : ( (-1, -1, -1,  0, 0, 0,  1, 1, 1),
                            (-1,  0,  1, -1, 0, 1, -1, 0, 1) )
                   ,  13 : ( (-2, -1, -1, -1,  0,  0, 0, 0, 0,  1, 1, 1, 2),
                             ( 0, -1,  0,  1, -2, -1, 0, 1, 2, -1, 0, 1, 0) )
                   , 25 : ( (-3, -2, -2, -2, -1, -1, -1, -1, -1,
                              0,  0,  0,  0,  0,  0,  0,
                              1,  1,  1,  1,  1,  2,  2,  2,  3),
                            ( 0, -1,  0,  1, -2, -1,  0,  1,  2,
                             -3, -2, -1,  0,  1,  2,  3,
                             -2, -1,  0,  1,  2, -1,  0,  1,  0) )
                   }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def closestNode(point_lon, point_lat, lon_grid, lat_grid):
    # find closest node
    lon_diffs = point_lon - lon_grid
    lat_diffs = point_lat - lat_grid
    distances = N.sqrt( (lon_diffs * lon_diffs) + (lat_diffs * lat_diffs) )
    closest = N.where(distances == distances.min())
    return lon_grid[closest], lat_grid[closest]

def indexOfClosestNode(point_lon, point_lat, lon_grid, lat_grid):
    node_lon, node_lat = closestNode(point_lon, point_lat, lon_grid, lat_grid)
    indexes = N.where((lon_grid == node_lon) & (lat_grid == node_lat))
    return indexes[0][0], indexes[1][0]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def neighborNodes(point_lon, point_lat, lon_grid, lat_grid, relative_nodes):
    if isinstance(relative_nodes, (list,tuple)):
        relative_node_indexes = relative_nodes
    else: relative_node_indexes = RELATIVE_INDEXES[relative_nodes]

    closest_y, closest_x = indexOfClosestNode(point_lon, point_lat,
                                              lon_grid, lat_grid)

    y_indexes = [ y+closest_y for y in relative_node_indexes[0] ]
    x_indexes = [ x+closest_x for x in relative_node_indexes[1] ]
    return [ y_indexes, x_indexes ]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def nodesInBBox(bbox, lon_grid, lat_grid, grid):
    max_lon = max(bbox[0], bbox[2])
    min_lon = min(bbox[0], bbox[2])
    max_lat = max(bbox[1], bbox[3])
    min_lat = min(bbox[1], bbox[3])
    indexes = N.where( (lon_grid >= min_lon) & (lat_grid >= min_lat) &
                        (lon_grid <= max_lon) & (lat_grid <= max_lat) )

    # i/x is in indexes[0], j/y is in indexes[1]
    indx_box = (min(indexes[0]), max(indexes[0])+1,
                min(indexes[1]), max(indexes[1])+1)
    if len(grid.shape) == 2:
        return grid[indx_box[0]:indx_box[1],indx_box[2]:indx_box[3]]
    return grid[:,indx_box[0]:indx_box[1],indx_box[2]:indx_box[3]]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def nodeInAllQuadrants(point_lon, point_lat, lon_grid, lat_grid):
    """ Verify that there is at least one grid point in each quadrant
    surrounding the point.
    """
    lon_diffs = lon_grid - point_lon
    lat_diffs = lat_grid - point_lat

    quadrants = N.zeros(lon_grid.shape)
    quadrants[ N.where((lon_diffs > 0.) & (lat_diffs >= 0.)) ] = 1
    quadrants[ N.where((lon_diffs > 0.) & (lat_diffs < 0.)) ] = 2
    quadrants[ N.where((lon_diffs < 0.) & (lat_diffs < 0.)) ] = 3
    quadrants[ N.where((lon_diffs < 0.) & (lat_diffs >= 0.)) ] = 4
    coverage = N.unique(quadrants)

    return 1 in coverage and 2 in coverage and 3 in coverage and 4 in coverage

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def quadrantAndDistance(point_lon, point_lat, node_lon, node_lat):
    """ Returns quadrant and distance of a grid node relative to a point

    Valid for Northern Latitudes / Western (negative) Longitudes 

                          +-------+-------+
                          |       |       |
                          |   1   |   4   |
                          |       |       |
                          +-------O-------+
                          |       |       |
                          |   2   |   3   |
                          |       |       |
                          +-------+-------+
    """
    lon_diff = node_lon - point_lon
    lat_diff = node_lat - point_lat

    distance = math.sqrt( (abs(lon_diff) ** 2.) + (abs(lat_diff) ** 2.) )

    if lon_diff > 0.: # node west of point
        if lat_diff < 0.: return 2, distance # node south of point
        else: return 1, distance # node north of point or at same latitude
    elif lon_diff < -1.: # node east of point
        if lat_diff < 0.: return 3, distance # node south of point
        else: return 4, distance # node north of point or at same latitude
    else: return 0, distance # node is at the point


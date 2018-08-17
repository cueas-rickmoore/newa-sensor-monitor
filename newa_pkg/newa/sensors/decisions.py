
import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.sensors.config import sensors as SENSORS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DecisionTree(object):
    
    def __init__(self, *rules):
        self.rules = tuple(rules)

    def __call__(self, *args, **kwargs):
        for rule in self.rules:
            result = rule(*args, **kwargs)
            if result is not None: return result
        return None

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def ghostPrecip(detector, date, sensor, station, grid):
    if station['total_precip'] >= SENSORS.pcpn.station_threshold\
    and N.nanmax(grid) < 0.01:
        return detector.ghostPrecip(date, sensor, station, grid)
    return None

def noPrecip(detector, date, sensor, station, grid):
    if station['total_precip'] == 0\
    and N.nanmin(grid) >= SENSORS.pcpn.grid_threshold:
        return detector.noPrecip(date, sensor, station, grid)
    return None

precipValidationTree = DecisionTree(noPrecip, ghostPrecip)


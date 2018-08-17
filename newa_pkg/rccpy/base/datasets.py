""" Definitions of common datasets and their metadata
"""

import numpy as N

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

DEFAULT_MASKED = N.nan
DEFAULT_MISSING = N.inf

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


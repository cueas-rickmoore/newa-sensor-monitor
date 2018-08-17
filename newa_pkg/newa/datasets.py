
import numpy as N

from newa.config import config as CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

AVAILABLE_DATA = { 'newa' : CONFIG.networks.newa.elements,
                   'icao' : CONFIG.networks.icao.elements,
                   'cu_log' : CONFIG.networks.cu_log.elements,
                   'njwx' : CONFIG.networks.njwx.elements,
                 }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DATA_UNITS = { }    #(hdf5 type,  hdf5 units,   script type, script units)
DATA_UNITS['daily_pcpn'] = CONFIG.elements.daily_pcpn.units
DATA_UNITS['dewpt'] = CONFIG.elements.dewpt.units
DATA_UNITS['dewpt_depr'] = CONFIG.elements.dewpt_depr.units
DATA_UNITS['lwet'] = CONFIG.elements.lwet.units
DATA_UNITS['pcpn'] = CONFIG.elements.pcpn.units
DATA_UNITS['rhum'] = CONFIG.elements.rhum.units
DATA_UNITS['srad'] = CONFIG.elements.srad.units
DATA_UNITS['st4i'] = CONFIG.elements.st4i.units
DATA_UNITS['st8i'] = CONFIG.elements.st8i.units
DATA_UNITS['temp'] = CONFIG.elements.temp.units
DATA_UNITS['wdir'] = CONFIG.elements.wdir.units
DATA_UNITS['wspd'] = CONFIG.elements.wspd.units

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DESCRIPTIONS = { }    
DESCRIPTIONS['daily_pcpn'] = CONFIG.elements.daily_pcpn.description
DESCRIPTIONS['dewpt'] =  CONFIG.elements.dewpt.description
DESCRIPTIONS['dewpt_depr'] = CONFIG.elements.dewpt_depr.description
DESCRIPTIONS['lwet'] = CONFIG.elements.lwet.description
DESCRIPTIONS['pcpn'] = CONFIG.elements.pcpn.description
DESCRIPTIONS['rhum'] = CONFIG.elements.rhum.description
DESCRIPTIONS['srad'] = CONFIG.elements.srad.description
DESCRIPTIONS['st4i'] = CONFIG.elements.st4i.description
DESCRIPTIONS['st8i'] = CONFIG.elements.st8i.description
DESCRIPTIONS['temp'] = CONFIG.elements.temp.description
DESCRIPTIONS['wdir'] = CONFIG.elements.wdir.description
DESCRIPTIONS['wspd'] = CONFIG.elements.wspd.description

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

HOURLY_DATA_TYPES = { }
HOURLY_DATA_TYPES['dewpt'] = CONFIG.elements.dewpt.gen_type
HOURLY_DATA_TYPES['dewpt_depr'] = CONFIG.elements.dewpt_depr.gen_type
HOURLY_DATA_TYPES['lwet'] = CONFIG.elements.lwet.tsvar_type
HOURLY_DATA_TYPES['pcpn'] = CONFIG.elements.pcpn.tsvar_type
HOURLY_DATA_TYPES['rhum'] = CONFIG.elements.rhum.tsvar_type
HOURLY_DATA_TYPES['srad'] = CONFIG.elements.srad.tsvar_type
HOURLY_DATA_TYPES['st4i'] = CONFIG.elements.st4i.tsvar_type
HOURLY_DATA_TYPES['st8i'] = CONFIG.elements.st8i.tsvar_type
HOURLY_DATA_TYPES['temp'] = CONFIG.elements.temp.tsvar_type
HOURLY_DATA_TYPES['wdir'] = CONFIG.elements.wdir.tsvar_type
HOURLY_DATA_TYPES['wspd'] = CONFIG.elements.wspd.tsvar_type

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

SERIAL_CRITERIA = { }
SERIAL_CRITERIA['daily_pcpn'] = CONFIG.elements.daily_pcpn.serial_type
SERIAL_CRITERIA['dewpt'] = CONFIG.elements.dewpt.serial_type
SERIAL_CRITERIA['dewpt_depr'] = CONFIG.elements.dewpt_depr.serial_type
SERIAL_CRITERIA['lwet'] = CONFIG.elements.lwet.serial_type
SERIAL_CRITERIA['pcpn'] = CONFIG.elements.pcpn.serial_type
SERIAL_CRITERIA['rhum'] = CONFIG.elements.rhum.serial_type
SERIAL_CRITERIA['srad'] = CONFIG.elements.srad.serial_type
SERIAL_CRITERIA['st4i'] = CONFIG.elements.st4i.serial_type
SERIAL_CRITERIA['st8i'] = CONFIG.elements.st8i.serial_type
SERIAL_CRITERIA['temp'] = CONFIG.elements.temp.serial_type
SERIAL_CRITERIA['wdir'] = CONFIG.elements.wdir.serial_type
SERIAL_CRITERIA['wspd'] = CONFIG.elements.wspd.serial_type

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

VALUE_TYPES = { } 
VALUE_TYPES['daily_pcpn'] = CONFIG.elements.daily_pcpn.value_type
VALUE_TYPES['dewpt'] = CONFIG.elements.dewpt.value_type
VALUE_TYPES['dewpt_depr'] = CONFIG.elements.dewpt_depr.value_type
VALUE_TYPES['lwet'] = CONFIG.elements.lwet.value_type
VALUE_TYPES['pcpn'] = CONFIG.elements.pcpn.value_type
VALUE_TYPES['rhum'] = CONFIG.elements.rhum.value_type
VALUE_TYPES['srad'] = CONFIG.elements.srad.value_type
VALUE_TYPES['st4i'] = CONFIG.elements.st4i.value_type
VALUE_TYPES['st8i'] = CONFIG.elements.st8i.value_type
VALUE_TYPES['temp'] = CONFIG.elements.temp.value_type
VALUE_TYPES['wdir'] = CONFIG.elements.wdir.value_type
VALUE_TYPES['wspd'] = CONFIG.elements.wspd.value_type

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

SEQUENCE_FILTERS = CONFIG.sequences.filters
SEQUENCE_ELEMENTS = SEQUENCE_FILTERS.keys()

SPIKE_FILTERS = CONFIG.spikes.filters
SPIKE_ELEMENTS = SPIKE_FILTERS.keys()


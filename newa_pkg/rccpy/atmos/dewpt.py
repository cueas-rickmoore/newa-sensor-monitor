
from dateutil.relativedelta import relativedelta

import numpy as N

from rccpy.utils.time import asDatetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def convertTempToKelvin(temp, temp_units):
    if temp_units == 'F*10':
        return ((5.0 / 9.0) * ((temp / 10.) - 32.0)) + 273.15
    elif temp_units == 'F': return ((5.0 / 9.0) * (temp - 32.0)) + 273.15
    elif temp_units == 'C': return temp + 273.15
    elif temp_units == 'K': return  temp
    else:
        errmsg = 'Cannot convert temperture in degrees %s to degrees Kelvin'
        raise ValueError, errmsg % temp_units

def convertTempFromKelvin(temp, temp_units):
    if temp_units == 'F*10':
        return (((9.0 / 5.0) * (temp - 273.15)) + 32) * 10.
    elif temp_units == 'F': return ((9.0 / 5.0) * (temp - 273.15)) + 32
    elif temp_units == 'C': return temp - 273.15
    elif temp_units == 'K': return temp
    else:
        errmsg = 'Cannot convert temperture in degrees Kelvin to degrees %s'
        raise ValueError, errmsg % temp_units

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def vaporPressureFromTemp(temp, temp_units, debug=False):
    # need temperature in degrees Celsius
    k_temp = convertTempToKelvin(temp, temp_units)
    # calculate saturation vapor pressure (sat_vp)
    vp = 6.11 * N.exp( 5420. * ( (k_temp - 273.15) / (273.15 * k_temp) ) )
    if debug: print 'vaporPressureFromTemp', vp, k_temp, temp
    return vp

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def dewpointFromHumidityAndTemp(relative_humidity, temp, temp_units,
                                debug=False):
    # saturation vapor pressure (sat_vp)
    sat_vp = vaporPressureFromTemp(temp, temp_units, debug)
    if debug:
        print 'dewpointFromHumidityAndTemp', relative_humidity, temp, temp_units
        print '    saturation vapor pressure', sat_vp
    # actual vapor pressure (vp)
    if isinstance(relative_humidity, N.ndarray):
        relative_humidity[N.where(relative_humidity==0)] = N.nan
        vp = (relative_humidity * sat_vp) / 100.
    else:
        if relative_humidity == 0: vp = N.nan
        else: vp = (relative_humidity * sat_vp) / 100.
    if debug: print '    actual vapor pressure', vp
    # dewpoint temperature in degrees Celsius
    k_dew_point = 1. / ( (1./273.15) - (N.log(vp/6.11) / 5420.) )
    dew_point = convertTempFromKelvin(k_dew_point, temp_units)
    if debug: print '    dew_point', k_dew_point, dew_point
    # convert back to units of input temperature
    return dew_point

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def dewpointDepression(relative_humidity, temp, temp_units):
    return temp - dewpointFromHumidityAndTemp(relative_humidity,temp,temp_units)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def relativeHumidityFromdDewpointAndTemp(dew_point, temp, temp_units):
    # saturation vapor pressure (sat_vp)
    sat_vp = vaporPressureFromTemp(temp, temp_units)
    # dewpoint (actual) vapor pressure (vp)
    vp = vaporPressureFromTemp(dew_point, temp_units)
    # relative humidity
    return (vp / sat_vp)*100

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def generateDewpointArray(rhum_data, rhum_base_hour,
                          temp_data, temp_base_hour, temp_units):
    _rhum_base_hour = asDatetime(rhum_base_hour)
    _temp_base_hour = asDatetime(temp_base_hour)
    # temperature typically has a longer history than relative humidity
    # so we need to sync up indexes into the rhum and temp data arrays
    base_hour = max(_rhum_base_hour, _temp_base_hour)
    # find base index into each data array
    if _rhum_base_hour == base_hour:
        rhum_start_indx = 0
        delta = base_hour - _temp_base_hour
        temp_start_indx = (delta.days * 24) + (delta.seconds / 3600)
        num_usable_hours = min(len(temp_data)-temp_start_indx, len(rhum_data))
    else:
        temp_start_indx = 0
        delta = base_hour - _rhum_base_hour
        rhum_start_indx = (delta.days * 24) + (delta.seconds / 3600)
        num_usable_hours = min(len(rhum_data)-rhum_start_indx, len(temp_data))

    rhum_end_indx = rhum_start_indx + num_usable_hours
    temp_end_indx = temp_start_indx + num_usable_hours

    data = dewpointFromHumidityAndTemp(rhum_data[rhum_start_indx:rhum_end_indx],
                                       temp_data[temp_start_indx:temp_end_indx],
                                       temp_units)

    return base_hour, base_hour+relativedelta(hours=num_usable_hours), data

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def calculateDewpointDepression(dewpt_data, dewpt_base_hour,
                                temp_data, temp_base_hour):
    _dewpt_base_hour = asDatetime(dewpt_base_hour)
    _temp_base_hour = asDatetime(temp_base_hour)
    # temperature typically has a longer history than relative humidity
    # (which is used to calculate dew point) so we need to sync up indexes
    # into the dewpt and temp data arrays
    base_hour = max(_dewpt_base_hour, _temp_base_hour)
    if _dewpt_base_hour == base_hour:
        dewpt_start_indx = 0
        delta = base_hour - _temp_base_hour
        temp_start_indx = (delta.days * 24) + (delta.seconds / 3600)
        num_usable_hours = min(len(temp_data)-temp_start_indx, len(dewpt_data))
    else:
        temp_start_indx = 0
        delta = base_hour - _dewpt_base_hour
        dewpt_start_indx = (delta.days * 24) + (delta.seconds / 3600)
        num_usable_hours = min(len(dewpt_data)-dewpt_start_indx, len(temp_data))

    dewpt_end_indx = dewpt_start_indx + num_usable_hours
    temp_end_indx = temp_start_indx + num_usable_hours

    data = temp_data[temp_start_indx:temp_end_indx] - \
           dewpt_data[dewpt_start_indx:dewpt_end_indx]
    return base_hour, base_hour+relativedelta(hours=num_usable_hours), data


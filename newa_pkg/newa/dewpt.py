
import numpy as N

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

def vaporPressureFromTemp(temp, temp_units):
    # need temperature in degrees Celsius
    k_temp = convertTempToKelvin(temp, temp_units)
    # calculate saturation vapor pressure (sat_vp)
    vp = 6.11 * N.exp( 5420. * ( (k_temp - 273.15) / (273.15 * k_temp) ) )
    return vp

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def dewpointFromHumidityAndTemp(relative_humidity, temp, temp_units):
    # saturation vapor pressure (sat_vp)
    sat_vp = vaporPressureFromTemp(temp, temp_units)
    # actual vapor pressure (vp)
    if isinstance(relative_humidity, N.ndarray):
        relative_humidity[N.where(relative_humidity==0)] = N.nan
        print len(temp), len(relative_humidity), len(sat_vp)
        vp = (relative_humidity * sat_vp) / 100.
    else:
        if relative_humidity == 0: vp = N.nan
        else: vp = (relative_humidity * sat_vp) / 100.
    # dewpoint temperature in degrees Celsius
    dew_point = 1. / ( (1./273.15) - (N.log(vp/6.11) / 5420.) )
    # convert back to units of input temperature
    return convertTempFromKelvin(dew_point, temp_units)

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


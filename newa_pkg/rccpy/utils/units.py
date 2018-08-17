""" Unit conversion utilities
"""

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

FIVE_NINTHS = 5./9.
NINE_FIFTHS = 9./5.
                    
CONVERSION_FUNCS = {
     # temperature conversions
    'C_F'         : lambda x : (x * NINE_FIFTHS) + 32.
    , 'C_K'       : lambda x : x + 273.15
    , 'F_C'       : lambda x : (x - 32.) * FIVE_NINTHS
    , 'F_K'       : lambda x : ((x - 32.) * FIVE_NINTHS) + 273.15
    , 'K_C'       : lambda x : x - 273.15
    , 'K_F'       : lambda x : ((x - 273.15) * NINE_FIFTHS) + 32.
    # unit temperature difference 
    , 'dC_dF'     : lambda x : x * NINE_FIFTHS
    , 'dC_dK'     : lambda x : x
    , 'dF_dC'     : lambda x : x * FIVE_NINTHS
    , 'dF_dK'     : lambda x : x * FIVE_NINTHS
    , 'dK_dC'     : lambda x : x
    , 'dK_dF'     : lambda x : x * NINE_FIFTHS
    # US linear measurement units
    , 'ft_in'     : lambda x : x * 12.
    , 'in_ft'     : lambda x : x / 12.
    # metric lienar measurement units
    , 'cm_m'      : lambda x : x / 100.
    , 'cm_mm'     : lambda x : x * 10.
    , 'm_cm'      : lambda x : x * 100.
    , 'm_mm'      : lambda x : x * 1000.
    , 'mm_cm'     : lambda x : x / 10.
    , 'mm_m'      : lambda x : x / 1000.
    # US lienar to metric linear 
    , 'ft_cm'     : lambda x : (x / 3.2808399) * 100.
    , 'ft_m'      : lambda x : x / 3.2808399
    , 'ft_mm'     : lambda x : (x / 3.2808399) * 1000.
    , 'in_cm'     : lambda x : x * 2.54
    , 'in_m'      : lambda x : x * 0.0254
    , 'in_mm'     : lambda x : x * 25.4
    # metric linear to US lieanr
    , 'cm_in'     : lambda x : x / 2.54
    , 'cm_ft'     : lambda x : (x / 2.54) / 12.
    , 'm_ft'      : lambda x : x * 3.2808399
    , 'm_in'      : lambda x : x * 39.3701
    , 'mm_in'     : lambda x : x / 25.4
    , 'mm_ft'     : lambda x : (x / 25.4) / 12.
    # humidity
    , 'in_kg/m2'  : lambda x : x * 25.4
    , 'kg/m2_in'  : lambda x : x / 25.4
    , 'kg/m2_mm'  : lambda x : x
    , 'mm_kg/m2'  : lambda x : x
    # solar radiation
    , 'watt/meter2_langley' : lambda x : x * 0.086
    , 'langley_watt/meter2' : lambda x : x / 0.086
    #
    , 'mph_miles/hour' : lambda x : x
    , 'miles/hour_mph' : lambda x : x
    }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def convertUnits(data, from_units, to_units):
    if from_units == to_units: return data

    if '*' in from_units:
        from_units, from_scale =  from_units.split('*')
        if data.dtype.kind == 'f': data /= float(from_scale)
        elif data.dtype.kind == 'i': data /= int(from_scale)

    if '*' in to_units: to_units, to_scale = to_units.split('*')
    else: to_scale = None

    func = CONVERSION_FUNCS.get('%s_%s' % (from_units,to_units), None)
    if func is not None: data = func(data)

    if to_scale is not None:
        if data.dtype.kind == 'f': data *= float(to_scale)
        elif data.dtype.kind == 'i': data *= int(to_scale)
    return data

def getConversionFunction(from_units, to_units):
    if from_units is not None and to_units is not None:
        def convert(data): return convertUnits(data, from_units, to_units)
        return convert
    return None

def isSupportedUnitConversion(from_units, to_units):
    conversion = '%s_%s' % (from_units, to_units)
    return conversion in CONVERSION_FUNCS


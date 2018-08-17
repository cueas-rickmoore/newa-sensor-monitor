
ELEM_TO_TSVAR = {
    'cu_log':{ 'lwet': ( (118,  0), (118,  1), (118,  2), ),
               'pcpn': ( (  5,  0), (  5,  7), ),
               'prcp': ( (  5,  0), (  5,  7), ),
               'rhum': ( ( 24,  0), ( 24,  6), ),
               'srad': ( (132,  0), (132,  1), ),
               'st4i': ( (121,265), ),
               'st8i': ( (121,393), ),
               'temp': ( (126,  0), (126,  1), ),
               'wdir': ( (130,  0), (130,  1), ),
               'wspd': ( (128,  0), (128,  1), ),
             },
    'newa' : { 'lwet': ( (118,  0), (118,  1), ),
               'pcpn': ( (  5,  0), (  5,  6), ),
               'prcp': ( (  5,  0), (  5,  6), ),
               'rhum': ( ( 24,  0), ( 24,  5), ),
               'srad': ( (132,  0), (132,  1), (119,  0), (119,  1), ),
               'st4i': ( (120,  1), ),
               'st8i': ( (120,  2), ),
               'temp': ( ( 23,  0), ( 23,  6), ),
               'wdir': ( ( 27,  0), (130,  0), ( 27,  5), ),
               'wspd': ( ( 28,  0), (128,  0), ( 28,  5), ),
             },
    'icao' : { 'pcpn': ( (  5,  0), (  5,  3), ),
               'prcp': ( (  5,  0), (  5,  3), ),
               'rhum': ( ( 24,  0), ( 24,  3), ),
               'temp': ( ( 23,  0), ( 23,  3), ),
               'wdir': ( ( 27,  0), ( 27,  3), ),
               'wspd': ( ( 28,  0), ( 28,  3), ),
             },
    'njwx' : { 'pcpn': ( (  5,  0), (  5,  6), ),
               'prcp': ( (  5,  0), (  5,  6), ),
               'rhum': ( ( 24,  0), ( 24,  5), ),
               'srad': ( (149,  0), (149,  1), ),
               'temp': ( ( 23,  0), ( 23,  6), ),
               'wdir': ( ( 27,  0), ( 27,  5), ),
               'wspd': ( ( 28,  0), ( 28,  5), ),
             },
    }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DATA_FORMATS = { 'lwet': '%3.0f',
                 'pcpn': '%.2f',
                 'prcp': '%.2f',
                 'rhum': '%.1f',
                 'srad': '%.2f',
                 'st4i': '%.1f',
                 'st8i': '%.1f',
                 'temp': '%.1f',
                 'wdir': '%.0f',
                 'wspd': '%.1f',
               }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DATA_UNITS  = { 'pcpn': 'in',
                'prcp': 'in',
                'temp': 'F',
                'lwet': '',
                'rhum': '%',
                'wspd': 'mph',
                'srad': 'langley',
                'st4i': 'F',
                'st8i': 'F',
              },

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class UcanUndefinedElementError(Exception): pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getTsVarCodeset(network, element_name):
    try:
        return ELEM_TO_TSVAR[network][element_name]
    except:
        errmsg = 'TsVar codes have not been defined for %s on the %s network'
        raise UcanUndefinedElementError, errmsg % (element_name, network)


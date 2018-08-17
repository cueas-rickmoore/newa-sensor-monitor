
from rccpy.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize limits for data extremes
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

extremes = ConfigObject('extremes',None)
extremes.stddevs = {
    'invalid' : {'daily_pcpn':10,'dewpt':7,'dewpt_depr':7,'lwet':7,'pcpn':10,
                 'rhum':7,'srad':7,'st4i':7,'st8i':7,'temp':7,'wdir':7,'wspd':7},
    'suspect' : {'daily_pcpn':7,'dewpt':4,'dewpt_depr':4,'lwet':4,'pcpn':7,
                 'rhum':4,'srad':4,'st4i':4,'st8i':4,'temp':4,'wdir':4,'wspd':4},
    }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize sequence filters and limits
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

sequences = ConfigObject('sequences',None)
sequences.filters = {
    'default' : ( ('x==x', '', 'identical values', str),
                  ('missing', '', 'missing values', 'missing'), ),
    'dewpt' : ( ('x==x', '', 'identical dew point values', lambda x:'%d' % x),
               ('missing', '', 'missing dew point values', 'missing'), ),
    'dewpt_depr' : ( ('x==x', '', 'identical dew point depression values', lambda x:'%d' % x),
               ('missing', '', 'missing dew point depression values', 'missing'), ),
    'lwet' : ( ('x==0', 'if run[0] == 0', 'leaf wetness == 0', '0'),
               ('0<X<60', 'if (run[0] > 0 and run[0] < 60)', '0 < leaf wetness < 60', lambda x:'%d' % x),
               ('x==60', 'if run[0] == 60', 'leaf wetness == 60', '60'),
               ('missing', '', 'missing values for leaf wetness', 'missing'), ),
    'pcpn' : ( ('x==0', 'if run[0] == 0', 'precipitation == 0', '0'),
               ('x>0', 'if run[0] > 0', 'precipitation > 0', lambda x:('%5.2f' % x).strip()),
               ('missing', '', 'missing precipitation values', 'missing'), ),
    'rhum' : ( ('0<x<100', 'if (run[0] > 0 and run[0] < 100)', '0 < humidity < 100', lambda x:'%d' % x),
               ('x==100', 'if run[0] == 100', 'humidity == 100', '100'),
               ('missing', '', 'missing values', 'missing'), ),
    'srad' : ( ('x==0', 'if run[0] == 0', 'surface radiation == 0', '0'),
               ('x>0', 'if run[0] > 0', 'surface radiation > 0', lambda x:('%5.2f' % x).strip()),
               ('missing', '', 'missing surface radiation values', 'missing'), ),
    'temp' : ( ('x==x', '', 'identical temperature values', lambda x:'%d' % x),
               ('missing', '', 'missing temperature values', 'missing'), ),
    'wdir' : ( ('x==x', '', 'identical wind directions', lambda x:'%d' % x),
               ('missing', '', 'missing wind directions values', 'missing'), ),
    'wspd' : ( ('x<5', 'if run[0] < 5', 'wind speed < 5', lambda x:'%d' % x),
               ('5<=x<10', 'if run[0] >= 5 and run[0] < 10', '5 <= wind speed < 10', lambda x:'%d' % x),
               ('x>=10', 'if run[0] >= 10', 'wind speed >= 10', lambda x:'%d' % x),
               ('missing', '', 'missing wind speed values', 'missing'), ),
    'zero' : ( ('x<0', 'if run[0] < 0', 'value < 0', str),
               ('x==0', 'if run[0] == 0', 'value == 0', '0'),
               ('x>0', 'if run[0] > 0', 'value > 0', str),
               ('missing', '', 'missing values', 'missing'), ),
    }
sequences.filters['st4i'] = sequences.filters['temp']
sequences.filters['st8i'] = sequences.filters['temp']

sequences.min_run_lengths = {'dewpt':2,'dewpt_depr':2,'lwet':2,'pcpn':2,
                             'rhum':2,'srad':2,'st4i':2,'st8i':2,'temp':2,
                             'wdir':2,'wspd':2}
sequences.stddevs = {
    'invalid' : {'dewpt':7,'dewpt_depr':7,'lwet':7,'pcpn':7,'rhum':7,'srad':7,
                 'st4i':7,'st8i':7,'temp':7,'wdir':7,'wspd':7},
    'suspect' : {'dewpt':4,'dewpt_depr':4,'lwet':4,'pcpn':4,'rhum':4,'srad':4,
                 'st4i':4,'st8i':4,'temp':4,'wdir':4,'wspd':4},
    }

sequences.log_filename_template = '%d_sequences.log'
sequences.min_count_cuttoff = 2

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# initialize spike filters and limits
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

spikes = ConfigObject('spikes',None)
spikes.filters = {
      'dewpt' : (('x>0', 'if spike != 0', 'dew point spike > 0', str),),
      'dewpt_depr' : (('x>0', 'if spike != 0', 'dew point depression spike > 0', str),),
      'rhum' : (('x>0', 'if spike != 0', 'humidity spike > 0', str),),
      'srad' : (('x>0', 'if spike != 0', 'surface radiation spike > 0', str),),
      'temp' : (('x>0', 'if spike != 0', 'temperature spike > 0', str),),
      'wdir' : (('x>0', 'if spike != 0', 'wind direction spike > 0', str),),
      'wspd' : (('x>0', 'if spike != 0', 'wind speed spike > 0', str),),
     }
spikes.filters['st4i'] = spikes.filters['temp']
spikes.filters['st8i'] = spikes.filters['temp']

spikes.stddevs = {
    'invalid' : {'dewpt':7,'dewpt_depr':7,'lwet':7,'pcpn':10,'rhum':7,'srad':7,
                 'st4i':7,'st8i':7,'temp':7,'wdir':7,'wspd':7},
    'suspect' : {'dewpt':4,'dewpt_depr':4,'lwet':4,'pcpn':7,'rhum':4,'srad':4,
                 'st4i':4,'st8i':4,'temp':4,'wdir':4,'wspd':4},
    }


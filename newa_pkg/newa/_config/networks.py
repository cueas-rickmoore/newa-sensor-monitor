
from rccpy.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DEFAULT_DATASETS = ('lwet','pcpn','rhum','srad','st4i','st8i','temp','wdir','wspd')
DEFAULT_METADATA = ('network','state','id','name','lon','lat','elev') 

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

networks = ConfigObject('networks',None)

networks.cu_log = { 'metadata' : DEFAULT_METADATA,
                    'elements' : DEFAULT_DATASETS,
                  }
networks.icao = { 'metadata' : DEFAULT_METADATA,
                  'elements' : ('pcpn','rhum','temp','wdir','wspd'),
                }
networks.newa = { 'metadata' : DEFAULT_METADATA,
                  'elements' : DEFAULT_DATASETS,
                }

networks.newa.coordinators = { 'CT' : { 'contact' : 'Mary Concklin',
                                        'email'   : 'mary.concklin@uconn.edu' },
                               'MA' : { 'contact' : 'Jon Clements ',
                                        'email'   : 'jon.clements@umass.edu' },
                               'PA' : { 'contact' : 'Rob Crassweller ',
                                        'email'   : 'rmc7@psu.edu' },
                               'NY' : { 'contact' : 'Juliet Carroll ',
                                        'email'   : 'jec3@cornell.edu' },
                               'VT' : { 'contact' : 'Terry Bradshaw ',
                                        'email'   : 'tbradsha@uvm.edu' },
                             }

networks.njwx = { 'metadata' : DEFAULT_METADATA,
                  'elements' : ('pcpn','rhum','srad','temp','wdir','wspd'),
                }



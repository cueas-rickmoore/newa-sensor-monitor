
import numpy as N

from rccpy.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CONSTRAINT_OPS = ('==','!=','<','<=','>','>=')

FILEMAKER_COLUMN_MAP = { 'Active' : 'active', 'Contact Name' : 'contact',
          'Contact Email' : 'email', 'Contact Phone' : 'phone',
          'Backup Contact Email' :'bemail', 'Backup Contact Name' : 'bcontact',
          'Instrument Brand' : 'sensor', 'Instrument Connection' : 'uplink',
          'Station ID' : 'sid', 'Station Name' : 'name',
          }

REVERSE_COLUMN_MAP = { }
for key, value in FILEMAKER_COLUMN_MAP.items():
    REVERSE_COLUMN_MAP[value] = key

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

INDEX = ConfigObject('INDEX', None)

# 'constraints':(type, format, (operators)) 

INDEX.active =      { 'data_type':N.dtype('a1'), 'missing':'O', 'units':None,
                      'description':'is station active (Yes,Out,Disconnected)',
                    }
INDEX.bcontact =    { 'data_type':N.dtype('object'), 'missing':'', 'units':None,
                      'description':'backup contact for sensor maintenance',
                    }
INDEX.bemail =      { 'data_type':N.dtype('object'), 'missing':'', 'units':None,
                      'description':'email address of backup contact',
                    }
INDEX.comments =    { 'data_type':N.dtype('object'), 'missing':'', 'units':None,
                      'description':'miscellaneous comments',
                    }
INDEX.contact =     { 'data_type':N.dtype('object'), 'missing':'', 'units':None,
                      'description':'primary contact for sensor maintenance',
                    }
INDEX.county =      { 'data_type':N.dtype('object'), 'missing':'', 'units':None,
                      'constraints':(str, "'%s'", ('==','!=')),
                      'description':'county name',
                    }
INDEX.datasets =    { 'data_type':N.dtype('a64'), 'missing':'', 'units':None,
                      'description':'list of variables in database',
                    }
# this is a duplicate of datasets carried for compatability with older code
#TODO optimize this out
INDEX.elements =    { 'data_type':N.dtype('a64'), 'missing':'', 'units':None,
                      'description':'list of variables in database',
                    }
INDEX.elev =        { 'data_type':float, 'missing':N.inf, 'units':'ft',
                      'constraints':(float, '%7.1', CONSTRAINT_OPS),
                      'description':'elevation',
                    }
INDEX.email =       { 'data_type':N.dtype('object'), 'missing':'', 'units':None,
                      'description':'email address of primary contact',
                    }
INDEX.first_hour =  { 'data_type':N.dtype('i4'), 'missing':-32768, 'units':'YYYYMMDDHH',
                      'description':'first hour in database',
                    }
INDEX.gmt =         { 'data_type':int, 'missing':-32768, 'units':'hours',
                      'constraints':(int, '%d', CONSTRAINT_OPS),
                      'description':'ofsset from UTC time',
                    }
INDEX.last_report = { 'data_type':N.dtype('i4'), 'missing':-32768, 'units':'YYYYMMDDHH',
                      'description':'day that station last reported valid data',
                    }
INDEX.lat =         { 'data_type':float, 'missing':N.inf, 'units':'degrees',
                      'constraints':(float, '%9.5f', CONSTRAINT_OPS),
                      'description':'latitude',
                    }
INDEX.lon =         { 'data_type':float, 'missing':N.inf, 'units':'degrees',
                      'constraints':(float, '%10.5f', CONSTRAINT_OPS),
                      'description':'longitude',
                    }
INDEX.name =        { 'data_type':N.dtype('object'), 'missing':'', 'units':None,
                      'constraints':(str, "'%s'", ('==','!=')),
                      'description':'full station name',
                    }
INDEX.network =     { 'data_type':N.dtype('a8'), 'missing':'', 'units':None,
                      'constraints':(str, "'%s'", ('==','!=')),
                      'description':'observation network',
                    }
INDEX.sensor =      { 'data_type':N.dtype('object'), 'missing':'', 'units':None,
                      'description':'type of sensor/instrument',
                    }
INDEX.sid =         { 'data_type':N.dtype('a8'), 'missing':'', 'units':None,
                      'constraints':(str, "'%s'", ('==','!=')),
                      'description':'station identifier (network specific)',
                    }
INDEX.state =       { 'data_type':N.dtype('a2'), 'missing':'', 'units':None,
                      'constraints':(str, "'%s'", ('==','!=')),
                      'description':'abbreviation of state name',
                    }
INDEX.ucanid =      { 'data_type':int, 'missing':-32768, 'units':None,
                      'constraints':(int, '%d', CONSTRAINT_OPS),
                      'description':'unique station identifier',
                    }
INDEX.uplink =      { 'data_type':N.dtype('object'), 'missing':'', 'units':None,
                      'description':'type of connection for data uplink',
                    }
INDEX.uplink_info = { 'data_type':N.dtype('object'), 'missing':'', 'units':None, 
                      'description':'additional informtion about data uplink',
                    }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getDictTemplate(metadata='all'):
    if metadata == 'all': metadata = list(INDEX.keys())
    template = [ ]
    if 'sid' in metadata: template.append('"sid":"%(sid)s"')
    if 'name' in metadata: template.append('"name":"%(name)s"')
    if 'county' in metadata: template.append('"county":"%(county)s"')
    if 'state' in metadata: template.append('"state":"%(state)s"')
    if 'network' in metadata: template.append('"network":"%(network)s"')
    if 'active' in metadata: template.append('"active":"%(active)s"')
    if 'first_hour' in metadata: template.append('"first_hour":%(first_hour)d')
    if 'last_report' in metadata: template.append('"last_report":%(last_report)d')
    # this is a HACK for transitional purposes only
    #TODO optimize this out
    if 'datasets' in metadata or 'elements' in metadata:
        template.append('"elements":""')
    if 'datasets' in metadata: template.append('"datasets":"%(datasets)s"')
    if 'ucanid' in metadata: template.append('"ucanid":%(ucanid)d')
    if 'lat' in metadata: template.append('"lat":%(lat)8.5f')
    if 'lon' in metadata: template.append('"lon":%(lon)10.5f')
    if 'elev' in metadata: template.append('"elev":%(elev)7.1f')
    if 'sensor' in metadata: template.append('"sensor":"%(sensor)s"')
    if 'uplink' in metadata: template.append('"uplink":"%(uplink)s"')
    if 'contact' in metadata: template.append('"contact":"%(contact)s"')
    if 'email' in metadata: template.append('"email":"%(email)s"')
    if 'bcontact' in metadata: template.append('"bcontact":"%(bcontact)s"')
    if 'bemail' in metadata: template.append('"bemail":"%(bemail)s"')
    if 'gmt' in metadata: template.append('"gmt":%(gmt)d')
    if 'uplink_info' in metadata: template.append('"uplink_info":"%(uplink_info)s"')
    if 'comments' in metadata: template.append('"comments":"%(comments)s"')
    return '{%s}' % ','.join(template)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getSortBy(*args):
    template = [ ]
    for key in args:
        if key == 'sid': template.append('%(sid)s')
        if key == 'name': template.append('%(name)s')
        if key == 'county': template.append('%(county)s')
        if key == 'state': template.append('%(state)s')
        if key == 'network': template.append('%(network)s')
        if key == 'active': template.append('%(active)s')
        if key == 'first_hour': template.append('%(first_hour)d')
        if key == 'last_report': template.append('%(last_report)d')
        if key == 'datasets': template.append('%(datasets)s')
        if key == 'ucanid': template.append('%(ucanid)d')
        if key == 'lat': template.append('%(lat)8.5f')
        if key == 'lon': template.append('%(lon)10.5f')
        if key == 'elev': template.append('%(elev)7.1f')
        if key == 'sensor': template.append('%(sensor)s')
        if key == 'uplink': template.append('%(uplink)s')
        if key == 'contact': template.append('%(contact)s')
        if key == 'email': template.append('%(email)s')
        if key == 'bcontact': template.append('%(bcontact)s')
        if key == 'bemail': template.append('%(bemail)s')
        if key == 'gmt': template.append('%(gmt)d')
        if key == 'uplink_info': template.append('%(uplink_info)s')
        if key == 'comments': template.append('%(comments)s')
    return ' '.join(template)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getSpreadsheetTemplate(metadata='all', separator='\t'):
    if metadata == 'all': metadata = INDEX.keys()
    template = [ ]
    for key in metadata:
        if key == 'sid': template.append('%(sid)s')
        if key == 'name': template.append('%(name)s')
        if key == 'county': template.append('%(county)s')
        if key == 'state': template.append('%(state)s')
        if key == 'network': template.append('%(network)s')
        if key == 'active': template.append('%(active)s')
        if key == 'first_hour': template.append('%(first_hour)d')
        if key == 'last_report': template.append('%(last_report)d')
        if key == 'datasets': template.append('%(datasets)s')
        if key == 'ucanid': template.append('%(ucanid)d')
        if key == 'lat': template.append('%(lat)8.5f')
        if key == 'lon': template.append('%(lon)10.5f')
        if key == 'elev': template.append('%(elev7.1f')
        if key == 'sensor': template.append('%(sensor)s')
        if key == 'uplink': template.append('%(uplink)s')
        if key == 'contact': template.append('%(contact)s')
        if key == 'email': template.append('%(email)s')
        if key == 'bcontact': template.append('%(bcontact)s')
        if key == 'bemail': template.append('%(bemail)s')
        if key == 'gmt': template.append('%(gmt)d')
        if key == 'uplink_info': template.append('%(uplink_info)s')
        if key == 'comments': template.append('%(comments)s')
    return '%s' % separator.join(template)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getTextTemplate(metadata='all'):
    if metadata == 'all': metadata = INDEX.keys()
    template = [ ]
    for key in metadata:
        if key == 'sid': template.append('sid="%(sid)s"')
        if key == 'name': template.append('name="%(name)s"')
        if key == 'county': template.append('county="%(county)s"')
        if key == 'state': template.append('state="%(state)s"')
        if key == 'network': template.append('network="%(network)s"')
        if key == 'active': template.append('active="%(active)s"')
        if key == 'first_hour': template.append('first_hour=%(first_hour)d')
        if key == 'last_report': template.append('last_report=%(last_report)d')
        if key == 'datasets': template.append('%(datasets)s')
        if key == 'ucanid': template.append('ucanid=%(ucanid)d')
        if key == 'lat': template.append('lat=%(lat)8.5f')
        if key == 'lon': template.append('lon=%(lon)10.5f')
        if key == 'elev': template.append('elev=%(elev)7.1f')
        if key == 'sensor': template.append('sensor="%(sensor)s"')
        if key == 'uplink': template.append('uplink="%(uplink)s"')
        if key == 'contact': template.append('contact="%(contact)s"')
        if key == 'email': template.append('email="%(email)s"')
        if key == 'bcontact': template.append('bcontact="%(bcontact)s"')
        if key == 'bemail': template.append('bemail="%(bemail)s"')
        if key == 'gmt': template.append('gmt=%(gmt)d')
        if key == 'uplink_info': template.append('%(uplink_info)s')
        if key == 'comments': template.append('%(comments)s')
    return ', '.join(template)


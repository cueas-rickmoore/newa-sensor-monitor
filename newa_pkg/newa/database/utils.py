import os
import datetime
import urllib2

from newa.factory import ObsnetDataFactory
from newa.database.index import getDictTemplate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from BaseHTTPServer import BaseHTTPRequestHandler
HTTP_RESPONSES = BaseHTTPRequestHandler.responses

from newa.config import config as CONFIG
COLUMN_LABELS = CONFIG.metadata.download.tab_labels
META_DOWNLOAD = CONFIG.metadata.download
TAB_LABEL_MAP = CONFIG.metadata.column_map

FILE_EXT_MAP = { '\t':'.tsv', ',':'.csv' }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

STATE_NAME_MAP = { 'WA': 'Washington', 'DE': 'Delaware', 'WI': 'Wisconsin',
                   'WV': 'West Virginia', 'HI': 'Hawaii', 'FL': 'Florida',
                   'WY': 'Wyoming', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
                   'NM': 'New Mexico', 'TX': 'Texas', 'LA': 'Louisiana',
                   'AK': 'Alaska', 'NC': 'North Carolina', 'ND': 'North Dakota',
                   'NE': 'Nebraska', 'TN': 'Tennessee', 'NY': 'New York',
                   'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'NV': 'Nevada',
                   'VA': 'Virginia', 'CO': 'Colorado', 'CA': 'California',
                   'AL': 'Alabama', 'AR': 'Arkansas', 'VT': 'Vermont',
                   'IL': 'Illinois', 'GA': 'Georgia', 'IN': 'Indiana',
                   'IA': 'Iowa', 'MA': 'Massachusetts', 'AZ': 'Arizona',
                   'ID': 'Idaho', 'CT': 'Connecticut', 'ME': 'Maine',
                   'MD': 'Maryland', 'OK': 'Oklahoma', 'OH': 'Ohio',
                   'UT': 'Utah', 'MO': 'Missouri', 'MN': 'Minnesota',
                   'MI': 'Michigan', 'KS': 'Kansas', 'MT': 'Montana',
                   'MS': 'Mississippi', 'SC': 'South Carolina',
                   'KY': 'Kentucky', 'OR': 'Oregon', 'SD': 'South Dakota'
                  }

def getStateName(abbr):
    return STATE_NAME_MAP.get(abbr, None)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def downloadMetadata(root_url, state, date_str, fmt='dump',
                     download_dirpath=None, column_map=TAB_LABEL_MAP,
                     debug=False):

    separator = '\t'
    template_dict = {'date':date_str, 'state':state}

    download_source_name = META_DOWNLOAD.source_tmpl % template_dict
    if root_url[-1] == '/':
        url = '%s%s' % (root_url, download_source_name)
    else: url = '%s/%s' % (root_url, download_source_name)
    if debug: print 'Downloading from', url

    try:
        response = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        print 'HTTP Error %d : %s' % (e.code, HTTP_RESPONSES[e.code][1])
        if e.code == 404:
            print 'Metadata for %s is not available at this time.' % state
            return None
        else: raise e

    data = response.read()
    if '''''' in data: eol = ''''''
    elif '\r' in data: eol = '\r'
    else: eol = '\n'

    stations = [ ]
    count = 0
    for record in data.split(eol):
        count += 1
        record = record.replace('\x0b','')
        if len(record) == 0: continue
        if debug: print 'record %d :\n' % count, record
        if count == 1:
            if 'Station ID' in record:
                column_labels = record.split(separator)
                metadata = [ column_map[column] for column in column_labels ]
                continue
            else: metadata = [ column_map[column] for column in COLUMN_LABELS ]
            if debug: print '\nmetadata fields :\n', metadata

        values = [value.strip() for value in record.split(separator)]
        station = dict(zip(metadata, values))
        if debug: print '\nstation :\n', station
        stations.append(station)
    stations = tuple(stations)

    if len(stations) > 0 and download_dirpath is not None:
        # save metadata directly into a file
        filename = META_DOWNLOAD.dest_tmpl % template_dict
        filepath = os.path.join(download_dirpath, filename)

        if fmt == 'tsv':
            filepath += '.tsv'
            writeStationsToFile(stations, filepath, fmt='tsv', mode='w')
        else:
            filepath += '.dump'
            writeStationsToFile(stations, filepath, fmt='dump', mode='w')
        return filepath
    else: return stations

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def readDumpFile(filepath):
    stations = [ ]
    dump_file = open(filepath, 'rU')
    line = dump_file.readline()
    while line:
        station = eval(line.strip())
        stations.append(station)
        line = dump_file.readline()
    dump_file.close()
    return tuple(stations)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def readSpreadsheetFile(filepath, separator='\t', column_map=TAB_LABEL_MAP):

    in_file = open(filepath, 'rU')
    # get column names from first line in file
    line = in_file.readline()
    column_names = [ column_map[column.strip()] 
                     for column in line.split(separator) ]

    # add stations to a list as they are read
    stations = [ ]
    
    line = input_file.readline().replace('"','')
    while line:
        data = line.split(separator)
        # tsv files from Excel that had ^M as line separators get screwed up
        # when the ^M is removed
        if data[-1] == '\n': data[-1] = ''
        elif data[-1].endswith('\n'):
            data[-1] = data[-1].strip()
        # the last \t may also disapper if the last column was empty
        # this is especially a problem with the MAC version of Excel
        if num_ss_columns - len(data) == 1:
            data.append('')

        station = dict(zip(column_names, data))
        stations.append(station)
        line = in_file.readline()

    return tuple(stations)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def writeStationsToFile(stations, filepath, fmt='dump', mode='w'):
    out_file = open(filepath, mode)

    # write each station as a line in a tab separated values file
    if fmt == 'tsv':
        keys = list(stations[0].keys())
        keys.sort()
        if 'ucanid' in keys:
            del(keys[keys.index('ucanid')])
            keys.insert(0, 'ucanid')
        if 'name' in keys:
            del(keys[keys.index('name')])
            keys.insert(0, 'name')
        if 'sid' in keys:
            del(keys[keys.index('sid')])
            keys.insert(0, 'sid')
        out_file.write('\t'.join(keys))
        
        for station in stations:
            values = [ station[key] for key in keys ]
            out_file.write('\n%s' % '\t'.join(values))

    # write to a json file
    elif fmt == 'json':
        import json
        out_file.write(json.dumps( {'stations':list(stations)} ))

    # write each station as a python dictionary
    else:
        station = stations[0]
        template = getDictTemplate(station)
        out_file.write(template % station)
        for station in stations[1:]:
            out_file.write('\n')
            template = getDictTemplate(station)
            out_file.write(template % station)

    out_file.close()


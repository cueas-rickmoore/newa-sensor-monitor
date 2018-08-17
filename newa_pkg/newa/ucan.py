
from datetime import datetime

from rccpy.stations.ucan import UcanConnection
from rccpy.stations.ucan import UcanErrorExplanation
from rccpy.utils.exceptutils import reportLastException
from rccpy.utils.timeutils import asDatetime, dateAsTuple, dateAsInt

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from newa.config import config as CONFIG
STATION_INFO = 'Network %(network)s : Station %(sid)s : %(name)s : %(ucanid)d'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def explainException(e, station, detail=None):
    exception_type = e.__class__.__name__
    args = list(e.args)
    if detail is not None: args.insert(0, detail)
    if exception_type != 'UcanErrorExplanation':
        args.insert(0, STATION_INFO % station)
        args.insert(0, 'Exception : %s' % exception_type)
    e.args = tuple(args)
    return e

def getTsVarType(station, dataset_name):
    tsvar_type = CONFIG.datasets[dataset_name].tsvar_type
    if dataset_name == 'srad' and station['network'] == 'njwx':
        tsvar_type = list(tsvar_type)
        tsvar_type[-1] = 'watt/meter2'
        return tuple(tsvar_type)
    return tsvar_type

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class HourlyDataConnection(object):

    def __init__(self, days_per_request=1, base_time=None, first_hour_in_day=0):
        self.days_per_request = days_per_request
        self.base_time = base_time
        self.first_hour_in_day = first_hour_in_day
        self.ucan = UcanConnection(base_time, days_per_request)

    def getTimeSpan(self, date):
        _time = list(dateAsTuple(date)[:3])
        _time.append(self.first_hour_in_day)
        start_time = asDatetime(_time)
        end_time = start_time + ONE_DAY
        return start_time, end_time

    def getData(self, station, dataset_name, start_time, end_time, debug=False):
        dtype,missing,units,tsv_name,tsv_units =\
        getTsVarType(station,dataset_name)
        try:
            return self.ucan.getHourlyData(station, tsv_name, dtype, tsv_units,
                                           missing, dateAsTuple(start_time,True),
                                           dateAsTuple(end_time,True), debug)
        except Exception as e:
            errmsg = "Exception occurred while requesting data for '%s'."
            detail = errmsg % dataset_name
            reportLastException(None, None, detail)
            raise explainException(e, station, detail)

    def getOneDay(self, station, dataset_name, date, debug=False):
        start_time, end_time = self.getTimeSpan(date)
        return  self.getData(station, dataset_name, start_time, end_time, debug)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getValidDateRange(self, station_dict, elem, debug=False):
        return self.ucan.getValidDateRange(station_dict, elem, debug)

    def getValidDatetimeRange(self, station_dict, elem, debug=False):
        start_time, end_time = self.getValidDateRange(station_dict, elem, debug)
        return datetime(*start_time), datetime(*end_time)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def updateWithUcanMetadata(station, ucan_connection=None, update_datasets=True):
    """ Update a station dictionary with metadata from Ucan/Tsvar
    """
    if ucan_connection is not None:
        ucan = ucan_connection
    else: ucan = UcanConnection()

    ucanid = ucan.ucanid(station)
    station['ucanid'] = ucanid
    station_keys = station.keys()

    meta = ucan.getMetadata(station)
    for key in ('county','elev','lat','lon'):
        if key not in station_keys: station[key] = meta[key]
    if 'state' not in station_keys: station['state'] = meta['postal']
    if 'gmt' not in station_keys:
        gmt = int(meta['gmt_offset'])
        if gmt > 0: gmt = -gmt
        station['gmt'] = gmt

    datasets = [ ]
    first_hour = 9999999999
    last_report = 0
    for dataset_name in CONFIG.raw_datasets:
        try:
            ts_var = ucan.getTsVar(station, dataset_name)
        except:
            pass
        else:
            datasets.append(dataset_name)
            start_hour, end_hour = ts_var.getValidDateRange()
            first_hour = min(first_hour, dateAsInt(start_hour, True))
            last_report = max(last_report, dateAsInt(end_hour, True))
            del ts_var

    if ucan_connection is not None: del ucan

    if update_datasets:
        station['datasets'] = ','.join(datasets)

    if first_hour == 9999999999: station['first_hour'] = -32768
    else: station['first_hour'] = first_hour

    if last_report == 0: station['last_report'] = -32768
    else: station['last_report'] = last_report

    return station


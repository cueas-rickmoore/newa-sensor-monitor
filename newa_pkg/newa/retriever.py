
import os, sys
from datetime import datetime
from itertools import izip

from dateutil.relativedelta import relativedelta

import numpy as N

from rccpy.utils.options import optionsAsDict
from rccpy.utils.timeutils import asDatetime

from newa.ucan import HourlyDataConnection

from newa.scripts.factory import ObsnetDataFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

#APP = os.path.splitext(os.path.split(__file__)[1])[0].upper().replace('_',' ')
APP = os.path.split(sys.argv[0])[1] + ' ' + ' '.join(sys.argv[1:])
#PID = os.getpid()
PID = 'PID %d' % os.getpid()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class HourlyDataRetriever(object):

    def __init__(self, options={}):
        self.factory = factory = ObsnetDataFactory(options)
        base_time = factory.config.get('base_time',None)
        days_per_request = factory.config.get('days_per_request',2)
        first_hour_in_day = factory.config.get('first_hour_in_day',1)

        self.connection = HourlyDataConnection(days_per_request, base_time,
                                               first_hour_in_day)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getBuddies(self, ucanid):
        manager = self.factory.getFileManager((ucanid,'statistics'), 'r')
        buddies = [int(record[0]) for record in manager.getData('buddies')
                                  if int(record[0]) > 0]
        manager.closeFile()
        return self.getMetadata(buddies)

    def getOneDay(self, station, element, date):
        return self.connection.getOneDay(station, element, date)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getMetadata(self, ucanids):
        if not isinstance(ucanids, (list,tuple)): _ucanids = (ucanids,)
        else: _ucanids = ucanids
        conditions = '|'.join(['(ucanid==%d)' % ucanid for ucanid in _ucanids])
        where = 'N.where(%s)' % conditions

        manager = self.factory.getFileManager('index', 'r')
        id_dataset = manager.getData('ucanid')
        indexes = eval(where, globals(), {'ucanid':id_dataset,})

        data = [ ]
        dataset_names = manager.listDatasets()
        for dataset_name in dataset_names:
            if dataset_name == 'ucanid':
                data.append(id_dataset[indexes])
            else:
                data.append(manager.getData(dataset_name)[indexes])
        manager.closeFile()

        metadata = { }
        for _dict in (dict(zip(dataset_names,row)) for row in izip(*data)):
            metadata[_dict['ucanid']] = _dict
        return tuple([metadata[ucanid] for ucanid in _ucanids])


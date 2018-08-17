
from rccpy.utils.timeutils import asDatetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class DecisionTree(object):
    
    def __init__(self, *rules):
        self.rules = tuple(rules)

    def __call__(self, *args, **kwargs):
        for rule in self.rules:
            result = rule(*args, **kwargs)
            if result is not None: return result
        return None

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# rem63 20180608 - per Dan Olmstead - special message for first day # 
def isFirstOccurrence(manager, station, days_since_last, **kwargs):
    if days_since_last in (0,1):
        return manager.allMissing(station, 'out_24_hours', days_since_last)
    elif days_since_last < 7:
        return manager.trackMissing(station, days_since_last)
    return None

# rem63 20180608 - per Dan Olmstead - no longer send weekly messages # 
#def weeklyOccurrence(manager, station, days_since_last, **kwargs):
#    if days_since_last / 7 in (1,2):
#        if days_since_last % 7 == 0: # rem63 20180608 # 
#            return manager.allMissing(station, days_since_last)
#        return manager.trackMissing(station, days_since_last)
#    return None

# rem63 20180608 - per Dan Olmstead - 7th day message replaces weeklyOccurence # 
def isSeventhDay(manager, station, days_since_last, **kwargs):
    if days_since_last / 7 == 1:
        if days_since_last % 7 == 0:
            return manager.allMissing(station, 'out_7_days', days_since_last)
    if days_since_last < 21:
       return manager.trackMissing(station, days_since_last)
    return None

# rem63 20180608 - per Dan Olmstead - no longer send weekly messages # 
def outTooLong(manager, station, days_since_last, **kwargs):
    if days_since_last / 7 == 3:
        if days_since_last % 7 > 0:
            return manager.deactivate(station, days_since_last)
        else: return manager.deactivate(station, days_since_last, True)
    return None

def pastDue(manager, station, days_since_last, **kwargs):
    return manager.pastDue(station, days_since_last)

# rem63 20180608 - per Dan Olmstead - 7th day message replaces weeklyOccurence # 
#activeMissingTree = DecisionTree(isFirstOccurrence, weeklyOccurrence,
#                                 outTooLong, pastDue)
activeMissingTree = DecisionTree(isFirstOccurrence, isSeventhDay,
                                 outTooLong, pastDue)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def activeMissing(manager, station, **kwargs):
    if len(station['missing_datasets']) == len(station['reportable_datasets']):
        last_time = asDatetime(station['last_report'],True)
        days_since_last = (manager.end_time - last_time).days
        return activeMissingTree(manager, station, days_since_last, **kwargs)
    return None

def activeNotMissing(manager, station, **kwargs):
    station = manager.updateLastReport(station)
    return station, None

activeTree = DecisionTree(activeMissing, activeNotMissing)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def inactiveNotMissing(manager, station, **kwargs):
    if len(station['valid_hours']) > 0:
        return manager.activate(station)
    return None

def inactiveMissing(manager, station, **kwargs):
    return manager.ignore(station)

inactiveTree = DecisionTree(inactiveNotMissing, inactiveMissing)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def inNetwork(manager, station, **kwargs):
    if station['network'] in manager.networks:
        if station['active'] == 'Y':
            return activeTree(manager, station, **kwargs)
        elif station['active'] == 'O':
            return inactiveTree(manager, station, **kwargs)
        else: return manager.ignore(station)
    return None, None

def notInNetwork(manager, station, **kwargs):
    if len(station['missing_datasets']) < len(station['reportable_datasets']):
        station = manager.updateLastReport(station)
    return station, None

decisionTree = DecisionTree(inNetwork, notInNetwork)


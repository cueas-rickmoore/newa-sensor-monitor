
import optparse

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getBboxFromOptions(options):
    if hasattr(options, 'bbox') and options.bbox is not None:
        return stringToBbox(options.bbox)
    else:
        return None

def stringToBbox(bbox):
    errmsg = 'Invalid bbox string : %s' % bbox
    if '(' in bbox or '[' in bbox:
        return tuple([float(coord) for coord in eval(bbox)])
    elif ',' in bbox:
        values = bbox.split(',')
        if len(values) == 4:
            return tuple([float(coord) for coord in values])
        elif len(values) > 4:
            return tuple([float(coord) for coord in values[:4]])
        else:
            raise ValueError, errmsg
    else:
        raise ValueError, errmsg

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def optionsToDate(options, *args):
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    if len(args) == 3:
        year = int(args[0])
        month = int(args[1])
        day = int(args[2])
        date = datetime.date(year,month,day)
    else:
        date = datetime.date.today()
        if options.days_ago > 0:
            date -= relativedelta(days=options.days_ago)
        elif options.weeks_ago > 0:
            date -= relativedelta(weeks=options.weeks_ago)
        elif options.months_ago > 0:
            date -= relativedelta(months=options.months_ago)
    return date

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def optionsAsDict(options, trim=False):
    opt_dict = vars(options)
    if not trim: return opt_dict

    usable_options = { }
    for key,value in opt_dict.items():
        if value is None or (isinstance(value, (basestring, tuple, list, dict))
        and len(value) is 0): continue
        
        usable_options[key] = value
    return usable_options

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def stringToTuple(_string, _type=None):
    _str = _string.strip()
    if _str.startswith('['):
        if _str.endswith(']'):
            _str = _str[1:-1]
        else:
            raise ValueError, 'Badly formed string sequence : %s' % _string

    elif _str.startswith('('):
        if _str.endswith(')'):
            _str = _str[1:-1]
        else:
            raise ValueError, 'Badly formed string sequence : %s' % _string

    if ',' in _str: sequence = _str.split(',')
    else: sequence = (_str,)

    if _type is not None: return tuple([_type(value) for value in sequence])
    else: return tuple(sequence)

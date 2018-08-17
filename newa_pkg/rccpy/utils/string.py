
def tupleFromString(_string_):
    if _string_.startswith('['):
        right = _string_.rfind(']')
        _string_ = _string_[1:right].strip()
    elif _string_.startswith('('):
        right = _string_.rfind(')')
        _string_ = _string_[1:right].strip()
    return tuple([substr.strip() for substr in _string_.split(',')])

def strippedFloat(float_num, precision=5, format='%%20.%df'):
    return ((format % precision) % float_num).strip()


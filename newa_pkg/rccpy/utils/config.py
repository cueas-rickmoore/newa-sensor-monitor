
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

FOLLOW_FAILED = hash('_follow_path_ does not result in ConfigObject')
GETATTR_FAILED = hash('attribute/object path lookup failed')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ConfigObject(object):

    def __init__(self, name, parent, *children, **kwargs):
        if '.' in name:
            errmsg = "Trying to create instance of ConfigObject with name = '%s'"
            errmsg += '\nDotted paths cannot be used as a name for ConfigObjects'
            raise ValueError, errmsg % name

        object.__init__(self)
        self.__dict__['__name__'] = name
        self.__dict__['__children__'] = { }

        if len(children) > 0:
            for child in children:
                if isinstance(child, basestring):
                    self.newChild(child)
                elif isinstance(child, ConfigObject):
                    self.addChild(child)
                else:
                    indx = children.index(child)
                    raise TypeError, 'Invalid type for argument %d' % indx

        if len(kwargs) > 0:
            for key, value in kwargs.items():
                self._setAttributeValue_(key, value)

        if parent is not None: parent.addChild(self)
        else: self.__dict__['__parent__'] = None

    def _child_names(self):
        names = [ key for (key, obj) in self.__dict__['__children__'].items()
                  if isinstance(obj, ConfigObject) ]
        names.sort()
        return tuple(names)
    child_names = property(_child_names)

    def _children(self):
        return tuple( [ self.__dict__['__children__'][name]
                        for name in self.child_names ] )
    children = property(_children)

    def _name(self):
        return self.__dict__['__name__']
    name = property(_name)

    def _parent(self):
        return self.__dict__['__parent__']
    parent = property(_parent)

    def _path(self):
        if self.parent is None: return self.name
        else: return '%s.%s' % (self.parent._path(), self.name)
    path = property(_path)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def addChild(self, config_obj):
        self.__dict__['__children__'][config_obj.name] = config_obj
        config_obj.__dict__['__parent__'] = self

    def addChildren(self, *children):
        for name in children:
            self.__dict__['__children__'][name] = ConfigObject(name, self)
    
    def asDict(self):
        wrapped = { }
        for name, value in self.__dict__['__children__'].items():
            if name.startswith('__'): continue
            if isinstance(value, ConfigObject):
                wrapped[name] = value.asDict()
            else:
                wrapped[name] = value
        return wrapped
    dict = property(asDict)

    def extend(self, obj):
        if isinstance(obj, ConfigObject):
            if obj.name in self.child_names: self.update(obj)
            else: self.addChild(obj)
        elif isinstance(obj, dict):
            for key, value in obj.items():
                self._setAttributeValue_(key, value)
        else:
            raise TypeError, "Invalid type for 'obj' argument : %s" % type(obj)

    def find(self, path):
        keys = path.split('.')
        # check to see if my own name is at the beginning of the path
        if self._is_my_name_(keys[0]): return self._find_(keys[1:])
        return self._find_(keys)
 
    def hasAttr(self, path):
        return self.__dict__['__children__'].has_key(path)

    def hasChild(self, name):
        if self.hasAttr(name):
            return isinstance(self.__dict__['__children__'][name],ConfigObject)
        return False

    def hierarchy(self, seed=None, hierarchy=[ ]):
        my_name = self.__dict__['__name__']
        if seed is None: _seed = my_name
        else: _seed = '%s.%s' % (seed, my_name)
        hierarchy.append(_seed)

        for name in self.keys():
            obj = self.__dict__['__children__'][name]
            if isinstance(obj, ConfigObject):
                hierarchy = obj.hierarchy(_seed, hierarchy)
            else:
                hierarchy.append('%s.%s' % (_seed, name))

        if seed is None: return tuple(hierarchy)
        else: return hierarchy

    def listChildren(self):
        return self.__dict__['__children__'].keys()

    def newChild(self, path):
        if '.' not in path:
            if path not in self.__dict__['__children__']:
                child = ConfigObject(path, self)
                self.__dict__['__children__'][path] = child
        else: child = self._construct_obj_tree_(path.split('.'))
        return child

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    # implementation of dictionary methods
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def clear(self): self.__dict__['__children__'].clear()

    def copy(self, new_name=None, parent=None):
        if new_name is None: new_name = self.name
        #if parent is None: parent = self.parent
        config_obj = ConfigObject(new_name, parent)
        if parent is not None: # copying entire config tree
            parent.addChild(config_obj)

        for key, value in self.__dict__['__children__'].items():
            if isinstance(value, ConfigObject):
                config_obj[key] = value.copy(key, config_obj)
            elif isinstance(value, dict):
                config_obj[key] = self._copyDict_(value)
            elif isinstance(value, tuple):
                config_obj[key] = tuple([x for x in value])
            elif isinstance(value, list):
                config_obj[key] = [x for x in value]
            
            else:
                config_obj[key] = value
        return config_obj

    def get(self, path, default=None):
        return self._getAttributeValue_(path, default)

    def has_key(self, key):
        return key in self.keys()

    def items(self):
        return tuple( [ (name, self.__dict__['__children__'][name])
                        for name in self.child_names ] )

    def iter(self):
        for name in self.child_names: yield name

    def iteritems(self):
        for name in self.child_names: 
            yield (name, self.__dict__['__children__'][name])

    def iterkeys(self):
        for name in self.child_names: yield name

    def itervalues(self):
        for name in self.child_names: 
            yield self.__dict__['__children__'][name]
    iterChildren = property(itervalues)

    def keys(self):
        keys = [key for key in self.__dict__['__children__'].keys()
                    if not key.startswith('__')]
        keys.sort()
        return tuple(keys)

    def set(self, **kwargs):
        for path, _value in kwargs.items():
            self._setAttributeValue_(path, _value)

    def update(self, obj):
        if isinstance(obj, (ConfigObject, dict)):
            for key, value in obj.items():
                self._setAttributeValue_(key, value)
        else:
            raise TypeError, "Invalid type for 'obj' argument : %s" % type(obj)

    def values(self):
        return tuple( [ self.__dict__['__children__'][name]
                        for name in self.child_names ] )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    # ConfigObject "dirty work" methods
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


    def _construct_obj_tree_(self, keys):
        name = keys[0]
        child = self.__dict__['__children__'].get(name, None)
        if child is None:
            child = ConfigObject(name, self)
            self.__dict__['__children__'][name] = child
        if len(keys) > 1 : child._construct_obj_tree_(keys[1:]) 

    def _copyDict_(self, _dict):
        dict_copy = { }
        for key, value in _dict.items():
            if isinstance(value, ConfigObject):
                dict_copy[key] = value.copy(key, self)
            elif isinstance(value, dict):
                dict_copy[key] = self._copy_dict(value)
            elif isinstance(value, tuple):
                dict_copy[key] = tuple([x for x in value])
            elif isinstance(value, list):
                dict_copy[key] = [x for x in value]
        return dict_copy

    def _deleteChild_(self, name):
        child = self.__dict__['__children__'][name]
        if isinstance(child, ConfigObject):
            child._deleteChildren_()
            del self.__dict__['__children__'][name]

    def _deleteChildren_(self):
        for key, child in self.__dict__['__children__'].items():
            if isinstance(child, ConfigObject):
                child._deleteChildren_()
                del self.__dict__['__children__'][key]

    def _deleteTree_(self, path):
        if isinstance(path, basestring): dot = path.find('.')
        else: dot = -1
        if dot > 0:
            attr_key = path[:dot]
            if self.__dict__['__children__'].has_key(attr_key):
                obj = self.__getitem__(attr_key)
                if isinstance(obj, ConfigObject):
                    obj._deleteTree_(path[dot+1:])
            self.__dict__['__children__'].__delitem__(attr_key)
        else: self.__dict__['__children__'].__delitem__(path)

    def _dict_keys(): return self.__dict__.keys()

    def _find_(self, find_keys):
        found = [ ]
        first_key = find_keys[0]

        if first_key == '*':
            if len(find_keys) > 1:
                for key in self.keys():
                    obj = self.__dict__['__children__'][key]
                    if isinstance(obj, ConfigObject):
                        found.extend(obj._find_(find_keys[1:]))
            else:
                for key in self.keys():
                    obj = self.__dict__['__children__'][first_key]
                    path = '%s.%s' % (self._path(), first_key)
                    if isinstance(obj, ConfigObject):
                        found.append( (path, obj.asDict()) )
                    else:
                        found.append( (path, obj) )
        else:
            if first_key in self.__dict__['__children__']:
                if len(find_keys) > 1:
                    obj = self.__dict__['__children__'][first_key]
                    if isinstance(obj, ConfigObject):
                        found.extend(obj._find_(find_keys[1:]))
                else:
                    obj = self.get(first_key, GETATTR_FAILED)
                    if obj is not GETATTR_FAILED:
                        path = '%s.%s' % (self._path(), first_key)
                        if isinstance(obj, ConfigObject):
                            found.append( (path, obj.asDict()) )
                        else:
                            found.append( (path, obj) )
        return found

    def _follow_path_(self, path):
        """ follows a path to the last ConfigObject
        """
        if '.' in path:
            dot = path.find('.')
            name = path[:dot]
            if self.__dict__['__children__'].has_key(name):
                child = self.__dict__['__children__'][name]
                if isinstance(child, ConfigObject):
                    return child._follow_path_(path[dot+1:])
            return self, path

        # not a dotted path
        elif self.__dict__['__children__'].has_key(path):
            # path refers to one of my attributes, return self
            child = self.__dict__['__children__'][name]
            if isinstance(child, ConfigObject): return child, None
            else: return self, None

        return FOLLOW_FAILED

    def _getAttributeValue_(self, path, default=GETATTR_FAILED):
        if isinstance(path, basestring):
            if path.startswith('__') and self.__dict__.has_key(path):
                return self.__dict__[path]

            dot = path.find('.')
            if dot > 0:
                attr_key = path[:dot]
                if self.parent is None and self._is_my_name_(attr_key):
                    return self._getAttributeValue_(path[dot+1:], default)
                if self.__dict__['__children__'].has_key(attr_key):
                    obj = self.__dict__['__children__'][attr_key]
                    if isinstance(obj, ConfigObject):
                        return obj._getAttributeValue_(path[dot+1:], default)
            else:
                if path == 'dict': return self.asDict()
                elif path.isdigit()\
                and self.__dict__['__children__'].has_key(int(path)):
                    return self.__dict__['__children__'][int(path)]

        if self.has_key(path): return self.__dict__['__children__'][path]
        else: return default

    def _ingest_(self, key, value):
        if self.has_key(key): self._deleteChild_(key)

        if isinstance(value, dict):
            child = ConfigObject(key, self)
            for key_, value_ in value.items():
                child._ingest_(key_, value_)
            self.__dict__['__children__'][key] = child
        elif isinstance(value, ConfigObject):
            self.__dict__['__children__'][key] = value.copy(parent=self)
        else:
            self.__dict__['__children__'][key] = value

    def _is_my_name_(self, name):
        return name == self.name

    def _setAttributeValue_(self, path, value):
        if isinstance(path, basestring):
            if not path.startswith('__'):
                dot = path.find('.')
                if dot > 0:
                    attr_key = path[:dot]
                    if self.__dict__['__children__'].has_key(attr_key):
                        obj = self.__dict__['__children__'][attr_key]
                    else: obj = self.newChild(attr_key)
                    obj._setAttributeValue_(path[dot+1:], value)
                else: self._ingest_(path, value)
            else: self.__dict__[path] = value
        else: self._ingest_(path, value)

    def _top_(self):
        if self.parent is not None:
            return self.parent._top_()
        return self

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    #
    # overrides for builtin methods
    #
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __contains__(self, key):
        return key in self.child_names

    def __delitem__(self, path): self._deleteTree_(path)

    def __getattr__(self, path):
        value = self._getAttributeValue_(path, GETATTR_FAILED)
        try:
            if value != GETATTR_FAILED: return value
        except: # will get here if value is an 'object'
            return value
        raise KeyError, "'%s' is an invalid key" % path

    def __getitem__(self, path):
        value = self._getAttributeValue_(path)
        if value is not None: return value
        raise KeyError, "'%s' is an invalid key" % path

    def __hash__(self):
        hash_key = list(self.keys())
        hash_key.insert(0, self.path)
        return hash(tuple(hash_key))

    def __iter__(self):
        for key in self.keys(): yield key

    def __len__(self):
        return len(self.__dict__['__children__'])

    def __repr__(self):
        description = "<instance of class '%s' named '%s' with children '%s'>"
        children = [child for child in self.__dict__['__children__']]
        return description % (self.__class__.__name__, self.name,
                              ', '.join(children))

    def __set__(self, path, value):
        self._setAttributeValue_(path, value)

    def __setitem__(self, path, value):
        self._setAttributeValue_(path, value)

    def __setattr__(self, path, value):
        self._setAttributeValue_(path, value)

    def __str__(self):
        return str(self.asDict())

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # comparison operators
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __eq__(self, other):
        if isinstance(other, ConfigObject):
            return hash(self) == hash(other)
        return False

    def __ge__(self, other):
        if isinstance(other, ConfigObject):
            return hash(self) >= hash(other)
        return False

    def __gt__(self, other):
        if isinstance(other, ConfigObject):
            return hash(self) > hash(other)
        return False

    def __le__(self, other):
        if isinstance(other, ConfigObject):
            return hash(self) <= hash(other)
        return False

    def __lt__(self, other):
        if isinstance(other, ConfigObject):
            return hash(self) < hash(other)
        return True

    def __ne__(self, other): return not self.__eq__(other)


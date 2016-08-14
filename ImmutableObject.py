#A DOOP Immutable Object
import uuid
from Field import Field
from ChangeType import *
from FieldList import FieldList
from operator import itemgetter
import hashlib


class ImmutableObject(object):
    
    def __init__(self, **kwargs):
        self.insetup = True
        self.doop_field = dict()
        variables = [a for a in dir(self.__class__) if not a.startswith('__') and not callable(getattr(self.__class__,a))]
        for k in variables:
            var = getattr(self.__class__, k)
            self.doop_field[k] = var
            assert isinstance(var, FieldList) == False #Immutable objects not allow references to other objects just use a FieldText as a key
            if isinstance(var, Field):
                setattr(self, k, var.CreateInstance(self, k))
                if k in kwargs:
                    setattr(self, k, kwargs[k])
        self._prevhash = kwargs['_prevhash'] if '_prevhash' in kwargs else ''
            
        self.insetup = False
        
    def __setattr__(self, name, value):
        if name == "insetup":
            super(ImmutableObject, self).__setattr__(name, value)
            return
        if not self.insetup:
            assert False #Attempting to change an immutable object
            return
        super(ImmutableObject, self).__setattr__(name, value)

    def GetHash(self):
        #Immutable objects don't have UUIDs have have SHA1 hashes of their content
        s = sorted([(k,str(getattr(self, k))) for (k,v) in self.doop_field.iteritems()], key=itemgetter(0)) + [('_prevhash', str(self._prevhash))]

        return hashlib.sha256(str(s)).hexdigest()
        
    def asDict(self):
        #Return a dict suitable for transport
        ret = dict()
        for k in self.doop_field:
            ret[k] = getattr(self, k)
        ret["_prevhash"] = self._prevhash
        ret["classname"] = self.__class__.__name__
        ret["hash"] = self.GetHash()
        return ret

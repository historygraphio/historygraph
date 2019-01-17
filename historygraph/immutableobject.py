# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A HistoryGraph Immutable Object
import uuid
from .changetype import *
from . import fields
from operator import itemgetter
import hashlib
import six

class ImmutableObject(object):
    is_singleton = False


    def __init__(self, **kwargs):
        # Initialise the immutable object from the kwargs. It can never be changed once initialise
        self.insetup = True
        self._field = dict()
        variables = [a for a in dir(self.__class__) if not a.startswith('__') and not callable(getattr(self.__class__,a))]
        for k in variables:
            var = getattr(self.__class__, k)
            self._field[k] = var
            assert isinstance(var, fields.Collection) == False #Immutable objects not allow references to other objects just use a FieldText as a key
            if isinstance(var, fields.Field):
                setattr(self, k, var.create_instance(self, k))
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

    def get_hash(self):
        #Immutable objects don't have UUIDs they have SHA256 hashes of their content
        s = sorted([(k,str(getattr(self, k))) for (k,v) in six.iteritems(self._field)], key=itemgetter(0)) + [('_prevhash', str(self._prevhash))]

        return hashlib.sha256(str(s)).hexdigest()

    def as_dict(self):
        #Return a dict suitable for transport
        ret = dict()
        for k in self._field:
            ret[k] = getattr(self, k)
        ret["_prevhash"] = self._prevhash
        ret["classname"] = self.__class__.__name__
        ret["hash"] = self.get_hash()
        return ret

    def get_is_deleted(self):
        return False

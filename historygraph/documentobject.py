# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A HistoryGraph Document Object
import uuid
from .changetype import *
from . import fields

class DocumentObject(object):
    def Clone(self):
        ret = self.__class__(self.id)
        ret.CopyDocumentObject(self)
        for prop in self._field:
            if isinstance(prop, fields.Collection):
                retlist = ret.getattr(prop.name)
                retlist.empty()
                for obj in prop:
                    retlist.add(obj.Clone())
        return ret
    
    def __init__(self, id=None):
        self.insetattr = True
        self._field = dict()
        self.change_handlers = list()
        self.parent = None
        if id is None:
            id = str(uuid.uuid4())
        self.id = id
        variables = [a for a in dir(self.__class__) if not a.startswith('__') and not callable(getattr(self.__class__,a))]
        for k in variables:
            var = getattr(self.__class__, k)
            self._field[k] = var
            if isinstance(var, fields.Field):
                setattr(self, k, var.CreateInstance(self, k))
        self.insetattr = False
        
    def __setattr__(self, name, value):
        super(DocumentObject, self).__setattr__(name, value)
        if name == "insetattr" or self.insetattr:
            return
        self.insetattr = True
        if name in self._field:
            if type(self._field[name]) != fields.Collection and type(self._field[name]) != fields.IntCounter and type(self._field[name]) != fields.List:
                self.WasChanged(ChangeType.SET_PROPERTY_VALUE, self.id, name, value, self._field[name].GetTypeName())
        self.insetattr = False
        for h in self.change_handlers:
            h(self)
         
    def WasChanged(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
        if self.parent is not None:
            assert isinstance(propertyownerid, basestring)
            self.parent.WasChanged(changetype, propertyownerid, propertyname, propertyvalue, propertytype)

    def CopyDocumentObject(self, src):
        for k in src._field:
            v = src._field[k]
            setattr(self, k, v.Clone(k, src, self))

    def GetDocument(self):
        #Return the document
        return self.parent.GetDocument()

    def __str__(self):
        return '\n'.join([str(k) + ':' + str(getattr(self, k)) for k in self._field])

    def AddHandler(self, h):
        self.change_handlers.append(h)

    def RemoveHandler(self, h):
        self.change_handlers.remove(h)


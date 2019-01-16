# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A HistoryGraph Document Object
import uuid
from .changetype import *
from . import fields

class DocumentObject(object):
    is_singleton = False

    def clone(self):
        # Make a copy of this object and return it
        ret = self.__class__(self.id)
        ret.copy_document_object(self)
        for prop in self._field:
            #TODO: There should be a similar test for field.List members
            if isinstance(prop, fields.Collection):
                retlist = ret.getattr(prop.name)
                retlist.empty()
                for obj in prop:
                    retlist.add(obj.clone())
        ret._is_deleted = self._is_deleted
        return ret

    def __init__(self, id=None):
        self.insetattr = True
        self.dc = None
        self._field = dict()
        self.change_handlers = list()
        self.parent = None
        if id is None:
            id = str(uuid.uuid4())
        self.id = id
        # Get the fields from the class and create an instance of each one for this instance
        variables = [a for a in dir(self.__class__) if not a.startswith('__')
                     and not callable(getattr(self.__class__,a))
                     and a != 'is_singleton']
        for k in variables:
            var = getattr(self.__class__, k)
            self._field[k] = var
            if isinstance(var, fields.Field):
                setattr(self, k, var.create_instance(self, k))
        self._is_deleted = False
        self.insetattr = False

    def __setattr__(self, name, value):
        # Handle setting an attribute and building the HistoryGraph edge that represents it
        super(DocumentObject, self).__setattr__(name, value)
        if name == "insetattr" or self.insetattr:
            return
        self.insetattr = True
        if name in self._field:
            assert self.get_document().dc is not None
            if type(self._field[name]) == fields.ForeignKey:
                self.was_changed(ChangeType.SET_PROPERTY_VALUE, self.id, name,
                                 '' if value is None else value.id,
                                 self._field[name].get_type_name())
            elif type(self._field[name]) != fields.Collection and \
               type(self._field[name]) != fields.IntCounter and \
               type(self._field[name]) != fields.List:
                self.was_changed(ChangeType.SET_PROPERTY_VALUE, self.id, name,
                                 value, self._field[name].get_type_name())
        self.insetattr = False
        for h in self.change_handlers:
            h(self)

    def was_changed(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
        # If we are just a document object cascade the changes up to the parent
        if self.parent is not None:
            assert isinstance(propertyownerid, basestring)
            self.parent.was_changed(changetype, propertyownerid, propertyname, propertyvalue, propertytype)

    def copy_document_object(self, src):
        self.dc = src.dc
        self.insetattr = True
        for k in src._field:
            v = src._field[k]
            setattr(self, k, v.clone(k, src, self))
        self.insetattr = False

    def get_document(self):
        #Return the document
        return self.parent.get_document()

    def __str__(self):
        # Return a string representation which is useful for debugging
        return '\n'.join([str(k) + ':' + str(getattr(self, k)) for k in
                          self._field])

    def add_handler(self, h):
        self.change_handlers.append(h)

    def remove_handler(self, h):
        self.change_handlers.remove(h)

    def delete(self, create_edge=True):
        # Mark as deleted
        self._is_deleted = True
        if create_edge:
            self.was_changed(ChangeType.DELETE_DOCUMENT_OBJECT, self.id, '', '', '')
        # If we have a parent remove ourselves from any collections or lists
        if self.parent is not None and hasattr(self.parent, 'remove_by_objid'):
            self.parent.remove_by_objid(self.id, create_edge=False)
        # If we have any children cascade this deletion to them
        for k, v in self._field.iteritems():
            v.cascade_delete(self, k)


    def get_is_deleted(self):
        return self._is_deleted

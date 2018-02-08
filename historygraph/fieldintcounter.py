# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#An integer register field in HistoryGraph
from .field import Field
from .changetype import ChangeType

class FieldIntCounter(Field):
    class FieldIntCounterImpl(object):
        def __init__(self, owner, name):
            self.parent = owner
            self.name = name
            self.value = 0

        def add(self, change):
            self.value += change
            self.WasChanged(ChangeType.ADD_INT_COUNTER, self.parent.id, self.name, change, "FieldIntCounter")

        def subtract(self, change):
            self.value -= change
            self.WasChanged(ChangeType.ADD_INT_COUNTER, self.parent.id, self.name, -change, "FieldIntCounter")

        def get(self):
            return self.value

        def WasChanged(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
            assert isinstance(propertyownerid, basestring)
            self.parent.WasChanged(changetype, propertyownerid, propertyname, propertyvalue, propertytype)

        def Clone(self, owner, name):
            ret = FieldIntCounter.FieldIntCounterImpl(self.parent, self.name)
            ret.value = self.value
            return ret

        def Clean(self):
            self.value = 0


    def CreateInstance(self, owner, name):
        return FieldIntCounter.FieldIntCounterImpl(owner, name)

    def Clone(self, name, src, owner):
        return getattr(src, name).Clone(owner, name)

    def TranslateFromString(self, s):
        return int(s)

    def Clean(self, owner, name):
        return getattr(owner, name).Clean()


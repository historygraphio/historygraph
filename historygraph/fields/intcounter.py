# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#An integer register field in HistoryGraph
from . import Field
from ..changetype import ChangeType

class IntCounter(Field):
    class _FieldIntCounterImpl(object):
        def __init__(self, owner, name):
            self.parent = owner
            self.name = name
            self.value = 0

        def add(self, change):
            self.value += change
            self.was_changed(ChangeType.ADD_INT_COUNTER, self.parent.id, self.name, change, "IntCounter")

        def subtract(self, change):
            self.value -= change
            self.was_changed(ChangeType.ADD_INT_COUNTER, self.parent.id, self.name, -change, "IntCounter")

        def get(self):
            return self.value

        def was_changed(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
            assert isinstance(propertyownerid, basestring)
            if not self.parent.insetattr:
                self.parent.was_changed(changetype, propertyownerid, propertyname, propertyvalue, propertytype)

        def clone(self, owner, name):
            ret = IntCounter._FieldIntCounterImpl(self.parent, self.name)
            ret.value = self.value
            return ret

        def clean(self):
            self.value = 0


    def create_instance(self, owner, name):
        return IntCounter._FieldIntCounterImpl(owner, name)

    def clone(self, name, src, owner):
        return getattr(src, name).clone(owner, name)

    def translate_from_string(self, s):
        return int(s)

    def clean(self, owner, name):
        return getattr(owner, name).clean()


# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#An integer register field in HistoryGraph
from . import Field
from ..changetype import ChangeType
from decimal import Decimal


class DecimalCounter(Field):
    class _FieldDecimalCounterImpl(object):
        # This implementation class is what actually get attacted to the document object to implement the required
        # behaviour
        def __init__(self, owner, name):
            self.parent = owner
            self.name = name
            self.value = Decimal('0')

        def add(self, change):
            self.value += change
            self.was_changed(ChangeType.ADD_DECIMAL_COUNTER, self.parent.id, self.name, change, "DecimalCounter")

        def subtract(self, change):
            self.value -= change
            self.was_changed(ChangeType.ADD_DECIMAL_COUNTER, self.parent.id, self.name, -change, "DecimalCounter")

        def get(self):
            return self.value

        def was_changed(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
            # TODO: Possible balloonian function
            assert isinstance(propertyownerid, basestring)
            if not self.parent.insetattr:
                self.parent.was_changed(changetype, propertyownerid, propertyname, propertyvalue, propertytype)

        def clone(self, owner, name):
            ret = DecimalCounter._FieldDecimalCounterImpl(self.parent, self.name)
            ret.value = self.value
            return ret

        def clean(self):
            self.value = Decimal('0')


    def create_instance(self, owner, name):
        return DecimalCounter._FieldDecimalCounterImpl(owner, name)

    def clone(self, name, src, owner):
        return getattr(src, name).clone(owner, name)

    def translate_from_string(self, s):
        return Decimal(s)

    def clean(self, owner, name):
        return getattr(owner, name).clean()

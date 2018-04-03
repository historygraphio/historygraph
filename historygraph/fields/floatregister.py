# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#An integer register field in HistoryGraph
from . import Field

class FloatRegister(Field):
    def create_instance(self, owner, name):
        return 0.0

    def translate_from_string(self, s):
        return float(s)

    def clone(self, propertyname, src, owner):
        return getattr(src, propertyname)

    def get_type_name(self):
        return "float"

    def clean(self, owner, name):
        pass

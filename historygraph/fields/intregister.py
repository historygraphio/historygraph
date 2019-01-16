# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#An integer register field in HistoryGraph
from . import Field

class IntRegister(Field):
    def create_instance(self, owner, name):
        return 0

    def translate_from_string(self, s, dc):
        return int(s)

    def clone(self, propertyname, src, owner):
        return getattr(src, propertyname)

    def get_type_name(self):
        return "int"

    def clean(self, owner, name):
        pass

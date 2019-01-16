# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A text field in a HistoryGraph object
from . import Field

class CharRegister(Field):
    def create_instance(self, owner, name):
        return ""

    def translate_from_string(self, s, dc):
        return s

    def clone(self, propertyname, src, owner):
        return getattr(src, propertyname)

    def get_type_name(self):
        return "basestring"

    def clean(self, owner, name):
        pass

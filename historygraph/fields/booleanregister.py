# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A boolean register field in HistoryGraph
from . import Field
import six


class BooleanRegister(Field):
    def create_instance(self, owner, name):
        return False

    def translate_from_string(self, s, dc):
        if isinstance(s, six.string_types):
            return s == "True"
        else:
            return s

    def clone(self, propertyname, src, owner):
        return getattr(src, propertyname)

    def get_type_name(self):
        return "boolean"

    def clean(self, owner, name):
        pass

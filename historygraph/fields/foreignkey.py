# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A text field in a HistoryGraph object
from . import Field

class ForeignKey(Field):
    def __init__(self, cls):
        self.cls = cls
        super(ForeignKey, self).__init__()

    def create_instance(self, owner, name):
        return None

    def translate_from_string(self, s, dc):
        if s == '':
            return None
        else:
            return dc.get_object_by_id(self.cls.__name__, s)

    def clone(self, propertyname, src, owner):
        return getattr(src, propertyname)

    def get_type_name(self):
        return "foreignkey"

    def clean(self, owner, name):
        pass

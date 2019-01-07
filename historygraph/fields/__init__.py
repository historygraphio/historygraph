# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function
# A field in a HistoryGraph object


class Field(object):
    def cascade_delete(self, owner, name):
        # The owning object is being deleted cascade onto it's children
        pass


from .intregister import IntRegister
from .collection import Collection
from .charregister import CharRegister
from .intcounter import IntCounter
from .list import List
from .floatregister import FloatRegister
from .booleanregister import BooleanRegister

# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

from historygraph.edges import AddIntCounter

def int_counter_integer_value(edge, historygraph):
    if isinstance(edge, AddIntCounter):
        try:
            int(edge.propertyvalue)
            return True
        except ValueError:
            return False
    return True

# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#Add list of all of the possible change types that can happen to a document object

class ChangeType(object):
    SET_PROPERTY_VALUE = 0
    ADD_CHILD = 1
    REMOVE_CHILD = 2
    ADD_INT_COUNTER = 3
    ADD_LISTITEM = 4 
    REMOVE_LISTITEM = 5 

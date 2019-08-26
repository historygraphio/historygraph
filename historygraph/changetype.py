# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function


class ChangeType(object):
    # A list of all of the possible change types that can happen to a document
    SET_PROPERTY_VALUE = 0
    ADD_CHILD = 1
    REMOVE_CHILD = 2
    ADD_INT_COUNTER = 3
    ADD_LISTITEM = 4
    REMOVE_LISTITEM = 5
    DELETE_DOCUMENT_OBJECT = 6
    ADD_FLOAT_COUNTER = 7
    ADD_DECIMAL_COUNTER = 8
    ADD_TEXTEDIT_FRAGMENT = 9
    

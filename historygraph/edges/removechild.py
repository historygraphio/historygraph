# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A HistoryGraph edge that removes a child
from . import Edge
import six


class RemoveChild(Edge):
    def __init__(self, startnodes, propertyownerid,
                 propertyname, propertyvalue, propertytype, documentid,
                 documentclassname, sessionid, transaction_hash=''):
        super(RemoveChild, self).__init__(startnodes, documentid,
            documentclassname, sessionid, transaction_hash)
        assert isinstance(propertyownerid, six.string_types)
        assert isinstance(propertytype, six.string_types)
        assert isinstance(propertyvalue, six.string_types)
        self.propertyownerid = propertyownerid
        self.propertyname = propertyname
        self.propertyvalue = propertyvalue
        self.propertytype = propertytype

    def replay(self, doc):
        # Remove the item if it's parent exits
        if doc.has_document_object(self.propertyownerid):
            parent = doc.get_document_object(self.propertyownerid)
            getattr(parent, self.propertyname).remove(self.propertyvalue)

    def clone(self):
        return RemoveChild(self._start_hashes,
            self.propertyownerid, self.propertyname, self.propertyvalue,
            self.propertytype, self.documentid, self.documentclassname,
            self.sessionid, self.transaction_hash)

    def get_conflict_winner(self, edge2, doc_obj_heirachy):
        return 0

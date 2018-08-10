# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#The edge representing adding a child object in HistoryGraph
from . import Edge
from json import JSONEncoder, JSONDecoder

class RemoveListItem(Edge):
    def __init__(self, startnodes, propertyownerid,
                 propertyname, propertyvalue, propertytype, documentid, documentclassname, nonce='', transaction_hash=''):
        super(RemoveListItem, self).__init__(startnodes, documentid, documentclassname, nonce, transaction_hash)
        assert isinstance(propertyownerid, basestring)
        assert isinstance(propertytype, basestring)
        assert isinstance(propertyvalue, basestring)
        self.propertyownerid = propertyownerid
        self.propertyname = propertyname
        self.propertyvalue = propertyvalue
        self.propertytype = propertytype
        self.transaction_hash = transaction_hash

    def replay(self, doc):
        # Remove the item if it's parent exits
        if doc.has_document_object(self.propertyownerid):
            parent = doc.get_document_object(self.propertyownerid)
            getattr(parent, self.propertyname).remove_by_nodeid(self.propertyvalue)

    def clone(self):
        return RemoveListItem(self._start_hashes, 
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype, self.documentid, self.documentclassname, self.nonce, self.transaction_hash)

    def get_conflict_winner(self, edge2):
        return 0

    
        

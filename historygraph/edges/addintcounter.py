# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#An edge that changes a value in a document
from . import Edge
import uuid

class AddIntCounter(Edge):
    def __init__(self, startnodes, propertyownerid,
                 propertyname, propertyvalue, propertytype, documentid,
                 documentclassname, nonce='', transaction_hash=''):
        if nonce == '':
            # If the nonce isn't set it
            nonce = str(uuid.uuid4())
        super(AddIntCounter, self).__init__(startnodes, documentid, documentclassname, nonce, transaction_id)
        assert isinstance(propertyownerid, basestring)
        assert isinstance(propertytype, basestring), "propertytype should be basestring but it actually is " + str(type(propertytype))
        assert propertytype == 'int' or propertytype == 'basestring' or propertytype == 'IntCounter', "Unexpected property type, actually got " + propertytype
        self.propertyownerid = propertyownerid
        self.propertyname = propertyname
        self.propertyvalue = propertyvalue
        self.propertytype = propertytype

    def replay(self, doc):
        if self.inactive:
            return
        if doc.has_document_object(self.propertyownerid):
            # Find the relevant field on the relavant document object and increment/decrement it's value
            edgeobject = doc.get_document_object(self.propertyownerid)
            field = edgeobject._field[self.propertyname]
            getattr(edgeobject, self.propertyname).add(field.translate_from_string(self.propertyvalue))

    def clone(self):
        return AddIntCounter(self._start_hashes,
                self.propertyownerid, self.propertyname, self.propertyvalue,
                self.propertytype, self.documentid, self.documentclassname, self.nonce, self.transaction_id)

    def get_conflict_winner(self, edge2):
        return 0 # Counter CRDT edges can never conflict

    #def get_edge_description(self):
    #    #Return a description of the edgeuseful for debugging purposes
    #    return "Edge type = " + self.__class__.__name__ + " edgeid = " + self.edgeid + " start nodes = " + str(self._start_hashes) + " end node = " + self.endnode + "  self.propertyname = " +  self.propertyname + " self.propertyvalue = " + self.propertyvalue + " self.propertytype = " + str(self.propertytype)

# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#An edge that changes a value in a document
from . import Edge

class SimpleProperty(Edge):
    def __init__(self, startnodes, propertyownerid,
                 propertyname, propertyvalue, propertytype, documentid,
                 documentclassname, nonce='', transaction_hash=''):
        super(SimpleProperty, self).__init__(startnodes, documentid, documentclassname, nonce, transaction_hash)
        assert isinstance(propertyownerid, basestring)
        assert isinstance(propertytype, basestring)
        assert propertytype == 'int' or propertytype == 'basestring' or propertytype == 'float'
        self.propertyownerid = propertyownerid
        self.propertyname = propertyname
        self.propertyvalue = propertyvalue
        self.propertytype = propertytype

    def replay(self, doc):
        if self.inactive:
            return
        if doc.has_document_object(self.propertyownerid):
            # Is needed if the document object has been deleted somewhere else
            edgeobject = doc.get_document_object(self.propertyownerid)
            field = edgeobject._field[self.propertyname]
            setattr(edgeobject, self.propertyname, field.translate_from_string(self.propertyvalue))

    def clone(self):
        return SimpleProperty(self._start_hashes,
                self.propertyownerid, self.propertyname, self.propertyvalue,
                self.propertytype, self.documentid, self.documentclassname,
                self.nonce, self.transaction_id)

    def get_conflict_winner(self, edge2):
        # For a numeric register the maximum value is the conflict winner
        # For a character register the minimum value is the conflict winner
        if self.propertyownerid != edge2.propertyownerid:
            return 0
        if self.propertyname != edge2.propertyname:
            return 0
        if self.propertytype == "int":
            if int(self.propertyvalue) > int(edge2.propertyvalue):
                return -1
            else:
                return 1
        elif self.propertytype == "basestring":
            if self.propertyvalue > edge2.propertyvalue:
                return -1
            else:
                return 1
        elif self.propertytype == "float":
            if float(self.propertyvalue) > float(edge2.propertyvalue):
                return -1
            else:
                return 1
        else:
            assert False
            return 0

    #def get_edge_description(self):
    #    #Return a description of the edgeuseful for debugging purposes
    #    return "Edge type = " + self.__class__.__name__ + " edgeid = " + self.edgeid + " start nodes = " + str(self._start_hashes) + " end node = " + self.endnode + "  self.propertyname = " +  self.propertyname + " self.propertyvalue = " + self.propertyvalue + " self.propertytype = " + str(self.propertytype)

# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#The edge representing adding a child object in HistoryGraph
from . import Edge

class AddChild(Edge):
    def __init__(self, startnodes, propertyownerid, propertyname, propertyvalue, propertytype, documentid, documentclassname, nonce=''):
        super(AddChild, self).__init__(startnodes, documentid, documentclassname, nonce)
        assert isinstance(propertyownerid, basestring)
        assert isinstance(propertytype, basestring)
        assert isinstance(propertyvalue, basestring)
        self.propertyownerid = propertyownerid
        self.propertyvalue = propertyvalue
        self.propertyname = propertyname
        self.propertytype = propertytype

    def replay(self, doc):
        objid = self.propertyvalue
        if objid not in doc.documentobjects:
            newobj = doc.dc.classes[self.propertytype](objid)
            newobj.dc = doc.dc
            doc.documentobjects[newobj.id] = newobj
        else:
            newobj = doc.documentobjects[objid]
        if isinstance(self, AddChild) and self.propertyownerid == "" and self.propertyname == "":
            pass #There is no parent object and this edge is creating a stand alone object
        else:
            if doc.has_document_object(self.propertyownerid):
                parent = doc.get_document_object(self.propertyownerid)
                getattr(parent, self.propertyname).add(newobj)

    def clone(self):
        return AddChild(self._start_hashes, 
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype, self.documentid, self.documentclassname, self.nonce)

    def get_conflict_winner(self, edge2):
        return 0 #There can never be a conflict because all edges are new

    
        

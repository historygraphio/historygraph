# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#The edge representing adding a child object in HistoryGraph
from . import Edge
import six


class AddChild(Edge):
    def __init__(self, startnodes, propertyownerid, propertyname, propertyvalue,
                 propertytype, documentid, documentclassname, sessionid, transaction_hash=''):
        super(AddChild, self).__init__(startnodes, documentid, documentclassname, sessionid, transaction_hash)
        assert isinstance(propertyownerid, six.string_types)
        assert isinstance(propertytype, six.string_types)
        assert isinstance(propertyvalue, six.string_types)
        self.propertyownerid = propertyownerid
        self.propertyvalue = propertyvalue
        self.propertyname = propertyname
        self.propertytype = propertytype

    def replay(self, doc):
        # Create the document object if it does not already exist
        objid = self.propertyvalue
        if objid not in doc.documentobjects:
            newobj = doc.dc.classes[self.propertytype](objid)
            newobj.dc = doc.dc
            doc.documentobjects[newobj.id] = newobj
        else:
            newobj = doc.documentobjects[objid]
        if isinstance(self, AddChild) and self.propertyownerid == "" and \
           self.propertyname == "":
            pass #There is no parent object and this edge is creating a stand alone object
        else:
            if doc.has_document_object(self.propertyownerid):
                # Make sure the document exists before going too far
                parent = doc.get_document_object(self.propertyownerid)
                getattr(parent, self.propertyname).add(newobj)

    def clone(self):
        return AddChild(self._start_hashes,
            self.propertyownerid, self.propertyname, self.propertyvalue,
            self.propertytype, self.documentid, self.documentclassname,
            self.sessionid, self.transaction_hash)

    def get_conflict_winner(self, edge2, doc_obj_heirachy):
        return 0 #There can never be a conflict because all edges are new

    def get_heirachy_update(self):
        # Return a dict of the heirachy change made by this edge
        # key = the id of this object
        # value = the id of the parent
        return {self.propertyvalue: self.propertyownerid}

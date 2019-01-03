# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#The edge representing delete a document object from a HistoryGraph
from . import Edge

class DeleteDocumentObject(Edge):
    def __init__(self, startnodes, propertyownerid, propertyname, propertyvalue,
                 propertytype, documentid, documentclassname, nonce='', transaction_hash=''):
        super(DeleteDocumentObject, self).__init__(startnodes, documentid, documentclassname, nonce, transaction_hash)
        assert isinstance(propertyownerid, basestring)
        assert isinstance(propertytype, basestring)
        assert isinstance(propertyvalue, basestring)
        self.propertyownerid = propertyownerid
        self.propertyvalue = propertyvalue
        self.propertyname = propertyname
        self.propertytype = propertytype

    def replay(self, doc):
        if self.inactive:
            return
        # Create the document object if it does not already exist
        objid = self.propertyownerid
        if doc.dc.has_object_by_id(self.documentclassname, objid):
            obj = doc.dc.get_object_by_id(self.documentclassname, objid)
            obj._is_deleted = True
            if obj.parent:
                obj.parent.remove_by_objid(objid)

    def clone(self):
        return DeleteDocumentObject(self._start_hashes,
            self.propertyownerid, self.propertyname, self.propertyvalue,
            self.propertytype, self.documentid, self.documentclassname,
            self.nonce, self.transaction_hash)

    def get_conflict_winner(self, edge2):
        # Deleting a document object always loses a conflict with anything
        # other than another deletion (which is a draw)
        if self.propertyownerid != edge2.propertyownerid:
            return 0
        if isinstance(edge2, DeleteDocumentObject):
            return 0 # Deletion edges never conflict
        return 1 # The other edge always wins

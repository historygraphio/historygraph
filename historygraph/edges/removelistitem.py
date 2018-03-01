# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#The edge representing adding a child object in HistoryGraph
from . import Edge
from json import JSONEncoder, JSONDecoder

class RemoveListItem(Edge):
    def __init__(self, startnodes, propertyownerid,
                 propertyname, propertyvalue, propertytype, documentid, documentclassname):
        super(RemoveListItem, self).__init__(startnodes, documentid, documentclassname)
        assert isinstance(propertyownerid, basestring)
        assert isinstance(propertytype, basestring)
        assert isinstance(propertyvalue, basestring)
        self.propertyownerid = propertyownerid
        self.propertyname = propertyname
        self.propertyvalue = propertyvalue
        self.propertytype = propertytype

    def Replay(self, doc):
        parent = doc.GetDocumentObject(self.propertyownerid)
        getattr(parent, self.propertyname).remove_by_nodeid(self.propertyvalue)

    def Clone(self):
        return RemoveListItem(self.startnodes, 
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype, self.documentid, self.documentclassname)

    def GetConflictWinner(self, edge2):
        return 0

    
        

# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#An edge that changes a value in a document
from .historyedge import HistoryEdge
from .fieldintregister import FieldIntRegister

class HistoryEdgeAddIntCounter(HistoryEdge):
    def __init__(self, startnodes, propertyownerid,
                 propertyname, propertyvalue, propertytype, documentid, documentclassname):
        super(HistoryEdgeAddIntCounter, self).__init__(startnodes, documentid, documentclassname)
        assert isinstance(propertyownerid, basestring)
        assert isinstance(propertytype, basestring), "propertytype should be basestring but it actually is " + str(type(propertytype))
        assert propertytype == 'int' or propertytype == 'basestring' or propertytype == 'FieldIntCounter', "Expected int or basestring for property type, actually got " + propertytype
        self.propertyownerid = propertyownerid
        self.propertyname = propertyname
        self.propertyvalue = propertyvalue
        self.propertytype = propertytype

    def Replay(self, doc):
        if self.inactive:
            return
        edgeobject = doc.GetDocumentObject(self.propertyownerid)
        field = edgeobject._field[self.propertyname]
        getattr(edgeobject, self.propertyname).add(field.TranslateFromString(self.propertyvalue))

    def Clone(self):
        return HistoryEdgeAddIntCounter(self.startnodes, 
                self.propertyownerid, self.propertyname, self.propertyvalue,
                self.propertytype, self.documentid, self.documentclassname)

    def GetConflictWinner(self, edge2):
        return 0 # Counter CRDT edges can never conflict

    def GetEdgeDescription(self):
        #Return a description of the edgeuseful for debugging purposes
        return "Edge type = " + self.__class__.__name__ + " edgeid = " + self.edgeid + " start nodes = " + str(self.startnodes) + " end node = " + self.endnode + "  self.propertyname = " +  self.propertyname + " self.propertyvalue = " + self.propertyvalue + " self.propertytype = " + str(self.propertytype)
    

        
        

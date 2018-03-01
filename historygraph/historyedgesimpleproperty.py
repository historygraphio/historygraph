# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#An edge that changes a value in a document
from .historyedge import HistoryEdge

class HistoryEdgeSimpleProperty(HistoryEdge):
    def __init__(self, startnodes, propertyownerid,
                 propertyname, propertyvalue, propertytype, documentid, documentclassname):
        super(HistoryEdgeSimpleProperty, self).__init__(startnodes, documentid, documentclassname)
        assert isinstance(propertyownerid, basestring)
        assert isinstance(propertytype, basestring)
        assert propertytype == 'int' or propertytype == 'basestring'
        self.propertyownerid = propertyownerid
        self.propertyname = propertyname
        self.propertyvalue = propertyvalue
        self.propertytype = propertytype

    def Replay(self, doc):
        if self.inactive:
            return
        edgeobject = doc.GetDocumentObject(self.propertyownerid)
        field = edgeobject._field[self.propertyname]
        setattr(edgeobject, self.propertyname, field.TranslateFromString(self.propertyvalue))

    def Clone(self):
        return HistoryEdgeSimpleProperty(self.startnodes, 
                self.propertyownerid, self.propertyname, self.propertyvalue,
                self.propertytype, self.documentid, self.documentclassname)

    def GetConflictWinner(self, edge2):
        if self.propertyownerid != edge2.propertyownerid:
            return 0
        if self.propertyname != edge2.propertyname:
            assert False
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
        else:
            assert False
            return 0

    def GetEdgeDescription(self):
        #Return a description of the edgeuseful for debugging purposes
        return "Edge type = " + self.__class__.__name__ + " edgeid = " + self.edgeid + " start nodes = " + str(self.startnodes) + " end node = " + self.endnode + "  self.propertyname = " +  self.propertyname + " self.propertyvalue = " + self.propertyvalue + " self.propertytype = " + str(self.propertytype)
    

        
        

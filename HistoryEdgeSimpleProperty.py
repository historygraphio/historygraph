#An edge that changes a value in a document
from HistoryEdge import HistoryEdge
from FieldInt import FieldInt

class HistoryEdgeSimpleProperty(HistoryEdge):
    def __init__(self, edgeid, startnodes, endnode, propertyownerid,
                 propertyname, propertyvalue, propertytype):
        super(HistoryEdgeSimpleProperty, self).__init__(edgeid, startnodes, endnode)
        self.propertyownerid = propertyownerid
        self.propertyname = propertyname
        self.propertyvalue = propertyvalue
        self.propertytype = propertytype

    def Replay(self, doc):
        if self.inactive:
            return
        edgeobject = doc.GetDocumentObject(self.propertyownerid)
        field = edgeobject.doop_field[self.propertyname]
        setattr(edgeobject, self.propertyname, field.TranslateFromString(self.propertyvalue))

    def Clone(self):
        return HistoryEdgeSimpleProperty(self.edgeid, self.startnodes, self.endnode,
                self.propertyownerid, self.propertyname, self.propertyvalue,
                self.propertytype)

    def GetConflictWinner(self, edge2):
        if self.propertyownerid != edge2.propertyownerid:
            return 0
        #print "self.propertyname = " + self.propertyname
        #print "edge2.propertyname = " + edge2.propertyname
        if self.propertyname != edge2.propertyname:
            assert False
            return 0
        #print "self.propertytype = " + str(self.propertytype)
        if self.propertytype == int:
            if int(self.propertyvalue) > int(edge2.propertyvalue):
                return -1
            else:
                return 1
        elif self.propertytype == str:
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
    

        
        

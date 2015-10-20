#The edge representing adding a child object in DOOP
from HistoryEdge import HistoryEdge

class HistoryEdgeAddChild(HistoryEdge):
    def __init__(self, edgeid, startnodes, endnode, propertyownerid, propertyname, propertyvalue, propertytype):
        super(HistoryEdgeAddChild, self).__init__(edgeid, startnodes, endnode)
        self.propertyownerid = propertyownerid
        self.propertyvalue = propertyvalue
        self.propertyname = propertyname
        self.propertytype = propertytype

    def Replay(self, doc):
        parent = self.GetDocumentObject(self.propertyownerid)
        newobj = self.propertytype(self.edgeid)
        getattr(parent, self.propertyname).add(newobj)
        doc.AddDocumentObject(newobj)

    def Clone(self):
        return HistoryEdgeAddChild(self.edgeid, self.startnodes, self.endnode,
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype)

    def GetConflictWinner(self, edge2):
        return 0 #There can never be a conflict becuase all edges are new

    
        

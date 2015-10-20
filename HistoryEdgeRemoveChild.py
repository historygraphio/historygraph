#A DOOP edge that removes a child
from HistoryEdge import HistoryEdge

class HistoryEdgeRemoveChild(HistoryEdge):
    def __init__(self, edgeid, startnodes, endnode, propertyownerid,
                 propertyname, propertyvalue, propertytype):
        super(HistoryEdgeRemoveChild, self).__init__(edgeid, startnodes, endnode)
        self.propertyownerid = propertyownerid
        self.propertyname = propertyname
        self.propertyvalue = propertyvalue
        self.propertytype = propertytype

    def Replay(self, doc):
        parent = doc.GetDocumentObject(self.propertyownerid)
        parent.RemoveChild(self.propertyvalue)

    def Clone(self):
        return HistoryEdgeRemoveChild(self.edgeid, self.startnodes, self.endnode,
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype)

    def GetConflictWinner(self, edge2):
        return 0

    
        

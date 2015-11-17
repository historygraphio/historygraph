#The edge representing adding a child object in DOOP
from HistoryEdge import HistoryEdge

class HistoryEdgeAddChild(HistoryEdge):
    def __init__(self, edgeid, startnodes, endnode, propertyownerid, propertyname, propertyvalue, propertytype):
        super(HistoryEdgeAddChild, self).__init__(edgeid, startnodes, endnode)
        assert isinstance(propertyownerid, basestring)
        self.propertyownerid = propertyownerid
        self.propertyvalue = propertyvalue
        self.propertyname = propertyname
        self.propertytype = propertytype

    def Replay(self, doc):
        parent = doc.GetDocumentObject(self.propertyownerid)
        newobj = self.propertytype(self.propertyvalue)
        getattr(parent, self.propertyname).add(newobj)
        doc.documentobjects[newobj.id] = newobj

    def Clone(self):
        return HistoryEdgeAddChild(self.edgeid, self.startnodes, self.endnode,
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype)

    def GetConflictWinner(self, edge2):
        return 0 #There can never be a conflict becuase all edges are new

    
        

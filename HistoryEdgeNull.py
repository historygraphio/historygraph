#A null edge is used to merge a branched hypergraph back together
from HistoryEdge import HistoryEdge

class HistoryEdgeNull(HistoryEdge):
    def __init__(self, edgeid, startnodes, endnode):
        super(HistoryEdgeNull, self).__init__(edgeid, startnodes, endnode)

    def Clone(self):
        return HistoryEdgeNull(self.edgeid, set(self.startnodes), self.endnode)

    def Replay(self, doc):
        pass
    
    def GetEdgeDescription(self):
        #Return a description of the edgeuseful for debugging purposes
        return "Edge type = " + self.__class__.__name__ + " edgeid = " + self.edgeid + " start nodes = " + str(self.startnodes) + " end node = " + self.endnode

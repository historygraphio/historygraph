#A null edge is used to merge a branched hypergraph back together

class HistoryEdgeNull(HistoryEdge):
    def __init__(self, edgeid, startnodes, endnode):
        super(HistoryEdgeNull, self).__init__(edgeid, startnodes, endnode)

    def Clone(self):
        return HistoryEdgeNull(self.edgeid, m_startnodes, m_endnode)

    

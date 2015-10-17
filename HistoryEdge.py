#The base class for edges in DOOP

class HistoryEdge(object):
    def __init__(self, edgeid, startnodes, endnode):
        self.edgeid = edgeid
        self.startnodes = startnodes
        self.endnode = endnode
        self.inactive = False
        self.played = False

        
    def RecordPastEdges(pastedges, graph):
        self.pastedges = set(pastedges)
        edges = graph.edgesbystartnode(self.endnode)
        pastedges.add(self.edgeid)
        for k in edges:
            edge = edges[k]
            edge.RecordPastEdges(pastedges, graph)

    
    def CanReplay(self, graph):
        for node in self.startnodes:
            if node != "":
                edge = graph.edgebyendnode[node]
                if edge.isplayed == False:
                    return False
        return True

    def ResetPastEdges(self):
        self.pastedges = set()

    def HasPastEdge(self, pastedgeid):
        return pastedgeid in self.pastedges

    def CompareForConflicts(self, edge2):
	if (self.__class__ != pedge2.__class__)
		return; #Different edge types can never conflict
	if (self.inactive || edge2.inactive)
		return; #Inactive edges can never conflict with active edges
	conflictwinner = self.GetConflictWinner(edge2)
	assert conflictwinner == -1 or conflictwinner == 0 or conflictwinner == 1
	if conflictwinner == 1:
            self.inactive = True
	else
            edge2.inactive = True
        
    

#A DOOP history graph
from collections import defaultdict

class HistoryGraph(object):
    def __init__(self):
        self.edgesbystartnode = defaultdict(list)
        self.edgesbyendnode = dict()
        self.edges = dict()
        self.isreplaying = False

    def AddEdge(self, edge):
        if self.isreplaying:
            return
        if edge.id in self.edges:
            return
        nodes = edge.GetStartNodes()
        for node in nodes:
            self.edgesbystartnode[node.id].append(node)
        self.edgesbyendnode[edge.GetEndNode()] = edge
        self.edges[edge.id] = edge

    def Replay(doc):
        self.isreplaying = True
        for k in self.edges:
            edge = self.edges[k]
            edge.isplayed = False
        l = self.edgesbystartnode
        assert len(l) == 1
        self.ReplayEdges(doc, l[0])
        doc.history = self.Clone()
        self.isreplaying = False

    def Clone(self):
        ret = HistoryGraph()
        for k in self.edges:
            edge = self.edges[k]
            ret.AddEdge(edge.Clone())
        return ret

    def ReplayEdges(self):
        if edge.CanReplay() == False:
            return
        edge.Replay(doc)
        edge.isplayed = True
        edges = self.edgesbystartnode[edge.endnode]
        if len(edges) > 0:
            for edge2 in edges:
                self.ReplayEdges(edge2)
        else:
            doc.currentnode = edge.endnode

    def RecordPastEdges(self):
        if len(self.edges) == 0:
            return
        for k in self.edges:
            edge = self.edges[k]
            edge.ResetPastEdges()
        l = self.edgesbystartnode[""]
        assert len(l) == 1
        pastedges = set()
        l[0].RecordPastEdges(pastedges, self)

    def MergeGraphs(self, graph):
        for k in graph.edges:
            edge = graph.edges[k]
            self.AddEdge(edge)
        presentnodes = set()
        for k in self.edges:
            edge = self.edges[k]
            l = self.edgesbystartnode[edge.endnode]
            if len(l) == 0:
                presentnodes.add(edge.endnode)
        if len(presentnodes) > 1:
            assert len(presentnodes) == 2
            nextnode = str(uuid.uuid4())
            nulledge = HistoryEdgeNull(str(uuid.uuid4()), presentnodes, nextnode)
            self.AddEdge(nulledge)

    def ProcessConflictWinners(self):
        for k in self.edges:
            edge = self.edges[k]
            edge.inactive = False
        for k1 in self.edges:
            edge1 = self.edges[k1]
            for k2 in self.edges:
                edge2 = self.edges[k2]

                if k1 != k2:
                    if not edge2.HasPastEdge(k1) and not edge1.HastPastEdge(k2):
                        edge1.CompareForConflicts(edge2)
                        


        

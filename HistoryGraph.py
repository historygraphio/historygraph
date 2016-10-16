#A DOOP history graph
from collections import defaultdict
import uuid
from HistoryEdgeNull import HistoryEdgeNull

class HistoryGraph(object):
    def __init__(self):
        self.edgesbystartnode = defaultdict(list)
        self.edgesbyendnode = dict()
        self.isreplaying = False

    def AddEdges(self, edges):
        if self.isreplaying:
            return
        edges2 = [edge for edge in edges if edge.GetEndNode() not in self.edgesbyendnode]
        if len(edges2) == 0:
            return
        for edge in edges2:
            nodes = edge.startnodes
            for node in nodes:
                self.edgesbystartnode[node].append(edge)
            self.edgesbyendnode[edge.GetEndNode()] = edge

    def Replay(self, doc):
        self.isreplaying = True
        doc.Clean()
        for k in self.edgesbyendnode:
            edge = self.edgesbyendnode[k]
            edge.isplayed = False
        l = self.edgesbystartnode[""]
        assert len(l) == 1
        self.ReplayEdges(doc, l[0])
        doc.history = self.Clone()
        self.isreplaying = False

    def Clone(self):
        ret = HistoryGraph()
        edgeclones = list()
        for k in self.edgesbyendnode:
            edge = self.edgesbyendnode[k]
            edgeclones.append(edge.Clone())
        ret.AddEdges(edgeclones)
        return ret

    def ReplayEdges(self, doc, edge):
        if edge.CanReplay(self) == False:
            return
        #print "Playing edge = ", edge.asDict()
        edge.Replay(doc)
        edge.isplayed = True
        edges = self.edgesbystartnode[edge.GetEndNode()]
        doc.currentnode = edge.GetEndNode()
        for edge2 in edges:
            self.ReplayEdges(doc, edge2)

    def RecordPastEdges(self):
        if len(self.edgesbyendnode) == 0:
            return
        for k in self.edgesbyendnode:
            edge = self.edgesbyendnode[k]
            edge.ResetPastEdges()
        l = self.edgesbystartnode[""]
        assert len(l) == 1
        pastedges = set()
        l[0].RecordPastEdges(pastedges, self)

    def MergeGraphs(self, graph):
        for k in graph.edgesbyendnode:
            edge = graph.edgesbyendnode[k]
            self.AddEdges([edge])
        self.ProcessGraph()

    def ProcessGraph(self):
        presentnodes = set()
        for k in self.edgesbyendnode:
            edge = self.edgesbyendnode[k]
            l = self.edgesbystartnode[edge.GetEndNode()]
            if len(l) == 0:
                presentnodes.add(edge.GetEndNode())
                documentid = edge.documentid
                documentclassname = edge.documentclassname
        if len(presentnodes) > 1:
            nulledge = HistoryEdgeNull(presentnodes, "", "", "", "", documentid, documentclassname)
            self.AddEdges([nulledge])
            if len(presentnodes) > 2:
                self.ProcessGraph()

    def ProcessConflictWinners(self):
        for k in self.edgesbyendnode:
            edge = self.edgesbyendnode[k]
            edge.inactive = False
        for k1 in self.edgesbyendnode:
            edge1 = self.edgesbyendnode[k1]
            for k2 in self.edgesbyendnode:
                edge2 = self.edgesbyendnode[k2]

                #print "edge1 = " + edge1.GetEdgeDescription()
                #print "edge2 = " + edge2.GetEdgeDescription()
                if k1 != k2:
                    if not edge2.HasPastEdge(k1) and not edge1.HasPastEdge(k2):
                        edge1.CompareForConflicts(edge2)
                        
    def HasDanglingEdges(self):
        # A sanity check a graph has dangling edges if there is more than one endnode that does not have a start node
        # It means that a Merge needs to be run
        startnodes = set([k for (k, v) in self.edgesbystartnode.iteritems()])
        endnodes = set([k for (k, v) in self.edgesbyendnode.iteritems()])
        return len(endnodes - startnodes) > 1

    def GetAllEdges(self):
        return [v for (k, v) in self.edgesbyendnode.iteritems()]
        
    def depth(self, currentnode):
        if currentnode == '':
            return 0
        else:
            return self.edgesbyendnode[currentnode].depth(self)
        

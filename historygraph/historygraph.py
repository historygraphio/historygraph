# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A HistoryGraph
from collections import defaultdict
import uuid
from . import edges

class HistoryGraph(object):
    def __init__(self):
        self.edgesbystartnode = defaultdict(list)
        self.edgesbyendnode = dict()
        self.isreplaying = False

    def AddEdges(self, edges_list):
        if self.isreplaying:
            return
        edges2 = [edge for edge in edges_list if edge.get_end_node() not in self.edgesbyendnode]
        if len(edges2) == 0:
            return
        for edge in edges2:
            nodes = edge._start_hashes
            for node in nodes:
                self.edgesbystartnode[node].append(edge)
            self.edgesbyendnode[edge.get_end_node()] = edge

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
        assert doc._clockhash in self.edgesbyendnode, doc._clockhash + ' not found'
        assert doc._clockhash in doc.history.edgesbyendnode, doc._clockhash + ' not found'

    def Clone(self):
        ret = HistoryGraph()
        edgeclones = list()
        for k in self.edgesbyendnode:
            edge = self.edgesbyendnode[k]
            edge2 = edge.Clone()
            edgeclones.append(edge2)
            assert edge.get_end_node() == edge2.get_end_node(), 'Mismatch edge = ' + repr(edge.asDict()) + ', edge2 = ' + repr(edge2.asDict())
        ret.AddEdges(edgeclones)
        return ret

    def ReplayEdges(self, doc, edge):
        if edge.can_replay(self) == False:
            return
        edge.Replay(doc)
        edge.isplayed = True
        edges = self.edgesbystartnode[edge.get_end_node()]
        doc._clockhash = edge.get_end_node()
        for edge2 in edges:
            self.ReplayEdges(doc, edge2)

    def record_past_edges(self):
        if len(self.edgesbyendnode) == 0:
            return
        for k in self.edgesbyendnode:
            edge = self.edgesbyendnode[k]
            edge.reset_past_edges()
        l = self.edgesbystartnode[""]
        assert len(l) == 1
        pastedges = set()
        l[0].record_past_edges(pastedges, self)

    def MergeGraphs(self, graph):
        for k in graph.edgesbyendnode:
            edge = graph.edgesbyendnode[k]
            self.AddEdges([edge])
        self.ProcessGraph()

    def ProcessGraph(self):
        presentnodes = set()
        for k in self.edgesbyendnode:
            edge = self.edgesbyendnode[k]
            l = self.edgesbystartnode[edge.get_end_node()]
            if len(l) == 0:
                presentnodes.add(edge.get_end_node())
                documentid = edge.documentid
                documentclassname = edge.documentclassname
        if len(presentnodes) > 1:
            nulledge = edges.Merge(presentnodes, "", "", "", "", documentid, documentclassname)
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

                if k1 != k2:
                    if not edge2.has_past_edge(k1) and not edge1.has_past_edge(k2):
                        edge1.compare_for_conflicts(edge2)
                        
    def HasDanglingEdges(self):
        # A sanity check a graph has dangling edges if there is more than one endnode that does not have a start node
        # It means that a Merge needs to be run
        startnodes = set([k for (k, v) in self.edgesbystartnode.iteritems()])
        endnodes = set([k for (k, v) in self.edgesbyendnode.iteritems()])
        return len(endnodes - startnodes) > 1

    def GetAllEdges(self):
        return [v for (k, v) in self.edgesbyendnode.iteritems()]
        
    def depth(self, _clockhash):
        if _clockhash == '':
            return 0
        else:
            #if _clockhash not in self.edgesbyendnode:
            #    print ('self.edgesbyendnode=',[e.asTuple() for e in self.edgesbyendnode.values()])
            return self.edgesbyendnode[_clockhash].depth(self)
        

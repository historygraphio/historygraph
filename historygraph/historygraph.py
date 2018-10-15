# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A HistoryGraph
from collections import defaultdict
import uuid
from . import edges

class HistoryGraph(object):
    def __init__(self):
        # We maintain dictionaries by the start and end nodes. The various functions
        # inside this class need to lookup on that basis
        self.edgesbystartnode = defaultdict(list)
        self.edgesbyendnode = dict()
        self.isreplaying = False

    def add_edges(self, edges_list):
        # Add edges to this graph. This only updates the dictionaries
        if self.isreplaying:
            return
        edges2 = [edge for edge in edges_list if edge.get_end_node() not in self.edgesbyendnode]
        for edge in edges2:
            nodes = edge._start_hashes
            for node in nodes:
                self.edgesbystartnode[node].append(edge)
            self.edgesbyendnode[edge.get_end_node()] = edge

    def replay(self, doc):
        # Replay the entrie HistoryGraph. This marks every edge as not played and the starts
        # playing them recursively from the start edge
        self.isreplaying = True
        doc.clean()
        for k in self.edgesbyendnode:
            edge = self.edgesbyendnode[k]
            edge.isplayed = False
        l = self.edgesbystartnode[""]
        assert len(l) == 1
        self.replay_edges(doc, l[0])
        doc.history = self.clone()
        self.isreplaying = False
        assert doc._clockhash in self.edgesbyendnode, doc._clockhash + ' not found'
        assert doc._clockhash in doc.history.edgesbyendnode, doc._clockhash + ' not found'

    def clone(self):
        # Return a copy of this HistoryGraph
        ret = HistoryGraph()
        edgeclones = list()
        for k in self.edgesbyendnode:
            edge = self.edgesbyendnode[k]
            #edge2 = edge.clone()
            #edgeclones.append(edge2)
            edgeclones.append(edge)
            #assert edge.get_end_node() == edge2.get_end_node(), 'Mismatch edge = ' + repr(edge.as_dict()) + ', edge2 = ' + repr(edge2.as_dict())
        ret.add_edges(edgeclones)
        return ret

    def replay_edges(self, doc, edge):
        # Replay this edge and then the next edge.
        if edge.can_replay(self) == False:
            # An edge would not be playable usually if it is a merge and both previous edges have
            # not been played
            return
        edge.replay(doc)
        edge.isplayed = True
        doc._clockhash = edge.get_end_node()
        # Find the next edges and recursively play them
        edges = self.edgesbystartnode[edge.get_end_node()]
        for edge2 in edges:
            self.replay_edges(doc, edge2)

    def has_start_edge(self):
        return len(self.edgesbystartnode[""]) == 1

    def record_past_edges(self):
        # Each edge needs to know which edges are in their past because edges that
        # 'know' about each other can never conflict
        if len(self.edgesbyendnode) == 0:
            return
        # Clear any previous edges
        for k in self.edgesbyendnode:
            edge = self.edgesbyendnode[k]
            edge.reset_past_edges()
        # Get the first edge and then start recuring over it
        l = self.edgesbystartnode[""]
        assert len(l) == 1, 'len(l) == {} should be 1'.format(len(l))
        pastedges = set()
        l[0].record_past_edges(pastedges, self)

    def merge_graphs(self, graph):
        #for k in graph.edgesbyendnode:
        #    edge = graph.edgesbyendnode[k]
        #    self.add_edges([edge])
        self.add_edges(graph.edgesbyendnode.values())
        self.process_graph()

    def process_graph(self):
        # Look over the graph. We are looking for end edges. If there is
        # more than one end node their needs to be a merge
        presentnodes = set()
        for k in self.edgesbyendnode:
            edge = self.edgesbyendnode[k]
            l = self.edgesbystartnode[edge.get_end_node()]
            if len(l) == 0:
                presentnodes.add(edge.get_end_node())
                documentid = edge.documentid
                documentclassname = edge.documentclassname
        if len(presentnodes) > 1:
            presentnodes = list(presentnodes)
            nulledge = edges.Merge(set(presentnodes[:2]), "", "", "", "", documentid, documentclassname)
            self.add_edges([nulledge])
            if len(presentnodes) > 2:
                self.process_graph()

    def process_conflict_winners(self):
        # Iterate over the graph and look for conflict and determine the winners
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

    def has_dangling_edges(self):
        # A sanity check a graph has dangling edges if there is more than one endnode that does not have a start node
        # It means that a Merge needs to be run
        startnodes = set([k for (k, v) in self.edgesbystartnode.iteritems()])
        endnodes = set([k for (k, v) in self.edgesbyendnode.iteritems()])
        return len(endnodes - startnodes) > 1

    def get_all_edges(self):
        return [v for (k, v) in self.edgesbyendnode.iteritems()]

    def depth(self, _clockhash):
        if _clockhash == '':
            return 0
        else:
            return self.edgesbyendnode[_clockhash].depth(self)


class FrozenHistoryGraph(HistoryGraph):
    # This subclass handles the case of a history graph that writes any new edges it receives
    # into the historygraph it was cloned from
    def __init__(self, source_historygraph, source_doc):
        super(FrozenHistoryGraph, self).__init__()
        self.source_historygraph = source_historygraph
        self.source_doc = source_doc
        self.in_init = True
        edgeclones = list()
        for k in self.edgesbyendnode:
            edge = self.edgesbyendnode[k]
            edge2 = edge.clone()
            edgeclones.append(edge2)
            assert edge.get_end_node() == edge2.get_end_node(), 'Mismatch edge = ' + repr(edge.as_dict()) + ', edge2 = ' + repr(edge2.as_dict())
        self.add_edges(edgeclones)
        self.in_init = False

    def add_edges(self, edges_list):
        # When we add edges they also need to go into the source historygraph
        if self.in_init:
            return
        super(FrozenHistoryGraph, self).add_edges(edges_list)
        cloned_edges_list = [e.clone() for e in edges_list]
        self.source_historygraph.add_edges(edges_list)
        self.source_historygraph.process_graph()
        self.source_historygraph.record_past_edges()
        self.source_historygraph.process_conflict_winners()
        self.source_historygraph.replay(self.source_doc)
        for l in self.source_doc.edgeslistener:
            l.edges_added(edges_list)

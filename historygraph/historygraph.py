# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A HistoryGraph
from collections import defaultdict
import uuid
from . import edges
import hashlib
from historygraph.edges import EndTransaction

class HistoryGraph(object):
    def __init__(self):
        # We maintain dictionaries by the start and end nodes. The various functions
        # inside this class need to lookup on that basis
        #self.edgesbystartnode = defaultdict(list)
        self._edgesbyendnode = dict()
        self.isreplaying = False

    def get_edges_by_end_node(self, clockhash):
        return self._edgesbyendnode[clockhash]

    def get_edges_by_start_node(self, clockhash):
        return [edge for edge in self._edgesbyendnode.values() if clockhash in edge._start_hashes]

    def has_edge(self, clockhash):
        # Return true iff we have this edge
        return clockhash in self._edgesbyendnode

    def add_edges(self, edges_list):
        # Add edges to this graph. This only updates the dictionaries
        if self.isreplaying:
            return
        edges2 = [edge for edge in edges_list if edge.get_end_node() not in self._edgesbyendnode]
        #print('add_edges edges2=', [edge.as_dict() for edge in edges2])
        for edge in edges2:
            #nodes = edge._start_hashes
            #for node in nodes:
            #    self.edgesbystartnode[node].append(edge)
            self._edgesbyendnode[edge.get_end_node()] = edge

    def replay(self, doc):
        # Replay the entrie HistoryGraph. This marks every edge as not played and the starts
        # playing them recursively from the start edge
        self.isreplaying = True
        doc.clean()
        for edge in self.get_all_edges():
            edge.isplayed = False
        l = self.get_edges_by_start_node("")
        assert len(l) == 1
        self.replay_edges(doc, l[0])
        doc.history = self.clone()
        self.isreplaying = False
        assert doc._clockhash in self._edgesbyendnode, doc._clockhash + ' not found'
        assert doc._clockhash in doc.history._edgesbyendnode, doc._clockhash + ' not found'

    def clone(self):
        # Return a copy of this HistoryGraph
        ret = HistoryGraph()
        edgeclones = self.get_edges_clones()
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
        edges = self.get_edges_by_start_node(edge.get_end_node())
        for edge2 in edges:
            self.replay_edges(doc, edge2)

    def has_start_edge(self):
        return len(self.get_edges_by_start_node("")) == 1

    def record_past_edges(self):
        # Each edge needs to know which edges are in their past because edges that
        # 'know' about each other can never conflict
        if len(self._edgesbyendnode) == 0:
            return
        # Clear any previous edges
        for edge in self.get_all_edges():
            edge.reset_past_edges()
        # Get the first edge and then start recuring over it
        l = self.get_edges_by_start_node("")
        assert len(l) == 1, 'len(l) == {} should be 1'.format(len(l))
        pastedges = set()
        l[0].record_past_edges(pastedges, self)

    def merge_graphs(self, graph):
        for edge in graph.get_all_edges():
            self.add_edges([edge])
        self.process_graph()

    def process_graph(self):
        # Look over the graph. We are looking for end edges. If there is
        # more than one end node their needs to be a merge
        presentnodes = set()
        for edge in self.get_all_edges():
            l = self.get_edges_by_start_node(edge.get_end_node())
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
        for edge in self.get_all_edges():
            edge.inactive = False
        for k1 in self._edgesbyendnode:
            edge1 = self._edgesbyendnode[k1]
            for k2 in self._edgesbyendnode:
                edge2 = self._edgesbyendnode[k2]

                if k1 != k2:
                    if not edge2.has_past_edge(k1) and not edge1.has_past_edge(k2):
                        edge1.compare_for_conflicts(edge2)

    def has_dangling_edges(self):
        # A sanity check a graph has dangling edges if there is more than one endnode that does not have a start node
        # It means that a Merge needs to be run
        #startnodes = set([k for (k, v) in self.get_edges_by_start_node.iteritems()])
        startnodes = {item for sublist._start_hashes in self.get_all_edges() for item in sublist}
        endnodes = set([edge.get_end_node() for edge in self.get_all_edges()])
        return len(endnodes - startnodes) > 1

    def get_all_edges(self):
        return [v for v in self._edgesbyendnode.values()]

    def depth(self, _clockhash):
        if _clockhash == '':
            return 0
        else:
            return self.get_edges_by_end_node(_clockhash).depth(self)

    def get_edges_clones(self):
        # Return a list of clones of all of the edges
        return [edge.clone() for edge in self.get_all_edges()]

    def is_in_transaction(self):
        return False

class FrozenHistoryGraph(HistoryGraph):
    # This subclass handles the case of a history graph that writes any new edges it receives
    # into the historygraph it was cloned from
    def __init__(self, source_historygraph, source_doc):
        super(FrozenHistoryGraph, self).__init__()
        self.source_historygraph = source_historygraph
        self.source_doc = source_doc
        self.in_init = True
        edgeclones = self.get_edges_clones()
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

class TransactionHistoryGraph(HistoryGraph):
    # This subclass handles the case of a history graph that writes any new edges it receives
    # into the historygraph it was cloned from
    def __init__(self, source_historygraph, source_doc):
        super(TransactionHistoryGraph, self).__init__()
        self.source_historygraph = source_historygraph
        self.source_doc = source_doc
        self.in_init = True
        edgeclones = self.source_historygraph.get_edges_clones()
        super(TransactionHistoryGraph, self).add_edges(edgeclones)
        self.in_init = False
        self._added_edges = list()
        self._transaction_id = str(uuid.uuid4())

    def add_edges(self, edges_list):
        # When we add edges they also need to go into the source historygraph
        if self.in_init:
            return

        assert len(edges_list) == 1
        edge = edges_list[0]
        edge.transaction_id = self._transaction_id
        self._added_edges.append(edge)

    def is_in_transaction(self):
        return True

    def get_last_transaction_edge(self):
        return self._added_edges[-1]

    def end_transaction(self):
        cloned_edges_list = [e.clone() for e in self._edgesbyendnode.values()] + \
            [e.clone() for e in self._added_edges]
        last_edge = cloned_edges_list[-1]
        cloned_edges_list.append(EndTransaction({last_edge.get_end_node()},
            '', '', '',
            '', last_edge.documentid, last_edge.documentclassname,
            '', last_edge.transaction_id))
        #print("end_transaction self._added_edges=", [edge.as_dict() for edge in self._added_edges])
        #print("end_transaction cloned_edges_list=", [edge.as_dict() for edge in cloned_edges_list])
        #print("end_transaction self.source_historygraph._edgesbyendnode.values()=", [edge.as_dict() for edge in self.source_historygraph._edgesbyendnode.values()])
        self.source_historygraph.add_edges(cloned_edges_list)
        #print("end_transaction self.source_historygraph.add_edges completed")
        self.source_historygraph.process_graph()
        self.source_historygraph.record_past_edges()
        self.source_historygraph.process_conflict_winners()
        self.source_historygraph.replay(self.source_doc)
        for l in self.source_doc.edgeslistener:
            l.edges_added(cloned_edges_list)

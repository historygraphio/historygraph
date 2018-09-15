# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A HistoryGraph
from collections import defaultdict
import uuid
from . import edges
import hashlib

def get_transaction_hash(edges):
    return hashlib.sha256(''.join([str(edge.get_transaction_info_hash())
                          for edge in edges])).hexdigest()

def order_edges(edges):
    # Assuming edges is a totally ordered set return a list with the edges in the
    # correct order
    start_hashes = {item for edge in edges for item in edge._start_hashes}
    end_hashes = {edge.get_end_node() for edge in edges}
    start_hash = list(start_hashes - end_hashes)[0]
    start_hashes = {edge._start_hashes[0]: edge for edge in edges}

    def process_order_edges(start_hash, start_hashes):
        if start_hash not in start_hashes:
            return []
        else:
            edge = start_hashes[start_hash]
            return [edge] + process_order_edges(edge.get_end_node(),
                                                start_hashes)

    return process_order_edges(start_hash, start_hashes)

class HistoryGraph(object):
    def __init__(self):
        # We maintain dictionaries by the start and end nodes. The various functions
        # inside this class need to lookup on that basis
        #self.edgesbystartnode = defaultdict(list)
        self._edgesbyendnode = dict()
        self.isreplaying = False
        self.dc = None
        self._transaction_edges = defaultdict(dict)

    def get_edges_by_end_node(self, clockhash):
        return self._edgesbyendnode[clockhash]

    def get_edges_by_start_node(self, clockhash):
        return [edge for edge in self._edgesbyendnode.values() if clockhash in edge._start_hashes]

    def has_edge(self, clockhash):
        # Return true iff we have this edge
        return clockhash in self._edgesbyendnode

    def get_valid_transaction_edges(self):
        def is_continuous(edges):
            if any([len(edge._start_hashes) > 1 for edge in edges]):
                # All edges must have only one start hashes for this to be
                # a totally ordered set
                return False
            # Return True iff the list of edges is a totally ordered set
            start_hashes = {item for edge in edges for item in edge._start_hashes}
            end_hashes = {edge.get_end_node() for edge in edges}
            # For edges to be continous there must be one start hashes without an end hash
            # and vice versa
            if len(start_hashes - end_hashes) != 1:
                return False
            if len(end_hashes - start_hashes) != 1:
                return False
            return True

        matching_edges = []
        for k, d2 in self._transaction_edges.iteritems():
            edges = d2.values()
            if is_continuous(edges):
                edges = order_edges(edges)
                transaction_hash = get_transaction_hash(edges)
                #print('get_valid_transaction_edges transaction_hash=', transaction_hash)
                #print('get_valid_transaction_edges edges.get_transaction_info_hash=', ','.join([edge.get_transaction_info_hash() for edge in edges]))
                #print('get_valid_transaction_edges edges.transaction_hash=', ','.join([edge.transaction_hash for edge in edges]))
                #print('get_valid_transaction_edges edges.start_hashes=', ','.join([edge._start_hashes[0] for edge in edges]))
                #print('get_valid_transaction_edges edges.get_end_node=', ','.join([edge.get_end_node() for edge in edges]))
                if all([edge.transaction_hash == transaction_hash for edge in edges]):
                    # Verify the calculated transaction hash matches the provided transaction hash
                    if self.is_custom_transaction(edges) is False or self.is_valid_custom_transaction(edges):
                        matching_edges = matching_edges + edges
                        self._transaction_edges[k] = dict()
        #ret = [d2.values() for k, d2 in self._transaction_edges.iteritems()]
        #ret = []
        #self._transaction_edges = defaultdict(dict)
        return matching_edges

    def is_valid_custom_transaction(self, edges_list):
        begin_edge = edges_list[0]
        validator = [v for v in self.dc.get_customer_validators() if v.__name__ == begin_edge.nonce][0]
        return validator.is_valid(edges_list, self)

    def is_custom_transaction(self, edges_list):
        return len(edges_list) >= 1 and \
            isinstance(edges_list[0], edges.BeginCustomTransaction)


    #def get_valid_custom_transaction_edges(self):
    #    return []

    def filter_valid_edges(self, edges_list):
        #print('filter_valid_edges edges_list=', edges_list)
        validators = self.dc.get_validators()
        # Seperate out edges in a transaction for others
        transaction_edges = [edge for edge in edges_list if edge.transaction_hash != '']
        edges_list = [edge for edge in edges_list if edge.transaction_hash == '']
        #print('filter_valid_edges 2 edges_list=', edges_list)
        #print('filter_valid_edges 2 transaction_edges=', transaction_edges)
        for edge in transaction_edges:
            self._transaction_edges[edge.transaction_hash][edge.get_end_node()] = edge
        transaction_edges = [edges for edges in self.get_valid_transaction_edges()]
        #custom_transaction_edges = [edges for edges in self.get_valid_custom_transaction_edges()]
        #transaction_edges = [item for sublist in transaction_edges for item in sublist]
        edges_list = edges_list + transaction_edges# + custom_transaction_edges
        return [edge for edge in edges_list if all([v(edge, self) for v in validators])]

    def add_edges(self, edges_list):
        # Add edges to this graph. This only updates the dictionaries
        if self.isreplaying:
            return
        edges_list = self.filter_valid_edges(edges_list)
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
        ret.dc = self.dc
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
    def __init__(self, source_historygraph, source_doc, custom_transaction):
        super(TransactionHistoryGraph, self).__init__()
        self.source_historygraph = source_historygraph
        self.source_doc = source_doc
        self.in_init = True
        self.custom_transaction = custom_transaction
        edgeclones = self.source_historygraph.get_edges_clones()
        self.dc = source_historygraph.dc
        super(TransactionHistoryGraph, self).add_edges(edgeclones)
        self.in_init = False
        self._added_edges = list()
        self._transaction_id = ''
        self.custom_transaction = custom_transaction
        if custom_transaction is not None:
            #print('TransactionHistoryGraph adding custom transaction edge')
            begin_custom_transaction_edge = edges.BeginCustomTransaction({self.source_doc._clockhash},
                '', '', '', '', source_doc.id, source_doc.__class__.__name__,
                custom_transaction.__name__)
            self._added_edges.append(begin_custom_transaction_edge)

    def add_edges(self, edges_list):
        # When we add edges they also need to go into the source historygraph
        if self.in_init:
            return

        assert len(edges_list) == 1
        self._added_edges.append(edges_list[0])
        transaction_hash = get_transaction_hash(self._added_edges)
        #transaction_hash = hashlib.sha256(''.join([str(edge.get_end_node()) for edge in self._added_edges])).hexdigest()
        #print('add_edges transaction_id=', transaction_id)
        #print('add_edges type(transaction_id)=', type(transaction_id))
        for i in range(len(self._added_edges)):
            edge = self._added_edges[i]
            edge.transaction_hash = transaction_hash
            if i > 0:
                edge._start_hashes = [self._added_edges[i - 1].get_end_node()]

    def is_in_transaction(self):
        return True

    def get_last_transaction_edge(self):
        return self._added_edges[-1]

    def end_transaction(self):
        if self.custom_transaction:
            assert self.custom_transaction.is_valid(self._added_edges, self), "Transaction did not validate"
        cloned_edges_list = [e.clone() for e in self._edgesbyendnode.values()] + \
            [e.clone() for e in self._added_edges]
        #print('end_transaction cloned_edges_list=', cloned_edges_list)
        #print('end_transaction len(self.source_historygraph._edgesbyendnode)=', len(self.source_historygraph._edgesbyendnode))
        self.source_historygraph.add_edges(cloned_edges_list)
        #print('end_transaction len(self.source_historygraph._edgesbyendnode)=', len(self.source_historygraph._edgesbyendnode))
        self.source_historygraph.process_graph()
        self.source_historygraph.record_past_edges()
        self.source_historygraph.process_conflict_winners()
        self.source_historygraph.replay(self.source_doc)
        #print('end_transaction self.source_doc.covers=', self.source_doc.covers)
        for l in self.source_doc.edgeslistener:
            l.edges_added(cloned_edges_list)

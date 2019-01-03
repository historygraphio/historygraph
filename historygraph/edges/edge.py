# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#The base class for edges in HistoryGraph
import hashlib

class Edge(object):
    def __init__(self, start_hashes, documentid, documentclassname, nonce, transaction_hash):
        assert len(start_hashes) <= 2
        self._start_hashes = sorted(start_hashes)
        self.inactive = False
        self.documentid = documentid
        self.documentclassname = documentclassname
        self.nonce = nonce
        self.transaction_hash = transaction_hash

    def record_past_edges(self, pastedges, graph):
        # Add all the passed in edges to the current class. This is a set union
        # because for a merge edge this function is called twice
        self.pastedges = self.pastedges | set(pastedges)
        edges = graph.get_edges_by_start_node(self.get_end_node())
        # Add this edge to the set of edges and recursively called our future edges
        pastedges.add(self.get_end_node())
        for edge in edges:
            edge.record_past_edges(set(pastedges), graph)

    def can_replay(self, graph):
        # Return true if this edge can be played. Only a merge edge will ever
        # return false from here
        for node in self._start_hashes:
            if node != "":
                if not graph.has_edge(node):
                    return False
                edge = graph.get_edges_by_end_node(node)
                if edge.isplayed == False:
                    return False
        return True

    def reset_past_edges(self):
        self.pastedges = set()

    def has_past_edge(self, past_edge_id):
        return past_edge_id in self.pastedges

    def compare_for_conflicts(self, edge2):
	    from .deletedocumentobject import DeleteDocumentObject
	    if (self.inactive or edge2.inactive):
		    return; #Inactive edges can never conflict with active edges
	    if self.__class__ != DeleteDocumentObject and edge2.__class__ != DeleteDocumentObject and self.__class__ != edge2.__class__:
		    return #Different edge types can never conflict except for deletion edges
        # Determine the conflict loser and mark it as inactive
	    if edge2.__class__ == DeleteDocumentObject:
	        conflictwinner = -1 * edge2.get_conflict_winner(self)
	    else:
	        conflictwinner = self.get_conflict_winner(edge2)
	    assert conflictwinner == -1 or conflictwinner == 0 or conflictwinner == 1
	    if conflictwinner == 1:
	        self.inactive = True
	    elif conflictwinner == -1:
	        edge2.inactive = True

    def as_dict(self):
        return {"classname":self.__class__.__name__,
            "start_hashes":list(self._start_hashes),
            "endnode":self.get_end_node(),
            "propertyownerid":self.propertyownerid,
            "propertyvalue":self.propertyvalue,
            "propertyname":self.propertyname,
            "propertytype":self.propertytype,
            "documentid":self.documentid,
            "documentclassname":self.documentclassname,
            "nonce":self.nonce,
            "transaction_hash": self.transaction_hash,
         }

    def __str__(self):
        return str(self.as_dict())

    def get_end_node(self):
        if hasattr(self, '_end_node'):
            return self._end_node
        # Get the end node value it is a SHA256 hash of our current contents
        start_hashes= list(self._start_hashes)
        start_hash_1 = start_hashes[0]
        if len(start_hashes) > 1:
            start_hash_2 = start_hashes[1]
        else:
            start_hash_2 = ""
        s = ("classname",str(self.__class__.__name__),
            "start_hash_1",str(start_hash_1),
            "start_hash_2",str(start_hash_2),
            "propertyownerid",str(self.propertyownerid),

            "propertyvalue",str(self.propertyvalue),
            "propertyname",str(self.propertyname),
            "propertytype",str(self.propertytype),
            "documentid",str(self.documentid),
            "documentclassname",str(self.documentclassname),
            "nonce",str(self.nonce),
            "transaction_hash", str(self.transaction_hash)
         )
        self._end_node = hashlib.sha256(str(s)).hexdigest()
        return self._end_node

    def as_tuple(self):
        # Return a tuple that represents the edge when it is turned in JSON
        start_hashes = list(self._start_hashes)
        start_hash_1 = start_hashes[0]
        if len(start_hashes) > 1:
            start_hash_2 = start_hashes[1]
        else:
            start_hash_2 = ""
        return (str(self.documentid),
                str(self.documentclassname),
                str(self.__class__.__name__),
                str(self.get_end_node()),
                str(start_hash_1),
                str(start_hash_2),
                str(self.propertyownerid),
                str(self.propertyname),
                str(self.propertyvalue),
                str(self.propertytype),
                str(self.nonce),
                str(self.transaction_hash))

    def depth(self, historygraph):
        # The depth from this edge is the longest distance back to the start
        start_hashes = list(self._start_hashes)
        if len(start_hashes) == 1:
            if start_hashes[0] == '':
                return 1
            else:
                return historygraph.get_edges_by_end_node(start_hashes[0]).depth(historygraph) + 1
        elif len(self._start_hashes) == 2:
            depth1 = historygraph.get_edges_by_end_node(start_hashes[0]).depth(historygraph) + 1
            depth2 = historygraph.get_edges_by_end_node(start_hashes[1]).depth(historygraph) + 1
            return max(depth1, depth2)
        else:
            assert False

    def get_transaction_info_hash(self):
        # Get the same as end node but with transaction hash remove and
        # assuming one start hash
        start_hashes= list(self._start_hashes)
        start_hash_1 = start_hashes[0]
        #assert len(start_hashes) == 1
        s = ("classname",str(self.__class__.__name__),
            "propertyownerid",str(self.propertyownerid),

            "propertyvalue",str(self.propertyvalue),
            "propertyname",str(self.propertyname),
            "propertytype",str(self.propertytype),
            "documentid",str(self.documentid),
            "documentclassname",str(self.documentclassname),
            "nonce",str(self.nonce),
         )
        return hashlib.sha256(str(s)).hexdigest()

    def clear_end_node_cache(self):
        #Todo remove this edges should be immutable
        if hasattr(self, '_end_node'):
            delattr(self, '_end_node')

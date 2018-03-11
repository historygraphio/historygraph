# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#The base class for edges in HistoryGraph
import hashlib

class Edge(object):
    def __init__(self, start_hashes, documentid, documentclassname):
        self._start_hashes = sorted(start_hashes)
        self.inactive = False
        self.played = False
        self.documentid = documentid
        self.documentclassname = documentclassname

        
    def RecordPastEdges(self, pastedges, graph):
        self.pastedges = self.pastedges | set(pastedges)
        edges = graph.edgesbystartnode[self.GetEndNode()]
        pastedges.add(self.GetEndNode())
        for edge in edges:
            edge.RecordPastEdges(set(pastedges), graph)

    
    def CanReplay(self, graph):
        for node in self._start_hashes:
            if node != "":
                if node not in graph.edgesbyendnode:
                    return False
                edge = graph.edgesbyendnode[node]
                if edge.isplayed == False:
                    return False
        return True

    def ResetPastEdges(self):
        self.pastedges = set()

    def HasPastEdge(self, pastedgeid):
        return pastedgeid in self.pastedges

    def CompareForConflicts(self, edge2):
	    if (self.__class__ != edge2.__class__):
		    return; #Different edge types can never conflict
	    if (self.inactive or edge2.inactive):
		    return; #Inactive edges can never conflict with active edges
	    conflictwinner = self.GetConflictWinner(edge2)
	    assert conflictwinner == -1 or conflictwinner == 0 or conflictwinner == 1
	    if conflictwinner == 1:
	        self.inactive = True
	    elif conflictwinner == -1:
	        edge2.inactive = True
        
    def asDict(self):
        return {"classname":self.__class__.__name__,
            "start_hashes":list(self._start_hashes),
            "endnode":self.GetEndNode(),
            "propertyownerid":self.propertyownerid,
            "propertyvalue":self.propertyvalue,
            "propertyname":self.propertyname,
            "propertytype":self.propertytype,
            "documentid":self.documentid,
            "documentclassname":self.documentclassname,
         }

    def __str__(self):
        return str(self.asDict())

    def GetEndNode(self):
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
         )
        return hashlib.sha256(str(s)).hexdigest()

    def asTuple(self):
        #Return a tuple that represents the edge when it is turned in JSON
        start_hashes = list(self._start_hashes)
        start_hash_1 = start_hashes[0]
        if len(start_hashes) > 1:
            start_hash_2 = start_hashes[1]
        else:
            start_hash_2 = ""
        return (str(self.documentid),
                str(self.documentclassname),
                str(self.__class__.__name__),
                str(self.GetEndNode()),
                str(start_hash_1),
                str(start_hash_2),
                str(self.propertyownerid),
                str(self.propertyname), 
                str(self.propertyvalue),
                str(self.propertytype))
    
    def depth(self, historygraph):
        start_hashes = list(self._start_hashes)
        if len(start_hashes) == 1:
            if start_hashes[0] == '':
                return 1
            else:
                return historygraph.edgesbyendnode[start_hashes[0]].depth(historygraph) + 1
        elif len(self._start_hashes) == 2:
            depth1 = historygraph.edgesbyendnode[start_hashes[0]].depth(historygraph) + 1
            depth2 = historygraph.edgesbyendnode[start_hashes[1]].depth(historygraph) + 1
            return max(depth1, depth2)
        else:
            assert False


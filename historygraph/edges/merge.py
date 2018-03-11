# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A merge edge is used to merge a branched hypergraph back together
from . import Edge

class Merge(Edge):
    def __init__(self, startnodes, propertyownerid, propertyname, propertyvalue, propertytype, documentid, documentclassname):
        super(Merge, self).__init__(startnodes, documentid, documentclassname)
        assert isinstance(propertyownerid, basestring)
        assert isinstance(propertytype, basestring)
        assert isinstance(propertyvalue, basestring)
        self.propertyownerid = propertyownerid
        self.propertyname = propertyname
        self.propertyvalue = propertyvalue
        self.propertytype = propertytype

    def clone(self):
        return Merge(self._start_hashes, self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype, self.documentid, self.documentclassname)

    def replay(self, doc):
        pass
    
    #def get_edge_description(self):
    #    #Return a description of the edgeuseful for debugging purposes
    #    return "Edge type = " + self.__class__.__name__ + " edgeid = " + self.edgeid + " start nodes = " + str(self._start_hashes) + " end node = " + self.endnode

    def get_conflict_winner(self, edge2):
        return 0 #Merge edges can never conflict with anything


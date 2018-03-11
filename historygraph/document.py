# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A HistoryGraph document
from .documentobject import DocumentObject
import uuid
from .historygraph import HistoryGraph
from .changetype import ChangeType
from . import edges

class Document(DocumentObject):
    def clone(self):
        # Return a deep copy of this object. This object all of it's children and
        # it's history are cloned
        ret = self.__class__(self.id)
        ret.copy_document_object(self)
        ret.history = self.history.clone()
        ret.dc = self.dc
        ret._clockhash = self._clockhash
        return ret

    def merge(self, doc2):
        assert self.id == doc2.id
        assert isinstance(doc2, Document)
        # Make a copy of self's history
        history = self.history.clone()
        # Merge doc2's history
        history.merge_graphs(doc2.history)
        history.record_past_edges()
        history.process_conflict_winners()
        # Create the return object and replay the history in to it
        ret = self.__class__(self.id)
        ret.dc = self.dc
        history.replay(ret)
        return ret

    def __init__(self, id=None):
        super(Document, self).__init__(id)
        self.insetattr = True
        self.parent = None
        self.history = HistoryGraph()
        self.documentobjects = dict()
        self._clockhash = ""
        self.dc = None #The document collection this document belongs to
        self.isfrozen = False
        self.edges_received_while_frozen = False
        self.edgeslistener = list()
        self.insetattr = False
        
    def was_changed(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
        nodeset = set()
        nodeset.add(self._clockhash)
        if changetype == ChangeType.SET_PROPERTY_VALUE:
            edge = edges.SimpleProperty(nodeset, propertyownerid, propertyname, propertyvalue, propertytype, self.id, self.__class__.__name__)
        elif changetype == ChangeType.ADD_CHILD:
            edge = edges.AddChild(nodeset, propertyownerid, propertyname, propertyvalue, propertytype, self.id, self.__class__.__name__)
        elif changetype == ChangeType.REMOVE_CHILD:
            edge = edges.RemoveChild(nodeset, propertyownerid, propertyname, propertyvalue, propertytype, self.id, self.__class__.__name__)
        elif changetype == ChangeType.ADD_INT_COUNTER:
            edge = edges.AddIntCounter(nodeset, propertyownerid, propertyname, propertyvalue, propertytype, self.id, self.__class__.__name__)
        elif changetype == ChangeType.ADD_LISTITEM:
            edge = edges.AddListItem(nodeset, propertyownerid, propertyname, propertyvalue, propertytype, self.id, self.__class__.__name__)
        elif changetype == ChangeType.REMOVE_LISTITEM:
            edge = edges.RemoveListItem(nodeset, propertyownerid, propertyname, propertyvalue, propertytype, self.id, self.__class__.__name__)
        else:
            assert False
        self._clockhash = edge.get_end_node()
        self.history.add_edges([edge])
        for l in self.edgeslistener:
            l.edges_added([edge])

    def get_document_object(self, id):
        if id == self.id:
            return self
        return self.documentobjects[id]

    def get_document(self):
        #Return the document
        return self

    def add_edges(self, edges_list):
        if self.isfrozen:
            #If we are frozen just add the edge to the history graph. We will be a full replay on unfreezing
            self.history.add_edges(edges_list)
            self.edges_received_while_frozen = True
            return
        fullreplay = False
        startnodes = set()
        endnodes = set()
        for edge in edges_list:
            if isinstance(edge, edges.Merge):
                #Always perform a full replay on null
                self.full_replay(edges_list)
                return
            startnode = list(edge._start_hashes)[0]
            if startnode == '':
                #If we received a start edge it's OK as long as it is the same as the one we already have
                assert edge.get_end_node() == self.history.edgesbystartnode[''][0].get_end_node()

            #If any of startnodes in the list are in the history but not the current node we need to do a full replay
            
            if startnode != self._clockhash and startnode in self.history.edgesbyendnode:
                self.full_replay(edges_list)
                return

            startnodes.add(startnode)
            endnodes.add(edge.get_end_node())

        startnodes_not_in_endnodes = startnodes - endnodes
        endnodes_not_in_startnodes = endnodes - startnodes

        if len(startnodes_not_in_endnodes) != 1 or len(endnodes_not_in_startnodes) != 1:
            #If this is a continuous chain there is only one start node and endnode
            self.full_replay(edges_list)
            return

        if list(startnodes_not_in_endnodes)[0] != self._clockhash:
            #If the first node in the chain is not the current node 
            self.full_replay(edges_list)
            return

        #Play each edge in the list in sequence
        edgesdict = dict([(list(edge._start_hashes)[0], edge) for edge in edges_list])
        while len(edgesdict) > 0:
            #Get the next edge
            oldnode = self._clockhash
            edge = edgesdict[self._clockhash]
            #Play it
            self.history.add_edges([edge])
            edge.replay(self)
            assert self._clockhash == edge.get_end_node()
            assert self._clockhash != oldnode
            if edge.get_end_node() in self.history.edgesbystartnode:
                l = self.history.edgesbystartnode[edge.get_end_node()]
                if len(l) > 0:
                    #If multiple edge match this one we need to do a full replay
                    self.full_replay(edges_list)
                    return
                #If the end node matches an edge we already have
                edge2internal = l[0]
                edge2external = edgesdict[edge.get_end_node()]
                if edge2internal.get_end_node() != edge2external.get_end_node():
                    #If the edges are different so do a full replay
                    self.full_replay(edges)
                    return
            del edgesdict[oldnode]
            
            
        
        
    def full_replay(self, edges_list):
        history = self.history.clone()
        history.add_edges(edges_list)
        history.process_graph()
        history.record_past_edges()
        history.process_conflict_winners()
        history.replay(self)

    def freeze(self):
        assert self.isfrozen == False
        self.isfrozen = True
        self.edges_received_while_frozen = False

    def unfreeze(self):
        assert self.isfrozen == True
        self.isfrozen = False
        if self.edges_received_while_frozen:
            history = self.history.clone()
            history.process_graph()
            history.record_past_edges()
            history.process_conflict_winners()
            history.replay(self)
            edges = history.get_all_edges()
            for l in self.edgeslistener:
                l.edges_added(edges)

    def add_edges_listener(self, listener):
        self.edgeslistener.append(listener)

    def clean(self):
        for (propname, prop) in self._field.items():
            prop.clean(self, propname)

    def depth(self):
        return self.history.depth(self._clockhash)

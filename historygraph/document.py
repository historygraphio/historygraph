# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A HistoryGraph document
from .documentobject import DocumentObject
import uuid
from .historygraph import HistoryGraph, FrozenHistoryGraph, TransactionHistoryGraph
from .changetype import ChangeType
from . import edges


class Document(DocumentObject):
    def __init__(self, id=None):
        super(Document, self).__init__(id)
        self.insetattr = True
        self.parent = None
        self.history = HistoryGraph()
        self.documentobjects = dict()
        self._clockhash = "" # Clock hash is what time it is for document. The end node hash for the last edge.
        self.dc = None #The document collection this document belongs to
        self.edgeslistener = list()
        self.insetattr = False

    def was_changed(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
        # Called whenever this there is a change to this document or one of it's child
        # DocumentObjects
        if self.history.isreplaying:
            # Don't build new edges if we are replaying
            return
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
        elif changetype == ChangeType.DELETE_DOCUMENT_OBJECT:
            edge = edges.DeleteDocumentObject(nodeset, propertyownerid, propertyname, propertyvalue, propertytype, self.id, self.__class__.__name__)
        else:
            assert False
        self.history.dc = self.dc
        self.history.add_edges([edge])
        if self.history.is_in_transaction():
            # If we are in a transaction the historygraph has changed the edge for
            # us use that edge instead
            edge = self.history.get_last_transaction_edge()
        self._clockhash = edge.get_end_node()
        for l in self.edgeslistener:
            # Signal the listener that there was a change
            l.edges_added([edge])

    def get_document_object(self, id):
        # Lookup document object by id
        if id == self.id:
            return self
        return self.documentobjects[id]

    def has_document_object(self, id):
        return id == self.id or id in self.documentobjects

    def get_document(self):
        #Return the document
        return self

    def add_edges(self, edges_list):
        # Add the passed in edges to the historygraph for this documentt
        #TODO: This appear to be obsolete code left left from the old freeze function
        #if self.isfrozen:
        #    #If we are frozen just add the edge to the history graph. We will be a full replay on unfreezing
        #    self.history.add_edges(edges_list)
        #    self.edges_received_while_frozen = True
        #    return
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
                assert edge.get_end_node() == self.history.get_edges_by_start_node('')[0].get_end_node()

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

        # Play each edge in the list in sequence. If we don't need a full replay we do
        # a partial replay for better performance
        edgesdict = dict([(list(edge._start_hashes)[0], edge) for edge in edges_list])
        while len(edgesdict) > 0:
            #TODO: This functinoality is never tested and doesn't work
            assert False
            #Get the next edge
            oldnode = self._clockhash
            edge = edgesdict[self._clockhash]
            #Play it
            self.history.add_edges([edge])
            edge.replay(self)
            assert self._clockhash == edge.get_end_node() # Sanity check
            assert self._clockhash != oldnode
            if edge.get_end_node() in self.history.edgesbystartnode:
                l = self.history.get_edges_by_start_node(edge.get_end_node())
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
        # full_replay of the historygraph
        history = self.history.clone()
        history.add_edges(edges_list)
        history.process_graph()
        history.record_past_edges()
        history.process_conflict_winners()
        history.replay(self)

    def add_edges_listener(self, listener):
        self.edgeslistener.append(listener)

    def clean(self):
        for (propname, prop) in self._field.items():
            prop.clean(self, propname)

    def depth(self):
        # Calculate the depth of the graph (number of steps back to the start)
        # needed for FieldList
        return self.history.depth(self._clockhash)

    def frozen(self):
        # Return a deep copy of this object. This object all of it's children and
        # it's history is cloned. It's history is a frozen history so it writes back to the parent
        ret = self.__class__(self.id)
        ret.copy_document_object(self)
        ret.history = FrozenHistoryGraph(self.history, self)
        ret.dc = self.dc
        ret._clockhash = self._clockhash
        return ret

    def transaction(self, custom_transaction=None):
        # Return a deep copy of this object. This object all of it's children and
        # it's history is cloned. It's history is a frozen history so it writes back to the parent
        ret = self.__class__(self.id)
        ret.copy_document_object(self)
        ret.history = TransactionHistoryGraph(self.history, self, custom_transaction)
        ret.dc = self.dc
        if custom_transaction  is None:
            ret._clockhash = self._clockhash
        else:
            #print('transaction setting clockhash from auto created edge')
            ret._clockhash = ret.history.get_last_transaction_edge().get_end_node()
        return ret

    def endtransaction(self):
        self.history.end_transaction()

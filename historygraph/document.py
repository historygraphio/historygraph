# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A HistoryGraph document
from .documentobject import DocumentObject
import uuid
from .historygraph import HistoryGraph
from .changetype import ChangeType
from . import edges

class Document(DocumentObject):
    def Clone(self):
        #Return a deep copy of this object. This object all of it's children and
        #it's history are cloned
        ret = self.__class__(self.id)
        ret.CopyDocumentObject(self)
        ret.history = self.history.Clone()
        ret.dc = self.dc
        ret._hashclock = self._hashclock
        return ret

    def Merge(self, doc2):
        assert self.id == doc2.id
        assert isinstance(doc2, Document)
        #Make a copy of self's history
        history = self.history.Clone()
        #Merge doc2's history
        history.MergeGraphs(doc2.history)
        history.RecordPastEdges()
        history.ProcessConflictWinners()
        #Create the return object and replay the history in to it
        ret = self.__class__(self.id)
        ret.dc = self.dc
        history.Replay(ret)
        return ret

    def __init__(self, id=None):
        super(Document, self).__init__(id)
        self.insetattr = True
        self.parent = None
        self.history = HistoryGraph()
        self.documentobjects = dict()
        self._hashclock = ""
        self.dc = None #The document collection this document belongs to
        self.isfrozen = False
        self.edges_received_while_frozen = False
        self.edgeslistener = list()
        self.insetattr = False
        
    def WasChanged(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
        nodeset = set()
        nodeset.add(self._hashclock)
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
        self._hashclock = edge.GetEndNode()
        self.history.AddEdges([edge])
        for l in self.edgeslistener:
            l.EdgesAdded([edge])

    def GetDocumentObject(self, id):
        if id == self.id:
            return self
        return self.documentobjects[id]

    def GetDocument(self):
        #Return the document
        return self

    def AddEdges(self, edges_list):
        if self.isfrozen:
            #If we are frozen just add the edge to the history graph. We will be a full replay on unfreezing
            self.history.AddEdges(edges_list)
            self.edges_received_while_frozen = True
            return
        fullreplay = False
        startnodes = set()
        endnodes = set()
        for edge in edges_list:
            if isinstance(edge, edges.Merge):
                #Always perform a full replay on null
                self.FullReplay(edges_list)
                return
            startnode = list(edge.startnodes)[0]
            if startnode == '':
                #If we received a start edge it's OK as long as it is the same as the one we already have
                assert edge.GetEndNode() == self.history.edgesbystartnode[''][0].GetEndNode()

            #If any of startnodes in the list are in the history but not the current node we need to do a full replay
            
            if startnode != self._hashclock and startnode in self.history.edgesbyendnode:
                self.FullReplay(edges_list)
                return

            startnodes.add(startnode)
            endnodes.add(edge.GetEndNode())

        startnodes_not_in_endnodes = startnodes - endnodes
        endnodes_not_in_startnodes = endnodes - startnodes

        if len(startnodes_not_in_endnodes) != 1 or len(endnodes_not_in_startnodes) != 1:
            #If this is a continuous chain there is only one start node and endnode
            self.FullReplay(edges_list)
            return

        if list(startnodes_not_in_endnodes)[0] != self._hashclock:
            #If the first node in the chain is not the current node 
            self.FullReplay(edges_list)
            return

        #Play each edge in the list in sequence
        edgesdict = dict([(list(edge.startnodes)[0], edge) for edge in edges_list])
        while len(edgesdict) > 0:
            #Get the next edge
            oldnode = self._hashclock
            edge = edgesdict[self._hashclock]
            #Play it
            self.history.AddEdges([edge])
            edge.Replay(self)
            assert self._hashclock == edge.GetEndNode()
            assert self._hashclock != oldnode
            if edge.GetEndNode() in self.history.edgesbystartnode:
                l = self.history.edgesbystartnode[edge.GetEndNode()]
                if len(l) > 0:
                    #If multiple edge match this one we need to do a full replay
                    self.FullReplay(edges_list)
                    return
                #If the end node matches an edge we already have
                edge2internal = l[0]
                edge2external = edgesdict[edge.GetEndNode()]
                if edge2internal.GetEndNode() != edge2external.GetEndNode():
                    #If the edges are different so do a full replay
                    self.FullReplay(edges)
                    return
            del edgesdict[oldnode]
            
            
        
        
    def FullReplay(self, edges_list):
        history = self.history.Clone()
        history.AddEdges(edges_list)
        history.ProcessGraph()
        history.RecordPastEdges()
        history.ProcessConflictWinners()
        history.Replay(self)

    def Freeze(self):
        assert self.isfrozen == False
        self.isfrozen = True
        self.edges_received_while_frozen = False

    def Unfreeze(self):
        assert self.isfrozen == True
        self.isfrozen = False
        if self.edges_received_while_frozen:
            history = self.history.Clone()
            history.ProcessGraph()
            history.RecordPastEdges()
            history.ProcessConflictWinners()
            history.Replay(self)
            edges = history.GetAllEdges()
            for l in self.edgeslistener:
                l.EdgesAdded(edges)

    def AddEdgesListener(self, listener):
        self.edgeslistener.append(listener)

    def Clean(self):
        for (propname, prop) in self._field.items():
            prop.Clean(self, propname)

    def depth(self):
        return self.history.depth(self._hashclock)

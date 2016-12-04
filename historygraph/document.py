#A DOOP document
from documentobject import DocumentObject
import uuid
from historygraph import HistoryGraph
from changetype import ChangeType
from historyedgesimpleproperty import HistoryEdgeSimpleProperty
from historyedgeaddchild import HistoryEdgeAddChild
from historyedgeremovechild import HistoryEdgeRemoveChild
from historyedgenull import HistoryEdgeNull
from historyedgeaddintcounter import HistoryEdgeAddIntCounter
from historyedgeaddlistitem import HistoryEdgeAddListItem
from historyedgeremovelistitem import HistoryEdgeRemoveListItem

class Document(DocumentObject):
    def Clone(self):
        #Return a deep copy of this object. This object all of it's children and
        #it's history are cloned
        ret = self.__class__(self.id)
        ret.CopyDocumentObject(self)
        ret.history = self.history.Clone()
        ret.dc = self.dc
        ret.currentnode = self.currentnode
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

    def __init__(self, id):
        super(Document, self).__init__(id)
        self.insetattr = True
        self.parent = None
        self.history = HistoryGraph()
        self.documentobjects = dict()
        self.currentnode = ""
        self.dc = None #The document collection this document belongs to
        self.isfrozen = False
        self.edges_received_while_frozen = False
        self.edgeslistener = list()
        self.insetattr = False
        
    def WasChanged(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
        nodeset = set()
        nodeset.add(self.currentnode)
        if changetype == ChangeType.SET_PROPERTY_VALUE:
            edge = HistoryEdgeSimpleProperty(nodeset, propertyownerid, propertyname, propertyvalue, propertytype, self.id, self.__class__.__name__)
        elif changetype == ChangeType.ADD_CHILD:
            edge = HistoryEdgeAddChild(nodeset, propertyownerid, propertyname, propertyvalue, propertytype, self.id, self.__class__.__name__)
        elif changetype == ChangeType.REMOVE_CHILD:
            edge = HistoryEdgeRemoveChild(nodeset, propertyownerid, propertyname, propertyvalue, propertytype, self.id, self.__class__.__name__)
        elif changetype == ChangeType.ADD_INT_COUNTER:
            edge = HistoryEdgeAddIntCounter(nodeset, propertyownerid, propertyname, propertyvalue, propertytype, self.id, self.__class__.__name__)
        elif changetype == ChangeType.ADD_LISTITEM:
            edge = HistoryEdgeAddListItem(nodeset, propertyownerid, propertyname, propertyvalue, propertytype, self.id, self.__class__.__name__)
        elif changetype == ChangeType.REMOVE_LISTITEM:
            edge = HistoryEdgeRemoveListItem(nodeset, propertyownerid, propertyname, propertyvalue, propertytype, self.id, self.__class__.__name__)
        else:
            assert False
        #print "Document edge created = ",edge
        self.currentnode = edge.GetEndNode()
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

    def AddEdges(self, edges):
        if self.isfrozen:
            #If we are frozen just add the edge to the history graph. We will be a full replay on unfreezing
            self.history.AddEdges(edges)
            self.edges_received_while_frozen = True
            return
        fullreplay = False
        startnodes = set()
        endnodes = set()
        for edge in edges:
            if isinstance(edge, HistoryEdgeNull):
                #Always perform a full replay on null
                self.FullReplay(edges)
                return
            startnode = list(edge.startnodes)[0]
            if startnode == '':
                #If we received a start edge it's OK as long as it is the same as the one we already have
                assert edge.GetEndNode() == self.history.edgesbystartnode[''][0].GetEndNode()

            #If any of startnodes in the list are in the history but not the current node we need to do a full replay
            
            if startnode != self.currentnode and startnode in self.history.edgesbyendnode:
                self.FullReplay(edges)
                return

            startnodes.add(startnode)
            endnodes.add(edge.GetEndNode())

        startnodes_not_in_endnodes = startnodes - endnodes
        endnodes_not_in_startnodes = endnodes - startnodes

        if len(startnodes_not_in_endnodes) != 1 or len(endnodes_not_in_startnodes) != 1:
            #If this is a continuous chain there is only one start node and endnode
            self.FullReplay(edges)
            return

        if list(startnodes_not_in_endnodes)[0] != self.currentnode:
            #If the first node in the chain is not the current node 
            self.FullReplay(edges)
            return

        #Play each edge in the list in sequence
        edgesdict = dict([(list(edge.startnodes)[0], edge) for edge in edges])
        while len(edgesdict) > 0:
            #Get the next edge
            oldnode = self.currentnode
            edge = edgesdict[self.currentnode]
            #Play it
            self.history.AddEdges([edge])
            edge.Replay(self)
            assert self.currentnode == edge.GetEndNode()
            assert self.currentnode != oldnode
            if edge.GetEndNode() in self.history.edgesbystartnode:
                l = self.history.edgesbystartnode[edge.GetEndNode()]
                if len(l) > 0:
                    #If multiple edge match this one we need to do a full replay
                    self.FullReplay(edges)
                    return
                #If the end node matches an edge we already have
                edge2internal = l[0]
                edge2external = edgesdict[edge.GetEndNode()]
                if edge2internal.GetEndNode() != edge2external.GetEndNode():
                    #If the edges are different so do a full replay
                    self.FullReplay(edges)
                    return
            del edgesdict[oldnode]
            
            
        
        
    def FullReplay(self, edges):
        history = self.history.Clone()
        history.AddEdges(edges)
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
        for (propname, prop) in self.doop_field.items():
            prop.Clean(self, propname)

    def depth(self):
        return self.history.depth(self.currentnode)

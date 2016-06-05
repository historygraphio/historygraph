#A DOOP document
from DocumentObject import DocumentObject
import uuid
from HistoryGraph import HistoryGraph
from ChangeType import ChangeType
from HistoryEdgeSimpleProperty import HistoryEdgeSimpleProperty
from HistoryEdgeAddChild import HistoryEdgeAddChild
from HistoryEdgeRemoveChild import HistoryEdgeRemoveChild
from HistoryEdgeNull import HistoryEdgeNull

class Document(DocumentObject):
    def Clone(self):
        #Return a deep copy of this object. This object all of it's children and
        #it's history are cloned
        ret = self.__class__(self.id)
        ret.CopyDocumentObject(self)
        ret.history = self.history.Clone()
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
        history.Replay(ret)
        return ret

    def __init__(self, id):
        super(Document, self).__init__(id)
        self.insetattr = True
        self.parent = None
        self.history = HistoryGraph()
        self.documentobjects = dict()
        self.currentnode = ""
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
        else:
            assert False
        #print "Document edge created = ",edge
        self.currentnode = edge.GetEndNode()
        self.history.AddEdge(edge)

    def GetDocumentObject(self, id):
        if id == self.id:
            return self
        return self.documentobjects[id]

    def GetDocument(self):
        #Return the document
        return self

    def AddEdge(self, edge):
        #print "Document.AddEdge edge = ",edge
        fullreplay = False
        if isinstance(edge, HistoryEdgeNull):
            #Always perform a full replay on null
            fullreplay = True
        startnode = list(edge.startnodes)[0]
        assert startnode != ''
        #print "Document.Addedge startnode = ",startnode
        #print "Document.Addedge self.currentnode = ",self.currentnode
        if startnode == self.currentnode:
            self.history.AddEdge(edge)
            edge.Replay(self)
            if edge.GetEndNode() in self.history.edgesbystartnode:
                l = self.history.edgesbystartnode[edge.GetEndNode()]
                if len(l) == 2:
                    fullreplay = True
                else:
                    assert len(l) == 1
                    self.AddEdge(l[0])
        elif startnode in self.history.edgesbyendnode:
            fullreplay = True
        else:
            self.history.AddEdge(edge)

        if fullreplay:
            history = self.history.Clone()
            history.Replay(self)

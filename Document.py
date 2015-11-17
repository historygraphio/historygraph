#A DOOP document
from DocumentObject import DocumentObject
import uuid
from HistoryGraph import HistoryGraph
from ChangeType import ChangeType
from HistoryEdgeSimpleProperty import HistoryEdgeSimpleProperty
from HistoryEdgeAddChild import HistoryEdgeAddChild
from HistoryEdgeRemoveChild import HistoryEdgeRemoveChild

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
        nextnode  = str(uuid.uuid4())
        nodeset = set()
        nodeset.add(self.currentnode)
        if changetype == ChangeType.SET_PROPERTY_VALUE:
            edge = HistoryEdgeSimpleProperty(str(uuid.uuid4()), nodeset, nextnode, propertyownerid, propertyname, propertyvalue, propertytype)
        elif changetype == ChangeType.ADD_CHILD:
            edge = HistoryEdgeAddChild(str(uuid.uuid4()), nodeset, nextnode, propertyownerid, propertyname, propertyvalue, propertytype)
        elif changetype == ChangeType.REMOVE_CHILD:
            edge = HistoryEdgeRemoveChild(str(uuid.uuid4()), nodeset, nextnode, propertyownerid, propertyname, propertyvalue, propertytype)
        else:
            assert False
        self.currentnode = nextnode
        self.history.AddEdge(edge)

    def GetDocumentObject(self, id):
        if id == self.id:
            return self
        return self.documentobjects[id]

    def GetDocument(self):
        #Return the document
        return self

    

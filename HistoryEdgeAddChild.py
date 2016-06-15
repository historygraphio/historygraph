#The edge representing adding a child object in DOOP
from HistoryEdge import HistoryEdge

class HistoryEdgeAddChild(HistoryEdge):
    def __init__(self, startnodes, propertyownerid, propertyname, propertyvalue, propertytype, documentid, documentclassname):
        super(HistoryEdgeAddChild, self).__init__(startnodes, documentid, documentclassname)
        assert isinstance(propertyownerid, basestring)
        assert isinstance(propertytype, basestring)
        assert isinstance(propertyvalue, basestring)
        self.propertyownerid = propertyownerid
        self.propertyvalue = propertyvalue
        self.propertyname = propertyname
        self.propertytype = propertytype

    def Replay(self, doc):
        import DocumentCollection
        #print "DocumentCollection.documentcollection.classes = ",DocumentCollection.documentcollection.classes
        newobj = DocumentCollection.documentcollection.classes[self.propertytype](self.propertyvalue)
        doc.documentobjects[newobj.id] = newobj
        if isinstance(self, HistoryEdgeAddChild) and self.propertyownerid == "" and self.propertyname == "":
            pass #There is no parent object and this edge is creating a stand alone object
        else:
            parent = doc.GetDocumentObject(self.propertyownerid)
            getattr(parent, self.propertyname).add(newobj)
        #parent = doc.GetDocumentObject(self.propertyownerid)
        #newobj = self.propertytype(self.propertyvalue)
        #getattr(parent, self.propertyname).add(newobj)
        #doc.documentobjects[newobj.id] = newobj

    def Clone(self):
        return HistoryEdgeAddChild(self.startnodes, 
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype, self.documentid, self.documentclassname)

    def GetConflictWinner(self, edge2):
        return 0 #There can never be a conflict because all edges are new

    
        

#An edge that changes a value in a document

class HistoryEdgeSimpleProperty(HistoryEdge):
    def __init__(self, edgeid, startnodes, endnode, propertyownerid,
                 propertyname, propertyvalue, propertytype):
        super(HistoryEdgeSimpleProperty, self).__init__(edgeid, startnodes, endnode)
        self.propertyownerid = propertyownerid
        self.propertyname = propertyname
        self.propertyvalue = propertyvalue
        self.propertytype = propertytype

    def Replay(self, doc):
        if self.inactive:
            return
        edgeobject = doc.GetDocumentObject(self.propertyownerid)
        field = edgeobject.GetField(self.propertyname)
        field.SetFromString(self.propertyvalue)

    def Clone(self):
        return HistoryEdgeSimpleProperty(self.edgeid, self.startnodes, self.endnode,
                self.propertyownerid, self.propertyname, self.propertyvalue,
                self.propertytype)

    def GetConflictWinner(self, edge2):
        if self.propertyownerid != edge2.propertyownerid:
            return 0
        if self.propertyname != edge2.propertyname:
            return 0
        if self.propertytype == FieldInt.__name__:
            if int(self.m_propertyvalue) > int(edge2.propertyvalue):
                return -1
            else:
                return 1
        else:
            assert False
            return 0


        
        

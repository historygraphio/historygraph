# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#An edge that changes a value in a document
from . import Edge

class SimpleProperty(Edge):
    def __init__(self, startnodes, propertyownerid,
                 propertyname, propertyvalue, propertytype, documentid, documentclassname):
        super(SimpleProperty, self).__init__(startnodes, documentid, documentclassname)
        assert isinstance(propertyownerid, basestring)
        assert isinstance(propertytype, basestring)
        assert propertytype == 'int' or propertytype == 'basestring'
        self.propertyownerid = propertyownerid
        self.propertyname = propertyname
        self.propertyvalue = propertyvalue
        self.propertytype = propertytype

    def replay(self, doc):
        if self.inactive:
            return
        edgeobject = doc.get_document_object(self.propertyownerid)
        field = edgeobject._field[self.propertyname]
        setattr(edgeobject, self.propertyname, field.translate_from_string(self.propertyvalue))

    def clone(self):
        return SimpleProperty(self._start_hashes, 
                self.propertyownerid, self.propertyname, self.propertyvalue,
                self.propertytype, self.documentid, self.documentclassname)

    def get_conflict_winner(self, edge2):
        if self.propertyownerid != edge2.propertyownerid:
            return 0
        if self.propertyname != edge2.propertyname:
            assert False
            return 0
        if self.propertytype == "int":
            if int(self.propertyvalue) > int(edge2.propertyvalue):
                return -1
            else:
                return 1
        elif self.propertytype == "basestring":
            if self.propertyvalue > edge2.propertyvalue:
                return -1
            else:
                return 1
        else:
            assert False
            return 0

    #def get_edge_description(self):
    #    #Return a description of the edgeuseful for debugging purposes
    #    return "Edge type = " + self.__class__.__name__ + " edgeid = " + self.edgeid + " start nodes = " + str(self._start_hashes) + " end node = " + self.endnode + "  self.propertyname = " +  self.propertyname + " self.propertyvalue = " + self.propertyvalue + " self.propertytype = " + str(self.propertytype)
    

        
        

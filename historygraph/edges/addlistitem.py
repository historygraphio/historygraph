# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#The edge representing adding a child object in HistoryGraph
from . import Edge
from json import JSONEncoder, JSONDecoder
from .. import fields

class AddListItem(Edge):
    def __init__(self, startnodes, propertyownerid, propertyname, propertyvalue, propertytype, documentid, documentclassname, nonce=''):
        super(AddListItem, self).__init__(startnodes, documentid, documentclassname, nonce)
        assert isinstance(propertyownerid, basestring)
        assert isinstance(propertytype, basestring)
        assert isinstance(propertyvalue, basestring)
        self.propertyownerid = propertyownerid
        self.propertyvalue = propertyvalue
        self.propertyname = propertyname
        self.propertytype = propertytype

    def replay(self, doc):
        (objid, added_node_id, added_node_parent, added_node_timestamp, added_node_data) = JSONDecoder().decode(self.propertyvalue)
        if objid not in doc.documentobjects:
            newobj = doc.dc.classes[self.propertytype](objid)
            newobj.dc = doc.dc
            doc.documentobjects[newobj.id] = newobj
        else:
            newobj = doc.documentobjects[objid]
        added_node = fields.List._ListNode(added_node_parent, added_node_timestamp, added_node_data, newobj)
        added_node.id = added_node_id
        if self.propertyownerid == "" and self.propertyname == "":
            assert False # We can never create stand alone object this way
        else:
            parent = doc.get_document_object(self.propertyownerid)
            newobj.parent = parent
            flImpl = getattr(parent, self.propertyname)
            # TODO: Rewrite the section below so that instead of a list of classes we use a set of named tuples
            # and there fore do not need manually determine are we add a duplicate
            for n in flImpl._listnodes:
                # Test if this listnode is a deuplicate of a existing one and don't add it if it is
                if n.parent == added_node.parent and n.timestamp == added_node.timestamp and \
                   n.data == added_node.data and n.obj == added_node.obj:
                    return
                
            if hasattr(flImpl, "_rendered_list"):
                delattr(flImpl, "_rendered_list")
            flImpl._listnodes.append(added_node)

    def clone(self):
        return AddListItem(self._start_hashes, 
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype, self.documentid, self.documentclassname, self.nonce)

    def get_conflict_winner(self, edge2):
        return 0 #There can never be a conflict because all edges are new

    
        

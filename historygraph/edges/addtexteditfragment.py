# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#The edge representing adding a child object in HistoryGraph
from . import Edge
from json import JSONEncoder, JSONDecoder
from .. import fields
import six

class AddTextEditFragment(Edge):
    def __init__(self, startnodes, propertyownerid, propertyname, propertyvalue,
                 propertytype, documentid, documentclassname, nonce='', transaction_hash=''):
        super(AddTextEditFragment, self).__init__(startnodes, documentid, documentclassname, nonce, transaction_hash)
        assert isinstance(propertyownerid, six.string_types)
        assert isinstance(propertytype, six.string_types)
        assert isinstance(propertyvalue, six.string_types)
        self.propertyownerid = propertyownerid
        self.propertyvalue = propertyvalue
        self.propertyname = propertyname
        self.propertytype = propertytype

    def replay(self, doc):
        # List items are actually listnodes (or tombstone) they are then replayed via their own algorithm
        (added_node_id, added_node_parent, added_node_timestamp, added_node_data) = \
            JSONDecoder().decode(self.propertyvalue)
        # Create the document object if it doesn't already exist
        added_node = fields.TestEdit._Fragment(added_node_parent, added_node_timestamp, added_node_data)
        added_node.id = added_node_id
        if self.propertyownerid == "" and self.propertyname == "":
            assert False # We can never create stand alone object this way
        else:
            parent = doc.get_document_object(self.propertyownerid)
            flImpl = getattr(parent, self.propertyname)
            # TODO: Rewrite the section below so that instead of a list of classes we use a set of named tuples
            # and there fore do not need manually determine are we are adding a duplicate
            for n in flImpl._listnodes:
                # Test if this listnode is a duplicate of a existing one and don't add it if it is
                if n.parent == added_node.parent and n.timestamp == added_node.timestamp and \
                   n.data == added_node.data and n.obj == added_node.obj:
                    return

            if hasattr(flImpl, "_rendered_list"):
                delattr(flImpl, "_rendered_list")
            flImpl._listnodes.append(added_node)

    def clone(self):
        return AddTextEditFragment(self._start_hashes,
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype,
            self.documentid, self.documentclassname, self.nonce, self.transaction_hash)

    def get_conflict_winner(self, edge2, doc_obj_heirachy):
        return 0 #There can never be a conflict because all edges are new

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
        # Extract the fragment values from the JSON payload
        (id, text, sessionid,
                internal_start_pos, relative_to, relative_start_pos,
                has_been_split) = \
                    JSONDecoder().decode(self.propertyvalue)
        # Create the document object if it doesn't already exist
        added_fragment = fields.TextEdit._Fragment(id, text, sessionid,
                internal_start_pos, relative_to, relative_start_pos,
                has_been_split)
        if self.propertyownerid == "" and self.propertyname == "":
            assert False # We can never create stand alone object this way
        else:
            parent = doc.get_document_object(self.propertyownerid)
            flImpl = getattr(parent, self.propertyname)

            assert len(flImpl._listfragments) == 0
            flImpl._listfragments.append(added_fragment)

    def clone(self):
        return AddTextEditFragment(self._start_hashes,
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype,
            self.documentid, self.documentclassname, self.nonce, self.transaction_hash)

    def get_conflict_winner(self, edge2, doc_obj_heirachy):
        return 0 #There can never be a conflict because all edges are new

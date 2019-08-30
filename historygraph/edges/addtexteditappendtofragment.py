# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#The edge representing adding a child object in HistoryGraph
from . import Edge
from json import JSONEncoder, JSONDecoder
from .. import fields
import six

class AddTextEditAppendToFragment(Edge):
    def __init__(self, startnodes, propertyownerid, propertyname, propertyvalue,
                 propertytype, documentid, documentclassname, sessionid,
                 transaction_hash=''):
        super(AddTextEditAppendToFragment, self).__init__(startnodes, documentid,
            documentclassname, sessionid, transaction_hash)
        assert isinstance(propertyownerid, six.string_types)
        assert isinstance(propertytype, six.string_types)
        assert isinstance(propertyvalue, six.string_types)
        self.propertyownerid = propertyownerid
        self.propertyvalue = propertyvalue
        self.propertyname = propertyname
        self.propertytype = propertytype

    def replay(self, doc):
        # Extract the fragment values from the JSON payload
        (fragment_id, text, fragment_text_len) = \
            JSONDecoder().decode(self.propertyvalue)
        if self.propertyownerid == "" and self.propertyname == "":
            assert False # We can never create stand alone object this way
        else:
            parent = doc.get_document_object(self.propertyownerid)
            flImpl = getattr(parent, self.propertyname)
            # Get the last fragment and append to it
            fragments = [f for f in flImpl._listfragments if f.id == fragment_id]
            last_fragment = fragments[-1]
            assert last_fragment.internal_start_pos + len(last_fragment.text) <= fragment_text_len
            last_fragment.text += text

            """
            was_found = False
            for f in flImpl._listfragments:
                if f.id == fragment_id and f.internal_start_pos + len(f.text) == fragment_text_len:
                    f.text += text
                    was_found = True
            assert was_found, "No matching fragment found"
            """

    def clone(self):
        return AddTextEditAppendToFragment(self._start_hashes,
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype,
            self.documentid, self.documentclassname, self.nonce, self.transaction_hash)

    def get_conflict_winner(self, edge2, doc_obj_heirachy):
        return 0 #There can never be a conflict because all edges are new

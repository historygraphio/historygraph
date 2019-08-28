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

            if added_fragment.relative_to == "":
                # This is the first fragment it does immediately after the start
                # of the list
                assert len(flImpl._listfragments) == 0
                flImpl._listfragments.append(added_fragment)
            else:
                fragment_index = 0
                was_found = False
                for fragment in flImpl._listfragments:
                    if fragment.id == added_fragment.relative_to:
                        if relative_start_pos >= fragment.internal_start_pos and \
                           relative_start_pos <= fragment.internal_start_pos + len(fragment.text):
                            was_found = True
                    if was_found == False:
                        fragment_index += 1
                assert was_found, "A matching fragment was not found"
                fragment = flImpl._listfragments[fragment_index]
                if relative_start_pos < fragment.internal_start_pos + len(fragment.text):
                    #We need to break this fragment apart
                    # TODO: COde shared with textedit.py move to a library
                    fragment_break_pos = relative_start_pos - fragment.internal_start_pos
                    if fragment_break_pos > 0:
                        new_split_frag = fields.TextEdit._Fragment(fragment.id,
                            fragment.text[fragment_break_pos:],
                            sessionid, fragment.internal_start_pos + fragment_break_pos,
                            fragment.relative_to, fragment.relative_start_pos, False)
                        fragment.has_been_split = True
                        fragment.text = fragment.text[:fragment_break_pos]
                        flImpl._listfragments.insert(fragment_index + 1, new_split_frag)
                        flImpl._listfragments.insert(fragment_index + 1, added_fragment)
                    else:
                        flImpl._listfragments.insert(fragment_index, added_fragment)
                elif relative_start_pos == fragment.internal_start_pos + len(fragment.text):
                    assert False, "New fragment goes exactly at the end of an existing one not yet handled"
                #assert False

    def clone(self):
        return AddTextEditFragment(self._start_hashes,
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype,
            self.documentid, self.documentclassname, self.nonce, self.transaction_hash)

    def get_conflict_winner(self, edge2, doc_obj_heirachy):
        return 0 #There can never be a conflict because all edges are new

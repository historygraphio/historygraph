# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#The edge representing adding a child object in HistoryGraph
from . import Edge
from json import JSONEncoder, JSONDecoder
from .. import fields
import six
from collections import Iterable

class AddTextEditRemove(Edge):
    def __init__(self, startnodes, propertyownerid, propertyname, propertyvalue,
                 propertytype, documentid, documentclassname, sessionid, transaction_hash=''):
        super(AddTextEditRemove, self).__init__(startnodes, documentid, documentclassname,
            sessionid, transaction_hash)
        assert isinstance(propertyownerid, six.string_types)
        assert isinstance(propertytype, six.string_types)
        assert isinstance(propertyvalue, six.string_types)
        self.propertyownerid = propertyownerid
        self.propertyvalue = propertyvalue
        self.propertyname = propertyname
        self.propertytype = propertytype

    def replay(self, doc):
        print("AddTextEditRemove.replay called")
        # Extract the fragment values from the JSON payload
        (target_fragment_id, remove_start, remove_end, sessionid) = \
                    JSONDecoder().decode(self.propertyvalue)
        parent = doc.get_document_object(self.propertyownerid)
        flImpl = getattr(parent, self.propertyname)

        def _process_fragment(fragment):
            # Return a processed fragment
            if fragment.id != target_fragment_id:
                # Does not match our target so just ignore
                return fragment
            if fragment.internal_start_pos >= remove_end:
                # Is before this fragment so ignore
                return fragment
            if fragment.internal_start_pos + len(fragment.text) < remove_start:
                # Is after this fragment so ignore
                return fragment
            if fragment.internal_start_pos >= remove_start and \
               fragment.internal_start_pos + len(fragment.text) <= remove_end:
                # This entire fragment should be deleted just return the same fragment with the text removed and has_been_split set
                return fields.TextEdit._Fragment(fragment.id,
                    "",
                    sessionid, fragment.internal_start_pos,
                    fragment.relative_to, fragment.relative_start_pos,
                    "", 0,
                    True)
            if fragment.internal_start_pos >= remove_start and \
               fragment.internal_start_pos + len(fragment.text) > remove_end:
                # The start of this fragment should be removed
                fragment_break_pos = remove_end - fragment.internal_start_pos
                return fields.TextEdit._Fragment(fragment.id,
                    fragment.text[fragment_break_pos:],
                    sessionid, fragment.internal_start_pos + fragment_break_pos,
                    fragment.relative_to, fragment.relative_start_pos,
                    "", 0, fragment.has_been_split)
            if fragment.internal_start_pos < remove_start and \
               fragment.internal_start_pos + len(fragment.text) <= remove_end:
                # The end of this fragment should be removed
                fragment_break_pos = remove_start - fragment.internal_start_pos
                return fields.TextEdit._Fragment(fragment.id,
                    fragment.text[:fragment_break_pos],
                    sessionid, fragment.internal_start_pos,
                    fragment.relative_to, fragment.relative_start_pos,
                    "", 0,
                    True)
            if fragment.internal_start_pos < remove_start and \
               fragment.internal_start_pos + len(fragment.text) > remove_end:
                # The middle of the list has been removed
                start_fragment_break_pos = remove_start - fragment.internal_start_pos
                end_fragment_break_pos = remove_end - fragment.internal_start_pos
                return [fields.TextEdit._Fragment(fragment.id,
                        fragment.text[:start_fragment_break_pos],
                        sessionid, fragment.internal_start_pos,
                        fragment.relative_to, fragment.relative_start_pos,
                        "", 0, True),
                    fields.TextEdit._Fragment(fragment.id,
                        fragment.text[end_fragment_break_pos:],
                        sessionid, fragment.internal_start_pos + end_fragment_break_pos,
                        fragment.relative_to, fragment.relative_start_pos,
                        "", 0, fragment.has_been_split)]
            assert False, "There should be no other possible combination"

        # Process all of the fragments
        list_fragments = map(_process_fragment, flImpl._listfragments)
        # Filter out the tombstoned fragments
        list_fragments = filter(lambda f: f is not None, list_fragments)
        # Make into a list of lists
        list_fragments = map(lambda e: e if isinstance(e, Iterable) else [e],
                             list_fragments)
        list_fragments = [item for sublist in list_fragments for item in sublist] #From: https://stackoverflow.com/a/952952

        flImpl._listfragments = list_fragments

        flImpl.content = ''.join([f.text for f in flImpl._listfragments])
        for f in flImpl._listfragments:
            f.length = len(f.text)
        absolute_start_pos = 0
        for f in flImpl._listfragments:
            f.absolute_start_pos = absolute_start_pos
            absolute_start_pos += len(f.text)

        return


    def clone(self):
        return AddTextEditRemove(self._start_hashes,
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype,
            self.documentid, self.documentclassname, self.nonce, self.transaction_hash)

    def get_conflict_winner(self, edge2, doc_obj_heirachy):
        return 0 #There can never be a conflict because all edges are new

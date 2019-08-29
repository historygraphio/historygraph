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
                # This entire fragment should be deleted so return None (is filtered out in the next function)
                return None
            if fragment.internal_start_pos >= remove_start and \
               fragment.internal_start_pos + len(fragment.text) > remove_end:
                # The start of this fragment should be removed
                fragment_break_pos = remove_end - fragment.internal_start_pos
                return fields.TextEdit._Fragment(fragment.id,
                    fragment.text[fragment_break_pos:],
                    sessionid, fragment.internal_start_pos + fragment_break_pos,
                    fragment.relative_to, fragment.relative_start_pos,
                    fragment.has_been_split)
            if fragment.internal_start_pos < remove_start and \
               fragment.internal_start_pos + len(fragment.text) <= remove_end:
                # The end of this fragment should be removed
                fragment_break_pos = remove_start - fragment.internal_start_pos
                return fields.TextEdit._Fragment(fragment.id,
                    fragment.text[:fragment_break_pos],
                    sessionid, fragment.internal_start_pos,
                    fragment.relative_to, fragment.relative_start_pos,
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
                        True),
                    fields.TextEdit._Fragment(fragment.id,
                        fragment.text[end_fragment_break_pos:],
                        sessionid, fragment.internal_start_pos + end_fragment_break_pos,
                        fragment.relative_to, fragment.relative_start_pos,
                        fragment.has_been_split)]
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

        return

        """
        index = 0
        while index < len(flImpl._listfragments):
            fragment = flImpl._listfragments[index]
            if fragment.id == target_fragment_id:
                if remove_start <= fragment.internal_start_pos and \
                    remove_end >= fragment.internal_start_pos + len(fragment.text):
                     # Delete the entire fragment
                     assert False, "TODO: Build a test that does this"
                elif remove_start <= fragment.internal_start_pos and \
                    remove_end > fragment.internal_start_pos:
                     # Delete at the start of the fragment
                     assert False, "TODO: Build a test that does this"
                elif remove_start > fragment.internal_start_pos and \
                    remove_end >= fragment.internal_start_pos + len(fragment.text):
                     # Delete at the end of the fragment
                     assert False, "TODO: Build a test that does this"
                elif remove_start > fragment.internal_start_pos and \
                    remove_end >= fragment.internal_start_pos + len(fragment.text):
                     # Delete at the end of the fragment
                     assert False, "TODO: Build a test that does this"
        """

        """
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
                """

    def clone(self):
        return AddTextEditRemove(self._start_hashes,
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype,
            self.documentid, self.documentclassname, self.nonce, self.transaction_hash)

    def get_conflict_winner(self, edge2, doc_obj_heirachy):
        return 0 #There can never be a conflict because all edges are new

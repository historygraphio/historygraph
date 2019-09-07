# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#The edge representing adding a child object in HistoryGraph
from . import Edge
from json import JSONEncoder, JSONDecoder
from .. import fields
import six

class AddTextEditFragment(Edge):
    def __init__(self, startnodes, propertyownerid, propertyname, propertyvalue,
                 propertytype, documentid, documentclassname, sessionid, transaction_hash=''):
        super(AddTextEditFragment, self).__init__(startnodes, documentid, documentclassname,
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
        print("AddTextEditFragment.replay called")
        (fragment_id, text, sessionid,
                internal_start_pos, relative_to, relative_start_pos,
                before_frag_id, before_frag_start_pos, has_been_split) = \
                    JSONDecoder().decode(self.propertyvalue)
        # Create the document object if it doesn't already exist
        added_fragment = fields.TextEdit._Fragment(fragment_id, text, sessionid,
                internal_start_pos, relative_to, relative_start_pos,
                before_frag_id, before_frag_start_pos, has_been_split)
        if self.propertyownerid == "" and self.propertyname == "":
            assert False # We can never create stand alone object this way
        else:
            parent = doc.get_document_object(self.propertyownerid)
            flImpl = getattr(parent, self.propertyname)

            if added_fragment.relative_to == "" and len(flImpl._listfragments) == 0:
                print("AddTextEditFragment.replay This is the first fragment it does immediately after the start of the list")
                # This is the first fragment it does immediately after the start
                # of the list
                flImpl._listfragments.append(added_fragment)
                flImpl.content = added_fragment.text
                added_fragment.absolute_start_pos = 0
                added_fragment.length = len(added_fragment.text)
            else:
                fragment_index = 0
                was_found = False
                if added_fragment.relative_to != "":
                    # Look for a fragment we can insert inside of
                    fragments_with_index = zip(range(len(flImpl._listfragments)),
                                               flImpl._listfragments)
                    # Look for all fragments belong to the one we are relative to
                    fragments_with_index = filter(lambda f: f[1].id ==
                                                  added_fragment.relative_to,
                                                  fragments_with_index)
                    # Look for all fragments we are inside
                    fragments_with_index = list(filter(lambda f: added_fragment.relative_start_pos >= f[1].internal_start_pos and \
                                                  added_fragment.relative_start_pos <= f[1].internal_start_pos + len(f[1].text),
                                                  fragments_with_index))
                    if len(fragments_with_index) > 0:
                        # There is one insert relative to it
                        fragment_index = fragments_with_index[0][0]
                    else:
                        # Otherwise find a fragment we are insered after
                        fragments_with_index = zip(range(len(flImpl._listfragments)),
                                                   flImpl._listfragments)
                        # Look for all fragments belong to the one we are relative to
                        fragments_with_index = filter(lambda f: f[1].id ==
                                                      added_fragment.relative_to,
                                                      fragments_with_index)
                        # Look for all fragments we are after
                        fragments_with_index = list(filter(lambda f: added_fragment.relative_start_pos > f[1].internal_start_pos + len(f[1].text),
                                                      fragments_with_index))
                        fragment_index = fragments_with_index[-1][0]

                fragment = flImpl._listfragments[fragment_index]
                if relative_start_pos < fragment.internal_start_pos + len(fragment.text):
                    #We need to break this fragment apart
                    # TODO: Code shared with textedit.py move to a library
                    fragment_break_pos = relative_start_pos - fragment.internal_start_pos
                    if fragment_break_pos > 0:
                        new_split_frag = fields.TextEdit._Fragment(fragment.id,
                            fragment.text[fragment_break_pos:],
                            sessionid, fragment.internal_start_pos + fragment_break_pos,
                            fragment.relative_to, fragment.relative_start_pos,
                            "", 0, False)
                        fragment.has_been_split = True
                        fragment.text = fragment.text[:fragment_break_pos]
                        flImpl._listfragments.insert(fragment_index + 1, new_split_frag)
                        flImpl._listfragments.insert(fragment_index + 1, added_fragment)
                    else:
                        fragment_index2 = fragment_index
                        do_insert = False
                        while not do_insert and fragment_index2 < len(flImpl._listfragments):
                            fragment2 = flImpl._listfragments[fragment_index2]
                            if fragment2.relative_to == added_fragment.relative_to and \
                               fragment2.relative_start_pos == added_fragment.relative_start_pos:
                                # Test should we insert before this fragment or not
                                if added_fragment.id > fragment2.id and \
                                    (added_fragment.before_frag_id != fragment2.id or \
                                     added_fragment.before_frag_start_pos < fragment2.internal_start_pos):
                                    # Always insert before a fragment if the original user coudl see
                                    # the fragment
                                    # Use the order of the fragment ID's as a tie break
                                    # The id's should be in ascending order
                                    fragment_index2 += 1
                                else:
                                    do_insert = True
                            else:
                                do_insert = True
                        flImpl._listfragments.insert(fragment_index2, added_fragment)
                elif relative_start_pos >= fragment.internal_start_pos + len(fragment.text):
                    fragment_index2 = fragment_index + 1
                    do_insert = False
                    while not do_insert and fragment_index2 < len(flImpl._listfragments):
                        fragment2 = flImpl._listfragments[fragment_index2]
                        if fragment2.relative_to == added_fragment.relative_to and \
                           fragment2.relative_start_pos == added_fragment.relative_start_pos:
                            # Test should we insert before this fragment or not
                            if added_fragment.id > fragment2.id and \
                                (added_fragment.before_frag_id != fragment2.id or \
                                 added_fragment.before_frag_start_pos < fragment2.internal_start_pos):
                                # Always insert before a fragment if the original user coudl see
                                # the fragment
                                # Use the order of the fragment ID's as a tie break
                                # The id's should be in ascending order
                                fragment_index2 += 1
                            else:
                                do_insert = True
                        else:
                            do_insert = True
                    flImpl._listfragments.insert(fragment_index2, added_fragment)
                else:
                    assert False, "Should never be reached"

    def clone(self):
        return AddTextEditFragment(self._start_hashes,
            self.propertyownerid, self.propertyname, self.propertyvalue, self.propertytype,
            self.documentid, self.documentclassname, self.nonce, self.transaction_hash)

    def get_conflict_winner(self, edge2, doc_obj_heirachy):
        return 0 #There can never be a conflict because all edges are new

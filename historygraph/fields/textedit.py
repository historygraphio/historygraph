# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

from . import Field
from ..changetype import ChangeType
import uuid
from json import JSONEncoder, JSONDecoder
import six

class TextEdit(Field):
    class _Fragment(object):
        # Fields
        # id = a uuid cast to a string uniquely identifying this fragment. It is set upon it's creation
        # text = the text of this fragment
        # internal_start_pos = the internal position in the string of this fragment
        # relative_to = the uuid of the fragment this is relative to.
        # relative_start_pos the string position this fragment starts relative to another
        # has_been_split True iff this string is been split by another operation.
        # Is_tombstone this fragment is a tombstone and
        def __init__(self, id, text, sessionid, internal_start_pos, relative_to,
                     relative_start_pos, has_been_split):
            self.id = id
            self.text = text
            self.sessionid = sessionid
            self.internal_start_pos = internal_start_pos
            self.relative_to = relative_to
            self.relative_start_pos = relative_start_pos
            self.has_been_split = has_been_split


    class _TextEditImpl(object):
        # This implementation class is what actually get attacted to the document object to implement the required
        # behaviour
        def __init__(self, parent, name):
            self.parent = parent
            assert self.parent is not None
            self.name = name
            self._listfragments = list()

        def _get_add_fragment_json(self, id, text, sessionid,
                internal_start_pos, relative_to, relative_start_pos,
                has_been_split):
            # Return the JSON representing an add fragment event
            return JSONEncoder().encode((id, text, sessionid, internal_start_pos,
                relative_to, relative_start_pos, has_been_split))


        def removerange(self, start, end):
            sessionid = self.get_document().dc.sessionid
            fragment_start_index = self.get_fragment_at_index(start)
            fragment_end_index = self.get_fragment_to_append_to_by_index(end)
            if fragment_start_index == fragment_end_index:
                # If this deletion is inside a single fragment
                fragment = self._listfragments[fragment_start_index]
                fragment_start_pos = self.get_fragment_start_position(fragment_start_index)

                self.was_changed(ChangeType.ADD_TEXTEDIT_REMOVE, self.parent.id,
                     self.name, JSONEncoder().encode((fragment.id,
                         start - fragment_start_pos + fragment.internal_start_pos,
                          end - fragment_start_pos + fragment.internal_start_pos, sessionid)),
                     "string")

                if start == fragment_start_pos and end == fragment_start_pos + len(fragment.text):
                    # We are deleting an entrie fragment just remove it
                    self._listfragments.remove(fragment)
                elif start == fragment_start_pos:
                    # We are deleting at the start there is no new fragment just chop characters off
                    fragment.text = fragment.text[end - fragment_start_pos:]
                    fragment.internal_start_pos = fragment.internal_start_pos + end - fragment_start_pos
                elif end == fragment_start_pos + len(fragment.text):
                    # We are deleting to the end of an existing fragment so just chop characters off
                    fragment.text = fragment.text[:start - fragment_start_pos]
                    fragment.has_been_split = True
                else:
                    # We are deleting somewhere in the middle
                    new_split_frag = TextEdit._Fragment(fragment.id,
                        fragment.text[end - fragment_start_pos:], sessionid,
                        end - fragment_start_pos,
                        fragment.relative_to, fragment.relative_start_pos, False)
                    fragment.has_been_split = True
                    fragment.text = fragment.text[:start - fragment_start_pos]
                    self._listfragments.insert(fragment_start_pos + 1, new_split_frag)

            else:
                # Delete the first fragment we match
                fragment = self._listfragments[fragment_start_index]
                fragment_start_pos = self.get_fragment_start_position(fragment_start_index)
                fragment_end = fragment_start_pos + len(fragment.text)
                self.removerange(start, fragment_end)
                # Delete the rest
                self.removerange(start, end - (fragment_end - start))

        def was_changed(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
            # TODO: Possible balloonian function
            assert isinstance(propertyownerid, six.string_types)
            self.parent.was_changed(changetype, propertyownerid, propertyname, propertyvalue, propertytype)

        def __len__(self):
            self.render()
            return len(self._rendered_list)

        def __getitem__(self,index):
            self.render()
            return self._rendered_list[index].obj

        def clone(self, owner, name):
            # Two lists are the same if they have the same set of ListNodes and Tombstones
            ret = List.FieldListImpl(self.theclass, owner, name)
            ret._listfragments = [f.clone() for f in self._listfragments]
            return ret

        def clean(self):
            self._listfragments = list()

        def get_document(self):
            #Return the document
            return self.parent.get_document()

        def insert(self, index, text):
            sessionid = self.get_document().dc.sessionid
            # Get insert text at position index
            if len(self._listfragments) == 0:
                if index == 0:
                    # This always goes at the start
                    assert len(self._listfragments) == 0 # The below only works for empty lists
                    fragment_id = str(uuid.uuid4())
                    self._listfragments.append(TextEdit._Fragment(fragment_id,
                        text, sessionid, 0, "", 0, False))
                    self.was_changed(ChangeType.ADD_TEXTEDIT_FRAGMENT, self.parent.id,
                                     self.name, self._get_add_fragment_json(fragment_id,
                                         text, sessionid, 0, "", 0, False),
                                     "string")

                    return
                else:
                    assert False, "We can only insert at position zero if there are no fragments"
            fragment_index = self.get_fragment_to_append_to_by_index(index)
            fragment_start_pos = self.get_fragment_start_position(fragment_index)
            fragment = self._listfragments[fragment_index]
            if index == fragment_start_pos + len(fragment.text) and \
               fragment.sessionid == sessionid:
                # We are inserting at the end of a fragment so we can append
                self.was_changed(ChangeType.ADD_TEXTEDIT_APPEND_TO_FRAGMENT, self.parent.id,
                                 self.name, JSONEncoder().encode((fragment.id,
                                     text, fragment.internal_start_pos + len(fragment.text))),
                                 "string")
                fragment.text += text
                return
            elif index == fragment_start_pos + len(fragment.text) and \
               fragment.sessionid != sessionid:
                # We are inserting at the end of another sessions's fragment so create a new fragment and insert it
                new_inserted_frag = TextEdit._Fragment(str(uuid.uuid4()), text, sessionid, 0,
                    fragment.id, 0, False)
                self._listfragments.insert(fragment_index + 1, new_inserted_frag)
                return
            else:
                internal_start_pos = index - fragment_start_pos
                if internal_start_pos == 0:
                    inserted_fragment_id = str(uuid.uuid4())
                    new_inserted_frag = TextEdit._Fragment(inserted_fragment_id, text, sessionid, 0,
                        fragment.id, 0, False)
                    self._listfragments.insert(fragment_start_pos, new_inserted_frag)
                    self.was_changed(ChangeType.ADD_TEXTEDIT_FRAGMENT, self.parent.id,
                                     self.name, self._get_add_fragment_json(inserted_fragment_id,
                                         text, sessionid, 0,
                                         fragment.id, fragment.internal_start_pos + internal_start_pos, False),
                                     "string")
                    return
                else:
                    # TODO: COde shared with addtexteditfragment.py move to a library
                    new_split_frag = TextEdit._Fragment(fragment.id, fragment.text[internal_start_pos:],
                        sessionid, fragment.internal_start_pos + internal_start_pos,
                        fragment.relative_to, fragment.relative_start_pos, False)
                    fragment.has_been_split = True
                    fragment.text = fragment.text[:internal_start_pos]
                    inserted_fragment_id = str(uuid.uuid4())
                    new_inserted_frag = TextEdit._Fragment(inserted_fragment_id, text,
                        sessionid, 0, fragment.id, fragment.internal_start_pos + internal_start_pos, False)
                    self._listfragments.insert(fragment_index + 1, new_split_frag)
                    self._listfragments.insert(fragment_index + 1, new_inserted_frag)
                    self.was_changed(ChangeType.ADD_TEXTEDIT_FRAGMENT, self.parent.id,
                                     self.name, self._get_add_fragment_json(inserted_fragment_id,
                                         text, sessionid, 0,
                                         fragment.id, fragment.internal_start_pos + internal_start_pos, False),
                                     "string")
                    return


            assert False


        def get_text(self):
            # Return the full version of the string
            return ''.join(f.text for f in self._listfragments)

        def get_fragment_to_append_to_by_index(self, index):
            # Return the index into the fragment list of the current index position
            pos = 0
            for i in range(len(self._listfragments)):
                f = self._listfragments[i]
                if index >= pos and index <= pos + len(f.text):
                    return i
                else:
                    pos += len(f.text)
            assert False, "Read past end of string"

        def get_fragment_start_position(self, fragment_index):
            # Return the number of characters before the given fragment_index
            return sum([len(f.text) for f in self._listfragments[:fragment_index]])

        def get_fragment_at_index(self, index):
            # Return the index into the fragment list of the current index position
            pos = 0
            for i in range(len(self._listfragments)):
                f = self._listfragments[i]
                if index >= pos and index < pos + len(f.text):
                    return i
                else:
                    pos += len(f.text)
            assert False, "Read past end of string"


    def __init__(self):
        pass

    def create_instance(self, owner, name):
        return TextEdit._TextEditImpl(owner, name)

    def clone(self, name, src, owner):
        return getattr(src, name).clone(owner, name)

    def clean(self, owner, name):
        return getattr(owner, name).clean()

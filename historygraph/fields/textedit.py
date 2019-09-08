# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

from . import Field
from ..changetype import ChangeType
import uuid
from json import JSONEncoder, JSONDecoder
import six
from collections import namedtuple

Marker = namedtuple('Marker', 'line column')

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
                     relative_start_pos, before_frag_id, before_frag_start_pos,
                     has_been_split):
            self.id = id
            self.text = text
            self.sessionid = sessionid
            self.internal_start_pos = internal_start_pos
            self.relative_to = relative_to
            self.relative_start_pos = relative_start_pos
            self.has_been_split = has_been_split
            self.before_frag_id = before_frag_id
            self.before_frag_start_pos = before_frag_start_pos


    class _TextEditImpl(object):
        # This implementation class is what actually get attacted to the document object to implement the required
        # behaviour
        def __init__(self, parent, name):
            self.parent = parent
            assert self.parent is not None
            self.name = name
            self._listfragments = list()
            self.content = ""

        def _get_add_fragment_json(self, id, text, sessionid,
                internal_start_pos, relative_to, relative_start_pos,
                before_frag_id, before_frag_start_pos, has_been_split):
            # Return the JSON representing an add fragment event
            return JSONEncoder().encode((id, text, sessionid, internal_start_pos,
                relative_to, relative_start_pos, before_frag_id,
                before_frag_start_pos, has_been_split))


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
                    fragment.text = ""
                    fragment.has_been_split = True
                    fragment.length = 0
                    self.content = self.content[:start] + \
                        self.content[end:]
                    for i in range(fragment_start_index + 1, len(self._listfragments)):
                        self._listfragments[i].absolute_start_pos -= end - start
                elif start == fragment_start_pos:
                    # We are deleting at the start there is no new fragment just chop characters off
                    fragment.text = fragment.text[end - fragment_start_pos:]
                    fragment.internal_start_pos = fragment.internal_start_pos + end - fragment_start_pos
                    fragment.length = len(fragment.text)
                    self.content = self.content[:fragment_start_pos] + \
                        self.content[end:]
                    for i in range(fragment_start_pos + 1, len(self._listfragments)):
                        self._listfragments[i].absolute_start_pos -= end - fragment_start_pos
                elif end == fragment_start_pos + len(fragment.text):
                    # We are deleting to the end of an existing fragment so just chop characters off
                    old_length = len(fragment.text)
                    fragment.text = fragment.text[:start - fragment_start_pos]
                    fragment.has_been_split = True
                    fragment.length = len(fragment.text)
                    self.content = self.content[:start] + \
                        self.content[fragment_start_pos + old_length:]
                    for i in range(fragment_start_pos + 1, len(self._listfragments)):
                        self._listfragments[i].absolute_start_pos -= fragment_start_pos + old_length - start
                else:
                    # We are deleting somewhere in the middle
                    new_split_frag = TextEdit._Fragment(fragment.id,
                        fragment.text[end - fragment_start_pos:], sessionid,
                        end - fragment_start_pos,
                        fragment.relative_to, fragment.relative_start_pos,
                        "", 0, False)
                    new_split_frag.absolute_start_pos = \
                        fragment.absolute_start_pos + start - fragment_start_pos
                    new_split_frag.length = len(new_split_frag.text)
                    fragment.has_been_split = True
                    fragment.text = fragment.text[:start - fragment_start_pos]
                    fragment.length = len(fragment.text)
                    self._listfragments.insert(fragment_start_pos + 1, new_split_frag)
                    self.content = self.content[:start] + \
                        self.content[end:]
                    for i in range(fragment_start_pos + 2, len(self._listfragments)):
                        self._listfragments[i].absolute_start_pos -= end - start

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
                    fragment = TextEdit._Fragment(fragment_id,
                        text, sessionid, 0, "", 0, "", 0, False)
                    fragment.absolute_start_pos = 0
                    fragment.length = len(text)
                    self._listfragments.append(fragment)
                    self.content = text
                    self.was_changed(ChangeType.ADD_TEXTEDIT_FRAGMENT, self.parent.id,
                                     self.name, self._get_add_fragment_json(fragment_id,
                                         text, sessionid, 0, "", 0, "", 0, False),
                                     "string")

                    return
                else:
                    assert False, "We can only insert at position zero if there are no fragments"
            fragment_index = self.get_fragment_to_append_to_by_index(index)
            fragment_start_pos = self.get_fragment_start_position(fragment_index)
            fragment = self._listfragments[fragment_index]
            if index == fragment_start_pos + len(fragment.text) and \
               fragment.sessionid == sessionid:
                if fragment.has_been_split == False:
                    # We are inserting at the end of a fragment then  so we can append
                    self.was_changed(ChangeType.ADD_TEXTEDIT_APPEND_TO_FRAGMENT, self.parent.id,
                                     self.name, JSONEncoder().encode((fragment.id,
                                         text, fragment.internal_start_pos + len(fragment.text))),
                                     "string")
                    self.content = self.content[:fragment.absolute_start_pos + fragment.length] + \
                        text + self.content[fragment.absolute_start_pos + fragment.length:]
                    for i in range(fragment_index + 1, len(self._listfragments)):
                        self._listfragments[i].absolute_start_pos += len(text)
                    fragment.text += text
                    fragment.length += len(text)
                    return
                else:
                    # If the fragment was split aways make a new one don't try to append
                    inserted_fragment_id = str(uuid.uuid4())
                    before_frag_id = ""
                    before_frag_start_pos = 0
                    if fragment_index + 1 < len(self._listfragments):
                        # Set this fragment to be before the next fragment we know of
                        after_frag = self._listfragments[fragment_index + 1]
                        before_frag_id = after_frag.id
                        before_frag_start_pos = after_frag.internal_start_pos
                    new_inserted_frag = TextEdit._Fragment(inserted_fragment_id, text, sessionid, 0,
                        fragment.id, len(fragment.text), before_frag_id, before_frag_start_pos, False)
                    before_fragment = self._listfragments[fragment_index]
                    new_inserted_frag.absolute_start_pos = before_fragment.absolute_start_pos + before_fragment.length
                    new_inserted_frag.length = len(new_inserted_frag.text)
                    self.content = self.content[:before_fragment.absolute_start_pos + before_fragment.length] + \
                        text + self.content[before_fragment.absolute_start_pos + before_fragment.length:]
                    for i in range(fragment_index + 1, len(self._listfragments)):
                        self._listfragments[i].absolute_start_pos += len(text)
                    self._listfragments.insert(fragment_index + 1, new_inserted_frag)
                    self.was_changed(ChangeType.ADD_TEXTEDIT_FRAGMENT, self.parent.id,
                                     self.name, self._get_add_fragment_json(inserted_fragment_id,
                                         text, sessionid, 0,
                                         fragment.id, len(fragment.text),
                                         before_frag_id, before_frag_start_pos, False),
                                     "string")
                    return

            elif index == fragment_start_pos + len(fragment.text) and \
               fragment.sessionid != sessionid:
                # We are inserting at the end of another sessions's fragment so create a new fragment and insert it
                inserted_fragment_id = str(uuid.uuid4())
                new_inserted_frag = TextEdit._Fragment(inserted_fragment_id, text, sessionid, 0,
                    fragment.id, len(fragment.text), "", 0, False)
                new_inserted_frag.absolute_start_pos = fragment.absolute_start_pos + fragment.length
                new_inserted_frag.length = len(new_inserted_frag.text)
                self.content = self.content[:fragment.absolute_start_pos + fragment.length] + \
                    text + self.content[fragment.absolute_start_pos + fragment.length:]
                for i in range(fragment_index + 1, len(self._listfragments)):
                    self._listfragments[i].absolute_start_pos += len(text)
                self._listfragments.insert(fragment_index + 1, new_inserted_frag)
                self.was_changed(ChangeType.ADD_TEXTEDIT_FRAGMENT, self.parent.id,
                                 self.name, self._get_add_fragment_json(inserted_fragment_id,
                                     text, sessionid, 0,
                                     fragment.id, len(fragment.text), "", 0,
                                     False),
                                 "string")
                return
            else:
                internal_start_pos = index - fragment_start_pos
                if internal_start_pos == 0:
                    # This fragment is being inserted before the very first fragment in the list
                    inserted_fragment_id = str(uuid.uuid4())
                    before_frag_id = ""
                    before_frag_start_pos = 0
                    if fragment_start_pos < len(self._listfragments):
                        # Set this fragment to be before the next fragment we know of
                        after_frag = self._listfragments[fragment_start_pos]
                        before_frag_id = after_frag.id
                        before_frag_start_pos = after_frag.internal_start_pos
                    self.content = text + self.content
                    for i in range(0, len(self._listfragments)):
                        self._listfragments[i].absolute_start_pos += len(text)
                    new_inserted_frag = TextEdit._Fragment(inserted_fragment_id, text, sessionid, 0,
                        "", 0, before_frag_id, before_frag_start_pos, False)
                    new_inserted_frag.absolute_start_pos = 0
                    new_inserted_frag.length = len(text)
                    self._listfragments.insert(fragment_start_pos, new_inserted_frag)
                    self.was_changed(ChangeType.ADD_TEXTEDIT_FRAGMENT, self.parent.id,
                                     self.name, self._get_add_fragment_json(inserted_fragment_id,
                                         text, sessionid, 0,
                                         "", 0,
                                         before_frag_id, before_frag_start_pos, False),
                                     "string")
                    return
                else:
                    # TODO: COde shared with addtexteditfragment.py move to a library
                    self.content = self.content[:fragment.absolute_start_pos + internal_start_pos] + \
                        text + self.content[fragment.absolute_start_pos + internal_start_pos:]
                    for i in range(fragment_index + 1, len(self._listfragments)):
                        self._listfragments[i].absolute_start_pos += len(text)
                    new_split_frag = TextEdit._Fragment(fragment.id, fragment.text[internal_start_pos:],
                        sessionid, fragment.internal_start_pos + internal_start_pos,
                        fragment.relative_to, fragment.relative_start_pos, "", 0, False)
                    new_split_frag.absolute_start_pos = fragment.absolute_start_pos + internal_start_pos +len(text)
                    new_split_frag.length = len(new_split_frag.text)
                    fragment.has_been_split = True
                    fragment.text = fragment.text[:internal_start_pos]
                    fragment.length = len(fragment.text)
                    inserted_fragment_id = str(uuid.uuid4())
                    new_inserted_frag = TextEdit._Fragment(inserted_fragment_id, text,
                        sessionid, 0, fragment.id,
                        fragment.internal_start_pos + internal_start_pos,
                        new_split_frag.id, new_split_frag.internal_start_pos, False)
                    new_inserted_frag.absolute_start_pos = fragment.absolute_start_pos +internal_start_pos
                    new_inserted_frag.length = len(new_inserted_frag.text)
                    self._listfragments.insert(fragment_index + 1, new_split_frag)
                    self._listfragments.insert(fragment_index + 1, new_inserted_frag)
                    self.was_changed(ChangeType.ADD_TEXTEDIT_FRAGMENT, self.parent.id,
                                     self.name, self._get_add_fragment_json(inserted_fragment_id,
                                         text, sessionid, 0,
                                         fragment.id, fragment.internal_start_pos + internal_start_pos,
                                         new_split_frag.id, new_split_frag.internal_start_pos, False),
                                     "string")
                    return


            assert False


        def get_text(self):
            # Return the full version of the string
            #return ''.join(f.text for f in self._listfragments)
            return self.content

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

        def get_lines(self):
            # Return an array of lines of text from this document
            # Each line consists of the start point (fragment + offset)
            # The start of the line is the character after the previous \n
            # except the frst line always starts at position 0. The end of the
            # line is the next \n. Except the last line which is the last
            # character in the textedit
            class LineInfo(object):
                def __init__(self, start_fragment, start_offset, rendered_list):
                    self.start_fragment = start_fragment
                    self.start_offset = start_offset
                    self.rendered_list = rendered_list

                def get_content(self):
                    def _get_content(fragment, start_offset):
                        if fragment >= len(self.rendered_list):
                            return ""
                        text = self.rendered_list[fragment].text
                        text = text[start_offset:]
                        pos = text.find('\n')
                        if pos == -1:
                            return text + _get_content(fragment + 1, 0)
                        else:
                            return text[:pos]

                    return _get_content(self.start_fragment, self.start_offset)

            lastlineinfo = None
            rawlines = list()
            for index in range(0, len(self._listfragments)):
                if lastlineinfo == None:
                    lastlineinfo = LineInfo(index,0,self._listfragments)
                fragment = self._listfragments[index]
                thispos = 0
                while True:
                    lastsearch = fragment.text[thispos:].find('\n')
                    if lastsearch == -1:
                        break
                    else:
                        lastsearch += thispos
                        thispos = lastsearch + 1
                        rawlines.append(lastlineinfo)
                        if thispos < len(fragment.text):
                            lastlineinfo = LineInfo(index, thispos,
                                                    self._listfragments)
                        else:
                            lastlineinfo = LineInfo(index + 1, 0,
                                                    self._listfragments)
            rawlines.append(lastlineinfo)
            return rawlines

        def get_marker(self, fragment_id, offset):
            # Retreive the index of the fragment that match fragment_id and offset
            # That is the last fragment that matches the fragment ID and has an
            # internal start position before the offset
            fragment_indexes = [i for i in range(len(self._listfragments)) if
                         self._listfragments[i].id == fragment_id and
                         offset >= self._listfragments[i].internal_start_pos]
            # The last one in the list is the one we are looking for
            fragment_index = fragment_indexes[-1]
            # Get the line
            lines = self.get_lines()
            # Get all lines that start on or after the given index
            indexes = [i for i in range(len(lines)) if (lines[i].start_fragment <=
                     fragment_index and lines[i].start_offset <= offset)
                     or lines[i].start_fragment < fragment_index]
            # The first one is the one we want
            first_index = indexes[-1]
            lineinfo = lines[first_index]
            info_start_fragment = self._listfragments[lineinfo.start_fragment]
            if info_start_fragment.id == fragment_id and \
               info_start_fragment.internal_start_pos <= offset:
                # This fragment is the one we want
                return Marker(first_index, offset - lineinfo.start_offset)
            else:
                #print("get_marker lineinfo.start_fragment=", lineinfo.start_fragment)
                #print("get_marker fragment_index=", fragment_index)
                #print("get_marker first_index=", first_index)
                extra_chars = sum([len(self._listfragments[i].text) for i in range(lineinfo.start_fragment, fragment_index)])
                return Marker(first_index, offset - lineinfo.start_offset + extra_chars)
                #assert False


    def __init__(self):
        pass

    def create_instance(self, owner, name):
        return TextEdit._TextEditImpl(owner, name)

    def clone(self, name, src, owner):
        return getattr(src, name).clone(owner, name)

    def clean(self, owner, name):
        return getattr(owner, name).clean()

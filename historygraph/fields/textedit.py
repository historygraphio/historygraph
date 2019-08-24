# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

# An ordered list of sub objects in HistoryGraph
# From work by Marek Zawirski https://twitter.com/zzzawir/status/757635463536578560
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
        # relative_to = the uuid of the fragment this is relative to.
        # relative_start_pos the string position this fragment starts relative to another
        # has_been_split True iff this string is been split by another operation.
        # Is_tombstone this fragment is a tombstone and
        def __init__(self, id, text, relative_to, relative_start_pos, has_been_split):
            self.id = id
            self.text = text
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


        def removerange(self, start, end):
            assert False

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
            # Get insert text at position index
            if index == 0:
                # This always goes at the start
                assert len(self._listfragments) == 0 # The below only works for empty lists
                self._listfragments.append(TextEdit._Fragment(str(uuid.uuid4()), text,
                    "", 0, False))


        def get_text(self):
            # Return the full version of the string
            return ''.join(f.text for f in self._listfragments)


    def __init__(self):
        pass

    def create_instance(self, owner, name):
        return TextEdit._TextEditImpl(owner, name)

    def clone(self, name, src, owner):
        return getattr(src, name).clone(owner, name)

    def clean(self, owner, name):
        return getattr(owner, name).clean()

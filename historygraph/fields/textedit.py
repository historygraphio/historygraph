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
        def __init__(self, parent, timestamp, data, starts_at, original_id):
            self.id = str(uuid.uuid4())
            assert isinstance(parent, six.string_types)
            self.parent = parent
            self.timestamp = timestamp
            assert isinstance(parent, six.string_types)
            self.data = data
            self.starts_at = starts_at
            self.original_id = original_id

        def get_original_id(self):
            return self.original_id if self.original_id != "" else self.id

    class _TextEditImpl(object):
        # This implementation class is what actually get attacted to the document object to implement the required
        # behaviour
        def __init__(self, parent, name):
            self.parent = parent
            assert self.parent is not None
            self.name = name
            self._listnodes = list()
            self._tombstones = set()

        def _insert(self, index, fragmenttext, original_id=""):
            # Insert a fragment in the conflict free list
            assert isinstance(fragmenttext, six.string_types)
            index = index - 1
            if index == -1:
                # Add as the first fragment in the list
                added_node = TextEdit._Fragment('', self.parent.get_document().depth(),
                                                fragmenttext, 0, original_id)
                self._listnodes.append(added_node)
            else:
                # Add at an artbitrary location in the list
                self.render()
                # The previous fragment in the list
                prev_fragment = self._rendered_list[index]
                added_node = TextEdit._Fragment(self._rendered_list[index].id,
                    self.parent.get_document().depth(), fragmenttext,
                    prev_fragment.starts_at + len(prev_fragment.data),
                    original_id)
                self._listnodes.append(added_node)
            if hasattr(self, "_rendered_list"):
                delattr(self, "_rendered_list")

            self.render()
            for i in range(index + 2, len(self._rendered_list)):
                prev_fragment = self._rendered_list[i - 1]
                self._rendered_list[i].starts_at = prev_fragment.starts_at + \
                    len(prev_fragment.data)

            self.was_changed(ChangeType.ADD_TEXTEDIT_FRAGMENT, self.parent.id,
                             self.name, JSONEncoder().encode((added_node.id,
                                added_node.parent, added_node.timestamp, added_node.data,
                                added_node.original_id)),
                             "string")

        def _append(self, fragmenttext):
            # Insert at the end of the list
            self.insert(len(self), fragmenttext)

        def _remove(self, index):
            # Remove a fragment
            self.render()
            node = self._rendered_list[index] # Get the node we are deleting
            self.remove_by_node(node)

        def remove_by_nodeid(self, objid):
            # We have an id remove the object. Usually from replaying an edge
            for node in self._listnodes:
                if node.id == objid:
                    self.remove_by_node(node)
                    return
            assert False

        def remove_by_node(self, node, create_edge=True):
            # Find the given node and remove it
            self._tombstones.add(node.id)
            if hasattr(self, "_rendered_list"):
                delattr(self, "_rendered_list")

            if create_edge:
                self.was_changed(ChangeType.REMOVE_TEXTEDITFRAGMENT,
                    self.parent.id,
                    self.name, node.id, "string")

        def removerange(self, start, end):
            assert start >= 0
            frag_start, frag_start_index = self.get_fragment_by_index(start)
            if frag_start.starts_at != start:
                # If the start position is in the middle of a fragment. Split that
                # fragment
                self._split_fragment(frag_start_index, start - frag_start.starts_at)
                self.render()
            frag_end, frag_end_index = self.get_fragment_by_index(end)
            if frag_end.starts_at != end:
                # If the start position is in the middle of a fragment. Split that
                # fragment
                self._split_fragment(frag_end_index, end - frag_end.starts_at)
                self.render()

            self.render()
            self._rendered_list[0].starts_at = 0
            for i in range(max(frag_start_index, 1), len(self._rendered_list)):
                prev_fragment = self._rendered_list[i - 1]
                self._rendered_list[i].starts_at = prev_fragment.starts_at + \
                    len(prev_fragment.data)

            # Now we should only be deleting whole fragments
            frag_start, frag_start_index = self.get_fragment_by_index(start)
            frag_end, frag_end_index = self.get_fragment_by_index(end)
            if end >= frag_end.starts_at + len(frag_end.data) and frag_end_index == len(self._rendered_list) - 1:
                # If past the end of the last fragment bump up by one
                frag_end_index += 1
            node_ids = [self._rendered_list[i].id for i in
                        range(frag_start_index, frag_end_index)]
            for nodeid in node_ids:
                self.remove_by_nodeid(nodeid)
            self.render()
            self._rendered_list[0].starts_at = 0
            for i in range(max(frag_start_index, 1), len(self._rendered_list)):
                prev_fragment = self._rendered_list[i - 1]
                self._rendered_list[i].starts_at = prev_fragment.starts_at + \
                    len(prev_fragment.data)


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
            ret._listnodes = list(self._listnodes)
            ret._tombstones = set(self._tombstones)
            return ret

        def clean(self):
            self._listnodes = list()
            self._tombstones = set()
            if hasattr(self, "_rendered_list"):
                delattr(self, "_rendered_list")

        def render(self):
            # _rendered_list is the cached contents of the list. Can be useful for performance and iterators
            if hasattr(self, "_rendered_list"):
                return
            # render the list - replay all of the additions
            l = self._render('')
            self._rendered_list = tuple([node for node in l if node.id not in self._tombstones])

        def _render(self, nodeid):
            matching = self.get_matching_list_nodes(nodeid)
            ret = list()
            for node in matching:
                ret.append(node)
                ret.extend(self._render(node.id))
            return ret

        def get_matching_list_nodes(self, nodeid):
            # Get a list of nodes with matching ids
            l = [n for n in self._listnodes if n.parent == nodeid]
            # Sort the nodes in timestamp then id order
            return sorted(l, key=lambda n: (-n.timestamp, n.get_original_id()))

        def get_document(self):
            #Return the document
            return self.parent.get_document()

        def insert(self, index, fragmenttext):
            # Get the fragment index points at
            target_fragment, fragment_index = self.get_fragment_by_index(index)
            if target_fragment is None:
                # If the fragment list is empty proceed with the insertion
                pass
            elif index == target_fragment.starts_at + len(target_fragment.data):
                # Usually if target_fragment is the last fragment the insert
                # point should be one past it
                fragment_index += 1
            elif index == target_fragment.starts_at:
                # If it points to the start of a fragment insert before the
                # fragment
                pass
            else:
                self._split_fragment(fragment_index, index - target_fragment.starts_at)
                self.render()
                self.insert(index, fragmenttext)
                return
            self._insert(fragment_index, fragmenttext)

        def get_text(self):
            self.render()
            return ''.join([node.data for node in self._rendered_list])

        def get_fragment_by_index(self, index):
            # If the index is equal or after the last fragments start it points
            # at the last fragment
            self.render()
            if len(self._rendered_list) == 0:
                # If the list is empty return None as position 0
                return None, 0
            last_fragment = self._rendered_list[-1]
            if index >= last_fragment.starts_at:
                return last_fragment, len(self._rendered_list) - 1
            return self._get_fragment_by_index(index, 0, len(self._rendered_list)-1)

        def _get_fragment_by_index(self, index, start_frag_index, end_frag_index):
            # Perform a binary search to find the matching fragment
            start_frag = self._rendered_list[start_frag_index]
            if index >= start_frag.starts_at and index < start_frag.starts_at + len(start_frag.data):
                return start_frag, start_frag_index
            end_frag = self._rendered_list[end_frag_index]
            if index >= end_frag.starts_at and index < end_frag.starts_at + len(end_frag.data):
                return end_frag, end_frag_index
            mid_frag_index = (start_frag_index + end_frag_index) // 2
            mid_frag = self._rendered_list[mid_frag_index]

            if index >= mid_frag.starts_at:
                return self._get_fragment_by_index(index, mid_frag_index, end_frag_index)
            else:
                return self._get_fragment_by_index(index, start_frag_index, mid_frag_index)

        def _split_fragment(self, frag_index, split_position):
            # Split a fragment ie remove and old one and replace it with a new one
            # frag_index is the fragment to replace, split_position is the position
            # in the string to split at
            self.render()
            old_fragment = self._rendered_list[frag_index] # The fragment being replaced
            self._remove(frag_index)
            self.render()
            self._insert(frag_index, old_fragment.data[:split_position],
                         original_id=old_fragment.id)
            if split_position < len(old_fragment.data):
                self.render()
                self._insert(frag_index + 1, old_fragment.data[split_position:])

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
                        data = self.rendered_list[fragment].data
                        data = data[start_offset:]
                        pos = data.find('\n')
                        if pos == -1:
                            return data + _get_content(fragment + 1, 0)
                        else:
                            return data[:pos]

                    return _get_content(self.start_fragment, self.start_offset)

            lastlineinfo = None
            rawlines = list()
            for index in range(0, len(self._rendered_list)):
                if lastlineinfo == None:
                    lastlineinfo = LineInfo(index,0,self._rendered_list)
                fragment = self._rendered_list[index]
                thispos = 0
                while True:
                    lastsearch = fragment.data[thispos:].find('\n')
                    if lastsearch == -1:
                        break
                    else:
                        lastsearch += thispos
                        thispos = lastsearch + 1
                        rawlines.append(lastlineinfo)
                        if thispos < len(fragment.data):
                            lastlineinfo = LineInfo(index,thispos,self._rendered_list)
                        else:
                            lastlineinfo = LineInfo(index + 1,0,self._rendered_list)
            rawlines.append(lastlineinfo)
            return rawlines

    def __init__(self):
        pass

    def create_instance(self, owner, name):
        return TextEdit._TextEditImpl(owner, name)

    def clone(self, name, src, owner):
        return getattr(src, name).clone(owner, name)

    def clean(self, owner, name):
        return getattr(owner, name).clean()

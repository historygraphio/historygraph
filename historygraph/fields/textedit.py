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
        def __init__(self, parent, timestamp, data):
            self.id = str(uuid.uuid4())
            assert isinstance(parent, six.string_types)
            self.parent = parent
            self.timestamp = timestamp
            assert isinstance(parent, six.string_types)
            self.data = data

    class _TextEditImpl(object):
        # This implementation class is what actually get attacted to the document object to implement the required
        # behaviour
        def __init__(self, parent, name):
            self.parent = parent
            assert self.parent is not None
            self.name = name
            self._listnodes = list()
            self._tombstones = set()

        def _insert(self, index, fragmenttext):
            # Insert a fragment in the conflict free list
            assert isinstance(fragmenttext, six.string_types)
            index = index - 1
            if index == -1:
                # Add as the first fragment in the list
                added_node = TextEdit._Fragment('', self.parent.get_document().depth(),
                                                fragmenttext)
                self._listnodes.append(added_node)
            else:
                # Add at an artbitrary location in the list
                self.render()
                added_node = TextEdit._Fragment(self._rendered_list[index].id,
                    self.parent.get_document().depth(), fragmenttext)
                self._listnodes.append(added_node)
            if hasattr(self, "_rendered_list"):
                delattr(self, "_rendered_list")

            self.was_changed(ChangeType.ADD_TEXTEDIT_FRAGMENT, self.parent.id,
                             self.name, JSONEncoder().encode((added_node.id,
                                added_node.parent, added_node.timestamp, added_node.data)),
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
            obj = node.obj
            self._tombstones.add(node.id)
            if hasattr(self, "_rendered_list"):
                delattr(self, "_rendered_list")

            if create_edge:
                self.was_changed(ChangeType.REMOVE_TEXTEDITFRAGMENT,
                    self.parent.id,
                    self.name, node.id, obj.__class__.__name__)

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
            return sorted(l, key=lambda n: (-n.timestamp, n.id))

        def get_document(self):
            #Return the document
            return self.parent.get_document()

        def insert(self, index, fragmenttext):
            self._insert(index, fragmenttext)

        def get_text(self):
            self.render()
            return ''.join([node.data for node in self._rendered_list])


    def __init__(self):
        pass

    def create_instance(self, owner, name):
        return TextEdit._TextEditImpl(owner, name)

    def clone(self, name, src, owner):
        return getattr(src, name).clone(owner, name)

    def clean(self, owner, name):
        return getattr(owner, name).clean()

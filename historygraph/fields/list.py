# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

# An ordered list of sub objects in HistoryGraph
# From work by Marek Zawirski https://twitter.com/zzzawir/status/757635463536578560
# Available in this repo as documents/research_papers/Zawirski_lists.pdf
# Full title "Specification and Complexity of Collaborative Text Editing"
from . import Field
from ..changetype import ChangeType
import uuid
from json import JSONEncoder, JSONDecoder
import six

class List(Field):
    class _ListNode(object):
        def __init__(self, parent, timestamp, data, obj):
            self.id = str(uuid.uuid4())
            assert isinstance(parent, six.string_types)
            self.parent = parent
            self.timestamp = timestamp
            self.data = data
            self.obj = obj

    class FieldListImpl(object):
        # This implementation class is what actually get attacted to the document object to implement the required
        # behaviour
        def __init__(self, theclass, parent, name):
            self.theclass = theclass
            self.parent = parent
            assert self.parent is not None
            self.name = name
            self._listnodes = list()
            self._tombstones = set()

        def insert(self, index, obj):
            # Insert an object in the conflict free list
            assert isinstance(obj, self.theclass)
            obj.parent = self
            self.parent.get_document().documentobjects[obj.id] = obj
            index = index - 1
            if index == -1:
                # Add as the first item in the list
                added_node = List._ListNode('', self.parent.get_document().depth(), obj.id, obj)
                self._listnodes.append(added_node)
            else:
                # Add at an artbitrary location in the list
                self.render()
                added_node = List._ListNode(self._rendered_list[index].id, self.parent.get_document().depth(), obj.id, obj)
                self._listnodes.append(added_node)
            if hasattr(self, "_rendered_list"):
                delattr(self, "_rendered_list")

            self.was_changed(ChangeType.ADD_LISTITEM, self.parent.id, self.name, JSONEncoder().encode((obj.id, added_node.id,
                             added_node.parent, added_node.timestamp, added_node.data)), obj.__class__.__name__)

        def append(self, obj):
            # Insert at the end of the list
            self.insert(len(self), obj)

        def remove(self, index):
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

        def remove_by_objid(self, objid, create_edge=True):
            # We have an id remove the object. Usually from replaying an edge
            for node in self._listnodes:
                if node.obj.id == objid:
                    self.remove_by_node(node, create_edge=create_edge)
                    return
            assert False

        def remove_by_node(self, node, create_edge=True):
            # Find the given node and remove it
            obj = node.obj
            self._tombstones.add(node.id)
            if hasattr(self, "_rendered_list"):
                delattr(self, "_rendered_list")

            obj = self.parent.get_document().documentobjects[obj.id]
            del self.parent.get_document().documentobjects[obj.id]
            if create_edge:
                self.was_changed(ChangeType.REMOVE_LISTITEM, self.parent.id,
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
            ret = tuple()
            for node in matching:
                ret = ret + (node, )
                ret = ret + self._render(node.id)
            return ret

        def get_matching_list_nodes(self, nodeid):
            # Get a list of nodes with matching ids
            l = [n for n in self._listnodes if n.parent == nodeid]
            # Sort the nodes in timestamp then id order
            return sorted(l, key=lambda n: (-n.timestamp, n.id))

        def get_document(self):
            #Return the document
            return self.parent.get_document()

        def _cascade_delete(self):
            doc = self.parent.get_document()
            for item in self:
                item.delete()


    def __init__(self, theclass):
        self.theclass = theclass

    def create_instance(self, owner, name):
        return List.FieldListImpl(self.theclass, owner, name)

    def clone(self, name, src, owner):
        return getattr(src, name).clone(owner, name)

    def clean(self, owner, name):
        return getattr(owner, name).clean()

    def cascade_delete(self, owner, name):
        getattr(owner, name)._cascade_delete()

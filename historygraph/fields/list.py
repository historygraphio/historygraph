# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#An ordered list of sub objects in HistoryGraph
# From work by Marek Zawirski https://twitter.com/zzzawir/status/757635463536578560
from . import Field
from ..changetype import ChangeType
import uuid
from json import JSONEncoder, JSONDecoder

class List(Field):
    class _ListNode(object):
        def __init__(self, parent, timestamp, data, obj):
            self.id = str(uuid.uuid4())
            assert isinstance(parent, basestring)
            self.parent = parent
            self.timestamp = timestamp
            self.data = data
            self.obj = obj

    class FieldListImpl(object):
        def __init__(self, theclass, parent, name):
            self.theclass = theclass
            self.parent = parent
            assert self.parent is not None
            self.name = name
            self._listnodes = list()
            self._tombstones = set()

        def insert(self, index, obj):
            assert isinstance(obj, self.theclass)
            obj.parent = self
            self.parent.get_document().documentobjects[obj.id] = obj
            index = index - 1
            if index == -1:
                added_node = List._ListNode('', self.parent.get_document().depth(), obj.id, obj)
                self._listnodes.append(added_node)
            else:
                self.render()
                added_node = List._ListNode(self._rendered_list[index].id, self.parent.get_document().depth(), obj.id, obj)
                self._listnodes.append(added_node)
            if hasattr(self, "_rendered_list"):
                delattr(self, "_rendered_list")
                
            self.was_changed(ChangeType.ADD_LISTITEM, self.parent.id, self.name, JSONEncoder().encode((obj.id, added_node.id, added_node.parent, added_node.timestamp, added_node.data)), obj.__class__.__name__)

        def append(self, obj):
            self.insert(len(self), obj)

        def remove(self, index):
            self.render()
            node = self._rendered_list[index] # Get the node we are deleting
            self.remove_by_node(node)

        def remove_by_nodeid(self, objid):
            for node in self._listnodes:
                if node.id == objid:
                    self.remove_by_node(node)
                    return
            assert False

        def remove_by_node(self, node):
            obj = node.obj
            self._tombstones.add(node.id)
            if hasattr(self, "_rendered_list"):
                delattr(self, "_rendered_list")

            obj = self.parent.get_document().documentobjects[obj.id]
            del self.parent.get_document().documentobjects[obj.id]
            self.was_changed(ChangeType.REMOVE_LISTITEM, self.parent.id, self.name, node.id, obj.__class__.__name__)            

        def was_changed(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
            assert isinstance(propertyownerid, basestring)
            self.parent.was_changed(changetype, propertyownerid, propertyname, propertyvalue, propertytype)

        def __len__(self):
            self.render()
            return len(self._rendered_list)

        def __getitem__(self,index):
            self.render()
            return self._rendered_list[index].obj

        def clone(self, owner, name):
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
            


    def __init__(self, theclass):
        self.theclass = theclass

    def create_instance(self, owner, name):
        return List.FieldListImpl(self.theclass, owner, name)

    def clone(self, name, src, owner):
        return getattr(src, name).clone(owner, name)

    def clean(self, owner, name):
        return getattr(owner, name).clean()

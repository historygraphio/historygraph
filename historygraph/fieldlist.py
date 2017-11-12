#An ordered list of sub objects in HistoryGraph
# From work by Marek Zawirski https://twitter.com/zzzawir/status/757635463536578560
from field import Field
from changetype import ChangeType
import uuid
from json import JSONEncoder, JSONDecoder

class FieldList(Field):
    class ListNode(object):
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
            self.parent.GetDocument().documentobjects[obj.id] = obj
            index = index - 1
            if index == -1:
                added_node = FieldList.ListNode('', self.parent.GetDocument().depth(), obj.id, obj)
                self._listnodes.append(added_node)
            else:
                self.Render()
                added_node = FieldList.ListNode(self._rendered_list[index].id, self.parent.GetDocument().depth(), obj.id, obj)
                self._listnodes.append(added_node)
            if hasattr(self, "_rendered_list"):
                delattr(self, "_rendered_list")
                
            self.WasChanged(ChangeType.ADD_LISTITEM, self.parent.id, self.name, JSONEncoder().encode((obj.id, added_node.id, added_node.parent, added_node.timestamp, added_node.data)), obj.__class__.__name__)

        def append(self, obj):
            self.insert(len(self), obj)

        def remove(self, index):
            self.Render()
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

            obj = self.parent.GetDocument().documentobjects[obj.id]
            del self.parent.GetDocument().documentobjects[obj.id]
            self.WasChanged(ChangeType.REMOVE_LISTITEM, self.parent.id, self.name, node.id, obj.__class__.__name__)            

        def WasChanged(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
            assert isinstance(propertyownerid, basestring)
            self.parent.WasChanged(changetype, propertyownerid, propertyname, propertyvalue, propertytype)

        def __len__(self):
            self.Render()
            return len(self._rendered_list)

        def __getitem__(self,index):
            self.Render()
            return self._rendered_list[index].obj

        def Clone(self, owner, name):
            ret = FieldList.FieldListImpl(self.theclass, owner, name)
            ret._listnodes = list(self._listnodes)
            ret._tombstones = set(self._tombstones)
            return ret

        def Clean(self):
            self._listnodes = list()
            self._tombstones = set()
            if hasattr(self, "_rendered_list"):
                delattr(self, "_rendered_list")

        def Render(self):
            if hasattr(self, "_rendered_list"):
                return
            # Render the list - replay all of the additions
            l = self._render('')
            self._rendered_list = tuple([node for node in l if node.id not in self._tombstones])

        def _render(self, nodeid):
            matching = self.GetMatchingListNodes(nodeid)
            ret = tuple()
            for node in matching:
                ret = ret + (node, )
                ret = ret + self._render(node.id)
            return ret

        def GetMatchingListNodes(self, nodeid):
            # Get a list of nodes with matching ids
            l = [n for n in self._listnodes if n.parent == nodeid]
            # Sort the nodes in timestamp then id order
            return sorted(l, key=lambda n: (-n.timestamp, n.id))

        def GetDocument(self):
            #Return the document
            return self.parent.GetDocument()
            


    def __init__(self, theclass):
        self.theclass = theclass

    def CreateInstance(self, owner, name):
        return FieldList.FieldListImpl(self.theclass, owner, name)

    def Clone(self, name, src, owner):
        return getattr(src, name).Clone(owner, name)

    def Clean(self, owner, name):
        return getattr(owner, name).Clean()

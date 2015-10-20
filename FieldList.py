#A list of sub objects in doop
from Field import Field
from ChangeType import ChangeType

class FieldList(Field):
    class FieldListImpl(object):
        def __init__(self, theclass, parent, name):
            self.theclass = theclass
            self.parent = parent
            self.name = name
            self.l = set()

        def add(self, obj):
            assert isinstance(obj, self.theclass)
            self.l.add(obj)
            assert obj.parent is None
            obj.parent = self
            self.parent.GetDocument().documentobjects[obj.id] = obj
            self.WasChanged(ChangeType.ADD_CHILD, self.parent, self.name, obj.id, obj.__class__)

        def remove(self, obj):
            self.l.remove(obj)
            del self.parent.GetDocument().documentobjects[obj.id]
            self.WasChanged(ChangeType.REMOVE_CHILD, self.parent, self.name, obj.id, obj.__class__)            

        def WasChanged(self, changetype, propertyowner, propertyname, propertyvalue, propertytype):
            self.parent.WasChanged(changetype, propertyowner, propertyname, propertyvalue, propertytype)

        def __len__(self):
            return len(self.l)

    def __init__(self, theclass):
        self.theclass = theclass
    def CreateInstance(self, owner, name):
        return FieldList.FieldListImpl(self.theclass, owner, name)


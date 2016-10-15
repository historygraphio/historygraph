#A list of sub objects in doop
from Field import Field
from ChangeType import ChangeType

class FieldCollection(Field):
    class FieldCollectionImpl(object):
        def __init__(self, theclass, parent, name):
            self.theclass = theclass
            self.parent = parent
            self.name = name
            self.l = set()

        def add(self, obj):
            assert isinstance(obj, self.theclass)
            self.l.add(obj.id)
            assert obj.parent is None
            obj.parent = self
            self.parent.GetDocument().documentobjects[obj.id] = obj
            self.WasChanged(ChangeType.ADD_CHILD, self.parent.id, self.name, obj.id, obj.__class__.__name__)

        def remove(self, objid):
            assert isinstance(objid, basestring)
            self.l.remove(objid)
            obj = self.parent.GetDocument().documentobjects[objid]
            del self.parent.GetDocument().documentobjects[objid]
            self.WasChanged(ChangeType.REMOVE_CHILD, self.parent.id, self.name, objid, obj.__class__.__name__)            

        def WasChanged(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
            assert isinstance(propertyownerid, basestring)
            self.parent.WasChanged(changetype, propertyownerid, propertyname, propertyvalue, propertytype)

        def __len__(self):
            return len(self.l)

        def __iter__(self):
            doc = self.parent.GetDocument()
            for item in self.l:
                yield doc.documentobjects[item]

        def Clone(self, owner, name):
            ret = FieldCollection.FieldCollectionImpl(self.theclass, owner, name)
            srcdoc = self.parent.GetDocument()
            for objid in self.l:
                srcobj = srcdoc.documentobjects[objid]
                ret.add(srcobj.Clone())
            return ret


    def __init__(self, theclass):
        self.theclass = theclass
    def CreateInstance(self, owner, name):
        return FieldCollection.FieldCollectionImpl(self.theclass, owner, name)

    def Clone(self, name, src, owner):
        return getattr(src, name).Clone(owner, name)



#A DOOP Document Object
import uuid

class DocumentObject(object):
    def Clone(self):
        ret = self.__class__()
        ret.id = self.id
        ret.CopyPropertyOwner(self)
        for prop in self.properties:
            if isinstance(prop, FieldList):
                retlist = ret.getattr(prop.name)
                retlist.empty()
                for obj in prop:
                    retlist.add(obj.Clone())

    
    def __init__(self):
         self.parent = None
         self.id = str(uuid.uuid4())
         
    def WasChanged(self, changetype, propertyowner, propertyname, propertyvalue, propertytype):
         self.parent.WasChanged(changetype, propertyowner, propertyname, propertyvalue, propertytype)

    def Clone(self):
        pass

    def CopyPropertyOwner(self, src):
        pass

    

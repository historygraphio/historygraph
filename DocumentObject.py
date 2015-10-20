#A DOOP Document Object
import uuid
from Field import Field
from ChangeType import *

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

    
    def __init__(self, id):
        self.insetattr = True
        self.doop_field = dict()
        self.parent = None
        if id is None:
            id = str(uuid.uuid4())
        self.id = id
        variables = [a for a in dir(self.__class__) if not a.startswith('__') and not callable(getattr(self.__class__,a))]
        for k in variables:
            var = getattr(self.__class__, k)
            self.doop_field[k] = var
            if isinstance(var, Field):
                setattr(self, k, var.CreateInstance(self, k))
        self.insetattr = False
        
    def __setattr__(self, name, value):
        super(DocumentObject, self).__setattr__(name, value)
        if name == "insetattr" or name == "parent" or name == "isreplaying" or name == "doop_field" or self.insetattr:
            return
        self.insetattr = True
        if name in self.doop_field:
            self.WasChanged(ChangeType.SET_PROPERTY_VALUE, self.id, name, value, type(value))
        self.insetattr = False
         
    def WasChanged(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
        assert isinstance(propertyownerid, basestring)
        self.parent.WasChanged(changetype, propertyownerid, propertyname, propertyvalue, propertytype)

    def Clone(self):
        pass

    def CopyDocumentObject(self, src):
        for k in src.doop_field:
            v = src.doop_field[k]
            setattr(self, k, v.Clone(k, src))

    def GetDocument(self):
        #Return the document
        return self.parent.GetDocument()

    

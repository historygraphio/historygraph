#An integer field in DOOP
from Field import Field

class FieldInt(Field):
    def CreateInstance(self, owner, name):
        return 0

    def TranslateFromString(self, s):
        return int(s)

    def Clone(self, propertyname, src, owner):
        return getattr(src, propertyname)

    def GetTypeName(self):
        return "int"



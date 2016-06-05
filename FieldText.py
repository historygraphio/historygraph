#A text field in a DOOP object
from Field import Field

class FieldText(Field):
    def CreateInstance(self, owner, name):
        return ""

    def TranslateFromString(self, s):
        return s

    def Clone(self, propertyname, src, owner):
        return getattr(src, propertyname)

    def GetTypeName(self):
        return "basestring"



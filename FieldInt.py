#An integer field in DOOP
from Field import Field

class FieldInt(Field):
    def CreateInstance(self):
        return 0

    def TranslateFromString(self, s):
        return int(s)

    def Clone(self, propertyname, src):
        return getattr(src, propertyname)



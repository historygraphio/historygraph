#A text field in a HistoryGraph object
from field import Field

class FieldText(Field):
    def CreateInstance(self, owner, name):
        return ""

    def TranslateFromString(self, s):
        return s

    def Clone(self, propertyname, src, owner):
        return getattr(src, propertyname)

    def GetTypeName(self):
        return "basestring"

    def Clean(self, owner, name):
        pass
    

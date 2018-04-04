# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#A list of sub objects in HistoryGraph
from . import Field
from ..changetype import ChangeType

class Collection(Field):
    class _FieldCollectionImpl(object):
        # This implementation class is what actually get attacted to the document object to implement the required
        # behaviour
        def __init__(self, theclass, parent, name):
            self.theclass = theclass
            self.parent = parent
            self.name = name
            self.l = set()

        def add(self, obj):
            # Add a new document object to the collection
            assert isinstance(obj, self.theclass)
            self.l.add(obj.id)
            assert obj.parent is None or obj.parent is self
            obj.parent = self
            self.parent.get_document().documentobjects[obj.id] = obj
            self.was_changed(ChangeType.ADD_CHILD, self.parent.id, self.name, obj.id, obj.__class__.__name__)

        def remove(self, objid):
            assert isinstance(objid, basestring)
            self.l.remove(objid)
            obj = self.parent.get_document().documentobjects[objid]
            del self.parent.get_document().documentobjects[objid]
            self.was_changed(ChangeType.REMOVE_CHILD, self.parent.id, self.name, objid, obj.__class__.__name__)            

        def was_changed(self, changetype, propertyownerid, propertyname, propertyvalue, propertytype):
            # TODO: Possible balloonian function
            assert isinstance(propertyownerid, basestring)
            if not self.parent.insetattr:
                self.parent.was_changed(changetype, propertyownerid, propertyname, propertyvalue, propertytype)

        def __len__(self):
            return len(self.l)

        def __iter__(self):
            doc = self.parent.get_document()
            for item in self.l:
                yield doc.documentobjects[item]

        def clone(self, owner, name):
            # Create a deepcopy style clone of this collection
            ret = Collection._FieldCollectionImpl(self.theclass, owner, name)
            srcdoc = self.parent.get_document()
            for objid in self.l:
                srcobj = srcdoc.documentobjects[objid]
                ret.add(srcobj.clone())
            return ret

        def clean(self):
            self.l = set()

        def get_document(self):
            #Return the document
            return self.parent.get_document()


    def __init__(self, theclass):
        self.theclass = theclass

    def create_instance(self, owner, name):
        return Collection._FieldCollectionImpl(self.theclass, owner, name)

    def clone(self, name, src, owner):
        return getattr(src, name).clone(owner, name)

    def clean(self, owner, name):
        return getattr(owner, name).clean()

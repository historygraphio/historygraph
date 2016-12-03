# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import unittest
from DocumentCollection import DocumentCollection
from DocumentObject import DocumentObject
from Document import Document
from FieldIntRegister import FieldIntRegister
from FieldCollection import FieldCollection

class TestPropertyOwner2(DocumentObject):
    cover = FieldIntRegister()
    quantity = FieldIntRegister()

class TestPropertyOwner1(Document):
    covers = FieldIntRegister()
    propertyowner2s = FieldCollection(TestPropertyOwner2)
    def WasChanged(self, changetype, propertyowner, propertyname, propertyvalue, propertytype):
        super(TestPropertyOwner1, self).WasChanged(changetype, propertyowner, propertyname, propertyvalue, propertytype)
        self.bWasChanged = True

class Covers(Document):
    def __init__(self, id):
        super(Covers, self).__init__(id)
    covers = FieldIntRegister()

class SimpleCoversTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(TestPropertyOwner1)
        self.dc.Register(TestPropertyOwner2)

    def runTest(self):
        #Test merging together simple covers documents
        test = Covers(None)
        test.covers = 1
        #Test we can set a value
        self.assertEqual(test.covers, 1)
        test2 = Covers(test.id)
        test.history.Replay(test2)
        #Test we can rebuild a simple object by playing an edge
        self.assertEqual(test2.covers, 1)
        #Test these are just the same history object but it was actually copied
        assert test.history is not test2.history
        
        test3 = test2.Clone()
        #Test the clone is the same as the original. But not just refering to the same object
        self.assertEqual(test3.covers, test2.covers)
        assert test2 is not test3
        assert test2.history is not test3.history
        
        test = Covers(None)
        test.covers = 1
        test.covers = 2
        test2 = Covers(test.id)
        test.history.Replay(test2)
        self.assertEqual(test.covers, 2)
        assert test.history is not test2.history
        assert test is not test2
    


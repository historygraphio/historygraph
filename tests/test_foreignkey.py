# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection
from historygraph import Document
from historygraph import fields
from decimal import Decimal
import uuid


class DecimalRegisterClass(Document):
    test_decimal = fields.DecimalRegister()


class ForeignKeyTest(Document):
    test_fk = fields.ForeignKey(DecimalRegisterClass)


class ForeignKeyTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection()
        self.dc1.register(DecimalRegisterClass)
        self.dc1.register(ForeignKeyTest)
        self.dc2 = DocumentCollection(master=self.dc1)
        self.dc2.register(DecimalRegisterClass)
        self.dc2.register(ForeignKeyTest)

    def test_covers_with_single_edge(self):
        test = DecimalRegisterClass()
        self.dc1.add_document_object(test)
        test.test_decimal = Decimal('0.5')
        test_fk = ForeignKeyTest()
        self.dc1.add_document_object(test_fk)
        test_fk.test_fk = test
        #Test we can set a value
        self.assertEqual(test.test_decimal, Decimal('0.5'))
        self.assertEqual(test_fk.test_fk.id, test.id)
        #Test we can rebuild a simple object by playing an edge via sharing in linked DCs
        test2 = self.dc2.get_object_by_id(DecimalRegisterClass.__name__, test.id)
        test2_fk = self.dc2.get_object_by_id(ForeignKeyTest.__name__, test_fk.id)
        self.assertEqual(test2.test_decimal, Decimal('0.5'))
        self.assertEqual(test2_fk.test_fk.id, test2.id)
        #Test these are not just the same document but it was actually copied
        assert test is not test2
        assert test.history is not test2.history

        assert test_fk is not test2_fk
        assert test_fk.history is not test2_fk.history

    def test_covers_with_two_edges(self):
        test = DecimalRegisterClass()
        self.dc1.add_document_object(test)
        test.test_decimal = Decimal('0.5')
        test2 = DecimalRegisterClass()
        self.dc1.add_document_object(test2)
        test2.test_decimal = Decimal('0.9')
        test_fk = ForeignKeyTest()
        self.dc1.add_document_object(test_fk)
        test_fk.test_fk = test
        #Test we can set a value
        self.assertEqual(test.test_decimal, Decimal('0.5'))
        self.assertEqual(test_fk.test_fk.id, test.id)
        test_fk.test_fk = test2
        #Test we can update a value
        self.assertEqual(test2.test_decimal, Decimal('0.9'))
        self.assertEqual(test_fk.test_fk.id, test2.id)
        #Test we can rebuild a simple object by playing an edge via sharing in linked DCs
        test2 = self.dc2.get_object_by_id(DecimalRegisterClass.__name__, test2.id)
        test2_fk = self.dc2.get_object_by_id(ForeignKeyTest.__name__, test_fk.id)
        self.assertEqual(test2.test_decimal, Decimal('0.9'))
        self.assertEqual(test2_fk.test_fk.id, test2.id)

    def test_merge_of_foreignkeys(self):
        test = DecimalRegisterClass(id='e77dbe66-553d-4960-9601-929b2e104a2d')
        self.dc1.add_document_object(test)
        test.test_decimal = Decimal('0.5')
        test2 = DecimalRegisterClass(id='d67f239c-a628-49ff-8ecb-a8766ae75502')
        self.dc1.add_document_object(test2)
        test2.test_decimal = Decimal('0.9')
        test_fk = ForeignKeyTest()
        self.dc1.add_document_object(test_fk)
        test_fk.test_fk = None

        self.dc2.freeze_dc_comms()
        test_fk.test_fk = test
        test2_fk = self.dc2.get_object_by_id(ForeignKeyTest.__name__, test_fk.id)
        test2_fk.test_fk = test2

        self.dc2.unfreeze_dc_comms()
        #Test the merge resolves correctly
        self.assertEqual(test_fk.test_fk.id, test.id)
        self.assertEqual(test2_fk.test_fk.id, test.id)

    def test_merge_of_foreignkeys_reverse(self):
        test = DecimalRegisterClass(id='d67f239c-a628-49ff-8ecb-a8766ae75502')
        self.dc1.add_document_object(test)
        test.test_decimal = Decimal('0.5')
        test2 = DecimalRegisterClass(id='e77dbe66-553d-4960-9601-929b2e104a2d')
        self.dc1.add_document_object(test2)
        test2.test_decimal = Decimal('0.9')
        test_fk = ForeignKeyTest()
        self.dc1.add_document_object(test_fk)
        test_fk.test_fk = None

        self.dc2.freeze_dc_comms()
        test_fk.test_fk = test
        test2_fk = self.dc2.get_object_by_id(ForeignKeyTest.__name__, test_fk.id)
        test2_fk.test_fk = test2

        self.dc2.unfreeze_dc_comms()
        #Test the merge resolves correctly
        self.assertEqual(test_fk.test_fk.id, test2.id)
        self.assertEqual(test2_fk.test_fk.id, test2.id)

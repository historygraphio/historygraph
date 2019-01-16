# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection
from historygraph import Document
from historygraph import fields
from decimal import Decimal


class DecimalRegisterClass(Document):
    test_decimal = fields.DecimalRegister()


class DecimalRegisterTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection()
        self.dc1.register(DecimalRegisterClass)
        self.dc2 = DocumentCollection(master=self.dc1)
        self.dc2.register(DecimalRegisterClass)

    def test_covers_with_single_edge(self):
        #Test merging together simple covers documents
        test = DecimalRegisterClass()
        self.dc1.add_document_object(test)
        test.test_decimal = Decimal('0.5')
        #Test we can set a value
        self.assertEqual(test.test_decimal, Decimal('0.5'))
        #Test we can rebuild a simple object by playing an edge via sharing in linked DCs
        test2 = self.dc2.get_object_by_id(DecimalRegisterClass.__name__, test.id)
        self.assertEqual(test2.test_decimal, Decimal('0.5'))
        #Test these are not just the same document but it was actually copied
        assert test is not test2
        assert test.history is not test2.history

    def test_covers_with_two_edges(self):
        test = DecimalRegisterClass()
        self.dc1.add_document_object(test)
        test.test_decimal = Decimal('0.1')
        test.test_decimal = Decimal('0.2')
        test2 = self.dc2.get_object_by_id(DecimalRegisterClass.__name__, test.id)
        self.assertEqual(test.test_decimal, Decimal('0.2'))
        assert test.history is not test2.history
        assert test is not test2

    def test_merge_of_float_registers(self):
        #Test merge together two simple covers objects
        test = DecimalRegisterClass()
        self.dc1.add_document_object(test)
        test.test_decimal = Decimal('0.1')
        test2 = self.dc2.get_object_by_id(DecimalRegisterClass.__name__, test.id)
        self.dc2.freeze_dc_comms()
        test.test_decimal = Decimal('0.2')
        self.assertEqual(test2.test_decimal, Decimal('0.1'))
        test2.test_decimal = Decimal('0.3')
        self.assertEqual(test.test_decimal, Decimal('0.2'))
        self.assertEqual(test2.test_decimal, Decimal('0.3'))
        self.dc2.unfreeze_dc_comms()
        #In a merge conflict between two integers the greater one is the winner
        edges = [e.as_tuple() for e in test2.history.get_all_edges()]
        self.assertEqual(test2.test_decimal, Decimal('0.3'), 'test.covers={} test2.covers={} edges={}'.format(test.test_decimal, test2.test_decimal, edges))
        edges = [e.as_tuple() for e in test.history.get_all_edges()]
        self.assertEqual(test.test_decimal, Decimal('0.3'), 'test.covers={} test2.covers={} edges={}'.format(test.test_decimal, test2.test_decimal, edges))

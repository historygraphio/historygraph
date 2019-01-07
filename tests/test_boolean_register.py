# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection
from historygraph import Document
from historygraph import fields


class BooleanRegisterClass(Document):
    test_boolean = fields.BooleanRegister()


class BooleanRegisterTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection()
        self.dc1.register(BooleanRegisterClass)
        self.dc2 = DocumentCollection(master=self.dc1)
        self.dc2.register(BooleanRegisterClass)

    def test_boolean_register_with_single_edge(self):
        #Test merging together simple boolean register documents
        test = BooleanRegisterClass()
        self.dc1.add_document_object(test)
        test.test_boolean = True
        #Test we can set a value
        self.assertEqual(test.test_boolean, True)
        #Test we can rebuild a simple object by playing an edge via sharing in linked DCs
        test2 = self.dc2.get_object_by_id(BooleanRegisterClass.__name__, test.id)
        self.assertEqual(test2.test_boolean, True)
        #Test these are not just the same document but it was actually copied
        assert test is not test2
        assert test.history is not test2.history

    def test_boolean_register_with_two_edges(self):
        test = BooleanRegisterClass()
        self.dc1.add_document_object(test)
        test.test_boolean = True
        test.test_boolean = False
        test2 = self.dc2.get_object_by_id(BooleanRegisterClass.__name__, test.id)
        self.assertEqual(test.test_boolean, False)
        assert test.history is not test2.history
        assert test is not test2

    def test_merge_of_boolean_registers(self):
        #Test merge together two simple boolean register objects
        test = BooleanRegisterClass()
        self.dc1.add_document_object(test)
        test.test_boolean = False
        test2 = self.dc2.get_object_by_id(BooleanRegisterClass.__name__, test.id)
        self.dc2.freeze_dc_comms()
        test.test_boolean = True
        self.assertEqual(test2.test_boolean, False)
        test2.test_boolean = False
        self.assertEqual(test.test_boolean, True)
        self.assertEqual(test2.test_boolean, False)
        self.dc2.unfreeze_dc_comms()
        #In a merge conflict between two integers the greater one is the winner
        edges = [e.as_tuple() for e in test2.history.get_all_edges()]
        self.assertEqual(test2.test_boolean, True, 'test.test_boolean={} test2.test_boolean={} edges={}'.format(test.test_boolean, test2.test_boolean, edges))
        edges = [e.as_tuple() for e in test.history.get_all_edges()]
        self.assertEqual(test.test_boolean, True, 'test.test_boolean={} test2.test_boolean={} edges={}'.format(test.test_boolean, test2.test_boolean, edges))

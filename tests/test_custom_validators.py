from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection, Covers, CounterTestContainer
from historygraph.edges import SimpleProperty, AddIntCounter, Merge
from historygraph.historygraph import get_transaction_hash
import hashlib
import uuid


class SimpleCustomValidationTestCase(unittest.TestCase):
    class Between1And5(object):
        @classmethod
        def is_valid(cls, edge, historygraph):
            is_valid_called['result'] = True
            return True

    def setUp(self):
        self.dc1 = DocumentCollection(has_standard_validators=False)
        self.dc1.register(Covers)

    def test_success(self):
        is_valid_called = dict()
        is_valid_called['result'] = False
        class AlwaysValid(object):
            @classmethod
            def is_valid(cls, edges_list, historygraph):
                is_valid_called['result'] = True
                return True


        self.dc1.register_custom_validator(AlwaysValid)
        test1 = Covers()
        self.dc1.add_document_object(test1)
        test1.covers = 1
        self.assertEqual(len(test1.history._edgesbyendnode), 1)
        transaction_test1 = test1.transaction(custom_transaction=AlwaysValid)
        self.assertEqual(len(transaction_test1.history._edgesbyendnode) + len(transaction_test1.history._added_edges), 2)
        self.assertEqual(len(transaction_test1.history._added_edges), 1)
        transaction_test1.covers = 2
        self.assertEqual(len(transaction_test1.history._added_edges), 2)
        transaction_test1.endtransaction()
        self.assertEqual(len(test1.history._edgesbyendnode), 3)
        self.assertEqual(test1.covers,2)
        self.assertTrue(is_valid_called['result'])

        """
        last_edge = test.history.get_edges_by_end_node(test._clockhash)

        edge = SimpleProperty({test._clockhash},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 2,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, last_edge.nonce)

        test.full_replay([edge])

        self.assertEqual(test.covers, 2)
        self.assertTrue(is_valid_called['result'])
        """

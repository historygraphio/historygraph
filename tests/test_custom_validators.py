from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection, Covers, CounterTestContainer
from historygraph.edges import SimpleProperty, AddIntCounter, Merge
from historygraph.historygraph import get_transaction_hash
import hashlib
import uuid
from historygraph import edges


class SimpleCustomValidationTestCase(unittest.TestCase):
    class Between1And5(object):
        @classmethod
        def is_valid(cls, edges_list, historygraph):
            if len(edges_list) > 2:
                # Only set a single edge in this transacrtion
                return False
            edge = edges_list[1]
            if not isinstance(edge, SimpleProperty) or \
               not edge.documentclassname == Covers.__name__ or \
               not edge.propertyname == 'covers':
                # Check the edge type, document type and the property it attachs to
                return False
            try:
                int_value = int(edge.propertyvalue)
            except ValueError as ex:
                # Return false if we can't convert to an int
                return False
            # Return true iff between 1 and 5 (inclusive)
            return int_value >= 1 and int_value <= 5

    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()), has_standard_validators=False)
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

    def test_success_on_real_test(self):
        self.dc1.register_custom_validator(SimpleCustomValidationTestCase.Between1And5)
        test1 = Covers()
        self.dc1.add_document_object(test1)
        test1.covers = 1
        self.assertEqual(len(test1.history._edgesbyendnode), 1)
        transaction_test1 = test1.transaction(custom_transaction=SimpleCustomValidationTestCase.Between1And5)
        self.assertEqual(len(transaction_test1.history._edgesbyendnode) + len(transaction_test1.history._added_edges), 2)
        self.assertEqual(len(transaction_test1.history._added_edges), 1)
        transaction_test1.covers = 2
        self.assertEqual(len(transaction_test1.history._added_edges), 2)
        transaction_test1.endtransaction()
        self.assertEqual(len(test1.history._edgesbyendnode), 3)
        self.assertEqual(test1.covers,2)

    def test_fails_on_value_too_large(self):
        self.dc1.register_custom_validator(SimpleCustomValidationTestCase.Between1And5)
        test1 = Covers()
        self.dc1.add_document_object(test1)
        test1.covers = 1
        self.assertEqual(len(test1.history._edgesbyendnode), 1)
        transaction_test1 = test1.transaction(custom_transaction=SimpleCustomValidationTestCase.Between1And5)
        self.assertEqual(len(transaction_test1.history._edgesbyendnode) + len(transaction_test1.history._added_edges), 2)
        self.assertEqual(len(transaction_test1.history._added_edges), 1)
        transaction_test1.covers = 9
        self.assertEqual(len(transaction_test1.history._added_edges), 2)
        with self.assertRaises(AssertionError):
            transaction_test1.endtransaction()
        self.assertEqual(len(test1.history._edgesbyendnode), 1)
        self.assertEqual(test1.covers,1)

    def test_fails_on_value_too_large_manually_created_transaction(self):
        self.dc1.register_custom_validator(SimpleCustomValidationTestCase.Between1And5)
        test1 = Covers()
        self.dc1.add_document_object(test1)
        test1.covers = 1
        self.assertEqual(len(test1.history._edgesbyendnode), 1)
        transaction_test1 = test1.transaction(custom_transaction=SimpleCustomValidationTestCase.Between1And5)
        self.assertEqual(len(transaction_test1.history._edgesbyendnode) + len(transaction_test1.history._added_edges), 2)
        self.assertEqual(len(transaction_test1.history._added_edges), 1)
        last_edge = transaction_test1.history.get_last_transaction_edge()

        edge = SimpleProperty({transaction_test1._clockhash},
                              test1.id,
                              'covers', 9,
                              'int', last_edge.documentid,
                              last_edge.documentclassname, last_edge.sessionid,
                              last_edge.transaction_hash)

        edges = [last_edge, edge]
        transaction_hash = get_transaction_hash(edges)
        #print('test_success transaction_hash=', transaction_hash)
        #print('test_success edges.get_transaction_info_hash=', ','.join([edge.get_transaction_info_hash() for edge in edges]))
        for i in range(len(edges)):
            edge = edges[i]
            edge.transaction_hash = transaction_hash
            if i > 0:
                edge._start_hashes = [edges[i - 1].get_end_node()]

        test1.full_replay(edges)

        self.assertEqual(test1.covers, 1)


class ValueDependentValidationTestCase(unittest.TestCase):
    # Test that we can
    class MustAlwaysIncrease(object):
        @classmethod
        def is_valid(cls, edges_list, historygraph):
            if len(edges_list) > 2:
                # Only set a single edge in this transacrtion
                return False
            edge = edges_list[1]
            if not isinstance(edge, SimpleProperty) or \
               not edge.documentclassname == Covers.__name__ or \
               not edge.propertyname == 'covers':
                # Check the edge type, document type and the property it attachs to
                return False
            try:
                int_value = int(edge.propertyvalue)
            except ValueError as ex:
                # Return false if we can't convert to an int
                return False
            # Get the previous value
            doc = Covers(id=edge.documentid)
            doc.dc = historygraph.dc
            #if edges_list[0]._start_hashes[0] not in historygraph._edgesbyendnode:
            #    return False
            historygraph.replay(doc, to=edges_list[0]._start_hashes[0])
            # Return true iff between 1 and 5 (inclusive)
            return int_value > doc.covers

    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()), has_standard_validators=False)
        self.dc1.register(Covers)

    def test_success_on_real_validation_test(self):
        self.dc1.register_custom_validator(ValueDependentValidationTestCase.MustAlwaysIncrease)
        test1 = Covers()
        self.dc1.add_document_object(test1)
        test1.covers = 1
        self.assertEqual(len(test1.history._edgesbyendnode), 1)
        transaction_test1 = test1.transaction(custom_transaction=ValueDependentValidationTestCase.MustAlwaysIncrease)
        self.assertEqual(len(transaction_test1.history._edgesbyendnode) + len(transaction_test1.history._added_edges), 2)
        self.assertEqual(len(transaction_test1.history._added_edges), 1)
        transaction_test1.covers = 2
        self.assertEqual(len(transaction_test1.history._added_edges), 2)
        transaction_test1.endtransaction()
        self.assertEqual(len(test1.history._edgesbyendnode), 3)
        self.assertEqual(test1.covers,2)

    def test_fails_on_value_decreases(self):
        self.dc1.register_custom_validator(ValueDependentValidationTestCase.MustAlwaysIncrease)
        test1 = Covers()
        self.dc1.add_document_object(test1)
        test1.covers = 2
        self.assertEqual(len(test1.history._edgesbyendnode), 1)
        transaction_test1 = test1.transaction(custom_transaction=ValueDependentValidationTestCase.MustAlwaysIncrease)
        self.assertEqual(len(transaction_test1.history._edgesbyendnode) + len(transaction_test1.history._added_edges), 2)
        self.assertEqual(len(transaction_test1.history._added_edges), 1)
        transaction_test1.covers = 1
        self.assertEqual(len(transaction_test1.history._added_edges), 2)
        with self.assertRaises(AssertionError):
            transaction_test1.endtransaction()
        self.assertEqual(len(test1.history._edgesbyendnode), 1)
        self.assertEqual(test1.covers,2)

    def test_fails_on_value_decrease_manually_created_transaction(self):
        self.dc1.register_custom_validator(ValueDependentValidationTestCase.MustAlwaysIncrease)
        test1 = Covers()
        self.dc1.add_document_object(test1)
        test1.covers = 2
        self.assertEqual(len(test1.history._edgesbyendnode), 1)
        transaction_test1 = test1.transaction(custom_transaction=ValueDependentValidationTestCase.MustAlwaysIncrease)
        self.assertEqual(len(transaction_test1.history._edgesbyendnode) + len(transaction_test1.history._added_edges), 2)
        self.assertEqual(len(transaction_test1.history._added_edges), 1)
        last_edge = transaction_test1.history.get_last_transaction_edge()

        edge = SimpleProperty({transaction_test1._clockhash},
                              test1.id,
                              'covers', 1,
                              'int', last_edge.documentid,
                              last_edge.documentclassname, last_edge.sessionid,
                              last_edge.transaction_hash)

        edges = [last_edge, edge]
        transaction_hash = get_transaction_hash(edges)
        #print('test_success transaction_hash=', transaction_hash)
        #print('test_success edges.get_transaction_info_hash=', ','.join([edge.get_transaction_info_hash() for edge in edges]))
        for i in range(len(edges)):
            edge = edges[i]
            edge.transaction_hash = transaction_hash
            if i > 0:
                edge._start_hashes = [edges[i - 1].get_end_node()]

        test1.full_replay(edges)

        self.assertEqual(test1.covers, 2)

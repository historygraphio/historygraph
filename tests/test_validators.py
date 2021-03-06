from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection, Covers, CounterTestContainer
from historygraph.edges import SimpleProperty, AddIntCounter, Merge
from historygraph.historygraph import get_transaction_hash
import hashlib
import uuid



class SimpleValidationTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()), has_standard_validators=False)
        self.dc1.register(Covers)

    def test_success(self):
        is_valid_called = dict()
        is_valid_called['result'] = False
        def always_valid(edge, historygraph):
            is_valid_called['result'] = True
            return True

        self.dc1.register_validator(always_valid)
        test = Covers()
        self.dc1.add_document_object(test)
        test.covers = 1

        last_edge = test.history.get_edges_by_end_node(test._clockhash)

        edge = SimpleProperty({test._clockhash},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 2,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, last_edge.sessionid)

        test.full_replay([edge])

        self.assertEqual(test.covers, 2)
        self.assertTrue(is_valid_called['result'])

    def test_failing(self):
        is_valid_called = dict()
        is_valid_called['result'] = False
        def fail_if_greater_than_2(edge, historygraph):
            is_valid_called['result'] = True
            if edge.documentclassname == 'Covers' and edge.propertyname == 'covers':
                return edge.propertyvalue < 2
            return True

        self.dc1.register_validator(fail_if_greater_than_2)
        test = Covers()
        self.dc1.add_document_object(test)
        test.covers = 1

        last_edge = test.history.get_edges_by_end_node(test._clockhash)

        edge = SimpleProperty({test._clockhash},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 2,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, last_edge.sessionid)

        test.full_replay([edge])

        self.assertEqual(test.covers, 1)
        self.assertEqual(test._clockhash, last_edge.get_end_node())
        self.assertTrue(is_valid_called['result'])

class StandardValidationTestCase(unittest.TestCase):
    # The standard validators should only allow ints to be applied to
    # intcounter fields
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()),has_standard_validators=True)
        self.dc1.register(CounterTestContainer)

    def test_success(self):
        test = CounterTestContainer()
        self.dc1.add_document_object(test)
        test.testcounter.add(1)

        last_edge = test.history.get_edges_by_end_node(test._clockhash)

        edge = AddIntCounter({test._clockhash},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 1,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, last_edge.sessionid)

        test.full_replay([edge])

        self.assertEqual(test.testcounter.get(), 2)

    def test_failing(self):
        test = CounterTestContainer()
        self.dc1.add_document_object(test)
        test.testcounter.add(1)

        last_edge = test.history.get_edges_by_end_node(test._clockhash)

        edge = AddIntCounter({test._clockhash},
                              last_edge.propertyownerid,
                              last_edge.propertyname, "hello",
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, last_edge.sessionid)

        test.full_replay([edge])

        self.assertEqual(test.testcounter.get(), 1)
        self.assertEqual(test._clockhash, last_edge.get_end_node())

class StandardTransactionValidationTestCase(unittest.TestCase):
    # The standard validators should only allow ints to be applied to
    # intcounter fields
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()), has_standard_validators=True)
        self.dc1.register(CounterTestContainer)

    def test_success(self):
        test = CounterTestContainer()
        self.dc1.add_document_object(test)
        test.testcounter.add(1)

        last_edge = test.history.get_edges_by_end_node(test._clockhash)

        edge1 = AddIntCounter({test._clockhash},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 1,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, last_edge.sessionid)
        edge2 = AddIntCounter({edge1.get_end_node()},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 1,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, last_edge.sessionid)
        edges = [ edge1, edge2 ]

        transaction_hash = get_transaction_hash(edges)
        #print('test_success transaction_hash=', transaction_hash)
        #print('test_success edges.get_transaction_info_hash=', ','.join([edge.get_transaction_info_hash() for edge in edges]))
        for i in range(len(edges)):
            edge = edges[i]
            edge.clear_end_node_cache()
            edge.transaction_hash = transaction_hash
            if i > 0:
                edge._start_hashes = [edges[i - 1].get_end_node()]

        test.full_replay(edges)

        self.assertEqual(test.testcounter.get(), 3)

    def test_incorrect_hash_transaction_is_rejected(self):
        test = CounterTestContainer()
        self.dc1.add_document_object(test)
        test.testcounter.add(1)

        last_edge = test.history.get_edges_by_end_node(test._clockhash)

        edge1 = AddIntCounter({test._clockhash},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 1,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, str(uuid.uuid4()))
        edge2 = AddIntCounter({edge1.get_end_node()},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 1,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, str(uuid.uuid4()))
        edges = [ edge1, edge2 ]

        transaction_hash = hashlib.sha256(','.join([str(edge.get_transaction_info_hash())
            for edge in edges]).encode('utf-8')).hexdigest()
        for i in range(len(edges)):
            edge = edges[i]
            edge.transaction_hash = transaction_hash
            if i > 0:
                edge._start_hashes = [edges[i - 1].get_end_node()]

        test.full_replay(edges)

        self.assertEqual(test.testcounter.get(), 1)

    def test_missing_edge_is_rejected(self):
        test = CounterTestContainer()
        self.dc1.add_document_object(test)
        test.testcounter.add(1)

        last_edge = test.history.get_edges_by_end_node(test._clockhash)

        edge1 = AddIntCounter({test._clockhash},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 1,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, str(uuid.uuid4()))
        edge2 = AddIntCounter({edge1.get_end_node()},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 1,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, str(uuid.uuid4()))
        edge3 = AddIntCounter({edge2.get_end_node()},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 1,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, str(uuid.uuid4()))
        edges = [ edge1, edge2, edge3 ]

        transaction_hash = hashlib.sha256(','.join([str(edge.get_transaction_info_hash())
            for edge in edges]).encode('utf-8')).hexdigest()

        for i in range(len(edges)):
            edge = edges[i]
            edge.transaction_hash = transaction_hash
            if i > 0:
                edge._start_hashes = [edges[i - 1].get_end_node()]

        test.full_replay([ edge1, edge3 ])

        self.assertEqual(test.testcounter.get(), 1)

    def test_transaction_containing_merge_is_rejected(self):
        test = CounterTestContainer()
        self.dc1.add_document_object(test)
        test.testcounter.add(1)

        last_edge = test.history.get_edges_by_end_node(test._clockhash)

        edge1 = AddIntCounter({test._clockhash},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 1,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, str(uuid.uuid4()))
        edge2 = AddIntCounter({edge1.get_end_node(), test._clockhash},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 1,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, str(uuid.uuid4()))
        edge3 = Merge({edge1.get_end_node(), edge2.get_end_node()},
                              '',
                              '', '',
                              '', last_edge.documentid,
                              last_edge.documentclassname, '')
        edges = [ edge1, edge2, edge3 ]

        transaction_hash = hashlib.sha256(','.join([str(edge.get_transaction_info_hash())
            for edge in edges]).encode('utf-8')).hexdigest()
        for i in range(len(edges)):
            edge = edges[i]
            edge.transaction_hash = transaction_hash
            if i > 0:
                edge._start_hashes = [edges[i - 1].get_end_node()]

        edge3._start_hashes = {edge1.get_end_node(), edge2.get_end_node()}

        test.full_replay(edges)

        self.assertEqual(test.testcounter.get(), 1)

    def test_forking_transaction_is_rejected(self):
        test = CounterTestContainer()
        self.dc1.add_document_object(test)
        test.testcounter.add(1)

        last_edge = test.history.get_edges_by_end_node(test._clockhash)

        edge1 = AddIntCounter({test._clockhash},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 1,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, str(uuid.uuid4()))
        edge2 = AddIntCounter({edge1.get_end_node()},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 1,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, str(uuid.uuid4()))
        edge3 = AddIntCounter({edge1.get_end_node()},
                              last_edge.propertyownerid,
                              last_edge.propertyname, 1,
                              last_edge.propertytype, last_edge.documentid,
                              last_edge.documentclassname, str(uuid.uuid4()))
        edges = [ edge1, edge2, edge3 ]

        transaction_hash = hashlib.sha256(','.join([str(edge.get_transaction_info_hash())
            for edge in edges]).encode('utf-8')).hexdigest()

        for i in range(len(edges)):
            edge = edges[i]
            edge.transaction_hash = transaction_hash
            if i > 0:
                edge._start_hashes = [edges[i - 1].get_end_node()]

        edge2._start_hashes = {edge1.get_end_node()}
        edge3._start_hashes = {edge1.get_end_node()}

        test.full_replay([ edge1, edge2, edge3 ])

        self.assertEqual(test.testcounter.get(), 1)

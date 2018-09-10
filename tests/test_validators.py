from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection, Covers, CounterTestContainer
from historygraph.edges import SimpleProperty, AddIntCounter

class SimpleValidationTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(has_standard_validators=False)
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
                              last_edge.documentclassname, last_edge.nonce)

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
                              last_edge.documentclassname, last_edge.nonce)

        test.full_replay([edge])

        self.assertEqual(test.covers, 1)
        self.assertEqual(test._clockhash, last_edge.get_end_node())
        self.assertTrue(is_valid_called['result'])

class StandardValidationTestCase(unittest.TestCase):
    # The standard validators should only allow ints to be applied to
    # intcounter fields
    def setUp(self):
        self.dc1 = DocumentCollection(has_standard_validators=True)
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
                              last_edge.documentclassname, last_edge.nonce)

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
                              last_edge.documentclassname, last_edge.nonce)

        test.full_replay([edge])

        self.assertEqual(test.testcounter.get(), 1)
        self.assertEqual(test._clockhash, last_edge.get_end_node())

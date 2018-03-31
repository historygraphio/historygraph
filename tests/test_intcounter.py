from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection, CounterTestContainer


class IntCounterTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection()
        self.dc1.register(CounterTestContainer)
        self.dc2 = DocumentCollection(master=self.dc1)
        self.dc2.register(CounterTestContainer)

    def test_parallel_int_counters_of_the_same_value(self):
        # We need to test that two int counter at the same time and amount
        # give the correct outcome. The proof of concept version naively
        # gave the wrong value
        test1 = CounterTestContainer()
        self.dc1.add_document_object(test1)
        test1.testcounter.add(1)
        self.assertEqual(test1.testcounter.get(), 1)
        test2 = self.dc2.get_object_by_id(CounterTestContainer.__name__, test1.id)
        self.dc2.freeze_dc_comms()
        test1.testcounter.add(1)
        test2.testcounter.add(1)
        self.dc2.unfreeze_dc_comms()
        self.assertEqual(test1.testcounter.get(), 3)
        self.assertEqual(test2.testcounter.get(), 3)



from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection, FloatCounterTestContainer
import uuid


class FloatCounterTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(uuid.uuid4())
        self.dc1.register(FloatCounterTestContainer)
        self.dc2 = DocumentCollection(uuid.uuid4(), master=self.dc1)
        self.dc2.register(FloatCounterTestContainer)

    def test_parallel_float_counters_of_the_same_value(self):
        # We need to test that two int counter at the same time and amount
        # give the correct outcome. The proof of concept version naively
        # gave the wrong value
        test1 = FloatCounterTestContainer()
        self.dc1.add_document_object(test1)
        test1.testcounter.add(0.1)
        self.assertAlmostEqual(test1.testcounter.get(), 0.1)
        test2 = self.dc2.get_object_by_id(FloatCounterTestContainer.__name__, test1.id)
        self.dc2.freeze_dc_comms()
        test1.testcounter.add(0.1)
        test2.testcounter.add(0.1)
        self.dc2.unfreeze_dc_comms()
        self.assertAlmostEqual(test1.testcounter.get(), 0.3)
        self.assertAlmostEqual(test2.testcounter.get(), 0.3)

# Code that is useful for running tests inside IDLE
#if __name__ == '__main__':
#    suite = unittest.TestLoader().loadTestsFromName( 'test_intcounter.IntCounterTestCase.test_parallel_int_counters_of_the_same_value' )
#    unittest.TextTestRunner(verbosity=2).run( suite )

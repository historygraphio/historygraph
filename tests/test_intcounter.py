from __future__ import absolute_import, unicode_literals, print_function

import unittest


class IntCounterTestCase(unittest.TestCase):
    def test_parallel_int_counters_of_the_same_value(self):
        # We need to test that two int counter at the same time and amount
        # give the correct outcome. The proof of concept version naively
        # gave the wrong value
        pass



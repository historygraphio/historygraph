from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection, Covers


class HistoryGraphReplayToIDTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection()
        self.dc1.register(Covers)
        self.dc2 = DocumentCollection(master=self.dc1)
        self.dc2.register(Covers)

    def test_replay_to_id(self):
        test1 = Covers()
        self.dc1.add_document_object(test1)
        test1.covers = 1
        clockhash1 = test1._clockhash
        test1.covers = 2
        clockhash2 = test1._clockhash
        test1.covers = 3
        clockhash3 = test1._clockhash

        history2 = test1.history.past_or_equal(clockhash2)
        self.assertEqual(len(history2._edgesbyendnode), 2)
        self.assertIn(clockhash1, history2._edgesbyendnode)
        self.assertIn(clockhash2, history2._edgesbyendnode)

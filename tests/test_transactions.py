from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection, Covers, TestPropertyOwner2, TestPropertyOwner1
from historygraph.edges import EndTransaction


class TransactionTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection()
        self.dc1.register(Covers)
        self.dc2 = DocumentCollection(master=self.dc1)
        self.dc2.register(Covers)

    def test_frozen_function_basic(self):
        test1 = Covers()
        self.dc1.add_document_object(test1)
        test1.covers = 1
        test2 = self.dc2.get_object_by_id(Covers.__name__, test1.id)
        self.dc2.freeze_dc_comms()

        #Test edges have a transaction hash
        edge1 = test2.history.get_edges_by_end_node(test2._clockhash)
        self.assertEqual(edge1.transaction_hash,'')

        transaction_test1 = test1.transaction()
        self.assertEqual(transaction_test1.covers, 1)
        transaction_test1.table = 1
        transaction_test1.covers = 2
        self.assertEqual(transaction_test1.covers, 2)
        self.assertEqual(test1.covers, 1)
        self.assertEqual(transaction_test1.table, 1)
        self.assertNotEqual(transaction_test1, test1)
        self.assertNotEqual(transaction_test1, self.dc1.get_object_by_id(Covers.__name__, test1.id))
        transaction_test1.endtransaction()
        self.dc2.unfreeze_dc_comms()
        self.assertEqual(transaction_test1.covers, 2)
        self.assertEqual(transaction_test1.table, 1)
        # The unfrozen version should be normal
        self.assertEqual(test1.covers,2)
        self.assertEqual(test1.table, 1)

        #Test the last edge in the graph is an end transaction edge
        test1_edge1 = test1.history.get_edges_by_end_node(test1._clockhash)
        self.assertTrue(isinstance(test1_edge1, EndTransaction))

        #Test the last three edges in the local copy of the graph have the same hash
        test1_edge2 = test1.history.get_edges_by_end_node(list(test1_edge1._start_hashes)[0])
        test1_edge3 = test1.history.get_edges_by_end_node(list(test1_edge2._start_hashes)[0])
        self.assertNotEqual(test1_edge1.transaction_hash, '')
        self.assertNotEqual(test1_edge2.transaction_hash, '')
        self.assertNotEqual(test1_edge3.transaction_hash, '')
        self.assertEqual(test1_edge1.transaction_hash, test1_edge2.transaction_hash)
        self.assertEqual(test1_edge2.transaction_hash, test1_edge3.transaction_hash)

        #Test the last three edges in the remote copy of the graph have the same hash
        test2_edge1 = test2.history.get_edges_by_end_node(test2._clockhash)
        self.assertTrue(isinstance(test2_edge1, EndTransaction))
        test2_edge2 = test2.history.get_edges_by_end_node(list(test2_edge1._start_hashes)[0])
        test2_edge3 = test2.history.get_edges_by_end_node(list(test2_edge2._start_hashes)[0])
        self.assertNotEqual(test2_edge1.transaction_hash, '')
        self.assertNotEqual(test2_edge2.transaction_hash, '')
        self.assertNotEqual(test2_edge3.transaction_hash, '')
        self.assertEqual(test2_edge1.transaction_hash, test2_edge2.transaction_hash)
        self.assertEqual(test2_edge2.transaction_hash, test2_edge3.transaction_hash)
        self.assertEqual(test2.covers, 2)
        self.assertEqual(test2.table, 1)

        self.assertEqual(test2_edge1.transaction_hash, test1_edge1.transaction_hash)
        self.assertEqual(test2_edge2.transaction_hash, test1_edge2.transaction_hash)
        self.assertEqual(test2_edge3.transaction_hash, test1_edge3.transaction_hash)

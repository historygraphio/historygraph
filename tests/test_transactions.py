from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection, Covers, TestPropertyOwner2, TestPropertyOwner1


class TransactionTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection()
        self.dc1.register(Covers)
        self.dc2 = DocumentCollection(master=self.dc1)
        self.dc2.register(Covers)

    @unittest.skip("Expected failure functionality incompelete")
    def test_frozen_function_basic(self):
        test1 = Covers()
        self.dc1.add_document_object(test1)
        test1.covers = 1
        test2 = self.dc2.get_object_by_id(Covers.__name__, test1.id)
        self.dc2.freeze_dc_comms()

        #Test edges have a transaction hash
        edge1 = test2.history.edgesbyendnode[test2._clockhash]
        self.assertEqual(edge1._transaction_hash,'')

        transaction_test1 = test1.transaction()
        transaction_test1.covers = 2
        transaction_test1.table = 1
        self.assertEqual(transaction_test1.covers, 2)
        self.assertEqual(test1.covers, 1)
        self.assertEqual(testtransaction_test1.table, 1)
        self.assertNotEqual(transaction_test1, test1)
        self.assertNotEqual(transaction_test1, self.dc1.get_object_by_id(Covers.__name__, test1.id))
        transaction_test1.endtransaction()
        self.dc2.unfreeze_dc_comms()
        self.assertEqual(transaction_test1.covers, 2)
        # The unfrozen version should be normal
        self.assertEqual(test1.covers,2)
        self.assertEqual(test1.table, 1)
        self.assertEqual(test2.covers, 2)
        self.assertEqual(test2,table, 1)

        #Test the last two edges in the graph have the same hash
        edge1 = test2.history.edgesbyendnode[test2._clockhash]
        edge2 = test2.history.edgesbyendnode[list(edge1._start_hashes)[0]]
        self.assertEqual(edge1._transaction_hash, edge2._transaction_hash)

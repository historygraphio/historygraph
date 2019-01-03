from __future__ import absolute_import, unicode_literals, print_function

# A collection of tests cover deleting documents and document objects

import unittest
from .common import DocumentCollection, TestPropertyOwner2, TestPropertyOwner1


class TestDeletion(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection()
        self.dc1.register(TestPropertyOwner1)
        self.dc2 = DocumentCollection(master=self.dc1)
        self.dc2.register(TestPropertyOwner1)

    def test_simple_deletion(self):
        test = TestPropertyOwner1()
        self.dc1.add_document_object(test)
        test.covers = 17
        self.assertEqual(test._is_deleted, False)
        test1s = self.dc1.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        self.assertEqual(test.covers, test1s[0].covers)

        self.dc2.freeze_dc_comms()
        test1s = self.dc2.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        self.assertEqual(test.covers, test1s[0].covers)

        test.delete()
        self.assertEqual(test._is_deleted, True)
        test1s = self.dc1.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 0)

        self.dc2.unfreeze_dc_comms()
        test1s = self.dc2.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 0)

    def test_deletion_conflict(self):
        # deletion should lose every conflict
        test = TestPropertyOwner1()
        self.dc1.add_document_object(test)
        test.covers = 17
        self.assertEqual(test._is_deleted, False)
        test1s = self.dc1.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        self.assertEqual(test.covers, test1s[0].covers)

        self.dc2.freeze_dc_comms()
        test1s = self.dc2.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        self.assertEqual(test.covers, test1s[0].covers)

        test1s[0].covers = 18
        self.assertNotEqual(test.covers, test1s[0].covers)

        test.delete()
        self.assertEqual(test._is_deleted, True)
        test1s = self.dc1.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 0)

        self.dc2.unfreeze_dc_comms()
        test1s = self.dc2.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        self.assertEqual(test1s[0].covers, 18)

        test1s = self.dc1.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        self.assertEqual(test1s[0].covers, 18)

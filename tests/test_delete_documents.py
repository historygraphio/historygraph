from __future__ import absolute_import, unicode_literals, print_function

# A collection of tests cover deleting documents and document objects

import unittest
from .common import (DocumentCollection, TestPropertyOwner2,
                     TestPropertyOwner1, TestFieldListOwner2,
                     TestFieldListOwner1)


class TestDeletion(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection()
        self.dc1.register(TestPropertyOwner1)
        self.dc1.register(TestPropertyOwner2)
        self.dc1.register(TestFieldListOwner2)
        self.dc1.register(TestFieldListOwner1)
        self.dc2 = DocumentCollection(master=self.dc1)
        self.dc2.register(TestPropertyOwner1)
        self.dc2.register(TestPropertyOwner2)
        self.dc2.register(TestFieldListOwner2)
        self.dc2.register(TestFieldListOwner1)

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

    def test_deletion_conflict_reverse_order(self):
        # deletion should lose every conflict. This test reverses the comparision
        # above
        test = TestPropertyOwner1()
        self.dc1.add_document_object(test)
        test.covers = 17
        self.assertEqual(test._is_deleted, False)
        test1s = self.dc1.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        self.assertEqual(test.covers, test1s[0].covers)

        self.dc2.freeze_dc_comms()
        test2s = self.dc2.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test2s), 1)
        self.assertEqual(test.covers, test2s[0].covers)

        test.covers = 18
        self.assertNotEqual(test.covers, test2s[0].covers)

        test2s[0].delete()
        self.assertEqual(test2s[0]._is_deleted, True)
        test2s = self.dc2.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test2s), 0)

        self.dc2.unfreeze_dc_comms()
        test1s = self.dc2.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        self.assertEqual(test1s[0].covers, 18)

        test1s = self.dc1.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        self.assertEqual(test1s[0].covers, 18)

    def test_simple_deletion_child_in_collection(self):
        test = TestPropertyOwner1()
        self.dc1.add_document_object(test)
        test.covers = 17
        testitem = TestPropertyOwner2()
        test.propertyowner2s.add(testitem)
        self.dc1.add_document_object(testitem)
        testitem.cover = 1
        self.assertEqual(testitem._is_deleted, False)
        test1s2 = self.dc1.get_by_class(TestPropertyOwner2)
        self.assertEqual(len(test1s2), 1)
        self.assertEqual(testitem.cover, test1s2[0].cover)

        self.dc2.freeze_dc_comms()
        test1s = self.dc2.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        self.assertEqual(len(test1s[0].propertyowner2s), 1)
        for testitem2 in test1s[0].propertyowner2s:
            self.assertEqual(testitem.cover, testitem2.cover)

        testitem.delete()
        self.assertEqual(testitem._is_deleted, True)
        test1 = self.dc1.get_by_class(TestPropertyOwner1)[0]
        self.assertEqual(len(test1.propertyowner2s), 0)

        self.dc2.unfreeze_dc_comms()
        test2 = self.dc2.get_by_class(TestPropertyOwner1)[0]
        self.assertEqual(len(test2.propertyowner2s), 0)


    def test_simple_deletion_child_in_list(self):
        test = TestFieldListOwner1()
        self.dc1.add_document_object(test)
        test.covers = 17
        testitem = TestFieldListOwner2()
        test.propertyowner2s.append(testitem)
        self.dc1.add_document_object(testitem)
        testitem.cover = 1
        self.assertEqual(testitem._is_deleted, False)
        test1s2 = self.dc1.get_by_class(TestFieldListOwner2)
        self.assertEqual(len(test1s2), 1)
        self.assertEqual(testitem.cover, test1s2[0].cover)

        self.dc2.freeze_dc_comms()
        test1s = self.dc2.get_by_class(TestFieldListOwner1)
        self.assertEqual(len(test1s), 1)
        self.assertEqual(len(test1s[0].propertyowner2s), 1)
        for testitem2 in test1s[0].propertyowner2s:
            self.assertEqual(testitem.cover, testitem2.cover)

        testitem.delete()
        self.assertEqual(testitem._is_deleted, True)
        test1 = self.dc1.get_by_class(TestFieldListOwner1)[0]
        self.assertEqual(len(test1.propertyowner2s), 0)

        self.dc2.unfreeze_dc_comms()
        test2 = self.dc2.get_by_class(TestFieldListOwner1)[0]
        self.assertEqual(len(test2.propertyowner2s), 0)


    def test_simple_deletion_parent_in_collection(self):
        test = TestPropertyOwner1()
        self.dc1.add_document_object(test)
        test.covers = 17
        testitem = TestPropertyOwner2()
        test.propertyowner2s.add(testitem)
        self.dc1.add_document_object(testitem)
        testitem.cover = 1
        self.assertEqual(testitem._is_deleted, False)
        test1s2 = self.dc1.get_by_class(TestPropertyOwner2)
        self.assertEqual(len(test1s2), 1)
        self.assertEqual(testitem.cover, test1s2[0].cover)

        self.dc2.freeze_dc_comms()
        test1s = self.dc2.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        self.assertEqual(len(test1s[0].propertyowner2s), 1)
        for testitem2 in test1s[0].propertyowner2s:
            self.assertEqual(testitem.cover, testitem2.cover)

        test.delete()
        self.assertEqual(test._is_deleted, True)
        self.assertEqual(testitem._is_deleted, True)
        test1s = self.dc1.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 0)

        self.dc2.unfreeze_dc_comms()
        test2s = self.dc2.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test2s), 0)

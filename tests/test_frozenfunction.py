from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection, Covers, TestPropertyOwner2, TestPropertyOwner1


class FrozenFunctionTestCase(unittest.TestCase):
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
        
        test1.covers = 2
        test2.covers = 3
        self.assertEqual(test1.covers, 2)
        frozen_test1 = test1.frozen()
        self.assertNotEqual(frozen_test1, test1)
        self.assertNotEqual(frozen_test1, self.dc1.get_object_by_id(Covers.__name__, test1.id))
        self.dc2.unfreeze_dc_comms()
        self.assertEqual(frozen_test1.covers, 2)
        # The unfrozen version should be normal
        self.assertEqual(test1.covers, 3)


class FrozenFunctionCollectionsTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection()
        self.dc1.register(TestPropertyOwner1)
        self.dc1.register(TestPropertyOwner2)
        self.dc2 = DocumentCollection(master=self.dc1)
        self.dc2.register(TestPropertyOwner1)
        self.dc2.register(TestPropertyOwner2)

    def test_replicating_an_object_in_a_collection(self):
        test1 = TestPropertyOwner1()
        self.dc1.add_document_object(test1)
        testitem1 = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem1)
        self.dc1.add_document_object(testitem1)
        testitem1.cover = 1
        self.dc2.freeze_dc_comms()
        testitem1.cover = 3
        test2 = self.dc2.get_object_by_id(TestPropertyOwner1.__name__, test1.id)
        self.assertEqual(len(test2.propertyowner2s), 1)
        for po2 in test2.propertyowner2s:
            self.assertEqual(po2.__class__.__name__ , TestPropertyOwner2.__name__)
            self.assertEqual(po2.cover, 1)

        frozen_test2 = test2.frozen()

        self.assertEqual(len(frozen_test2.propertyowner2s), 1)
        for po2 in frozen_test2.propertyowner2s:
            self.assertEqual(po2.__class__.__name__ , TestPropertyOwner2.__name__)
            self.assertEqual(po2.cover, 1)

        for po2 in test2.propertyowner2s:
            self.assertEqual(po2.__class__.__name__ , TestPropertyOwner2.__name__)
            po2.cover = 2
        self.assertEqual(len(test2.propertyowner2s), 1)
        for po2 in frozen_test2.propertyowner2s:
            self.assertEqual(po2.__class__.__name__ , TestPropertyOwner2.__name__)
            self.assertEqual(po2.cover, 1)

        self.dc2.unfreeze_dc_comms()

        self.assertEqual(len(test2.propertyowner2s), 1)
        for po2 in test2.propertyowner2s:
            self.assertEqual(po2.__class__.__name__ , TestPropertyOwner2.__name__)
            self.assertEqual(po2.cover, 3)

        self.assertEqual(len(frozen_test2.propertyowner2s), 1)
        for po2 in frozen_test2.propertyowner2s:
            self.assertEqual(po2.__class__.__name__ , TestPropertyOwner2.__name__)
            self.assertEqual(po2.cover, 1)


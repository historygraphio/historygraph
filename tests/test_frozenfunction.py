from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection, Covers


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


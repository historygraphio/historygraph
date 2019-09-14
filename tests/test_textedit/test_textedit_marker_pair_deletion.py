from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import Document
from historygraph import fields
from ..common import DocumentCollection, TestFieldTextEditOwner1
import uuid

# Test if a marker pair is deleted. A marker pair is deleted if both
# elements are at the same position

class TextEditDeleteMarkersTest(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(TestFieldTextEditOwner1)

    def test_marker_pair_is_not_deleted(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        self.assertFalse(textowner.text.is_marker_pair_deleted(
                         textowner.text._listfragments[0].id, 2,
                         textowner.text._listfragments[0].id, 4))

    def test_marker_pair_is_deleted_if_text_between_is_not_delete(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.removerange(2, 4)

        self.assertTrue(textowner.text.is_marker_pair_deleted(
                         textowner.text._listfragments[0].id, 2,
                         textowner.text._listfragments[0].id, 4))

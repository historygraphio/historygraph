from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import Document
from historygraph import fields
from ..common import DocumentCollection, TestFieldTextEditOwner1
import uuid

# Test in this file are used to test feature relating to marker deletion
# If the user deletes a fragment of text the markers should go with it

class TextEditDeleteMarkersTest(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(TestFieldTextEditOwner1)

    def test_marker_is_not_deleted(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        self.assertFalse(textowner.text.is_marker_deleted(textowner.text._listfragments[0].id,
                                           3))

    def test_marker_inside_a_fragment_which_is_partially_deleted(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        textowner.text.removerange(2, 4)

        self.assertTrue(textowner.text.is_marker_deleted(textowner.text._listfragments[0].id,
                                           3))

    def test_marker_at_end_of_fragment_is_not_deleted(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        textowner.text.removerange(2, 4)

        self.assertFalse(textowner.text.is_marker_deleted(textowner.text._listfragments[0].id,
                                           2))

    def test_marker_at_start_of_fragment_is_not_deleted(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        textowner.text.removerange(2, 4)

        self.assertFalse(textowner.text.is_marker_deleted(textowner.text._listfragments[0].id,
                                           4))

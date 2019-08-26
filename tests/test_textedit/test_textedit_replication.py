from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import Document
from historygraph import fields
from ..common import DocumentCollection, TestFieldTextEditOwner1
import uuid


class TextEditTestReplication(unittest.TestCase):
    # Test that the textedit works when replicated in simple scenarios
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(TestFieldTextEditOwner1)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(TestFieldTextEditOwner1)

    def test_create_text_with_single_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)

        self.assertEqual(test2.text.get_text(), "abcdef")
        self.assertEqual(len(test2.text._listfragments), 1)
        fragment = test2.text._listfragments[0]
        assert fragment.text == "abcdef"
        assert fragment.relative_to == ""
        assert fragment.relative_start_pos == 0
        assert fragment.internal_start_pos == 0
        assert fragment.has_been_split == False
        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(5) == 0
        assert test2.text.get_fragment_at_index(0) == 0
        assert test2.text.get_fragment_at_index(2) == 0
        assert test2.text.get_fragment_at_index(5) == 0

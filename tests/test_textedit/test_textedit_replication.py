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

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

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

    def test_append_text_to_single_fragment_extends_the_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.insert(6, "ghi")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)
        self.assertEqual(test2.text.get_text(), "abcdefghi")
        self.assertEqual(len(test2.text._listfragments), 1)
        fragment = test2.text._listfragments[0]
        assert fragment.text == "abcdefghi"
        assert fragment.relative_to == ""
        assert fragment.relative_start_pos == 0
        assert fragment.internal_start_pos == 0
        assert fragment.has_been_split == False
        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(5) == 0
        assert test2.text.get_fragment_to_append_to_by_index(7) == 0
        assert test2.text.get_fragment_to_append_to_by_index(9) == 0

    def test_insert_in_middle_of_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdefghi")
        textowner.text.insert(3, "z")
        textowner.text.insert(6, "y")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.assertEqual(test2.text.get_text(), "abczdeyfghi")
        self.assertEqual(len(test2.text._listfragments), 5)
        fragments = test2.text._listfragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].id != fragments[0].id
        assert fragments[1].text == "z"
        assert fragments[1].relative_to == fragments[0].id
        assert fragments[1].relative_start_pos == 3
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 0

        assert fragments[2].id == fragments[0].id
        assert fragments[2].text == "de"
        assert fragments[2].relative_to == ""
        assert fragments[2].relative_start_pos == 0
        assert fragments[2].has_been_split == True
        assert fragments[2].internal_start_pos == 3

        assert fragments[3].id != fragments[0].id
        assert fragments[3].text == "y"
        assert fragments[3].relative_to == fragments[0].id
        assert fragments[3].relative_start_pos == 5
        assert fragments[3].has_been_split == False
        assert fragments[3].internal_start_pos == 0

        assert fragments[4].id == fragments[0].id
        assert fragments[4].text == "fghi"
        assert fragments[4].relative_to == ""
        assert fragments[4].relative_start_pos == 0
        assert fragments[4].has_been_split == False
        assert fragments[4].internal_start_pos == 5

        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(3) == 0
        assert test2.text.get_fragment_to_append_to_by_index(4) == 1
        assert test2.text.get_fragment_to_append_to_by_index(5) == 2
        assert test2.text.get_fragment_to_append_to_by_index(6) == 2
        assert test2.text.get_fragment_to_append_to_by_index(7) == 3
        assert test2.text.get_fragment_to_append_to_by_index(8) == 4
        assert test2.text.get_fragment_to_append_to_by_index(10) == 4

        assert test2.text.get_fragment_at_index(0) == 0
        assert test2.text.get_fragment_at_index(2) == 0
        assert test2.text.get_fragment_at_index(3) == 1
        assert test2.text.get_fragment_at_index(4) == 2
        assert test2.text.get_fragment_at_index(5) == 2
        assert test2.text.get_fragment_at_index(6) == 3
        assert test2.text.get_fragment_at_index(7) == 4
        assert test2.text.get_fragment_at_index(8) == 4
        assert test2.text.get_fragment_at_index(10) == 4
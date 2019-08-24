from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import Document
from historygraph import fields
from ..common import DocumentCollection, TestFieldTextEditOwner1
import uuid

# A TextEdit is a new CRDT similar to a list in some ways but designed for
# storing collaboratively edited text files. The problem it solves is -
# we could implement a text edit as a List of characters but that is
# unduely slow for fairly large files. A test of inserted 100,000 characters
# in such an array took 38 seconds. So for example importing an existing
# source code file. This data is designed to handle these large copy paste type
# edit much more easily.
#
# We are implementing the LogootSplitString algorithm
#
class TextEditTest(unittest.TestCase):
    # Test the basic stand alone functionality of the text edit
    def test_create_text_with_single_fragment(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection(str(uuid.uuid4()))
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        self.assertEqual(textowner.text.get_text(), "abcdef")
        self.assertEqual(len(textowner.text._listfragments), 1)
        fragment = textowner.text._listfragments[0]
        assert fragment.text == "abcdef"
        assert fragment.relative_to == ""
        assert fragment.relative_start_pos == 0
        assert fragment.has_been_split == False
        assert textowner.text.get_fragment_by_index(0) == 0
        assert textowner.text.get_fragment_by_index(2) == 0
        assert textowner.text.get_fragment_by_index(5) == 0

    def test_append_text_to_single_fragment_extends_the_fragment(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection(str(uuid.uuid4()))
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.insert(6, "ghi")

        self.assertEqual(textowner.text.get_text(), "abcdefghi")
        self.assertEqual(len(textowner.text._listfragments), 1)
        fragment = textowner.text._listfragments[0]
        assert fragment.text == "abcdefghi"
        assert fragment.relative_to == ""
        assert fragment.relative_start_pos == 0
        assert fragment.has_been_split == False
        assert textowner.text.get_fragment_by_index(0) == 0
        assert textowner.text.get_fragment_by_index(2) == 0
        assert textowner.text.get_fragment_by_index(5) == 0
        assert textowner.text.get_fragment_by_index(7) == 0
        assert textowner.text.get_fragment_by_index(9) == 0

    def test_insert_in_middle_of_fragment(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection(str(uuid.uuid4()))
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.insert(3, "z")

        self.assertEqual(textowner.text.get_text(), "abczdef")
        self.assertEqual(len(textowner.text._listfragments), 3)
        fragments = textowner.text._listfragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True

        assert fragments[1].text == "z"
        assert fragments[1].relative_to == fragments[0].id
        assert fragments[1].relative_start_pos == 3
        assert fragments[1].has_been_split == False

        assert fragments[2].text == "def"
        assert fragments[2].relative_to == ""
        assert fragments[2].relative_start_pos == 0
        assert fragments[2].has_been_split == False

        assert textowner.text.get_fragment_by_index(0) == 0
        assert textowner.text.get_fragment_by_index(2) == 0
        assert textowner.text.get_fragment_by_index(4) == 1
        assert textowner.text.get_fragment_by_index(5) == 2
        assert textowner.text.get_fragment_by_index(7) == 2

    def test_insert_at_start_of_fragment(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection(str(uuid.uuid4()))
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.insert(0, "z")

        self.assertEqual(textowner.text.get_text(), "zabcdef")
        self.assertEqual(len(textowner.text._listfragments), 2)
        fragments = textowner.text._listfragments

        assert fragments[0].text == "z"
        assert fragments[0].relative_to == fragments[0].id
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == False

        assert fragments[1].text == "abcdef"
        assert fragments[1].relative_to == ""
        assert fragments[1].relative_start_pos == 0
        assert fragments[1].has_been_split == False

        assert textowner.text.get_fragment_by_index(0) == 0
        assert textowner.text.get_fragment_by_index(1) == 0
        assert textowner.text.get_fragment_by_index(2) == 1
        assert textowner.text.get_fragment_by_index(5) == 1
        assert textowner.text.get_fragment_by_index(7) == 1

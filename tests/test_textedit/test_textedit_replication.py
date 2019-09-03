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

    def test_insert_at_start_of_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.insert(0, "z")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.assertEqual(test2.text.get_text(), "zabcdef")
        self.assertEqual(len(test2.text._listfragments), 2)
        fragments = test2.text._listfragments

        assert fragments[0].text == "z"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == False
        assert fragments[0].internal_start_pos == 0
        assert fragments[0].before_frag_id == fragments[1].id
        assert fragments[0].before_frag_start_pos == 0

        assert fragments[0].id != fragments[1].id
        assert fragments[1].text == "abcdef"
        assert fragments[1].relative_to == ""
        assert fragments[1].relative_start_pos == 0
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 0

        assert textowner.text.get_fragment_to_append_to_by_index(0) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(1) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(2) == 1
        assert textowner.text.get_fragment_to_append_to_by_index(5) == 1
        assert textowner.text.get_fragment_to_append_to_by_index(7) == 1

        assert textowner.text.get_fragment_at_index(0) == 0
        assert textowner.text.get_fragment_at_index(1) == 1
        assert textowner.text.get_fragment_at_index(2) == 1
        assert textowner.text.get_fragment_at_index(3) == 1
        assert textowner.text.get_fragment_at_index(5) == 1
        assert textowner.text.get_fragment_at_index(6) == 1

    def test_delete_text_from_single_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.removerange(3,4)

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.assertEqual(test2.text.get_text(), "abcef")
        self.assertEqual(len(test2.text._listfragments), 2)
        fragments = test2.text._listfragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].text == "ef"
        assert fragments[1].relative_to == ""
        assert fragments[1].relative_start_pos == 0
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 4

        assert textowner.text.get_fragment_to_append_to_by_index(0) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(2) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(3) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(4) == 1

        assert textowner.text.get_fragment_at_index(0) == 0
        assert textowner.text.get_fragment_at_index(2) == 0
        assert textowner.text.get_fragment_at_index(1) == 0
        assert textowner.text.get_fragment_at_index(4) == 1

        # Delete a seoncd fragment
        textowner.text.removerange(3,4)

        self.assertEqual(test2.text.get_text(), "abcf")
        self.assertEqual(len(test2.text._listfragments), 2)
        fragments = test2.text._listfragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].text == "f"
        assert fragments[1].relative_to == ""
        assert fragments[1].relative_start_pos == 0
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 5

        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(3) == 0
        assert test2.text.get_fragment_to_append_to_by_index(4) == 1

        assert test2.text.get_fragment_at_index(0) == 0
        assert test2.text.get_fragment_at_index(2) == 0
        assert test2.text.get_fragment_at_index(1) == 0
        assert test2.text.get_fragment_at_index(3) == 1

    def test_delete_text_from_single_fragment_alt_pattern(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.removerange(3,4)

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.assertEqual(test2.text.get_text(), "abcef")
        self.assertEqual(len(test2.text._listfragments), 2)
        fragment = test2.text._listfragments[0]
        fragments = test2.text._listfragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].text == "ef"
        assert fragments[1].relative_to == ""
        assert fragments[1].relative_start_pos == 0
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 4

        assert textowner.text.get_fragment_to_append_to_by_index(0) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(2) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(3) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(4) == 1

        assert textowner.text.get_fragment_at_index(0) == 0
        assert textowner.text.get_fragment_at_index(2) == 0
        assert textowner.text.get_fragment_at_index(1) == 0
        assert textowner.text.get_fragment_at_index(4) == 1

        # Delete a second fragment this time from the end of the first
        textowner.text.removerange(2,3)

        self.assertEqual(test2.text.get_text(), "abef")
        self.assertEqual(len(test2.text._listfragments), 2)
        fragment = textowner.text._listfragments[0]
        fragments = textowner.text._listfragments

        assert fragments[0].text == "ab"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].text == "ef"
        assert fragments[1].relative_to == ""
        assert fragments[1].relative_start_pos == 0
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 4

        assert textowner.text.get_fragment_to_append_to_by_index(0) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(2) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(3) == 1
        assert textowner.text.get_fragment_to_append_to_by_index(4) == 1

        assert textowner.text.get_fragment_at_index(0) == 0
        assert textowner.text.get_fragment_at_index(1) == 0
        assert textowner.text.get_fragment_at_index(2) == 1
        assert textowner.text.get_fragment_at_index(3) == 1

    def test_delete_text_from_start_of_single_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.removerange(0,1)

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.assertEqual(test2.text.get_text(), "bcdef")
        self.assertEqual(len(test2.text._listfragments), 1)
        fragments = test2.text._listfragments

        assert fragments[0].text == "bcdef"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == False
        assert fragments[0].internal_start_pos == 1

        assert textowner.text.get_fragment_to_append_to_by_index(0) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(2) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(3) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(4) == 0

        assert textowner.text.get_fragment_at_index(0) == 0
        assert textowner.text.get_fragment_at_index(2) == 0
        assert textowner.text.get_fragment_at_index(1) == 0
        assert textowner.text.get_fragment_at_index(4) == 0

        # Delete another bit from the fragment
        textowner.text.removerange(0,1)

        self.assertEqual(test2.text.get_text(), "cdef")
        self.assertEqual(len(test2.text._listfragments), 1)
        fragments = test2.text._listfragments

        assert fragments[0].text == "cdef"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == False
        assert fragments[0].internal_start_pos == 2

        assert textowner.text.get_fragment_to_append_to_by_index(0) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(2) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(3) == 0

        assert textowner.text.get_fragment_at_index(0) == 0
        assert textowner.text.get_fragment_at_index(2) == 0
        assert textowner.text.get_fragment_at_index(1) == 0

    def test_whole_delete_whole_fragment_from_middle(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.insert(3, "yz")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.assertEqual(test2.text.get_text(), "abcyzdef")
        self.assertEqual(len(test2.text._listfragments), 3)
        fragments = test2.text._listfragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].id != fragments[0].id
        assert fragments[1].text == "yz"
        assert fragments[1].relative_to == fragments[0].id
        assert fragments[1].relative_start_pos == 3
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 0

        assert fragments[2].id == fragments[0].id
        assert fragments[2].text == "def"
        assert fragments[2].relative_to == ""
        assert fragments[2].relative_start_pos == 0
        assert fragments[2].has_been_split == False
        assert fragments[2].internal_start_pos == 3

        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(3) == 0
        assert test2.text.get_fragment_to_append_to_by_index(4) == 1
        assert test2.text.get_fragment_to_append_to_by_index(5) == 1
        assert test2.text.get_fragment_to_append_to_by_index(6) == 2
        assert test2.text.get_fragment_to_append_to_by_index(8) == 2

        assert test2.text.get_fragment_at_index(0) == 0
        assert test2.text.get_fragment_at_index(2) == 0
        assert test2.text.get_fragment_at_index(3) == 1
        assert test2.text.get_fragment_at_index(4) == 1
        assert test2.text.get_fragment_at_index(5) == 2
        assert test2.text.get_fragment_at_index(6) == 2
        assert test2.text.get_fragment_at_index(7) == 2

        textowner.text.removerange(3, 5)
        self.assertEqual(test2.text.get_text(), "abcdef")
        self.assertEqual(len(test2.text._listfragments), 3)
        fragments = test2.text._listfragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].id != fragments[0].id
        assert fragments[1].text == ""
        assert fragments[1].relative_to == fragments[0].id
        assert fragments[1].relative_start_pos == 3
        assert fragments[1].has_been_split == True
        assert fragments[1].internal_start_pos == 0

        assert fragments[2].id == fragments[0].id
        assert fragments[2].text == "def"
        assert fragments[2].relative_to == ""
        assert fragments[2].relative_start_pos == 0
        assert fragments[2].has_been_split == False
        assert fragments[2].internal_start_pos == 3

        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(3) == 0
        assert test2.text.get_fragment_to_append_to_by_index(4) == 2
        assert test2.text.get_fragment_to_append_to_by_index(6) == 2

        assert test2.text.get_fragment_at_index(0) == 0
        assert test2.text.get_fragment_at_index(2) == 0
        assert test2.text.get_fragment_at_index(3) == 2
        assert test2.text.get_fragment_at_index(4) == 2
        assert test2.text.get_fragment_at_index(5) == 2

    def test_delete_whole_fragment_plus_more_from_middle(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.insert(3, "yz")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.assertEqual(test2.text.get_text(), "abcyzdef")
        self.assertEqual(len(test2.text._listfragments), 3)
        fragments = test2.text._listfragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].id != fragments[0].id
        assert fragments[1].text == "yz"
        assert fragments[1].relative_to == fragments[0].id
        assert fragments[1].relative_start_pos == 3
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 0

        assert fragments[2].id == fragments[0].id
        assert fragments[2].text == "def"
        assert fragments[2].relative_to == ""
        assert fragments[2].relative_start_pos == 0
        assert fragments[2].has_been_split == False
        assert fragments[2].internal_start_pos == 3

        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(3) == 0
        assert test2.text.get_fragment_to_append_to_by_index(4) == 1
        assert test2.text.get_fragment_to_append_to_by_index(5) == 1
        assert test2.text.get_fragment_to_append_to_by_index(6) == 2
        assert test2.text.get_fragment_to_append_to_by_index(8) == 2

        assert test2.text.get_fragment_at_index(0) == 0
        assert test2.text.get_fragment_at_index(2) == 0
        assert test2.text.get_fragment_at_index(3) == 1
        assert test2.text.get_fragment_at_index(4) == 1
        assert test2.text.get_fragment_at_index(5) == 2
        assert test2.text.get_fragment_at_index(6) == 2
        assert test2.text.get_fragment_at_index(7) == 2

        textowner.text.removerange(2, 6)
        self.assertEqual(test2.text.get_text(), "abef")
        self.assertEqual(len(test2.text._listfragments), 3)
        fragments = test2.text._listfragments

        assert fragments[0].text == "ab"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].id != fragments[0].id
        assert fragments[1].text == ""
        assert fragments[1].relative_to == fragments[0].id
        assert fragments[1].relative_start_pos == 3
        assert fragments[1].has_been_split == True
        assert fragments[1].internal_start_pos == 0

        assert fragments[2].id == fragments[0].id
        assert fragments[2].text == "ef"
        assert fragments[2].relative_to == ""
        assert fragments[2].relative_start_pos == 0
        assert fragments[2].has_been_split == False
        assert fragments[2].internal_start_pos == 4

        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(3) == 2
        assert test2.text.get_fragment_to_append_to_by_index(4) == 2

        assert test2.text.get_fragment_at_index(0) == 0
        assert test2.text.get_fragment_at_index(1) == 0
        assert test2.text.get_fragment_at_index(2) == 2
        assert test2.text.get_fragment_at_index(3) == 2

    def test_delete_at_end_of_single_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.removerange(4, 6)

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.assertEqual(test2.text.get_text(), "abcd")
        self.assertEqual(len(test2.text._listfragments), 1)
        fragment = test2.text._listfragments[0]
        assert fragment.text == "abcd"
        assert fragment.relative_to == ""
        assert fragment.relative_start_pos == 0
        assert fragment.internal_start_pos == 0
        assert fragment.has_been_split == True
        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(3) == 0
        assert test2.text.get_fragment_at_index(0) == 0
        assert test2.text.get_fragment_at_index(2) == 0
        assert test2.text.get_fragment_at_index(3) == 0

    def test_append_to_broken_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.insert(3, "z")
        textowner.text.insert(7, "ghi")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.assertEqual(test2.text.get_text(), "abczdefghi")
        self.assertEqual(len(test2.text._listfragments), 3)
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
        assert fragments[2].text == "defghi"
        assert fragments[2].relative_to == ""
        assert fragments[2].relative_start_pos == 0
        assert fragments[2].has_been_split == False
        assert fragments[2].internal_start_pos == 3

        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(3) == 0
        assert test2.text.get_fragment_to_append_to_by_index(4) == 1
        assert test2.text.get_fragment_to_append_to_by_index(5) == 2
        assert test2.text.get_fragment_to_append_to_by_index(7) == 2
        assert test2.text.get_fragment_to_append_to_by_index(10) == 2

        assert test2.text.get_fragment_at_index(0) == 0
        assert test2.text.get_fragment_at_index(2) == 0
        assert test2.text.get_fragment_at_index(3) == 1
        assert test2.text.get_fragment_at_index(4) == 2
        assert test2.text.get_fragment_at_index(5) == 2
        assert test2.text.get_fragment_at_index(6) == 2
        assert test2.text.get_fragment_at_index(9) == 2

    def test_append_to_broken_fragment_caused_by_deletion(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.removerange(3,4)
        textowner.text.insert(5, "ghi")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.assertEqual(test2.text.get_text(), "abcefghi")
        self.assertEqual(len(test2.text._listfragments), 2)
        fragments = test2.text._listfragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].text == "efghi"
        assert fragments[1].relative_to == ""
        assert fragments[1].relative_start_pos == 0
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 4

        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(3) == 0
        assert test2.text.get_fragment_to_append_to_by_index(4) == 1

        assert test2.text.get_fragment_at_index(0) == 0
        assert test2.text.get_fragment_at_index(2) == 0
        assert test2.text.get_fragment_at_index(1) == 0
        assert test2.text.get_fragment_at_index(4) == 1

    def test_do_not_append_to_the_end_of_a_fragment_created_by_another_session(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        test2.text.insert(6, "ghi")

        self.assertEqual(textowner.text.get_text(), "abcdefghi")
        self.assertEqual(len(textowner.text._listfragments), 2)
        fragments = textowner.text._listfragments

        assert fragments[0].text == "abcdef"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == False
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].text == "ghi"
        assert fragments[1].relative_to == fragments[0].id
        assert fragments[1].relative_start_pos == 6
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 0

        assert textowner.text.get_fragment_to_append_to_by_index(0) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(2) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(5) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(6) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(8) == 1
        assert textowner.text.get_fragment_to_append_to_by_index(9) == 1

        assert textowner.text.get_fragment_at_index(0) == 0
        assert textowner.text.get_fragment_at_index(1) == 0
        assert textowner.text.get_fragment_at_index(2) == 0
        assert textowner.text.get_fragment_at_index(5) == 0
        assert textowner.text.get_fragment_at_index(7) == 1
        assert textowner.text.get_fragment_at_index(8) == 1

        self.assertEqual(test2.text.get_text(), "abcdefghi")
        self.assertEqual(len(test2.text._listfragments), 2)
        fragments = test2.text._listfragments

        assert fragments[0].text == "abcdef"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == False
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].text == "ghi"
        assert fragments[1].relative_to == fragments[0].id
        assert fragments[1].relative_start_pos == 6
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 0

        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(5) == 0
        assert test2.text.get_fragment_to_append_to_by_index(6) == 0
        assert test2.text.get_fragment_to_append_to_by_index(8) == 1
        assert test2.text.get_fragment_to_append_to_by_index(9) == 1

        assert test2.text.get_fragment_at_index(0) == 0
        assert test2.text.get_fragment_at_index(1) == 0
        assert test2.text.get_fragment_at_index(2) == 0
        assert test2.text.get_fragment_at_index(5) == 0
        assert test2.text.get_fragment_at_index(7) == 1
        assert test2.text.get_fragment_at_index(8) == 1

    def test_append_multi_fragments_before(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcd")
        textowner.text.removerange(3,4)

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.dc2.freeze_dc_comms()

        textowner.text.insert(3, "ghi")

        textowner.text.insert(3, "xyz")

        self.dc2.unfreeze_dc_comms()

        self.assertEqual(textowner.text.get_text(), "abcxyzghi")
        self.assertEqual(test2.text.get_text(), "abcxyzghi")

        self.assertEqual(len(textowner.text._listfragments), 3)
        self.assertEqual(len(test2.text._listfragments), 3)

        fragments = textowner.text._listfragments
        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0
        assert fragments[0].before_frag_id == ""
        assert fragments[0].before_frag_start_pos == 0

        assert fragments[1].text == "xyz"
        assert fragments[1].relative_to == fragments[0].id
        assert fragments[1].relative_start_pos == 3
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 0
        assert fragments[1].before_frag_id == fragments[2].id, \
            "fragments[1].before_frag_id={} fragments[2].id={}".format(fragments[1].before_frag_id, fragments[2].id)
        assert fragments[1].before_frag_start_pos == 0

        assert fragments[2].text == "ghi"
        assert fragments[2].relative_to == fragments[0].id
        assert fragments[2].relative_start_pos == 3
        assert fragments[2].has_been_split == False
        assert fragments[2].internal_start_pos == 0
        assert fragments[2].before_frag_id == ""
        assert fragments[2].before_frag_start_pos == 0

        assert textowner.text.get_fragment_to_append_to_by_index(0) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(2) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(3) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(4) == 1
        assert textowner.text.get_fragment_to_append_to_by_index(6) == 1
        assert textowner.text.get_fragment_to_append_to_by_index(7) == 2
        assert textowner.text.get_fragment_to_append_to_by_index(8) == 2
        assert textowner.text.get_fragment_to_append_to_by_index(9) == 2

        assert textowner.text.get_fragment_at_index(0) == 0
        assert textowner.text.get_fragment_at_index(1) == 0
        assert textowner.text.get_fragment_at_index(2) == 0
        assert textowner.text.get_fragment_at_index(3) == 1
        assert textowner.text.get_fragment_at_index(5) == 1
        assert textowner.text.get_fragment_at_index(6) == 2
        assert textowner.text.get_fragment_at_index(8) == 2

        fragments = test2.text._listfragments
        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0
        assert fragments[0].before_frag_id == ""
        assert fragments[0].before_frag_start_pos == 0

        assert fragments[1].text == "xyz"
        assert fragments[1].relative_to == fragments[0].id
        assert fragments[1].relative_start_pos == 3
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 0
        assert fragments[1].before_frag_id == fragments[2].id, \
            "fragments[1].before_frag_id={} fragments[2].id={}".format(fragments[1].before_frag_id, fragments[2].id)
        assert fragments[1].before_frag_start_pos == 0

        assert fragments[2].text == "ghi"
        assert fragments[2].relative_to == fragments[0].id
        assert fragments[2].relative_start_pos == 3
        assert fragments[2].has_been_split == False
        assert fragments[2].internal_start_pos == 0
        assert fragments[2].before_frag_id == ""
        assert fragments[2].before_frag_start_pos == 0

        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(3) == 0
        assert test2.text.get_fragment_to_append_to_by_index(4) == 1
        assert test2.text.get_fragment_to_append_to_by_index(6) == 1
        assert test2.text.get_fragment_to_append_to_by_index(7) == 2
        assert test2.text.get_fragment_to_append_to_by_index(8) == 2
        assert test2.text.get_fragment_to_append_to_by_index(9) == 2

        assert test2.text.get_fragment_at_index(0) == 0
        assert test2.text.get_fragment_at_index(1) == 0
        assert test2.text.get_fragment_at_index(2) == 0
        assert test2.text.get_fragment_at_index(3) == 1
        assert test2.text.get_fragment_at_index(5) == 1
        assert test2.text.get_fragment_at_index(6) == 2
        assert test2.text.get_fragment_at_index(8) == 2

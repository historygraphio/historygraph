from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import Document
from historygraph import fields
from ..common import DocumentCollection, TestFieldTextEditOwner1
import uuid


class TextEditTestReplication(unittest.TestCase):
    # Test that the textedit works when replicated in complex scenarios
    # where there are conflicting updates
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(TestFieldTextEditOwner1)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(TestFieldTextEditOwner1)

    def test_append_multi_conflicting_fragments(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcd")
        textowner.text.removerange(3,4)

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.dc2.freeze_dc_comms()

        textowner.text.insert(3, "def")

        test2.text.insert(3, "xyz")

        self.dc2.unfreeze_dc_comms()

        self.assertTrue(test2.text.get_text() == "abcdefxyz" or
                        test2.text.get_text() == "abcxyzdef")

        self.assertEqual(textowner.text.get_text(), test2.text.get_text())

        self.assertEqual(len(textowner.text._listfragments), 3)
        self.assertEqual(len(test2.text._listfragments), 3)

    def test_insert_multi_conflicting_fragments(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.dc2.freeze_dc_comms()

        textowner.text.insert(3, "ghi")

        test2.text.insert(3, "xyz")

        self.dc2.unfreeze_dc_comms()

        self.assertTrue(test2.text.get_text() == "abcghixyzdef" or
                        test2.text.get_text() == "abcxyzghidef")

        self.assertEqual(textowner.text.get_text(), test2.text.get_text())

        self.assertEqual(len(textowner.text._listfragments), 4)
        self.assertEqual(len(test2.text._listfragments), 4)

    def test_delete_text_from_single_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdefghi")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.dc2.freeze_dc_comms()
        textowner.text.removerange(3,6)
        test2.text.removerange(3,6)
        self.dc2.unfreeze_dc_comms()

        self.assertEqual(textowner.text.get_text(), "abcghi")
        self.assertEqual(len(textowner.text._listfragments), 2)
        fragments = textowner.text._listfragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].text == "ghi"
        assert fragments[1].relative_to == ""
        assert fragments[1].relative_start_pos == 0
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 6

        assert textowner.text.get_fragment_to_append_to_by_index(0) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(2) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(5) == 1
        assert textowner.text.get_fragment_to_append_to_by_index(6) == 1

        assert textowner.text.get_fragment_at_index(0) == 0
        assert textowner.text.get_fragment_at_index(1) == 0
        assert textowner.text.get_fragment_at_index(2) == 0
        assert textowner.text.get_fragment_at_index(3) == 1
        assert textowner.text.get_fragment_at_index(4) == 1
        assert textowner.text.get_fragment_at_index(5) == 1

    def test_delete_text_non_identical_operations_from_single_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdefghi")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.dc2.freeze_dc_comms()
        textowner.text.removerange(3,5)
        test2.text.removerange(4,6)
        self.dc2.unfreeze_dc_comms()

        self.assertEqual(textowner.text.get_text(), "abcghi")
        self.assertEqual(len(textowner.text._listfragments), 2)
        fragments = textowner.text._listfragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].text == "ghi"
        assert fragments[1].relative_to == ""
        assert fragments[1].relative_start_pos == 0
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 6

        assert textowner.text.get_fragment_to_append_to_by_index(0) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(2) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(5) == 1
        assert textowner.text.get_fragment_to_append_to_by_index(6) == 1

        assert textowner.text.get_fragment_at_index(0) == 0
        assert textowner.text.get_fragment_at_index(1) == 0
        assert textowner.text.get_fragment_at_index(2) == 0
        assert textowner.text.get_fragment_at_index(3) == 1
        assert textowner.text.get_fragment_at_index(4) == 1
        assert textowner.text.get_fragment_at_index(5) == 1

    def test_inserts_at_start_of_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.dc2.freeze_dc_comms()
        textowner.text.insert(0, "z")
        test2.text.insert(0, "y")

        self.dc2.unfreeze_dc_comms()

        self.assertTrue(textowner.text.get_text() == "zyabcdef" or
                        textowner.text.get_text() == "yzabcdef")
        self.assertEqual(textowner.text.get_text(), test2.text.get_text())
        self.assertEqual(len(textowner.text._listfragments), 3)

    def test_delete_text_conflicts_with_insert_from_single_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdefghi")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.dc2.freeze_dc_comms()
        textowner.text.removerange(3,6)
        test2.text.insert(4,"xyz")
        self.dc2.unfreeze_dc_comms()

        self.assertEqual(textowner.text.get_text(), "abcxyzghi")
        self.assertEqual(len(textowner.text._listfragments), 3)
        fragments = textowner.text._listfragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].text == "xyz"
        assert fragments[1].relative_to == fragments[0].id
        assert fragments[1].relative_start_pos == 4
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 0

        assert fragments[2].text == "ghi"
        assert fragments[2].relative_to == ""
        assert fragments[2].relative_start_pos == 0
        assert fragments[2].has_been_split == False
        assert fragments[2].internal_start_pos == 6

        assert textowner.text.get_fragment_to_append_to_by_index(0) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(2) == 0
        assert textowner.text.get_fragment_to_append_to_by_index(5) == 1
        assert textowner.text.get_fragment_to_append_to_by_index(6) == 1
        assert textowner.text.get_fragment_to_append_to_by_index(7) == 2
        assert textowner.text.get_fragment_to_append_to_by_index(9) == 2

        assert textowner.text.get_fragment_at_index(0) == 0
        assert textowner.text.get_fragment_at_index(1) == 0
        assert textowner.text.get_fragment_at_index(2) == 0
        assert textowner.text.get_fragment_at_index(3) == 1
        assert textowner.text.get_fragment_at_index(4) == 1
        assert textowner.text.get_fragment_at_index(5) == 1
        assert textowner.text.get_fragment_at_index(6) == 2
        assert textowner.text.get_fragment_at_index(8) == 2

        self.assertEqual(test2.text.get_text(), "abcxyzghi")
        self.assertEqual(len(test2.text._listfragments), 3)
        fragments = test2.text._listfragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].text == "xyz"
        assert fragments[1].relative_to == fragments[0].id
        assert fragments[1].relative_start_pos == 4
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 0

        assert fragments[2].text == "ghi"
        assert fragments[2].relative_to == ""
        assert fragments[2].relative_start_pos == 0
        assert fragments[2].has_been_split == False
        assert fragments[2].internal_start_pos == 6

        assert test2.text.get_fragment_to_append_to_by_index(0) == 0
        assert test2.text.get_fragment_to_append_to_by_index(2) == 0
        assert test2.text.get_fragment_to_append_to_by_index(5) == 1
        assert test2.text.get_fragment_to_append_to_by_index(6) == 1
        assert test2.text.get_fragment_to_append_to_by_index(7) == 2
        assert test2.text.get_fragment_to_append_to_by_index(9) == 2

        assert test2.text.get_fragment_at_index(0) == 0
        assert test2.text.get_fragment_at_index(1) == 0
        assert test2.text.get_fragment_at_index(2) == 0
        assert test2.text.get_fragment_at_index(3) == 1
        assert test2.text.get_fragment_at_index(4) == 1
        assert test2.text.get_fragment_at_index(5) == 1
        assert test2.text.get_fragment_at_index(6) == 2
        assert test2.text.get_fragment_at_index(8) == 2

    def test_deleting_entire_fragment_conflicts_with_insert_from_single_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        # Make a text string of three fragments
        textowner.text.insert(0, "abcghi")
        textowner.text.insert(3, "def")
        self.assertEqual(textowner.text.get_text(), "abcdefghi")
        self.assertEqual(len(textowner.text._listfragments), 3)

        deleted_middle_fragment = textowner.text._listfragments[1]

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.dc2.freeze_dc_comms()
        textowner.text.removerange(3,6)
        test2.text.insert(5,"xyz")
        self.dc2.unfreeze_dc_comms()

        self.assertEqual(textowner.text.get_text(), "abcxyzghi")
        non_deleted_list_fragments = [f for f in textowner.text._listfragments if f.text != ""]
        deleted_list_fragments = [f for f in textowner.text._listfragments if f.id == deleted_middle_fragment.id]
        # There can be either one or two fragments because of the ordering of events
        self.assertTrue(len(deleted_list_fragments) == 1 or len(deleted_list_fragments) == 2)
        # Check they really were deleted
        self.assertTrue(all([f.text == "" for f in deleted_list_fragments]))
        self.assertEqual(len(non_deleted_list_fragments), 3)
        fragments = non_deleted_list_fragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].text == "xyz"
        assert fragments[1].relative_to == deleted_middle_fragment.id
        assert fragments[1].relative_start_pos == 2
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 0

        assert fragments[2].text == "ghi"
        assert fragments[2].relative_to == ""
        assert fragments[2].relative_start_pos == 0
        assert fragments[2].has_been_split == False
        assert fragments[2].internal_start_pos == 3

        self.assertEqual(test2.text.get_text(), "abcxyzghi")
        non_deleted_list_fragments = [f for f in textowner.text._listfragments if f.text != ""]
        deleted_list_fragments = [f for f in textowner.text._listfragments if f.id == deleted_middle_fragment.id]
        # There can be either one or two fragments because of the ordering of events
        self.assertTrue(len(deleted_list_fragments) == 1 or len(deleted_list_fragments) == 2)
        # Check they really were deleted
        self.assertTrue(all([f.text == "" for f in deleted_list_fragments]))
        self.assertEqual(len(non_deleted_list_fragments), 3)
        fragments = non_deleted_list_fragments

        assert fragments[0].text == "abc"
        assert fragments[0].relative_to == ""
        assert fragments[0].relative_start_pos == 0
        assert fragments[0].has_been_split == True
        assert fragments[0].internal_start_pos == 0

        assert fragments[1].text == "xyz"
        assert fragments[1].relative_to == deleted_middle_fragment.id
        assert fragments[1].relative_start_pos == 2
        assert fragments[1].has_been_split == False
        assert fragments[1].internal_start_pos == 0

        assert fragments[2].text == "ghi"
        assert fragments[2].relative_to == ""
        assert fragments[2].relative_start_pos == 0
        assert fragments[2].has_been_split == False
        assert fragments[2].internal_start_pos == 3

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
        print("test_append_multi_conflicting_fragments self.dc1.id=", self.dc1.id)
        print("test_append_multi_conflicting_fragments self.dc2.id=", self.dc2.id)
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcd")
        textowner.text.removerange(3,4)

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__,
                                          textowner.id)

        self.dc2.freeze_dc_comms()

        textowner.text.insert(3, "def")

        textowner.text.insert(3, "xyz")

        self.dc2.unfreeze_dc_comms()

        self.assertTrue(test2.text.get_text() == "abcdefxyz" or
                        test2.text.get_text() == "abcxyzdef")

        print("test_append_multi_conflicting_fragments textowner.text=", [f.text for f in textowner.text._listfragments])
        print("test_append_multi_conflicting_fragments textowner.text=", [f.id for f in textowner.text._listfragments])
        print("test_append_multi_conflicting_fragments test2.text=", [f.text for f in test2.text._listfragments])
        print("test_append_multi_conflicting_fragments test2.text=", [f.id for f in test2.text._listfragments])
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

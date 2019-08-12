from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import Document
from historygraph import fields
from ..common import DocumentCollection, TestFieldTextEditOwner1


class TextEditTestReplication(unittest.TestCase):
    # Test that the textedit works when replicated in simple scenarios
    def setUp(self):
        self.dc1 = DocumentCollection()
        self.dc1.register(TestFieldTextEditOwner1)
        self.dc2 = DocumentCollection(master=self.dc1)
        self.dc2.register(TestFieldTextEditOwner1)

    def test_create_two_conflicting_fragments(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)
        test2.text.render()
        self.dc2.freeze_dc_comms()
        textowner.text.insert(3, "ghi")
        test2.text.insert(3, "def")
        self.dc2.unfreeze_dc_comms()

        test2.text.render()

        self.assertTrue(test2.text.get_text() == "abcdefghi" or test2.text.get_text() == "abcghidef")
        self.assertEqual(test2.text.get_text(), textowner.text.get_text())

        if test2.text.get_text() == "abcdefghi":
            self.assertEqual(len(test2.text._rendered_list), 3)
            self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
            self.assertEqual(test2.text._rendered_list[0].data, "abc")
            self.assertEqual(test2.text._rendered_list[1].starts_at, 3)
            self.assertEqual(test2.text._rendered_list[1].data, "def")
            self.assertEqual(test2.text._rendered_list[2].starts_at, 6)
            self.assertEqual(test2.text._rendered_list[2].data, "ghi")
        if test2.text.get_text() == "abcghidef":
            self.assertEqual(len(test2.text._rendered_list), 3)
            self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
            self.assertEqual(test2.text._rendered_list[0].data, "abc")
            self.assertEqual(test2.text._rendered_list[1].starts_at, 3)
            self.assertEqual(test2.text._rendered_list[1].data, "ghi")
            self.assertEqual(test2.text._rendered_list[2].starts_at, 6)
            self.assertEqual(test2.text._rendered_list[2].data, "def")

        self.assertEqual(test2.text._rendered_list[0],
                         test2.text.get_fragment_by_index(0)[0])
        self.assertEqual(test2.text._rendered_list[0],
                         test2.text.get_fragment_by_index(2)[0])
        self.assertEqual(test2.text._rendered_list[1],
                         test2.text.get_fragment_by_index(3)[0])
        self.assertEqual(test2.text._rendered_list[1],
                         test2.text.get_fragment_by_index(5)[0])
        self.assertEqual(test2.text._rendered_list[2],
                         test2.text.get_fragment_by_index(6)[0])
        self.assertEqual(test2.text._rendered_list[2],
                         test2.text.get_fragment_by_index(8)[0])
        self.assertEqual(0, test2.text.get_fragment_by_index(0)[1])
        self.assertEqual(0, test2.text.get_fragment_by_index(2)[1])
        self.assertEqual(1, test2.text.get_fragment_by_index(3)[1])
        self.assertEqual(1, test2.text.get_fragment_by_index(5)[1])
        self.assertEqual(2, test2.text.get_fragment_by_index(6)[1])
        self.assertEqual(2, test2.text.get_fragment_by_index(8)[1])

    def test_two_identical_conflicting_deletions(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdefghi")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)
        test2.text.render()
        self.dc2.freeze_dc_comms()
        textowner.text.removerange(3, 6)
        test2.text.removerange(3, 6)
        self.dc2.unfreeze_dc_comms()

        test2.text.render()

        self.assertEqual(test2.text.get_text(), "abcghi")
        self.assertEqual(textowner.text.get_text(), "abcghi")

        self.assertEqual(len(test2.text._rendered_list), 2)
        self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
        self.assertEqual(test2.text._rendered_list[0].data, "abc")
        self.assertEqual(test2.text._rendered_list[1].starts_at, 3)
        self.assertEqual(test2.text._rendered_list[1].data, "ghi")

        self.assertEqual(len(textowner.text._rendered_list), 2)
        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "abc")
        self.assertEqual(textowner.text._rendered_list[1].starts_at, 3)
        self.assertEqual(textowner.text._rendered_list[1].data, "ghi")

        self.assertEqual(test2.text._rendered_list[0],
                         test2.text.get_fragment_by_index(0)[0])
        self.assertEqual(test2.text._rendered_list[0],
                         test2.text.get_fragment_by_index(2)[0])
        self.assertEqual(test2.text._rendered_list[1],
                         test2.text.get_fragment_by_index(3)[0])
        self.assertEqual(test2.text._rendered_list[1],
                         test2.text.get_fragment_by_index(5)[0])
        self.assertEqual(0, test2.text.get_fragment_by_index(0)[1])
        self.assertEqual(0, test2.text.get_fragment_by_index(2)[1])
        self.assertEqual(1, test2.text.get_fragment_by_index(3)[1])
        self.assertEqual(1, test2.text.get_fragment_by_index(5)[1])

    def test_two_overlapping_conflicting_deletions(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdefghi")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)
        test2.text.render()
        self.dc2.freeze_dc_comms()
        textowner.text.removerange(3, 7)
        test2.text.removerange(3, 6)
        self.dc2.unfreeze_dc_comms()

        test2.text.render()

        self.assertEqual(test2.text.get_text(), textowner.text.get_text())
        self.assertEqual(test2.text.get_text(), "abchi")
        self.assertEqual(textowner.text.get_text(), "abchi")

        self.assertEqual(len(test2.text._rendered_list), 2)
        self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
        self.assertEqual(test2.text._rendered_list[0].data, "abc")
        self.assertEqual(test2.text._rendered_list[1].starts_at, 3)
        self.assertEqual(test2.text._rendered_list[1].data, "hi")

        self.assertEqual(len(textowner.text._rendered_list), 2)
        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "abc")
        self.assertEqual(textowner.text._rendered_list[1].starts_at, 3)
        self.assertEqual(textowner.text._rendered_list[1].data, "hi")

        self.assertEqual(test2.text._rendered_list[0],
                         test2.text.get_fragment_by_index(0)[0])
        self.assertEqual(test2.text._rendered_list[0],
                         test2.text.get_fragment_by_index(2)[0])
        self.assertEqual(test2.text._rendered_list[1],
                         test2.text.get_fragment_by_index(3)[0])
        self.assertEqual(test2.text._rendered_list[1],
                         test2.text.get_fragment_by_index(5)[0])
        self.assertEqual(0, test2.text.get_fragment_by_index(0)[1])
        self.assertEqual(0, test2.text.get_fragment_by_index(2)[1])
        self.assertEqual(1, test2.text.get_fragment_by_index(3)[1])
        self.assertEqual(1, test2.text.get_fragment_by_index(5)[1])

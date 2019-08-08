from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import Document
from historygraph import fields
from ..common import DocumentCollection, TestFieldTextEditOwner1


class TextEditTestReplication(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection()
        self.dc1.register(TestFieldTextEditOwner1)
        self.dc2 = DocumentCollection(master=self.dc1)
        self.dc2.register(TestFieldTextEditOwner1)

    def test_create_text_with_single_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)

        self.assertEqual(test2.text.get_text(), "abcdef")
        self.assertEqual(len(test2.text._rendered_list), 1)
        self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
        fragment = test2.text._rendered_list[0]
        self.assertEqual(fragment, test2.text.get_fragment_by_index(0)[0])
        self.assertEqual(fragment, test2.text.get_fragment_by_index(2)[0])
        self.assertEqual(fragment, test2.text.get_fragment_by_index(5)[0])
        self.assertEqual(0, test2.text.get_fragment_by_index(0)[1])

    def test_create_text_with_two_consecutative_fragments(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "def")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)
        test2.text.render()

        self.assertEqual(test2.text.get_text(), "abcdef")
        self.assertEqual(len(test2.text._rendered_list), 2)
        self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
        self.assertEqual(test2.text._rendered_list[0].data, "abc")
        self.assertEqual(test2.text._rendered_list[1].starts_at, 3)
        self.assertEqual(test2.text._rendered_list[1].data, "def")

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

    def test_create_text_with_two_reversed_fragments(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(0, "def")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)
        test2.text.render()

        self.assertEqual(test2.text.get_text(), "defabc")
        self.assertEqual(len(test2.text._rendered_list), 2)
        self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
        self.assertEqual(test2.text._rendered_list[0].data, "def")
        self.assertEqual(test2.text._rendered_list[1].starts_at, 3)
        self.assertEqual(test2.text._rendered_list[1].data, "abc")

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

    def test_create_text_with_three_consecutative_fragments(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)
        test2.text.render()

        self.assertEqual(test2.text.get_text(), "abcdefghi")
        self.assertEqual(len(test2.text._rendered_list), 3)
        self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
        self.assertEqual(test2.text._rendered_list[0].data, "abc")
        self.assertEqual(test2.text._rendered_list[1].starts_at, 3)
        self.assertEqual(test2.text._rendered_list[1].data, "def")
        self.assertEqual(test2.text._rendered_list[2].starts_at, 6)
        self.assertEqual(test2.text._rendered_list[2].data, "ghi")

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

    def test_delete_text_whole_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        textowner.text.render()

        old_first_node = textowner.text._rendered_list[0]
        old_last_node = textowner.text._rendered_list[2]

        textowner.text.removerange(3, 6)

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)
        test2.text.render()
        test2.text.recalc_starts_at(0)

        self.assertEqual(test2.text.get_text(), "abcghi")

        self.assertEqual(len(test2.text._rendered_list), 2)
        self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
        self.assertEqual(test2.text._rendered_list[0].data, "abc")
        self.assertEqual(test2.text._rendered_list[0].id, old_first_node.id)
        self.assertEqual(test2.text._rendered_list[1].starts_at, 3)
        self.assertEqual(test2.text._rendered_list[1].data, "ghi")
        self.assertEqual(test2.text._rendered_list[1].id, old_last_node.id)

    def test_delete_across_fragments(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        textowner.text.render()

        old_first_node = textowner.text._rendered_list[0]
        old_last_node = textowner.text._rendered_list[2]

        textowner.text.removerange(2, 7)

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)
        test2.text.render()
        test2.text.recalc_starts_at(0)

        self.assertEqual(len(test2.text._rendered_list), 2)
        self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
        self.assertEqual(test2.text._rendered_list[0].data, "ab")
        self.assertNotEqual(test2.text._rendered_list[0].id, old_first_node.id)
        self.assertEqual(test2.text._rendered_list[0].get_original_id(), old_first_node.id)
        self.assertEqual(test2.text._rendered_list[1].starts_at, 2)
        self.assertEqual(test2.text._rendered_list[1].data, "hi")
        self.assertNotEqual(test2.text._rendered_list[1].id, old_last_node.id)

    def test_delete_partial_fragment_at_start(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        textowner.text.render()

        old_first_node = textowner.text._rendered_list[0]

        textowner.text.removerange(0, 2)

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)
        test2.text.render()
        test2.text.recalc_starts_at(0)

        self.assertEqual(len(test2.text._rendered_list), 3)
        self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
        self.assertEqual(test2.text._rendered_list[0].data, "c")
        self.assertNotEqual(test2.text._rendered_list[0].id, old_first_node.id)
        self.assertNotEqual(test2.text._rendered_list[0].get_original_id(), old_first_node.id)
        self.assertEqual(test2.text._rendered_list[1].starts_at, 1)
        self.assertEqual(test2.text._rendered_list[1].data, "def")
        self.assertEqual(test2.text._rendered_list[2].starts_at, 4)
        self.assertEqual(test2.text._rendered_list[2].data, "ghi")

    def test_delete_multi_partial_fragment_at_start(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        textowner.text.render()

        textowner.text.removerange(0, 4)

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)
        test2.text.render()
        test2.text.recalc_starts_at(0)

        self.assertEqual(len(test2.text._rendered_list), 2)
        self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
        self.assertEqual(test2.text._rendered_list[0].data, "ef")
        self.assertEqual(test2.text._rendered_list[1].starts_at, 2)
        self.assertEqual(test2.text._rendered_list[1].data, "ghi")

    def test_delete_partial_fragment_at_end(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        textowner.text.render()

        old_first_node = textowner.text._rendered_list[0]

        textowner.text.removerange(7, 9)

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)
        test2.text.render()
        test2.text.recalc_starts_at(0)

        self.assertEqual(len(test2.text._rendered_list), 3)
        self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
        self.assertEqual(test2.text._rendered_list[0].data, "abc")
        self.assertEqual(test2.text._rendered_list[0].id, old_first_node.id)
        self.assertEqual(test2.text._rendered_list[0].get_original_id(), old_first_node.id)
        self.assertEqual(test2.text._rendered_list[1].starts_at, 3)
        self.assertEqual(test2.text._rendered_list[1].data, "def")
        self.assertEqual(test2.text._rendered_list[2].starts_at, 6)
        self.assertEqual(test2.text._rendered_list[2].data, "g")

    def test_delete_multi_partial_fragment_at_end(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        textowner.text.render()

        old_first_node = textowner.text._rendered_list[0]

        textowner.text.removerange(5, 9)

        test2 = self.dc2.get_object_by_id(TestFieldTextEditOwner1.__name__, textowner.id)
        test2.text.render()
        test2.text.recalc_starts_at(0)

        self.assertEqual(len(test2.text._rendered_list), 2)
        self.assertEqual(test2.text._rendered_list[0].starts_at, 0)
        self.assertEqual(test2.text._rendered_list[0].data, "abc")
        self.assertEqual(test2.text._rendered_list[0].id, old_first_node.id)
        self.assertEqual(test2.text._rendered_list[0].get_original_id(), old_first_node.id)
        self.assertEqual(test2.text._rendered_list[1].starts_at, 3)
        self.assertEqual(test2.text._rendered_list[1].data, "de")

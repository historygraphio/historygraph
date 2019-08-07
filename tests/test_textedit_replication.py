from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import Document
from historygraph import fields
from .common import DocumentCollection, TestFieldTextEditOwner1


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

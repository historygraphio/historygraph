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

        textowner.text.insert(3, "xyz")

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

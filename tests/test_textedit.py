from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import Document
from historygraph import fields
from .common import DocumentCollection

# A TextEdit is a new CRDT similar to a list in some ways but designed for
# storing collaboratively edited text files. The problem it solves is -
# we could implement a text edit as a List of characters but that is
# unduely slow for fairly large files. A test of inserted 100,000 characters
# in such an array took 38 seconds. So for example importing an existing
# source code file. This data is designed to handle these large copy paste type
# edit much more easily.
#
# Algorithm notes
# Text is an array of fragments.
#
# Each fragment is a string of text. Once a fragment is produced it can never
# be changed (but it can be replaced by two new fragments with the same
# content as the old one)
#
# The text fragment also caches it's current index into the output. When a new
# fragment is inserted every fragment after it must be moved along.
#
# When a fragment is deleted fragments after it are moved back.
#
# When we insert we can easily go from the current index into the string to which ever fragment we are in because we can then perform a binary search thru the list.
#
# Each fragment has a few operations
# Split which will remove a fragment and replace it which two other ones
# Insert new fragment - this inserts a new fragment and moves everything else around
# Delete a fragment - remove it from the current list. This tombstones it since we can never fully delete.
#
# In the future we will need to calculate line begining and put them into this list.
#
# This work is inspired by y.js, concave and atom teletype-crdt. But not based
# on any of their algorithms
#
# Future evolution:
# Stage one is to get this to work as outlined for simple text editing
# Stage one point five get it to generate a list of lines. Ie a list of strings
# Stage two add support for markers (as per atom teletype)
# Stage three a new related datatype for rich text editing
#
class TextEditTest(unittest.TestCase):
    def test_create_text_with_single_fragment(self):
        class TestFieldTextEditOwner1(Document):
            text = fields.TextEdit()

        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        self.assertEqual(textowner.text.get_text(), "abcdef")
        self.assertEqual(len(textowner.text._rendered_list), 1)
        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        fragment = textowner.text._rendered_list[0]
        self.assertEqual(fragment, textowner.text.get_fragment_by_index(0)[0])
        self.assertEqual(fragment, textowner.text.get_fragment_by_index(2)[0])
        self.assertEqual(fragment, textowner.text.get_fragment_by_index(5)[0])
        self.assertEqual(0, textowner.text.get_fragment_by_index(0)[1])

    def test_create_text_with_two_consecutative_fragments(self):
        class TestFieldTextEditOwner1(Document):
            text = fields.TextEdit()

        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "def")

        textowner.text.render()
        self.assertEqual(len(textowner.text._rendered_list), 2)
        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "abc")
        self.assertEqual(textowner.text._rendered_list[1].starts_at, 3)
        self.assertEqual(textowner.text._rendered_list[1].data, "def")

        self.assertEqual(textowner.text._rendered_list[0],
                         textowner.text.get_fragment_by_index(0)[0])
        self.assertEqual(textowner.text._rendered_list[0],
                         textowner.text.get_fragment_by_index(2)[0])
        self.assertEqual(textowner.text._rendered_list[1],
                         textowner.text.get_fragment_by_index(3)[0])
        self.assertEqual(textowner.text._rendered_list[1],
                         textowner.text.get_fragment_by_index(5)[0])
        self.assertEqual(0, textowner.text.get_fragment_by_index(0)[1])
        self.assertEqual(0, textowner.text.get_fragment_by_index(2)[1])
        self.assertEqual(1, textowner.text.get_fragment_by_index(3)[1])
        self.assertEqual(1, textowner.text.get_fragment_by_index(5)[1])

        self.assertEqual(textowner.text.get_text(), "abcdef")

    def test_create_text_with_two_reversed_fragments(self):
        class TestFieldTextEditOwner1(Document):
            text = fields.TextEdit()

        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(0, "def")

        textowner.text.render()
        self.assertEqual(len(textowner.text._rendered_list), 2)
        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "def")
        self.assertEqual(textowner.text._rendered_list[1].starts_at, 3)
        self.assertEqual(textowner.text._rendered_list[1].data, "abc")

        self.assertEqual(textowner.text._rendered_list[0],
                         textowner.text.get_fragment_by_index(0)[0])
        self.assertEqual(textowner.text._rendered_list[0],
                         textowner.text.get_fragment_by_index(2)[0])
        self.assertEqual(textowner.text._rendered_list[1],
                         textowner.text.get_fragment_by_index(3)[0])
        self.assertEqual(textowner.text._rendered_list[1],
                         textowner.text.get_fragment_by_index(5)[0])
        self.assertEqual(0, textowner.text.get_fragment_by_index(0)[1])
        self.assertEqual(0, textowner.text.get_fragment_by_index(2)[1])
        self.assertEqual(1, textowner.text.get_fragment_by_index(3)[1])
        self.assertEqual(1, textowner.text.get_fragment_by_index(5)[1])

        self.assertEqual(textowner.text.get_text(), "defabc")

    def test_split_fragments(self):
        class TestFieldTextEditOwner1(Document):
            text = fields.TextEdit()

        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "def")

        textowner.text.render()
        self.assertEqual(len(textowner.text._rendered_list), 2)

        old_fragment = textowner.text._rendered_list[0] # The fragment being split

        textowner.text._split_fragment(0, 2)
        textowner.text.render()
        self.assertEqual(len(textowner.text._rendered_list), 3)

        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "ab")
        # Test the first new fragments original id matches the id of the original node
        # this ensure the sort order does not change it is dedenpendt on node id's
        self.assertEqual(old_fragment.id,
                         textowner.text._rendered_list[0].get_original_id())
        self.assertEqual(textowner.text._rendered_list[1].starts_at, 2)
        self.assertEqual(textowner.text._rendered_list[1].id,
                         textowner.text._rendered_list[1].get_original_id())
        self.assertNotEqual(old_fragment.id,
                            textowner.text._rendered_list[1].get_original_id())
        self.assertEqual(textowner.text._rendered_list[1].data, "c")
        self.assertEqual(textowner.text._rendered_list[2].starts_at, 3)
        self.assertEqual(textowner.text._rendered_list[2].data, "def")
        self.assertEqual(textowner.text._rendered_list[2].id,
                         textowner.text._rendered_list[2].get_original_id())
        self.assertNotEqual(old_fragment.id,
                            textowner.text._rendered_list[2].get_original_id())

    def test_split_second_fragment(self):
        class TestFieldTextEditOwner1(Document):
            text = fields.TextEdit()

        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "def")

        textowner.text.render()
        self.assertEqual(len(textowner.text._rendered_list), 2)

        old_fragment = textowner.text._rendered_list[1] # The fragment being split

        textowner.text._split_fragment(1, 1)
        textowner.text.render()
        self.assertEqual(len(textowner.text._rendered_list), 3)

        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "abc")
        self.assertEqual(textowner.text._rendered_list[0].id,
                         textowner.text._rendered_list[0].get_original_id())

        self.assertEqual(textowner.text._rendered_list[1].starts_at, 3)
        self.assertEqual(textowner.text._rendered_list[1].data, "d")

        self.assertEqual(old_fragment.id,
                         textowner.text._rendered_list[1].get_original_id())
        self.assertNotEqual(textowner.text._rendered_list[1].id,
                            textowner.text._rendered_list[1].get_original_id())

        self.assertEqual(textowner.text._rendered_list[2].starts_at, 4)
        self.assertEqual(textowner.text._rendered_list[2].data, "ef")
        self.assertEqual(textowner.text._rendered_list[2].id,
                         textowner.text._rendered_list[2].get_original_id())
        self.assertNotEqual(old_fragment.id,
                            textowner.text._rendered_list[2].get_original_id())

    def test_split_middle_fragment(self):
        class TestFieldTextEditOwner1(Document):
            text = fields.TextEdit()

        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "def")
        textowner.text.insert(6, "ghi")

        textowner.text.render()

        self.assertEqual(len(textowner.text._rendered_list), 3)

        old_fragment = textowner.text._rendered_list[1] # The fragment being split

        textowner.text._split_fragment(1, 1)
        textowner.text.render()

        self.assertEqual(len(textowner.text._rendered_list), 4)

        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "abc")
        self.assertEqual(textowner.text._rendered_list[0].id,
                         textowner.text._rendered_list[0].get_original_id())

        self.assertEqual(textowner.text._rendered_list[1].starts_at, 3)
        self.assertEqual(textowner.text._rendered_list[1].data, "d")

        self.assertEqual(old_fragment.id,
                         textowner.text._rendered_list[1].get_original_id())
        self.assertNotEqual(textowner.text._rendered_list[1].id,
                            textowner.text._rendered_list[1].get_original_id())

        self.assertEqual(textowner.text._rendered_list[2].starts_at, 4)
        self.assertEqual(textowner.text._rendered_list[2].data, "ef")
        self.assertEqual(textowner.text._rendered_list[2].id,
                         textowner.text._rendered_list[2].get_original_id())
        self.assertNotEqual(old_fragment.id,
                            textowner.text._rendered_list[2].get_original_id())

        self.assertEqual(textowner.text._rendered_list[3].starts_at, 6)
        self.assertEqual(textowner.text._rendered_list[3].data, "ghi")
        self.assertEqual(textowner.text._rendered_list[3].id,
                         textowner.text._rendered_list[3].get_original_id())
        self.assertNotEqual(old_fragment.id,
                            textowner.text._rendered_list[3].get_original_id())

    def test_create_text_with_three_consecutative_fragments(self):
        class TestFieldTextEditOwner1(Document):
            text = fields.TextEdit()

        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        textowner.text.render()
        self.assertEqual(len(textowner.text._rendered_list), 3)
        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "abc")
        self.assertEqual(textowner.text._rendered_list[1].starts_at, 3)
        self.assertEqual(textowner.text._rendered_list[1].data, "def")
        self.assertEqual(textowner.text._rendered_list[2].starts_at, 6)
        self.assertEqual(textowner.text._rendered_list[2].data, "ghi")

        self.assertEqual(textowner.text._rendered_list[0],
                         textowner.text.get_fragment_by_index(0)[0])
        self.assertEqual(textowner.text._rendered_list[0],
                         textowner.text.get_fragment_by_index(2)[0])
        self.assertEqual(textowner.text._rendered_list[1],
                         textowner.text.get_fragment_by_index(3)[0])
        self.assertEqual(textowner.text._rendered_list[1],
                         textowner.text.get_fragment_by_index(5)[0])
        self.assertEqual(textowner.text._rendered_list[2],
                         textowner.text.get_fragment_by_index(6)[0])
        self.assertEqual(textowner.text._rendered_list[2],
                         textowner.text.get_fragment_by_index(8)[0])
        self.assertEqual(0, textowner.text.get_fragment_by_index(0)[1])
        self.assertEqual(0, textowner.text.get_fragment_by_index(2)[1])
        self.assertEqual(1, textowner.text.get_fragment_by_index(3)[1])
        self.assertEqual(1, textowner.text.get_fragment_by_index(5)[1])
        self.assertEqual(2, textowner.text.get_fragment_by_index(6)[1])
        self.assertEqual(2, textowner.text.get_fragment_by_index(8)[1])

        self.assertEqual(textowner.text.get_text(), "abcdefghi")

    def test_delete_text_whole_fragment(self):
        class TestFieldTextEditOwner1(Document):
            text = fields.TextEdit()

        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        textowner.text.render()

        old_first_node = textowner.text._rendered_list[0]
        old_last_node = textowner.text._rendered_list[2]

        textowner.text.removerange(3, 6)

        textowner.text.render()

        self.assertEqual(len(textowner.text._rendered_list), 2)
        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "abc")
        self.assertEqual(textowner.text._rendered_list[0].id, old_first_node.id)
        self.assertEqual(textowner.text._rendered_list[1].starts_at, 3)
        self.assertEqual(textowner.text._rendered_list[1].data, "ghi")
        self.assertEqual(textowner.text._rendered_list[1].id, old_last_node.id)

    def test_delete_across_fragments(self):
        class TestFieldTextEditOwner1(Document):
            text = fields.TextEdit()

        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        textowner.text.render()

        old_first_node = textowner.text._rendered_list[0]
        old_last_node = textowner.text._rendered_list[2]

        textowner.text.removerange(2, 7)

        textowner.text.render()

        self.assertEqual(len(textowner.text._rendered_list), 2)
        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "ab")
        self.assertNotEqual(textowner.text._rendered_list[0].id, old_first_node.id)
        self.assertEqual(textowner.text._rendered_list[0].get_original_id(), old_first_node.id)
        self.assertEqual(textowner.text._rendered_list[1].starts_at, 2)
        self.assertEqual(textowner.text._rendered_list[1].data, "hi")
        self.assertNotEqual(textowner.text._rendered_list[1].id, old_last_node.id)

    def test_delete_partial_fragment_at_start(self):
        class TestFieldTextEditOwner1(Document):
            text = fields.TextEdit()

        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        textowner.text.render()

        old_first_node = textowner.text._rendered_list[0]

        textowner.text.removerange(0, 2)

        textowner.text.render()

        self.assertEqual(len(textowner.text._rendered_list), 3)
        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "c")
        self.assertNotEqual(textowner.text._rendered_list[0].id, old_first_node.id)
        self.assertNotEqual(textowner.text._rendered_list[0].get_original_id(), old_first_node.id)
        self.assertEqual(textowner.text._rendered_list[1].starts_at, 1)
        self.assertEqual(textowner.text._rendered_list[1].data, "def")
        self.assertEqual(textowner.text._rendered_list[2].starts_at, 4)
        self.assertEqual(textowner.text._rendered_list[2].data, "ghi")

    def test_delete_multi_partial_fragment_at_start(self):
        class TestFieldTextEditOwner1(Document):
            text = fields.TextEdit()

        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        textowner.text.render()

        textowner.text.removerange(0, 4)

        textowner.text.render()

        self.assertEqual(len(textowner.text._rendered_list), 2)
        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "ef")
        self.assertEqual(textowner.text._rendered_list[1].starts_at, 2)
        self.assertEqual(textowner.text._rendered_list[1].data, "ghi")

    def test_delete_partial_fragment_at_end(self):
        class TestFieldTextEditOwner1(Document):
            text = fields.TextEdit()

        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        textowner.text.render()

        old_first_node = textowner.text._rendered_list[0]

        textowner.text.removerange(7, 9)

        textowner.text.render()

        self.assertEqual(len(textowner.text._rendered_list), 3)
        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "abc")
        self.assertEqual(textowner.text._rendered_list[0].id, old_first_node.id)
        self.assertEqual(textowner.text._rendered_list[0].get_original_id(), old_first_node.id)
        self.assertEqual(textowner.text._rendered_list[1].starts_at, 3)
        self.assertEqual(textowner.text._rendered_list[1].data, "def")
        self.assertEqual(textowner.text._rendered_list[2].starts_at, 6)
        self.assertEqual(textowner.text._rendered_list[2].data, "g")

    def test_delete_multi_partial_fragment_at_end(self):
        class TestFieldTextEditOwner1(Document):
            text = fields.TextEdit()

        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "ghi")
        textowner.text.insert(3, "def")

        textowner.text.render()

        old_first_node = textowner.text._rendered_list[0]

        textowner.text.removerange(5, 9)

        textowner.text.render()

        self.assertEqual(len(textowner.text._rendered_list), 2)
        self.assertEqual(textowner.text._rendered_list[0].starts_at, 0)
        self.assertEqual(textowner.text._rendered_list[0].data, "abc")
        self.assertEqual(textowner.text._rendered_list[0].id, old_first_node.id)
        self.assertEqual(textowner.text._rendered_list[0].get_original_id(), old_first_node.id)
        self.assertEqual(textowner.text._rendered_list[1].starts_at, 3)
        self.assertEqual(textowner.text._rendered_list[1].data, "de")

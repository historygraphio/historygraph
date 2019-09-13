from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import Document
from historygraph import fields
from ..common import DocumentCollection, TestFieldTextEditOwner1
import uuid

# A marker is a position in the code. We anticpate that markers will be
# attached to other data type that will determine the position in the code.
# Each of the these data types will have their own handling for various
# conditions. Most notably the marker has been deleted. This may include
# a double marker has been deleted
#
# A marker is just the id of a fragment and offset into that fragment.
# We would typically want to turn this into a line number and column position
# Other typical operations are to determine if a marker has been deleted
# or the entire range between a pair of markers has been deleted


class TextEditMarkersTest(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(TestFieldTextEditOwner1)

    # Test the lines algorithm works correctly in standalone scenarios
    def test_marker_inside_a_simple_document(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        marker = textowner.text.get_marker(textowner.text._listfragments[0].id,
                                           3)

        self.assertEqual(marker.line, 0)
        self.assertEqual(marker.column, 3)

    def test_marker_before_a_simple_linkbreak(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcd\nef")

        marker = textowner.text.get_marker(textowner.text._listfragments[0].id,
                                           3)

        self.assertEqual(marker.line, 0)
        self.assertEqual(marker.column, 3)

    def test_marker_after_a_simple_linkbreak(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "ab\ncdef")

        marker = textowner.text.get_marker(textowner.text._listfragments[0].id,
                                           4)

        self.assertEqual(marker.line, 1)
        self.assertEqual(marker.column, 1)

    def test_marker_in_second_fragment_on_line(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcd\nef")
        # Fake the first fragment belonging to a different session so we get
        # two fragments created
        textowner.text._listfragments[0].sessionid = str(uuid.uuid4())
        textowner.text.insert(7, "ghi")

        marker = textowner.text.get_marker(textowner.text._listfragments[1].id,
                                           1)

        self.assertEqual(marker.line, 1)
        self.assertEqual(marker.column, 3)

    def test_marker_in_third_fragment_on_line(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcd\nef")
        # Fake the first fragment belonging to a different session so we get
        # two fragments created
        textowner.text._listfragments[0].sessionid = str(uuid.uuid4())
        textowner.text.insert(7, "ghi")
        textowner.text._listfragments[1].sessionid = str(uuid.uuid4())
        textowner.text.insert(10, "jkl")

        marker = textowner.text.get_marker(textowner.text._listfragments[2].id,
                                           1)

        self.assertEqual(marker.line, 1)
        self.assertEqual(marker.column, 6)

    def test_marker_last_position_before_a_simple_linkbreak(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcd\nef")

        marker = textowner.text.get_marker(textowner.text._listfragments[0].id,
                                           4)

        self.assertEqual(marker.line, 0)
        self.assertEqual(marker.column, 4)

    def test_marker_first_position_after_a_simple_linkbreak(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcd\nef")

        marker = textowner.text.get_marker(textowner.text._listfragments[0].id,
                                           5)

        self.assertEqual(marker.line, 1)
        self.assertEqual(marker.column, 0)

    def test_marker_inside_a_split_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        textowner.text.insert(3, "g\nhi")

        marker = textowner.text.get_marker(textowner.text._listfragments[0].id,
                                           4)
        self.assertEqual(marker.line, 1)
        self.assertEqual(marker.column, 3)

    def test_marker_inside_a_split_fragment_alt_pattern(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcd\nef")

        textowner.text.insert(3, "ghi")

        marker = textowner.text.get_marker(textowner.text._listfragments[0].id,
                                           6)
        self.assertEqual(marker.line, 1)
        self.assertEqual(marker.column, 1)

    # Test marker inside a simple deleted fragment
    def test_marker_inside_a_frqagment_which_is_partially_deleted(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        textowner.text.removerange(2, 4)

        marker = textowner.text.get_marker(textowner.text._listfragments[0].id,
                                           3)

        self.assertEqual(marker.line, 0)
        self.assertEqual(marker.column, 2)

    def test_marker_at_start_of_a_fragment_which_is_partially_deleted(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        textowner.text.removerange(2, 4)

        marker = textowner.text.get_marker(textowner.text._listfragments[0].id,
                                           2)

        self.assertEqual(marker.line, 0)
        self.assertEqual(marker.column, 2)

    def test_marker_at_end_of_a_fragment_which_is_partially_deleted(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        textowner.text.removerange(2, 4)

        marker = textowner.text.get_marker(textowner.text._listfragments[0].id,
                                           4)

        self.assertEqual(marker.line, 0)
        self.assertEqual(marker.column, 2)

    def test_marker_completely_deleted_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.insert(3, "xyz")

        fragment_id = textowner.text._listfragments[1].id

        textowner.text.removerange(3, 6)

        marker = textowner.text.get_marker(fragment_id,
                                           1)
        self.assertEqual(marker.line, 0)
        self.assertEqual(marker.column, 3)

    def test_marker_in_start_of_partially_deleted_fragment(self):
        textowner = TestFieldTextEditOwner1()

        self.dc1.register(TestFieldTextEditOwner1)
        self.dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.insert(3, "xyz")

        fragment_id = textowner.text._listfragments[1].id

        textowner.text.removerange(3, 4)

        marker = textowner.text.get_marker(fragment_id,
                                           1)
        self.assertEqual(marker.line, 0)
        self.assertEqual(marker.column, 3)

from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import Document
from historygraph import fields
from ..common import DocumentCollection, TestFieldTextEditOwner1

class TextEditTest(unittest.TestCase):
    # Test the lines algorithm works correctly in standalone scenarios
    def test_simple_document_has_one_line(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 1)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abcdef")

    def test_two_fragment_document_is_one_line(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "def")

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 1)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abcdef")

    def test_split_fragment_document_is_one_line(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(1, "def")

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 1)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "adefbc")

    def test_simple_document_is_two_lines(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc\ndef")

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 2)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abc")

        line = lines[1]
        self.assertEqual(line.start_offset, 4)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "def")

    def test_simple_document_is_two_lines_new_line_at_end(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef\n")

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 2)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abcdef")

        line = lines[1]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 1)
        self.assertEqual(line.get_content(), "")

    def test_split_fragment_document_is_two_lines(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "\ndef")

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 2)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abc")

        line = lines[1]
        self.assertEqual(line.start_offset, 1)
        self.assertEqual(line.start_fragment, 1)
        self.assertEqual(line.get_content(), "def")

    def test_split_fragment_document_is_two_lines_new_line_at_end(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abcdef")
        textowner.text.insert(6, "\n")

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 2)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abcdef")

        line = lines[1]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 2)
        self.assertEqual(line.get_content(), "")

    def test_simple_document_two_lines_is_one_after_deletion(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc\ndef")

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 2)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abc")

        line = lines[1]
        self.assertEqual(line.start_offset, 4)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "def")

        textowner.text.removerange(3, 4)

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 1)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abcdef")

    def test_split_fragment_document_two_lines_is_one_after_deletion(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc")
        textowner.text.insert(3, "\ndef")

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 2)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abc")

        line = lines[1]
        self.assertEqual(line.start_offset, 1)
        self.assertEqual(line.start_fragment, 1)
        self.assertEqual(line.get_content(), "def")

        textowner.text.removerange(3, 4)

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 1)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abcdef")

    def test_simple_document_three_lines_is_two_after_deletion(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc\ndef\nghi")

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 3)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abc")

        line = lines[1]
        self.assertEqual(line.start_offset, 4)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "def")

        line = lines[2]
        self.assertEqual(line.start_offset, 8)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "ghi")

        textowner.text.removerange(3, 4)

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 2)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abcdef")

        line = lines[1]
        self.assertEqual(line.start_offset, 4)
        self.assertEqual(line.start_fragment, 1)
        self.assertEqual(line.get_content(), "ghi")

    def test_multi_fragment_document_three_lines_is_two_after_deletion(self):
        textowner = TestFieldTextEditOwner1()

        dc1 = DocumentCollection()
        dc1.register(TestFieldTextEditOwner1)
        dc1.add_document_object(textowner)

        textowner.text.insert(0, "abc\n")
        textowner.text.insert(4, "def\n")
        textowner.text.insert(8, "ghi")

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 3)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abc")

        line = lines[1]
        self.assertEqual(line.start_fragment, 1)
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.get_content(), "def")

        line = lines[2]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 2)
        self.assertEqual(line.get_content(), "ghi")

        textowner.text.removerange(3, 4)

        lines = textowner.text.get_lines()
        self.assertEqual(len(lines), 2)
        line = lines[0]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 0)
        self.assertEqual(line.get_content(), "abcdef")

        line = lines[1]
        self.assertEqual(line.start_offset, 0)
        self.assertEqual(line.start_fragment, 2)
        self.assertEqual(line.get_content(), "ghi")
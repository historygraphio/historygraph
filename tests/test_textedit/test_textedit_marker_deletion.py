from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import Document
from historygraph import fields
from ..common import DocumentCollection, TestFieldTextEditOwner1
import uuid

# Test in this file are used to test feature relating to marker deletion
# If the user deletes a fragment of text the markers should go with it

class TextEditMarkersTest(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(TestFieldTextEditOwner1)

    def test_marker_in_middle_of_deleted_fragment(self):
        pass

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

    @unittest.expectedFailure
    def test_create_two_conflicting_fragments(self):
        assert False

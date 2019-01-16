# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import Document, DocumentCollection
from historygraph import fields
import uuid


class SingletonDocumentTest(unittest.TestCase):
    def test_singleton_is_automatically_created(self):
        class TestSingleton(Document):
            is_singleton = True
            nothing = fields.CharRegister()

        dc1 = DocumentCollection()
        dc1.register(TestSingleton)
        docs = dc1.get_by_class(TestSingleton)
        # Test the document is created
        self.assertEqual(len(docs), 1)
         # Test it is in it's default state
        self.assertEqual(len(docs[0].history._edgesbyendnode), 0)
        # New single objects always have the same id
        self.assertEqual(docs[0].id, TestSingleton().id)

        with self.assertRaises(AssertionError):
            # Test we cannot create a singleton with a different id
            TestSingleton(uuid.uuid4())

        # Test we can create a signleton with the same ID
        TestSingleton(docs[0].id)

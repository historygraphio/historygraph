from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import (DocumentCollection, CounterTestContainer, Covers,
                     TestPropertyOwner2, TestPropertyOwner1,
                     TestFieldListOwner2, TestFieldListOwner1)
from historygraph import DocumentObject
from historygraph import Document
from historygraph import fields
from historygraph import edges
from historygraph import ImmutableObject
import time
import timeit
import uuid
import hashlib
from json import JSONEncoder, JSONDecoder
from collections import defaultdict


class SimpleCoversTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(Covers)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(Covers)

    def test_covers_with_single_edge(self):
        #Test merging together simple covers documents
        test = Covers()
        self.dc1.add_document_object(test)
        test.covers = 1
        #Test we can set a value
        self.assertEqual(test.covers, 1)
        #Test we can rebuild a simple object by playing an edge via sharing in linked DCs
        test2 = self.dc2.get_object_by_id(Covers.__name__, test.id)
        self.assertEqual(test2.covers, 1)
        #Test these are not just the same document but it was actually copied
        assert test is not test2
        assert test.history is not test2.history
        assert test.history.get_edges_by_end_node(test._clockhash).sessionid == self.dc1.sessionid
        assert test2.history.get_edges_by_end_node(test._clockhash).sessionid == self.dc1.sessionid

    def test_covers_with_two_edges(self):
        test = Covers()
        self.dc1.add_document_object(test)
        test.covers = 1
        test.covers = 2
        test2 = self.dc2.get_object_by_id(Covers.__name__, test.id)
        self.assertEqual(test.covers, 2)
        assert test.history is not test2.history
        assert test is not test2

    def test_add_document_listener(self):
        result = defaultdict(int)
        class TestListener(object):
            def document_object_added(self, dc, obj):
                result['document_object_added'] += 1
            def immutable_object_added(self, dc, obj):
                pass
            def edges_added(self, dc, edges):
                pass
        self.dc1.add_listener(TestListener())

        self.assertEqual(result['document_object_added'], 0)
        #Test merging together simple covers documents
        test = Covers()
        self.dc1.add_document_object(test)
        self.assertEqual(result['document_object_added'], 1)
        test.covers = 1
        #Test we can set a value
        self.assertEqual(test.covers, 1)
        #Test we can rebuild a simple object by playing an edge via sharing in linked DCs
        test2 = self.dc2.get_object_by_id(Covers.__name__, test.id)
        self.assertEqual(test2.covers, 1)
        #Test these are not just the same document but it was actually copied
        assert test is not test2
        assert test.history is not test2.history

class MergeHistoryCoverTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(Covers)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(Covers)

    def runTest(self):
        #Test merge together two simple covers objects
        test = Covers()
        self.dc1.add_document_object(test)
        test.covers = 1
        test2 = self.dc2.get_object_by_id(Covers.__name__, test.id)
        self.dc2.freeze_dc_comms()
        test.covers = 2
        self.assertEqual(test2.covers, 1)
        test2.covers = 3
        self.assertEqual(test.covers, 2)
        self.assertEqual(test2.covers, 3)
        self.dc2.unfreeze_dc_comms()
        #In a merge conflict between two integers the greater one is the winner
        edges = [e.as_tuple() for e in test2.history.get_all_edges()]
        self.assertEqual(test2.covers, 3, 'test.covers={} test2.covers={} edges={}'.format(test.covers, test2.covers, edges))
        edges = [e.as_tuple() for e in test.history.get_all_edges()]
        self.assertEqual(test.covers, 3, 'test.covers={} test2.covers={} edges={}'.format(test.covers, test2.covers, edges))

class MergeHistorySendEdgeCoverTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(Covers)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(Covers)

        self.test = Covers()
        self.dc1.add_document_object(self.test)
        self.test.covers = 1
        self.test2 = self.dc2.get_object_by_id(Covers.__name__, self.test.id)
        self.dc2.freeze_dc_comms()

        self.test2.covers = 3
        self.test2.covers = 4
        self.edge3 = self.test2.history.get_edges_by_end_node(self.test2._clockhash)
        self.edge2 = self.test2.history.get_edges_by_end_node(list(self.edge3._start_hashes)[0])

    def test_sending_edges_manually(self):
        # This function test that manually invocation of the send_edges method works correctly

        self.dc2.slave_listener.send_edges([self.edge2.as_tuple(), self.edge3.as_tuple()])
        self.assertEqual(self.test.covers, 4)

    def test_sending_edges_out_of_order(self):
        # First sent and orhaned edge and verify it is ignore
        self.dc2.slave_listener.send_edges([self.edge3.as_tuple()])
        self.assertEqual(self.test.covers, 1)

        self.dc2.slave_listener.send_edges([self.edge2.as_tuple()])
        self.assertEqual(self.test.covers, 4)

    def test_sending_merge_edge_with_one_invalid_start_hash(self):
        dummysha = hashlib.sha256('Invalid node'.encode('utf-8')).hexdigest()
        old_clockhash = self.test._clockhash
        edgenull = edges.Merge({self.test._clockhash, dummysha}, "", "", "", "", self.test.id, self.test.__class__.__name__)
        self.dc2.slave_listener.send_edges([edgenull.as_tuple()])
        self.assertEqual(self.test.covers, 1)
        self.assertEqual(self.test._clockhash, old_clockhash)

        # Test if we send more matching edges they work
        self.dc2.slave_listener.send_edges([self.edge2.as_tuple(), self.edge3.as_tuple()])
        self.assertEqual(self.test.covers, 4)

class ListItemChangeHistoryTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection(str(uuid.uuid4()))
        self.dc.register(TestPropertyOwner1)
        self.dc.register(TestPropertyOwner2)

    def runTest(self):
        #Test that various types of changes create was changed events
        test1 = TestPropertyOwner1()
        self.dc.add_document_object(test1)
        test1.bWasChanged = False
        test2 = TestPropertyOwner2()
        test1.propertyowner2s.add(test2)
        self.assertTrue(test1.bWasChanged)
        test1.bWasChanged = False
        test2.cover = 1
        self.assertTrue(test1.bWasChanged)
        test1.bWasChanged = False
        test2.cover = 1
        self.assertTrue(test1.bWasChanged)
        test1.propertyowner2s.remove(test2.id)
        self.assertEqual(len(test1.propertyowner2s), 0)

class SimpleItemTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(TestPropertyOwner1)
        self.dc1.register(TestPropertyOwner2)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(TestPropertyOwner1)
        self.dc2.register(TestPropertyOwner2)

    def test_replicating_an_object_in_a_collection(self):
        test1 = TestPropertyOwner1()
        self.dc1.add_document_object(test1)
        testitem = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem)
        self.dc1.add_document_object(testitem)
        testitem.cover = 1

        #Test semantics for retriving objects
        self.assertEqual(len(test1.propertyowner2s), 1)
        for po2 in test1.propertyowner2s:
            self.assertEqual(po2.__class__.__name__ , TestPropertyOwner2.__name__)
            self.assertEqual(po2.cover, 1)

        test2 = self.dc2.get_object_by_id(TestPropertyOwner1.__name__, test1.id)
        self.assertEqual(len(test2.propertyowner2s), 1)
        for po2 in test2.propertyowner2s:
            self.assertEqual(po2.__class__.__name__, TestPropertyOwner2.__name__)
            self.assertEqual(po2.cover, 1)

    def test_replicating_then_deleting_an_object_from_a_collection(self):
        test1 = TestPropertyOwner1()
        self.dc1.add_document_object(test1)
        testitem = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem)
        self.dc1.add_document_object(testitem)
        testitem.cover = 1
        test1.propertyowner2s.remove(testitem.id)

        #Test semantics for retriving objects
        self.assertEqual(len(test1.propertyowner2s), 0)

        test2 = self.dc2.get_object_by_id(TestPropertyOwner1.__name__, test1.id)
        self.assertEqual(len(test2.propertyowner2s), 0)


class AdvancedItemTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(TestPropertyOwner1)
        self.dc1.register(TestPropertyOwner2)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(TestPropertyOwner1)
        self.dc2.register(TestPropertyOwner2)

    def test_adding_and_deleting_a_sub_item(self):
        #Test changing them deleting a sub element
        test1 = TestPropertyOwner1()
        self.dc1.add_document_object(test1)
        testitem1 = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem1)
        self.dc1.add_document_object(testitem1)
        testitem1.cover = 1
        self.dc2.freeze_dc_comms()
        test2 = self.dc2.get_object_by_id(TestPropertyOwner1.__name__, test1.id)
        testitem2 = test2.get_document_object(testitem1.id)
        testitem2.cover = 2
        test2.propertyowner2s.remove(testitem2.id)
        self.dc2.unfreeze_dc_comms()
        self.assertEqual(len(test1.propertyowner2s), 0)

    def test_adding_and_deleting_a_sub_item_in_reverse_order(self):
        #Test changing them deleting a sub element. Test merging in the opposition order to previous test
        test1 = TestPropertyOwner1()
        self.dc1.add_document_object(test1)
        testitem1 = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem1)
        self.dc1.add_document_object(testitem1)
        testitem1.cover = 1
        self.dc2.freeze_dc_comms()
        test2 = self.dc2.get_object_by_id(TestPropertyOwner1.__name__, test1.id)
        testitem2 = test2.get_document_object(testitem1.id)
        testitem2.cover = 2
        test1.propertyowner2s.remove(testitem1.id)
        self.dc2.unfreeze_dc_comms()
        self.assertEqual(len(test2.propertyowner2s), 0)
        self.assertEqual(len(test1.propertyowner2s), 0)


    def test_merging_changes_to_different_objects_in_the_same_doc_works(self):
        #Test merging changes to different objects in the same document works
        test1 = TestPropertyOwner1()
        self.dc1.add_document_object(test1)
        test1.covers = 1
        testitem1 = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem1)
        self.dc1.add_document_object(testitem1)
        testitem1.cover = 1
        self.dc2.freeze_dc_comms()
        test1.covers = 3
        test2 = self.dc2.get_object_by_id(TestPropertyOwner1.__name__, test1.id)
        testitem2 = test2.get_document_object(testitem1.id)
        testitem2.cover = 2
        self.dc2.unfreeze_dc_comms()
        self.assertEqual(test1.covers, 3)
        self.assertEqual(test2.covers, 3)
        self.assertEqual(len(test2.propertyowner2s), 1)
        self.assertEqual(len(test1.propertyowner2s), 1)
        for item1 in test2.propertyowner2s:
            self.assertEqual(item1.cover, 2)
        for item1 in test1.propertyowner2s:
            self.assertEqual(item1.cover, 2)

    def test_changing_objects_on_different_branches_works(self):
        #Test changing different objects on different branches works
        test1 = TestPropertyOwner1()
        self.dc1.add_document_object(test1)
        test1.covers = 1
        testitem1 = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem1)
        self.dc1.add_document_object(testitem1)
        testitem1.cover = 1
        self.dc2.freeze_dc_comms()
        test2 = self.dc2.get_object_by_id(TestPropertyOwner1.__name__, test1.id)
        testitem2 = test2.get_document_object(testitem1.id)
        testitem1.cover = 2
        testitem1.quantity = 3
        testitem2.cover = 3
        testitem2.quantity = 2
        self.assertEqual(testitem2.cover, 3)
        self.assertEqual(testitem2.quantity, 2)
        self.assertEqual(testitem1.cover, 2)
        self.assertEqual(testitem1.quantity, 3)
        self.dc2.unfreeze_dc_comms()

        self.assertEqual(testitem2.cover, 3)
        self.assertEqual(testitem2.quantity, 3)
        self.assertEqual(testitem1.cover, 3)
        self.assertEqual(testitem1.quantity, 3)

    def test_changing_objects_on_different_branches_works_reverse_order(self):
        #Test changing different objects on different branches works reverse merge of above
        test1 = TestPropertyOwner1()
        self.dc1.add_document_object(test1)
        testitem1 = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem1)
        self.dc1.add_document_object(testitem1)
        self.dc2.freeze_dc_comms()
        test2 = self.dc2.get_object_by_id(TestPropertyOwner1.__name__, test1.id)
        testitem2 = test2.get_document_object(testitem1.id)
        testitem1.cover = 3
        testitem1.quantity = 2
        testitem2.cover = 2
        testitem2.quantity = 3
        self.dc2.unfreeze_dc_comms()

        self.assertEqual(testitem2.cover, 3)
        self.assertEqual(testitem2.quantity, 3)
        self.assertEqual(testitem1.cover, 3)
        self.assertEqual(testitem1.quantity, 3)


class Comments(Document):
    comment = fields.CharRegister()

class MergeHistoryCommentTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(Comments)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(Comments)

    def test_merge_text_register_objects(self):
        #Test merge together two simple Comment objects
        test1 = Comments()
        self.dc1.add_document_object(test1)
        test1.comment = "AAA"
        test2 = self.dc2.get_object_by_id(Comments.__name__, test1.id)
        self.dc2.freeze_dc_comms()
        test1.comment = "BBB"
        test2.comment = "CCC"
        self.dc2.unfreeze_dc_comms()
        #In a merge conflict between two string the one that is sooner in alphabetical order is the winner
        self.assertEqual(test1.comment, "CCC")
        self.assertEqual(test2.comment, "CCC")


    def test_merge_text_register_objects_reverse_order(self):
        #Test merge together two simple Comment objects
        test1 = Comments()
        self.dc1.add_document_object(test1)
        test1.comment = "AAA"
        test2 = self.dc2.get_object_by_id(Comments.__name__, test1.id)
        self.dc2.freeze_dc_comms()
        test1.comment = "CCC"
        test2.comment = "BBB"
        self.dc2.unfreeze_dc_comms()
        #In a merge conflict between two string the one that is sooner in alphabetical order is the winner
        self.assertEqual(test1.comment, "CCC")
        self.assertEqual(test2.comment, "CCC")


class StoreObjectsInJSONTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(TestPropertyOwner1)
        self.dc1.register(TestPropertyOwner2)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(TestPropertyOwner1)
        self.dc2.register(TestPropertyOwner2)

    def runTest(self):
        # Generate a complex historygraph with a merge to make this test more testing on the software
        test1 = TestPropertyOwner1()
        self.dc1.add_document_object(test1)
        test1.covers = 1
        testitem1 = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem1)
        self.dc1.add_document_object(testitem1)
        testitem1.cover = 1
        self.dc2.freeze_dc_comms()
        test2 = self.dc2.get_object_by_id(TestPropertyOwner1.__name__, test1.id)
        testitem2 = test2.get_document_object(testitem1.id)
        testitem1.cover = 2
        testitem1.quantity = 3
        testitem2.cover = 3
        testitem2.quantity = 2
        self.assertEqual(testitem2.cover, 3)
        self.assertEqual(testitem2.quantity, 2)
        self.assertEqual(testitem1.cover, 2)
        self.assertEqual(testitem1.quantity, 3)
        self.dc2.unfreeze_dc_comms()

        self.assertEqual(testitem2.cover, 3)
        self.assertEqual(testitem2.quantity, 3)
        self.assertEqual(testitem1.cover, 3)
        self.assertEqual(testitem1.quantity, 3)

        jsontext = self.dc1.as_json()
        dc3 = DocumentCollection(str(uuid.uuid4()))
        dc3.register(TestPropertyOwner1)
        dc3.register(TestPropertyOwner2)
        dc3.load_from_json(jsontext)
        test1s = dc3.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        test3 = test1s[0]
        test3id = test3.id
        self.assertEqual(len(test3.propertyowner2s), 1)
        for testitem3 in test3.propertyowner2s:
            self.assertEqual(testitem3.id, testitem1.id)
            self.assertEqual(testitem3.cover, 3)
        self.assertEqual(test3.covers, 1)


class MergeChangesMadeInJSONTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(TestPropertyOwner1)
        self.dc1.register(TestPropertyOwner2)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(TestPropertyOwner1)
        self.dc2.register(TestPropertyOwner2)

    def runTest(self):
        # Generate a complex historygraph with a merge to make this test more testing on the software
        test1 = TestPropertyOwner1()
        self.dc1.add_document_object(test1)
        test1.covers = 1
        testitem1 = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem1)
        self.dc1.add_document_object(testitem1)
        testitem1.cover = 1
        self.dc2.freeze_dc_comms()
        test2 = self.dc2.get_object_by_id(TestPropertyOwner1.__name__, test1.id)
        testitem2 = test2.get_document_object(testitem1.id)
        testitem1.cover = 2
        testitem1.quantity = 3
        testitem2.cover = 3
        testitem2.quantity = 2
        self.assertEqual(testitem2.cover, 3)
        self.assertEqual(testitem2.quantity, 2)
        self.assertEqual(testitem1.cover, 2)
        self.assertEqual(testitem1.quantity, 3)
        self.dc2.unfreeze_dc_comms()

        self.assertEqual(testitem2.cover, 3)
        self.assertEqual(testitem2.quantity, 3)
        self.assertEqual(testitem1.cover, 3)
        self.assertEqual(testitem1.quantity, 3)

        jsontext = self.dc1.as_json()
        dc3 = DocumentCollection(str(uuid.uuid4()))
        dc3.register(TestPropertyOwner1)
        dc3.register(TestPropertyOwner2)
        dc3.load_from_json(jsontext)
        test1s = dc3.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        test3 = test1s[0]
        test3id = test3.id
        self.assertEqual(len(test3.propertyowner2s), 1)
        for testitem3 in test3.propertyowner2s:
            self.assertEqual(testitem3.id, testitem1.id)
            self.assertEqual(testitem3.cover, 3)
        self.assertEqual(test3.covers, 1)

        # Change the value then load everything back in via JSON
        test3.covers = 4
        testitem3.cover = 4
        jsontext = dc3.as_json()
        self.dc1.load_from_json(jsontext)

        self.assertEqual(test1.covers, 4)
        self.assertEqual(len(test1.propertyowner2s), 1)
        self.assertEqual(testitem1.cover, 4)


class MergeAdvancedChangesMadeInJSONTestCase(unittest.TestCase):
    #Similar to merge changes test but testing things such as out of order reception of edges
    #Orphaned edges and partially orphaned merge edges
    def setUp(self):
        self.dc = DocumentCollection(str(uuid.uuid4()))
        self.dc.register(TestPropertyOwner1)
        self.dc.register(TestPropertyOwner2)

    def runTest(self):
        #Create an object and set some values
        test1 = TestPropertyOwner1()
        self.dc.add_document_object(test1)
        test1id = test1.id
        testitem1 = TestPropertyOwner2()
        testitem1id = testitem1.id
        test1.propertyowner2s.add(testitem1)
        testitem1.cover = 3
        test1.covers=2

        self.dc.add_document_object(test1)

        olddc = self.dc

        #Simulate sending the object to another user via conversion to JSON and emailing
        jsontext = self.dc.as_json()

        #Simulate the other user (who received the email with the edges) getting the document and loading it into memory
        self.dc = DocumentCollection(str(uuid.uuid4()))
        self.dc.register(TestPropertyOwner1)
        self.dc.register(TestPropertyOwner2)
        self.dc.load_from_json(jsontext)
        tpo1s = self.dc.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(tpo1s), 1)
        test2 = tpo1s[0]

        self.assertEqual(len(test2.propertyowner2s), 1)

        #The second user makes some changes and sends them back to the first
        for testitem2 in test2.propertyowner2s:
            testitem2.cover = 4

        edge4 = test2.history.get_edges_by_end_node(test2._clockhash)

        test2.covers = 3

        edge3 = test2.history.get_edges_by_end_node(test2._clockhash)

        #Simulate the first user received the second users changes out of order
        #the second edge is received first. Test it is right
        self.dc = olddc
        self.dc.load_from_json(JSONEncoder().encode({"history":[edge3.as_tuple()],"immutableobjects":[]}))
        test2s = self.dc.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test2s), 1)
        test2 = test2s[0]

        self.assertEqual(test2.covers, 2)
        for testitem2 in test2.propertyowner2s:
            self.assertEqual(testitem2.cover, 3)
        self.assertEqual(testitem2.cover, 3)

        #Simulate the first user received the second users changes out of order
        #the first edge is not received make sure everything
        self.dc.load_from_json(JSONEncoder().encode({"history":[edge4.as_tuple()],"immutableobjects":[]}))
        test2s = self.dc.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test2s), 1)

        test2 = test2s[0]

        self.assertEqual(test2.covers, 3)
        for testitem2 in test2.propertyowner2s:
            self.assertEqual(testitem2.cover, 4)
        self.assertEqual(testitem2.cover, 4)

        oldnode = test2._clockhash

        dummysha1 = hashlib.sha256('Invalid node 1'.encode('utf-8')).hexdigest()
        dummysha2 = hashlib.sha256('Invalid node 2'.encode('utf-8')).hexdigest()
        edgenull1 = edges.Merge({dummysha1, dummysha2}, "", "", "", "", test2.id, test2.__class__.__name__)
        edgenull2 = edges.Merge({test2._clockhash, edgenull1.get_end_node()}, "", "", "", "", test2.id, test2.__class__.__name__)

        self.dc.load_from_json(JSONEncoder().encode({"history":[edgenull2.as_tuple()],"immutableobjects":[]}))
        test2s = self.dc.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test2s), 1)
        test2 = test2s[0]

        self.assertEqual(oldnode, test2._clockhash)

        self.assertEqual(test2.covers, 3)
        for testitem2 in test2.propertyowner2s:
            self.assertEqual(testitem2.cover, 4)
        self.assertEqual(testitem2.cover, 4)

        self.dc.load_from_json(JSONEncoder().encode({"history":[edgenull1.as_tuple()],"immutableobjects":[]}))
        test2s = self.dc.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test2s), 1)
        test2 = test2s[0]

        self.assertEqual(oldnode, test2._clockhash)

        self.assertEqual(test2.covers, 3)
        for testitem2 in test2.propertyowner2s:
            self.assertEqual(testitem2.cover, 4)
        self.assertEqual(testitem2.cover, 4)


class LargeMergeTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(Covers)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(Covers)

    def runTest(self):
        test1 = Covers()
        self.dc1.add_document_object(test1)
        test1.covers = 1
        test2 = self.dc2.get_object_by_id(Covers.__name__, test1.id)
        self.dc2.freeze_dc_comms()

        for i in range(2,52):
            test1.covers = i
        for i in range(52,102):
            test2.covers = i
        #self.dc2.unfreeze_dc_comms()
        time_taken = timeit.timeit(self.dc2.unfreeze_dc_comms, number=10)
        #print('LargeMergeTestCase time_taken=', time_taken, 'sec')
        # Once we unfreeze the updates should play
        self.assertEqual(test1.covers, 101)


class MessageTest(ImmutableObject):
    # A demo class of an immutable object. It emulated a simple text message broadcast at a certain time
    # similar to a tweet
    messagetime = fields.IntRegister() # The time in epoch milliseconds of the message
    text = fields.CharRegister() # The text of the message

class ImmutableClassTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection(str(uuid.uuid4()))
        self.dc.register(MessageTest)

    def test_cant_mutate(self):
        t = int(round(time.time() * 1000))
        m = MessageTest(messagetime=t, text="Hello")
        self.assertEqual(m.messagetime, t)
        self.assertEqual(m.text, "Hello")

        was_exception = False
        with self.assertRaises(AssertionError):
            m.messagetime = int(round(time.time() * 1000))

    def test_triggers_a_listener_when_added_to_dc(self):
        result = defaultdict(int)
        class TestListener(object):
            def document_object_added(self, dc, obj):
                pass
            def immutable_object_added(self, dc, obj):
                result['immutable_object_added'] += 1
            def edges_added(self, dc, edges):
                pass
        self.dc.add_listener(TestListener())
        self.assertEqual(result['immutable_object_added'], 0)

        t = int(round(time.time() * 1000))
        m = MessageTest(messagetime=t, text="Hello")
        self.dc.add_immutable_object(m)

        self.assertEqual(result['immutable_object_added'], 1)


class StoreImmutableObjectsInJSONTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection(str(uuid.uuid4()))
        self.dc.register(MessageTest)

    def runTest(self):
        #Test writing the immutable object to an sql lite database
        t = int(round(time.time() * 1000))
        m = MessageTest(messagetime=t, text="Hello")
        self.dc.add_immutable_object(m)
        test1id = m.get_hash()

        test1s = self.dc.get_by_class(MessageTest)
        self.assertEqual(len(test1s), 1)

        jsontext = self.dc.as_json()

        self.dc = DocumentCollection(str(uuid.uuid4()))
        self.dc.register(MessageTest)
        self.dc.load_from_json(jsontext)
        test1s = self.dc.get_by_class(MessageTest)
        self.assertEqual(len(test1s), 1)
        test1 = test1s[0]
        self.assertEqual(test1id, test1.get_hash())


class TestUpdateHandler(object):
    #Handle update requests to us
    def WasChanged(self, source):
        self.covers = source.covers

class SimpleCoversUpdateTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection(str(uuid.uuid4()))
        self.dc.register(Covers)

    def runTest(self):
        #Test merging together simple covers documents
        test = Covers()
        self.dc.add_document_object(test)
        test.covers = 1
        handler = TestUpdateHandler()
        test.add_handler(handler.WasChanged)
        self.assertEqual(len(test.change_handlers), 1)
        test.covers = 2
        self.assertEqual(handler.covers, 2)
        test.remove_handler(handler.WasChanged)
        self.assertEqual(len(test.change_handlers), 0)
        test.covers = 3
        self.assertEqual(handler.covers, 2)


class SimpleCounterTestCase(unittest.TestCase):
    def runTest(self):
        dc1 = DocumentCollection(str(uuid.uuid4()))
        dc1.register(CounterTestContainer)
        #Test merging together simple counter documents
        test = CounterTestContainer()
        #Test we default to zero
        self.assertEqual(test.testcounter.get(), 0)
        #Test adding and subtract gives reasonable values
        test.dc = dc1
        test.testcounter.add(1)
        self.assertEqual(test.testcounter.get(), 1)
        test.testcounter.add(1)
        self.assertEqual(test.testcounter.get(), 2)
        test.testcounter.subtract(1)
        self.assertEqual(test.testcounter.get(), 1)

class MergeCounterTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(CounterTestContainer)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(CounterTestContainer)

    def runTest(self):
        #Test merge together two simple covers objects
        test1 = CounterTestContainer()
        self.dc1.add_document_object(test1)
        test1.testcounter.add(1)
        self.assertEqual(test1.testcounter.get(), 1)
        test2 = self.dc2.get_object_by_id(CounterTestContainer.__name__, test1.id)
        self.dc2.freeze_dc_comms()
        test1.testcounter.subtract(1)
        test2.testcounter.add(1)
        self.dc2.unfreeze_dc_comms()
        self.assertEqual(test1.testcounter.get(), 1)
        self.assertEqual(test2.testcounter.get(), 1)


class UncleanReplayCounterTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection(str(uuid.uuid4()))

    def runTest(self):
        #Test merge together two simple covers objects
        test = CounterTestContainer()
        test.dc = self.dc
        test.testcounter.add(1)
        self.assertEqual(test.testcounter.get(), 1)
        history2 = test.history.clone()
        history2.replay(test)
        self.assertEqual(test.testcounter.get(), 1)


class MergeCounterChangesMadeInJSONTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection(str(uuid.uuid4()))
        self.dc.register(CounterTestContainer)

    def runTest(self):
        #Create an object and set some values
        test1 = CounterTestContainer()
        test1id = test1.id

        self.dc.add_document_object(test1)
        test1.testcounter.add(1)
        self.assertEqual(test1.testcounter.get(), 1)

        olddc = self.dc

        sharedhashclock = test1._clockhash
        #Simulate sending the object to another user via conversion to JSON and emailing
        jsontext = self.dc.as_json()

        #Simulate making local conflicting changes
        test1.testcounter.subtract(1)
        self.assertEqual(test1.testcounter.get(), 0)

        #Simulate the other user (who received the email with the edges) getting the document and loading it into memory
        self.dc = DocumentCollection(str(uuid.uuid4()))
        self.dc.register(CounterTestContainer)
        self.dc.load_from_json(jsontext)
        self.assertEqual(jsontext, self.dc.as_json())
        tpo1s = self.dc.get_by_class(CounterTestContainer)
        self.assertEqual(len(tpo1s), 1)
        test2 = tpo1s[0]

        self.assertEqual(sharedhashclock, test2._clockhash)
        #The second user makes some changes and sends them back to the first
        test2.testcounter.add(1)
        self.assertEqual(test2.testcounter.get(), 2)

        edgenext = test2.history.get_edges_by_end_node(test2._clockhash)


        #Simulate the first user received the second users changes out of order
        #the second edge is received first. Test it is right
        self.dc = olddc
        self.dc.load_from_json(JSONEncoder().encode({"history":[edgenext.as_tuple()],"immutableobjects":[]}))
        test2s = self.dc.get_by_class(CounterTestContainer)
        self.assertEqual(len(test2s), 1)
        test2 = test2s[0]

        self.assertEqual(test2.testcounter.get(), 1)

class HistoryGraphDepthTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(Covers)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(Covers)

    def test_depth_simple_case(self):
        test1 = Covers()
        self.dc1.add_document_object(test1)
        #Test there are no edges in the object just created
        self.assertEqual(test1.depth(), 0)

        #Test just adding edge very simply
        test1.covers = 1
        self.assertEqual(test1.depth(), 1)

        test1.covers = 2

        self.assertEqual(test1.depth(), 2)

        test2 = self.dc2.get_object_by_id(Covers.__name__, test1.id)
        self.dc2.freeze_dc_comms()

        self.assertEqual(test2.depth(), 2)

        test2.covers = 3

        self.assertEqual(test1.depth(), 2)
        self.assertEqual(test2.depth(), 3)

        #Test merging back together simply
        self.dc2.unfreeze_dc_comms()

        self.assertEqual(test1.depth(), 3)
        self.assertEqual(test2.depth(), 3)

    def test_depth_conflicting_merge(self):

        test1 = Covers()
        self.dc1.add_document_object(test1)
        #Test there are no edges in the object just created
        self.assertEqual(test1.depth(), 0)

        #Test just adding edge very simply
        test1.covers = 1
        self.assertEqual(test1.depth(), 1)

        test1.covers = 2

        self.assertEqual(test1.depth(), 2)

        test2 = self.dc2.get_object_by_id(Covers.__name__, test1.id)
        self.dc2.freeze_dc_comms()

        self.assertEqual(test2.depth(), 2)

        test1.covers = 3
        test2.covers = 4

        self.assertEqual(test1.depth(), 3)
        self.assertEqual(test2.depth(), 3)

        #Test merging back together simply
        self.dc2.unfreeze_dc_comms()

        # The merge should have resulted in another edge being added
        # the merge edge
        self.assertEqual(test1.depth(), 4)
        self.assertEqual(test2.depth(), 4)


class FieldListFunctionsTestCase(unittest.TestCase):
    # Test each individual function in the fields.List and FieldListImpl classes
    def runTest(self):
        dc1 = DocumentCollection(str(uuid.uuid4()))
        dc1.register(TestPropertyOwner1)

        fl = fields.List(TestPropertyOwner1)
        self.assertEqual(fl.theclass, TestPropertyOwner1)

        parent = uuid.uuid4()
        name = uuid.uuid4()
        flImpl = fl.create_instance(parent, name)
        self.assertEqual(flImpl.theclass, TestPropertyOwner1)
        self.assertEqual(flImpl.parent, parent)
        self.assertEqual(flImpl.name, name)

        self.assertEqual(len(flImpl), 0)
        with self.assertRaises(IndexError):
            flImpl[0]

        parent = TestPropertyOwner1()
        parent.dc = dc1
        name = "test"
        flImpl = fl.create_instance(parent, name)
        test1 = TestPropertyOwner1()
        self.assertEqual(parent.depth(), 0)
        flImpl.insert(0, test1)
        self.assertEqual(parent.depth(), 1)
        self.assertFalse(hasattr(flImpl, "_rendered_list"))
        self.assertEqual(len(flImpl), 1)
        self.assertEqual(flImpl[0].id, test1.id)

        self.assertEqual(len(flImpl._listnodes), 1) # A single addition should have been added for this

        test2 = TestPropertyOwner1()
        flImpl.insert(1, test2)
        self.assertEqual(parent.depth(), 2)
        self.assertEqual(len(flImpl), 2)
        self.assertEqual(flImpl[0].id, test1.id)
        self.assertEqual(flImpl[1].id, test2.id)

        test3 = TestPropertyOwner1()
        flImpl.insert(0, test3)
        self.assertEqual(parent.depth(), 3)
        self.assertEqual(len(flImpl), 3)
        self.assertEqual(flImpl[0].id, test3.id)
        self.assertEqual(flImpl[1].id, test1.id)
        self.assertEqual(flImpl[2].id, test2.id)

        flImpl.remove(1)
        self.assertEqual(parent.depth(), 4)
        self.assertEqual(len(flImpl), 2)
        self.assertEqual(flImpl[0].id, test3.id)
        self.assertEqual(flImpl[1].id, test2.id)

        #Test iteration
        l = list()
        for n in flImpl:
            l.append(n)
        self.assertEqual(flImpl[0].id, l[0].id)
        self.assertEqual(flImpl[1].id, l[1].id)

        flImpl.clean()
        self.assertEqual(len(flImpl._listnodes), 0)
        self.assertEqual(len(flImpl._tombstones), 0)
        self.assertFalse(hasattr(flImpl, "_rendered_list"))


class FieldListMergeTestCase(unittest.TestCase):
    # Test each individual function in the fields.List and FieldListImpl classes
    def runTest(self):
        dc = DocumentCollection(str(uuid.uuid4()))
        dc.register(TestFieldListOwner1)
        dc.register(TestFieldListOwner2)
        test1 = TestFieldListOwner1()
        l0 = TestFieldListOwner2()
        l1 = TestFieldListOwner2()
        test1.propertyowner2s.insert(0, l0)
        test1.propertyowner2s.insert(1, l1)

        test2 = test1.clone()
        dc.add_document_object(test2)

        l2 = TestFieldListOwner2()
        test2.propertyowner2s.insert(2, l2)

        test1.propertyowner2s.remove(1)

        test3 = test2.merge(test1)

        self.assertEqual(len(test3.propertyowner2s), 2)
        self.assertEqual(test3.propertyowner2s[0].id, l0.id)
        self.assertEqual(test3.propertyowner2s[1].id, l2.id)


class TestListofLists3(DocumentObject):
    comment = fields.CharRegister()

class TestListofLists2(DocumentObject):
    cover = fields.IntRegister()
    quantity = fields.IntRegister()
    propertyowner2s = fields.List(TestListofLists3)

class TestListofLists1(Document):
    covers = fields.IntRegister()
    propertyowner2s = fields.List(TestListofLists2)


class FieldListMergeTestCase(unittest.TestCase):
    def setUp(self):
        self.dc1 = DocumentCollection(str(uuid.uuid4()))
        self.dc1.register(TestListofLists1)
        self.dc1.register(TestListofLists2)
        self.dc1.register(TestListofLists3)
        self.dc2 = DocumentCollection(str(uuid.uuid4()), master=self.dc1)
        self.dc2.register(TestListofLists1)
        self.dc2.register(TestListofLists2)
        self.dc2.register(TestListofLists3)

    # Test each individual function in the fields.List and FieldListImpl classes
    def runTest(self):
        test1 = TestListofLists1()
        self.dc1.add_document_object(test1)
        l0 = TestListofLists2()
        l1 = TestListofLists2()
        test1.propertyowner2s.insert(0, l0)
        self.dc1.add_document_object(l0)
        test1.propertyowner2s.insert(1, l1)
        self.dc1.add_document_object(l1)

        ll0 = TestListofLists3()
        l0.propertyowner2s.insert(0, ll0)
        self.dc1.add_document_object(ll0)

        assert test1.propertyowner2s[0].id == l0.id
        assert test1.propertyowner2s[1].id == l1.id
        assert test1.propertyowner2s[0].propertyowner2s[0].id == ll0.id
        self.assertEqual(len(test1.propertyowner2s[0].propertyowner2s), 1)
        assert test1.propertyowner2s[0].propertyowner2s[0].get_document().id == test1.id
        assert test1.propertyowner2s[0].get_document().id == test1.id

        test2 = self.dc2.get_object_by_id(TestListofLists1.__name__, test1.id)
        self.assertEqual(len(test2.propertyowner2s), 2)
        self.assertEqual(len(test1.propertyowner2s[0].propertyowner2s), 1)

        self.assertEqual(len(test2.propertyowner2s[0].propertyowner2s), 1)

        ll0.comment = 'Hello'

        assert test2.propertyowner2s[0].id == l0.id
        assert test2.propertyowner2s[1].id == l1.id
        assert test2.propertyowner2s[0].propertyowner2s[0].id == ll0.id
        self.assertEqual(len(test2.propertyowner2s[0].propertyowner2s), 1)
        assert test2.propertyowner2s[0].propertyowner2s[0].comment == 'Hello'
        assert test2.propertyowner2s[0].get_document().id == test1.id
        assert test2.propertyowner2s[0].propertyowner2s[0].get_document().id == test1.id
        self.assertEqual(len(test2.propertyowner2s[0].propertyowner2s), 1)

        test1.propertyowner2s[0].propertyowner2s.remove(0)
        self.assertEqual(len(test1.propertyowner2s[0].propertyowner2s), 0)

        assert test2.propertyowner2s[0].id == l0.id
        assert test2.propertyowner2s[1].id == l1.id
        self.assertEqual(len(test2.propertyowner2s[0].propertyowner2s), 0)

class TestColofCols3(DocumentObject):
    comment = fields.CharRegister()

class TestColofCol2(DocumentObject):
    cover = fields.IntRegister()
    quantity = fields.IntRegister()
    propertyowner2s = fields.Collection(TestColofCols3)

class TestColofCol1(Document):
    covers = fields.IntRegister()
    propertyowner2s = fields.Collection(TestColofCol2)


class FieldCollofCollMergeTestCase(unittest.TestCase):
    # Test each individual function in the fields.List and FieldListImpl classes
    def runTest(self):
        dc = DocumentCollection(str(uuid.uuid4()))
        dc.register(TestColofCol1)
        dc.register(TestColofCol2)
        dc.register(TestColofCols3)
        test1 = TestColofCol1()
        dc.add_document_object(test1)
        l0 = TestColofCol2()
        l1 = TestColofCol2()
        test1.propertyowner2s.add(l0)
        test1.propertyowner2s.add(l1)

        ll0 = TestColofCols3()
        l0.propertyowner2s.add(ll0)

        assert {l.id for l in test1.propertyowner2s} == {l0.id, l1.id}
        for l in test1.propertyowner2s:
            assert l.get_document().id == test1.id
            for l2 in l.propertyowner2s:
                assert l2.get_document().id == test1.id

        ll0.comment = 'Hello'

        dc2 = DocumentCollection(str(uuid.uuid4()))
        dc2.register(TestColofCol1)
        dc2.register(TestColofCol2)
        dc2.register(TestColofCols3)
        test2 = TestColofCol1(test1.id)
        dc2.add_document_object(test2)
        test1.history.replay(test2)

        assert {l.id for l in test1.propertyowner2s} == {l0.id, l1.id}
        for l in test1.propertyowner2s:
            assert l.get_document().id == test1.id
            for l2 in l.propertyowner2s:
                assert l2.get_document().id == test1.id
                assert l2.comment == 'Hello'

class DocumentCollectionCompulsoryTestCase(unittest.TestCase):
    # Test that we assert when we change Document or DocumentObject without adding to a DC
    def runTest(self):
        self.dc = DocumentCollection(str(uuid.uuid4()))
        self.dc.register(TestPropertyOwner1)
        self.dc.register(TestPropertyOwner2)

        # Test that if we add everything to the dc it all is OK
        test1 = TestPropertyOwner1()
        self.dc.add_document_object(test1)
        test1.covers = 1

        test2 = TestPropertyOwner2()
        test1.propertyowner2s.add(test2)
        test2.cover = 1

        # Test if we don't add the Document to the dc we get an assertion
        test3 = TestPropertyOwner1()
        with self.assertRaises(AssertionError):
            test3.covers = 1

# Code that is useful for running tests inside IDLE
#if __name__ == '__main__':
#    suite = unittest.TestLoader().loadTestsFromName( 'tests.AdvancedItemTestCase.test_changing_objects_on_different_branches_works' )
#    unittest.TextTestRunner(verbosity=2).run( suite )

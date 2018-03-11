# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

import unittest
from historygraph import DocumentCollection
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

class TestPropertyOwner2(DocumentObject):
    cover = fields.IntRegister()
    quantity = fields.IntRegister()

class TestPropertyOwner1(Document):
    covers = fields.IntRegister()
    propertyowner2s = fields.Collection(TestPropertyOwner2)
    def was_changed(self, changetype, propertyowner, propertyname, propertyvalue, propertytype):
        super(TestPropertyOwner1, self).was_changed(changetype, propertyowner, propertyname, propertyvalue, propertytype)
        self.bWasChanged = True

class Covers(Document):
    covers = fields.IntRegister()

class SimpleCoversTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(TestPropertyOwner1)
        self.dc.Register(TestPropertyOwner2)

    def runTest(self):
        #Test merging together simple covers documents
        test = Covers()
        test.covers = 1
        #Test we can set a value
        self.assertEqual(test.covers, 1)
        test2 = Covers(test.id)
        test.history.Replay(test2)
        #Test we can rebuild a simple object by playing an edge
        self.assertEqual(test2.covers, 1)
        #Test these are just the same history object but it was actually copied
        assert test.history is not test2.history
        
        test3 = test2.clone()
        #Test the clone is the same as the original. But not just refering to the same object
        self.assertEqual(test3.covers, test2.covers)
        assert test2 is not test3
        assert test2.history is not test3.history
        
        test = Covers()
        test.covers = 1
        test.covers = 2
        test2 = Covers(test.id)
        test.history.Replay(test2)
        self.assertEqual(test.covers, 2)
        assert test.history is not test2.history
        assert test is not test2
    

class MergeHistoryCoverTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()

    def runTest(self):
        #Test merge together two simple covers objects
        test = Covers()
        test.covers = 1
        test2 = test.clone()
        test.covers = 2
        test2.covers = 3
        test3 = test.merge(test2)
        #In a merge conflict between two integers the greater one is the winner
        self.assertEqual(test3.covers, 3)

class TestPropertyOwner2(DocumentObject):
    cover = fields.IntRegister()
    quantity = fields.IntRegister()

class TestPropertyOwner1(Document):
    covers = fields.IntRegister()
    propertyowner2s = fields.Collection(TestPropertyOwner2)
    def was_changed(self, changetype, propertyowner, propertyname, propertyvalue, propertytype):
        super(TestPropertyOwner1, self).was_changed(changetype, propertyowner, propertyname, propertyvalue, propertytype)
        self.bWasChanged = True

class MergeHistorySendEdgeCoverTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(Covers)

    def runTest(self):
        #Test merging together by receiving an edge
        test = Covers()
        test.covers = 1
        test2 = test.clone()
        test.covers = 2
        test2.covers = 3
        edge = test2.history.edgesbyendnode[test2._clockhash]
        history = test.history.Clone()
        history.AddEdges([edge])
        test3 = Covers(test.id)
        history.Replay(test3)
        #In a merge conflict between two integers the greater one is the winner
        self.assertEqual(test3.covers, 3)

        #Test the behaviour of receiving edges out of order
        test = Covers()
        test.covers = 1
        test2 = test.clone()
        test.covers = 2
        test5 = test2.clone()
        test6 = test2.clone()
        test2.covers = 3
        test2.covers = 4
        edge4 = test2.history.edgesbyendnode[test2._clockhash]
        edge3 = test2.history.edgesbyendnode[list(edge4._start_hashes)[0]]
        history = test.history.Clone()
        history.AddEdges([edge4])
        test3 = Covers(test.id)
        history.Replay(test3)
        #edge4 should be orphaned and not played
        self.assertEqual(test3.covers, 2)
        #Once edge3 is added we should replay automatically to 4
        history.AddEdges([edge3])
        test4 = Covers(test.id)
        history.Replay(test4)
        #edge4 should be orphaned and not played
        self.assertEqual(test4.covers, 4)

        #Test live adding of edges
        test5.add_edges([edge3])
        self.assertEqual(test5.covers, 3)
        
        #Test live adding of orphaned edges
        test6.add_edges([edge4])
        self.assertEqual(test6.covers, 1)
        test6.add_edges([edge3])
        self.assertEqual(test6.covers, 4)

        #Test adding a Null edge where we don't  have one of the start nodes.
        #In the old way        
        dummysha = hashlib.sha256('Invalid node').hexdigest()
        history = test.history.Clone()
        edgenull = edges.Merge({test6._clockhash, dummysha}, "", "", "", "", test6.id, test6.__class__.__name__)
        history.AddEdges([edgenull])
        test6 = Covers(test.id)
        history.Replay(test6)
        self.assertEqual(test6.covers, 2)

        #In the new way
        test6 = test.clone()
        oldnode = test6._clockhash
        edgenull = edges.Merge({test6._clockhash, dummysha}, "", "", "", "", test6.id, test6.__class__.__name__)
        test6.add_edges([edgenull])
        self.assertEqual(test6.covers, 2)
        self.assertEqual(test6._clockhash, oldnode)
        

class ListItemChangeHistoryTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()

    def runTest(self):
        #Test that various types of changes create was changed events
        test1 = TestPropertyOwner1()
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
        self.dc = DocumentCollection()
        self.dc.Register(TestPropertyOwner1)
        self.dc.Register(TestPropertyOwner2)

    def runTest(self):
        test1 = TestPropertyOwner1()
        testitem = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem)
        testitem.cover = 1
        #Test semantics for retriving objects
        self.assertEqual(len(test1.propertyowner2s), 1)
        for po2 in test1.propertyowner2s:
            self.assertEqual(po2.__class__.__name__ , TestPropertyOwner2.__name__)
            self.assertEqual(po2.cover, 1)

        test1 = TestPropertyOwner1()
        testitem = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem)
        testitem.cover = 1
        test1.propertyowner2s.remove(testitem.id)

        dc2 = DocumentCollection()
        dc2.Register(TestPropertyOwner1)
        dc2.Register(TestPropertyOwner2)
        test2 = TestPropertyOwner1(test1.id)
        dc2.AddDocumentObject(test2)
        test1.history.Replay(test2)

        #Check that replaying correctly removes the object
        self.assertEqual(len(test2.propertyowner2s), 0)

        test1 = TestPropertyOwner1()
        testitem = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem)
        testitem.cover = 1
        test2 = test1.clone()
        
        self.assertEqual(len(test2.propertyowner2s), 1)
        for po2 in test2.propertyowner2s:
            self.assertEqual(po2.__class__.__name__, TestPropertyOwner2.__name__)
            self.assertEqual(po2.cover, 1)

class AdvancedItemTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(TestPropertyOwner1)
        self.dc.Register(TestPropertyOwner2)

    def runTest(self):
        #Test changing them deleting a sub element
        test1 = TestPropertyOwner1()
        self.dc.AddDocumentObject(test1)
        testitem1 = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem1)
        testitem1.cover = 1
        test2 = test1.clone()
        testitem2 = test2.get_document_object(testitem1.id)
        testitem2.cover = 2
        test2.propertyowner2s.remove(testitem2.id)
        test3 = test1.merge(test2)
        self.assertEqual(len(test3.propertyowner2s), 0)

        #Test changing them deleting a sub element. Test merging in the opposition order to previous test
        test1 = TestPropertyOwner1()
        self.dc.AddDocumentObject(test1)
        testitem1 = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem1)
        testitem1.cover = 1
        test2 = test1.clone()
        testitem2 = test2.get_document_object(testitem1.id)
        testitem2.cover = 2
        test2.propertyowner2s.remove(testitem2.id)
        test3 = test2.merge(test1)
        self.assertEqual(len(test3.propertyowner2s), 0)

        #Test merging changes to different objects in the same document works
        test1 = TestPropertyOwner1()
        self.dc.AddDocumentObject(test1)
        testitem1 = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem1)
        test2 = test1.clone()
        testitem1.cover = 3
        test2.covers=2
        test3 = test2.merge(test1)
        self.assertEqual(len(test3.propertyowner2s), 1)
        for item1 in test3.propertyowner2s:
            self.assertEqual(item1.cover, 3)
        self.assertEqual(test3.covers, 2)

        #Test changing different objects on different branches works
        test1 = TestPropertyOwner1()
        self.dc.AddDocumentObject(test1)
        testitem1 = TestPropertyOwner2()
        id1 = testitem1.id
        test1.propertyowner2s.add(testitem1)
        testitem2 = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem2)
        id2 = testitem2.id
        test2 = test1.clone()
        testitem2 = test2.get_document_object(id2)
        testitem1.cover = 2
        testitem1.quantity = 3
        testitem2.cover = 3
        testitem2.quantity = 2
        test3 = test2.merge(test1)
        testitem1 = test3.get_document_object(id1)
        testitem2 = test3.get_document_object(id2)
        self.assertEqual(testitem2.cover, 3)
        self.assertEqual(testitem2.quantity, 2)
        self.assertEqual(testitem1.cover, 2)
        self.assertEqual(testitem1.quantity, 3)
        
        #Test changing different objects on different branches works reverse merge of above
        test1 = TestPropertyOwner1()
        self.dc.AddDocumentObject(test1)
        testitem1 = TestPropertyOwner2()
        id1 = testitem1.id
        test1.propertyowner2s.add(testitem1)
        testitem2 = TestPropertyOwner2()
        test1.propertyowner2s.add(testitem2)
        id2 = testitem2.id
        test2 = test1.clone()
        testitem2 = test2.get_document_object(id2)
        testitem1.cover = 2
        testitem1.quantity = 3
        testitem2.cover = 3
        testitem2.quantity = 2
        test3 = test1.merge(test2)
        testitem1 = test3.get_document_object(id1)
        testitem2 = test3.get_document_object(id2)
        self.assertEqual(testitem2.cover, 3)
        self.assertEqual(testitem2.quantity, 2)
        self.assertEqual(testitem1.cover, 2)
        self.assertEqual(testitem1.quantity, 3)
    
class Comments(Document):
    comment = fields.CharRegister()

class MergeHistoryCommentTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(TestPropertyOwner1)
        self.dc.Register(TestPropertyOwner2)

    def runTest(self):
        #Test merge together two simple covers objects
        test = Comments()
        test.comment = "AAA"
        test2 = test.clone()
        test.comment = "BBB"
        test2.comment = "CCC"
        test3 = test.merge(test2)
        #In a merge conflict between two string the one that is sooner in alphabetical order is the winner
        self.assertEqual(test3.comment, "CCC")

        #Test merge together two simple covers objects
        test = Comments()
        test.comment = "AAA"
        test2 = test.clone()
        test.comment = "CCC"
        test2.comment = "BBB"
        test3 = test.merge(test2)
        #In a merge conflict between two string the one that is sooner in alphabetical order is the winner
        self.assertEqual(test3.comment, "CCC")

class StoreObjectsInJSONTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(TestPropertyOwner1)
        self.dc.Register(TestPropertyOwner2)

    def runTest(self):
        #Test writing the history to a sql lite database
        test1 = TestPropertyOwner1()
        self.dc.AddDocumentObject(test1)
        test1id = test1.id
        testitem1 = TestPropertyOwner2()
        testitem1id = testitem1.id
        test1.propertyowner2s.add(testitem1)
        test2 = test1.clone()
        testitem1.cover = 3
        test2.covers=2        
        self.assertEqual(len(test1.propertyowner2s), 1)

        test3 = test2.merge(test1)
        self.assertEqual(len(test3.propertyowner2s), 1)
        for item1 in test3.propertyowner2s:
            self.assertEqual(item1.cover, 3)
        self.assertEqual(test3.covers, 2)
        self.dc.AddDocumentObject(test3)

        test1s = self.dc.GetByClass(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)

        jsontext = self.dc.asJSON()
        self.dc = DocumentCollection()
        self.dc.Register(TestPropertyOwner1)
        self.dc.Register(TestPropertyOwner2)
        self.dc.LoadFromJSON(jsontext)
        test1s = self.dc.GetByClass(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        test1 = test1s[0]
        test1id = test1.id
        self.assertEqual(len(test1.propertyowner2s), 1)
        for testitem1 in test3.propertyowner2s:
            self.assertEqual(testitem1id, testitem1.id)
            self.assertEqual(testitem1.cover, 3)
        self.assertEqual(test1.covers, 2)
    
class MergeChangesMadeInJSONTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(TestPropertyOwner1)
        self.dc.Register(TestPropertyOwner2)

    def runTest(self):
        #Create an object and set some values
        test1 = TestPropertyOwner1()
        self.dc.AddDocumentObject(test1)
        test1id = test1.id
        testitem1 = TestPropertyOwner2()
        testitem1id = testitem1.id
        test1.propertyowner2s.add(testitem1)
        testitem1.cover = 3
        test1.covers=2        

        self.dc.AddDocumentObject(test1)

        #Simulate sending the object to another user via conversion to JSON and emailing
        jsontext = self.dc.asJSON()

        #Make some local changes
        test1.covers = 4

        #Simulate the other user (who received the email with the edges) getting the document and loading it into memory
        self.dc = DocumentCollection()
        self.dc.Register(TestPropertyOwner1)
        self.dc.Register(TestPropertyOwner2)
        self.dc.LoadFromJSON(jsontext)
        tpo1s = self.dc.GetByClass(TestPropertyOwner1)
        self.assertEqual(len(tpo1s), 1)
        test2 = tpo1s[0]

        self.assertEqual(len(test2.propertyowner2s), 1)

        #The second user makes some changes and sends them back to the first
        for testitem2 in test2.propertyowner2s:
            testitem2.cover = 4

        test2.covers = 3
        
        jsontext = self.dc.asJSON()
        
        #Simulate the first user received the second users changes
        self.dc = DocumentCollection()
        self.dc.Register(TestPropertyOwner1)
        self.dc.Register(TestPropertyOwner2)
        self.dc.LoadFromJSON(jsontext)
        test2s = self.dc.GetByClass(TestPropertyOwner1)
        self.assertEqual(len(test2s), 1)
        test2 = test2s[0]

        self.assertEqual(test2.covers, 3)
        for testitem2 in test2.propertyowner2s:
            self.assertEqual(testitem2.cover, 4)
        self.assertEqual(testitem2.cover, 4)
         
        #The first user merges the changes back with his own
        test3 = test2.merge(test1)
        self.assertEqual(len(test3.propertyowner2s), 1)
        for testitem3 in test3.propertyowner2s:
            self.assertEqual(testitem3.cover, 4)
        self.assertEqual(test3.covers, 4)

    
class MergeAdvancedChangesMadeInJSONTestCase(unittest.TestCase):
    #Similar to merge changes test but testing things such as out of order reception of edges
    #Orphaned edges and partially orphaned merge edges
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(TestPropertyOwner1)
        self.dc.Register(TestPropertyOwner2)

    def runTest(self):
        #Create an object and set some values
        test1 = TestPropertyOwner1()
        test1id = test1.id
        testitem1 = TestPropertyOwner2()
        testitem1id = testitem1.id
        test1.propertyowner2s.add(testitem1)
        testitem1.cover = 3
        test1.covers=2        

        self.dc.AddDocumentObject(test1)

        olddc = self.dc

        #Simulate sending the object to another user via conversion to JSON and emailing
        jsontext = self.dc.asJSON()

        #Simulate the other user (who received the email with the edges) getting the document and loading it into memory
        self.dc = DocumentCollection()
        self.dc.Register(TestPropertyOwner1)
        self.dc.Register(TestPropertyOwner2)
        self.dc.LoadFromJSON(jsontext)
        tpo1s = self.dc.GetByClass(TestPropertyOwner1)
        self.assertEqual(len(tpo1s), 1)
        test2 = tpo1s[0]

        self.assertEqual(len(test2.propertyowner2s), 1)

        #The second user makes some changes and sends them back to the first
        for testitem2 in test2.propertyowner2s:
            testitem2.cover = 4

        edge4 = test2.history.edgesbyendnode[test2._clockhash]

        test2.covers = 3
        
        edge3 = test2.history.edgesbyendnode[test2._clockhash]

        #Simulate the first user received the second users changes out of order
        #the second edge is received first. Test it is right 
        self.dc = olddc
        self.dc.LoadFromJSON(JSONEncoder().encode({"history":[edge3.as_tuple()],"immutableobjects":[]}))
        test2s = self.dc.GetByClass(TestPropertyOwner1)
        self.assertEqual(len(test2s), 1)
        test2 = test2s[0]

        self.assertEqual(test2.covers, 2)
        for testitem2 in test2.propertyowner2s:
            self.assertEqual(testitem2.cover, 3)
        self.assertEqual(testitem2.cover, 3)
         
        #Simulate the first user received the second users changes out of order
        #the first edge is not received make sure everything 
        self.dc.LoadFromJSON(JSONEncoder().encode({"history":[edge4.as_tuple()],"immutableobjects":[]}))
        test2s = self.dc.GetByClass(TestPropertyOwner1)
        self.assertEqual(len(test2s), 1)

        test2 = test2s[0]

        self.assertEqual(test2.covers, 3)
        for testitem2 in test2.propertyowner2s:
            self.assertEqual(testitem2.cover, 4)
        self.assertEqual(testitem2.cover, 4)

        oldnode = test2._clockhash         

        dummysha1 = hashlib.sha256('Invalid node 1').hexdigest()
        dummysha2 = hashlib.sha256('Invalid node 2').hexdigest()
        edgenull1 = edges.Merge({dummysha1, dummysha2}, "", "", "", "", test2.id, test2.__class__.__name__)
        edgenull2 = edges.Merge({test2._clockhash, edgenull1.get_end_node()}, "", "", "", "", test2.id, test2.__class__.__name__)

        self.dc.LoadFromJSON(JSONEncoder().encode({"history":[edgenull2.as_tuple()],"immutableobjects":[]}))
        test2s = self.dc.GetByClass(TestPropertyOwner1)
        self.assertEqual(len(test2s), 1)
        test2 = test2s[0]

        self.assertEqual(oldnode, test2._clockhash)

        self.assertEqual(test2.covers, 3)
        for testitem2 in test2.propertyowner2s:
            self.assertEqual(testitem2.cover, 4)
        self.assertEqual(testitem2.cover, 4)

        self.dc.LoadFromJSON(JSONEncoder().encode({"history":[edgenull1.as_tuple()],"immutableobjects":[]}))
        test2s = self.dc.GetByClass(TestPropertyOwner1)
        self.assertEqual(len(test2s), 1)
        test2 = test2s[0]

        self.assertEqual(oldnode, test2._clockhash)

        self.assertEqual(test2.covers, 3)
        for testitem2 in test2.propertyowner2s:
            self.assertEqual(testitem2.cover, 4)
        self.assertEqual(testitem2.cover, 4)


class FreezeTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(Covers)

    def runTest(self):
        #Test merging together by receiving an edge
        test = Covers() 
        test.covers = 1
        test2 = test.clone()
        test.covers = 2
        test2.covers = 3
        test.freeze()
        edge = test2.history.edgesbyendnode[test2._clockhash]
        test.add_edges([edge])
        # Normally we would receive the edge and play it. The new edge would win the conflict and update the object but that shouldn't
        # happened because we are frozen
        self.assertEqual(test.covers, 2)
        # Once we unfreeze the updates should play
        test.unfreeze()
        self.assertFalse(test.history.HasDanglingEdges())
        self.assertEqual(test.covers, 3)

class FreezeThreeWayMergeTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(Covers)

    def runTest(self):
        #Test merging together by receiving an edge
        test = Covers()
        test.covers = 1
        test2 = test.clone()
        test3 = test.clone()
        test.covers = 2
        test2.covers = 3
        test3.covers = 4
        test.freeze()
        edge2 = test2.history.edgesbyendnode[test2._clockhash]
        edge3 = test3.history.edgesbyendnode[test3._clockhash]
        test.add_edges([edge2, edge3])
        # Normally we would receive the edge and play it. The new edge would win the conflict and update the object but that shouldn't
        # happened because we are frozen
        self.assertEqual(test.covers, 2)
        # Once we unfreeze the updates should play
        test.unfreeze()
        #print "test.id=",test.id
        self.assertFalse(test.history.HasDanglingEdges())
        self.assertEqual(test.covers, 4)

class LargeMergeTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(Covers)

    def runTest(self):
        #Test merging together performance by receiving large numbers of edges
        test = Covers()
        test.covers = 1
        test2 = test.clone()
        for i in range(2,52):
            test.covers = i
        for i in range(52,102):
            test2.covers = i
        # Perform this merge. This simulate databases that have been disconnected for a long time
        def wrapper(func, *args, **kwargs):
            def wrapped():
                return func(*args, **kwargs)
            return wrapped
        def test_add_edges(test, test2):
            test.add_edges([v for (k, v) in test2.history.edgesbyendnode.iteritems()])
        wrapped = wrapper(test_add_edges, test, test2)
        time_taken = timeit.timeit(wrapped, number=1)
        self.assertEqual(test.covers, 101)

class MessageTest(ImmutableObject):
    # A demo class of an immutable object. It emulated a simple text message broadcast at a certain time
    # similar to a tweet
    messagetime = fields.IntRegister() # The time in epoch milliseconds of the message
    text = fields.CharRegister() # The text of the message

class ImmutableClassTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(Covers)

    def runTest(self):
        t = int(round(time.time() * 1000))
        m = MessageTest(messagetime=t, text="Hello")
        self.assertEqual(m.messagetime, t)
        self.assertEqual(m.text, "Hello")
        
        was_exception = False
        with self.assertRaises(AssertionError):
            m.messagetime = int(round(time.time() * 1000))
            

class StoreImmutableObjectsInJSONTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(MessageTest)

    def runTest(self):
        #Test writing the immutable object to an sql lite database
        t = int(round(time.time() * 1000))
        m = MessageTest(messagetime=t, text="Hello")
        self.dc.AddImmutableObject(m)
        test1id = m.GetHash()

        test1s = self.dc.GetByClass(MessageTest)
        self.assertEqual(len(test1s), 1)

        jsontext = self.dc.asJSON()

        self.dc = DocumentCollection()
        self.dc.Register(MessageTest)
        self.dc.LoadFromJSON(jsontext)
        test1s = self.dc.GetByClass(MessageTest)
        self.assertEqual(len(test1s), 1)
        test1 = test1s[0]
        self.assertEqual(test1id, test1.GetHash())


class TestUpdateHandler(object):
    #Handle update requests to us
    def WasChanged(self, source):
        self.covers = source.covers
    
class SimpleCoversUpdateTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(TestPropertyOwner1)
        self.dc.Register(TestPropertyOwner2)

    def runTest(self):
        #Test merging together simple covers documents
        test = Covers()
        test.covers = 1
        handler = TestUpdateHandler()
        test.AddHandler(handler.WasChanged)
        self.assertEqual(len(test.change_handlers), 1)
        test.covers = 2
        self.assertEqual(handler.covers, 2)
        test.RemoveHandler(handler.WasChanged)
        self.assertEqual(len(test.change_handlers), 0)
        test.covers = 3
        self.assertEqual(handler.covers, 2)
    
class FreezeUpdateTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(Covers)

    def runTest(self):
        #Test merging together by receiving an edge
        test = Covers() 
        test.covers = 1

        test2 = test.clone()
        handler = TestUpdateHandler()
        test.AddHandler(handler.WasChanged)
        test.covers = 2
        test2.covers = 3
        test.freeze()
        self.assertEqual(handler.covers, 2)
        edge = test2.history.edgesbyendnode[test2._clockhash]
        test.add_edges([edge])
        # Normally we would receive the edge and play it. The new edge would win the conflict and update the object but that shouldn't
        # happened because we are frozen
        self.assertEqual(test.covers, 2)
        self.assertEqual(handler.covers, 2)
        # Once we unfreeze the updates should play
        test.unfreeze()
        self.assertFalse(test.history.HasDanglingEdges())
        self.assertEqual(test.covers, 3)
        self.assertEqual(handler.covers, 3)


class CounterTestContainer(Document):
    testcounter = fields.IntCounter()

class SimpleCounterTestCase(unittest.TestCase):
    def runTest(self):
        #Test merging together simple counter documents
        test = CounterTestContainer()
        #Test we default to zero
        self.assertEqual(test.testcounter.get(), 0)
        #Test adding and subtract gives reasonable values
        test.testcounter.add(1)
        self.assertEqual(test.testcounter.get(), 1)
        test.testcounter.add(1)
        self.assertEqual(test.testcounter.get(), 2)
        test.testcounter.subtract(1)
        self.assertEqual(test.testcounter.get(), 1)

class MergeCounterTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()

    def runTest(self):
        #Test merge together two simple covers objects
        test = CounterTestContainer()
        test.testcounter.add(1)
        self.assertEqual(test.testcounter.get(), 1)
        test2 = test.clone()
        test.testcounter.subtract(1)
        test2.testcounter.add(1)
        test3 = test.merge(test2)
        self.assertEqual(test3.testcounter.get(), 1)


class UncleanReplayCounterTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()

    def runTest(self):
        #Test merge together two simple covers objects
        test = CounterTestContainer()
        test.testcounter.add(1)
        self.assertEqual(test.testcounter.get(), 1)
        history2 = test.history.Clone()
        history2.Replay(test)
        self.assertEqual(test.testcounter.get(), 1)
        

class MergeCounterChangesMadeInJSONTestCase(unittest.TestCase):
    def setUp(self):
        self.dc = DocumentCollection()
        self.dc.Register(CounterTestContainer)

    def runTest(self):
        #Create an object and set some values
        test1 = CounterTestContainer()
        test1id = test1.id

        self.dc.AddDocumentObject(test1)
        test1.testcounter.add(1)
        self.assertEqual(test1.testcounter.get(), 1)

        olddc = self.dc

        sharedhashclock = test1._clockhash
        #Simulate sending the object to another user via conversion to JSON and emailing
        jsontext = self.dc.asJSON()

        #Simulate making local conflicting changes
        test1.testcounter.subtract(1)
        self.assertEqual(test1.testcounter.get(), 0)

        #Simulate the other user (who received the email with the edges) getting the document and loading it into memory
        self.dc = DocumentCollection()
        self.dc.Register(CounterTestContainer)
        self.dc.LoadFromJSON(jsontext)
        self.assertEqual(jsontext, self.dc.asJSON())
        tpo1s = self.dc.GetByClass(CounterTestContainer)
        self.assertEqual(len(tpo1s), 1)
        test2 = tpo1s[0]

        self.assertEqual(sharedhashclock, test2._clockhash)
        #The second user makes some changes and sends them back to the first
        test2.testcounter.add(1)
        self.assertEqual(test2.testcounter.get(), 2)

        edgenext = test2.history.edgesbyendnode[test2._clockhash]


        #Simulate the first user received the second users changes out of order
        #the second edge is received first. Test it is right 
        self.dc = olddc
        self.dc.LoadFromJSON(JSONEncoder().encode({"history":[edgenext.as_tuple()],"immutableobjects":[]}))
        test2s = self.dc.GetByClass(CounterTestContainer)
        self.assertEqual(len(test2s), 1)
        test2 = test2s[0]
        #print "test2 edges=",[str(edge) for edge in test2.history.GetAllEdges()]

        self.assertEqual(test2.testcounter.get(), 1)


class HistoryGraphDepthTestCase(unittest.TestCase):
    def runTest(self):
        test = Covers()
        #Test there are no edges in the object just created
        self.assertEqual(test.depth(), 0)

        #Test just adding edge very simply
        test.covers = 1
        self.assertEqual(test.depth(), 1)

        test.covers = 2

        self.assertEqual(test.depth(), 2)

        test2 = test.clone()

        self.assertEqual(test2.depth(), 2)

        test2.covers = 3

        self.assertEqual(test.depth(), 2)
        self.assertEqual(test2.depth(), 3)

        #Test merging back together simply
        test3 = test.merge(test2)

        self.assertEqual(test.depth(), 2)
        self.assertEqual(test2.depth(), 3)
        self.assertEqual(test3.depth(), 3)

        #Test with a conflicting merge
        test1 = None
        test2 = None
        test3 = None

        test = Covers()
        self.assertEqual(test.depth(), 0)
        test.covers = 1
        self.assertEqual(test.depth(), 1)

        test2 = test.clone()
        test2.covers = 3

        self.assertEqual(test.depth(), 1)
        self.assertEqual(test2.depth(), 2)

        test.covers = 4
        self.assertEqual(test.depth(), 2)
        test.covers = 5
        self.assertEqual(test.depth(), 3)
        self.assertEqual(test2.depth(), 2)

        #Test merging back together this time there is a conflict
        test3 = test2.merge(test)
        self.assertEqual(test3.covers, 5)
        self.assertEqual(test3.depth(), 4)
        self.assertTrue(test3.depth() > test2.depth())
        self.assertTrue(test3.depth() > test.depth())


class FieldListFunctionsTestCase(unittest.TestCase):
    # Test each individual function in the fields.List and FieldListImpl classes
    def runTest(self):
        fl = fields.List(TestPropertyOwner1)
        self.assertEqual(fl.theclass, TestPropertyOwner1)

        parent = uuid.uuid4()
        name = uuid.uuid4()
        flImpl = fl.CreateInstance(parent, name)
        self.assertEqual(flImpl.theclass, TestPropertyOwner1)
        self.assertEqual(flImpl.parent, parent)
        self.assertEqual(flImpl.name, name)

        self.assertEqual(len(flImpl), 0)
        with self.assertRaises(IndexError):
            flImpl[0]

        parent = TestPropertyOwner1()
        name = "test"
        flImpl = fl.CreateInstance(parent, name)
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
        
        flImpl.Clean()
        self.assertEqual(len(flImpl._listnodes), 0)
        self.assertEqual(len(flImpl._tombstones), 0)
        self.assertFalse(hasattr(flImpl, "_rendered_list"))


class TestFieldListOwner2(DocumentObject):
    cover = fields.IntRegister()
    quantity = fields.IntRegister()

class TestFieldListOwner1(Document):
    covers = fields.IntRegister()
    propertyowner2s = fields.List(TestFieldListOwner2)


class FieldListMergeTestCase(unittest.TestCase):
    # Test each individual function in the fields.List and FieldListImpl classes
    def runTest(self):
        dc = DocumentCollection()
        dc.Register(TestFieldListOwner1)
        dc.Register(TestFieldListOwner2)
        test1 = TestFieldListOwner1()
        l0 = TestFieldListOwner2()
        l1 = TestFieldListOwner2()
        test1.propertyowner2s.insert(0, l0)
        test1.propertyowner2s.insert(1, l1)

        test2 = test1.clone()
        dc.AddDocumentObject(test2)

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
    # Test each individual function in the fields.List and FieldListImpl classes
    def runTest(self):
        dc = DocumentCollection()
        dc.Register(TestListofLists1)
        dc.Register(TestListofLists2)
        dc.Register(TestListofLists3)
        test1 = TestListofLists1()
        dc.AddDocumentObject(test1)
        l0 = TestListofLists2()
        l1 = TestListofLists2()
        test1.propertyowner2s.insert(0, l0)
        test1.propertyowner2s.insert(1, l1)

        ll0 = TestListofLists3()
        l0.propertyowner2s.insert(0, ll0)

        assert test1.propertyowner2s[0].id == l0.id
        assert test1.propertyowner2s[1].id == l1.id
        assert test1.propertyowner2s[0].propertyowner2s[0].id == ll0.id
        assert test1.propertyowner2s[0].propertyowner2s[0].get_document().id == test1.id
        assert test1.propertyowner2s[0].get_document().id == test1.id

        ll0.comment = 'Hello'

        dc2 = DocumentCollection()
        dc2.Register(TestListofLists1)
        dc2.Register(TestListofLists2)
        dc2.Register(TestListofLists3)
        test2 = TestListofLists1(test1.id)
        dc2.AddDocumentObject(test2)
        test1.history.Replay(test2)

        assert test2.propertyowner2s[0].id == l0.id
        assert test2.propertyowner2s[1].id == l1.id
        assert test2.propertyowner2s[0].propertyowner2s[0].id == ll0.id
        assert test2.propertyowner2s[0].propertyowner2s[0].comment == 'Hello'
        assert test2.propertyowner2s[0].get_document().id == test1.id
        assert test2.propertyowner2s[0].propertyowner2s[0].get_document().id == test1.id

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
        dc = DocumentCollection()
        dc.Register(TestColofCol1)
        dc.Register(TestColofCol2)
        dc.Register(TestColofCols3)
        test1 = TestColofCol1()
        dc.AddDocumentObject(test1)
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

        dc2 = DocumentCollection()
        dc2.Register(TestColofCol1)
        dc2.Register(TestColofCol2)
        dc2.Register(TestColofCols3)
        test2 = TestColofCol1(test1.id)
        dc2.AddDocumentObject(test2)
        test1.history.Replay(test2)

        assert {l.id for l in test1.propertyowner2s} == {l0.id, l1.id}
        for l in test1.propertyowner2s:
            assert l.get_document().id == test1.id
            for l2 in l.propertyowner2s:
                assert l2.get_document().id == test1.id
                assert l2.comment == 'Hello'

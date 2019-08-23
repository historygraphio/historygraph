from __future__ import absolute_import, unicode_literals, print_function

import unittest
from .common import DocumentCollection, TestPropertyOwner1, TestPropertyOwner2
from historygraph import Document
from historygraph import fields
from historygraph import DocumentObject
import json
import uuid


class StoreObjectsInJSONEdgeReceivedOutofOrderTestCase(unittest.TestCase):
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

        #jsontext = self.dc1.as_json()
        edges = self.dc1.get_all_edges()[0]
        #print('StoreObjectsInJSONEdgeReceivedOutofOrderTestCase edges=', edges)
        first_edges = [edge for edge in edges if edge[4] == '' and edge[5] == '']
        later_edges = [edge for edge in edges if edge[4] != '' or edge[5] != '']
        #print('first_edges=', first_edges)
        #print('later_edges=', later_edges)

        dc3 = DocumentCollection(str(uuid.uuid4()))
        dc3.register(TestPropertyOwner1)
        dc3.register(TestPropertyOwner2)
        ##dc3.load_from_json(jsontext)
        dc3.load_from_json(json.dumps({'history': later_edges, 'immutableobjects': []}))
        dc3.load_from_json(json.dumps({'history': first_edges, 'immutableobjects': []}))
        #assert False
        test1s = dc3.get_by_class(TestPropertyOwner1)
        self.assertEqual(len(test1s), 1)
        test3 = test1s[0]
        test3id = test3.id
        self.assertEqual(len(test3.propertyowner2s), 1)
        for testitem3 in test3.propertyowner2s:
            self.assertEqual(testitem3.id, testitem1.id)
            self.assertEqual(testitem3.cover, 3)
        self.assertEqual(test3.covers, 1)

class StoreObjectsInJSONEdgeReceivedOutofOrderSpreadsheetTestCase(unittest.TestCase):
    # This test replications specific problems with the in browser test case example
    def test_spreadsheet(self):
        class SpreadsheetCell(DocumentObject):
            content = fields.CharRegister()

        class SpreadsheetColumn(DocumentObject):
            name = fields.CharRegister()
            cells = fields.List(SpreadsheetCell)

        class SpreadsheetShare(DocumentObject):
            email = fields.CharRegister()

        class Spreadsheet(Document):
            name = fields.CharRegister()
            columns = fields.List(SpreadsheetColumn)
            shares = fields.Collection(SpreadsheetShare)

        def CreateNewDocumentCollection(master=None):
            dc = DocumentCollection(str(uuid.uuid4()), master=master)
            dc.register(Spreadsheet)
            dc.register(SpreadsheetColumn)
            dc.register(SpreadsheetCell)
            dc.register(SpreadsheetShare)
            return dc

        dc1 = CreateNewDocumentCollection()
        spreadsheet1 = Spreadsheet()
        dc1.add_document_object(spreadsheet1)
        for i in range(5):
            col = SpreadsheetColumn()
            spreadsheet1.columns.append(col)
            dc1.add_document_object(col)
            for j in range(5):
                cell = SpreadsheetCell()
                col.cells.append(cell)
                dc1.add_document_object(cell)
                cell.content = '{}{}'.format('ABCDE'[i], j + 1)

        assert spreadsheet1.columns[1].cells[2].content == 'B3'

        edges = dc1.get_all_edges()[0]
        #print('StoreObjectsInJSONEdgeReceivedOutofOrderTestCase edges=', edges)
        first_edges = [edge for edge in edges if edge[4] == '' and edge[5] == '']
        later_edges = [edge for edge in edges if edge[4] != '' or edge[5] != '']
        dc2 = CreateNewDocumentCollection()

        dc2.load_from_json(json.dumps({'history': later_edges, 'immutableobjects': []}))
        dc2.load_from_json(json.dumps({'history': first_edges, 'immutableobjects': []}))

        assert len(dc2.get_by_class(Spreadsheet)) == 1

        spreadsheet2 = dc2.get_by_class(Spreadsheet)[0]
        #column = spreadsheet2.columns[1]
        #print('column.cells=', column.cells)
        assert spreadsheet2.columns[1].cells[2].content == 'B3'

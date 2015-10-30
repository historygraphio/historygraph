#This module handles storing all documents in the database (and reloading)
from collections import defaultdict
import sqlite3
from Document import Document
from HistoryEdgeSimpleProperty import HistoryEdgeSimpleProperty
from HistoryEdgeAddChild import HistoryEdgeAddChild
from HistoryEdgeRemoveChild import HistoryEdgeRemoveChild
from HistoryEdgeNull import HistoryEdgeNull
from HistoryEdge import HistoryEdge
from DocumentObject import DocumentObject
from FieldList import FieldList
from HistoryGraph import HistoryGraph
import os
from json import JSONEncoder, JSONDecoder

class DocumentCollection(object):
    def __init__(self):
        self.objects = defaultdict(list)
        self.classes = dict()
        self.historyedgeclasses = dict()
        for theclass in HistoryEdge.__subclasses__():
            self.historyedgeclasses[theclass.__name__] = theclass

    def Register(self, theclass):
        self.classes[theclass.__name__] = theclass
    def Save(self, filename):
        os.remove(filename)
        c = sqlite3.connect(filename)
        # Create table
        c.execute('''CREATE TABLE IF NOT EXISTS edge
                     (documentid text, documentclassname text, edgeclassname text, edgeid text, startnode1id text, startnode2id text, endnodeid text, 
                    propertyownerid text, propertyname text, propertyvalue text, propertytype text)''')
        c.execute("DELETE FROM edge")
        for documentid in self.objects:
            documentlist = self.objects[documentid]
            for document in documentlist:
                history = document.history
                for edgeid in history.edges:
                    edge = history.edges[edgeid]
                    startnodes = list(edge.startnodes)
                    if len(edge.startnodes) == 1:
                        startnode1id = startnodes[0]
                        startnode2id = ""
                    elif len(edge.startnodes) == 2:
                        startnode1id = startnodes[0]
                        startnode2id = startnodes[1]
                    else:
                        assert False
                    
                    if edge.propertytype is None:
                        propertytypename = ""
                    else:
                        propertytypename = edge.propertytype.__name__
                    c.execute("INSERT INTO edge VALUES ('" + document.id + "', '" + document.__class__.__name__ + "', '" + edge.__class__.__name__ + "', '" + edge.edgeid + "', " +
                        "'" + startnode1id + "', '" + startnode2id + "', '" + edge.endnode + "', '" + edge.propertyownerid + "', '" + edge.propertyname + "', '" + str(edge.propertyvalue) + "', "
                        "'" + propertytypename + "')")

        c.commit()
        c.close()

        
    def Load(self, filename):
        c = sqlite3.connect(filename)
        cur = c.cursor()    
        cur.execute("SELECT documentid, documentclassname, edgeclassname, edgeid, startnode1id, startnode2id, endnodeid, propertyownerid, propertyname, propertyvalue, propertytype FROM edge")

        historygraphdict = defaultdict(HistoryGraph)
        documentclassnamedict = dict()

        rows = cur.fetchall()
        for row in rows:
            documentid = row[0]
            documentclassname = row[1]
            edgeclassname = row[2]
            edgeid = row[3]
            startnode1id = row[4]
            startnode2id = row[5]
            endnodeid = row[6]
            propertyownerid = row[7]
            propertyname = row[8]
            propertyvaluestr = row[9]
            propertytypestr = row[10]

            if documentid in historygraphdict:
                historygraph = historygraphdict[documentid]
            else:
                historygraph = HistoryGraph()
                historygraphdict[documentid] = historygraph
                documentclassnamedict[documentid] = documentclassname
            if propertytypestr == "int":
                propertytype = int
                propertyvalue = int(propertyvaluestr)
            elif propertytypestr == "basestring":
                propertytype = basestring
                propertyvalue = str(propertyvaluestr)
            elif propertytypestr == "" and edgeclassname == "HistoryEdgeNull":
                propertytype = None
                propertyvalue = ""
            else:
                propertytype = self.classes[propertytypestr]
                propertyvalue = propertyvaluestr
            documentclassnamedict[documentid] = documentclassname
            if startnode2id == "":
                startnodes = {startnode1id}
            else:
                startnodes = {startnode1id, startnode2id}
            edge = self.historyedgeclasses[edgeclassname](edgeid, startnodes, endnodeid, propertyownerid, propertyname, propertyvalue, propertytype)
            history = historygraphdict[documentid]
            history.AddEdge(edge)

        for documentid in historygraphdict:
            doc = self.classes[documentclassnamedict[documentid]](documentid)
            history.Replay(doc)
            self.AddDocumentObject(doc)
            
    def asJSON(self):
        ret = list()
        for documentid in self.objects:
            documentlist = self.objects[documentid]
            for document in documentlist:
                history = document.history
                for edgeid in history.edges:
                    edge = history.edges[edgeid]
                    startnodes = list(edge.startnodes)
                    if len(edge.startnodes) == 1:
                        startnode1id = startnodes[0]
                        startnode2id = ""
                    elif len(edge.startnodes) == 2:
                        startnode1id = startnodes[0]
                        startnode2id = startnodes[1]
                    else:
                        assert False
                    
                    if edge.propertytype is None:
                        propertytypename = ""
                    else:
                        propertytypename = edge.propertytype.__name__
                    ret.append([document.id, document.__class__.__name__, edge.__class__.__name__, edge.edgeid, startnode1id, startnode2id, edge.endnode, edge.propertyownerid, edge.propertyname, 
                        str(edge.propertyvalue), propertytypename])
        return JSONEncoder().encode(ret)

    def LoadFromJSON(self, jsontext):
        historygraphdict = defaultdict(HistoryGraph)
        documentclassnamedict = dict()

        rows = JSONDecoder().decode(jsontext)

        for row in rows:
            documentid = row[0]
            documentclassname = row[1]
            edgeclassname = row[2]
            edgeid = row[3]
            startnode1id = row[4]
            startnode2id = row[5]
            endnodeid = row[6]
            propertyownerid = row[7]
            propertyname = row[8]
            propertyvaluestr = row[9]
            propertytypestr = row[10]

            if documentid in historygraphdict:
                historygraph = historygraphdict[documentid]
            else:
                historygraph = HistoryGraph()
                historygraphdict[documentid] = historygraph
                documentclassnamedict[documentid] = documentclassname
            if propertytypestr == "int":
                propertytype = int
                propertyvalue = int(propertyvaluestr)
            elif propertytypestr == "basestring":
                propertytype = basestring
                propertyvalue = str(propertyvaluestr)
            elif propertytypestr == "" and edgeclassname == "HistoryEdgeNull":
                propertytype = None
                propertyvalue = ""
            else:
                propertytype = self.classes[propertytypestr]
                propertyvalue = propertyvaluestr
            documentclassnamedict[documentid] = documentclassname
            if startnode2id == "":
                startnodes = {startnode1id}
            else:
                startnodes = {startnode1id, startnode2id}
            edge = self.historyedgeclasses[edgeclassname](edgeid, startnodes, endnodeid, propertyownerid, propertyname, propertyvalue, propertytype)
            history = historygraphdict[documentid]
            history.AddEdge(edge)

        for documentid in historygraphdict:
            doc = self.classes[documentclassnamedict[documentid]](documentid)
            history.Replay(doc)
            self.AddDocumentObject(doc)
            
       
    def GetByClass(self, theclass):
        #print "Getting object of class " + theclass.__name__
        return self.objects[theclass.__name__]
    def AddDocumentObject(self, obj):
        #print "Added object of class " + obj.__class__.__name__
        assert isinstance(obj, DocumentObject)
        assert obj.__class__.__name__  in self.classes
        for propname in obj.doop_field:
            propvalue = obj.doop_field[propname]
            if isinstance(propvalue, FieldList):
                for obj2 in getattr(obj, propname):
                    assert obj2.__class__.__name__  in self.classes
        self.objects[obj.__class__.__name__].append(obj)


documentcollection = None

def InitialiseDocumentCollection():
    global documentcollection
    documentcollection = DocumentCollection()



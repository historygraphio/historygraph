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
from FieldInt import FieldInt

class DocumentCollection(object):
    def __init__(self):
        self.objects = defaultdict(list)
        self.classes = dict()
        self.historyedgeclasses = dict()
        for theclass in HistoryEdge.__subclasses__():
            self.historyedgeclasses[theclass.__name__] = theclass

    def Register(self, theclass):
        self.classes[theclass.__name__] = theclass
    def Save(self, filenameedges, filenamedata):
        try:
            os.remove(filenameedges)
        except:
            pass
        c = sqlite3.connect(filenameedges)
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

        try:
            os.remove(filenamedata)
        except:
            pass
        self.database = sqlite3.connect(filenamedata)
        foreignkeydict = defaultdict(list)
        for classname in self.classes:
            theclass = self.classes[classname]
            variables = [a for a in dir(theclass) if not a.startswith('__') and not callable(getattr(theclass,a))]
            for a in variables:
                if isinstance(getattr(theclass, a), FieldList):
                    foreignkeydict[getattr(theclass, a).theclass.__name__].append((classname, a))
        columndict = defaultdict(list)
        for classname in self.classes:
            theclass = self.classes[classname]
            variables = [a for a in dir(theclass) if not a.startswith('__') and not callable(getattr(theclass,a))]
            for a in variables:
                if isinstance(getattr(theclass, a), FieldList) == False:
                    columndict[classname].append((a, "int" if isinstance(getattr(theclass, a), FieldInt) else "text"))
        for k in foreignkeydict:
            for (classname, a) in foreignkeydict[k]:
                columndict[k].append((classname + "id", "text"))
        for classname in columndict:
            columnlist = columndict[classname]
            sql = "CREATE TABLE " + classname + " (id text "
            for (a, thetype) in columnlist:
                sql += ","
                sql += a + " " + thetype
            sql += ")"

            self.database.execute(sql)
        
        for documentid in self.objects:
            self.SaveDocumentObject(self.objects[documentid][0], None, foreignkeydict, columndict)

        self.database.commit()

    def SaveDocumentObject(self, documentobject, parentobject, foreignkeydict, columndict):
        variables = [a for a in dir(documentobject.__class__) if not a.startswith('__') and not callable(getattr(documentobject.__class__,a))]
        for a in variables:
            if isinstance(getattr(documentobject.__class__, a), FieldList):
                for childobj in getattr(documentobject, a):
                    self.SaveDocumentObject(childobj, documentobject, foreignkeydict, columndict)
        foreignkeyclassname = ""
        if documentobject.__class__.__name__ in foreignkeydict:
            if len(foreignkeydict[documentobject.__class__.__name__]) == 0:
                pass #No foreign keys to worry about
            elif len(foreignkeydict[documentobject.__class__.__name__]) == 1:
                (foreignkeyclassname, a) = foreignkeydict[documentobject.__class__.__name__][0]
            else:
                assert False #Only one foreign key allowed
        sql = "INSERT INTO " + documentobject.__class__.__name__ + " VALUES ('" + documentobject.id + "'"
        for (columnname, columntype) in columndict[documentobject.__class__.__name__]:
            if columntype == "int":
                quote = ""
            elif columntype == "text":
                quote = "'"
            else:
                assert False
                quote = ""
            sql += ","
            if foreignkeyclassname != "" and foreignkeyclassname + "id" == columnname:
                sql += quote + parentobject.id + quote
            else:
                sql += quote + str(getattr(documentobject, columnname)) + quote
        sql += ")"
        self.database.execute(sql)
        
        
    def Load(self, filenameedges, filenamedata):
        c = sqlite3.connect(filenameedges)
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

        self.database = sqlite3.connect(filenamedata)

    def GetSQLObjects(self, query):
        ret = list()
        cur = self.database.cursor()    
        cur.execute(query)

        rows = cur.fetchall()
        for row in rows:
            for classname in self.objects:
                for obj in self.objects[classname]:
                    if obj.id == row[0]:
                        ret.append(obj)
        return ret
            
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



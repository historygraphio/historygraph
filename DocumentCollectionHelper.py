#DocumentCollectionHelper.py
# A collection of functions that work with DocumentCollections and do thing not available in pyjs

import sqlite3
import os
from collections import defaultdict
from HistoryEdge import HistoryEdge
from HistoryGraph import HistoryGraph
from FieldList import FieldList
from FieldIntRegister import FieldInt
from DocumentObject import DocumentObject
from ImmutableObject import ImmutableObject

def SaveDocumentCollection(dc, filenameedges, filenamedata):
    try:
        os.remove(filenameedges)
    except:
        pass
    c = sqlite3.connect(filenameedges)
    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS edge (
                    documentid text, 
                    documentclassname text, 
                    edgeclassname text, 
                    startnode1id text, 
                    startnode2id text, 
                    propertyownerid text, 
                    propertyname text, 
                    propertyvalue text, 
                    propertytype text
                )''')
    c.execute("DELETE FROM edge")
    for classname in dc.objects:
        if issubclass(dc.classes[classname], DocumentObject):
            documentdict = dc.objects[classname]
            for (documentid, document) in documentdict.iteritems():
                history = document.history
                for edgeid in history.edgesbyendnode:
                    edge = history.edgesbyendnode[edgeid]
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
                        propertytypename = edge.propertytype
                    c.execute("INSERT INTO edge VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (document.id, document.__class__.__name__, 
                        edge.__class__.__name__, startnode1id, startnode2id, edge.propertyownerid, edge.propertyname,
                        edge.propertyvalue, propertytypename))

    c.commit()
    c.close()

    try:
        os.remove(filenamedata)
    except:
        pass
    database = sqlite3.connect(filenamedata)
    foreignkeydict = defaultdict(list)
    for classname in dc.classes:
        theclass = dc.classes[classname]
        variables = [a for a in dir(theclass) if not a.startswith('__') and not callable(getattr(theclass,a))]
        for a in variables:
            if isinstance(getattr(theclass, a), FieldList):
                foreignkeydict[getattr(theclass, a).theclass.__name__].append((classname, a))
    columndict = defaultdict(list)
    for classname in dc.classes:
        theclass = dc.classes[classname]
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

        database.execute(sql)
    
    for documentid in dc.objects:
        objlist = [obj for (objid, obj) in dc.objects[documentid].iteritems()]
        SaveDocumentObject(database, objlist[0], None, foreignkeydict, columndict)

    database.commit()

def SaveDocumentObject(database, documentobject, parentobject, foreignkeydict, columndict):
    variables = [a for a in dir(documentobject.__class__) if not a.startswith('__') and not callable(getattr(documentobject.__class__,a))]
    for a in variables:
        if isinstance(getattr(documentobject.__class__, a), FieldList):
            for childobj in getattr(documentobject, a):
                SaveDocumentObject(database, childobj, documentobject, foreignkeydict, columndict)
    foreignkeyclassname = ""
    if documentobject.__class__.__name__ in foreignkeydict:
        if len(foreignkeydict[documentobject.__class__.__name__]) == 0:
            pass #No foreign keys to worry about
        elif len(foreignkeydict[documentobject.__class__.__name__]) == 1:
            (foreignkeyclassname, a) = foreignkeydict[documentobject.__class__.__name__][0]
        else:
            assert False #Only one foreign key allowed
    sql = "INSERT INTO " + documentobject.__class__.__name__ + " VALUES (?"
    values = list()
    for (columnname, columntype) in columndict[documentobject.__class__.__name__]:
        sql += ",?"
        
        if foreignkeyclassname != "" and foreignkeyclassname + "id" == columnname:
            values.append(parentobject.id)
        else:
            values.append(getattr(documentobject, columnname))
    sql += ")"
    if isinstance(documentobject, DocumentObject):
        database.execute(sql, tuple([documentobject.id] + values))
    elif isinstance(documentobject, ImmutableObject):
        database.execute(sql, tuple([documentobject.GetHash()] + values))
    else:
        assert False


def GetSQLObjects(documentcollection, filenamedata, query):
    database = sqlite3.connect(filenamedata)
    ret = list()
    cur = database.cursor()    
    cur.execute(query)

    rows = cur.fetchall()
    for row in rows:
        for classname in documentcollection.objects:
            for (objid, obj) in documentcollection.objects[classname].iteritems():
                if isinstance(obj, DocumentObject):
                    if obj.id == row[0]:
                        ret.append(obj)
                elif isinstance(obj, ImmutableObject):
                    if obj.GetHash() == row[0]:
                        ret.append(obj)
                else:
                    assert False
    return ret
        
def LoadDocumentCollection(dc, filenameedges, filenamedata):
    dc.objects = defaultdict(dict)
    #dc.classes = dict()
    dc.historyedgeclasses = dict()
    for theclass in HistoryEdge.__subclasses__():
        dc.historyedgeclasses[theclass.__name__] = theclass

    c = sqlite3.connect(filenameedges)
    cur = c.cursor()    
    c.execute('''CREATE TABLE IF NOT EXISTS edge (
                    documentid text, 
                    documentclassname text, 
                    edgeclassname text, 
                    edgeid text PRIMARY KEY, 
                    startnode1id text, 
                    startnode2id text, 
                    endnodeid text, 
                    propertyownerid text, 
                    propertyname text, 
                    propertyvalue text, 
                    propertytype text
                )''')
    c.commit()
    cur.execute("SELECT documentid, documentclassname, edgeclassname, startnode1id, startnode2id, propertyownerid, propertyname, propertyvalue, propertytype FROM edge")

    historygraphdict = defaultdict(HistoryGraph)
    documentclassnamedict = dict()

    rows = cur.fetchall()
    for row in rows:
        documentid = str(row[0])
        documentclassname = str(row[1])
        edgeclassname = str(row[2])
        startnode1id = str(row[3])
        startnode2id = str(row[4])
        propertyownerid = str(row[5])
        propertyname = str(row[6])
        propertyvaluestr = str(row[7])
        propertytypestr = str(row[8])

        if documentid in historygraphdict:
            historygraph = historygraphdict[documentid]
        else:
            historygraph = HistoryGraph()
            historygraphdict[documentid] = historygraph
            documentclassnamedict[documentid] = documentclassname
        if propertytypestr == "FieldInt" or propertytypestr == "int":
            propertytype = int
            propertyvalue = int(propertyvaluestr)
        elif propertytypestr == "FieldText":
            propertytype = basestring
            propertyvalue = str(propertyvaluestr)
        elif propertytypestr == "" and edgeclassname == "HistoryEdgeNull":
            propertytype = None
            propertyvalue = ""
        else:
            propertytype = dc.classes[propertytypestr]
            propertyvalue = propertyvaluestr
        documentclassnamedict[documentid] = documentclassname
        if startnode2id == "":
            startnodes = {startnode1id}
        else:
            startnodes = {startnode1id, startnode2id}
        edge = dc.historyedgeclasses[edgeclassname](startnodes, propertyownerid, propertyname, propertyvalue, propertytypestr, documentid, documentclassname)
        history = historygraphdict[documentid]
        history.AddEdges([edge])

    #nulledges = list()
    for documentid in historygraphdict:
        doc = dc.classes[documentclassnamedict[documentid]](documentid)
        doc.dc = dc
        history = historygraphdict[documentid]
    #    nulledges.extend(history.MergeDanglingBranches())
        history.Replay(doc)
        dc.AddDocumentObject(doc)
    #
    #SaveEdges(dc, filenameedges, nulledges)

    #Load all of the immutable objects

    c = sqlite3.connect(filenamedata) #Return the database that can used for get sql objects

    for (classname, theclass) in dc.classes.iteritems():
        if issubclass(theclass, ImmutableObject):
            variables = [a for a in dir(theclass) if not a.startswith('__') and not callable(getattr(theclass,a))]
            sql = "SELECT id"
            for v in variables:
                sql += ", " + v
            sql += " FROM " + theclass.__name__

            cur = c.cursor()    
            cur.execute(sql)

            rows = cur.fetchall()
            d = dict()
            for row in rows:
                for i in range(len(variables)):
                    d[variables[i]] = row[i + 1]
            obj = theclass(**d)
            assert obj.GetHash() == row[0]
            dc.AddImmutableObject(obj)

    return c

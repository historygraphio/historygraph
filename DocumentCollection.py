#This module handles storing all documents in the database (and reloading)
from collections import defaultdict
from HistoryEdgeSimpleProperty import HistoryEdgeSimpleProperty
from HistoryEdgeRemoveChild import HistoryEdgeRemoveChild
from HistoryEdgeNull import HistoryEdgeNull
from HistoryEdge import HistoryEdge
from DocumentObject import DocumentObject
from FieldList import FieldList
from HistoryGraph import HistoryGraph
from json import JSONEncoder, JSONDecoder
from FieldInt import FieldInt
from Document import Document
from HistoryEdgeAddChild import HistoryEdgeAddChild

class DocumentCollection(object):
    def __init__(self):
        self.objects = defaultdict(list)
        self.classes = dict()
        self.historyedgeclasses = dict()
        for theclass in HistoryEdge.__subclasses__():
            self.historyedgeclasses[theclass.__name__] = theclass

    def Register(self, theclass):
        self.classes[theclass.__name__] = theclass
        

    def asJSON(self):
        ret = list()
        for documentid in self.objects:
            documentlist = self.objects[documentid]
            for document in documentlist:
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
                    ret.append(edge.asTuple())
                    #print "DocumentCollection edge stored = ",edge
        return JSONEncoder().encode(ret)

    def LoadFromJSON(self, jsontext):
        historygraphdict = defaultdict(HistoryGraph)
        documentclassnamedict = dict()

        rows = JSONDecoder().decode(jsontext)

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
                #propertytype = self.classes[propertytypestr]
                propertyvalue = propertyvaluestr
            propertytype = propertytypestr
            documentclassnamedict[documentid] = documentclassname
            if startnode2id == "":
                startnodes = {startnode1id}
            else:
                startnodes = {startnode1id, startnode2id}
            #print "DocumentCollection propertytype = ",propertytype
            edge = self.historyedgeclasses[edgeclassname](startnodes, propertyownerid, propertyname, propertyvalue, propertytype, documentid, documentclassname)
            #print "DocumentCollection edge added = ",edge
            history = historygraphdict[documentid]
            history.AddEdges([edge])

        for documentid in historygraphdict:
            doc = None
            wasexisting = False
            if documentclassnamedict[documentid] in self.objects:
                for d2 in self.objects[documentclassnamedict[documentid]]:
                    if d2.id == documentid:
                        doc = d2
                        wasexisting = True
            if doc is None:
                doc = self.classes[documentclassnamedict[documentid]](documentid)
                assert len(doc.history.edgesbyendnode) == 0

            #Make a copy of self's history
            history = doc.history.Clone()
            #Merge doc2's history
            history.MergeGraphs(historygraphdict[documentid])
            history.RecordPastEdges()
            history.ProcessConflictWinners()
            #Create the return object and replay the history in to it
            history.Replay(doc)

            if not wasexisting:
                self.AddDocumentObject(doc)
            
       
    def GetByClass(self, theclass):
        return self.objects[theclass.__name__]
    def AddDocumentObject(self, obj):
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



#This module handles storing all documents in the database (and reloading)
from collections import defaultdict
from historyedgesimpleproperty import HistoryEdgeSimpleProperty
from historyedgeremovechild import HistoryEdgeRemoveChild
from historyedgenull import HistoryEdgeNull
from historyedge import HistoryEdge
from documentobject import DocumentObject
from fieldcollection import FieldCollection
from historygraph import HistoryGraph
from json import JSONEncoder, JSONDecoder
from fieldintregister import FieldIntRegister
from document import Document
from historyedgeaddchild import HistoryEdgeAddChild
from immutableobject import ImmutableObject
import hashlib
import uuid
#import utils

class DocumentCollection(object):
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.objects = defaultdict(dict)
        self.classes = dict()
        self.historyedgeclasses = dict()
        for theclass in HistoryEdge.__subclasses__():
            self.historyedgeclasses[theclass.__name__] = theclass
        self.listeners = list()

    def Register(self, theclass):
        self.classes[theclass.__name__] = theclass
        

    def getAllEdges(self):
        historyedges = list()
        immutableobjects = list()
        for classname in self.objects:
            documentdict = self.objects[classname]
            if issubclass(self.classes[classname], DocumentObject):
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
                        historyedges.append(edge.asTuple())
            elif issubclass(self.classes[classname], ImmutableObject):
                for (objid, obj) in documentdict.iteritems():
                    immutableobjects.append(obj.asDict())
            else:
                assert False
        return (historyedges, immutableobjects)

    def asJSON(self):
        (historyedges, immutableobjects) = self.getAllEdges()
        return JSONEncoder().encode({"history":historyedges,"immutableobjects":immutableobjects})

    def LoadFromJSON(self, jsontext):
        #utils.log_output("LoadFromJSON jsontext = ", jsontext)
        historygraphdict = defaultdict(HistoryGraph)
        documentclassnamedict = dict()

        rawdc = JSONDecoder().decode(jsontext)
        rows = rawdc["history"]

        for row in rows:
            documentid = str(row[0])
            documentclassname = str(row[1])
            edgeclassname = str(row[2])
            endnodeid = str(row[3])
            startnode1id = str(row[4])
            startnode2id = str(row[5])
            propertyownerid = str(row[6])
            propertyname = str(row[7])
            propertyvaluestr = str(row[8])
            propertytypestr = str(row[9])

            if documentid in historygraphdict:
                historygraph = historygraphdict[documentid]
            else:
                historygraph = HistoryGraph()
                historygraphdict[documentid] = historygraph
                documentclassnamedict[documentid] = documentclassname
            if propertytypestr == "int" or propertytypestr == "FieldIntCounter":
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
            edge = self.historyedgeclasses[edgeclassname](startnodes, propertyownerid, propertyname, propertyvalue, propertytype, documentid, documentclassname)
            #print "LoadFromJSON edge.asTuple() = ",edge.asTuple()
            #assert edge.GetEndNode() == endnodeid, "edge.GetEndNode() == endnodeid failed edge.GetEndNode() = " + str(edge.GetEndNode()) + " endnodeid = " + str(endnodeid)
            history = historygraphdict[documentid]
            history.AddEdges([edge])

        for documentid in historygraphdict:
            doc = None
            wasexisting = False
            if documentclassnamedict[documentid] in self.objects:
                for (d2id, d2) in self.objects[documentclassnamedict[documentid]].iteritems():
                    if d2.id == documentid:
                        doc = d2
                        wasexisting = True
            if doc is None:
                doc = self.classes[documentclassnamedict[documentid]](documentid)
                doc.dc = self
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
            
        rows = rawdc["immutableobjects"]
        for d in rows:
            #print "Docuemnt Collection LoadFromJSON received Imutable Object=",d
            classname = d["classname"]
            theclass = self.classes[classname]
            assert issubclass(theclass, ImmutableObject)
            thehash = d["hash"]
            del d["classname"]
            del d["hash"]
            io = theclass(**d)
            wasexisting = False
            for (io2id, io2) in self.objects[classname].iteritems():
                if io2.GetHash() == io.GetHash():
                    #print "We already have this object ignoring io2=",io2.asDict()
                    #print "self.objects[classname]=",self.objects[classname]
                    wasexisting = True
            if wasexisting == False:
                #print "Object not found adding"
                self.objects[classname][io.GetHash()] = io
            
       
    def GetByClass(self, theclass):
        return [obj for (objid, obj) in self.objects[theclass.__name__].iteritems()]

    def AddDocumentObject(self, obj):
        assert isinstance(obj, DocumentObject)
        obj.GetDocument().dc = self
        assert obj.__class__.__name__  in self.classes
        for propname in obj.doop_field:
            propvalue = obj.doop_field[propname]
            if isinstance(propvalue, FieldCollection):
                for obj2 in getattr(obj, propname):
                    assert obj2.__class__.__name__  in self.classes
        wasfound = False
        self.objects[obj.__class__.__name__][obj.id] = obj
        obj.GetDocument().AddEdgesListener(self)
        for l in self.listeners:
            l.AddDocumentObject(self, obj)

    def AddImmutableObject(self, obj):
        assert isinstance(obj, ImmutableObject)
        assert obj.__class__.__name__  in self.classes
        self.objects[obj.__class__.__name__][obj.GetHash()] = obj
        for l in self.listeners:
            l.ImmutableObjectAdded(self, obj)

    def AddListener(self, listener):
        self.listeners.append(listener)

    def GetObjectByID(self, classname, id):
        return self.objects[classname][id]
        """
        matches = [a for a in self.objects[classname] if a.id == id]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) == 0:
            return None
        else:
            assert False
        """

    def EdgesAdded(self, edges):
        for l in self.listeners:
            l.EdgesAdded(self, edges)
        



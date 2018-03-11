# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#This module handles storing all documents in the database (and reloading)
from collections import defaultdict
from .documentobject import DocumentObject
from . import fields, edges
from .historygraph import HistoryGraph
from json import JSONEncoder, JSONDecoder
from .document import Document
from .immutableobject import ImmutableObject
import hashlib
import uuid

class DocumentCollection(object):
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.objects = defaultdict(dict)
        self.classes = dict()
        self.historyedgeclasses = dict()
        for theclass in edges.Edge.__subclasses__():
            self.historyedgeclasses[theclass.__name__] = theclass
        self.listeners = list()

    def register(self, theclass):
        self.classes[theclass.__name__] = theclass
        

    def get_all_edges(self):
        historyedges = list()
        immutableobjects = list()
        for classname in self.objects:
            documentdict = self.objects[classname]
            if issubclass(self.classes[classname], DocumentObject):
                for (documentid, document) in documentdict.iteritems():
                    history = document.history
                    for edgeid in history.edgesbyendnode:
                        edge = history.edgesbyendnode[edgeid]
                        start_hashes = list(edge._start_hashes)
                        if len(edge._start_hashes) == 1:
                            start_hash_1 = start_hashes[0]
                            start_hash_2 = ""
                        elif len(edge._start_hashes) == 2:
                            start_hash_1 = start_hashes[0]

                            start_hash_2 = start_hashes[1]
                        else:
                            assert False
                        
                        if edge.propertytype is None:
                            propertytypename = ""
                        else:
                            propertytypename = edge.propertytype
                        historyedges.append(edge.as_tuple())
            elif issubclass(self.classes[classname], ImmutableObject):
                for (objid, obj) in documentdict.iteritems():
                    immutableobjects.append(obj.as_dict())
            else:
                assert False
        return (historyedges, immutableobjects)

    def as_json(self):
        (historyedges, immutableobjects) = self.get_all_edges()
        return JSONEncoder().encode({"history":historyedges,"immutableobjects":immutableobjects})

    def load_from_json(self, jsontext):
        historygraphdict = defaultdict(HistoryGraph)
        documentclassnamedict = dict()

        rawdc = JSONDecoder().decode(jsontext)
        rows = rawdc["history"]

        for row in rows:
            documentid = str(row[0])
            documentclassname = str(row[1])
            edgeclassname = str(row[2])
            endnodeid = str(row[3])
            start_hash_1 = str(row[4])
            start_hash_2 = str(row[5])
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
            elif propertytypestr == "" and edgeclassname == "Merge":
                propertytype = None
                propertyvalue = ""
            else:
                propertyvalue = propertyvaluestr
            propertytype = propertytypestr
            documentclassnamedict[documentid] = documentclassname
            if start_hash_2 == "":
                start_hashes = {start_hash_1}
            else:
                start_hashes = {start_hash_1, start_hash_2}
            edge = self.historyedgeclasses[edgeclassname](start_hashes, propertyownerid, propertyname, propertyvalue, propertytype, documentid, documentclassname)
            history = historygraphdict[documentid]
            history.add_edges([edge])

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
            history = doc.history.clone()
            #Merge doc2's history
            history.merge_graphs(historygraphdict[documentid])
            history.record_past_edges()
            history.process_conflict_winners()
            #Create the return object and replay the history in to it
            history.replay(doc)

            if not wasexisting:
                self.add_document_object(doc)
            
        rows = rawdc["immutableobjects"]
        for d in rows:
            classname = d["classname"]
            theclass = self.classes[classname]
            assert issubclass(theclass, ImmutableObject)
            thehash = d["hash"]
            del d["classname"]
            del d["hash"]
            io = theclass(**d)
            wasexisting = False
            for (io2id, io2) in self.objects[classname].iteritems():
                if io2.get_hash() == io.get_hash():
                    wasexisting = True
            if wasexisting == False:
                self.objects[classname][io.get_hash()] = io
            
       
    def get_by_class(self, theclass):
        return [obj for (objid, obj) in self.objects[theclass.__name__].iteritems()]

    def add_document_object(self, obj):
        assert isinstance(obj, DocumentObject)
        obj.get_document().dc = self
        assert obj.__class__.__name__  in self.classes
        for propname in obj._field:
            propvalue = obj._field[propname]
            if isinstance(propvalue, fields.Collection):
                for obj2 in getattr(obj, propname):
                    assert obj2.__class__.__name__  in self.classes
        wasfound = False
        self.objects[obj.__class__.__name__][obj.id] = obj
        obj.get_document().add_edges_listener(self)
        for l in self.listeners:
            l.document_object_added(self, obj)

    def add_immutable_object(self, obj):
        assert isinstance(obj, ImmutableObject)
        assert obj.__class__.__name__  in self.classes
        self.objects[obj.__class__.__name__][obj.get_hash()] = obj
        for l in self.listeners:
            l.immutable_object_added(self, obj)

    def add_listener(self, listener):
        self.listeners.append(listener)

    def get_object_by_id(self, classname, id):
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

    def edges_added(self, edges):
        for l in self.listeners:
            l.edges_added(self, edges)
        



# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function

#This module handles storing all documents in the database (and reloading)
from collections import defaultdict
from .documentobject import DocumentObject
from . import fields, edges, validators
from .historygraph import HistoryGraph
from json import JSONEncoder, JSONDecoder
from .document import Document
from .immutableobject import ImmutableObject
import hashlib
import uuid
import six


class DocumentCollection(object):

    standard_validators = [validators.int_counter_integer_value]

    def __init__(self, sessionid, has_standard_validators=True):
        self.id = str(uuid.uuid4())
        self.objects = defaultdict(dict)
        self.classes = dict()
        self.historyedgeclasses = dict()
        for theclass in edges.Edge.__subclasses__():
            self.historyedgeclasses[theclass.__name__] = theclass
        self.listeners = list()
        if has_standard_validators:
            self._validators = self.standard_validators
        else:
            self._validators = list()
        self._custom_validators = list()
        assert isinstance(sessionid, six.string_types)
        self.sessionid = sessionid

    def register(self, theclass):
        self.classes[theclass.__name__] = theclass
        if theclass.is_singleton:
            self.add_document_object(theclass())

    def get_all_edges(self):
        # Retreive all the edges for all of the documents in this dc
        # and all of the immutable objects
        historyedges = list()
        immutableobjects = list()
        for classname in self.objects:
            documentdict = self.objects[classname]
            if issubclass(self.classes[classname], Document):
                for (documentid, document) in six.iteritems(documentdict):
                    history = document.history
                    for edge in history.get_all_edges():
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
                for (objid, obj) in six.iteritems(documentdict):
                    immutableobjects.append(obj.as_dict())
            elif issubclass(self.classes[classname], DocumentObject):
                pass
            else:
                assert False
        return (historyedges, immutableobjects)

    def as_json(self):
        # Encode the entire dc in a form suitable to send over the internet
        (historyedges, immutableobjects) = self.get_all_edges()
        return JSONEncoder().encode({"history":historyedges,
                                     "immutableobjects":immutableobjects})

    def load_from_json(self, jsontext):
        # Load the sent edges as JSON. This will handle full or partial
        # updates to the dc correctly
        historygraphdict = defaultdict(HistoryGraph)
        documentclassnamedict = dict()

        rawdc = JSONDecoder().decode(jsontext)
        rows = rawdc["history"]

        for row in rows:
            # Loop over each record in the JSON array and build the appropriate edge
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
            sessionid = str(row[10])
            transaction_id = str(row[11])

            if documentid in historygraphdict:
                historygraph = historygraphdict[documentid]
            else:
                historygraph = HistoryGraph()
                historygraphdict[documentid] = historygraph
                documentclassnamedict[documentid] = documentclassname
            if propertytypestr == "int" or propertytypestr == "FieldIntCounter":
                #propertytype = int
                propertyvalue = int(propertyvaluestr)
            elif propertytypestr == "basestring":
                #propertytype = basestring
                propertyvalue = str(propertyvaluestr)
            elif propertytypestr == "boolean":
                #propertytype = bool
                propertyvalue = propertyvaluestr == "True"
            elif propertytypestr == "" and edgeclassname == "Merge":
                #propertytype = None
                propertyvalue = ""
            else:
                propertyvalue = propertyvaluestr
            propertytype = propertytypestr
            documentclassnamedict[documentid] = documentclassname
            if start_hash_2 == "":
                start_hashes = {start_hash_1}
            else:
                start_hashes = {start_hash_1, start_hash_2}
            edge = self.historyedgeclasses[edgeclassname](start_hashes, propertyownerid, propertyname,
                                                          propertyvalue, propertytype, documentid,
                                                          documentclassname, sessionid, transaction_id)
            history = historygraphdict[documentid]
            history.dc = self
            history.add_edges([edge])

        for documentid in historygraphdict:
            # Merge the received historygraph edges in with the ones currently in the
            # database
            doc = None
            wasexisting = False
            if documentclassnamedict[documentid] in self.objects:
                for (d2id, d2) in six.iteritems(self.objects[documentclassnamedict[documentid]]):
                    if d2.id == documentid:
                        doc = d2
                        wasexisting = True
            if doc is None:
                doc = self.classes[documentclassnamedict[documentid]](documentid)
                doc.history.dc = self
                doc.dc = self

            # Make a copy of self's history
            history = doc.history.clone()
            # Merge doc2's history
            history.merge_graphs(historygraphdict[documentid])
            has_start_edge = history.has_start_edge()
            if has_start_edge:
                history.record_past_edges()
                history.process_conflict_winners()
            # Create the target object and replay the history in to it
            doc.insetattr = True
            doc.history = history
            if has_start_edge:
                history.replay(doc)
            doc.insetattr = False

            if not wasexisting:
                self.add_document_object(doc)

        rows = rawdc["immutableobjects"]
        for d in rows:
            # Loop over each immutable object and recreate it
            classname = d["classname"]
            theclass = self.classes[classname]
            assert issubclass(theclass, ImmutableObject)
            thehash = d["hash"]
            del d["classname"]
            del d["hash"]
            io = theclass(**d)
            wasexisting = False
            for (io2id, io2) in six.iteritems(self.objects[classname]):
                if io2.get_hash() == io.get_hash():
                    wasexisting = True
            if wasexisting == False:
                self.objects[classname][io.get_hash()] = io


    def get_by_class(self, theclass):
        #TODO: change to get by class name to retain consistency with get_object_by_id
        return [obj for (objid, obj) in
                six.iteritems(self.objects[theclass.__name__])
                if obj.get_is_deleted() is False]

    def add_document_object(self, obj):
        # Add a newly created document object to the dc. This function needs to be called
        # before any changes are made to the document object
        assert isinstance(obj, DocumentObject)
        obj.get_document().dc = self
        obj.dc = self
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
        # Add a newly created immutable object to the dc.
        assert isinstance(obj, ImmutableObject)
        assert obj.__class__.__name__  in self.classes
        self.objects[obj.__class__.__name__][obj.get_hash()] = obj
        for l in self.listeners:
            l.immutable_object_added(self, obj)

    def add_listener(self, listener):
        self.listeners.append(listener)

    def get_object_by_id(self, classname, id):
        return self.objects[classname][id]

    def has_object_by_id(self, classname, id):
        return id in self.objects[classname]

    def edges_added(self, edges):
        # Inform the listeners that edges were added
        for l in self.listeners:
            l.edges_added(self, edges)

    def get_validators(self):
        return self._validators

    def register_validator(self, validator):
        self._validators.append(validator)

    def register_custom_validator(self, custom_validator):
        self._custom_validators.append(custom_validator)

    def get_customer_validators(self):
        return self._custom_validators

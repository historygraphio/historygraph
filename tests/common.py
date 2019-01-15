from __future__ import absolute_import, unicode_literals, print_function
from historygraph import DocumentCollection as _DocumentCollection
from json import JSONEncoder, JSONDecoder
from historygraph import Document
from historygraph import fields
from historygraph import DocumentObject


class DocumentCollection(_DocumentCollection):
    class GenericListener(object):
        def __init__(self, dc):
            self.slave = dc
            self.master = dc.master
            self.frozen = False
            self.frozen_edges = []
        def document_object_added(self, dc, obj):
            pass
        def immutable_object_added(self, dc, obj):
            pass
        def edges_added(self, dc, edges):
            if self.frozen:
                self.frozen_edges += [edge.as_tuple() for edge in edges]
            else:
                edges = [edge.as_tuple() for edge in edges]
                self.send_edges(edges)
        def freeze_dc_comms(self):
            self.frozen = True
        def unfreeze_dc_comms(self):
            self.frozen = False
            self.send_edges(self.frozen_edges)
            self.frozen_edges = []

    class MasterListener(GenericListener):
        def send_edges(self, edges):
            self.slave.load_from_json(JSONEncoder().encode({'history': edges, 'immutableobjects': []}))

    class SlaveListener(GenericListener):
        def send_edges(self, edges):
            self.master.load_from_json(JSONEncoder().encode({'history': edges, 'immutableobjects': []}))


    # This class is an inmemory simulation of two document collections which are
    # linked by exchanging edges
    def __init__(self, master=None, has_standard_validators=True):
        super(DocumentCollection, self).__init__(
              has_standard_validators=has_standard_validators)
        if master is not None:
            master.slave = self
            self.master = master
            self.slave = self
            self.master_listener = DocumentCollection.MasterListener(self)
            self.slave_listener = DocumentCollection.SlaveListener(self)
            self.master.add_listener(self.master_listener)
            self.add_listener(self.slave_listener)

    def master_edges_added(self, edges):
        self.load_from_json(json.dumps(edges))

    def slave_edges_added(self, edges):
        self.master.load_from_json(json.dumps(edges))

    def freeze_dc_comms(self):
        self.master_listener.freeze_dc_comms()
        self.slave_listener.freeze_dc_comms()

    def unfreeze_dc_comms(self):
        self.master_listener.unfreeze_dc_comms()
        self.slave_listener.unfreeze_dc_comms()

class CounterTestContainer(Document):
    testcounter = fields.IntCounter()

class Covers(Document):
    covers = fields.IntRegister()
    table = fields.IntRegister()

class TestPropertyOwner2(DocumentObject):
    cover = fields.IntRegister()
    quantity = fields.IntRegister()

class TestPropertyOwner1(Document):
    covers = fields.IntRegister()
    propertyowner2s = fields.Collection(TestPropertyOwner2)
    def was_changed(self, changetype, propertyowner, propertyname, propertyvalue, propertytype):
        super(TestPropertyOwner1, self).was_changed(changetype, propertyowner, propertyname, propertyvalue, propertytype)
        self.bWasChanged = True


class TestFieldListOwner2(DocumentObject):
    cover = fields.IntRegister()
    quantity = fields.IntRegister()

class TestFieldListOwner1(Document):
    covers = fields.IntRegister()
    propertyowner2s = fields.List(TestFieldListOwner2)

class FloatCounterTestContainer(Document):
    testcounter = fields.FloatCounter()

#The base class for edges in DOOP
import hashlib

class HistoryEdge(object):
    def __init__(self, startnodes, documentid, documentclassname):
        self.startnodes = startnodes
        self.inactive = False
        self.played = False
        self.documentid = documentid
        self.documentclassname = documentclassname

        
    def RecordPastEdges(self, pastedges, graph):
        self.pastedges = self.pastedges | set(pastedges)
        edges = graph.edgesbystartnode[self.GetEndNode()]
        pastedges.add(self.GetEndNode())
        for edge in edges:
            edge.RecordPastEdges(set(pastedges), graph)

    
    def CanReplay(self, graph):
        for node in self.startnodes:
            if node != "":
                edge = graph.edgesbyendnode[node]
                if edge.isplayed == False:
                    return False
        return True

    def ResetPastEdges(self):
        self.pastedges = set()

    def HasPastEdge(self, pastedgeid):
        return pastedgeid in self.pastedges

    def CompareForConflicts(self, edge2):
	    if (self.__class__ != edge2.__class__):
		    return; #Different edge types can never conflict
	    if (self.inactive or edge2.inactive):
		    return; #Inactive edges can never conflict with active edges
	    conflictwinner = self.GetConflictWinner(edge2)
	    assert conflictwinner == -1 or conflictwinner == 0 or conflictwinner == 1
	    if conflictwinner == 1:
	        self.inactive = True
	    elif conflictwinner == -1:
	        edge2.inactive = True
        
    def asDict(self):
        return {"classname":self.__class__.__name__,
            "startnodes":list(self.startnodes),
            "endnode":self.GetEndNode(),
            "propertyownerid":self.propertyownerid,
            "propertyvalue":self.propertyvalue,
            "propertyname":self.propertyname,
            "propertytype":self.propertytype,
            "documentid":self.documentid,
            "documentclassname":self.documentclassname,
         }

    def __str__(self):
        return str(self.asDict())

    def GetEndNode(self):
        s = ("classname",self.__class__.__name__,
            "startnodes",list(self.startnodes),
            "propertyownerid",self.propertyownerid,

            "propertyvalue",self.propertyvalue,
            "propertyname",self.propertyname,
            "propertytype",self.propertytype,
            "documentid",self.documentid,
            "documentclassname",self.documentclassname,
         )
        return hashlib.sha256(str(s)).hexdigest()


    

#The base class for edges in DOOP
import hashlib
#import utils

class HistoryEdge(object):
    def __init__(self, startnodes, documentid, documentclassname):
        self.startnodes = sorted(startnodes)
        self.inactive = False
        self.played = False
        self.documentid = documentid
        self.documentclassname = documentclassname

        
    def RecordPastEdges(self, pastedges, graph):
        self.pastedges = self.pastedges | set(pastedges)
        edges = graph.edgesbystartnode[self.GetEndNode()]
        pastedges.add(self.GetEndNode())
        #print "RecordPastEdges edges=",edges
        #print "RecordPastEdges pastedges=",pastedges
        for edge in edges:
            edge.RecordPastEdges(set(pastedges), graph)

    
    def CanReplay(self, graph):
        for node in self.startnodes:
            if node != "":
                if node not in graph.edgesbyendnode:
                    return False
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
        startnodes = list(self.startnodes)
        startnode1id = startnodes[0]
        if len(startnodes) > 1:
            startnode2id = startnodes[1]
        else:
            startnode2id = ""
        s = ("classname",str(self.__class__.__name__),
            "startnode1",str(startnode1id),
            "startnode2",str(startnode2id),
            "propertyownerid",str(self.propertyownerid),

            "propertyvalue",str(self.propertyvalue),
            "propertyname",str(self.propertyname),
            "propertytype",str(self.propertytype),
            "documentid",str(self.documentid),
            "documentclassname",str(self.documentclassname),
         )
        #utils.log_output("GetEndNode s = ",str(s))
        return hashlib.sha256(str(s)).hexdigest()

    def asTuple(self):
        #Return a tuple that represents the edge when it is turned in JSON
        startnodes = list(self.startnodes)
        startnode1id = startnodes[0]
        if len(startnodes) > 1:
            startnode2id = startnodes[1]
        else:
            startnode2id = ""
        return (str(self.documentid),
                str(self.documentclassname),
                str(self.__class__.__name__),
                str(self.GetEndNode()),
                str(startnode1id),
                str(startnode2id),
                str(self.propertyownerid),
                str(self.propertyname), 
                str(self.propertyvalue),
                str(self.propertytype))
    
    def depth(self, historygraph):
        startnodes = list(self.startnodes)
        if len(startnodes) == 1:
            if startnodes[0] == '':
                return 1
            else:
                return historygraph.edgesbyendnode[startnodes[0]].depth(historygraph) + 1
        elif len(self.startnodes) == 2:
            depth1 = historygraph.edgesbyendnode[startnodes[0]].depth(historygraph) + 1
            depth2 = historygraph.edgesbyendnode[startnodes[1]].depth(historygraph) + 1
            return max(depth1, depth2)
        else:
            assert False


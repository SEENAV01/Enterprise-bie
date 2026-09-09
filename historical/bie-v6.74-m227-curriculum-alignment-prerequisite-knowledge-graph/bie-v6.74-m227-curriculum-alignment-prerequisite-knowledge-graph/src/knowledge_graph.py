class KnowledgeGraph:
    def __init__(self):
        self.nodes={}; self.edges=[]
    def add_node(self,node_id,**data):
        self.nodes[node_id]=data
    def add_dependency(self,prerequisite,dependent):
        self.edges.append({"prerequisite":prerequisite,"dependent":dependent})
    def prerequisites(self,node_id):
        return [e["prerequisite"] for e in self.edges if e["dependent"]==node_id]
    def dependents(self,node_id):
        return [e["dependent"] for e in self.edges if e["prerequisite"]==node_id]

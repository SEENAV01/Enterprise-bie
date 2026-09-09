from dataclasses import dataclass, asdict

RELATIONS=[
    "prerequisite_of","part_of","causes","enables","contrasts_with",
    "derived_from","applies_to","measured_by","represented_by"
]

@dataclass
class Node:
    node_id:str
    label:str
    node_type:str          # concept, law, process, entity, application, equation
    provenance:list
    status:str              # SOURCE_DERIVED / INFERRED / EXTERNAL / SPECULATIVE
    confidence:float

@dataclass
class Edge:
    source:str
    target:str
    relation:str
    provenance:list
    status:str
    confidence:float

class KnowledgeGraph:
    def __init__(self):
        self.nodes={}
        self.edges=[]

    def add_node(self,node:Node):
        self.nodes[node.node_id]=node

    def add_edge(self,edge:Edge):
        if edge.relation not in RELATIONS:
            raise ValueError(f"Unsupported relation: {edge.relation}")
        self.edges.append(edge)

    def export(self):
        return {
            "nodes":[asdict(x) for x in self.nodes.values()],
            "edges":[asdict(x) for x in self.edges]
        }

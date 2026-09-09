import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))

from graph import graph,add_node,add_edge
from knowledge_graph import build_knowledge_graph,grounded
from learning_graph import build_learning_graph,valid_order
from prerequisites import prerequisite,valid
from dependencies import dependency
from ontology import ontology_term,consistent
from provenance import graph_provenance,traceable
from verification import verification,passed

def test_graph_building():
    kg=build_knowledge_graph(
        [{"concept_id":"c","label":"Concept","evidence_ids":["e"]}],
        [{"rel_id":"r","source":"c","target":"c",
          "relation":"RELATED","evidence_ids":["e"]}]
    )
    assert grounded(kg)

def test_learning_and_gates():
    lg=build_learning_graph(
        [{"id":"l","type":"LESSON","label":"Lesson","evidence_ids":["e"]}],
        []
    )
    pre=prerequisite("p","a","b",["e"])
    dep=dependency("d","a","b")
    terms=[ontology_term("a","A",["a"]),ontology_term("b","B",["b"])]
    p=graph_provenance("g",["s"],["e"],["up"])
    v=verification("v","g","PASS",["e"])
    assert valid_order(lg) and valid(pre) and dep["source"]=="a"
    assert consistent(terms) and traceable(p) and passed(v)

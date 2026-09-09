import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from graph import node,edge,build_graph
from relations import validate_relations
from prerequisites import validate_prerequisites
from curriculum import validate_curriculum
def test_m241():
 ns=[node("a","CONCEPT","A"),node("b","CONCEPT","B")]
 es=[edge("a","b","PREREQUISITE")]
 assert build_graph(ns,es)["valid"]
 assert validate_relations(es)["passed"]
 assert validate_prerequisites(ns,es)["passed"]
 assert validate_curriculum(ns,es)["order"]==["a","b"]

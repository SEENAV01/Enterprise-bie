import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from graph import KnowledgeGraph,Node,Edge
from path_planner import topological_path

def test_graph():
 g=KnowledgeGraph()
 g.add_node(Node("a","A","concept",["p1"],"SOURCE_DERIVED",1))
 g.add_node(Node("b","B","concept",["p2"],"SOURCE_DERIVED",1))
 g.add_edge(Edge("a","b","prerequisite_of",["p1"],"SOURCE_DERIVED",.95))
 assert topological_path(g.export()["nodes"],g.export()["edges"])==["a","b"]

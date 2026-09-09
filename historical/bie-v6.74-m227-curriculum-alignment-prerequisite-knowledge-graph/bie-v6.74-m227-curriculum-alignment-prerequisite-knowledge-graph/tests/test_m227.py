import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from knowledge_graph import KnowledgeGraph
from sequence import topological_order
def test_m227():
 g=KnowledgeGraph(); [g.add_node(x) for x in ["a","b","c"]]
 g.add_dependency("a","b"); g.add_dependency("b","c")
 assert topological_order(["a","b","c"],g.edges)==["a","b","c"]

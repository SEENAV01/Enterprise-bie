import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from graph_schema import node,edge
from higher_knowledge import propose_higher_knowledge
def test_graph():
 n=node("c1","concept","Current",["p1"])
 e=edge("c1","c2","depends_on",["p1"])
 assert n["source_scope"]=="BOOK"
 assert e["relation"]=="depends_on"

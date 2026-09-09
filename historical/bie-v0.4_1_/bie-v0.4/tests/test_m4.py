
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
from bie_m4.core import M4Graph, Node, Edge

def test_graph_and_order():
    g=M4Graph()
    for n in [
        Node("a","A"),Node("b","B"),Node("c","C")
    ]: g.add_node(n)
    g.add_edge(Edge("a","PREREQUISITE_OF","b",1.0))
    g.add_edge(Edge("b","PREREQUISITE_OF","c",1.0))
    assert g.cycles()==[]
    assert g.topological_learning_order()==["a","b","c"]

def test_cycle_detection():
    g=M4Graph()
    for x in "abc": g.add_node(Node(x,x))
    g.add_edge(Edge("a","PREREQUISITE_OF","b",1))
    g.add_edge(Edge("b","PREREQUISITE_OF","a",1))
    assert g.cycles()

def test_frontier():
    g=M4Graph()
    g.add_node(Node("i","internal"))
    g.add_node(Node("p","prereq","BOOK_PREREQUISITE"))
    g.add_node(Node("h","higher","HIGHER_LEVEL"))
    g.add_node(Node("a","app","EXTERNAL_APPLICATION"))
    assert set(g.frontier()["backward"])=={"p"}
    assert set(g.frontier()["forward"])=={"h"}
    assert set(g.frontier()["application"])=={"a"}

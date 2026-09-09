import sys
sys.path.insert(0,'../src')
from node import node
from dependency_graph import topological_order
from incremental import affected
def test_graph():
 ns=[node('a','CHAPTER'),node('b','LESSON',deps=['a']),node('c','LESSON',deps=['b'])]
 o=topological_order(ns); assert o.index('a')<o.index('b')<o.index('c')
 assert set(affected(['b'],ns))=={'b','c'}

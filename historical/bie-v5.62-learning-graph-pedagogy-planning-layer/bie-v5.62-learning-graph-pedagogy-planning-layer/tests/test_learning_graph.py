import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from path_planning import topological_learning_order

def test_learning_order():
 g={"relations":[
  {"source":"a","target":"b","relation_type":"PREREQUISITE_OF"},
  {"source":"b","target":"c","relation_type":"PREREQUISITE_OF"}]}
 assert topological_learning_order(g,["c"])==["a","b","c"]

def test_cycle_rejected():
 g={"relations":[
  {"source":"a","target":"b","relation_type":"PREREQUISITE_OF"},
  {"source":"b","target":"a","relation_type":"PREREQUISITE_OF"}]}
 try: topological_learning_order(g,["a"])
 except ValueError as e: assert str(e)=="LEARNING_GRAPH_CYCLE"
 else: assert False

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from rebuild import rebuild_plan

def test_downstream_order():
 g={"edges":[
  {"source":"A","target":"B","relation":"DEPENDS_ON"},
  {"source":"B","target":"C","relation":"DEPENDS_ON"},
  {"source":"A","target":"D","relation":"DEPENDS_ON"}]}
 p=rebuild_plan(g,["A"])
 assert p["rebuild_order"]==["A","B","C","D"]

def test_cycle():
 g={"edges":[
  {"source":"A","target":"B","relation":"DEPENDS_ON"},
  {"source":"B","target":"A","relation":"DEPENDS_ON"}]}
 try: rebuild_plan(g,["A"])
 except ValueError as e: assert str(e)=="DEPENDENCY_CYCLE"
 else: assert False

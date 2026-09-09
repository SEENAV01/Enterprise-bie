import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from scene_graph import create_scene_graph,add_node,add_edge,validate_graph
from timeline import dependency_order
from remotion_contract import build_remotion_scene,validate_remotion_scene
def test_m252():
 g=create_scene_graph("s"); add_node(g,{"id":"a"}); add_node(g,{"id":"b"}); add_edge(g,"a","b")
 assert validate_graph(g)["valid"]
 es=[{"id":"a","start_frame":0,"end_frame":1},{"id":"b","start_frame":1,"end_frame":2}]
 assert dependency_order(es,{"b":["a"]})["order"]==["a","b"]
 s=build_remotion_scene("s",10,30,[],[],es)
 assert validate_remotion_scene(s)["valid"]

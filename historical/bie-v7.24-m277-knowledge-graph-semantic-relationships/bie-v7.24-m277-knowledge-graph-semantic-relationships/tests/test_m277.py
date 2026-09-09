import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from graph import create_graph,add_entity,add_relation
from entities import create_entity,resolve_entity
from relations import create_relation
def test_m277():
 g=create_graph(); e=create_entity("1","concept","Charge"); add_entity(g,e)
 add_entity(g,create_entity("2","concept","Matter"))
 add_relation(g,create_relation("r","1","PROPERTY_OF","2",{"source_id":"s","source_version":1}))
 assert resolve_entity(list(g["entities"].values()),"charge")["resolved"]
 assert len(g["relations"])==1

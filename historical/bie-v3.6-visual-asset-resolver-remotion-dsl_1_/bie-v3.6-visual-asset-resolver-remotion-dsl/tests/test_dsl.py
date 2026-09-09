import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from scene_dsl import scene_spec,add_layer
from dsl_validator import validate_dsl
def test_dsl():
 s=scene_spec({"scene_id":"s1","objective":"x","narration_unit_ids":["u1"]},[])
 add_layer(s,"Text",{"text":"hello"})
 assert validate_dsl(s)["valid"]

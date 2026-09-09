import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from generation_plan import generation_plan,valid
from template import TemplateRegistry
from procedural import procedural_spec,deterministic
from validation import validate_asset
def test_m223():
 p=generation_plan("diagram","x",{}); assert valid(p)
 r=TemplateRegistry(); r.register("t","diagram",["x"],{"x":1})
 assert r.instantiate("t")["parameters"]["x"]==1
 s=procedural_spec("gen",7,{"x":1}); assert deterministic(s)
 a={"asset_type":"diagram","uri":"x","metadata":{}}
 assert validate_asset(a,{"asset_type":"diagram"})["passed"]

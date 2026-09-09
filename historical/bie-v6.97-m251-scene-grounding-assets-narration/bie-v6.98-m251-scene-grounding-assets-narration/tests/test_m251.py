import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from grounding import ground_concept,scene_intent
from assets import rank_asset_candidates
from equation_render import render_equation,validate_equation_render
from narration_sync import build_narration_segment,validate_sync
def test_m251():
 g=ground_concept("c","C","goal")
 i=scene_intent(g,"visual","n","x=1")
 assert i["concept_id"]=="c"
 ranked=rank_asset_candidates([{"id":"a","type":"diagram","tags":["c"]}],"diagram",["c"])
 assert ranked[0]["grounding_score"]==1
 e=render_equation("x = 1")
 assert validate_equation_render(e,"x = 1")["valid"]
 n=build_narration_segment("n","text",0,10,"s")
 assert validate_sync(n,0,20)["valid"]

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from assets import plan_assets
from style import visual_style
from voice import select_voice
from scene import scene,validate_scene
def test_m235():
 a=plan_assets("s",[{"asset_type":"TEXT","role":"definition"}])
 assert len(a)==1
 assert visual_style({"visual_density":"low"})["layout"]=="spacious"
 assert select_voice({"voice":"clear"})["selected"]=="clear"
 s=scene("s","T",a,{},{"voice":"clear"},{})
 assert validate_scene(s)["passed"]

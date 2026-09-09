import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from visual_planner import choose_visual
def test_visual():
 assert choose_visual({"type":"derivation"})=="equation"
 assert choose_visual({"type":"process_animation"})=="process"

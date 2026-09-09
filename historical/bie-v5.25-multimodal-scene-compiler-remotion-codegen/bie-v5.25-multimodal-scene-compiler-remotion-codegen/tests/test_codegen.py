import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_scene

def test_compile():
 r=compile_scene("s",12.5,30,["v"],"a",[],[],[])
 assert r["quality_gate"]["valid"]
 assert r["composition"]["durationInFrames"]==375
 assert "export const Scene_s" in r["component_source"]

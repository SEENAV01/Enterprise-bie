import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_visual_scene

def test_scene():
 s={"primitives":[{"primitive_id":"a"},{"primitive_id":"b"}],
    "relations":[{"source":"a","target":"b"}]}
 r=compile_visual_scene(s,[{"target":"a"}])
 assert r["quality_gate"]["valid"]

def test_bad_relation():
 s={"primitives":[{"primitive_id":"a"}],
    "relations":[{"source":"a","target":"missing"}]}
 assert not compile_visual_scene(s)["quality_gate"]["valid"]

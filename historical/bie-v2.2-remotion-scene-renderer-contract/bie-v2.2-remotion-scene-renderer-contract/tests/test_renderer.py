import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from scene_compiler import compile_lesson
def test_compile():
 d=json.loads((Path(__file__).parents[1]/"examples/lesson.json").read_text())
 r=compile_lesson(d)
 assert len(r["scenes"])==2
 assert r["scenes"][0]["scene_id"]=="C1_S01"
 assert r["scenes"][0]["duration_ms"]>0

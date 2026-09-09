import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_composition,validate_composition
from react_codegen import generate_react_source,validate_react_source
from render_job import build_render_job,validate_render_job
def test_m253():
 c=compile_composition({"scene_id":"s","fps":30,"duration_in_frames":10})
 assert validate_composition(c)["valid"]
 src=generate_react_source(c,[{"id":"x"}])
 assert validate_react_source(src)["valid"]
 j=build_render_job(c)
 assert validate_render_job(j)["valid"]

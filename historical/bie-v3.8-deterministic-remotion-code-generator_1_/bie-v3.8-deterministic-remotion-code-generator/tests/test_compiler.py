import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_scene
from validation import validate_compilation
def test_compile():
 s={"scene_id":"s1","objective":"x","duration":{"mode":"AUDIO_DRIVEN"},
    "layers":[{"type":"Text","props":{"text":"X"}}],"events":[]}
 r=compile_scene(s)
 assert validate_compilation(r)["valid"]
 assert "Scene_s1" in r["component_source"]

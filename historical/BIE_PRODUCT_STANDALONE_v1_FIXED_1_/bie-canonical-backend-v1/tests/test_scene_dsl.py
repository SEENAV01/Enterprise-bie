import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))

from scene_dsl import compile_scene_dsl, validate_scene_dsl

def test_scene_dsl_has_timing_audio_visuals():
    script={"sections":[{
        "script_id":"script:s1","title":"Charge",
        "narration":"Electric charge is a property of matter.",
        "source_blocks":["b1"]
    }]}
    knowledge={"evidence_index":{"b1":{"text":"Electric charge is a property of matter."}}}
    dsl=compile_scene_dsl(script,knowledge)
    scene=dsl["scenes"][0]
    assert scene["duration_seconds"] > 0
    assert scene["audio"]["text"] == script["sections"][0]["narration"]
    assert len(scene["visuals"]) == 2
    assert validate_scene_dsl(dsl,script,knowledge)["passed"] is True

def test_unknown_source_fails_scene_validation():
    script={"sections":[{"script_id":"script:s1","title":"x","narration":"x","source_blocks":["b1"]}]}
    knowledge={"evidence_index":{}}
    dsl=compile_scene_dsl(script,knowledge)
    assert validate_scene_dsl(dsl,script,knowledge)["passed"] is False

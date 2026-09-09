import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))

from remotion_generator import generate_remotion_project, validate_generated_project

def test_generates_real_remotion_sources(tmp_path):
    dsl={"scenes":[{
        "scene_id":"visual:0001",
        "duration_seconds":2,
        "audio":{"type":"narration","text":"Electric charge."},
        "visuals":[{"type":"title","text":"Charge"}]
    }]}
    meta=generate_remotion_project(dsl,tmp_path)
    assert (tmp_path/"generated"/"remotion"/"src"/"Root.tsx").exists()
    assert (tmp_path/"generated"/"remotion"/"src"/"BIELesson.tsx").exists()
    assert meta["duration_in_frames"] == 60
    assert validate_generated_project(meta)["passed"] is True

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from scene_engine.validate import validate

def test_scene_dsl():
    assert validate(Path(__file__).parents[1]/"examples/electricity-magnetism.scene.json")

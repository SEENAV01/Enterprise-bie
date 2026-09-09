import json
from pathlib import Path
from bie_m7.scene import compile_lesson, compile_scene_to_remotion
lesson=json.loads(Path(__file__).with_name("lesson.json").read_text())
scenes=compile_lesson(lesson)
print(json.dumps([compile_scene_to_remotion(s) for s in scenes],indent=2))

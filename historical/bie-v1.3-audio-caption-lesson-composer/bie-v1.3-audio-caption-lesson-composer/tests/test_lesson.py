import json
from pathlib import Path

def test_lesson():
 p=Path(__file__).parents[1]/"remotion/src/data/electricity-magnetism.lesson.json"
 d=json.loads(p.read_text())
 assert len(d["scenes"]) >= 18
 assert all(s["narration"]["script"] for s in d["scenes"])
 assert all(s["source_refs"] for s in d["scenes"])

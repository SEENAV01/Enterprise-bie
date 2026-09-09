import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from ingestion import validate_structure
from decomposition import lesson_units
from learning_path import validate_path
def test_m228():
 d={"chapters":[{"chapter_id":"c"}],"sections":[{"section_id":"s","chapter_id":"c"}]}
 assert validate_structure(d)["passed"]
 assert len(lesson_units("s",[{"concept_id":"a","title":"A"}]))==1
 assert validate_path({"lesson_order":["a"]})["passed"]

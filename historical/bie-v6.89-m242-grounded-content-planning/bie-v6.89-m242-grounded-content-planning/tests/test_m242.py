import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from prerequisite_generation import generate_lesson_sequence
from coverage import concept_coverage
from validation import validate_plan
def test_m242():
 p={"b":["a"],"c":["b"]}
 seq=generate_lesson_sequence(["c"],p)
 assert seq==["a","b","c"]
 assert concept_coverage(["c"],seq)["coverage"]==1
 assert validate_plan(seq,["c"],p)["passed"]

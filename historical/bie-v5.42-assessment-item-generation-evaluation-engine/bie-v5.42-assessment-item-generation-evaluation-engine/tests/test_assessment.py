import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_assessment

def test_valid():
 i={"item_id":"q","item_type":"MCQ","objective_ref":"o",
    "answer":"A","choices":[{"text":"A"},{"text":"B"}]}
 assert compile_assessment([i])["quality_gate"]["valid"]

def test_missing_objective():
 i={"item_id":"q","item_type":"SHORT_ANSWER","stem":"x"}
 assert not compile_assessment([i])["quality_gate"]["valid"]

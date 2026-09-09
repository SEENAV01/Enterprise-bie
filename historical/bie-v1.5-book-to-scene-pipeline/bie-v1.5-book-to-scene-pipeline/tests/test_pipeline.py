import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"pipeline"))
from pipeline import run

def test_pipeline(tmp_path):
    result=run("What is electric current?\n\nHow does a motor work?",tmp_path)
    assert result["book_ir"]["passages"]
    assert result["scene_plan"]
    assert result["question_coverage"]

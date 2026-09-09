import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from m301_real_execution import validate_mp4, acceptance

def test_missing_mp4_cannot_pass():
    r=validate_mp4("/definitely/missing/lesson.mp4")
    assert r["status"]=="failed"

def test_acceptance_requires_qa_and_artifacts():
    r=acceptance({"mp4":None},{"status":"accepted"})
    assert not r["accepted"]

def test_review_is_not_acceptance():
    r=acceptance({"mp4":"/tmp/nonexistent"},{"status":"review_required"})
    assert not r["accepted"]

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from m300_acceptance import validate_artifact_set, acceptance_gate

def artifacts():
    return {
        "source":"source.pdf","knowledge":"knowledge.json",
        "teaching_plan":"plan.json","script":"script.json",
        "scene_dsl":"scene.json","remotion_project":"project/",
        "mp4":"lesson.mp4","qa_report":"qa.json"
    }

def test_missing_artifact_fails():
    a=artifacts(); a["mp4"]=None
    r=validate_artifact_set(a)
    assert not r["passed"]
    assert "mp4" in r["missing"]

def test_qa_must_be_accepted():
    r=acceptance_gate(artifacts(),{"status":"review_required"})
    assert not r["accepted"]
    assert r["reason"]=="QA_NOT_ACCEPTED"

def test_full_gate_accepts():
    r=acceptance_gate(artifacts(),{"status":"accepted"})
    assert r["accepted"]
    assert r["reason"]=="ACCEPTED"

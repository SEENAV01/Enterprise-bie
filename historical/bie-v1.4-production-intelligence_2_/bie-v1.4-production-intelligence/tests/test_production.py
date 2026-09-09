import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from engine.qc import check
from engine.adaptive import next_action

def test_manifest_qc():
    p=Path(__file__).parents[1]/"examples/electricity-magnetism.production.json"
    m=json.loads(p.read_text())
    assert check(m)==[]

def test_adaptive():
    assert next_action("S17",1.0)=="advance"
    assert next_action("S17",.7)=="remediate_with_visual"
    assert next_action("S17",.2)=="reteach_prerequisite_then_retry"

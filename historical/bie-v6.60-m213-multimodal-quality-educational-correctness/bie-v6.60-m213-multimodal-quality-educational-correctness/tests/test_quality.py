import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))

from modality import modality_score,valid as modality_valid
from correctness import correctness_check
from objective import objective_coverage
from alignment import alignment_record
from evaluation import weighted_score,decision
from remediation_signal import remediation_signal
from provenance import provenance,traceable
from verification import verification,passed

def test_quality_evaluation():
    m=modality_score("VISUAL",.95)
    c=correctness_check("c","FACTUAL","lesson",.98)
    o=objective_coverage("o","Explain",True,.96)
    a=alignment_record("a","b1","sc1",["asset"],"n1",["cap"],.95)
    s=weighted_score([{"score":m["score"]},{"score":c["score"]}])
    sig=remediation_signal("s","q","LOW",["cap"],"timing","REVIEW_CAPTION_TIMING")
    p=provenance("q",["output"],["script"],["storyboard"],["e"],["s"])
    v=verification("v","q","PASS")
    assert modality_valid(m) and c["score"]==.98
    assert o["covered"] and a["scene_ref"]=="sc1"
    assert s > .9 and decision(s)=="PASS"
    assert sig["target_refs"] and traceable(p) and passed(v)

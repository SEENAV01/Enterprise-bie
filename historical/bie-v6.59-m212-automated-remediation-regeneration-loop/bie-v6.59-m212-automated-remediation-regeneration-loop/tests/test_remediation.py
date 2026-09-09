import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))

from failure import failure,valid as failure_valid
from diagnosis import diagnosis
from remediation import remediation
from impact import impact_analysis,minimal_scope
from regeneration import regeneration_job
from reqa import reqa_cycle,passed
from guard import regeneration_guard,safe
from provenance import provenance,traceable
from verification import verification,passed as verified

def test_remediation_loop():
    f=failure("f","VISUAL","LOW","asset-1","q","Mismatch")
    d=diagnosis("d","f","asset mismatch",["asset-1"])
    r=remediation("r","REGENERATE_ASSET",["asset-1"],"Fix it",["audio-1"])
    i=impact_analysis("i",["asset-1"],["audio-1"],["scene-1"])
    j=regeneration_job("j","r",["asset-1"])
    c=reqa_cycle("c","j","q2","PASS",["asset-1"])
    g=regeneration_guard(["f"],["r"],["audio-1"],3)
    p=provenance("loop",["j"],["f"],["d"],["r"],["q2"])
    v=verification("v","loop","PASS")
    assert failure_valid(f) and d["root_cause"]=="asset mismatch"
    assert r["action"]=="REGENERATE_ASSET" and minimal_scope(i)
    assert j["attempt"]==1 and passed(c) and safe(g)
    assert traceable(p) and verified(v)

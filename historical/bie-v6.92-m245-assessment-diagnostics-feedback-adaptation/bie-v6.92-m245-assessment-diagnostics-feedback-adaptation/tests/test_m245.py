import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from questions import question
from scoring import score_response,aggregate_mastery
from diagnostics import diagnose
from adaptation import adapt_from_diagnosis
def test_m245():
 q=question("q","c","x",["A"],"A")
 r=score_response(q,"A")
 assert r["correct"] and aggregate_mastery([r])["c"]==1
 assert diagnose("c",[r])["status"]=="MASTERED"
 assert adapt_from_diagnosis([{"concept_id":"c","status":"GAP"}])[0]["action"]=="RETEACH"

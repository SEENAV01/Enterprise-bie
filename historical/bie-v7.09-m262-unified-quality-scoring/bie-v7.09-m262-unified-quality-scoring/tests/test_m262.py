import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from scoring import weighted_score
from thresholds import evaluate_threshold
from hard_fail import collect_hard_failures
def test_m262():
 r={"a":{"valid":True},"b":{"valid":False}}
 assert weighted_score(r,{"a":1,"b":1})==50
 assert evaluate_threshold(95,90)["release"]
 assert collect_hard_failures({"x":{"valid":False,"errors":["AUDIO_MISSING"]}})

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_runtime

def test_runtime():
 q={"question_id":"q","concept_id":"c","correct_answer":5,"hints":[],"_attempt":1}
 r=compile_runtime(q,5,{"learner_id":"l","mastery":{"c":0.2}})
 assert r["runtime_result"]["evaluation"]["status"]=="CORRECT"
 assert r["runtime_result"]["mastery"]>0.2

def test_review():
 q={"question_id":"q","concept_id":"c","rubric":{"criteria":["explain"]}}
 r=compile_runtime(q,"answer",{"learner_id":"l"})
 assert r["runtime_result"]["evaluation"]["status"]=="REVIEW_REQUIRED"

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_assessment
def test_compile():
 r=compile_assessment(
  [{"objective_id":"o","concept_id":"c","statement":"Explain c","level":"EXPLAIN"}],
  [{"question_id":"q1","objective_id":"o","type":"CONCEPTUAL","prompt":"?","answer":"a"},
   {"question_id":"q2","objective_id":"o","type":"APPLICATION","prompt":"?","answer":"b"}])
 assert r["quality_gate"]["valid"]
def test_gap():
 r=compile_assessment(
  [{"objective_id":"o","concept_id":"c","statement":"Explain c","level":"EXPLAIN"}],
  [{"question_id":"q1","objective_id":"o","type":"CONCEPTUAL","prompt":"?","answer":"a"}])
 assert not r["quality_gate"]["valid"]

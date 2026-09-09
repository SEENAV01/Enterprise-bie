import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_observability

def test_summary():
 events=[
  {"event_type":"VALIDATION","payload":{"status":"PASS"}},
  {"event_type":"VALIDATION","payload":{"status":"FAIL"}},
  {"event_type":"RENDER","payload":{"status":"SUCCESS"}}]
 r=compile_observability(events)
 assert r["summaries"]["validation"]["total"]==2
 assert r["summaries"]["validation"]["failure_rate"]==0.5

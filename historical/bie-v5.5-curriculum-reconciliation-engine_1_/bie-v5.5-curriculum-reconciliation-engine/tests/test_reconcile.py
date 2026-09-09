import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from reconcile import reconcile
def test_order():
 r=reconcile(
  [{"id":"a","level":"FOUNDATION","required":True},
   {"id":"b","level":"FOUNDATION","prerequisites":["a"],"required":True}],
  [{"id":"c","level":"ADVANCED","prerequisites":["b"],"kind":"HIGHER_ORDER"}],
  "INTERMEDIATE")
 assert r["learning_order"]==["a","b","c"]
 assert r["quality_gate"]["valid"]
 assert r["nodes"][-1]["delivery"]=="DEEP_DIVE"
def test_cycle():
 r=reconcile(
  [{"id":"a","prerequisites":["b"]},{"id":"b","prerequisites":["a"]}],[], "INTERMEDIATE")
 assert not r["quality_gate"]["valid"]

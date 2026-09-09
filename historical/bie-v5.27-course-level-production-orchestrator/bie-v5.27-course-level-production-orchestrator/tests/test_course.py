import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_course

def test_course():
 r=compile_course("c",
  [{"lesson_id":"a"},{"lesson_id":"b"},{"lesson_id":"c"}],
  [["a","b"],["b","c"]],"style-v1",["asset"],2)
 assert r["quality_gate"]["valid"]
 assert r["lesson_order"]==["a","b","c"]
 assert r["render_batches"]==[["a","b"],["c"]]

def test_cycle():
 r=compile_course("c",
  [{"lesson_id":"a"},{"lesson_id":"b"]],
  [["a","b"],["b","a"]])
 assert not r["quality_gate"]["valid"]

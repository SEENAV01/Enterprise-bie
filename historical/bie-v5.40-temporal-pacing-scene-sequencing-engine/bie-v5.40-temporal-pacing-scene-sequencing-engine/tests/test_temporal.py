import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_timeline

def test_order():
 r=compile_timeline(
  [{"beat_id":"a"},{"beat_id":"b"}],
  [{"source":"a","target":"b"}])
 assert [x["beat_id"] for x in r["ordered_beats"]]==["a","b"]

def test_cycle():
 r=compile_timeline(
  [{"beat_id":"a"},{"beat_id":"b"}],
  [{"source":"a","target":"b"},{"source":"b","target":"a"}])
 assert not r["quality_gate"]["valid"]

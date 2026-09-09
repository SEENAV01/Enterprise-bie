import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from lesson_planner import plan_lesson
def test_plan():
 p=plan_lesson(
  {"type":"UNDERSTAND","topic":"c","depth":"CORE"},
  ["a","b","c"],
  [{"source":"a","target":"b"},{"source":"b","target":"c"}],
  {"a":["e1"],"b":["e2"],"c":["e3"]}
 )
 assert p["status"]=="READY"
 assert p["sequence"]==["a","b","c"]

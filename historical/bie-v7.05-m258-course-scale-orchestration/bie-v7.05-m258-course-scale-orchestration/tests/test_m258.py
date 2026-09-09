import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from dag import build_course_dag,topo_order
from incremental import fingerprint,plan_incremental
def test_m258():
 d=build_course_dag([{"id":"a"},{"id":"b"}],[{"source":"a","target":"b"}])
 assert topo_order(d)["order"]==["a","b"]
 old={"a":{"fingerprint":fingerprint({"x":1})}}
 assert plan_incremental(old,[{"id":"a","inputs":{"x":1}},{"id":"b","inputs":{"x":2}}])["reusable"]==["a"]

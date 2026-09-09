
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from bie_m6.planner import Unit, topo, build_lesson

def test_order():
    u=[Unit("b","B",prerequisite_ids=["a"]),Unit("a","A")]
    assert topo(u)==["a","b"]

def test_cycle():
    u=[Unit("a","A",prerequisite_ids=["b"]),Unit("b","B",prerequisite_ids=["a"])]
    try: topo(u)
    except ValueError: return
    assert False

def test_lesson():
    u=[Unit("a","A"),Unit("b","B",prerequisite_ids=["a"])]
    x=build_lesson(u)
    assert x["sequence"] and x["mastery"]["threshold"]==.85


import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from bie_m5.evaluator import evaluate

def test_pass():
    r=evaluate([{"id":"c","text":"x","support":"DIRECT","confidence":1,"source_refs":["p1"]}],
               [{"id":"a","scope":"BOOK_INTERNAL"}],[],1,1)
    assert r["decision"]=="PASS"

def test_cycle():
    r=evaluate([{"id":"c","text":"x","support":"DIRECT","confidence":1,"source_refs":["p1"]}],
               [{"id":"a","scope":"BOOK_INTERNAL"},{"id":"b","scope":"BOOK_INTERNAL"}],
               [{"source":"a","relation":"PREREQUISITE_OF","target":"b"},
                {"source":"b","relation":"PREREQUISITE_OF","target":"a"}],1,1)
    assert not r["cycle_free"] and r["decision"]!="PASS"

def test_provenance():
    r=evaluate([{"id":"c","text":"x","support":"DIRECT","confidence":1,"source_refs":[]}],
               [{"id":"a","scope":"BOOK_INTERNAL"}],[],1,1)
    assert r["provenance"]==0

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from alignment_pipeline import build_alignment
def test_alignment():
 text="A B C"
 ts=[{"start":0,"end":1},{"start":1,"end":2},{"start":2,"end":3}]
 x=build_alignment(text,ts,emphasis_terms=["B"])
 assert x["schema_version"]=="3.7"
 assert len(x["anchors"])>=4

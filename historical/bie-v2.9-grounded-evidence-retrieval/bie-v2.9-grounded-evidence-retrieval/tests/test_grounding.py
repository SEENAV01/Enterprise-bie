import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from retriever import retrieve
def test_retrieval():
 e=[{"evidence_id":"1","content":"Electric current is charge flow","page_number":1,"modality":"text"}]
 r=retrieve("electric current",e)
 assert r and r[0]["evidence_id"]=="1"

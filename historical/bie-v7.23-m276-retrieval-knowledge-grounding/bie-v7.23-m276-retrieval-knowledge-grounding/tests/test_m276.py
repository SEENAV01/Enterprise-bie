import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from ingestion import ingest_document
from chunking import chunk_document
from indexing import index_documents
from retrieval import retrieve
from freshness import freshness_status,source_allowed
def test_m276():
 d=ingest_document("d","alpha beta gamma")
 c=chunk_document(d,2,0); i=index_documents(c)
 assert retrieve("alpha",i)[0]["score"]>0
 assert freshness_status(2,2)=="CURRENT"
 assert source_allowed("CURRENT")
